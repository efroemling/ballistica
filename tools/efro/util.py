# Released under the MIT License. See LICENSE for details.
#
"""Small handy bits of functionality."""

from __future__ import annotations

import os
import time
import weakref
import datetime
import functools
from enum import Enum
from typing import TYPE_CHECKING, cast, TypeVar, Generic

_pytz_utc: Any

# We don't *require* pytz, but we want to support it for tzinfos if available.
try:
    import pytz

    _pytz_utc = pytz.utc
except ModuleNotFoundError:
    _pytz_utc = None  # pylint: disable=invalid-name

if TYPE_CHECKING:
    import asyncio
    from efro.call import Call as Call  # 'as Call' so we re-export.
    from typing import Any, Callable, NoReturn

T = TypeVar('T')
ValT = TypeVar('ValT')
ArgT = TypeVar('ArgT')
SelfT = TypeVar('SelfT')
RetT = TypeVar('RetT')
EnumT = TypeVar('EnumT', bound=Enum)


class _EmptyObj:
    pass


# TODO: kill this and just use efro.call.tpartial
if TYPE_CHECKING:
    Call = Call
else:
    Call = functools.partial


def enum_by_value(cls: type[EnumT], value: Any) -> EnumT:
    """Create an enum from a value.

    This is basically the same as doing 'obj = EnumType(value)' except
    that it works around an issue where a reference loop is created
    if an exception is thrown due to an invalid value. Since we disable
    the cyclic garbage collector for most of the time, such loops can lead
    to our objects sticking around longer than we want.
    This issue has been submitted to Python as a bug so hopefully we can
    remove this eventually if it gets fixed: https://bugs.python.org/issue42248
    UPDATE: This has been fixed as of later 3.8 builds, so we can kill this
    off once we are 3.9+ across the board.
    """

    # Note: we don't recreate *ALL* the functionality of the Enum constructor
    # such as the _missing_ hook; but this should cover our basic needs.
    value2member_map = getattr(cls, '_value2member_map_')
    assert value2member_map is not None
    try:
        out = value2member_map[value]
        assert isinstance(out, cls)
        return out
    except KeyError:
        # pylint: disable=consider-using-f-string
        raise ValueError(
            '%r is not a valid %s' % (value, cls.__name__)
        ) from None


def check_utc(value: datetime.datetime) -> None:
    """Ensure a datetime value is timezone-aware utc."""
    if value.tzinfo is not datetime.timezone.utc and (
        _pytz_utc is None or value.tzinfo is not _pytz_utc
    ):
        raise ValueError(
            'datetime value does not have timezone set as'
            ' datetime.timezone.utc'
        )


def utc_now() -> datetime.datetime:
    """Get offset-aware current utc time.

    This should be used for all datetimes getting sent over the network,
    used with the entity system, etc.
    (datetime.utcnow() gives a utc time value, but it is not timezone-aware
    which makes it less safe to use)
    """
    return datetime.datetime.now(datetime.timezone.utc)


def utc_today() -> datetime.datetime:
    """Get offset-aware midnight in the utc time zone."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return datetime.datetime(
        year=now.year, month=now.month, day=now.day, tzinfo=now.tzinfo
    )


def utc_this_hour() -> datetime.datetime:
    """Get offset-aware beginning of the current hour in the utc time zone."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return datetime.datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        tzinfo=now.tzinfo,
    )


def utc_this_minute() -> datetime.datetime:
    """Get offset-aware beginning of current minute in the utc time zone."""
    now = datetime.datetime.now(datetime.timezone.utc)
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

    def __init__(
        self,
        dirty: bool = False,
        retry_interval: float = 5.0,
        use_lock: bool = False,
        auto_dirty_seconds: float | None = None,
        min_update_interval: float | None = None,
    ):
        curtime = time.time()
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
            self._next_auto_dirty_time = time.time() + self._auto_dirty_seconds

        # If we're freshly dirty, schedule an immediate update.
        if not self._dirty and value:
            self._next_update_time = time.time()

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
        curtime = time.time()

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

        def __call__(self, value: ValT) -> RetT:
            ...

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
        raise TypeError('Got None value in check_non_optional.')
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


# NOTE: Even though this is available as part of typing_extensions, keeping
# it in here for now so we don't require typing_extensions as a dependency.
# Once 3.11 rolls around we can kill this and use typing.assert_never.
def assert_never(value: NoReturn) -> NoReturn:
    """Trick for checking exhaustive handling of Enums, etc.
    See https://github.com/python/typing/issues/735
    """
    assert False, f'Unhandled value: {value} ({type(value).__name__})'


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


def set_canonical_module(
    module_globals: dict[str, Any], names: list[str]
) -> None:
    """Override any __module__ attrs on passed classes/etc.

    This allows classes to present themselves using clean paths such as
    mymodule.MyClass instead of possibly ugly internal ones such as
    mymodule._internal._stuff.MyClass.
    """
    modulename = module_globals.get('__name__')
    if not isinstance(modulename, str):
        raise RuntimeError('Unable to get module name.')
    for name in names:
        obj = module_globals[name]
        existing = getattr(obj, '__module__', None)
        try:
            if existing is not None and existing != modulename:
                obj.__module__ = modulename
        except Exception:
            import logging

            logging.warning(
                'set_canonical_module: unable to change __module__'
                " from '%s' to '%s' on %s object at '%s'.",
                existing,
                modulename,
                type(obj),
                name,
            )
