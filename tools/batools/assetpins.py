# Released under the MIT License. See LICENSE for details.
#
"""Asset-package pin inspection / update.

``assetpins`` is the single owner of "what asset-package version
are we pinned to" across the source tree. It discovers pins in
two places:

- the ``"assets"`` entry in ``pconfig/projectconfig.json``
  (the construct-mode/bootloader pin),
- per-wrapper ``# ba_meta require asset-package <id>`` lines
  inside Python wrapper modules (server-generated; see the
  ``GET /api/v1/admin/asset-package-versions/{id}/python-wrapper``
  REST endpoint).

Per the global build-system design, this is the only build-flow
step that talks to the cloud and the only one that mutates
checked-in source as part of normal use (other than ``make
update``, which is purely about regenerating bookkeeping derived
from on-disk source state).

Apverid schema (from the third segment of ``<account>.<name>.<seg>``):

- ``<seg>`` starts with a digit → **PROD** (allowed anywhere).
- ``<seg>`` matches ``dev(\\d.*)?`` → **DEV** (allowed in
  private/internal-CI only; blocked from public).
- ``<seg>`` matches ``test\\d.*`` → **TEST** (allowed in
  private/internal-CI only; blocked from public).

Bare ``dev`` (no trailing digit) is an unresolved pseudo-id
meaning "give me the latest dev snapshot". The build refuses to
consume it; ``assetpins update`` resolves it via master and
writes the resolved ``devN`` form back to the pin's source file.

The ``update`` operation takes a TARGET and a VERSION:

- TARGET: ``all``, an asset-package name (e.g. ``bastdassets``)
  matching any pin of that package across accounts, or a file
  path matching exactly one pin.
- VERSION: ``latest`` (current track, newest version),
  ``prod`` / ``test`` / ``dev`` (switch to or stay on that track,
  newest version), or a full third-segment like ``260513a``
  (prod), ``test260512a``, or ``dev260513a`` (exact pin;
  account+package come from the pin's own apverid).

Each pin is independent — moving one pin does not move any
other. Track-switching is an explicit, deliberate operation.
"""

from __future__ import annotations

import re
import enum
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from pathlib import Path


# Total-width policy for the `assetpins` table output. We
# compute a "natural" width (everything visible, no clipping)
# from the data, then clamp it against an upper bound from the
# environment: terminal width when on a TTY (no narrower than
# ``MIN_TTY_COLS``); a stable fallback otherwise (so logs and
# tests stay deterministic). If the upper bound is below
# natural, the file column clips with leading ``...``.
MIN_TTY_COLS = 60
FALLBACK_COLS = 80


def _max_table_width() -> int:
    """Upper bound on total table width for the current env."""
    import sys
    import shutil

    if not sys.stdout.isatty():
        return FALLBACK_COLS
    return max(shutil.get_terminal_size().columns, MIN_TTY_COLS)


class PinType(enum.Enum):
    """Classification of an apverid by its third-segment shape."""

    PROD = 'prod'
    DEV = 'dev'
    TEST = 'test'


# Anchored regexes on the third segment of an apverid.
_RE_DEV = re.compile(r'^dev(\d.*)?$')
_RE_TEST = re.compile(r'^test\d.*$')


def classify_apverid(apverid: str) -> PinType:
    """Classify an apverid string by its third segment.

    Raises ``CleanError`` if the apverid is structurally
    malformed (wrong segment count, unrecognized third-segment
    shape).
    """
    parts = apverid.split('.')
    if len(parts) != 3:
        raise CleanError(
            f'Malformed apverid {apverid!r}: expected three'
            f' dot-separated segments, got {len(parts)}.'
        )
    seg = parts[2]
    if not seg:
        raise CleanError(
            f'Malformed apverid {apverid!r}: empty version segment.'
        )
    first = seg[0]
    if first.isdigit():
        return PinType.PROD
    if _RE_DEV.fullmatch(seg) is not None:
        return PinType.DEV
    if _RE_TEST.fullmatch(seg) is not None:
        return PinType.TEST
    raise CleanError(
        f'Malformed apverid {apverid!r}: third segment {seg!r}'
        f' does not match prod/dev/test shape.'
    )


