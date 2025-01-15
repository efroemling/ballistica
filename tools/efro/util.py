# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Small handy bits of functionality."""

from __future__ import annotations

import os
import time
import random
import weakref
import functools
import datetime
from enum import Enum
from typing import TYPE_CHECKING, cast, TypeVar, Generic, overload, ParamSpec

if TYPE_CHECKING:
    import asyncio
    from typing import Any, Callable, Literal, Sequence

T = TypeVar('T')
ValT = TypeVar('ValT')
ArgT = TypeVar('ArgT')
SelfT = TypeVar('SelfT')
RetT = TypeVar('RetT')
EnumT = TypeVar('EnumT', bound=Enum)

P = ParamSpec('P')


class _EmptyObj:
    pass


# A dead weak-ref should be immutable, right? So we can create exactly
# one and return it for all cases that need an empty weak-ref.
_g_empty_weak_ref = weakref.ref(_EmptyObj())
assert _g_empty_weak_ref() is None

# Note to self: adding a special form of partial for when we don't need
# to pass further args/kwargs (which I think is most cases). Even though
# partial is now type-checked in Mypy (as of Nov 2024) there are still some
# pitfalls that this avoids (see func docs below). Perhaps it would make
# sense to simply define a Call class for this purpose; it might be more
# efficient than wrapping partial anyway (should test this).
if TYPE_CHECKING:

    def strict_partial(
        func: Callable[P, T], *args: P.args, **kwargs: P.kwargs
    ) -> Callable[[], T]:
        """A version of functools.partial requiring all args to be passed.

        This helps avoid pitfalls where a function is wrapped in a
        partial but then an extra required arg is added to the function
        but no type checking error is triggered at usage sites because
        vanilla partial assumes that extra arg will be provided at call
        time.

        Note: it would seem like this pitfall could also be avoided on
        the back end by ensuring that the thing accepting the partial
        asks for Callable[[], None] instead of just Callable, but as of
        Nov 2024 it seems that Mypy does not support this; it in fact
        allows partials to be passed for any callable signature(!).
        """
        ...

else:
    strict_partial = functools.partial


def explicit_bool(val: bool) -> bool:
    """Return a non-inferable boolean value.

    Useful to be able to disable blocks of code without type checkers
    complaining/etc.
    """
    # pylint: disable=no-else-return
    if TYPE_CHECKING:
        # infer this! <boom>
        return random.random() < 0.5
    else:
        return val


def snake_case_to_title(val: str) -> str:
    """Given a snake-case string 'foo_bar', returns 'Foo Bar'."""
    # Kill empty words resulting from leading/trailing/multiple underscores.
    return ' '.join(w for w in val.split('_') if w).title()


def snake_case_to_camel_case(val: str) -> str:
    """Given a snake-case string 'foo_bar', returns camel-case 'FooBar'."""
    # Replace underscores with spaces; capitalize words; kill spaces.
    # Not sure about efficiency, but logically simple.
    return val.replace('_', ' ').title().replace(' ', '')


def check_utc(value: datetime.datetime) -> None:
    """Ensure a datetime value is timezone-aware utc."""
    if value.tzinfo is not datetime.UTC:
        raise ValueError(
            'datetime value does not have timezone set as datetime.UTC'
        )


def utc_now() -> datetime.datetime:
    """Get timezone-aware current utc time.

    Just a shortcut for datetime.datetime.now(datetime.UTC).
    Avoid datetime.datetime.utcnow() which is deprecated and gives naive
    times.
    """
    return datetime.datetime.now(datetime.UTC)


def utc_now_naive() -> datetime.datetime:
    """Get naive utc time.

    This can be used to replace datetime.utcnow(), which is now deprecated.
    Most all code should migrate to use timezone-aware times instead of
    relying on this.
    """
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def utc_from_timestamp_naive(timestamp: float) -> datetime.datetime:
    """Get a naive utc time from a timestamp.

    This can be used to replace datetime.utcfromtimestamp(), which is now
    deprecated. Most all code should migrate to use timezone-aware times
    instead of relying on this.
    """

    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC).replace(
        tzinfo=None
    )


