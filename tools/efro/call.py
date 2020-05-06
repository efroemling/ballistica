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
"""Call related functionality shared between all efro components."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic, Callable, cast

if TYPE_CHECKING:
    from typing import Any, overload

CT = TypeVar('CT', bound=Callable)


class _CallbackCall(Generic[CT]):
    """Descriptor for exposing a call with a type defined by a TypeVar."""

    def __get__(self, obj: Any, type_in: Any = None) -> CT:
        return cast(CT, None)


class CallbackSet(Generic[CT]):
    """Wrangles callbacks for a particular event in a type-safe manner."""

    # In the type-checker's eyes, our 'run' attr is a CallbackCall which
    # returns a callable with the type we were created with. This lets us
    # type-check our run calls. (Is there another way to expose a function
    # with a signature defined by a generic?..)
    # At runtime, run() simply passes its args verbatim to its registered
    # callbacks; no types are checked.
    if TYPE_CHECKING:
        run: _CallbackCall[CT] = _CallbackCall()
    else:

        def run(self, *args, **keywds):
            """Run all callbacks."""
            print('HELLO FROM RUN', *args, **keywds)

    def __init__(self) -> None:
        print('CallbackSet()')

    def __del__(self) -> None:
        print('~CallbackSet()')

    def add(self, call: CT) -> None:
        """Add a callback to be run."""
        print('Would add call', call)


# Define Call() which can be used in type-checking call-wrappers that behave
# similarly to functools.partial (in that they take a callable and some
# positional arguments to be passed to it)

# In type-checking land, We define several different _CallXArg classes
# corresponding to different argument counts and define Call() as an
# overloaded function which returns one of them based on how many args are
# passed.

# To use this, simply assign your call type to this Call for type checking:
# Example:
#  class _MyCallWrapper:
#    <runtime class defined here>
#  if TYPE_CHECKING:
#    MyCallWrapper = bafoundation.executils.Call
#  else:
#    MyCallWrapper = _MyCallWrapper

# Note that this setup currently only works with positional arguments; if you
# would like to pass args via keyword you can wrap a lambda or local function
# which takes keyword args and converts to a call containing keywords.

if TYPE_CHECKING:
    In1T = TypeVar('In1T')
    In2T = TypeVar('In2T')
    In3T = TypeVar('In3T')
    In4T = TypeVar('In4T')
    In5T = TypeVar('In5T')
    In6T = TypeVar('In6T')
    In7T = TypeVar('In7T')
    OutT = TypeVar('OutT')

    class _CallNoArgs(Generic[OutT]):
        """Single argument variant of call wrapper."""

        def __init__(self, _call: Callable[[], OutT]):
            ...

        def __call__(self) -> OutT:
            ...

    class _Call1Arg(Generic[In1T, OutT]):
        """Single argument variant of call wrapper."""

        def __init__(self, _call: Callable[[In1T], OutT]):
            ...

        def __call__(self, _arg1: In1T) -> OutT:
            ...

    class _Call2Args(Generic[In1T, In2T, OutT]):
        """Two argument variant of call wrapper"""

        def __init__(self, _call: Callable[[In1T, In2T], OutT]):
            ...

        def __call__(self, _arg1: In1T, _arg2: In2T) -> OutT:
            ...

    class _Call3Args(Generic[In1T, In2T, In3T, OutT]):
        """Three argument variant of call wrapper"""

        def __init__(self, _call: Callable[[In1T, In2T, In3T], OutT]):
            ...

        def __call__(self, _arg1: In1T, _arg2: In2T, _arg3: In3T) -> OutT:
            ...

    class _Call4Args(Generic[In1T, In2T, In3T, In4T, OutT]):
        """Four argument variant of call wrapper"""

        def __init__(self, _call: Callable[[In1T, In2T, In3T, In4T], OutT]):
            ...

        def __call__(self, _arg1: In1T, _arg2: In2T, _arg3: In3T,
                     _arg4: In4T) -> OutT:
            ...

    class _Call5Args(Generic[In1T, In2T, In3T, In4T, In5T, OutT]):
        """Five argument variant of call wrapper"""

        def __init__(self, _call: Callable[[In1T, In2T, In3T, In4T, In5T],
                                           OutT]):
            ...

        def __call__(self, _arg1: In1T, _arg2: In2T, _arg3: In3T, _arg4: In4T,
                     _arg5: In5T) -> OutT:
            ...

    class _Call6Args(Generic[In1T, In2T, In3T, In4T, In5T, In6T, OutT]):
        """Six argument variant of call wrapper"""

        def __init__(self,
                     _call: Callable[[In1T, In2T, In3T, In4T, In5T, In6T],
                                     OutT]):
            ...

        def __call__(self, _arg1: In1T, _arg2: In2T, _arg3: In3T, _arg4: In4T,
                     _arg5: In5T, _arg6: In6T) -> OutT:
            ...

    class _Call7Args(Generic[In1T, In2T, In3T, In4T, In5T, In6T, In7T, OutT]):
        """Seven argument variant of call wrapper"""

        def __init__(
                self,
                _call: Callable[[In1T, In2T, In3T, In4T, In5T, In6T, In7T],
                                OutT]):
            ...

        def __call__(self, _arg1: In1T, _arg2: In2T, _arg3: In3T, _arg4: In4T,
                     _arg5: In5T, _arg6: In6T, _arg7: In7T) -> OutT:
            ...

    # No arg call; no args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[], OutT]) -> _CallNoArgs[OutT]:
        ...

    # 1 arg call; 1 arg bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T], OutT], arg1: In1T) -> _CallNoArgs[OutT]:
        ...

    # 1 arg call; no args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T], OutT]) -> _Call1Arg[In1T, OutT]:
        ...

    # 2 arg call; 2 args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T], OutT], arg1: In1T,
             arg2: In2T) -> _CallNoArgs[OutT]:
        ...

    # 2 arg call; 1 arg bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T], OutT],
             arg1: In1T) -> _Call1Arg[In2T, OutT]:
        ...

    # 2 arg call; no args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T], OutT]) -> _CallNoArgs[OutT]:
        ...

    # 3 arg call; 3 args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T, In3T], OutT], arg1: In1T, arg2: In2T,
             arg3: In3T) -> _CallNoArgs[OutT]:
        ...

    # 3 arg call; 2 args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T, In3T], OutT], arg1: In1T,
             arg2: In2T) -> _Call1Arg[In3T, OutT]:
        ...

    # 3 arg call; 1 arg bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T, In3T], OutT],
             arg1: In1T) -> _Call2Args[In2T, In3T, OutT]:
        ...

    # 3 arg call; no args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(
        call: Callable[[In1T, In2T, In3T], OutT]
    ) -> _Call3Args[In1T, In2T, In3T, OutT]:
        ...

    # 4 arg call; 4 args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T, In3T, In4T], OutT], arg1: In1T,
             arg2: In2T, arg3: In3T, arg4: In4T) -> _CallNoArgs[OutT]:
        ...

    # 5 arg call; 5 args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T, In3T, In4T, In5T],
                            OutT], arg1: In1T, arg2: In2T, arg3: In3T,
             arg4: In4T, arg5: In5T) -> _CallNoArgs[OutT]:
        ...

    # 6 arg call; 6 args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T, In3T, In4T, In5T, In6T],
                            OutT], arg1: In1T, arg2: In2T, arg3: In3T,
             arg4: In4T, arg5: In5T, arg6: In6T) -> _CallNoArgs[OutT]:
        ...

    # 7 arg call; 7 args bundled.
    # noinspection PyPep8Naming
    @overload
    def Call(call: Callable[[In1T, In2T, In3T, In4T, In5T, In6T, In7T], OutT],
             arg1: In1T, arg2: In2T, arg3: In3T, arg4: In4T, arg5: In5T,
             arg6: In6T, arg7: In7T) -> _CallNoArgs[OutT]:
        ...

    # noinspection PyPep8Naming
    def Call(*_args: Any, **_keywds: Any) -> Any:
        ...
