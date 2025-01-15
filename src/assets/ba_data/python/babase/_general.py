# Released under the MIT License. See LICENSE for details.
#
"""Utility snippets applying to generic Python code."""
from __future__ import annotations

import sys
import types
import weakref
import random
import logging
import inspect
from typing import TYPE_CHECKING, TypeVar, Protocol, NewType, override

from efro.terminal import Clr

import _babase

if TYPE_CHECKING:
    import functools
    from typing import Any


# Declare distinct types for different time measurements we use so the
# type-checker can help prevent us from mixing and matching accidentally,
# even if the *actual* types being used are the same.

# Our monotonic time measurement that starts at 0 when the app launches
# and pauses while the app is suspended.
AppTime = NewType('AppTime', float)

# Like app-time but incremented at frame draw time and in a smooth
# consistent manner; useful to keep animations smooth and jitter-free.
DisplayTime = NewType('DisplayTime', float)


class Existable(Protocol):
    """A Protocol for objects supporting an exists() method.

    Category: **Protocols**
    """

    def exists(self) -> bool:
        """Whether this object exists."""


ExistableT = TypeVar('ExistableT', bound=Existable)
T = TypeVar('T')


def existing(obj: ExistableT | None) -> ExistableT | None:
    """Convert invalid references to None for any babase.Existable object.

    Category: **Gameplay Functions**

    To best support type checking, it is important that invalid references
    not be passed around and instead get converted to values of None.
    That way the type checker can properly flag attempts to pass possibly-dead
    objects (FooType | None) into functions expecting only live ones
    (FooType), etc. This call can be used on any 'existable' object
    (one with an exists() method) and will convert it to a None value
    if it does not exist.

    For more info, see notes on 'existables' here:
    https://ballistica.net/wiki/Coding-Style-Guide
    """
    assert obj is None or hasattr(obj, 'exists'), f'No "exists" on {obj}'
    return obj if obj is not None and obj.exists() else None


def getclass(
    name: str, subclassof: type[T], check_sdlib_modulename_clash: bool = False
) -> type[T]:
    """Given a full class name such as foo.bar.MyClass, return the class.

    Category: **General Utility Functions**

    The class will be checked to make sure it is a subclass of the provided
    'subclassof' class, and a TypeError will be raised if not.
    """
    import importlib

    splits = name.split('.')
    modulename = '.'.join(splits[:-1])
    classname = splits[-1]
    if modulename in sys.stdlib_module_names and check_sdlib_modulename_clash:
        raise Exception(f'{modulename} is an inbuilt module.')
    module = importlib.import_module(modulename)
    cls: type = getattr(module, classname)

    if not issubclass(cls, subclassof):
        raise TypeError(f'{name} is not a subclass of {subclassof}.')
    return cls


def utf8_all(data: Any) -> Any:
    """Convert any unicode data in provided sequence(s) to utf8 bytes."""
    if isinstance(data, dict):
        return dict(
            (utf8_all(key), utf8_all(value))
            for key, value in list(data.items())
        )
    if isinstance(data, list):
        return [utf8_all(element) for element in data]
    if isinstance(data, tuple):
        return tuple(utf8_all(element) for element in data)
    if isinstance(data, str):
        return data.encode('utf-8', errors='ignore')
    return data


def get_type_name(cls: type) -> str:
    """Return a full type name including module for a class."""
    return f'{cls.__module__}.{cls.__name__}'


