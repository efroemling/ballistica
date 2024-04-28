# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to teams sessions."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

import babase

import _bascenev1
from bascenev1._multiteamsession import MultiTeamSession

if TYPE_CHECKING:
    import bascenev1


class DualTeamSession(MultiTeamSession):
    """bascenev1.Session type for teams mode games.

    Category: **Gameplay Classes**
    """

    # Base class overrides:
    use_teams = True
    use_team_colors = True

    _playlist_selection_var = 'Team Tournament Playlist Selection'
    _playlist_randomize_var = 'Team Tournament Playlist Randomize'
    _playlists_var = 'Team Tournament Playlists'

    def __init__(self) -> None:
        babase.increment_analytics_count('Teams session start')
        super().__init__()

    @override
    def _switch_to_score_screen(self, results: bascenev1.GameResults) -> None:
        # pylint: disable=cyclic-import
        from bascenev1lib.activity.multiteamvictory import (
            TeamSeriesVictoryScoreScreenActivity,
        )
        from bascenev1lib.activity.dualteamscore import (
            TeamVictoryScoreScreenActivity,
        )
        from bascenev1lib.activity.drawscore import DrawScoreScreenActivity

        winnergroups = results.winnergroups

        # If everyone has the same score, call it a draw.
        if len(winnergroups) < 2:
            self.setactivity(_bascenev1.newactivity(DrawScoreScreenActivity))
        else:
            winner = winnergroups[0].teams[0]
            winner.customdata['score'] += 1

            # If a team has won, show final victory screen.
            if winner.customdata['score'] >= (self._series_length - 1) / 2 + 1:
                self.setactivity(
                    _bascenev1.newactivity(
                        TeamSeriesVictoryScoreScreenActivity,
                        {'winner': winner},
                    )
                )
            else:
                self.setactivity(
                    _bascenev1.newactivity(
                        TeamVictoryScoreScreenActivity, {'winner': winner}
                    )
                )
