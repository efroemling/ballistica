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
import warnings
from typing import TYPE_CHECKING, TypeVar, Protocol, NewType, override

from efro.terminal import Clr

import _babase

if TYPE_CHECKING:
    import functools
    from typing import Any, Callable


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
    """A :class:`~typing.Protocol` for objects with an ``exists()`` method.

    For more info about the concept of 'existables':
    https://ballistica.net/wiki/Coding-Style-Guide
    """

    def exists(self) -> bool:
        """Whether this object exists."""


def existing[ExistableT: Existable](
    obj: ExistableT | None,
) -> ExistableT | None:
    """Convert invalid refs to None for an :class:`~babase.Existable`.

    To best support type checking, it is important that invalid
    references not be passed around and instead get converted to values
    of None. That way the type checker can properly flag attempts to
    pass possibly-dead objects (``FooType | None``) into functions
    expecting only live ones (``FooType``), etc. This call can be used
    on any 'existable' object (one with an ``exists()`` method) to
    convert it to ``None`` if it does not exist.

    For more info about the concept of 'existables':
    https://ballistica.net/wiki/Coding-Style-Guide
    """
    assert obj is None or hasattr(obj, 'exists'), f'No "exists" attr on {obj}.'
    return obj if obj is not None and obj.exists() else None


