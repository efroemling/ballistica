# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to teams sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1
from .joinactivity import TournamentJoinActivity
from .screen import TournamentScreenActivities
from .lobby import RegisterTournamentMessage

if TYPE_CHECKING:
    from typing import Any


class TournamentSession(bascenev1.MultiTeamSession):
    """Common base for all custom Tournament related sessions."""

    def __init__(self) -> None:
        """Set up playlists & launch a bascenev1.Activity to accept joiners."""
        super().__init__()

        # Start in our custom join screen.
        self.setactivity(bascenev1.newactivity(TournamentJoinActivity))

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, RegisterTournamentMessage):
            self._on_player_ready(msg.chooser)  # type: ignore

    @override
    def on_activity_end(
        self, activity: bascenev1.Activity, results: Any
    ) -> None:
        # pylint: disable=cyclic-import

        # If we have a tutorial to show, that's the first thing we do no
        # matter what.
        if self._tutorial_activity_instance is not None:
            self.setactivity(self._tutorial_activity_instance)
            self._tutorial_activity_instance = None

        # If we're leaving the tutorial activity, pop a transition activity
        # to transition us into a round gracefully (otherwise we'd snap from
        # one terrain to another instantly).
        if isinstance(activity, TournamentJoinActivity):
            # self._complete_end_activity(activity, {})
            tourny_scr_act = TournamentScreenActivities.get_next_screen_act()
            self.setactivity(bascenev1.newactivity(tourny_scr_act))
