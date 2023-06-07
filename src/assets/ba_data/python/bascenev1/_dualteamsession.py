# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to teams sessions."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _babase
import _bascenev1
from bascenev1._multiteamsession import MultiTeamSession

if TYPE_CHECKING:
    import babase
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
        _babase.increment_analytics_count('Teams session start')
        super().__init__()

    def _switch_to_score_screen(self, results: bascenev1.GameResults) -> None:
        # pylint: disable=cyclic-import
        classic = _babase.app.classic
        assert classic is not None

        draw_score_screen_activity = classic.get_draw_score_screen_activity()
        team_victory_score_screen_activity = (
            classic.get_team_series_victory_score_screen_activity()
        )
        team_series_victory_score_screen_activity = (
            classic.get_team_series_victory_score_screen_activity()
        )
        winnergroups = results.winnergroups

        # If everyone has the same score, call it a draw.
        if len(winnergroups) < 2:
            self.setactivity(_bascenev1.newactivity(draw_score_screen_activity))
        else:
            winner = winnergroups[0].teams[0]
            winner.customdata['score'] += 1

            # If a team has won, show final victory screen.
            if winner.customdata['score'] >= (self._series_length - 1) / 2 + 1:
                self.setactivity(
                    _bascenev1.newactivity(
                        team_series_victory_score_screen_activity,
                        {'winner': winner},
                    )
                )
            else:
                self.setactivity(
                    _bascenev1.newactivity(
                        team_victory_score_screen_activity, {'winner': winner}
                    )
                )