def is_unresolved_dev(apverid: str) -> bool:
    """Return True if the apverid is a bare ``<account>.<name>.dev``.

    Bare-dev is a request to "use the latest dev snapshot" and
    must be resolved by ``assetpins update`` before any build
    step can consume it.
    """
    parts = apverid.split('.')
    return len(parts) == 3 and parts[2] == 'dev'


@dataclass
class Pin:
    """One discovered asset-package pin."""

    #: Pin-kind identifier; one of ``projectconfig`` or ``wrapper``.
    kind: str
    #: File the pin lives in, relative to projroot.
    file_path: Path
    #: Current apverid string.
    apverid: str
    pin_type: PinType
    #: ``<account>`` segment from the apverid (e.g. ``a-0``).
    account: str
    #: ``<name>`` segment from the apverid (e.g. ``bastdassets``).
    package: str
    #: For ``wrapper`` pins, which featureset's loader API the
    #: wrapper uses (``bascenev1`` or ``bauiv1``). None for
    #: projectconfig pins.
    wrapper_type: str | None = None
    #: Filled by ``do_list`` (master roundtrip); None if not
    #: queried.
    latest_available: str | None = None


# --------------------------------------------------------------------
# Public ops
# --------------------------------------------------------------------


def do_list(projroot: Path) -> None:
    """Print discovered pins + whether master has newer versions."""
    pins = _discover_pins(projroot)
    if not pins:
        print('No asset-package pins detected.')
        _print_help_pointer()
        return

    # Master roundtrips happen here (one per pin, sequential —
    # the pin set is small).
    for pin in pins:
        try:
            pin.latest_available = _query_latest_for_track(
                projroot, pin, pin.pin_type
            )
        except Exception as exc:
            print(f'  {pin.file_path}: lookup failed: {exc}')
            pin.latest_available = None

    _print_pin_table(pins)
    _print_help_pointer()


def _print_pin_table(pins: list[Pin]) -> None:
    """Render the discovered-pins table within the column budget."""
    headers = ('file', 'package', 'version', 'status')
    rows = [
        (
            str(pin.file_path),
            pin.package,
            _format_pin_label(pin),
            _pin_color(pin),
            _format_pin_status(pin),
        )
        for pin in pins
    ]

    # Non-file columns always size to fit their content.
    pkg_w = max(len(headers[1]), *(len(r[1]) for r in rows))
    pin_w = max(len(headers[2]), *(len(r[2]) for r in rows))
    status_w = max(len(headers[3]), *(len(r[4]) for r in rows))
    # 3 inter-column gaps of 2 spaces each = 6.
    fixed_w = pkg_w + pin_w + status_w + 6

    # Natural file-column width = enough to show every path
    # unclipped. We cap the total table width at the smaller of
    # (natural total, env upper bound) — never wider than needed,
    # never wider than the terminal. If the env bound is below
    # natural, the file column clips with leading ``...``.
    natural_file_w = max(len(headers[0]), *(len(r[0]) for r in rows))
    natural_total = natural_file_w + fixed_w
    total_w = min(natural_total, _max_table_width())
    file_w = max(len(headers[0]), total_w - fixed_w)

    sep = '-' * total_w

    print(f'{Clr.BLD}{Clr.SBLK}Asset Pins{Clr.RST}')
    print(f'{Clr.SBLK}{sep}{Clr.RST}')
    # Trailing column intentionally not padded — keeps output
    # free of trailing whitespace. Color codes are wrapped
    # around the fully-formatted line so the ``:<{width}}``
    # padding stays based on visible-text length.
    header_line = (
        f'{headers[0]:<{file_w}}  '
        f'{headers[1]:<{pkg_w}}  '
        f'{headers[2]:<{pin_w}}  '
        f'{headers[3]}'
    )
    print(f'{Clr.SBLK}{header_line}{Clr.RST}')
    for file_path, package, pin_label, pin_clr, status in rows:
        # Pad each cell to width as visible text *first*, then
        # wrap with color codes so column alignment is based on
        # visible width (ANSI codes have zero printable width
        # but the formatter doesn't know that).
        padded_pin = f'{pin_label:<{pin_w}}'
        colored_pin = (
            f'{pin_clr}{padded_pin}{Clr.RST}' if pin_clr else padded_pin
        )
        status_clr = _status_color(status)
        colored_status = (
            f'{status_clr}{status}{Clr.RST}' if status_clr else status
        )
        padded_package = f'{package:<{pkg_w}}'
        print(
            f'{_clip_left(file_path, file_w):<{file_w}}  '
            f'{Clr.BLD}{padded_package}{Clr.RST}  '
            f'{colored_pin}  '
            f'{colored_status}'
        )
    print(f'{Clr.SBLK}{sep}{Clr.RST}')


