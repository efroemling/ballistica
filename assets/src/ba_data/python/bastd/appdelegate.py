# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Provide our delegate for high level app functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Type, Any, Dict, Callable, Optional


class AppDelegate(ba.AppDelegate):
    """Defines handlers for high level app functionality."""

    def create_default_game_settings_ui(
            self, gameclass: Type[ba.GameActivity],
            sessionclass: Type[ba.Session], config: Optional[Dict[str, Any]],
            completion_call: Callable[[Optional[Dict[str, Any]]],
                                      Any]) -> None:
        """(internal)"""

        # Replace the main window once we come up successfully.
        from bastd.ui.playlist.editgame import PlaylistEditGameWindow
        prev_window = ba.app.main_menu_window
        ba.app.main_menu_window = (PlaylistEditGameWindow(
            gameclass, sessionclass, config,
            completion_call=completion_call).get_root_widget())
        ba.containerwidget(edit=prev_window, transition='out_left')
