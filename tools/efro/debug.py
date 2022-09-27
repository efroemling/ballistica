# Released under the MIT License. See LICENSE for details.
#
"""Utilities for debugging memory leaks or other issues."""
from __future__ import annotations

import gc
import sys
import types
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

ABS_MAX_LEVEL = 10

# NOTE: In general we want this toolset to allow us to explore
# which objects are holding references to others so we can diagnose
# leaks/etc. It is a bit tricky to do that, however, without
# affecting the objects we are looking at by adding temporary references
# from module dicts, function scopes, etc. So we need to try to be
# careful about cleaning up after ourselves and explicitly avoiding
# returning these temporary references wherever possible.

# A good test is running printrefs() repeatedly on some object that is
# known to be static. If the list of references changes or the id or any
# of the references, we're probably letting a temporary object sneak into
# the results and should fix it.


def getobjs(cls: type, contains: str | None = None) -> list[Any]:
    """Return all garbage-collected objects matching criteria.

    'type' can be an actual type or a string in which case objects
    whose types contain that string will be returned.

    If 'contains' is provided, objects will be filtered to those
    containing that in their str() representations.
    """

    # Don't wanna return stuff waiting to be garbage-collected.
    gc.collect()

    if not isinstance(cls, type | str):
        raise TypeError('Expected a type or string for cls')
    if not isinstance(contains, str | None):
        raise TypeError('Expected a string or None for contains')

    if isinstance(cls, str):
        objs = [o for o in gc.get_objects() if cls in str(type(o))]
    else:
        objs = [o for o in gc.get_objects() if isinstance(o, cls)]
    if contains is not None:
        objs = [o for o in objs if contains in str(o)]

    return objs


def getobj(objid: int) -> Any:
    """Return a garbage-collected object by its id.

    Remember that this is VERY inefficient and should only ever be used
    for debugging.
    """
    if not isinstance(objid, int):
        raise TypeError(f'Expected an int for objid; got a {type(objid)}.')

    # Don't wanna return stuff waiting to be garbage-collected.
    for obj in gc.get_objects():
        if id(obj) == objid:
            return obj
    raise RuntimeError(f'Object with id {objid} not found.')


def getrefs(obj: Any) -> list[Any]:
    """Given an object, return things referencing it."""
    v = vars()  # Ignore ref in locals.
    return [o for o in gc.get_referrers(obj) if o is not v]


def _desctype(obj: Any) -> str:
    cls = type(obj)
    if cls is types.ModuleType:
        return f'{type(obj).__name__} {obj.__name__}'
    if cls is types.MethodType:
        bnd = 'bound' if hasattr(obj, '__self__') else 'unbound'
        return f'{bnd} {type(obj).__name__} {obj.__name__}'
    return f'{type(obj).__name__}'


def _desc(obj: Any) -> str:
    extra: str | None = None
    if isinstance(obj, list | tuple):
        # Print length and the first few types.
        tps = [_desctype(i) for i in obj[:3]]
        tpsj = ', '.join(tps)
        tpss = (f', contains [{tpsj}, ...]'
                if len(obj) > 3 else f', contains [{tpsj}]' if tps else '')
        extra = f' (len {len(obj)}{tpss})'
    elif isinstance(obj, dict):
        # If it seems to be the vars() for a type or module,
        # try to identify what.
        for ref in getrefs(obj):
            if hasattr(ref, '__dict__') and vars(ref) is obj:
                extra = f' (vars for {_desctype(ref)} @ {id(ref)})'

        # Generic dict: print length and the first few key:type pairs.
        if extra is None:
            pairs = [
                f'{repr(n)}: {_desctype(v)}' for n, v in list(obj.items())[:3]
            ]
            pairsj = ', '.join(pairs)
            pairss = (f', contains {{{pairsj}, ...}}' if len(obj) > 3 else
                      f', contains {{{pairsj}}}' if pairs else '')
            extra = f' (len {len(obj)}{pairss})'
    if extra is None:
        extra = ''
    return f'{_desctype(obj)} @ {id(obj)}{extra}'


def _printrefs(obj: Any, level: int, max_level: int, exclude_objs: list,
               expand_ids: list[int]) -> None:
    ind = '  ' * level
    print(ind + _desc(obj), file=sys.stderr)
    v = vars()
    if level < max_level or (id(obj) in expand_ids and level < ABS_MAX_LEVEL):
        refs = getrefs(obj)
        for ref in refs:

            # It seems we tend to get a transient cell object with contents
            # set to obj. Would be nice to understand why that happens
            # but just ignoring it for now.
            if isinstance(ref, types.CellType) and ref.cell_contents is obj:
                continue

            # Ignore anything we were asked to ignore.
            if exclude_objs is not None:
                if any(ref is eobj for eobj in exclude_objs):
                    continue

            # Ignore references from our locals.
            if ref is v:
                continue

            # The 'refs' list we just made will be listed as a referrer
            # of this obj, so explicitly exclude it from the obj's listing.
            _printrefs(ref,
                       level=level + 1,
                       max_level=max_level,
                       exclude_objs=exclude_objs + [refs],
                       expand_ids=expand_ids)


def printrefs(obj: Any,
              max_level: int = 2,
              exclude_objs: list[Any] | None = None,
              expand_ids: list[int] | None = None) -> None:
    """Print human readable list of objects referring to an object.

    'max_level' specifies how many levels of recursion are printed.
    'exclude_objs' can be a list of exact objects to skip if found in the
      referrers list. This can be useful to avoid printing the local context
      where the object was passed in from (locals(), etc).
    'expand_ids' can be a list of object ids; if that particular object is
      found, it will always be expanded even if max_level has been reached.
    """
    _printrefs(obj,
               level=0,
               max_level=max_level,
               exclude_objs=[] if exclude_objs is None else exclude_objs,
               expand_ids=[] if expand_ids is None else expand_ids)
