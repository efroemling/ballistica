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

from ba._error import print_exception

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

        customdata
            A dict for use by the current ba.Session for
            storing data associated with this team.
            Unlike customdata, this persists for the duration
            of the session.
    """

    # Annotate our attr types at the class level so they're introspectable.
    name: Union[ba.Lstr, str]
    color: Tuple[float, ...]  # FIXME: can't we make this fixed len?
    players: List[ba.SessionPlayer]
    customdata: dict
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
        self.customdata = {}
        self.activityteam: Optional[Team] = None

    def leave(self) -> None:
        """(internal)"""
        self.customdata = {}


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
    color: Tuple[float, ...]  # FIXME: can't we make this fixed length?
    _sessionteam: ReferenceType[SessionTeam]
    _expired: bool
    _postinited: bool
    _customdata: dict

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
        self._customdata = {}
        self._expired = False
        self._postinited = True

    def manual_init(self, team_id: int, name: Union[ba.Lstr, str],
                    color: Tuple[float, ...]) -> None:
        """Manually init a team for uses such as bots."""
        self.id = team_id
        self.name = name
        self.color = color
        self._customdata = {}
        self._expired = False
        self._postinited = True

    @property
    def customdata(self) -> dict:
        """Arbitrary values associated with the team.
        Though it is encouraged that most player values be properly defined
        on the ba.Team subclass, it may be useful for player-agnostic
        objects to store values here. This dict is cleared when the team
        leaves or expires so objects stored here will be disposed of at
        the expected time, unlike the Team instance itself which may
        continue to be referenced after it is no longer part of the game.
        """
        assert self._postinited
        assert not self._expired
        return self._customdata

    def leave(self) -> None:
        """Called when the Team leaves a running game.

        (internal)
        """
        assert self._postinited
        assert not self._expired
        del self._customdata
        del self.players

    def expire(self) -> None:
        """Called when the Team is expiring (due to the Activity expiring).

        (internal)
        """
        assert self._postinited
        assert not self._expired
        self._expired = True

        try:
            self.on_expire()
        except Exception:
            print_exception(f'Error in on_expire for {self}.')

        del self._customdata
        del self.players

    def on_expire(self) -> None:
        """Can be overridden to handle team expiration."""

    @property
    def sessionteam(self) -> SessionTeam:
        """Return the ba.SessionTeam corresponding to this Team.

        Throws a ba.SessionTeamNotFoundError if there is none.
        """
        assert self._postinited
        if self._sessionteam is not None:
            sessionteam = self._sessionteam()
            if sessionteam is not None:
                return sessionteam
        from ba import _error
        raise _error.SessionTeamNotFoundError()


class EmptyTeam(Team['ba.EmptyPlayer']):
    """An empty player for use by Activities that don't need to define one.

    Category: Gameplay Classes

    ba.Player and ba.Team are 'Generic' types, and so passing them as
    type arguments when defining a ba.Activity reduces type safety.
    For example, activity.teams[0].player will have type 'Any' in that case.
    For that reason, it is better to pass EmptyPlayer and EmptyTeam when
    defining a ba.Activity that does not need custom types of its own.

    Note that EmptyPlayer defines its team type as EmptyTeam and vice versa,
    so if you want to define your own class for one of them you must do so
    for both.
    """
