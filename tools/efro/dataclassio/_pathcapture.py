# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to capturing nested dataclass paths."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from efro.dataclassio._base import _parse_annotated, _get_origin
from efro.dataclassio._prep import PrepSession

if TYPE_CHECKING:
    from typing import Any, Dict, Type, Tuple, Optional, List, Set


class FieldStoragePathCapture:
    """Utility for obtaining dataclass storage paths in a type safe way.

    Given dataclass instance foo, FieldStoragePathCapture(foo).bar.eep
    will return 'bar.eep' (or something like 'b.e' if storagenames are
    overridden). This can be combined with type-checking tricks that
    return foo in the type-checker's eyes while returning
    FieldStoragePathCapture(foo) at runtime in order to grant a measure
    of type safety to specifying field paths for things such as db
    queries. Be aware, however, that the type-checker will incorrectly
    think these lookups are returning actual attr values when they
    are actually returning strings.
    """

    def __init__(self, obj: Any, path: List[str] = None):
        if path is None:
            path = []
        if not dataclasses.is_dataclass(obj):
            raise TypeError(f'Expected a dataclass type/instance;'
                            f' got {type(obj)}.')
        self._cls = obj if isinstance(obj, type) else type(obj)
        self._path = path

    def __getattr__(self, name: str) -> Any:
        prep = PrepSession(explicit=False).prep_dataclass(self._cls,
                                                          recursion_level=0)
        try:
            anntype = prep.annotations[name]
        except KeyError as exc:
            raise AttributeError(f'{type(self)} has no {name} field.') from exc
        anntype, ioattrs = _parse_annotated(anntype)
        storagename = (name if (ioattrs is None or ioattrs.storagename is None)
                       else ioattrs.storagename)
        origin = _get_origin(anntype)
        path = self._path + [storagename]

        if dataclasses.is_dataclass(origin):
            return FieldStoragePathCapture(origin, path=path)
        return '.'.join(path)
