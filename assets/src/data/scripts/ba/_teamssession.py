"""Functionality related to teams sessions."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba import _teambasesession

if TYPE_CHECKING:
    import ba


class TeamsSession(_teambasesession.TeamBaseSession):
    """ba.Session type for teams mode games.

    Category: Gameplay Classes
    """
    _use_teams = True
    _playlist_selection_var = 'Team Tournament Playlist Selection'
    _playlist_randomize_var = 'Team Tournament Playlist Randomize'
    _playlists_var = 'Team Tournament Playlists'

    def __init__(self) -> None:
        _ba.increment_analytics_count('Teams session start')
        super().__init__()

    def _switch_to_score_screen(self, results: ba.TeamGameResults) -> None:
        # pylint: disable=cyclic-import
        from bastd.activity import drawscreen
        from bastd.activity import dualteamscorescreen
        from bastd.activity import multiteamendscreen
        winners = results.get_winners()

        # If everyone has the same score, call it a draw.
        if len(winners) < 2:
            self.set_activity(
                _ba.new_activity(drawscreen.DrawScoreScreenActivity))
        else:
            winner = winners[0].teams[0]
            winner.sessiondata['score'] += 1

            # If a team has won, show final victory screen.
            if winner.sessiondata['score'] >= (self._series_length -
                                               1) / 2 + 1:
                self.set_activity(
                    _ba.new_activity(
                        multiteamendscreen.
                        TeamSeriesVictoryScoreScreenActivity,
                        {'winner': winner}))
            else:
                self.set_activity(
                    _ba.new_activity(
                        dualteamscorescreen.TeamVictoryScoreScreenActivity,
                        {'winner': winner}))
