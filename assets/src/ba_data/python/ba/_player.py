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

from typing import TYPE_CHECKING, TypeVar, Generic

if TYPE_CHECKING:
    from typing import (Type, Optional, Sequence, Dict, Any, Union, Tuple,
                        Callable)
    import ba

TeamType = TypeVar('TeamType', bound='ba.Team')


class Player(Generic[TeamType]):
    """Testing."""

    # Defining these types at the class level instead of in __init__ so
    # that types are introspectable (these are still instance attrs).
    team: TeamType
    character: str
    actor: Optional[ba.Actor]
    color: Sequence[float]
    highlight: Sequence[float]
    _sessionplayer: ba.SessionPlayer
    _nodeactor: Optional[ba.NodeActor]

    # Should aim to kill this eventually (at least gamedata).
    # Game-specific data can be tacked on to the per-game player class.
    sessiondata: Dict
    gamedata: Dict

    # NOTE: avoiding having any __init__() here since it seems to not
    # get called by default if a dataclass inherits from us.

    def postinit(self, sessionplayer: ba.SessionPlayer) -> None:
        """Wire up a newly created player.

        (internal)
        """
        from ba._nodeactor import NodeActor
        import _ba

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
        self.team = sessionplayer.team.gameteam  # type: ignore
        assert self.team is not None
        self.sessiondata = sessionplayer.sessiondata
        self.gamedata = sessionplayer.gamedata

        # Create our player node in the current activity.
        node = _ba.newnode('player', attrs={'playerID': sessionplayer.id})
        self._nodeactor = NodeActor(node)
        sessionplayer.set_node(node)

    @property
    def sessionplayer(self) -> ba.SessionPlayer:
        """Return the ba.SessionPlayer corresponding to this Player.

        Throws a ba.SessionPlayerNotFoundError if it does not exist.
        """
        if bool(self._sessionplayer):
            return self._sessionplayer
        from ba import _error
        raise _error.SessionPlayerNotFoundError()

    @property
    def node(self) -> ba.Node:
        """A ba.Node of type 'player' associated with this Player.

        This node can be used to get a generic player position/etc.
        """
        if not self._nodeactor:
            from ba import _error
            raise _error.NodeNotFoundError
        return self._nodeactor.node

    @property
    def exists(self) -> bool:
        """Whether the player still exists.

        Most functionality will fail on a nonexistent player.
        Note that you can also use the boolean operator for this same
        functionality, so a statement such as "if player" will do
        the right thing both for Player objects and values of None.
        """
        return bool(self._sessionplayer)

    def get_name(self, full: bool = False, icon: bool = True) -> str:
        """get_name(full: bool = False, icon: bool = True) -> str

        Returns the player's name. If icon is True, the long version of the
        name may include an icon.
        """
        return self._sessionplayer.get_name(full=full, icon=icon)

    def set_actor(self, actor: Optional[ba.Actor]) -> None:
        """set_actor(actor: Optional[ba.Actor]) -> None

        Set the player's associated ba.Actor.
        """
        self.actor = actor

    def is_alive(self) -> bool:
        """is_alive() -> bool

        Returns True if the player has a ba.Actor assigned and its
        is_alive() method return True. False is returned otherwise.
        """
        return self.actor is not None and self.actor.is_alive()

    def get_icon(self) -> Dict[str, Any]:
        """get_icon() -> Dict[str, Any]

        Returns the character's icon (images, colors, etc contained in a dict)
        """
        return self._sessionplayer.get_icon()

    def assign_input_call(self, inputtype: Union[str, Tuple[str, ...]],
                          call: Callable) -> None:
        """assign_input_call(type: Union[str, Tuple[str, ...]],
          call: Callable) -> None

        Set the python callable to be run for one or more types of input.
        Valid type values are: 'jumpPress', 'jumpRelease', 'punchPress',
          'punchRelease','bombPress', 'bombRelease', 'pickUpPress',
          'pickUpRelease', 'upDown','leftRight','upPress', 'upRelease',
          'downPress', 'downRelease', 'leftPress','leftRelease','rightPress',
          'rightRelease', 'run', 'flyPress', 'flyRelease', 'startPress',
          'startRelease'
        """
        return self._sessionplayer.assign_input_call(type=inputtype, call=call)

    def reset_input(self) -> None:
        """reset_input() -> None

        Clears out the player's assigned input actions.
        """
        self._sessionplayer.reset_input()

    def __bool__(self) -> bool:
        return bool(self._sessionplayer)


PlayerType = TypeVar('PlayerType', bound='ba.Player')


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
    # noinspection PyTypeHints
    assert isinstance(player, (totype, type(None)))
    return player
