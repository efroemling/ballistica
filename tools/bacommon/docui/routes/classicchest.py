# Released under the MIT License. See LICENSE for details.
#
"""Routes for the classic chest doc-ui domain.

One chest slot: what's in it, its prize odds and its unlock wait, with
buttons to open it (now, for tokens, or once unlocked) or to watch an
ad to cut the wait. Opening answers with the chest's contents and the
open animation as client-effects.
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


class ChestRoute(DocUIRoute):
    """Family class for classic chest routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyChestRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # One chest centered, its odds beside it, buttons below.
        return dui2.WindowLayout.WIDE


@ioprepped
@dataclass
class Root(ChestRoute, path='/'):
    """A chest slot: its chest (if any) and what can be done with it.

    The two flags are things only the client knows, so it states them
    when asking.
    """

    #: Which slot (0-based).
    slot: Annotated[int, IOAttrs('s')]

    #: Whether an ad is ready to show right now (so a 'watch an ad to
    #: reduce the wait' button can work).
    ad_ready: Annotated[bool, IOAttrs('a', store_default=False)] = False

    #: Whether to remind about opening early with tokens (the player
    #: can switch the reminder off).
    open_me: Annotated[bool, IOAttrs('o', store_default=False)] = False


@ioprepped
@dataclass
class Open(ChestRoute, path='/open', method=dui2.RequestMethod.POST):
    """Open a chest, paying any tokens its wait currently costs.

    Answered with its contents and the open animation.
    """

    slot: Annotated[int, IOAttrs('s')]

    #: Tokens the player agreed to pay (0 for an unlocked chest). The
    #: open fails if the cost has since changed.
    token_payment: Annotated[int, IOAttrs('t')]


@ioprepped
@dataclass
class AdWatched(ChestRoute, path='/adwatched', method=dui2.RequestMethod.POST):
    """The player watched an ad to reduce a chest's wait.

    Answered like :class:`Open` if that unlocked it; otherwise with the
    slot as it now stands.
    """

    slot: Annotated[int, IOAttrs('s')]


# All chest routes.
AnyChestRoute = Root | Open | AdWatched


class ChestLocalAction(DocUILocalActionBase):
    """Family class for classic chest local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyChestLocalAction)


@ioprepped
@dataclass
class WatchAd(ChestLocalAction, name='watch_ad'):
    """Show an ad; once watched, ask for :class:`AdWatched`."""

    slot: Annotated[int, IOAttrs('s')]


@ioprepped
@dataclass
class StopReminding(ChestLocalAction, name='stop_reminding'):
    """Stop reminding about opening chests early; re-show the slot."""

    slot: Annotated[int, IOAttrs('s')]


@ioprepped
@dataclass
class GetTokens(ChestLocalAction, name='get_tokens'):
    """Offer to get more tokens (not enough to open a chest now)."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH


# All chest local-actions.
AnyChestLocalAction = WatchAd | StopReminding | GetTokens
