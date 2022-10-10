# Released under the MIT License. See LICENSE for details.
#
"""Provide our delegate for high level app functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Callable


class AppDelegate(ba.AppDelegate):
    """Defines handlers for high level app functionality."""

    def create_default_game_settings_ui(
        self,
        gameclass: type[ba.GameActivity],
        sessiontype: type[ba.Session],
        settings: dict | None,
        completion_call: Callable[[dict | None], Any],
    ) -> None:
        """(internal)"""

        # Replace the main window once we come up successfully.
        from bastd.ui.playlist.editgame import PlaylistEditGameWindow

        ba.app.ui.clear_main_menu_window(transition='out_left')
        ba.app.ui.set_main_menu_window(
            PlaylistEditGameWindow(
                gameclass,
                sessiontype,
                settings,
                completion_call=completion_call,
            ).get_root_widget()
        )
