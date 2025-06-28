# Released under the MIT License. See LICENSE for details.
#
"""Provides the AppComponent class."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast

import _babase

if TYPE_CHECKING:
    from typing import Callable, Any


class AppComponentSubsystem:
    """Subsystem for wrangling AppComponents.

    This subsystem acts as a registry for classes providing particular
    functionality for the app, and allows plugins or other custom code
    to easily override said functionality.

    Access the single shared instance of this class at
    babase.app.components.

    The general idea with this setup is that a base-class Foo is defined
    to provide some functionality and then anyone wanting that
    functionality calls getclass(Foo) to return the current registered
    implementation. The user should not know or care whether they are
    getting Foo itself or some subclass of it.

    Change-callbacks can also be requested for base classes which will
    fire in a deferred manner when particular base-classes are
    overridden.

    (This isn't ready for use yet so hiding it from docs)

    :meta private:
    """

    def __init__(self) -> None:
        self._implementations: dict[type, type] = {}
        self._prev_implementations: dict[type, type] = {}
        self._dirty_base_classes: set[type] = set()
        self._change_callbacks: dict[type, list[Callable[[Any], None]]] = {}

    def setclass(self, baseclass: type, implementation: type) -> None:
        """Set the class providing an implementation of some base-class.

        The provided implementation class must be a subclass of baseclass.
        """
        # Currently limiting this to logic-thread use; can revisit if
        # needed (would need to guard access to our implementations
        # dict).
        if not _babase.in_logic_thread():
            raise RuntimeError('this must be called from the logic thread.')

        if not issubclass(implementation, baseclass):
            raise TypeError(
                f'Implementation {implementation}'
                f' is not a subclass of baseclass {baseclass}.'
            )

        self._implementations[baseclass] = implementation

        # If we're the first thing getting dirtied, set up a callback to
        # clean everything. And add ourself to the dirty list
        # regardless.
        if not self._dirty_base_classes:
            _babase.pushcall(self._run_change_callbacks)
        self._dirty_base_classes.add(baseclass)

    def getclass[T: type](self, baseclass: T) -> T:
        """Given a base-class, return the current implementation class.

        If no custom implementation has been set, the provided
        base-class is returned.
        """
        if not _babase.in_logic_thread():
            raise RuntimeError('this must be called from the logic thread.')

        del baseclass  # Unused.

        # FIXME - I think our pylint plugin is doing the wrong thing
        # here and clearing all func generic params when it should just
        # be clearing their type annotations.
        return cast(T, None)  # pylint: disable=undefined-variable

    def register_change_callback[T: type](
        self, baseclass: T, callback: Callable[[T], None]
    ) -> None:
        """Register a callback to fire on class implementation changes.

        The callback will be scheduled to run in the logic thread event
        loop. Note that any further setclass calls before the callback
        runs will not result in additional callbacks.
        """
        if not _babase.in_logic_thread():
            raise RuntimeError('this must be called from the logic thread.')

        self._change_callbacks.setdefault(baseclass, []).append(callback)

    def _run_change_callbacks(self) -> None:
        pass
