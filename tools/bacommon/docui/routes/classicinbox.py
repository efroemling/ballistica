# Released under the MIT License. See LICENSE for details.
#
"""Routes for the classic inbox doc-ui domain.

The inbox lists an account's messages (rewards, notices, tournament
results) as cards; responding to one -- claiming a reward, accepting or
declining -- posts back and gets the updated list in return.
"""

from dataclasses import dataclass
from typing import Annotated, override

from efro.dataclassio import ioprepped, IOAttrs

import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    PressSound,
    family_members,
)


class InboxRoute(DocUIRoute):
    """Family class for classic inbox routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyInboxRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # A narrow column of message cards, like the classic inbox.
        return dui2.WindowLayout.SMALL_TALL


@ioprepped
@dataclass
class Root(InboxRoute, path='/'):
    """The inbox: every message, newest first."""

    #: Draw bounds and other debug bits.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


@ioprepped
@dataclass
class Respond(InboxRoute, path='/', method=dui2.RequestMethod.POST):
    """Respond to one message (claim it, accept or decline it, etc.).

    Answered with the updated inbox, with any effects of the response
    (reward animations, sounds) attached. Shares the inbox's own path so
    the client treats the answer as the same page updated (holding its
    scroll position) rather than a new one.
    """

    #: The message.
    entry_id: Annotated[str, IOAttrs('i')]

    #: Whether this is the message's positive response (claim, accept,
    #: ok) as opposed to its negative one (decline).
    positive: Annotated[bool, IOAttrs('p', store_default=False)] = True


# All inbox routes.
AnyInboxRoute = Root | Respond


class InboxLocalAction(DocUILocalActionBase):
    """Family class for classic inbox local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyInboxLocalAction)


@ioprepped
@dataclass
class OpenUrl(InboxLocalAction, name='open_url'):
    """Open a url in the platform's browser."""

    url: Annotated[str, IOAttrs('u')]


@ioprepped
@dataclass
class TourneyScores(InboxLocalAction, name='tourney_scores'):
    """Show a tournament's final standings."""

    tournament_id: Annotated[str, IOAttrs('t')]

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH


# All inbox local-actions.
AnyInboxLocalAction = OpenUrl | TourneyScores
