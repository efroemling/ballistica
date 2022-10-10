# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to game results."""
from __future__ import annotations

import copy
import weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.util import asserttype
from ba._team import Team, SessionTeam

if TYPE_CHECKING:
    from typing import Sequence
    import ba


@dataclass
class WinnerGroup:
    """Entry for a winning team or teams calculated by game-results."""

    score: int | None
    teams: Sequence[ba.SessionTeam]


class GameResults:
    """
    Results for a completed game.

    Category: **Gameplay Classes**

    Upon completion, a game should fill one of these out and pass it to its
    ba.Activity.end call.
    """

    def __init__(self) -> None:
        self._game_set = False
        self._scores: dict[
            int, tuple[weakref.ref[ba.SessionTeam], int | None]
        ] = {}
        self._sessionteams: list[weakref.ref[ba.SessionTeam]] | None = None
        self._playerinfos: list[ba.PlayerInfo] | None = None
        self._lower_is_better: bool | None = None
        self._score_label: str | None = None
        self._none_is_winner: bool | None = None
        self._scoretype: ba.ScoreType | None = None

    def set_game(self, game: ba.GameActivity) -> None:
        """Set the game instance these results are applying to."""
        if self._game_set:
            raise RuntimeError('Game set twice for GameResults.')
        self._game_set = True
        self._sessionteams = [
            weakref.ref(team.sessionteam) for team in game.teams
        ]
        scoreconfig = game.getscoreconfig()
        self._playerinfos = copy.deepcopy(game.initialplayerinfos)
        self._lower_is_better = scoreconfig.lower_is_better
        self._score_label = scoreconfig.label
        self._none_is_winner = scoreconfig.none_is_winner
        self._scoretype = scoreconfig.scoretype

    def set_team_score(self, team: ba.Team, score: int | None) -> None:
        """Set the score for a given team.

        This can be a number or None.
        (see the none_is_winner arg in the constructor)
        """
        assert isinstance(team, Team)
        sessionteam = team.sessionteam
        self._scores[sessionteam.id] = (weakref.ref(sessionteam), score)

    def get_sessionteam_score(self, sessionteam: ba.SessionTeam) -> int | None:
        """Return the score for a given ba.SessionTeam."""
        assert isinstance(sessionteam, SessionTeam)
        for score in list(self._scores.values()):
            if score[0]() is sessionteam:
                return score[1]

        # If we have no score value, assume None.
        return None

    @property
    def sessionteams(self) -> list[ba.SessionTeam]:
        """Return all ba.SessionTeams in the results."""
        if not self._game_set:
            raise RuntimeError("Can't get teams until game is set.")
        teams = []
        assert self._sessionteams is not None
        for team_ref in self._sessionteams:
            team = team_ref()
            if team is not None:
                teams.append(team)
        return teams

    def has_score_for_sessionteam(self, sessionteam: ba.SessionTeam) -> bool:
        """Return whether there is a score for a given session-team."""
        return any(s[0]() is sessionteam for s in self._scores.values())

    def get_sessionteam_score_str(self, sessionteam: ba.SessionTeam) -> ba.Lstr:
        """Return the score for the given session-team as an Lstr.

        (properly formatted for the score type.)
        """
        from ba._gameutils import timestring
        from ba._language import Lstr
        from ba._generated.enums import TimeFormat
        from ba._score import ScoreType

        if not self._game_set:
            raise RuntimeError("Can't get team-score-str until game is set.")
        for score in list(self._scores.values()):
            if score[0]() is sessionteam:
                if score[1] is None:
                    return Lstr(value='-')
                if self._scoretype is ScoreType.SECONDS:
                    return timestring(
                        score[1] * 1000,
                        centi=False,
                        timeformat=TimeFormat.MILLISECONDS,
                    )
                if self._scoretype is ScoreType.MILLISECONDS:
                    return timestring(
                        score[1], centi=True, timeformat=TimeFormat.MILLISECONDS
                    )
                return Lstr(value=str(score[1]))
        return Lstr(value='-')

    @property
    def playerinfos(self) -> list[ba.PlayerInfo]:
        """Get info about the players represented by the results."""
        if not self._game_set:
            raise RuntimeError("Can't get player-info until game is set.")
        assert self._playerinfos is not None
        return self._playerinfos

    @property
    def scoretype(self) -> ba.ScoreType:
        """The type of score."""
        if not self._game_set:
            raise RuntimeError("Can't get score-type until game is set.")
        assert self._scoretype is not None
        return self._scoretype

    @property
    def score_label(self) -> str:
        """The label associated with scores ('points', etc)."""
        if not self._game_set:
            raise RuntimeError("Can't get score-label until game is set.")
        assert self._score_label is not None
        return self._score_label

    @property
    def lower_is_better(self) -> bool:
        """Whether lower scores are better."""
        if not self._game_set:
            raise RuntimeError("Can't get lower-is-better until game is set.")
        assert self._lower_is_better is not None
        return self._lower_is_better

    @property
    def winning_sessionteam(self) -> ba.SessionTeam | None:
        """The winning ba.SessionTeam if there is exactly one, or else None."""
        if not self._game_set:
            raise RuntimeError("Can't get winners until game is set.")
        winners = self.winnergroups
        if winners and len(winners[0].teams) == 1:
            return winners[0].teams[0]
        return None

    @property
    def winnergroups(self) -> list[WinnerGroup]:
        """Get an ordered list of winner groups."""
        if not self._game_set:
            raise RuntimeError("Can't get winners until game is set.")

        # Group by best scoring teams.
        winners: dict[int, list[ba.SessionTeam]] = {}
        scores = [
            score
            for score in self._scores.values()
            if score[0]() is not None and score[1] is not None
        ]
        for score in scores:
            assert score[1] is not None
            sval = winners.setdefault(score[1], [])
            team = score[0]()
            assert team is not None
            sval.append(team)
        results: list[tuple[int | None, list[ba.SessionTeam]]] = list(
            winners.items()
        )
        results.sort(
            reverse=not self._lower_is_better,
            key=lambda x: asserttype(x[0], int),
        )

        # Also group the 'None' scores.
        none_sessionteams: list[ba.SessionTeam] = []
        for score in self._scores.values():
            scoreteam = score[0]()
            if scoreteam is not None and score[1] is None:
                none_sessionteams.append(scoreteam)

        # Add the Nones to the list (either as winners or losers
        # depending on the rules).
        if none_sessionteams:
            nones: list[tuple[int | None, list[ba.SessionTeam]]] = [
                (None, none_sessionteams)
            ]
            if self._none_is_winner:
                results = nones + results
            else:
                results = results + nones

        return [WinnerGroup(score, team) for score, team in results]