def utc_today() -> datetime.datetime:
    """Get offset-aware midnight in the utc time zone."""
    now = datetime.datetime.now(datetime.UTC)
    return datetime.datetime(
        year=now.year, month=now.month, day=now.day, tzinfo=now.tzinfo
    )


def utc_this_hour() -> datetime.datetime:
    """Get offset-aware beginning of the current hour in the utc time zone."""
    now = datetime.datetime.now(datetime.UTC)
    return datetime.datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        tzinfo=now.tzinfo,
    )


def utc_this_minute() -> datetime.datetime:
    """Get offset-aware beginning of current minute in the utc time zone."""
    now = datetime.datetime.now(datetime.UTC)
    return datetime.datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        tzinfo=now.tzinfo,
    )


def empty_weakref(objtype: type[T]) -> weakref.ref[T]:
    """Return an invalidated weak-reference for the specified type."""
    # At runtime, all weakrefs are the same; our type arg is just
    # for the static type checker.
    del objtype  # Unused.

    # Just create an object and let it die. Is there a cleaner way to do this?
    # return weakref.ref(_EmptyObj())  # type: ignore

    # Sharing a single ones seems at least a bit better.
    return _g_empty_weak_ref  # type: ignore


def data_size_str(bytecount: int, compact: bool = False) -> str:
    """Given a size in bytes, returns a short human readable string.

    In compact mode this should be 6 or fewer chars for most all
    sane file sizes.
    """
    # pylint: disable=too-many-return-statements

    # Special case: handle negatives.
    if bytecount < 0:
        val = data_size_str(-bytecount, compact=compact)
        return f'-{val}'

    if bytecount <= 999:
        suffix = 'B' if compact else 'bytes'
        return f'{bytecount} {suffix}'
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
        return f'{gbytecount:.1f} GB'
    return f'{gbytecount:.0f} GB'


class DirtyBit:
    """Manages whether a thing is dirty and regulates cleaning it.

    To use, simply set the 'dirty' value on this object to True when
    some update is needed, and then check the 'should_update' value to
    regulate when the actual update should occur. Set 'dirty' back to
    False after a successful update.

    If 'use_lock' is True, an asyncio Lock will be created and
    incorporated into update attempts to prevent simultaneous updates
    (should_update will only return True when the lock is unlocked).
    Note that It is up to the user to lock/unlock the lock during the
    actual update attempt.

    If a value is passed for 'auto_dirty_seconds', the dirtybit will
    flip itself back to dirty after being clean for the given amount of
    time.

    'min_update_interval' can be used to enforce a minimum update
    interval even when updates are successful (retry_interval only
    applies when updates fail)
    """

    def __init__(
        self,
        dirty: bool = False,
        retry_interval: float = 5.0,
        *,
        use_lock: bool = False,
        auto_dirty_seconds: float | None = None,
        min_update_interval: float | None = None,
    ):
        curtime = time.monotonic()
        self._retry_interval = retry_interval
        self._auto_dirty_seconds = auto_dirty_seconds
        self._min_update_interval = min_update_interval
        self._dirty = dirty
        self._next_update_time: float | None = curtime if dirty else None
        self._last_update_time: float | None = None
        self._next_auto_dirty_time: float | None = (
            (curtime + self._auto_dirty_seconds)
            if (not dirty and self._auto_dirty_seconds is not None)
            else None
        )
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
            self._next_auto_dirty_time = (
                time.monotonic() + self._auto_dirty_seconds
            )

        # If we're freshly dirty, schedule an immediate update.
        if not self._dirty and value:
            self._next_update_time = time.monotonic()

            # If they want to enforce a minimum update interval,
            # push out the next update time if it hasn't been long enough.
            if (
                self._min_update_interval is not None
                and self._last_update_time is not None
            ):
                self._next_update_time = max(
                    self._next_update_time,
                    self._last_update_time + self._min_update_interval,
                )

        self._dirty = value

    @property
    def should_update(self) -> bool:
        """Whether an attempt should be made to clean the target now.

        Always returns False if the target is not dirty.
        Takes into account the amount of time passed since the target
        was marked dirty or since should_update last returned True.
        """
        curtime = time.monotonic()

        # Auto-dirty ourself if we're into that.
        if (
            self._next_auto_dirty_time is not None
            and curtime > self._next_auto_dirty_time
        ):
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


