# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

from __future__ import annotations

import bascenev1 as bs
from bautils.chatutils import ServerCommand, register_command


@register_command
class End(ServerCommand):
    """
    /End
    """

    def on_command_call(self) -> None:
        game = bs.get_foreground_host_activity()
        with game.context:
            game.end_game()
