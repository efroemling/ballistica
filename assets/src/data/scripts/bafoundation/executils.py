# Copyright (c) 2011-2019 Eric Froemling
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
"""Exec related functionality shared between all ba components."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic, Callable, cast

if TYPE_CHECKING:
    from typing import Any

T = TypeVar('T', bound=Callable)


class _CallbackCall(Generic[T]):
    """Descriptor for exposing a call with a type defined by a TypeVar."""

    def __get__(self, obj: Any, type_in: Any = None) -> T:
        return cast(T, None)


class CallbackSet(Generic[T]):
    """Wrangles callbacks for a particular event."""

    # In the type-checker's eyes, our 'run' attr is a CallbackCall which
    # returns a callable with the type we were created with. This lets us
    # type-check our run calls. (Is there another way to expose a function
    # with a signature defined by a generic?..)
    # At runtime, run() simply passes its args verbatim to its registered
    # callbacks; no types are checked.
    if TYPE_CHECKING:
        run: _CallbackCall[T] = _CallbackCall()
    else:

        def run(self, *args, **keywds):
            """Run all callbacks."""
            print("HELLO FROM RUN", *args, **keywds)

    def __init__(self) -> None:
        print("CallbackSet()")

    def __del__(self) -> None:
        print("~CallbackSet()")

    def add(self, call: T) -> None:
        """Add a callback to be run."""
        print("Would add call", call)