def _format_pin_label(pin: Pin) -> str:
    """Return the human-readable label form.

    Prod pins display as the bare version segment (the track is
    conveyed by color in the rendered table). Test pins show
    ``test <suffix>``. Dev pins show just ``dev`` since the
    resolved snapshot suffix is volatile.
    """
    from typing import assert_never

    parts = pin.apverid.split('.')
    seg = parts[2] if len(parts) == 3 else ''
    match pin.pin_type:
        case PinType.PROD:
            return seg
        case PinType.TEST:
            return seg
        case PinType.DEV:
            return 'dev'
        case _:
            assert_never(pin.pin_type)


def _pin_color(pin: Pin) -> str:
    """Return the ANSI color sequence for a pin's version label.

    All version labels render bold; track is conveyed by hue.
    """
    from typing import assert_never

    match pin.pin_type:
        case PinType.PROD:
            return f'{Clr.BLD}{Clr.SGRN}'
        case PinType.DEV:
            return f'{Clr.BLD}{Clr.SYLW}'
        case PinType.TEST:
            return f'{Clr.BLD}{Clr.SMAG}'
        case _:
            assert_never(pin.pin_type)


def _format_pin_status(pin: Pin) -> str:
    if pin.latest_available is None or pin.latest_available == pin.apverid:
        return 'up to date'
    return 'UPDATE AVAILABLE'


def _status_color(status: str) -> str:
    """Return the ANSI color for a status label, or ``''``."""
    if status == 'UPDATE AVAILABLE':
        return f'{Clr.BLD}{Clr.CYN}'
    return ''


def _clip_left(text: str, width: int) -> str:
    """Truncate from the left with ``...`` if longer than ``width``."""
    if len(text) <= width:
        return text
    if width <= 3:
        return text[-width:]
    return '...' + text[-(width - 3) :]


def do_help() -> None:
    """Print usage examples for ``assetpins update``."""
    print(
        f'\n'
        f'{Clr.BLD}USAGE{Clr.RST}\n'
        f'\n'
        f'  {Clr.BLD}VIEWING PINS{Clr.RST}\n'
        f'    tools/pcommand assetpins\n'
        f'\n'
        f'  {Clr.BLD}UPDATING PINS{Clr.RST}\n'
        f'    tools/pcommand assetpins update <TARGET> <VERSION>\n'
        f'    TARGET:  all | <package-name> | <file-path>\n'
        f'    VERSION: latest | prod | test | dev | <full-third-segment>\n'
        '\n'
        f'{Clr.BLD}EXAMPLES{Clr.RST}\n'
        f'\n'
        f'  {Clr.MAG}make assetpins{Clr.RST}\n'
        f'      Show current pins.\n'
        f'      Same as `tools/pcommand assetpins`.\n'
        f'\n'
        f'  {Clr.MAG}make assetpins-latest{Clr.RST}\n'
        f'      Bump every pin to the newest version on its'
        f' current track.\n'
        f'      Same as `tools/pcommand assetpins update all latest`.\n'
        f'\n'
        f'  {Clr.MAG}tools/pcommand assetpins update'
        f' all prod{Clr.RST}\n'
        f'      Switch every pin to the latest prod'
        f' version.\n'
        f'\n'
        f'  {Clr.MAG}tools/pcommand assetpins update'
        f' pconfig/projectconfig.json dev{Clr.RST}\n'
        f'      Re-resolve just the projectconfig pin to the'
        f' current dev snapshot.\n'
        f'\n'
        f'  {Clr.MAG}tools/pcommand assetpins update myassetpack'
        f' test260513a{Clr.RST}\n'
        f'      Pin every myassetpack instance to a specific version.\n'
        f'\n'
    )