class DispatchMethodWrapper(Generic[ArgT, RetT]):
    """Type-aware standin for the dispatch func returned by dispatchmethod."""

    def __call__(self, arg: ArgT) -> RetT:
        raise RuntimeError('Should not get here')

    @staticmethod
    def register(
        func: Callable[[Any, Any], RetT]
    ) -> Callable[[Any, Any], RetT]:
        """Register a new dispatch handler for this dispatch-method."""
        raise RuntimeError('Should not get here')

    registry: dict[Any, Callable]


# noinspection PyProtectedMember,PyTypeHints
def dispatchmethod(
    func: Callable[[Any, ArgT], RetT]
) -> DispatchMethodWrapper[ArgT, RetT]:
    """A variation of functools.singledispatch for methods.

    Note: as of Python 3.9 there is now functools.singledispatchmethod,
    but it currently (as of Jan 2021) is not type-aware (at least in mypy),
    which gives us a reason to keep this one around for now.
    """
    from functools import singledispatch, update_wrapper

    origwrapper: Any = singledispatch(func)

    # Pull this out so hopefully origwrapper can die,
    # otherwise we reference origwrapper in our wrapper.
    dispatch = origwrapper.dispatch

    # All we do here is recreate the end of functools.singledispatch
    # where it returns a wrapper except instead of the wrapper using the
    # first arg to the function ours uses the second (to skip 'self').
    # This was made against Python 3.7; we should probably check up on
    # this in later versions in case anything has changed.
    # (or hopefully they'll add this functionality to their version)
    # NOTE: sounds like we can use functools singledispatchmethod in 3.8
    def wrapper(*args: Any, **kw: Any) -> Any:
        if not args or len(args) < 2:
            raise TypeError(
                f'{funcname} requires at least ' '2 positional arguments'
            )

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


def valuedispatch(call: Callable[[ValT], RetT]) -> ValueDispatcher[ValT, RetT]:
    """Decorator for functions to allow dispatching based on a value.

    This differs from functools.singledispatch in that it dispatches based
    on the value of an argument, not based on its type.
    The 'register' method of a value-dispatch function can be used
    to assign new functions to handle particular values.
    Unhandled values wind up in the original dispatch function."""
    return ValueDispatcher(call)


class ValueDispatcher(Generic[ValT, RetT]):
    """Used by the valuedispatch decorator"""

    def __init__(self, call: Callable[[ValT], RetT]) -> None:
        self._base_call = call
        self._handlers: dict[ValT, Callable[[], RetT]] = {}

    def __call__(self, value: ValT) -> RetT:
        handler = self._handlers.get(value)
        if handler is not None:
            return handler()
        return self._base_call(value)

    def _add_handler(
        self, value: ValT, call: Callable[[], RetT]
    ) -> Callable[[], RetT]:
        if value in self._handlers:
            raise RuntimeError(f'Duplicate handlers added for {value}')
        self._handlers[value] = call
        return call

    def register(
        self, value: ValT
    ) -> Callable[[Callable[[], RetT]], Callable[[], RetT]]:
        """Add a handler to the dispatcher."""
        from functools import partial

        return partial(self._add_handler, value)


def valuedispatch1arg(
    call: Callable[[ValT, ArgT], RetT]
) -> ValueDispatcher1Arg[ValT, ArgT, RetT]:
    """Like valuedispatch but for functions taking an extra argument."""
    return ValueDispatcher1Arg(call)


class ValueDispatcher1Arg(Generic[ValT, ArgT, RetT]):
    """Used by the valuedispatch1arg decorator"""

    def __init__(self, call: Callable[[ValT, ArgT], RetT]) -> None:
        self._base_call = call
        self._handlers: dict[ValT, Callable[[ArgT], RetT]] = {}

    def __call__(self, value: ValT, arg: ArgT) -> RetT:
        handler = self._handlers.get(value)
        if handler is not None:
            return handler(arg)
        return self._base_call(value, arg)

    def _add_handler(
        self, value: ValT, call: Callable[[ArgT], RetT]
    ) -> Callable[[ArgT], RetT]:
        if value in self._handlers:
            raise RuntimeError(f'Duplicate handlers added for {value}')
        self._handlers[value] = call
        return call

    def register(
        self, value: ValT
    ) -> Callable[[Callable[[ArgT], RetT]], Callable[[ArgT], RetT]]:
        """Add a handler to the dispatcher."""
        from functools import partial

        return partial(self._add_handler, value)


