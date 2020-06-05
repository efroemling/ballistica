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
"""Player related functionality."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, Generic, cast

import _ba
from ba._error import (SessionPlayerNotFoundError, print_exception,
                       ActorNotFoundError)
from ba._messages import DeathType, DieMessage

if TYPE_CHECKING:
    from typing import (Type, Optional, Sequence, Dict, Any, Union, Tuple,
                        Callable)
    import ba

PlayerType = TypeVar('PlayerType', bound='ba.Player')
TeamType = TypeVar('TeamType', bound='ba.Team')


@dataclass
class PlayerInfo:
    """Holds basic info about a player.

    Category: Gameplay Classes
    """
    name: str
    character: str


@dataclass
class StandLocation:
    """Describes a point in space and an angle to face.

    Category: Gameplay Classes
    """
    position: ba.Vec3
    angle: Optional[float] = None


class Player(Generic[TeamType]):
    """A player in a specific ba.Activity.

    Category: Gameplay Classes

    These correspond to ba.SessionPlayer objects, but are associated with a
    single ba.Activity instance. This allows activities to specify their
    own custom ba.Player types.

    Attributes:

      actor
        The ba.Actor associated with the player.

    """

    # These are instance attrs but we define them at the type level so
    # their type annotations are introspectable (for docs generation).
    character: str
    actor: Optional[ba.Actor]
    color: Sequence[float]
    highlight: Sequence[float]

    _team: TeamType
    _sessionplayer: ba.SessionPlayer
    _nodeactor: Optional[ba.NodeActor]
    _expired: bool
    _postinited: bool
    _customdata: dict

    # NOTE: avoiding having any __init__() here since it seems to not
    # get called by default if a dataclass inherits from us.
    # This also lets us keep trivial player classes cleaner by skipping
    # the super().__init__() line.

    def postinit(self, sessionplayer: ba.SessionPlayer) -> None:
        """Wire up a newly created player.

        (internal)
        """
        from ba._nodeactor import NodeActor

        # Sanity check; if a dataclass is created that inherits from us,
        # it will define an equality operator by default which will break
        # internal game logic. So complain loudly if we find one.
        if type(self).__eq__ is not object.__eq__:
            raise RuntimeError(
                f'Player class {type(self)} defines an equality'
                f' operator (__eq__) which will break internal'
                f' logic. Please remove it.\n'
                f'For dataclasses you can do "dataclass(eq=False)"'
                f' in the class decorator.')

        self.actor = None
        self.character = ''
        self._nodeactor: Optional[ba.NodeActor] = None
        self._sessionplayer = sessionplayer
        self.character = sessionplayer.character
        self.color = sessionplayer.color
        self.highlight = sessionplayer.highlight
        self._team = cast(TeamType, sessionplayer.sessionteam.activityteam)
        assert self._team is not None
        self._customdata = {}
        self._expired = False
        self._postinited = True
        node = _ba.newnode('player', attrs={'playerID': sessionplayer.id})
        self._nodeactor = NodeActor(node)
        sessionplayer.setnode(node)

    def leave(self) -> None:
        """Called when the Player leaves a running game.

        (internal)
        """
        assert self._postinited
        assert not self._expired
        try:
            # If they still have an actor, kill it.
            if self.actor:
                self.actor.handlemessage(DieMessage(how=DeathType.LEFT_GAME))
            self.actor = None
        except Exception:
            print_exception(f'Error killing actor on leave for {self}')
        self._nodeactor = None
        del self._team
        del self._customdata

    def expire(self) -> None:
        """Called when the Player is expiring (when its Activity does so).

        (internal)
        """
        assert self._postinited
        assert not self._expired
        self._expired = True

        try:
            self.on_expire()
        except Exception:
            print_exception(f'Error in on_expire for {self}.')

        self._nodeactor = None
        self.actor = None
        del self._team
        del self._customdata

    def on_expire(self) -> None:
        """Can be overridden to handle player expiration.

        The player expires when the Activity it is a part of expires.
        Expired players should no longer run any game logic (which will
        likely error). They should, however, remove any references to
        players/teams/games/etc. which could prevent them from being freed.
        """

    @property
    def team(self) -> TeamType:
        """The ba.Team for this player."""
        assert self._postinited
        assert not self._expired
        return self._team

    @property
    def customdata(self) -> dict:
        """Arbitrary values associated with the player.
        Though it is encouraged that most player values be properly defined
        on the ba.Player subclass, it may be useful for player-agnostic
        objects to store values here. This dict is cleared when the player
        leaves or expires so objects stored here will be disposed of at
        the expected time, unlike the Player instance itself which may
        continue to be referenced after it is no longer part of the game.
        """
        assert self._postinited
        assert not self._expired
        return self._customdata

    @property
    def sessionplayer(self) -> ba.SessionPlayer:
        """Return the ba.SessionPlayer corresponding to this Player.

        Throws a ba.SessionPlayerNotFoundError if it does not exist.
        """
        assert self._postinited
        if bool(self._sessionplayer):
            return self._sessionplayer
        raise SessionPlayerNotFoundError()

    @property
    def node(self) -> ba.Node:
        """A ba.Node of type 'player' associated with this Player.

        This node can be used to get a generic player position/etc.
        """
        assert self._postinited
        assert not self._expired
        assert self._nodeactor
        return self._nodeactor.node

    @property
    def position(self) -> ba.Vec3:
        """The position of the player, as defined by its current ba.Actor.

        If the player currently has no actor, raises a ba.ActorNotFoundError.
        """
        assert self._postinited
        assert not self._expired
        if self.actor is None:
            raise ActorNotFoundError
        return _ba.Vec3(self.node.position)

    def exists(self) -> bool:
        """Whether the underlying player still exists.

        This will return False if the underlying ba.SessionPlayer has
        left the game or if the ba.Activity this player was associated
        with has ended.
        Most functionality will fail on a nonexistent player.
        Note that you can also use the boolean operator for this same
        functionality, so a statement such as "if player" will do
        the right thing both for Player objects and values of None.
        """
        assert self._postinited
        return self._sessionplayer.exists() and not self._expired

    def getname(self, full: bool = False, icon: bool = True) -> str:
        """getname(full: bool = False, icon: bool = True) -> str

        Returns the player's name. If icon is True, the long version of the
        name may include an icon.
        """
        assert self._postinited
        assert not self._expired
        return self._sessionplayer.getname(full=full, icon=icon)

    def is_alive(self) -> bool:
        """is_alive() -> bool

        Returns True if the player has a ba.Actor assigned and its
        is_alive() method return True. False is returned otherwise.
        """
        assert self._postinited
        assert not self._expired
        return self.actor is not None and self.actor.is_alive()

    def get_icon(self) -> Dict[str, Any]:
        """get_icon() -> Dict[str, Any]

        Returns the character's icon (images, colors, etc contained in a dict)
        """
        assert self._postinited
        assert not self._expired
        return self._sessionplayer.get_icon()

    def assigninput(self, inputtype: Union[ba.InputType, Tuple[ba.InputType,
                                                               ...]],
                    call: Callable) -> None:
        """assigninput(type: Union[ba.InputType, Tuple[ba.InputType, ...]],
          call: Callable) -> None

        Set the python callable to be run for one or more types of input.
        """
        assert self._postinited
        assert not self._expired
        return self._sessionplayer.assigninput(type=inputtype, call=call)

    def resetinput(self) -> None:
        """resetinput() -> None

        Clears out the player's assigned input actions.
        """
        assert self._postinited
        assert not self._expired
        self._sessionplayer.resetinput()

    def __bool__(self) -> bool:
        return self.exists()


class EmptyPlayer(Player['ba.EmptyTeam']):
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


# NOTE: It seems we might not need these playercast() calls; have gone
# the direction where things returning players generally take a type arg
# and do this themselves; that way the user is 'forced' to deal with types
# instead of requiring extra work by them.


def playercast(totype: Type[PlayerType], player: ba.Player) -> PlayerType:
    """Cast a ba.Player to a specific ba.Player subclass.

    Category: Gameplay Functions

    When writing type-checked code, sometimes code will deal with raw
    ba.Player objects which need to be cast back to the game's actual
    player type so that access can be properly type-checked. This function
    is a safe way to do so. It ensures that Optional values are not cast
    into Non-Optional, etc.
    """
    assert isinstance(player, totype)
    return player


# NOTE: ideally we should have a single playercast() call and use overloads
# for the optional variety, but that currently seems to not be working.
# See: https://github.com/python/mypy/issues/8800
def playercast_o(totype: Type[PlayerType],
                 player: Optional[ba.Player]) -> Optional[PlayerType]:
    """A variant of ba.playercast() for use with optional ba.Player values.

    Category: Gameplay Functions
    """
    assert isinstance(player, (totype, type(None)))
    return player
