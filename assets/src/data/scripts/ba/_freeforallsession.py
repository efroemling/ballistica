"""Functionality related to free-for-all sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._teambasesession import TeamBaseSession

if TYPE_CHECKING:
    from typing import Dict
    import ba


class FreeForAllSession(TeamBaseSession):
    """ba.Session type for free-for-all mode games.

    Category: Gameplay Classes
    """
    _use_teams = False
    _playlist_selection_var = 'Free-for-All Playlist Selection'
    _playlist_randomize_var = 'Free-for-All Playlist Randomize'
    _playlists_var = 'Free-for-All Playlists'

    def get_ffa_point_awards(self) -> Dict[int, int]:
        """Return the number of points awarded for different rankings.

        This is based on the current number of players.
        """
        point_awards: Dict[int, int]
        if len(self.players) == 1:
            point_awards = {}
        elif len(self.players) == 2:
            point_awards = {0: 6}
        elif len(self.players) == 3:
            point_awards = {0: 6, 1: 3}
        elif len(self.players) == 4:
            point_awards = {0: 8, 1: 4, 2: 2}
        elif len(self.players) == 5:
            point_awards = {0: 8, 1: 4, 2: 2}
        elif len(self.players) == 6:
            point_awards = {0: 8, 1: 4, 2: 2}
        else:
            point_awards = {0: 8, 1: 4, 2: 2, 3: 1}
        return point_awards

    def __init__(self) -> None:
        _ba.increment_analytics_count('Free-for-all session start')
        super().__init__()

    def _switch_to_score_screen(self, results: ba.TeamGameResults) -> None:
        # pylint: disable=cyclic-import
        from bastd.activity import drawscreen
        from bastd.activity import multiteamendscreen
        from bastd.activity import freeforallendscreen
        winners = results.get_winners()

        # If there's multiple players and everyone has the same score,
        # call it a draw.
        if len(self.players) > 1 and len(winners) < 2:
            self.set_activity(
                _ba.new_activity(drawscreen.DrawScoreScreenActivity,
                                 {'results': results}))
        else:
            # Award different point amounts based on number of players.
            point_awards = self.get_ffa_point_awards()

            for i, winner in enumerate(winners):
                for team in winner.teams:
                    points = (point_awards[i] if i in point_awards else 0)
                    team.sessiondata['previous_score'] = (
                        team.sessiondata['score'])
                    team.sessiondata['score'] += points

            series_winners = [
                team for team in self.teams
                if team.sessiondata['score'] >= self._ffa_series_length
            ]
            series_winners.sort(reverse=True,
                                key=lambda tm: (tm.sessiondata['score']))
            if (len(series_winners) == 1
                    or (len(series_winners) > 1
                        and series_winners[0].sessiondata['score'] !=
                        series_winners[1].sessiondata['score'])):
                self.set_activity(
                    _ba.new_activity(
                        multiteamendscreen.
                        TeamSeriesVictoryScoreScreenActivity,
                        {'winner': series_winners[0]}))
            else:
                self.set_activity(
                    _ba.new_activity(
                        freeforallendscreen.
                        FreeForAllVictoryScoreScreenActivity,
                        {'results': results}))
