# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to teams sessions."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._multiteamsession import MultiTeamSession

if TYPE_CHECKING:
    import ba


class DualTeamSession(MultiTeamSession):
    """ba.Session type for teams mode games.

    Category: **Gameplay Classes**
    """

    # Base class overrides:
    use_teams = True
    use_team_colors = True

    _playlist_selection_var = 'Team Tournament Playlist Selection'
    _playlist_randomize_var = 'Team Tournament Playlist Randomize'
    _playlists_var = 'Team Tournament Playlists'

    def __init__(self) -> None:
        _ba.increment_analytics_count('Teams session start')
        super().__init__()

    def _switch_to_score_screen(self, results: ba.GameResults) -> None:
        # pylint: disable=cyclic-import
        from bastd.activity.drawscore import DrawScoreScreenActivity
        from bastd.activity.dualteamscore import TeamVictoryScoreScreenActivity
        from bastd.activity.multiteamvictory import (
            TeamSeriesVictoryScoreScreenActivity,
        )

        winnergroups = results.winnergroups

        # If everyone has the same score, call it a draw.
        if len(winnergroups) < 2:
            self.setactivity(_ba.newactivity(DrawScoreScreenActivity))
        else:
            winner = winnergroups[0].teams[0]
            winner.customdata['score'] += 1

            # If a team has won, show final victory screen.
            if winner.customdata['score'] >= (self._series_length - 1) / 2 + 1:
                self.setactivity(
                    _ba.newactivity(
                        TeamSeriesVictoryScoreScreenActivity, {'winner': winner}
                    )
                )
            else:
                self.setactivity(
                    _ba.newactivity(
                        TeamVictoryScoreScreenActivity, {'winner': winner}
                    )
                )