class _WeakCall:
    """Wrap a callable and arguments into a single callable object.

    Category: **General Utility Classes**

    When passed a bound method as the callable, the instance portion
    of it is weak-referenced, meaning the underlying instance is
    free to die if all other references to it go away. Should this
    occur, calling the WeakCall is simply a no-op.

    Think of this as a handy way to tell an object to do something
    at some point in the future if it happens to still exist.

    ##### Examples
    **EXAMPLE A:** this code will create a FooClass instance and call its
    bar() method 5 seconds later; it will be kept alive even though
    we overwrite its variable with None because the bound method
    we pass as a timer callback (foo.bar) strong-references it
    >>> foo = FooClass()
    ... babase.apptimer(5.0, foo.bar)
    ... foo = None

    **EXAMPLE B:** This code will *not* keep our object alive; it will die
    when we overwrite it with None and the timer will be a no-op when it
    fires
    >>> foo = FooClass()
    ... babase.apptimer(5.0, ba.WeakCall(foo.bar))
    ... foo = None

    **EXAMPLE C:** Wrap a method call with some positional and keyword args:
    >>> myweakcall = babase.WeakCall(self.dostuff, argval1,
    ...                          namedarg=argval2)
    ... # Now we have a single callable to run that whole mess.
    ... # The same as calling myobj.dostuff(argval1, namedarg=argval2)
    ... # (provided my_obj still exists; this will do nothing
    ... # otherwise).
    ... myweakcall()

    Note: additional args and keywords you provide to the WeakCall()
    constructor are stored as regular strong-references; you'll need
    to wrap them in weakrefs manually if desired.
    """

    # Optimize performance a bit; we shouldn't need to be super dynamic.
    __slots__ = ['_call', '_args', '_keywds']

    _did_invalid_call_warning = False

    def __init__(self, *args: Any, **keywds: Any) -> None:
        """Instantiate a WeakCall.

        Pass a callable as the first arg, followed by any number of
        arguments or keywords.
        """
        if hasattr(args[0], '__func__'):
            self._call = WeakMethod(args[0])
        else:
            app = _babase.app
            if not self._did_invalid_call_warning:
                logging.warning(
                    'Warning: callable passed to babase.WeakCall() is not'
                    ' weak-referencable (%s); use functools.partial instead'
                    ' to avoid this warning.',
                    args[0],
                    stack_info=True,
                )
                type(self)._did_invalid_call_warning = True
            self._call = args[0]
        self._args = args[1:]
        self._keywds = keywds

    def __call__(self, *args_extra: Any) -> Any:
        return self._call(*self._args + args_extra, **self._keywds)

    @override
    def __str__(self) -> str:
        return (
            '<ba.WeakCall object; _call='
            + str(self._call)
            + ' _args='
            + str(self._args)
            + ' _keywds='
            + str(self._keywds)
            + '>'
        )


class _Call:
    """Wraps a callable and arguments into a single callable object.

    Category: **General Utility Classes**

    The callable is strong-referenced so it won't die until this
    object does.

    WARNING: This is exactly the same as Python's built in functools.partial().
    Use functools.partial instead of this for new code, as this will probably
    be deprecated at some point.

    Note that a bound method (ex: ``myobj.dosomething``) contains a reference
    to ``self`` (``myobj`` in that case), so you will be keeping that object
    alive too. Use babase.WeakCall if you want to pass a method to a callback
    without keeping its object alive.
    """

    # Optimize performance a bit; we shouldn't need to be super dynamic.
    __slots__ = ['_call', '_args', '_keywds']

    def __init__(self, *args: Any, **keywds: Any):
        """Instantiate a Call.

        Pass a callable as the first arg, followed by any number of
        arguments or keywords.

        ##### Example
        Wrap a method call with 1 positional and 1 keyword arg:
        >>> mycall = babase.Call(myobj.dostuff, argval, namedarg=argval2)
        ... # Now we have a single callable to run that whole mess.
        ... # ..the same as calling myobj.dostuff(argval, namedarg=argval2)
        ... mycall()
        """
        self._call = args[0]
        self._args = args[1:]
        self._keywds = keywds

    def __call__(self, *args_extra: Any) -> Any:
        return self._call(*self._args + args_extra, **self._keywds)

    @override
    def __str__(self) -> str:
        return (
            '<ba.Call object; _call='
            + str(self._call)
            + ' _args='
            + str(self._args)
            + ' _keywds='
            + str(self._keywds)
            + '>'
        )


if TYPE_CHECKING:
    # For type-checking, point at functools.partial which gives us full
    # type checking on both positional and keyword arguments (as of mypy
    # 1.11).

    # FIXME: Actually, currently (as of Dec 2024) mypy doesn't fully
    # type check partial. The partial() call itself is checked, but the
    # resulting callable seems to be essentially untyped. We should
    # probably revise this stuff so that Call and WeakCall are for 100%
    # complete calls so we can fully type check them using ParamSpecs or
    # whatnot. We could then write a weak_partial() call if we actually
    # need that particular combination of functionality.

    # Note: Something here is wonky with pylint, possibly related to our
    # custom pylint plugin. Disabling all checks seems to fix it.
    # pylint: disable=all

    WeakCall = functools.partial
    Call = functools.partial
