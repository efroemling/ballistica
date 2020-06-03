# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Small handy bits of functionality."""

from __future__ import annotations

import datetime
import time
import weakref
from typing import TYPE_CHECKING, cast, TypeVar, Generic

if TYPE_CHECKING:
    import asyncio
    from weakref import ReferenceType
    from typing import Any, Dict, Callable, Optional, Type

T = TypeVar('T')
TVAL = TypeVar('TVAL')
TARG = TypeVar('TARG')
TRET = TypeVar('TRET')


class _EmptyObj:
    pass


def utc_now() -> datetime.datetime:
    """Get offset-aware current utc time.

    This should be used for all datetimes getting sent over the network,
    used with the entity system, etc.
    (datetime.utcnow() gives a utc time value, but it is not timezone-aware
    which makes it less safe to use)
    """
    return datetime.datetime.now(datetime.timezone.utc)


# noinspection PyUnresolvedReferences
def empty_weakref(objtype: Type[T]) -> ReferenceType[T]:
    """Return an invalidated weak-reference for the specified type."""
    # At runtime, all weakrefs are the same; our type arg is just
    # for the static type checker.
    del objtype  # Unused.
    # Just create an object and let it die. Is there a cleaner way to do this?
    return weakref.ref(_EmptyObj())  # type: ignore


def data_size_str(bytecount: int) -> str:
    """Given a size in bytes, returns a short human readable string.

    This should be 6 or fewer chars for most all sane file sizes.
    """
    # pylint: disable=too-many-return-statements
    if bytecount <= 999:
        return f'{bytecount} B'
    kbytecount = bytecount / 1024
    if round(kbytecount, 1) < 10.0:
        return f'{kbytecount:.1f} KB'
    if round(kbytecount, 0) < 999:
        return f'{kbytecount:.0f} KB'
    mbytecount = bytecount / (1024 * 1024)
    if round(mbytecount, 1) < 10.0:
        return f'{mbytecount:.1f} MB'
    if round(mbytecount, 0) < 999:
        return f'{mbytecount:.0f} MB'
    gbytecount = bytecount / (1024 * 1024 * 1024)
    if round(gbytecount, 1) < 10.0:
        return f'{mbytecount:.1f} GB'
    return f'{gbytecount:.0f} GB'


class DispatchMethodWrapper(Generic[TARG, TRET]):
    """Type-aware standin for the dispatch func returned by dispatchmethod."""

    def __call__(self, arg: TARG) -> TRET:
        pass

    @staticmethod
    def register(func: Callable[[Any, Any], TRET]) -> Callable:
        """Register a new dispatch handler for this dispatch-method."""

    registry: Dict[Any, Callable]


# noinspection PyProtectedMember,PyTypeHints
def dispatchmethod(
        func: Callable[[Any, TARG],
                       TRET]) -> DispatchMethodWrapper[TARG, TRET]:
    """A variation of functools.singledispatch for methods."""
    from functools import singledispatch, update_wrapper
    origwrapper: Any = singledispatch(func)

    # Pull this out so hopefully origwrapper can die,
    # otherwise we reference origwrapper in our wrapper.
    dispatch = origwrapper.dispatch

    # All we do here is recreate the end of functools.singledispatch
    # where it returns a wrapper except instead of the wrapper using the
    # first arg to the function ours uses the second (to skip 'self').
    # This was made with Python 3.7; we should probably check up on
    # this in later versions in case anything has changed.
    # (or hopefully they'll add this functionality to their version)
    def wrapper(*args: Any, **kw: Any) -> Any:
        if not args or len(args) < 2:
            raise TypeError(f'{funcname} requires at least '
                            '2 positional arguments')

        return dispatch(args[1].__class__)(*args, **kw)

    funcname = getattr(func, '__name__', 'dispatchmethod method')
    wrapper.register = origwrapper.register  # type: ignore
    wrapper.dispatch = dispatch  # type: ignore
    wrapper.registry = origwrapper.registry  # type: ignore
    # pylint: disable=protected-access
    wrapper._clear_cache = origwrapper._clear_cache  # type: ignore
    update_wrapper(wrapper, func)
    # pylint: enable=protected-access
    return cast(DispatchMethodWrapper, wrapper)


