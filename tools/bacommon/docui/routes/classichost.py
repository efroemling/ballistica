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
from bacommon.docui.routes import DocUIRoute, family_members


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
class KickVote(ClassicHostRoute, path='/kickvote'):
    """Start or follow a vote to kick someone.

    Clients open this with ``client_id`` set to whoever they chose to
    kick; without one it shows any vote in progress.
    """

    client_id: Annotated[int | None, IOAttrs('c', store_default=False)] = None


@ioprepped
@dataclass
class KickVoteStart(
    ClassicHostRoute, path='/kickvote', method=dui2.RequestMethod.POST
):
    """Start a vote to kick a client."""

    client_id: Annotated[int, IOAttrs('c')]


@ioprepped
@dataclass
class KickVoteCast(
    ClassicHostRoute, path='/kickvote/vote', method=dui2.RequestMethod.POST
):
    """Vote in the kick vote in progress."""

    yes: Annotated[bool, IOAttrs('y')]


AnyClassicHostRoute = Stats | KickVote | KickVoteStart | KickVoteCast