else:
    WeakCall = _WeakCall
    WeakCall.__name__ = 'WeakCall'
    Call = _Call
    Call.__name__ = 'Call'


class WeakMethod:
    """A weak-referenced bound method.

    Wraps a bound method using weak references so that the original is
    free to die. If called with a dead target, is simply a no-op.
    """

    # Optimize performance a bit; we shouldn't need to be super dynamic.
    __slots__ = ['_func', '_obj']

    def __init__(self, call: types.MethodType):
        assert isinstance(call, types.MethodType)
        self._func = call.__func__
        self._obj = weakref.ref(call.__self__)

    def __call__(self, *args: Any, **keywds: Any) -> Any:
        obj = self._obj()
        if obj is None:
            return None
        return self._func(*((obj,) + args), **keywds)

    @override
    def __str__(self) -> str:
        return '<ba.WeakMethod object; call=' + str(self._func) + '>'


def verify_object_death(obj: object) -> None:
    """Warn if an object does not get freed within a short period.

    Category: **General Utility Functions**

    This can be handy to detect and prevent memory/resource leaks.
    """

    try:
        ref = weakref.ref(obj)
    except Exception:
        logging.exception('Unable to create weak-ref in verify_object_death')
        return

    # Use a slight range for our checks so they don't all land at once
    # if we queue a lot of them.
    delay = random.uniform(2.0, 5.5)

    # Make this timer in an empty context; don't want it dying with the
    # scene/etc.
    with _babase.ContextRef.empty():
        _babase.apptimer(delay, Call(_verify_object_death, ref))


def _verify_object_death(wref: weakref.ref) -> None:
    obj = wref()
    if obj is None:
        return

    try:
        name = type(obj).__name__
    except Exception:
        print(f'Note: unable to get type name for {obj}')
        name = 'object'

    print(
        f'{Clr.RED}Error: {name} not dying when expected to:'
        f' {Clr.BLD}{obj}{Clr.RST}\n'
        'See efro.debug for ways to debug this.'
    )


def storagename(suffix: str | None = None) -> str:
    """Generate a unique name for storing class data in shared places.

    Category: **General Utility Functions**

    This consists of a leading underscore, the module path at the
    call site with dots replaced by underscores, the containing class's
    qualified name, and the provided suffix. When storing data in public
    places such as 'customdata' dicts, this minimizes the chance of
    collisions with other similarly named classes.

    Note that this will function even if called in the class definition.

    ##### Examples
    Generate a unique name for storage purposes:
    >>> class MyThingie:
    ...     # This will give something like
    ...     # '_mymodule_submodule_mythingie_data'.
    ...     _STORENAME = babase.storagename('data')
    ...
    ...     # Use that name to store some data in the Activity we were
    ...     # passed.
    ...     def __init__(self, activity):
    ...         activity.customdata[self._STORENAME] = {}
    """
    frame = inspect.currentframe()
    if frame is None:
        raise RuntimeError('Cannot get current stack frame.')
    fback = frame.f_back

    # Note: We need to explicitly clear frame here to avoid a ref-loop
    # that keeps all function-dicts in the stack alive until the next
    # full GC cycle (the stack frame refers to this function's dict,
    # which refers to the stack frame).
    del frame

    if fback is None:
        raise RuntimeError('Cannot get parent stack frame.')
    modulepath = fback.f_globals.get('__name__')
    if modulepath is None:
        raise RuntimeError('Cannot get parent stack module path.')
    assert isinstance(modulepath, str)
    qualname = fback.f_locals.get('__qualname__')
    if qualname is not None:
        assert isinstance(qualname, str)
        fullpath = f'_{modulepath}_{qualname.lower()}'
    else:
        fullpath = f'_{modulepath}'
    if suffix is not None:
        fullpath = f'{fullpath}_{suffix}'
    return fullpath.replace('.', '_')
