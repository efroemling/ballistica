# Released under the MIT License. See LICENSE for details.
#
"""Functionality for editing text strings.

This abstracts native edit dialogs as well as ones implemented via our
own ui toolkits.
"""

from __future__ import annotations

import time
import logging
import weakref
from typing import TYPE_CHECKING, final

from efro.util import empty_weakref

import _babase

if TYPE_CHECKING:
    pass


class StringEditSubsystem:
    """Full string-edit state for the app."""

    def __init__(self) -> None:
        self.active_adapter = empty_weakref(StringEditAdapter)


class StringEditAdapter:
    """Represents a string editing operation on some object.

    Editable objects such as text widgets or in-app-consoles can
    subclass this to make their contents editable on all platforms.

    There can only be one string-edit at a time for the app. New
    StringEdits will attempt to register themselves as the globally
    active one in their constructor, but this may not succeed. When
    creating a StringEditAdapter, always check its 'is_valid()' value after
    creating it. If this is False, it was not able to set itself as
    the global active one and should be discarded.
    """

    def __init__(
        self,
        description: str,
        initial_text: str,
        max_length: int | None,
        screen_space_center: tuple[float, float] | None,
    ) -> None:
        if not _babase.in_logic_thread():
            raise RuntimeError('This must be called from the logic thread.')

        self.create_time = time.monotonic()

        # Note: these attr names are hard-coded in C++ code so don't
        # change them willy-nilly.
        self.description = description
        self.initial_text = initial_text
        self.max_length = max_length
        self.screen_space_center = screen_space_center

        # Attempt to register ourself as the active edit.
        subsys = _babase.app.stringedit
        current_edit = subsys.active_adapter()
        if current_edit is None or current_edit.can_be_replaced():
            subsys.active_adapter = weakref.ref(self)

    @final
    def can_be_replaced(self) -> bool:
        """Return whether this adapter can be replaced by a new one.

        This is mainly a safeguard to allow adapters whose drivers have
        gone away without calling apply or cancel to time out and be
        replaced with new ones.
        """
        if not _babase.in_logic_thread():
            raise RuntimeError('This must be called from the logic thread.')

        # Allow ourself to be replaced after a bit.
        if time.monotonic() - self.create_time > 5.0:
            if _babase.do_once():
                logging.warning(
                    'StringEditAdapter can_be_replaced() check for %s'
                    ' yielding True due to timeout; ideally this should'
                    ' not be possible as the StringEditAdapter driver'
                    ' should be blocking anything else from kicking off'
                    ' new edits.',
                    self,
                )
            return True

        # We also are always considered replaceable if we're not the
        # active global adapter.
        current_edit = _babase.app.stringedit.active_adapter()
        if current_edit is not self:
            return True

        return False

    @final
    def apply(self, new_text: str) -> None:
        """Should be called by the owner when editing is complete.

        Note that in some cases this call may be a no-op (such as if
        this StringEditAdapter is no longer the globally active one).
        """
        if not _babase.in_logic_thread():
            raise RuntimeError('This must be called from the logic thread.')

        # Make sure whoever is feeding this adapter is honoring max-length.
        if self.max_length is not None and len(new_text) > self.max_length:
            logging.warning(
                'apply() on %s was passed a string of length %d,'
                ' but adapter max_length is %d; this should not happen'
                ' (will truncate).',
                self,
                len(new_text),
                self.max_length,
                stack_info=True,
            )
            new_text = new_text[: self.max_length]

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