def getclass[T](
    name: str, subclassof: type[T], check_sdlib_modulename_clash: bool = False
) -> type[T]:
    """Given a full class name such as ``foo.bar.MyClass``, return the class.

    The class will be checked to make sure it is a subclass of the
    provided 'subclassof' class, and a :class:`TypeError` will be raised
    if not.
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


def get_type_name(cls: type) -> str:
    """Return a fully qualified type name for a class."""
    return f'{cls.__module__}.{cls.__qualname__}'


# Note: Something here is wonky with pylint, possibly related to our
# custom pylint plugin. Disabling all checks seems to fix it.
# pylint: disable=all
if TYPE_CHECKING:
    # For type-checking, we point WeakCall and Call at
    # functools.partial. This gives decent type-checking considering the
    # open-ended nature of these calls (args being supplied at create
    # time and/or at call time). Just remember that we're slightly lying
    # to the type-checker here.
    WeakCallPartial = functools.partial
    CallPartial = functools.partial
    WeakCall = functools.partial
    Call = functools.partial
else:

    class WeakCallPartial:
        """Wrap a callable and arguments into a single callable object.

        When passed a bound method as the callable, the instance portion of
        it is weak-referenced, meaning the underlying instance is free to
        die if all other references to it go away. Should this occur,
        calling the weak-call is simply a no-op.

        Think of this as a handy way to tell an object to do something at
        some point in the future if it happens to still exist.

        **EXAMPLE A:** This code will create a ``FooClass`` instance and
        call its ``bar()`` method 5 seconds later; it will be kept alive
        even though we overwrite its variable with None because the bound
        method we pass as a timer callback (``foo.bar``) strong-references
        it::

            foo = FooClass()
            babase.apptimer(5.0, foo.bar)
            foo = None

        **EXAMPLE B:** This code will *not* keep our object alive; it will
        die when we overwrite it with ``None`` and the timer will be a no-op
        when it fires::

            foo = FooClass()
            babase.apptimer(5.0, ba.WeakCall(foo.bar))
            foo = None

        **EXAMPLE C:** Wrap a method call with some positional and keyword
        args::

            myweakcall = babase.WeakCall(self.dostuff, argval1,
                                         namedarg=argval2)

            # Now we have a single callable to run that whole mess.
            # The same as calling myobj.dostuff(argval1, namedarg=argval2)
            # (provided my_obj still exists; this will do nothing otherwise).
            myweakcall()

        Note: additional args and keywords you provide to the weak-call
        constructor are stored as regular strong-references; you'll need to
        wrap them in weakrefs manually if desired.
        """

        # Optimize performance a bit; we shouldn't need to be super dynamic.
        __slots__ = ['_call', '_args', '_keywds']

        _did_invalid_call_warning = False

        def __init__(self, call: Any, /, *args: Any, **keywds: Any) -> None:
            # Note: keeping _call, _args, _keywds private in this case
            # since we sub functools.partial for ourself in
            # type-checking so they will be unrecognized anyway. Use
            # non-partial versions if you want to access those.
            if hasattr(call, '__func__'):
                self._call = WeakMethod(call)
            else:
                app = _babase.app
                if not self._did_invalid_call_warning:
                    logging.warning(
                        'Warning: callable passed to WeakCall() is not'
                        ' weak-referencable (%s); use regular Call() instead'
                        ' to avoid this warning.',
                        args[0],
                        stack_info=True,
                    )
                    type(self)._did_invalid_call_warning = True
                self._call = call
            self._args = args
            self._keywds = keywds

        def __call__(self, *args_extra: Any, **keywds_extra: Any) -> Any:
            # Fast path: no extra args or kwargs.
            if not args_extra and not keywds_extra:
                return self._call(*self._args, **self._keywds)

            # Slightly slower path: handle extra args.
            if not keywds_extra:
                # Only extra positional args; skip dict merge.
                return self._call(*(self._args + args_extra), **self._keywds)

            # Handle kw overrides (call-time kwargs overriding stored).
            merged = {**self._keywds, **keywds_extra}
            return self._call(*(self._args + args_extra), **merged)

        @override
        def __repr__(self) -> str:
            return (
                f'<babase.WeakCall object; _call={self._call!r}'
                f' _args={self._args!r} _keywds={self._keywds!r}>'
            )

    class CallPartial:
        """Wraps a callable and args into a single callable object.

        The callable is strong-referenced so it won't die until this
        object does.

        Note that a bound method (ex: ``myobj.dosomething``) contains a
        reference to ``self`` (``myobj`` in that case), so you will be
        keeping that object alive too. Use babase.WeakCall if you want
        to pass a method to a callback without keeping its object alive.

        Example: Wrap a method call with 1 positional and 1 keyword arg::

            mycall = babase.Call(myobj.dostuff, argval, namedarg=argval2)

            # Now we have a single callable to run that whole mess.
            # ..the same as calling myobj.dostuff(argval, namedarg=argval2)
            mycall()
        """

        # Optimize performance a bit; we shouldn't need to be super dynamic.
        __slots__ = ['_call', '_args', '_keywds']

        def __init__(self, call: Any, /, *args: Any, **keywds: Any):
            # Note: keeping _call, _args, _keywds private in this case
            # since we sub functools.partial for ourself in
            # type-checking so they will be unrecognized anyway. Use
            # non-partial versions if you want to access those.
            self._call = call
            self._args = args
            self._keywds = keywds

        def __call__(self, *args_extra: Any, **keywds_extra: Any) -> Any:
            # Fast path: no extra args or kwargs.
            if not args_extra and not keywds_extra:
                return self._call(*self._args, **self._keywds)

            # Slightly slower path: handle extra args.
            if not keywds_extra:
                # Only extra positional args; skip dict merge.
                return self._call(*(self._args + args_extra), **self._keywds)

            # Handle kw overrides (call-time kwargs overriding stored).
            merged = {**self._keywds, **keywds_extra}
            return self._call(*(self._args + args_extra), **merged)

        @override
        def __repr__(self) -> str:
            return (
                f'<babase.Call object; _call={self.call!r}'
                f' _args={self.args!r} _keywds={self.keywds!r}>'
            )

    class WeakCall:
        """Currently alias of :meth:`WeakCallPartial`."""

        # Optimize performance a bit; we shouldn't need to be super dynamic.
        __slots__ = ['_call', '_args', '_keywds']

        _did_invalid_call_warning = False

        def __init__(self, call: Any, /, *args: Any, **keywds: Any) -> None:
            warnings.warn(
                'WeakCall should be replaced with either WeakCallPartial'
                ' (if passing extra args at call time) or WeakCallStrict'
                ' (it not). Once API 9 support ends, WeakCall can again be'
                ' used, but it will behave like WeakCallStrict instead of'
                ' WeakCallPartial.',
                DeprecationWarning,
                stacklevel=2,
            )
            # Note: keeping _call, _args, _keywds private in this case
            # since we sub functools.partial for ourself in
            # type-checking so they will be unrecognized anyway. Use
            # non-partial versions if you want to access those.
            if hasattr(call, '__func__'):
                self._call = WeakMethod(call)
            else:
                app = _babase.app
                if not self._did_invalid_call_warning:
                    logging.warning(
                        'Warning: callable passed to WeakCall() is not'
                        ' weak-referencable (%r); use regular Call() instead'
                        ' to avoid this warning.',
                        args[0],
                        stack_info=True,
                    )
                    type(self)._did_invalid_call_warning = True
                    self._call = call
            self._args = args
            self._keywds = keywds

        def __call__(self, *args_extra: Any, **keywds_extra: Any) -> Any:
            # Fast path: no extra args or kwargs.
            if not args_extra and not keywds_extra:
                return self._call(*self._args, **self._keywds)

            # Slightly slower path: handle extra args.
            if not keywds_extra:
                # Only extra positional args; skip dict merge.
                return self._call(*(self._args + args_extra), **self._keywds)

            # Handle kw overrides (call-time kwargs overriding stored).
            merged = {**self._keywds, **keywds_extra}
            return self._call(*(self._args + args_extra), **merged)

        @override
        def __repr__(self) -> str:
            return (
                f'<babase.WeakCall object; _call={self._call!r}'
                f' _args={self._args!r} _keywds={self._keywds!r}>'
            )

    class Call:
        """Currently alias of :meth:`CallPartial`."""

        # Optimize performance a bit; we shouldn't need to be super dynamic.
        __slots__ = ['_call', '_args', '_keywds']

        def __init__(self, call: Any, /, *args: Any, **keywds: Any):
            warnings.warn(
                'Call should be replaced with either CallPartial'
                ' (if passing extra args at call time) or CallStrict'
                ' (it not). Once API 9 support ends, Call can again be'
                ' used, but it will behave like CallStrict instead'
                ' of CallPartial.',
                DeprecationWarning,
                stacklevel=2,
            )
            # Note: keeping _call, _args, _keywds private in this case
            # since we sub functools.partial for ourself in
            # type-checking so they will be unrecognized anyway. Use
            # non-partial versions if you want to access those.
            self._call = call
            self._args = args
            self._keywds = keywds

        def __call__(self, *args_extra: Any, **keywds_extra: Any) -> Any:
            # Fast path: no extra args or kwargs.
            if not args_extra and not keywds_extra:
                return self._call(*self._args, **self._keywds)

            # Slightly slower path: handle extra args.
            if not keywds_extra:
                # Only extra positional args; skip dict merge.
                return self._call(*(self._args + args_extra), **self._keywds)

            # Handle kw overrides (call-time kwargs overriding stored).
            merged = {**self._keywds, **keywds_extra}
            return self._call(*(self._args + args_extra), **merged)

        @override
        def __repr__(self) -> str:
            return (
                f'<babase.Call object; _call={self.call!r}'
                f' _args={self.args!r} _keywds={self.keywds!r}>'
            )


# pylint: enable=all


class CallStrict[**P, T]:
    """Like :meth:`CallPartial()` but disallows extra args at call time.

    This allows more complete type checking to occur, so this is
    recommended if you do not need extra args at call time.
    """

    __slots__ = ('call', 'args', 'kwargs')

    def __init__(
        self, call: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs
    ) -> None:
        # Note: we allow access to these here since we don't use any
        # tricks like pointing at functools.partial for type checking or
        # whatnot that would break this.
        self.call = call
        self.args = args
        self.kwargs = kwargs

    def __call__(self) -> T:
        return self.call(*self.args, **self.kwargs)

    @override
    def __repr__(self) -> str:
        return (
            f'<babase.Call object; call={self.call!r},'
            f' args={self.args!r}, kwargs={self.kwargs!r}>'
        )


class WeakCallStrict[**P, T]:
    """Like :meth:`WeakCallPartial()` but disallows extra args at call time.

    This allows more complete type checking to occur, so this is
    recommended if you do not need extra args at call time.
    """

    __slots__ = ('call', 'args', 'kwargs')

    _did_invalid_call_warning = False

    def __init__(
        self, call: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs
    ) -> None:
        # Note: we allow access to these here since we don't use any
        # tricks like pointing at functools.partial for type checking or
        # whatnot that would break this.
        if hasattr(call, '__func__'):
            self.call: Any = WeakMethod(call)  # type: ignore
        else:
            app = _babase.app
            if not self._did_invalid_call_warning:
                logging.warning(
                    'Warning: callable passed to WeakCallStrict() is not'
                    ' weak-referencable (%r); use regular CallStrict() instead'
                    ' to avoid this warning.',
                    args[0],
                    stack_info=True,
                )
                type(self)._did_invalid_call_warning = True
            self.call = call
        self.args = args
        self.kwargs = kwargs

    def __call__(self) -> T:
        return self.call(*self.args, **self.kwargs)  # type: ignore

    @override
    def __repr__(self) -> str:
        return (
            f'<babase.WeakCall object; call={self.call!r},'
            f' args={self.args!r}, kwargs={self.kwargs!r}>'
        )


class WeakMethod:
    """A weak-referenced bound method.

    Wraps a bound method using weak references so that the original is
    free to die. If called with a dead target, is simply a no-op.
    """

    # Optimize performance a bit; we shouldn't need to be super dynamic.
    __slots__ = ['func', 'obj']

    def __init__(self, call: types.MethodType):
        assert isinstance(call, types.MethodType)
        self.func = call.__func__
        self.obj = weakref.ref(call.__self__)

    def __call__(self, *args: Any, **keywds: Any) -> Any:
        obj: Any = self.obj()
        if obj is None:
            return None
        return self.func(*((obj,) + args), **keywds)

    @override
    def __repr__(self) -> str:
        return f'<babase.WeakMethod object; func={self.func!r}>'


def verify_object_death(obj: object) -> None:
    """Warn if an object does not get freed within a short period.

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
        _babase.apptimer(delay, CallStrict(_verify_object_death, ref))


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

    This consists of a leading underscore, the module path at the call
    site with dots replaced by underscores, the containing class's
    qualified name, and the provided suffix. When storing data in public
    places such as 'customdata' dicts, this minimizes the chance of
    collisions with other similarly named classes.

    Note that this will function even if called in the class definition.

    Example: Generate a unique name for storage purposes::

        class MyThingie:

            # This will give something like
            # '_mymodule_submodule_mythingie_data'.
            _STORENAME = babase.storagename('data')

            # Use that name to store some data in the Activity we were
            # passed.
            def __init__(self, activity):
                activity.customdata[self._STORENAME] = {}

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
