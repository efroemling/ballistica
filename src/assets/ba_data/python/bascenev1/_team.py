# Released under the MIT License. See LICENSE for details.
#
"""Team related functionality."""

from __future__ import annotations

import weakref
import logging
from typing import TYPE_CHECKING, TypeVar, Generic

import babase

if TYPE_CHECKING:
    from typing import Sequence

    import bascenev1


class SessionTeam:
    """A team of one or more bascenev1.SessionPlayers.

    Category: **Gameplay Classes**

    Note that a SessionPlayer *always* has a SessionTeam;
    in some cases, such as free-for-all bascenev1.Sessions,
    each SessionTeam consists of just one SessionPlayer.
    """

    # Annotate our attr types at the class level so they're introspectable.

    name: babase.Lstr | str
    """The team's name."""

    color: tuple[float, ...]  # FIXME: can't we make this fixed len?
    """The team's color."""

    players: list[bascenev1.SessionPlayer]
    """The list of bascenev1.SessionPlayer-s on the team."""

    customdata: dict
    """A dict for use by the current bascenev1.Session for
       storing data associated with this team.
       Unlike customdata, this persists for the duration
       of the session."""

    id: int
    """The unique numeric id of the team."""

    def __init__(
        self,
        team_id: int = 0,
        name: babase.Lstr | str = '',
        color: Sequence[float] = (1.0, 1.0, 1.0),
    ):
        """Instantiate a bascenev1.SessionTeam.

        In most cases, all teams are provided to you by the bascenev1.Session,
        bascenev1.Session, so calling this shouldn't be necessary.
        """

        self.id = team_id
        self.name = name
        self.color = tuple(color)
        self.players = []
        self.customdata = {}
        self.activityteam: Team | None = None

    def leave(self) -> None:
        """(internal)"""
        self.customdata = {}


PlayerT = TypeVar('PlayerT', bound='bascenev1.Player')


class Team(Generic[PlayerT]):
    """A team in a specific bascenev1.Activity.

    Category: **Gameplay Classes**

    These correspond to bascenev1.SessionTeam objects, but are created
    per activity so that the activity can use its own custom team subclass.
    """

    # Defining these types at the class level instead of in __init__ so
    # that types are introspectable (these are still instance attrs).
    players: list[PlayerT]
    id: int
    name: babase.Lstr | str
    color: tuple[float, ...]  # FIXME: can't we make this fixed length?
    _sessionteam: weakref.ref[SessionTeam]
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
                f' in the class decorator.'
            )

        self.players = []
        self._sessionteam = weakref.ref(sessionteam)
        self.id = sessionteam.id
        self.name = sessionteam.name
        self.color = sessionteam.color
        self._customdata = {}
        self._expired = False
        self._postinited = True

    def manual_init(
        self, team_id: int, name: babase.Lstr | str, color: tuple[float, ...]
    ) -> None:
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
        on the bascenev1.Team subclass, it may be useful for player-agnostic
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
            logging.exception('Error in on_expire for %s.', self)

        del self._customdata
        del self.players

    def on_expire(self) -> None:
        """Can be overridden to handle team expiration."""

    @property
    def sessionteam(self) -> SessionTeam:
        """Return the bascenev1.SessionTeam corresponding to this Team.

        Throws a babase.SessionTeamNotFoundError if there is none.
        """
        assert self._postinited
        if self._sessionteam is not None:
            sessionteam = self._sessionteam()
            if sessionteam is not None:
                return sessionteam

        raise babase.SessionTeamNotFoundError()


class EmptyTeam(Team['bascenev1.EmptyPlayer']):
    """An empty player for use by Activities that don't need to define one.

    Category: **Gameplay Classes**

    bascenev1.Player and bascenev1.Team are 'Generic' types, and so passing
    those top level classes as type arguments when defining a
    bascenev1.Activity reduces type safety. For example,
    activity.teams[0].player will have type 'Any' in that case. For that
    reason, it is better to pass EmptyPlayer and EmptyTeam when defining
    a bascenev1.Activity that does not need custom types of its own.

    Note that EmptyPlayer defines its team type as EmptyTeam and vice versa,
    so if you want to define your own class for one of them you should do so
    for both.
    """
