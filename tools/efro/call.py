# Released under the MIT License. See LICENSE for details.
#
"""Call related functionality shared between all efro components."""

from __future__ import annotations

import weakref
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable


class CallbackSet[T]:
    """A simple way to manage a set of callbacks.

    Any number of calls can be registered with a callback set. Each
    registration results in a Registration object that can be used to
    deregister the call from the set later. Callbacks are also
    implicitly deregistered when an entry is deallocated, so make sure
    to hold on to the return value when adding.

    CallbackSet instances should be used from a single thread only (this
    will be checked in debug mode).
    """

    def __init__(self) -> None:
        self._entries: list[weakref.ref[CallbackRegistration[T]]] = []
        self.thread: threading.Thread
        if __debug__:
            self.thread = threading.current_thread()

    def register(self, call: T) -> CallbackRegistration[T]:
        """Register a new callback."""
        assert threading.current_thread() == self.thread

        self._prune()

        entry = CallbackRegistration(call, self)
        self._entries.append(weakref.ref(entry))
        return entry

    def getcalls(self) -> list[T]:
        """Return the current set of registered calls.

        Note that this returns a flattened list of calls; generally this
        should protect against calls which themselves add or remove
        callbacks.
        """
        assert threading.current_thread() == self.thread

        self._prune()

        # Ignore calls that have been deallocated or explicitly
        # deregistered.
        entries = [e() for e in self._entries]
        return [e.call for e in entries if e is not None and e.call is not None]

    def _prune(self) -> None:

        # Quick-out if all our entries are intact.
        needs_prune = False
        for entry in self._entries:
            entrytarget = entry()
            if entrytarget is None or entrytarget.call is None:
                needs_prune = True
                break
        if not needs_prune:
            return

        # Ok; something needs pruning. Rebuild the entries list.
        newentries: list[weakref.ref[CallbackRegistration[T]]] = []
        for entry in self._entries:
            entrytarget = entry()
            if entrytarget is not None and entrytarget.call is not None:
                newentries.append(entry)
        self._entries = newentries


class CallbackRegistration[T]:
    """An entry for a callback set."""

    def __init__(self, call: T, callbackset: CallbackSet[T]) -> None:
        self.call: T | None = call
        self.callbackset: CallbackSet[T] | None = callbackset

    def deregister(self) -> None:
        """Explicitly remove a callback from a CallbackSet."""
        assert (
            self.callbackset is None
            or threading.current_thread() == self.callbackset.thread
        )
        # Simply clear the call to mark us as dead.
        self.call = None
