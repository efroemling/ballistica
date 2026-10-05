# Released under the MIT License. See LICENSE for details.
#
"""Routes for the classic league-presidency doc-ui domain."""

from dataclasses import dataclass
from typing import Annotated, override

from efro.dataclassio import ioprepped, IOAttrs

import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    DocUIState,
    family_members,
)


class LeaguePresidencyRoute(DocUIRoute):
    """Family class for classic league-presidency routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyLeaguePresidencyRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # The page is one fixed-size block (it doesn't stretch to fill
        # a window), sized for a phone screen; wide keeps that block
        # the same at every ui-scale with a snug window around it.
        return dui2.WindowLayout.WIDE


@ioprepped
@dataclass
class BidState(DocUIState, state_id='classic.league_presidency.bid'):
    """The presidency page's state: the bid being composed.

    Clients that speak page state carry this; older ones carry the
    same value as the ``bid`` arg on the routes.
    """

    bid: Annotated[int, IOAttrs('t')] = 0


@ioprepped
@dataclass
class Root(LeaguePresidencyRoute, path='/'):
    """The presidency page for the account's current league."""

    #: The bid being composed (the page's +/- buttons adjust this).
    #: Only meaningful for clients without page state; others carry
    #: it in :class:`BidState`.
    bid: Annotated[int, IOAttrs('t')] = 0

    #: Draw bounds and other debug bits.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    #: Season the client was looking at when it opened us. Not
    #: currently used (the page always shows the current season).
    season: Annotated[str | None, IOAttrs('season', store_default=False)] = None


@ioprepped
@dataclass
class SubmitBid(
    LeaguePresidencyRoute, path='/', method=dui2.RequestMethod.POST
):
    """Submit a bid."""

    #: See :attr:`Root.bid`.
    bid: Annotated[int, IOAttrs('t')] = 0
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


# All routes in the family.
AnyLeaguePresidencyRoute = Root | SubmitBid


class LeaguePresidencyLocalAction(DocUILocalActionBase):
    """Family class for classic league-presidency local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyLeaguePresidencyLocalAction)


@ioprepped
@dataclass
class GetTokens(LeaguePresidencyLocalAction, name='get_tokens'):
    """Show the get-tokens window."""


# All local-actions in the family (just the one for now).
AnyLeaguePresidencyLocalAction = GetTokens