class DirtyBit:
    """Manages whether a thing is dirty and regulates attempts to clean it.

    To use, simply set the 'dirty' value on this object to True when some
    action is needed, and then check the 'should_update' value to regulate
    when attempts to clean it should be made. Set 'dirty' back to False after
    a successful update.
    If 'use_lock' is True, an asyncio Lock will be created and incorporated
    into update attempts to prevent simultaneous updates (should_update will
    only return True when the lock is unlocked). Note that It is up to the user
    to lock/unlock the lock during the actual update attempt.
    If a value is passed for 'auto_dirty_seconds', the dirtybit will flip
    itself back to dirty after being clean for the given amount of time.
    'min_update_interval' can be used to enforce a minimum update
    interval even when updates are successful (retry_interval only applies
    when updates fail)
    """

    def __init__(self,
                 dirty: bool = False,
                 retry_interval: float = 5.0,
                 use_lock: bool = False,
                 auto_dirty_seconds: float = None,
                 min_update_interval: Optional[float] = None):
        curtime = time.time()
        self._retry_interval = retry_interval
        self._auto_dirty_seconds = auto_dirty_seconds
        self._min_update_interval = min_update_interval
        self._dirty = dirty
        self._next_update_time: Optional[float] = (curtime if dirty else None)
        self._last_update_time: Optional[float] = None
        self._next_auto_dirty_time: Optional[float] = (
            (curtime + self._auto_dirty_seconds) if
            (not dirty and self._auto_dirty_seconds is not None) else None)
        self._use_lock = use_lock
        self.lock: asyncio.Lock
        if self._use_lock:
            import asyncio
            self.lock = asyncio.Lock()

    @property
    def dirty(self) -> bool:
        """Whether the target is currently dirty.

        This should be set to False once an update is successful.
        """
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:

        # If we're freshly clean, set our next auto-dirty time (if we have
        # one).
        if self._dirty and not value and self._auto_dirty_seconds is not None:
            self._next_auto_dirty_time = time.time() + self._auto_dirty_seconds

        # If we're freshly dirty, schedule an immediate update.
        if not self._dirty and value:
            self._next_update_time = time.time()

            # If they want to enforce a minimum update interval,
            # push out the next update time if it hasn't been long enough.
            if (self._min_update_interval is not None
                    and self._last_update_time is not None):
                self._next_update_time = max(
                    self._next_update_time,
                    self._last_update_time + self._min_update_interval)

        self._dirty = value

    @property
    def should_update(self) -> bool:
        """Whether an attempt should be made to clean the target now.

        Always returns False if the target is not dirty.
        Takes into account the amount of time passed since the target
        was marked dirty or since should_update last returned True.
        """
        curtime = time.time()

        # Auto-dirty ourself if we're into that.
        if (self._next_auto_dirty_time is not None
                and curtime > self._next_auto_dirty_time):
            self.dirty = True
            self._next_auto_dirty_time = None
        if not self._dirty:
            return False
        if self._use_lock and self.lock.locked():
            return False
        assert self._next_update_time is not None
        if curtime > self._next_update_time:
            self._next_update_time = curtime + self._retry_interval
            self._last_update_time = curtime
            return True
        return False


def valuedispatch(call: Callable[[TVAL], TRET]) -> ValueDispatcher[TVAL, TRET]:
    """Decorator for functions to allow dispatching based on a value.

    The 'register' method of a value-dispatch function can be used
    to assign new functions to handle particular values.
    Unhandled values wind up in the original dispatch function."""
    return ValueDispatcher(call)


class ValueDispatcher(Generic[TVAL, TRET]):
    """Used by the valuedispatch decorator"""

    def __init__(self, call: Callable[[TVAL], TRET]) -> None:
        self._base_call = call
        self._handlers: Dict[TVAL, Callable[[], TRET]] = {}

    def __call__(self, value: TVAL) -> TRET:
        handler = self._handlers.get(value)
        if handler is not None:
            return handler()
        return self._base_call(value)

    def _add_handler(self, value: TVAL, call: Callable[[], TRET]) -> None:
        if value in self._handlers:
            raise RuntimeError(f'Duplicate handlers added for {value}')
        self._handlers[value] = call

    def register(self, value: TVAL) -> Callable[[Callable[[], TRET]], None]:
        """Add a handler to the dispatcher."""
        from functools import partial
        return partial(self._add_handler, value)


def valuedispatch1arg(
    call: Callable[[TVAL, TARG],
                   TRET]) -> ValueDispatcher1Arg[TVAL, TARG, TRET]:
    """Like valuedispatch but for functions taking an extra argument."""
    return ValueDispatcher1Arg(call)


class ValueDispatcher1Arg(Generic[TVAL, TARG, TRET]):
    """Used by the valuedispatch1arg decorator"""

    def __init__(self, call: Callable[[TVAL, TARG], TRET]) -> None:
        self._base_call = call
        self._handlers: Dict[TVAL, Callable[[TARG], TRET]] = {}

    def __call__(self, value: TVAL, arg: TARG) -> TRET:
        handler = self._handlers.get(value)
        if handler is not None:
            return handler(arg)
        return self._base_call(value, arg)

    def _add_handler(self, value: TVAL, call: Callable[[TARG], TRET]) -> None:
        if value in self._handlers:
            raise RuntimeError(f'Duplicate handlers added for {value}')
        self._handlers[value] = call

    def register(self,
                 value: TVAL) -> Callable[[Callable[[TARG], TRET]], None]:
        """Add a handler to the dispatcher."""
        from functools import partial
        return partial(self._add_handler, value)


def make_hash(obj: Any) -> int:
    """Makes a hash from a dictionary, list, tuple or set to any level,
    that contains only other hashable types (including any lists, tuples,
    sets, and dictionaries).

    Note that this uses Python's hash() function internally so collisions/etc.
    may be more common than with fancy cryptographic hashes.

    Also be aware that Python's hash() output varies across processes, so
    this should only be used for values that will remain in a single process.
    """
    import copy

    if isinstance(obj, (set, tuple, list)):
        return hash(tuple([make_hash(e) for e in obj]))
    if not isinstance(obj, dict):
        return hash(obj)

    new_obj = copy.deepcopy(obj)
    for k, v in new_obj.items():
        new_obj[k] = make_hash(v)

    # NOTE: there is sorted works correctly because it compares only
    # unique first values (i.e. dict keys)
    return hash(tuple(frozenset(sorted(new_obj.items()))))