def _print_help_pointer() -> None:
    print(
        f'{Clr.SBLK}For pin-wrangling examples, run:'
        f' tools/pcommand assetpins help.{Clr.RST}'
    )


def do_update(projroot: Path, target_str: str, version_str: str) -> None:
    """Update one or more pins to a chosen version.

    ``target_str``: ``all``, an asset-package name (e.g.
    ``bastdassets``), or a file path matching exactly one pin.

    ``version_str``: ``latest`` (track-preserving), ``prod`` /
    ``test`` / ``dev`` (track-switching), or a full third
    segment (e.g. ``260513a``, ``dev260513a``, ``test260512a``).
    """
    pins = _discover_pins(projroot)
    if not pins:
        raise CleanError('No asset-package pins detected.')

    matched = _match_target(pins, target_str)

    projectconfig_changed = False
    for pin in matched:
        new_apverid = _compute_new_apverid(projroot, pin, version_str)
        if new_apverid == pin.apverid:
            print(
                f'  {Clr.BLD}{pin.file_path}{Clr.RST}'
                f' already at {Clr.CYN}{pin.apverid}{Clr.RST}.'
            )
            continue
        _apply_update(projroot, pin, new_apverid)
        print(
            f'  {Clr.BLD}{pin.file_path}{Clr.RST}'
            f' updated: {Clr.CYN}{pin.apverid}{Clr.RST}'
            f' -> {Clr.GRN}{new_apverid}{Clr.RST}'
        )
        if pin.kind == 'projectconfig':
            projectconfig_changed = True
        pin.apverid = new_apverid

    # If the projectconfig pin moved, refresh the local bundle
    # manifests + regenerate the C++ wrapper splice. (Wrapper
    # pins don't trigger this — they're per-package references
    # used at runtime, and the construct-mode pin in projectconfig
    # is what drives the build's bundled assets.)
    if projectconfig_changed:
        for variant in ('gui', 'headless'):
            _run_pcommand(projroot, 'asset_bundle_build', variant)
        from batools.builtinassetids import generate

        changed = generate(projroot, check=False)
        if changed:
            print(f'{Clr.GRN}C++ wrapper updated.{Clr.RST}')
        else:
            print(f'{Clr.BLU}C++ wrapper already up to date.{Clr.RST}')


def do_check(projroot: Path) -> list[Pin]:
    """Return the list of dev/test pins (empty = clean).

    Used by the pre-pubsync gate (and by ``make assetpins-check``)
    to refuse before any committed-source dev/test pin can flow
    to a public artifact.
    """
    return [
        pin
        for pin in _discover_pins(projroot)
        if pin.pin_type is not PinType.PROD
    ]


# --------------------------------------------------------------------
# Internal: pin discovery
# --------------------------------------------------------------------


def _discover_pins(projroot: Path) -> list[Pin]:
    """Find all asset-package pins in the source tree."""
    from pathlib import Path
    from efrotools.project import getprojectconfig

    pins: list[Pin] = []

    # projectconfig "assets" — the construct-mode/bootloader pin.
    pc_value = getprojectconfig(projroot).get('assets')
    if isinstance(pc_value, str) and pc_value:
        pin_type = (
            PinType.DEV
            if is_unresolved_dev(pc_value)
            else classify_apverid(pc_value)
        )
        account, package = _account_and_package_or_bare_dev(pc_value)
        pins.append(
            Pin(
                kind='projectconfig',
                file_path=Path('pconfig/projectconfig.json'),
                apverid=pc_value,
                pin_type=pin_type,
                account=account,
                package=package,
            )
        )

    # Python wrappers: any file under src/assets/ba_data/python/
    # carrying a ``# ba_meta require asset-package <id>`` line.
    pins.extend(_discover_wrapper_pins(projroot))

    return pins


