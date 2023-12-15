# Released under the MIT License. See LICENSE for details.
#
"""Defines AppDelegate class for handling high level app functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    from typing import Callable
    import bascenev1


class AppDelegate:
    """Defines handlers for high level app functionality.

    Category: App Classes
    """

    def create_default_game_settings_ui(
        self,
        gameclass: type[bascenev1.GameActivity],
        sessiontype: type[bascenev1.Session],
        settings: dict | None,
        completion_call: Callable[[dict | None], None],
    ) -> None:
        """Launch a UI to configure the given game config.

        It should manipulate the contents of config and call completion_call
        when done.
        """
        # Replace the main window once we come up successfully.
        from bauiv1lib.playlist.editgame import PlaylistEditGameWindow

        assert babase.app.classic is not None
        babase.app.ui_v1.clear_main_menu_window(transition='out_left')
        babase.app.ui_v1.set_main_menu_window(
            PlaylistEditGameWindow(
                gameclass,
                sessiontype,
                settings,
                completion_call=completion_call,
            ).get_root_widget(),
            from_window=False,  # Disable check since we don't know.
        )
