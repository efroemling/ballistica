# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to free-for-all sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._multiteamsession import MultiTeamSession

if TYPE_CHECKING:
    import ba


class FreeForAllSession(MultiTeamSession):
    """ba.Session type for free-for-all mode games.

    Category: **Gameplay Classes**
    """

    use_teams = False
    use_team_colors = False
    _playlist_selection_var = 'Free-for-All Playlist Selection'
    _playlist_randomize_var = 'Free-for-All Playlist Randomize'
    _playlists_var = 'Free-for-All Playlists'

    def get_ffa_point_awards(self) -> dict[int, int]:
        """Return the number of points awarded for different rankings.

        This is based on the current number of players.
        """
        point_awards: dict[int, int]
        if len(self.sessionplayers) == 1:
            point_awards = {}
        elif len(self.sessionplayers) == 2:
            point_awards = {0: 6}
        elif len(self.sessionplayers) == 3:
            point_awards = {0: 6, 1: 3}
        elif len(self.sessionplayers) == 4:
            point_awards = {0: 8, 1: 4, 2: 2}
        elif len(self.sessionplayers) == 5:
            point_awards = {0: 8, 1: 4, 2: 2}
        elif len(self.sessionplayers) == 6:
            point_awards = {0: 8, 1: 4, 2: 2}
        else:
            point_awards = {0: 8, 1: 4, 2: 2, 3: 1}
        return point_awards

    def __init__(self) -> None:
        _ba.increment_analytics_count('Free-for-all session start')
        super().__init__()

    def _switch_to_score_screen(self, results: ba.GameResults) -> None:
        # pylint: disable=cyclic-import
        from efro.util import asserttype
        from bastd.activity.drawscore import DrawScoreScreenActivity
        from bastd.activity.multiteamvictory import (
            TeamSeriesVictoryScoreScreenActivity,
        )
        from bastd.activity.freeforallvictory import (
            FreeForAllVictoryScoreScreenActivity,
        )

        winners = results.winnergroups

        # If there's multiple players and everyone has the same score,
        # call it a draw.
        if len(self.sessionplayers) > 1 and len(winners) < 2:
            self.setactivity(
                _ba.newactivity(DrawScoreScreenActivity, {'results': results})
            )
        else:
            # Award different point amounts based on number of players.
            point_awards = self.get_ffa_point_awards()

            for i, winner in enumerate(winners):
                for team in winner.teams:
                    points = point_awards[i] if i in point_awards else 0
                    team.customdata['previous_score'] = team.customdata['score']
                    team.customdata['score'] += points

            series_winners = [
                team
                for team in self.sessionteams
                if team.customdata['score'] >= self._ffa_series_length
            ]
            series_winners.sort(
                reverse=True,
                key=lambda t: asserttype(t.customdata['score'], int),
            )
            if len(series_winners) == 1 or (
                len(series_winners) > 1
                and series_winners[0].customdata['score']
                != series_winners[1].customdata['score']
            ):
                self.setactivity(
                    _ba.newactivity(
                        TeamSeriesVictoryScoreScreenActivity,
                        {'winner': series_winners[0]},
                    )
                )
            else:
                self.setactivity(
                    _ba.newactivity(
                        FreeForAllVictoryScoreScreenActivity,
                        {'results': results},
                    )
                )
