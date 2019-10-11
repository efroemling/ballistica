# Copyright (c) 2011-2019 Eric Froemling
"""Provide our delegate for high level app functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Type, Any, Dict, Callable, Optional


class AppDelegate(ba.AppDelegate):
    """Defines handlers for high level app functionality."""

    def create_default_game_config_ui(
            self, gameclass: Type[ba.GameActivity],
            sessionclass: Type[ba.Session], config: Optional[Dict[str, Any]],
            completion_call: Callable[[Optional[Dict[str, Any]]], Any]
    ) -> None:
        """(internal)"""

        # Replace the main window once we come up successfully.
        from bastd.ui.playlist.editgame import PlaylistEditGameWindow
        prev_window = ba.app.main_menu_window
        ba.app.main_menu_window = (PlaylistEditGameWindow(
            gameclass, sessionclass, config,
            completion_call=completion_call).get_root_widget())
        ba.containerwidget(edit=prev_window, transition='out_left')