if TYPE_CHECKING:

    class ValueDispatcherMethod(Generic[ValT, RetT]):
        """Used by the valuedispatchmethod decorator."""

        def __call__(self, value: ValT) -> RetT: ...

        def register(
            self, value: ValT
        ) -> Callable[[Callable[[SelfT], RetT]], Callable[[SelfT], RetT]]:
            """Add a handler to the dispatcher."""
            ...


def valuedispatchmethod(
    call: Callable[[SelfT, ValT], RetT]
) -> ValueDispatcherMethod[ValT, RetT]:
    """Like valuedispatch but works with methods instead of functions."""

    # NOTE: It seems that to wrap a method with a decorator and have self
    # dispatching do the right thing, we must return a function and not
    # an executable object. So for this version we store our data here
    # in the function call dict and simply return a call.

    _base_call = call
    _handlers: dict[ValT, Callable[[SelfT], RetT]] = {}

    def _add_handler(value: ValT, addcall: Callable[[SelfT], RetT]) -> None:
        if value in _handlers:
            raise RuntimeError(f'Duplicate handlers added for {value}')
        _handlers[value] = addcall

    def _register(value: ValT) -> Callable[[Callable[[SelfT], RetT]], None]:
        from functools import partial

        return partial(_add_handler, value)

    def _call_wrapper(self: SelfT, value: ValT) -> RetT:
        handler = _handlers.get(value)
        if handler is not None:
            return handler(self)
        return _base_call(self, value)

    # We still want to use our returned object to register handlers, but we're
    # actually just returning a function. So manually stuff the call onto it.
    setattr(_call_wrapper, 'register', _register)

    # To the type checker's eyes we return a ValueDispatchMethod instance;
    # this lets it know about our register func and type-check its usage.
    # In reality we just return a raw function call (for reasons listed above).
    # pylint: disable=undefined-variable, no-else-return
    if TYPE_CHECKING:
        return ValueDispatcherMethod[ValT, RetT]()
    else:
        return _call_wrapper


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
        return hash(tuple(make_hash(e) for e in obj))
    if not isinstance(obj, dict):
        return hash(obj)

    new_obj = copy.deepcopy(obj)
    for k, v in new_obj.items():
        new_obj[k] = make_hash(v)

    # NOTE: there is sorted works correctly because it compares only
    # unique first values (i.e. dict keys)
    return hash(tuple(frozenset(sorted(new_obj.items()))))


def float_hash_from_string(s: str) -> float:
    """Given a string value, returns a float between 0 and 1.

    If consistent across processes. Can be useful for assigning db ids
    shard values for efficient parallel processing.
    """
    import hashlib

    hash_bytes = hashlib.md5(s.encode()).digest()

    # Generate a random 64 bit int from hash digest bytes.
    ival = int.from_bytes(hash_bytes[:8])
    return ival / ((1 << 64) - 1)


def asserttype(obj: Any, typ: type[T]) -> T:
    """Return an object typed as a given type.

    Assert is used to check its actual type, so only use this when
    failures are not expected. Otherwise use checktype.
    """
    assert isinstance(typ, type), 'only actual types accepted'
    assert isinstance(obj, typ)
    return obj


def asserttype_o(obj: Any, typ: type[T]) -> T | None:
    """Return an object typed as a given optional type.

    Assert is used to check its actual type, so only use this when
    failures are not expected. Otherwise use checktype.
    """
    assert isinstance(typ, type), 'only actual types accepted'
    assert isinstance(obj, (typ, type(None)))
    return obj


