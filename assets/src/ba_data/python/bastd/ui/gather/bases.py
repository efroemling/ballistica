# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for inviting/joining friends."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from bastd.ui.gather import GatherWindow


class GatherTab:
    """Defines a tab for use in the gather UI."""

    def __init__(self, window: GatherWindow) -> None:
        self._window = weakref.ref(window)

    @property
    def window(self) -> GatherWindow:
        """The GatherWindow that this tab belongs to."""
        window = self._window()
        if window is None:
            raise ba.NotFoundError("GatherTab's window no longer exists.")
        return window

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> ba.Widget:
        """Called when the tab becomes the active one.

        The tab should create and return a container widget covering the
        specified region.
        """

    def on_deactivate(self) -> None:
        """Called when the tab will no longer be the active one."""

    def save_state(self) -> None:
        """Called when the parent window is saving state."""

    def restore_state(self) -> None:
        """Called when the parent window is restoring state."""