def _discover_wrapper_pins(projroot: Path) -> list[Pin]:
    """Walk Python source via bacommon.metascan to find wrappers."""
    from pathlib import Path
    from bacommon.metascan import DirectoryScan

    python_root = projroot / 'src/assets/ba_data/python'
    if not python_root.is_dir():
        return []

    scanner = DirectoryScan(paths=[str(python_root)])
    scanner.run()

    pins: list[Pin] = []
    for apverid, modulenames in scanner.results.asset_packages.items():
        for modulename in modulenames:
            file_path = Path(
                'src/assets/ba_data/python',
                *modulename.split('.'),
            ).with_suffix('.py')
            wrapper_type = _detect_wrapper_type(projroot / file_path)
            account, package = _account_and_package_or_bare_dev(apverid)
            pins.append(
                Pin(
                    kind='wrapper',
                    file_path=file_path,
                    apverid=apverid,
                    pin_type=classify_apverid(apverid),
                    account=account,
                    package=package,
                    wrapper_type=wrapper_type,
                )
            )
    return pins


# Wrapper-type tag in the wrapper's module docstring. The
# server emits e.g. ``"""Asset-package wrapper for ``<id>``
# (bascenev1)."""`` as the first line of the docstring; the
# parenthesised value is the wrapper type.
_RE_WRAPPER_DOCSTRING_TYPE = re.compile(
    r'Asset-package wrapper for ``[^`]+`` \((bascenev1|bauiv1)\)'
)


def _detect_wrapper_type(path: Path) -> str:
    """Sniff a wrapper's featureset target from its docstring.

    Server-generated wrappers carry the wrapper type in their
    module docstring (``Asset-package wrapper for ``<id>``
    (<wrapper_type>).``). Extracting from there is more robust
    than parsing imports, which now live under TYPE_CHECKING +
    function-local statements so they don't trip the project's
    "package shouldn't import its own top-level" rule when the
    wrapper sits inside its featureset's own package.
    """
    if not path.is_file():
        raise CleanError(
            f'Wrapper file {path} does not exist on disk;'
            f' metascan and disk disagree.'
        )
    text = path.read_text()
    match = _RE_WRAPPER_DOCSTRING_TYPE.search(text)
    if match is None:
        raise CleanError(
            f'Could not detect wrapper_type in {path};'
            f' expected an ``Asset-package wrapper for ``<id>``'
            f' (bascenev1|bauiv1)`` docstring line.'
        )
    return match.group(1)


def _account_and_package_or_bare_dev(apverid: str) -> tuple[str, str]:
    """Return ``(account, package)`` from an apverid.

    Tolerates bare-dev apverids (``<account>.<name>.dev``).
    """
    parts = apverid.split('.')
    if len(parts) != 3:
        raise CleanError(
            f'Cannot extract account/package from'
            f' malformed apverid {apverid!r}.'
        )
    return parts[0], parts[1]


# --------------------------------------------------------------------
# Internal: target matching
# --------------------------------------------------------------------


def _match_target(pins: list[Pin], target_str: str) -> list[Pin]:
    """Resolve a TARGET string against the discovered pins."""
    from pathlib import Path

    if target_str == 'all':
        return pins

    # Try as package name (matches any pin whose package
    # segment equals the target, possibly across accounts).
    by_package = [p for p in pins if p.package == target_str]
    if by_package:
        return by_package

    # Try as file path. Normalise both to ``Path`` so trailing
    # slash / leading ``./`` shouldn't matter.
    target_path = Path(target_str)
    by_path = [p for p in pins if p.file_path == target_path]
    if by_path:
        return by_path

    known_packages = sorted({p.package for p in pins})
    known_paths = sorted(str(p.file_path) for p in pins)
    raise CleanError(
        f'No pins match target {target_str!r}.'
        f' Known packages: {known_packages}.'
        f' Known files: {known_paths}.'
    )


# --------------------------------------------------------------------
# Internal: version → new apverid
# --------------------------------------------------------------------


