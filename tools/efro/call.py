# Released under the MIT License. See LICENSE for details.
#
"""Call related functionality shared between all efro components."""

from __future__ import annotations

# import functools
from typing import TYPE_CHECKING, TypeVar, Generic

T = TypeVar('T')

if TYPE_CHECKING:
    pass


class SimpleCallbackSet(Generic[T]):
    """A simple way to manage a set of callbacks."""

    def __init__(self) -> None:
        self._entries: list[SimpleCallbackSetEntry[T]] = []

    def add(self, call: T) -> None:
        """Add a callback."""
        self._entries.append(SimpleCallbackSetEntry(call))

    def getcalls(self) -> list[T]:
        """Return the current set of registered calls."""
        return [e.call for e in self._entries]


class SimpleCallbackSetEntry(Generic[T]):
    """An entry for a callback set."""

    def __init__(self, call: T) -> None:
        self.call = call
