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
"""Functionality related to game results."""
from __future__ import annotations

import copy
import weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import Sequence, Tuple, Any, Optional, Dict, List
    import ba


@dataclass
class WinnerGroup:
    """Entry for a winning team or teams calculated by game-results."""
    score: Optional[int]
    teams: Sequence[ba.Team]


class TeamGameResults:
    """
    Results for a completed ba.TeamGameActivity.

    Category: Gameplay Classes

    Upon completion, a game should fill one of these out and pass it to its
    ba.Activity.end() call.
    """

    def __init__(self) -> None:
        """Instantiate a results instance."""
        self._game_set = False
        self._scores: Dict[int, Tuple[ReferenceType[ba.Team], int]] = {}
        self._teams: Optional[List[ReferenceType[ba.Team]]] = None
        self._player_info: Optional[List[Dict[str, Any]]] = None
        self._lower_is_better: Optional[bool] = None
        self._score_name: Optional[str] = None
        self._none_is_winner: Optional[bool] = None
        self._score_type: Optional[str] = None

    def set_game(self, game: ba.GameActivity) -> None:
        """Set the game instance these results are applying to."""
        if self._game_set:
            raise RuntimeError("Game set twice for TeamGameResults.")
        self._game_set = True
        self._teams = [weakref.ref(team) for team in game.teams]
        score_info = game.get_resolved_score_info()
        self._player_info = copy.deepcopy(game.initial_player_info)
        self._lower_is_better = score_info['lower_is_better']
        self._score_name = score_info['score_name']
        self._none_is_winner = score_info['none_is_winner']
        self._score_type = score_info['score_type']

    def set_team_score(self, team: ba.Team, score: int) -> None:
        """Set the score for a given ba.Team.

        This can be a number or None.
        (see the none_is_winner arg in the constructor)
        """
        self._scores[team.get_id()] = (weakref.ref(team), score)

    def get_team_score(self, team: ba.Team) -> Optional[int]:
        """Return the score for a given team."""
        for score in list(self._scores.values()):
            if score[0]() is team:
                return score[1]

        # If we have no score value, assume None.
        return None

    def get_teams(self) -> List[ba.Team]:
        """Return all ba.Teams in the results."""
        if not self._game_set:
            raise RuntimeError("Can't get teams until game is set.")
        teams = []
        assert self._teams is not None
        for team_ref in self._teams:
            team = team_ref()
            if team is not None:
                teams.append(team)
        return teams

    def has_score_for_team(self, team: ba.Team) -> bool:
        """Return whether there is a score for a given team."""
        for score in list(self._scores.values()):
            if score[0]() is team:
                return True
        return False

    def get_team_score_str(self, team: ba.Team) -> ba.Lstr:
        """Return the score for the given ba.Team as an Lstr.

        (properly formatted for the score type.)
        """
        from ba._gameutils import timestring
        from ba._lang import Lstr
        from ba._enums import TimeFormat
        if not self._game_set:
            raise RuntimeError("Can't get team-score-str until game is set.")
        for score in list(self._scores.values()):
            if score[0]() is team:
                if score[1] is None:
                    return Lstr(value='-')
                if self._score_type == 'seconds':
                    return timestring(score[1] * 1000,
                                      centi=False,
                                      timeformat=TimeFormat.MILLISECONDS)
                if self._score_type == 'milliseconds':
                    return timestring(score[1],
                                      centi=True,
                                      timeformat=TimeFormat.MILLISECONDS)
                return Lstr(value=str(score[1]))
        return Lstr(value='-')

    def get_player_info(self) -> List[Dict[str, Any]]:
        """Get info about the players represented by the results."""
        if not self._game_set:
            raise RuntimeError("Can't get player-info until game is set.")
        assert self._player_info is not None
        return self._player_info

    def get_score_type(self) -> str:
        """Get the type of score."""
        if not self._game_set:
            raise RuntimeError("Can't get score-type until game is set.")
        assert self._score_type is not None
        return self._score_type

    def get_score_name(self) -> str:
        """Get the name associated with scores ('points', etc)."""
        if not self._game_set:
            raise RuntimeError("Can't get score-name until game is set.")
        assert self._score_name is not None
        return self._score_name

    def get_lower_is_better(self) -> bool:
        """Return whether lower scores are better."""
        if not self._game_set:
            raise RuntimeError("Can't get lower-is-better until game is set.")
        assert self._lower_is_better is not None
        return self._lower_is_better

    def get_winning_team(self) -> Optional[ba.Team]:
        """Get the winning ba.Team if there is exactly one; None otherwise."""
        if not self._game_set:
            raise RuntimeError("Can't get winners until game is set.")
        winners = self.get_winners()
        if winners and len(winners[0].teams) == 1:
            return winners[0].teams[0]
        return None

    def get_winners(self) -> List[WinnerGroup]:
        """Get an ordered list of winner groups."""
        if not self._game_set:
            raise RuntimeError("Can't get winners until game is set.")

        # Group by best scoring teams.
        winners: Dict[int, List[ba.Team]] = {}
        scores = [
            score for score in self._scores.values()
            if score[0]() is not None and score[1] is not None
        ]
        for score in scores:
            sval = winners.setdefault(score[1], [])
            team = score[0]()
            assert team is not None
            sval.append(team)
        results: List[Tuple[Optional[int],
                            List[ba.Team]]] = list(winners.items())
        results.sort(reverse=not self._lower_is_better)

        # Also group the 'None' scores.
        none_teams: List[ba.Team] = []
        for score in self._scores.values():
            if score[0]() is not None and score[1] is None:
                none_teams.append(score[0]())

        # Add the Nones to the list (either as winners or losers
        # depending on the rules).
        if none_teams:
            nones: List[Tuple[Optional[int],
                              List[ba.Team]]] = [(None, none_teams)]
            if self._none_is_winner:
                results = nones + results
            else:
                results = results + nones

        return [WinnerGroup(score, team) for score, team in results]
