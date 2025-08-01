# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to teams sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1
import babase

from bautils.tourny import (
    TournamentScreenActivity,
    NextScreenActivityMessage,
    register_screen_activity,
)

if TYPE_CHECKING:
    pass


@register_screen_activity
class PointsTableScreen(TournamentScreenActivity):
    """_summary_

    Args:
        TournamentScreenActivity (_type_): _description_
    """

    @override
    def on_player_join(self, player: bascenev1.Player) -> None:
        player.assigninput(
            (
                babase.InputType.JUMP_PRESS,
                babase.InputType.BOMB_PRESS,
                babase.InputType.PICK_UP_PRESS,
            ),
            babase.Call(self.handlemessage, NextScreenActivityMessage(2)),
        )
        player.assigninput(
            (babase.InputType.UP_PRESS, babase.InputType.DOWN_PRESS),
            babase.Call(bascenev1.broadcastmessage, "scroll"),
        )

    @override
    def on_transition_in(self) -> None:
        print("we are on points table screen.")

    @override
    def on_transition_out(self) -> None:
        print("we are out of points table screen.")

    @override
    @staticmethod
    def get_screen_index() -> int:
        return 1
