# Released under the MIT License. See LICENSE for details.
#
"""Utility snippets applying to generic Python code."""
from __future__ import annotations

import types
import weakref
import random
import inspect
from typing import TYPE_CHECKING, TypeVar, Protocol

from efro.terminal import Clr
import _ba
from ba._error import print_error, print_exception
from ba._generated.enums import TimeType

if TYPE_CHECKING:
    from typing import Any
    from efro.call import Call as Call  # 'as Call' so we re-export.


class Existable(Protocol):
    """A Protocol for objects supporting an exists() method.

    Category: **Protocols**
    """

    def exists(self) -> bool:
        """Whether this object exists."""


ExistableT = TypeVar('ExistableT', bound=Existable)
T = TypeVar('T')


def existing(obj: ExistableT | None) -> ExistableT | None:
    """Convert invalid references to None for any ba.Existable object.

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


def getclass(name: str, subclassof: type[T]) -> type[T]:
    """Given a full class name such as foo.bar.MyClass, return the class.

    Category: **General Utility Functions**

    The class will be checked to make sure it is a subclass of the provided
    'subclassof' class, and a TypeError will be raised if not.
    """
    import importlib

    splits = name.split('.')
    modulename = '.'.join(splits[:-1])
    classname = splits[-1]
    module = importlib.import_module(modulename)
    cls: type = getattr(module, classname)

    if not issubclass(cls, subclassof):
        raise TypeError(f'{name} is not a subclass of {subclassof}.')
    return cls


def json_prep(data: Any) -> Any:
    """Return a json-friendly version of the provided data.

    This converts any tuples to lists and any bytes to strings
    (interpreted as utf-8, ignoring errors). Logs errors (just once)
    if any data is modified/discarded/unsupported.
    """

    if isinstance(data, dict):
        return dict(
            (json_prep(key), json_prep(value))
            for key, value in list(data.items())
        )
    if isinstance(data, list):
        return [json_prep(element) for element in data]
    if isinstance(data, tuple):
        print_error('json_prep encountered tuple', once=True)
        return [json_prep(element) for element in data]
    if isinstance(data, bytes):
        try:
            return data.decode(errors='ignore')
        except Exception:
            from ba import _error

            print_error('json_prep encountered utf-8 decode error', once=True)
            return data.decode(errors='ignore')
    if not isinstance(data, (str, float, bool, type(None), int)):
        print_error(
            'got unsupported type in json_prep:' + str(type(data)), once=True
        )
    return data


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
    return cls.__module__ + '.' + cls.__name__


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
    ... ba.timer(5.0, foo.bar)
    ... foo = None

    **EXAMPLE B:** This code will *not* keep our object alive; it will die
    when we overwrite it with None and the timer will be a no-op when it
    fires
    >>> foo = FooClass()
    ... ba.timer(5.0, ba.WeakCall(foo.bar))
    ... foo = None

    **EXAMPLE C:** Wrap a method call with some positional and keyword args:
    >>> myweakcall = ba.WeakCall(self.dostuff, argval1,
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

    def __init__(self, *args: Any, **keywds: Any) -> None:
        """Instantiate a WeakCall.

        Pass a callable as the first arg, followed by any number of
        arguments or keywords.
        """
        if hasattr(args[0], '__func__'):
            self._call = WeakMethod(args[0])
        else:
            app = _ba.app
            if not app.did_weak_call_warning:
                print(
                    (
                        'Warning: callable passed to ba.WeakCall() is not'
                        ' weak-referencable ('
                        + str(args[0])
                        + '); use ba.Call() instead to avoid this '
                        'warning. Stack-trace:'
                    )
                )
                import traceback

                traceback.print_stack()
                app.did_weak_call_warning = True
            self._call = args[0]
        self._args = args[1:]
        self._keywds = keywds

    def __call__(self, *args_extra: Any) -> Any:
        return self._call(*self._args + args_extra, **self._keywds)

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

    Note that a bound method (ex: ``myobj.dosomething``) contains a reference
    to ``self`` (``myobj`` in that case), so you will be keeping that object
    alive too. Use ba.WeakCall if you want to pass a method to callback
    without keeping its object alive.
    """

    def __init__(self, *args: Any, **keywds: Any):
        """Instantiate a Call.

        Pass a callable as the first arg, followed by any number of
        arguments or keywords.

        ##### Example
        Wrap a method call with 1 positional and 1 keyword arg:
        >>> mycall = ba.Call(myobj.dostuff, argval, namedarg=argval2)
        ... # Now we have a single callable to run that whole mess.
        ... # ..the same as calling myobj.dostuff(argval, namedarg=argval2)
        ... mycall()
        """
        self._call = args[0]
        self._args = args[1:]
        self._keywds = keywds

    def __call__(self, *args_extra: Any) -> Any:
        return self._call(*self._args + args_extra, **self._keywds)

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
    # Some interaction between our ballistica pylint plugin
    # and this code is crashing starting on pylint 2.15.0.
    # This seems to fix things for now.
    # pylint: disable=all
    WeakCall = Call
    Call = Call
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

    def __init__(self, call: types.MethodType):
        assert isinstance(call, types.MethodType)
        self._func = call.__func__
        self._obj = weakref.ref(call.__self__)

    def __call__(self, *args: Any, **keywds: Any) -> Any:
        obj = self._obj()
        if obj is None:
            return None
        return self._func(*((obj,) + args), **keywds)

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
        print_exception('Unable to create weak-ref in verify_object_death')

    # Use a slight range for our checks so they don't all land at once
    # if we queue a lot of them.
    delay = random.uniform(2.0, 5.5)
    with _ba.Context('ui'):
        _ba.timer(
            delay, lambda: _verify_object_death(ref), timetype=TimeType.REAL
        )


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
    ...     _STORENAME = ba.storagename('data')
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
