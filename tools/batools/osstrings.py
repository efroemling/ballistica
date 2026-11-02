# Released under the MIT License. See LICENSE for details.
#
"""OS resource strings: native resource files fed from asset packages.

Some text has to live in an app bundle's native resources because the
OS reads it before (or without) the engine running: Android's launcher
label and a few Java-side dialog strings, or Apple's local-network
permission prompt. Those strings are authored in the builtin asset
package like any other, and flow out to native files in two steps:

1. When ``assetpins`` moves the builtin pin, :func:`fetch_data` pulls
   each entry in :data:`OS_STRINGS` for every locale (one cloud call)
   and the result is committed as a format-neutral JSON file
   (:data:`DATA_PATH`).
2. :func:`render_files` turns that file into the native files, offline.
   ``update_project`` writes them in the core repo (and fails on drift
   in check mode); spinoff renders them for dst projects, layering the
   dst's own override file (:data:`OVERRIDE_PATH`, fetched from the
   package its ``spinoffconfig.py`` pins via ``ctx.os_strings_package``)
   over the src values.

Design record: strings-asset-migration decision D40.
"""

import re
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    from typing import Any
    from pathlib import Path

    from bacommon.locale import LocaleResolved


@dataclass(frozen=True)
class OsString:
    """One string that lands in native OS resource files."""

    #: Neutral key; also the Android string-resource name.
    key: str

    #: Logical path of the string in the builtin asset package.
    entry: str

    #: Whether it goes into Android ``strings.xml`` files.
    android: bool = False

    #: The ``Info.plist`` key it localizes on Apple platforms, if any.
    apple_plist_key: str | None = None


#: Every OS resource string, and where each comes from and goes.
OS_STRINGS: list[OsString] = [
    OsString('app_name', 'strings/os/app_name', android=True),
    OsString('app_name_vr', 'strings/os/app_name_vr', android=True),
    OsString('fatal_error', 'strings/os/fatal_error', android=True),
    OsString('ok', 'strings/ui/ok', android=True),
    OsString('done', 'strings/ui/done', android=True),
    OsString(
        'local_network_usage',
        'strings/os/local_network_usage',
        apple_plist_key='NSLocalNetworkUsageDescription',
    ),
]

#: Where the fetched values live (committed; written by ``assetpins``).
DATA_PATH = 'pconfig/osstrings.json'

#: A spinoff dst's override values (committed in the dst; written by
#: ``assetpins`` from the package ``ctx.os_strings_package`` pins).
OVERRIDE_PATH = 'pconfig/osstrings_override.json'

#: An override package's strings live under this dir, one per key
#: (``strings/os/app_name`` overrides ``app_name``).
OVERRIDE_ENTRY_PREFIX = 'strings/os/'

ANDROID_RES_DIR = 'ballisticakit-android/BallisticaKit/src/main/res'
APPLE_LOCALIZABLE = (
    'ballisticakit-xcode/BallisticaKit Shared/Localizable.xcstrings'
)
APPLE_INFOPLIST = 'ballisticakit-xcode/BallisticaKit Shared/InfoPlist.xcstrings'

_APPLE_MACOS_DIR = 'ballisticakit-xcode/BallisticaKit macOS'

#: Info.plist files whose English (development-language) values we keep
#: in sync; the catalog supplies every other language.
#: (Built from parts rather than as split literals: spinoff renames
#: shorten these, and a split literal would then rejoin into a one-line
#: implicit concatenation that pylint rejects in dst projects.)
APPLE_PLISTS = [
    'ballisticakit-xcode/BallisticaKit iOS/BallisticaKit-iOS-Info.plist',
    *(
        f'{_APPLE_MACOS_DIR}/BallisticaKit-macOS-{variant}-Info.plist'
        for variant in ('AppStore', 'Steam', 'TestBuild')
    ),
]

_GENERATED_NOTE = (
    f'Generated from {DATA_PATH} by update_project (see'
    ' batools/osstrings.py); do not edit.'
)


