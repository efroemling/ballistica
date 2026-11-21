# Released under the MIT License. See LICENSE for details.
#
"""Routes for the classic host doc-ui domain.

Pages a game host serves its connected clients over the game
connection (see ``bacommon.hostui``): the defaults classic hosts ship
with. Hosts may serve other routes of their own alongside these.
"""

from dataclasses import dataclass
from typing import Annotated, override

from efro.dataclassio import ioprepped, IOAttrs

import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    family_members,
)


class ClassicHostRoute(DocUIRoute):
    """Family class for classic host routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyClassicHostRoute)

    # (Window layout: the route default, wide.)


@ioprepped
@dataclass
class Stats(ClassicHostRoute, path='/stats'):
    """Who is in the party and how their connections are doing."""


@ioprepped
@dataclass
class Client(ClassicHostRoute, path='/client'):
    """One party member (a connected client, or -1 for the host).

    Their account, connection and players, and kicking them. Party
    windows open this when a member's name is pressed.
    """

    client_id: Annotated[int, IOAttrs('c')]

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # (A few labeled values and a row of players; a narrow window
        # keeps labels near their values.)
        return dui2.WindowLayout.SMALL_TALL


@ioprepped
@dataclass
class Player(ClassicHostRoute, path='/player'):
    """One player in the game, by their session player id.

    How they're doing, who they're playing as, and kicking them.
    """

    player_id: Annotated[int, IOAttrs('p')]

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # (A big icon and name over a wide row of columns.)
        return dui2.WindowLayout.WIDE_TALL


@ioprepped
@dataclass
class KickVote(ClassicHostRoute, path='/kickvote'):
    """Start or follow a vote to kick someone.

    Clients open this with ``client_id`` set to whoever they chose to
    kick (and ``player_id`` to the player they chose them by, if any);
    without one it shows any vote in progress.
    """

    client_id: Annotated[int | None, IOAttrs('c', store_default=False)] = None
    player_id: Annotated[int | None, IOAttrs('p', store_default=False)] = None

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # (Its most is a question, a couple of lines, Yes/No buttons and
        # a countdown.)
        return dui2.WindowLayout.SMALL


@ioprepped
@dataclass
class KickVoteStart(
    ClassicHostRoute, path='/kickvote', method=dui2.RequestMethod.POST
):
    """Start a vote to kick a client."""

    client_id: Annotated[int, IOAttrs('c')]
    player_id: Annotated[int | None, IOAttrs('p', store_default=False)] = None


@ioprepped
@dataclass
class KickVoteCast(
    ClassicHostRoute, path='/kickvote/vote', method=dui2.RequestMethod.POST
):
    """Vote in the kick vote in progress."""

    yes: Annotated[bool, IOAttrs('y')]


AnyClassicHostRoute = (
    Stats | Client | Player | KickVote | KickVoteStart | KickVoteCast
)


#: First engine build that runs :class:`ShowAccount` from host pages
#: (older ones ignore host local-actions; the button then does nothing).
SHOW_ACCOUNT_BUILD = 23075


class ClassicHostLocalAction(DocUILocalActionBase):
    """Family class for local-actions host pages may use.

    Hosts are untrusted, so these are the only things a host page can
    make a client do locally: each is safe whatever a host passes it
    (its fields arrive from the host as-is). Clients ignore anything
    else.
    """

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyClassicHostLocalAction)


@ioprepped
@dataclass
class ShowAccount(ClassicHostLocalAction, name='show_account'):
    """Open an account's page from the master server, over this one.

    (See :class:`bacommon.docui.routes.classicaccount.Account`; backing
    out of it returns to the host page.) Only presses can do it.
    Builds before :data:`SHOW_ACCOUNT_BUILD` ignore it.
    """

    #: The account (``a-XXX``).
    account_id: Annotated[str, IOAttrs('a')]


# All local-actions in the family.
AnyClassicHostLocalAction = ShowAccount