def checktype(obj: Any, typ: type[T]) -> T:
    """Return an object typed as a given type.

    Always checks the type at runtime with isinstance and throws a TypeError
    on failure. Use asserttype for more efficient (but less safe) equivalent.
    """
    assert isinstance(typ, type), 'only actual types accepted'
    if not isinstance(obj, typ):
        raise TypeError(f'Expected a {typ}; got a {type(obj)}.')
    return obj


def checktype_o(obj: Any, typ: type[T]) -> T | None:
    """Return an object typed as a given optional type.

    Always checks the type at runtime with isinstance and throws a TypeError
    on failure. Use asserttype for more efficient (but less safe) equivalent.
    """
    assert isinstance(typ, type), 'only actual types accepted'
    if not isinstance(obj, (typ, type(None))):
        raise TypeError(f'Expected a {typ} or None; got a {type(obj)}.')
    return obj


def warntype(obj: Any, typ: type[T]) -> T:
    """Return an object typed as a given type.

    Always checks the type at runtime and simply logs a warning if it is
    not what is expected.
    """
    assert isinstance(typ, type), 'only actual types accepted'
    if not isinstance(obj, typ):
        import logging

        logging.warning('warntype: expected a %s, got a %s', typ, type(obj))
    return obj  # type: ignore


def warntype_o(obj: Any, typ: type[T]) -> T | None:
    """Return an object typed as a given type.

    Always checks the type at runtime and simply logs a warning if it is
    not what is expected.
    """
    assert isinstance(typ, type), 'only actual types accepted'
    if not isinstance(obj, (typ, type(None))):
        import logging

        logging.warning(
            'warntype: expected a %s or None, got a %s', typ, type(obj)
        )
    return obj  # type: ignore


def assert_non_optional(obj: T | None) -> T:
    """Return an object with Optional typing removed.

    Assert is used to check its actual type, so only use this when
    failures are not expected. Use check_non_optional otherwise.
    """
    assert obj is not None
    return obj


def check_non_optional(obj: T | None) -> T:
    """Return an object with Optional typing removed.

    Always checks the actual type and throws a TypeError on failure.
    Use assert_non_optional for a more efficient (but less safe) equivalent.
    """
    if obj is None:
        raise ValueError('Got None value in check_non_optional.')
    return obj


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """A smooth transition function.

    Returns a value that smoothly moves from 0 to 1 as we go between edges.
    Values outside of the range return 0 or 1.
    """
    y = min(1.0, max(0.0, (x - edge0) / (edge1 - edge0)))
    return y * y * (3.0 - 2.0 * y)


def linearstep(edge0: float, edge1: float, x: float) -> float:
    """A linear transition function.

    Returns a value that linearly moves from 0 to 1 as we go between edges.
    Values outside of the range return 0 or 1.
    """
    return max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))


def _compact_id(num: int, chars: str) -> str:
    if num < 0:
        raise ValueError('Negative integers not allowed.')

    # Chars must be in sorted order for sorting to work correctly
    # on our output.
    assert ''.join(sorted(list(chars))) == chars

    base = len(chars)
    out = ''
    while num:
        out += chars[num % base]
        num //= base
    return out[::-1] or '0'


def human_readable_compact_id(num: int) -> str:
    """Given a positive int, return a compact string representation for it.

    Handy for visualizing unique numeric ids using as few as possible chars.
    This representation uses only lowercase letters and numbers (minus the
    following letters for readability):
     's' is excluded due to similarity to '5'.
     'l' is excluded due to similarity to '1'.
     'i' is excluded due to similarity to '1'.
     'o' is excluded due to similarity to '0'.
     'z' is excluded due to similarity to '2'.

    Therefore for n chars this can store values of 21^n.

    When reading human input consisting of these IDs, it may be desirable
    to map the disallowed chars to their corresponding allowed ones
    ('o' -> '0', etc).

    Sort order for these ids is the same as the original numbers.

    If more compactness is desired at the expense of readability,
    use compact_id() instead.
    """
    return _compact_id(num, '0123456789abcdefghjkmnpqrtuvwxy')


