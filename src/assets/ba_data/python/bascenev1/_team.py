# Released under the MIT License. See LICENSE for details.
#
"""Team related functionality."""

from __future__ import annotations

import weakref
import logging
from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    from typing import Sequence

    import bascenev1


class SessionTeam:
    """A team of one or more :class:`~bascenev1.SessionPlayer`.

    Note that a player will *always* have a team. in some cases, such as
    free-for-all :class:`~bascenev1.Session`, each team consists of
    just one player.
    """

    # We annotate our attr types at the class level so they're more
    # introspectable by docs tools/etc.

    #: The team's name.
    name: babase.Lstr | str

    #: The team's color.
    color: tuple[float, ...]  # FIXME: can't we make this fixed len?

    #: The list of players on the team.
    players: list[bascenev1.SessionPlayer]

    #: A dict for use by the current :class:`~bascenev1.Session` for
    #: storing data associated with this team. Unlike customdata, this
    #: persists for the duration of the session.
    customdata: dict

    #: The unique numeric id of the team.
    id: int

    def __init__(
        self,
        team_id: int = 0,
        name: babase.Lstr | str = '',
        color: Sequence[float] = (1.0, 1.0, 1.0),
    ):
        self.id = team_id
        self.name = name
        self.color = tuple(color)
        self.players = []
        self.customdata = {}
        self.activityteam: Team | None = None

    def leave(self) -> None:
        """(internal)

        :meta private:
        """
        self.customdata = {}


class Team[PlayerT: bascenev1.Player]:
    """A team in a specific :class:`~bascenev1.Activity`.

    These correspond to :class:`~bascenev1.SessionTeam` objects, but are
    created per activity so that the activity can use its own custom
    team subclass.
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
        """Internal: Wire up a newly created SessionTeam.

        :meta private:
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
        """Arbitrary values associated with the team. Though it is
        encouraged that most player values be properly defined on the
        :class:`~bascenev1.Team` subclass, it may be useful for
        player-agnostic objects to store values here. This dict is
        cleared when the team leaves or expires so objects stored here
        will be disposed of at the expected time, unlike the
        :class:`~bascenev1.Team` instance itself which may continue to
        be referenced after it is no longer part of the game.
        """
        assert self._postinited
        assert not self._expired
        return self._customdata

    def leave(self) -> None:
        """Internal: Called when the team leaves a running game.

        :meta private:
        """
        assert self._postinited
        assert not self._expired
        del self._customdata
        del self.players

    def expire(self) -> None:
        """Internal: Called when team is expiring (due to its activity).

        :meta private:
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
        """The :class:`~bascenev1.SessionTeam` corresponding to this team.

        Throws a :class:`~babase.SessionTeamNotFoundError` if there is
        none.
        """
        assert self._postinited
        if self._sessionteam is not None:
            sessionteam = self._sessionteam()
            if sessionteam is not None:
                return sessionteam

        raise babase.SessionTeamNotFoundError()


class EmptyTeam(Team['bascenev1.EmptyPlayer']):
    """An empty player for use by Activities that don't define one.

    bascenev1.Player and bascenev1.Team are 'Generic' types, and so
    passing those top level classes as type arguments when defining a
    bascenev1.Activity reduces type safety. For example,
    activity.teams[0].player will have type 'Any' in that case. For that
    reason, it is better to pass EmptyPlayer and EmptyTeam when defining
    a bascenev1.Activity that does not need custom types of its own.

    Note that EmptyPlayer defines its team type as EmptyTeam and vice
    versa, so if you want to define your own class for one of them you
    should do so for both.
    """
