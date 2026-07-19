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


def serialize_language_blob(
    values: dict[str, str | StringSelector],
    wraps: 'dict[str, WrapParams] | None' = None,
) -> str:
    """Serialize a per-locale value map to the canonical language blob.

    ``values`` maps each string's logical name to its value -- a plain
    ``str`` or a :class:`StringSelector`. ``wraps`` optionally maps
    names to their definition-time :class:`WrapParams` (decision D-t);
    a wrapped entry is emitted as a ``{'v': value, 'w': wrap}`` carrier
    dict (which pre-wrap clients skip fail-soft). Output is
    deterministic (sorted keys, fixed formatting) for cache stability
    and diffability.
    """

    def _encode(name: str, value: str | StringSelector) -> object:
        out: object = (
            dataclass_to_dict(value)
            if isinstance(value, StringSelector)
            else value
        )
        wrap = None if wraps is None else wraps.get(name)
        if wrap is not None:
            out = {'v': out, 'w': dataclass_to_dict(wrap)}
        return out

    return json.dumps(
        {
            LANGUAGE_BLOB_STRINGS_KEY: {
                name: _encode(name, value) for name, value in values.items()
            }
        },
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