def _compute_new_apverid(projroot: Path, pin: Pin, version_str: str) -> str:
    """Compute what apverid ``pin`` should move to.

    Track-preserving (``latest``) and track-switching
    (``prod``/``test``/``dev``) forms query master. Concrete
    third-segment forms (e.g. ``260513``, ``dev260513a``) are
    used as-is, combined with the pin's own account+package.
    """
    if version_str == 'latest':
        return _query_latest_for_track(projroot, pin, pin.pin_type)
    if version_str == 'prod':
        return _query_latest_for_track(projroot, pin, PinType.PROD)
    if version_str == 'test':
        return _query_latest_for_track(projroot, pin, PinType.TEST)
    if version_str == 'dev':
        return _query_latest_for_track(projroot, pin, PinType.DEV)
    # Concrete third-segment form. Validate by classifying the
    # synthesised apverid; this also rejects malformed inputs
    # like ``dev`` (which would re-introduce the bare-pseudo-id
    # state we just resolved away — users should pass ``dev``
    # as the track-switching form above instead).
    new = f'{pin.account}.{pin.package}.{version_str}'
    if is_unresolved_dev(new):
        raise CleanError(
            f'VERSION {version_str!r} is the bare dev pseudo-id;'
            f' pass `dev` (without the third-segment quotes) as a'
            f' track-switching form to resolve to the current'
            f' devN snapshot.'
        )
    classify_apverid(new)  # raises on malformed
    return new


def _query_latest_for_track(projroot: Path, pin: Pin, track: PinType) -> str:
    """Ask master for the latest apverid on ``track`` for pin.

    Always uses the pin's own ``account`` to avoid cross-account
    aliasing — two pins on different accounts but the same
    package name have separate version histories.
    """
    from typing import assert_never

    match track:
        case PinType.DEV:
            return _resolve_bare_dev(projroot, pin.account, pin.package)
        case PinType.PROD:
            result = _bacloud_version(
                projroot, pin.account, pin.package, prod=True
            )
            if result is None:
                raise CleanError(
                    f'No prod version of {pin.account}.{pin.package}'
                    f' found on master.'
                )
            return result
        case PinType.TEST:
            result = _bacloud_version(
                projroot, pin.account, pin.package, prod=False
            )
            if result is None:
                raise CleanError(
                    f'No test version of {pin.account}.{pin.package}'
                    f' found on master.'
                )
            return result
        case _:
            assert_never(track)


# --------------------------------------------------------------------
# Internal: master roundtrips
# --------------------------------------------------------------------


