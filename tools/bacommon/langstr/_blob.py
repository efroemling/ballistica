# Released under the MIT License. See LICENSE for details.
#
"""Canonical serialization for per-locale language-string blobs.

The single on-disk/wire form of a resolved asset-package's per-locale
strings: a ``{'strings': {name: value}}`` JSON object where each value is a
plain ``str`` or a :class:`~bacommon.loctext.StringSelector` in its compact
dict form. One format, produced by the asset-build recipe and the vendor
command alike and parsed by the client decode -- :func:`parse_language_blob`
is the exact inverse of :func:`serialize_language_blob`, so producers and
consumer can never drift.

New-format strings live under the top-level ``strings`` key; the old
per-locale language data uses a sibling ``legacy`` key (a different on-disk
shape). A package ships one or the other.
"""

import json

from typing import TYPE_CHECKING

from efro.dataclassio import dataclass_to_dict, dataclass_from_dict
from bacommon.loctext import StringSelector

if TYPE_CHECKING:
    from bacommon.langstr._core import WrapParams

#: Top-level key the new-format strings live under (sibling to ``legacy``).
LANGUAGE_BLOB_STRINGS_KEY = 'strings'

#: Top-level key holding formatter components copied in at build time
#: (unit words for ``data_size`` and friends).
#:
#: A sibling of ``strings`` rather than a reserved path inside it, and
#: that is load-bearing. String indices are assigned in sorted-name
#: order over the ``strings`` map; the producer derives them from briefs
#: (no components) and the consumer from the blob. Component entries
#: living in ``strings`` would shift every authored string's index on
#: the consumer side only, and :class:`LangStrSpecResourceIndexed` would
#: decode to the wrong string. Out here they cannot perturb anything,
#: and no name needs reserving in the authored namespace.
LANGUAGE_BLOB_COMPONENTS_KEY = 'components'


def serialize_language_blob(
    values: dict[str, str | StringSelector],
    wraps: 'dict[str, WrapParams] | None' = None,
    param_kinds: dict[str, dict[str, str]] | None = None,
    components: 'dict[str, str | StringSelector] | None' = None,
) -> str:
    """Serialize a per-locale value map to the canonical language blob.

    ``values`` maps each string's logical name to its value -- a plain
    ``str`` or a :class:`StringSelector`. ``wraps`` optionally maps
    names to their definition-time :class:`WrapParams` (decision D-t);
    a wrapped entry is emitted as a ``{'v': value, 'w': wrap}`` carrier
    dict (which pre-wrap clients skip fail-soft). Output is
    deterministic (sorted keys, fixed formatting) for cache stability
    and diffability.

    ``param_kinds`` optionally maps a name to its ``{param: kind}`` for
    params whose kind the *display* side must know -- a byte count
    rendered as "1.2 GB" cannot be recovered from the translated text,
    which carries only a ``{name}`` token. It rides the same carrier
    under ``'k'``.

    Pass only the params that actually need it (anything but ``'text'``).
    A string with none is emitted exactly as before, so adding this
    leaves every existing blob byte-identical -- which matters because
    blob content is a cache key.
    """

    def _encode(name: str, value: str | StringSelector) -> object:
        out: object = (
            dataclass_to_dict(value)
            if isinstance(value, StringSelector)
            else value
        )
        wrap = None if wraps is None else wraps.get(name)
        kinds = None if param_kinds is None else param_kinds.get(name)
        if wrap is not None or kinds:
            carrier: dict[str, object] = {'v': out}
            if wrap is not None:
                carrier['w'] = dataclass_to_dict(wrap)
            if kinds:
                carrier['k'] = dict(sorted(kinds.items()))
            out = carrier
        return out

    out: dict[str, object] = {
        LANGUAGE_BLOB_STRINGS_KEY: {
            name: _encode(name, value) for name, value in values.items()
        }
    }
    if components:
        out[LANGUAGE_BLOB_COMPONENTS_KEY] = {
            name: (
                dataclass_to_dict(value)
                if isinstance(value, StringSelector)
                else value
            )
            for name, value in components.items()
        }
    return json.dumps(
        out,
        ensure_ascii=False,
        indent=1,
        sort_keys=True,
    )


def parse_language_blob(text: str) -> dict[str, str | StringSelector]:
    """Parse a canonical language blob into a ``{name: value}`` map.

    The exact inverse of :func:`serialize_language_blob`: reads the
    top-level ``strings`` object, turning each value back into a ``str``
    (plain) or a :class:`StringSelector` (a dict). A blob with no ``strings``
    key (e.g. a legacy-only package) yields an empty map; malformed values
    are skipped (fail-soft on the consumer side).
    """
    blob = json.loads(text)
    strings = (
        blob.get(LANGUAGE_BLOB_STRINGS_KEY) if isinstance(blob, dict) else None
    )
    if not isinstance(strings, dict):
        return {}
    out: dict[str, str | StringSelector] = {}
    for name, value in strings.items():
        # A {'v': ..., 'w': ...} carrier (decision D-t) holds the value
        # plus its definition-time wrap hint; only the value matters
        # here (the native tables read the wrap themselves).
        if isinstance(value, dict) and 'v' in value:
            value = value['v']
        if isinstance(value, str):
            out[name] = value
        elif isinstance(value, dict):
            out[name] = dataclass_from_dict(StringSelector, value)
    return out


def parse_language_components(text: str) -> dict[str, str | StringSelector]:
    """Read the build-embedded formatter components out of a blob.

    Same value shapes as :func:`parse_language_blob` (plain ``str`` or
    :class:`StringSelector`), read from the sibling
    ``components`` key. Absent on any package with no spec'd params,
    and on every blob written before components existed -- both yield
    an empty map rather than an error.
    """
    blob = json.loads(text)
    comps = (
        blob.get(LANGUAGE_BLOB_COMPONENTS_KEY)
        if isinstance(blob, dict)
        else None
    )
    if not isinstance(comps, dict):
        return {}
    out: dict[str, str | StringSelector] = {}
    for name, value in comps.items():
        if isinstance(value, str):
            out[name] = value
        elif isinstance(value, dict):
            out[name] = dataclass_from_dict(StringSelector, value)
    return out


def parse_language_param_kinds(text: str) -> dict[str, dict[str, str]]:
    """Read the ``{name: {param: kind}}`` map out of a language blob.

    The display-side counterpart of ``param_kinds`` in
    :func:`serialize_language_blob`. Only strings carrying a non-text
    param appear; everything else is absent and reads as plain text
    substitution, which is what a blob written before this existed
    yields for every entry. Fail-soft throughout, matching
    :func:`parse_language_blob` -- a malformed entry is skipped rather
    than failing the whole blob.
    """
    blob = json.loads(text)
    strings = (
        blob.get(LANGUAGE_BLOB_STRINGS_KEY) if isinstance(blob, dict) else None
    )
    if not isinstance(strings, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for name, value in strings.items():
        if not isinstance(value, dict) or 'v' not in value:
            continue
        kinds = value.get('k')
        if not isinstance(kinds, dict):
            continue
        clean = {
            param: kind
            for param, kind in kinds.items()
            if isinstance(param, str) and isinstance(kind, str)
        }
        if clean:
            out[name] = clean
    return out
