# Synced from bamaster.
# EFRO_SYNC_HASH=43697789967751346220367938882574464737
#
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