def _resolve_bare_dev(projroot: Path, account: str, package: str) -> str:
    """Ask master to resolve to the current dev snapshot.

    Uses ``bacloud assetpackage version --dev`` which routes
    through the workspace-aware dev-resolve path on master and
    returns just the resolved apverid — no assemble, no
    recipe-cache work, no local manifest side-effects.
    """
    cmd = [
        str(projroot / 'tools' / 'bacloud'),
        'assetpackage',
        'version',
        package,
        '--account',
        account,
        '--dev',
    ]
    result = subprocess.run(
        cmd, cwd=projroot, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise CleanError(
            f'Failed to resolve {account}.{package}.dev via'
            f' bacloud assetpackage version --dev:'
            f' {result.stderr.strip()}'
        )
    out = result.stdout.strip()
    if not out:
        raise CleanError(
            f'bacloud assetpackage version --dev returned empty'
            f' output for {account}.{package}.'
        )
    return out


def _bacloud_version(
    projroot: Path, account: str, package: str, *, prod: bool
) -> str | None:
    """Return the newest version id for ``account.package``.

    Wraps ``bacloud assetpackage version --account <X>``. Returns
    None if bacloud reports no matching version.
    """
    cmd = [
        str(projroot / 'tools' / 'bacloud'),
        'assetpackage',
        'version',
        package,
        '--account',
        account,
    ]
    if prod:
        cmd.append('--prod')
    result = subprocess.run(
        cmd, cwd=projroot, capture_output=True, text=True, check=False
    )
    # bacloud convention: exit 0 = found, exit 1 = no match,
    # exit 2 = error.
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise CleanError(
            f'bacloud assetpackage version failed for'
            f' {account}.{package} (prod={prod}):'
            f' {result.stderr.strip()}'
        )
    out = result.stdout.strip()
    return out or None


def _fetch_wrapper(projroot: Path, apverid: str, wrapper_type: str) -> str:
    """Fetch a freshly-generated wrapper module from master.

    Hits the admin REST endpoint via ``tools/pcommand bacurl``
    (which injects Bearer auth from localconfig). Returns the
    wrapper source as a string.
    """
    url = (
        f'https://www.ballistica.net/api/v1/admin/'
        f'asset-package-versions/{apverid}/python-wrapper'
        f'?wrapper_type={wrapper_type}'
    )
    result = subprocess.run(
        [
            str(projroot / 'tools' / 'pcommand'),
            'bacurl',
            url,
        ],
        cwd=projroot,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CleanError(
            f'Failed to fetch wrapper for {apverid}'
            f' (wrapper_type={wrapper_type}):'
            f' {result.stderr.strip()}'
        )
    content = result.stdout
    if not content.lstrip().startswith('# Released under'):
        raise CleanError(
            f'Fetched wrapper for {apverid} does not look like a'
            f' valid wrapper source (first chars: {content[:80]!r}).'
        )
    return content


# --------------------------------------------------------------------
# Internal: apply update (writeback)
# --------------------------------------------------------------------


def _apply_update(projroot: Path, pin: Pin, new_apverid: str) -> None:
    """Mutate the pin's source file to point at ``new_apverid``."""
    if pin.kind == 'projectconfig':
        _writeback_projectconfig(projroot, new_apverid)
        return
    if pin.kind == 'wrapper':
        _writeback_wrapper(projroot, pin, new_apverid)
        return
    raise CleanError(f'Internal error: unknown pin kind {pin.kind!r}.')


def _writeback_projectconfig(projroot: Path, new_apverid: str) -> None:
    """Replace ``"assets"`` in projectconfig.

    Uses a string-level read/edit/write to preserve formatting
    (comments, key ordering, trailing newline) since the rest of
    the file may carry editorial intent we don't want
    ``json.dump`` to wash away.
    """
    pc = projroot / 'pconfig' / 'projectconfig.json'
    text = pc.read_text()
    new_text, count = re.subn(
        r'("assets"\s*:\s*)"[^"]*"',
        lambda m: f'{m.group(1)}"{new_apverid}"',
        text,
        count=1,
    )
    if count == 0:
        raise CleanError(
            f'Could not locate "assets" entry in {pc} for writeback.'
        )
    if new_text != text:
        pc.write_text(new_text)
        # ``efrotools.project.getprojectconfig`` caches its
        # parsed result in a process-wide dict. Since we wrote
        # the file directly (preserving formatting) instead of
        # going through ``setprojectconfig``, the cache is now
        # stale; clear it so subsequent reads see our update.
        from efrotools import project as _project

        _project._g_project_configs.pop(  # pylint: disable=protected-access
            str(projroot), None
        )


def _writeback_wrapper(projroot: Path, pin: Pin, new_apverid: str) -> None:
    """Re-fetch the wrapper at the new apverid and overwrite file.

    Wrappers are server-generated; updating means asking the
    server for a fresh version pointing at ``new_apverid`` and
    replacing the file in-place. We never hand-edit a wrapper.
    """
    assert pin.wrapper_type is not None
    content = _fetch_wrapper(projroot, new_apverid, pin.wrapper_type)
    full = projroot / pin.file_path
    if full.read_text() != content:
        full.write_text(content)


# --------------------------------------------------------------------
# Internal: pcommand invocation
# --------------------------------------------------------------------


def _run_pcommand(projroot: Path, name: str, *args: str) -> None:
    """Subprocess-invoke a sibling pcommand."""
    cmd = [str(projroot / 'tools' / 'pcommand'), name, *args]
    subprocess.run(cmd, cwd=projroot, check=True)