def compact_id(num: int) -> str:
    """Given a positive int, return a compact string representation for it.

    Handy for visualizing unique numeric ids using as few as possible chars.
    This version is more compact than human_readable_compact_id() but less
    friendly to humans due to using both capital and lowercase letters,
    both 'O' and '0', etc.

    Therefore for n chars this can store values of 62^n.

    Sort order for these ids is the same as the original numbers.
    """
    return _compact_id(
        num, '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    )


def caller_source_location() -> str:
    """Returns source file name and line of the code calling us.

    Example: 'mymodule.py:23'
    """
    try:
        import inspect

        frame = inspect.currentframe()
        for _i in range(2):
            if frame is None:
                raise RuntimeError()
            frame = frame.f_back
        if frame is None:
            raise RuntimeError()
        fname = os.path.basename(frame.f_code.co_filename)
        return f'{fname}:{frame.f_lineno}'
    except Exception:
        return '<unknown source location>'


def unchanging_hostname() -> str:
    """Return an unchanging name for the local device.

    Similar to the `hostname` call (or os.uname().nodename in Python)
    except attempts to give a name that doesn't change depending on
    network conditions. (A Mac will tend to go from Foo to Foo.local,
    Foo.lan etc. throughout its various adventures)
    """
    import platform
    import subprocess

    # On Mac, this should give the computer name assigned in System Prefs.
    if platform.system() == 'Darwin':
        return (
            subprocess.run(
                ['scutil', '--get', 'ComputerName'],
                check=True,
                capture_output=True,
            )
            .stdout.decode()
            .strip()
            .replace(' ', '-')
        )
    return os.uname().nodename


def set_canonical_module_names(module_globals: dict[str, Any]) -> None:
    """Do the thing."""
    if os.environ.get('EFRO_SUPPRESS_SET_CANONICAL_MODULE_NAMES') == '1':
        return

    modulename = module_globals.get('__name__')
    if not isinstance(modulename, str):
        raise RuntimeError('Unable to get module name.')
    assert not modulename.startswith('_')
    modulename_prefix = f'{modulename}.'
    modulename_prefix_2 = f'_{modulename}.'

    for name, obj in module_globals.items():
        if name.startswith('_'):
            continue
        existing = getattr(obj, '__module__', None)
        try:
            # Override the module ONLY if it lives under us somewhere.
            # So ourpackage._submodule.Foo becomes ourpackage.Foo
            # but otherpackage._submodule.Foo remains untouched.
            if existing is not None and (
                existing.startswith(modulename_prefix)
                or existing.startswith(modulename_prefix_2)
            ):
                obj.__module__ = modulename
        except Exception:
            import logging

            logging.warning(
                'set_canonical_module_names: unable to change __module__'
                " from '%s' to '%s' on %s object at '%s'.",
                existing,
                modulename,
                type(obj),
                name,
            )


def timedelta_str(
    timeval: datetime.timedelta | float, maxparts: int = 2, decimals: int = 0
) -> str:
    """Return a simple human readable time string for a length of time.

    Time can be given as a timedelta or a float representing seconds.
    Example output:
      "23d 1h 2m 32s" (with maxparts == 4)
      "23d 1h" (with maxparts == 2)
      "23d 1.08h" (with maxparts == 2 and decimals == 2)

    Note that this is hard-coded in English and probably not especially
    performant.
    """
    # pylint: disable=too-many-locals

    if isinstance(timeval, float):
        timevalfin = datetime.timedelta(seconds=timeval)
    else:
        timevalfin = timeval

    # Internally we only handle positive values.
    if timevalfin.total_seconds() < 0:
        return f'-{timedelta_str(timeval=-timeval, maxparts=maxparts)}'

    years = timevalfin.days // 365
    days = timevalfin.days % 365
    hours = timevalfin.seconds // 3600
    hour_remainder = timevalfin.seconds % 3600
    minutes = hour_remainder // 60
    seconds = hour_remainder % 60

    # Now, if we want decimal places for our last value,
    # calc fractional parts.
    if decimals:
        # Calc totals of each type.
        t_seconds = timevalfin.total_seconds()
        t_minutes = t_seconds / 60
        t_hours = t_minutes / 60
        t_days = t_hours / 24
        t_years = t_days / 365

        # Calc fractional parts that exclude all whole values to their left.
        years_covered = years
        years_f = t_years - years_covered
        days_covered = years_covered * 365 + days
        days_f = t_days - days_covered
        hours_covered = days_covered * 24 + hours
        hours_f = t_hours - hours_covered
        minutes_covered = hours_covered * 60 + minutes
        minutes_f = t_minutes - minutes_covered
        seconds_covered = minutes_covered * 60 + seconds
        seconds_f = t_seconds - seconds_covered
    else:
        years_f = days_f = hours_f = minutes_f = seconds_f = 0.0

    parts: list[str] = []
    for part, part_f, suffix in (
        (years, years_f, 'y'),
        (days, days_f, 'd'),
        (hours, hours_f, 'h'),
        (minutes, minutes_f, 'm'),
        (seconds, seconds_f, 's'),
    ):
        if part or parts or (not parts and suffix == 's'):
            # Do decimal version only for the last part.
            if decimals and (len(parts) >= maxparts - 1 or suffix == 's'):
                parts.append(f'{part+part_f:.{decimals}f}{suffix}')
            else:
                parts.append(f'{part}{suffix}')
            if len(parts) >= maxparts:
                break
    return ' '.join(parts)


def ago_str(
    timeval: datetime.datetime,
    maxparts: int = 1,
    now: datetime.datetime | None = None,
    decimals: int = 0,
) -> str:
    """Given a datetime, return a clean human readable 'ago' str.

    Note that this is hard-coded in English so should not be used
    for visible in-game elements; only tools/etc.

    If now is not passed, efro.util.utc_now() is used.
    """
    if now is None:
        now = utc_now()
    return (
        timedelta_str(now - timeval, maxparts=maxparts, decimals=decimals)
        + ' ago'
    )


def split_list(input_list: list[T], max_length: int) -> list[list[T]]:
    """Split a single list into smaller lists."""
    return [
        input_list[i : i + max_length]
        for i in range(0, len(input_list), max_length)
    ]


def extract_flag(args: list[str], name: str) -> bool:
    """Given a list of args and a flag name, returns whether it is present.

    The arg flag, if present, is removed from the arg list.
    """
    from efro.error import CleanError

    count = args.count(name)
    if count > 1:
        raise CleanError(f'Flag {name} passed multiple times.')
    if not count:
        return False
    args.remove(name)
    return True


@overload
def extract_arg(
    args: list[str], name: str, required: Literal[False] = False
) -> str | None: ...


@overload
def extract_arg(args: list[str], name: str, required: Literal[True]) -> str: ...


def extract_arg(
    args: list[str], name: str, required: bool = False
) -> str | None:
    """Given a list of args and an arg name, returns a value.

    The arg flag and value are removed from the arg list.
    raises CleanErrors on any problems.
    """
    from efro.error import CleanError

    count = args.count(name)
    if not count:
        if required:
            raise CleanError(f'Required argument {name} not passed.')
        return None

    if count > 1:
        raise CleanError(f'Arg {name} passed multiple times.')

    argindex = args.index(name)
    if argindex + 1 >= len(args):
        raise CleanError(f'No value passed after {name} arg.')

    val = args[argindex + 1]
    del args[argindex : argindex + 2]

    return val


def pairs_to_flat(pairs: Sequence[tuple[T, T]]) -> list[T]:
    """Given a sequence of same-typed pairs, flattens to a list."""
    return [item for pair in pairs for item in pair]


def pairs_from_flat(flat: Sequence[T]) -> list[tuple[T, T]]:
    """Given a flat even numbered sequence, returns pairs."""
    if len(flat) % 2 != 0:
        raise ValueError('Provided sequence has an odd number of elements.')
    out: list[tuple[T, T]] = []
    for i in range(0, len(flat) - 1, 2):
        out.append((flat[i], flat[i + 1]))
    return out


def weighted_choice(*args: tuple[T, float]) -> T:
    """Given object/weight pairs as args, returns a random object.

    Intended as a shorthand way to call random.choices on a few explicit
    options.
    """
    items: tuple[T]
    weights: tuple[float]
    items, weights = zip(*args)
    return random.choices(items, weights=weights)[0]
