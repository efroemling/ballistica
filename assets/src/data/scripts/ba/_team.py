"""Defines Team class."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Sequence, Any, Tuple, Union
    import ba


class Team:
    """A team of one or more ba.Players.

    Category: Gameplay Classes

    Note that a player *always* has a team;
    in some cases, such as free-for-all ba.Sessions,
    each team consists of just one ba.Player.

    Attributes:

        name
            The team's name.

        color
            The team's color.

        players
            The list of ba.Players on the team.

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
    color: Tuple[float, ...]
    players: List[ba.Player]
    gamedata: Dict
    sessiondata: Dict

    def __init__(self,
                 team_id: int = 0,
                 name: Union[ba.Lstr, str] = "",
                 color: Sequence[float] = (1.0, 1.0, 1.0)):
        """Instantiate a ba.Team.

        In most cases, all teams are provided to you by the ba.Session,
        ba.Session, so calling this shouldn't be necessary.
        """

        # TODO: Once we spin off team copies for each activity, we don't
        #  need to bother with trying to lock things down, since it won't
        #  matter at that point if the activity mucks with them.

        # Temporarily allow us to set our own attrs
        # (keeps pylint happier than using __setattr__ explicitly for all).
        object.__setattr__(self, '_locked', False)
        self._team_id: int = team_id
        self.name = name
        self.color = tuple(color)
        self.players = []
        self.gamedata = {}
        self.sessiondata = {}

        # Now prevent further attr sets.
        self._locked = True

    def get_id(self) -> int:
        """Returns the numeric team ID."""
        return self._team_id

    def celebrate(self, duration: float = 10.0) -> None:
        """Tells all players on the team to celebrate.

        duration is given in seconds.
        """
        for player in self.players:
            try:
                if player.actor is not None and player.actor.node:
                    # Internal node-message is in milliseconds.
                    player.actor.node.handlemessage('celebrate',
                                                    int(duration * 1000))
            except Exception:
                from ba import _error
                _error.print_exception('Error on celebrate')

    def reset(self) -> None:
        """(internal)"""
        self.reset_gamedata()
        object.__setattr__(self, 'players', [])

    def reset_gamedata(self) -> None:
        """(internal)"""
        object.__setattr__(self, 'gamedata', {})

    def reset_sessiondata(self) -> None:
        """(internal)"""
        object.__setattr__(self, 'sessiondata', {})

    def __setattr__(self, name: str, value: Any) -> None:
        if self._locked:
            raise Exception("can't set attrs on ba.Team objects")
        object.__setattr__(self, name, value)
