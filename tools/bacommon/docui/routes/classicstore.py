# Released under the MIT License. See LICENSE for details.
#
"""Routes for the classic store and inventory doc-ui domains.

The store and inventory are two domains served by a single set of
pages (the inventory is essentially the store filtered to owned things
plus player-profiles), so they share one route family. Each has its
own local-actions.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Annotated, override

from efro.dataclassio import ioprepped, IOAttrs

import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    DocUIState,
    PressSound,
    family_members,
)


class PurchaseMethod(Enum):
    """How to purchase something."""

    TOKENS = 't'
    TICKETS = 'k'
    PURPLE_TICKETS = 'p'
    GOLD_PASS = 'g'


class StoreRoute(DocUIRoute):
    """Family class for classic store/inventory routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyStoreRoute)


@ioprepped
@dataclass
class Root(StoreRoute, path='/'):
    """The main store/inventory listing."""

    #: Draw bounds and other debug bits.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    #: Set on the page's own refresh button. One-time-use; the server
    #: does not carry it into further links.
    is_refresh: Annotated[bool, IOAttrs('r', store_default=False)] = False

    #: (Inventory) the client is showing its locally-spliced legacy
    #: profiles; omit cloud profile rows.
    legacy_profiles: Annotated[bool, IOAttrs('lp', store_default=False)] = False

    #: (Inventory) render only the profiles section (the in-game
    #: profile browser).
    profiles_only: Annotated[bool, IOAttrs('po', store_default=False)] = False

    #: Legacy purchase ids required to unlock something; when provided,
    #: only items providing those are shown.
    unlockreqs: Annotated[
        list[str] | None, IOAttrs('unlockreqs', store_default=False)
    ] = None


@ioprepped
@dataclass
class Purchase(StoreRoute, path='/p'):
    """Purchase options for a single item."""

    purchase_id: Annotated[str, IOAttrs('i')]
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


@ioprepped
@dataclass
class PurchaseConfirm(StoreRoute, path='/pc', method=dui2.RequestMethod.POST):
    """Actually purchase an item."""

    purchase_id: Annotated[str, IOAttrs('i')]
    purchase_method: Annotated[PurchaseMethod, IOAttrs('m')]
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


@ioprepped
@dataclass
class ProfileDraft(DocUIState, state_id='classic.profile_draft'):
    """The profile editor's working profile.

    Page state for the editor and its save: what the user has composed
    so far. A request with no draft at all (the first visit) gets one
    built from the stored profile, or fresh defaults when creating; an
    empty name or character means the same for that field.
    """

    color: Annotated[tuple[float, float, float], IOAttrs('cl')]
    highlight: Annotated[tuple[float, float, float], IOAttrs('h')]
    name: Annotated[str, IOAttrs('n')] = ''
    character: Annotated[str, IOAttrs('c')] = ''


@ioprepped
@dataclass
class ProfileEdit(StoreRoute, path='/profile'):
    """(Inventory) the cloud player-profile editor.

    The draft being composed rides along as :class:`ProfileDraft`
    page state; the route itself only says which stored profile (if
    any) is being edited.
    """

    #: Stored profile being edited, or None when creating one.
    profile_name: Annotated[str | None, IOAttrs('pn', store_default=False)] = (
        None
    )

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # The editor's controls go in the column; the pane beside them
        # shows the character being composed.
        return dui2.WindowLayout.VIEWER


@ioprepped
@dataclass
class ProfileSave(
    StoreRoute, path='/profile/save', method=dui2.RequestMethod.POST
):
    """(Inventory) save the editor's draft (its :class:`ProfileDraft`)."""

    #: See :attr:`ProfileEdit.profile_name`.
    profile_name: Annotated[str | None, IOAttrs('pn', store_default=False)] = (
        None
    )


@ioprepped
@dataclass
class ProfileDelete(
    StoreRoute, path='/profile/delete', method=dui2.RequestMethod.POST
):
    """(Inventory) delete a stored profile."""

    profile_name: Annotated[str, IOAttrs('pn')]


# All routes in the family.
AnyStoreRoute = (
    Root
    | Purchase
    | PurchaseConfirm
    | ProfileEdit
    | ProfileSave
    | ProfileDelete
)


class StoreLocalAction(DocUILocalActionBase):
    """Family class for classic store local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyStoreLocalAction)


@ioprepped
@dataclass
class GetTokens(StoreLocalAction, name='get_tokens'):
    """Show the get-tokens window."""


@ioprepped
@dataclass
class RestorePurchases(StoreLocalAction, name='restore_purchases'):
    """Kick off a platform purchase-restore."""


# All store local-actions.
AnyStoreLocalAction = GetTokens | RestorePurchases


class InventoryLocalAction(DocUILocalActionBase):
    """Family class for classic inventory local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyInventoryLocalAction)


@ioprepped
@dataclass
class NewProfile(InventoryLocalAction, name='new_profile'):
    """Open the (legacy) profile editor on a new profile."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH


@ioprepped
@dataclass
class EditProfile(InventoryLocalAction, name='edit_profile'):
    """Open the (legacy) profile editor on an existing profile."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH

    profile: Annotated[str, IOAttrs('profile')]


@ioprepped
@dataclass
class SpawnBot(InventoryLocalAction, name='spawn_bot'):
    """Spawn a character in the main-menu background."""

    #: Internal appearance name of the character.
    name: Annotated[str, IOAttrs('name')]


@ioprepped
@dataclass
class ShowLegacyProfiles(InventoryLocalAction, name='show_legacy_profiles'):
    """Switch the inventory to the client's legacy profiles."""


@ioprepped
@dataclass
class ShowCloudProfiles(InventoryLocalAction, name='show_cloud_profiles'):
    """Switch the inventory to cloud profiles."""


# All inventory local-actions.
AnyInventoryLocalAction = (
    NewProfile | EditProfile | SpawnBot | ShowLegacyProfiles | ShowCloudProfiles
)