@dataclass
class OsStringsData:
    """Fetched per-locale values for some set of OS strings."""

    #: The package version the values came from.
    apverid: str

    #: Key -> :class:`~bacommon.locale.Locale` value -> text.
    strings: dict[str, dict[str, str]]

    def to_json(self) -> str:
        """Our committed file form."""
        return (
            json.dumps(
                {'apverid': self.apverid, 'strings': self.strings},
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + '\n'
        )

    @classmethod
    def from_json(cls, text: str) -> OsStringsData:
        """Parse our committed file form."""
        raw = json.loads(text)
        apverid = raw['apverid']
        strings = raw['strings']
        if not isinstance(apverid, str) or not isinstance(strings, dict):
            raise CleanError('Malformed OS strings data.')
        return cls(apverid=apverid, strings=strings)

    @classmethod
    def load(cls, path: Path) -> OsStringsData:
        """Load from a file."""
        try:
            return cls.from_json(path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            raise CleanError(
                f"OS strings data not found at '{path}'."
            ) from None


# --------------------------------------------------------------------
# Fetching (cloud; assetpins only)
# --------------------------------------------------------------------


def fetch_data(projroot: Path, apverid: str) -> OsStringsData:
    """Fetch every :data:`OS_STRINGS` entry's values from ``apverid``."""
    by_entry = _fetch_strings(projroot, apverid, [s.entry for s in OS_STRINGS])
    return OsStringsData(
        apverid=apverid,
        strings={s.key: by_entry[s.entry] for s in OS_STRINGS},
    )


def fetch_override_data(projroot: Path, apverid: str) -> OsStringsData:
    """Fetch a spinoff override package's values.

    Every string under :data:`OVERRIDE_ENTRY_PREFIX` in the package
    overrides the key of the same name; one with no matching key is an
    error (likely a typo that would otherwise silently do nothing).
    """
    listing = _bacloud_json(
        projroot, apverid, ['assetpackage', '_listing', apverid]
    )
    valid = {s.key for s in OS_STRINGS}
    entries: list[str] = []
    for asset in listing['assets']:
        path = asset['path']
        assert isinstance(path, str)
        if asset['kind'] != 'string':
            continue
        if not path.startswith(OVERRIDE_ENTRY_PREFIX):
            continue
        key = path.removeprefix(OVERRIDE_ENTRY_PREFIX)
        if key not in valid:
            validstr = ', '.join(sorted(valid))
            raise CleanError(
                f'{apverid} has {path!r}, which matches no OS string'
                f' (valid keys: {validstr}).'
            )
        entries.append(path)
    if not entries:
        raise CleanError(
            f'{apverid} has no strings under {OVERRIDE_ENTRY_PREFIX!r};'
            ' nothing to override.'
        )
    by_entry = _fetch_strings(projroot, apverid, entries)
    return OsStringsData(
        apverid=apverid,
        strings={
            e.removeprefix(OVERRIDE_ENTRY_PREFIX): v
            for e, v in by_entry.items()
        },
    )


def _fetch_strings(
    projroot: Path, apverid: str, entries: list[str]
) -> dict[str, dict[str, str]]:
    """Fetch string entries' per-locale values from a package version."""
    data = _bacloud_json(
        projroot, apverid, ['assetpackage', '_strings', apverid], entries
    )
    strings = data['strings']
    assert isinstance(strings, dict)
    for entry in entries:
        if 'eng' not in strings.get(entry, {}):
            raise CleanError(f'{apverid} has no English value for {entry!r}.')
    return strings


def _bacloud_json(
    projroot: Path,
    apverid: str,
    cmd: list[str],
    extra_args: list[str] | None = None,
) -> dict[str, Any]:  # Any: parsed json, checked by each caller.
    """Run a bacloud command that writes a json file; return its data.

    The output path goes right after ``cmd`` (the convention for these
    commands), then ``extra_args``.
    """
    import os
    import tempfile
    import subprocess

    tmpdir = projroot / 'build/tmp'
    tmpdir.mkdir(parents=True, exist_ok=True)
    fd, tmppath = tempfile.mkstemp(suffix='.json', dir=tmpdir)
    os.close(fd)
    try:
        subprocess.run(
            [
                str(projroot / 'tools/bacloud'),
                *cmd,
                tmppath,
                *(extra_args or []),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        with open(tmppath, encoding='utf-8') as infile:
            data = json.load(infile)
        assert isinstance(data, dict)
        return data
    except subprocess.CalledProcessError as exc:
        # Structural cycle only: assetpins is the sole caller, so it is
        # always fully imported by the time we run.
        # pylint: disable=cyclic-import
        from batools.assetpins import describe_apverid_fetch_failure

        raise CleanError(
            describe_apverid_fetch_failure(
                apverid,
                action=f'fetch OS-string data from {apverid!r}',
                exc=exc,
                output=(exc.stderr or '') + (exc.stdout or ''),
            )
        ) from exc
    finally:
        if os.path.exists(tmppath):
            os.unlink(tmppath)


# --------------------------------------------------------------------
# Rendering (offline)
# --------------------------------------------------------------------


def merge(base: OsStringsData, override: OsStringsData | None) -> OsStringsData:
    """Layer an override's values over a base's, key by key.

    An overridden key takes all its locales from the override (falling
    back to the override's English), never mixing in the base's.
    """
    if override is None:
        return base
    strings = dict(base.strings)
    strings.update(override.strings)
    return OsStringsData(apverid=base.apverid, strings=strings)


def value(data: OsStringsData, key: str, locale: LocaleResolved) -> str:
    """A key's text for a locale, falling back to English."""
    values = data.strings.get(key)
    if values is None:
        raise CleanError(f'OS strings data has no {key!r} entry.')
    text = values.get(locale.locale.value)
    if text is None:
        text = values['eng']
    return text


def real_locales() -> list[LocaleResolved]:
    """Locales we hand the OS (skips private-use ``-x-`` ones)."""
    from bacommon.locale import LocaleResolved

    return [l for l in LocaleResolved if '-x-' not in l.tag]


def render_files(
    data: OsStringsData, existing: dict[str, str]
) -> dict[str, str]:
    """All native files for ``data``, keyed by (src-form) project path.

    ``existing`` maps each of :data:`APPLE_PLISTS` to its current text;
    those are rewritten in place (only their English values change),
    whereas everything else is generated whole.
    """
    out: dict[str, str] = {}
    for locale in real_locales():
        out[android_strings_path(locale)] = _render_android(data, locale)
    out[APPLE_LOCALIZABLE] = _render_apple_localizable()
    out[APPLE_INFOPLIST] = _render_apple_infoplist(data)
    for path in APPLE_PLISTS:
        out[path] = _render_plist(data, path, existing[path])
    return out


def generated_paths() -> list[str]:
    """Every project path :func:`render_files` produces."""
    return [android_strings_path(l) for l in real_locales()] + [
        APPLE_LOCALIZABLE,
        APPLE_INFOPLIST,
        *APPLE_PLISTS,
    ]


def android_strings_path(locale: LocaleResolved) -> str:
    """A locale's ``strings.xml`` path.

    English is the default (``values/``); others use Android 7+ BCP 47
    qualifiers (``values-b+es+419/``).
    """
    from bacommon.locale import LocaleResolved

    if locale is LocaleResolved.ENGLISH:
        subdir = 'values'
    else:
        subdir = 'values-' + '+'.join(['b'] + locale.tag.split('-'))
    return f'{ANDROID_RES_DIR}/{subdir}/strings.xml'


def _escape_android(text: str) -> str:
    """Escape text for an Android ``<string>`` resource."""
    text = (
        text.replace('\\', '\\\\')
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '\\"')
        .replace('\'', '\\\'')
        .replace('\n', '\\n')
    )
    # A leading '@' or '?' would read as a resource/attr reference.
    if text[:1] in ('@', '?'):
        text = '\\' + text
    return text


def _render_android(data: OsStringsData, locale: LocaleResolved) -> str:
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<!-- {_GENERATED_NOTE} -->',
        '<resources>',
        # The engine's own name for the locale (read at startup to pick
        # its language); not a translation.
        f'    <string name="ba_locale">{locale.locale.long_value}</string>',
    ]
    for ostr in OS_STRINGS:
        if not ostr.android:
            continue
        text = _escape_android(value(data, ostr.key, locale))
        lines.append(f'    <string name="{ostr.key}">{text}</string>')
    lines.append('</resources>')
    return '\n'.join(lines) + '\n'


#: The (string-only) json shapes our Apple string catalogs use.
type _CatalogJson = str | dict[str, _CatalogJson]


def _xcstrings_json(obj: _CatalogJson) -> str:
    # Xcode's own formatting (2-space indent, sorted keys, 'key : val',
    # raw utf-8, no trailing newline) so a build that rewrites the
    # catalog leaves it byte-identical.
    return json.dumps(
        obj,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ' : '),
    )


def _xcstrings_unit(text: str) -> _CatalogJson:
    return {'stringUnit': {'state': 'translated', 'value': text}}


def _render_apple_localizable() -> str:
    # 'Ballistica Locale' tells the engine which of its locales the OS
    # picked (FromCpp.swift getBaLocale); not a translation.
    return _xcstrings_json(
        {
            'sourceLanguage': 'en',
            'strings': {
                'Ballistica Locale': {
                    'localizations': {
                        l.tag: _xcstrings_unit(l.locale.long_value)
                        for l in real_locales()
                    }
                }
            },
            'version': '1.0',
        }
    )


def _render_apple_infoplist(data: OsStringsData) -> str:
    strings: dict[str, _CatalogJson] = {}
    for ostr in OS_STRINGS:
        if ostr.apple_plist_key is None:
            continue
        strings[ostr.apple_plist_key] = {
            'localizations': {
                l.tag: _xcstrings_unit(value(data, ostr.key, l))
                for l in real_locales()
            }
        }
    return _xcstrings_json(
        {'sourceLanguage': 'en', 'strings': strings, 'version': '1.0'}
    )


def _escape_plist(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _render_plist(data: OsStringsData, path: str, text: str) -> str:
    from bacommon.locale import LocaleResolved

    for ostr in OS_STRINGS:
        if ostr.apple_plist_key is None:
            continue
        english = _escape_plist(value(data, ostr.key, LocaleResolved.ENGLISH))
        matches = list(
            re.finditer(
                rf'<key>{re.escape(ostr.apple_plist_key)}</key>\s*<string>'
                r'([^<]*)</string>',
                text,
            )
        )
        if len(matches) != 1:
            raise CleanError(
                f'Expected one {ostr.apple_plist_key} entry in {path};'
                f' found {len(matches)}.'
            )
        start, end = matches[0].span(1)
        text = text[:start] + english + text[end:]
    return text
