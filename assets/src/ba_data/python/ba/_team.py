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
"""Team related functionality."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, TypeVar, Generic

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import Dict, List, Sequence, Tuple, Union, Optional
    import ba


class SessionTeam:
    """A team of one or more ba.SessionPlayers.

    Category: Gameplay Classes

    Note that a SessionPlayer *always* has a SessionTeam;
    in some cases, such as free-for-all ba.Sessions,
    each SessionTeam consists of just one SessionPlayer.

    Attributes:

        name
            The team's name.

        id
            The unique numeric id of the team.

        color
            The team's color.

        players
            The list of ba.SessionPlayers on the team.

        gamedata
            A dict for use by the current ba.Activity
            for storing data associated with this team.
            This gets cleared for each new ba.Activity.

        sessiondata
            A dict for use by the current ba.Session for
            storing data associated with this team.
            Unlike gamedata, this persists for the duration
            of the session.
    """

    # Annotate our attr types at the class level so they're introspectable.
    name: Union[ba.Lstr, str]
    color: Tuple[float, ...]  # FIXME: can't we make this fixed len?
    players: List[ba.SessionPlayer]
    gamedata: Dict
    sessiondata: Dict
    id: int

    def __init__(self,
                 team_id: int = 0,
                 name: Union[ba.Lstr, str] = '',
                 color: Sequence[float] = (1.0, 1.0, 1.0)):
        """Instantiate a ba.SessionTeam.

        In most cases, all teams are provided to you by the ba.Session,
        ba.Session, so calling this shouldn't be necessary.
        """

        self.id = team_id
        self.name = name
        self.color = tuple(color)
        self.players = []
        self.gamedata = {}
        self.sessiondata = {}
        self.gameteam: Optional[Team] = None

    def reset_gamedata(self) -> None:
        """(internal)"""
        self.gamedata = {}

    def reset_sessiondata(self) -> None:
        """(internal)"""
        self.sessiondata = {}


PlayerType = TypeVar('PlayerType', bound='ba.Player')


class Team(Generic[PlayerType]):
    """A team in a specific ba.Activity.

    Category: Gameplay Classes

    These correspond to ba.SessionTeam objects, but are created per activity
    so that the activity can use its own custom team subclass.
    """

    # Defining these types at the class level instead of in __init__ so
    # that types are introspectable (these are still instance attrs).
    players: List[PlayerType]
    id: int
    name: Union[ba.Lstr, str]
    color: Tuple[float, ...]  # FIXME: can't we make this fixed len?
    _sessionteam: ReferenceType[SessionTeam]

    # TODO: kill these.
    gamedata: Dict
    sessiondata: Dict

    # NOTE: avoiding having any __init__() here since it seems to not
    # get called by default if a dataclass inherits from us.

    def postinit(self, sessionteam: SessionTeam) -> None:
        """Wire up a newly created SessionTeam.

        (internal)
        """

        # Sanity check; if a dataclass is created that inherits from us,
        # it will define an equality operator by default which will break
        # internal game logic. So complain loudly if we find one.
        if type(self).__eq__ is not object.__eq__:
            raise RuntimeError(
                f'Team class {type(self)} defines an equality'
                f' operator (__eq__) which will break internal'
                f' logic. Please remove it.\n'
                f'For dataclasses you can do "dataclass(eq=False)"'
                f' in the class decorator.')

        self.players = []
        self._sessionteam = weakref.ref(sessionteam)
        self.id = sessionteam.id
        self.name = sessionteam.name
        self.color = sessionteam.color
        self.gamedata = sessionteam.gamedata
        self.sessiondata = sessionteam.sessiondata

    def manual_init(self, team_id: int, name: Union[ba.Lstr, str],
                    color: Tuple[float, ...]) -> None:
        """Manually init a team for uses such as bots."""
        self.id = team_id
        self.name = name
        self.color = color
        self.gamedata = {}
        self.sessiondata = {}

    @property
    def sessionteam(self) -> SessionTeam:
        """Return the ba.SessionTeam corresponding to this Team.

        Throws a ba.SessionTeamNotFoundError if there is none.
        """
        if self._sessionteam is not None:
            sessionteam = self._sessionteam()
            if sessionteam is not None:
                return sessionteam
        from ba import _error
        raise _error.SessionTeamNotFoundError()
