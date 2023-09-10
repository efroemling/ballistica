# Released under the MIT License. See LICENSE for details.
#
"""Functionality for editing text strings.

This abstracts native edit dialogs as well as ones implemented via our
own ui toolkits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

import _babase

if TYPE_CHECKING:
    pass


class StringEditSubsystem:
    """Full string-edit state for the app."""

    def __init__(self) -> None:
        pass
        # print('HELLO FROM STRING EDIT')


class StringEdit:
    """Represents a string editing operation on some object.

    Editable objects such as text widgets or in-app-consoles can
    subclass this to make their contents editable on all platforms.
    """

    def __init__(self, initial_text: str) -> None:
        pass

    @final
    def apply(self, new_text: str) -> None:
        """Should be called by the owner when editing is complete.

        Note that in some cases this call may be a no-op (such as if
        this StringEdit is no longer the globally active one).
        """
        if not _babase.in_logic_thread():
            raise RuntimeError('This must be called from the logic thread.')
        self._do_apply(new_text)

    @final
    def cancel(self) -> None:
        """Should be called by the owner when editing is cancelled."""
        if not _babase.in_logic_thread():
            raise RuntimeError('This must be called from the logic thread.')
        self._do_cancel()

    def _do_apply(self, new_text: str) -> None:
        """Should be overridden by subclasses to handle apply.

        Will always be called in the logic thread.
        """
        raise NotImplementedError('Subclasses must override this.')

    def _do_cancel(self) -> None:
        """Should be overridden by subclasses to handle cancel.

        Will always be called in the logic thread.
        """
        raise NotImplementedError('Subclasses must override this.')
