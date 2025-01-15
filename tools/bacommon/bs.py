# Released under the MIT License. See LICENSE for details.
#
"""BombSquad specific bits."""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.util import pairs_to_flat
from efro.dataclassio import ioprepped, IOAttrs, IOMultiType
from efro.message import Message, Response


@ioprepped
@dataclass
class PrivatePartyMessage(Message):
    """Message asking about info we need for private-party UI."""

    need_datacode: Annotated[bool, IOAttrs('d')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [PrivatePartyResponse]


@ioprepped
@dataclass
class PrivatePartyResponse(Response):
    """Here's that private party UI info you asked for, boss."""

    success: Annotated[bool, IOAttrs('s')]
    tokens: Annotated[int, IOAttrs('t')]
    gold_pass: Annotated[bool, IOAttrs('g')]
    datacode: Annotated[str | None, IOAttrs('d')]


class ClassicChestAppearance(Enum):
    """Appearances bombsquad classic chests can have."""

    UNKNOWN = 'u'
    DEFAULT = 'd'
    L1 = 'l1'
    L2 = 'l2'
    L3 = 'l3'
    L4 = 'l4'
    L5 = 'l5'
    L6 = 'l6'


@ioprepped
@dataclass
class ClassicAccountLiveData:
    """Live account data fed to the client in the bs classic app mode."""

    @dataclass
    class Chest:
        """A lovely chest."""

        appearance: Annotated[
            ClassicChestAppearance,
            IOAttrs('a', enum_fallback=ClassicChestAppearance.UNKNOWN),
        ]
        unlock_time: Annotated[datetime.datetime, IOAttrs('t')]
        ad_allow_time: Annotated[datetime.datetime | None, IOAttrs('at')]

    class LeagueType(Enum):
        """Type of league we are in."""

        BRONZE = 'b'
        SILVER = 's'
        GOLD = 'g'
        DIAMOND = 'd'

    tickets: Annotated[int, IOAttrs('ti')]

    tokens: Annotated[int, IOAttrs('to')]
    gold_pass: Annotated[bool, IOAttrs('g')]

    achievements: Annotated[int, IOAttrs('a')]
    achievements_total: Annotated[int, IOAttrs('at')]

    league_type: Annotated[LeagueType | None, IOAttrs('lt')]
    league_num: Annotated[int | None, IOAttrs('ln')]
    league_rank: Annotated[int | None, IOAttrs('lr')]

    level: Annotated[int, IOAttrs('lv')]
    xp: Annotated[int, IOAttrs('xp')]
    xpmax: Annotated[int, IOAttrs('xpm')]

    inbox_count: Annotated[int, IOAttrs('ibc')]
    inbox_count_is_max: Annotated[bool, IOAttrs('ibcm')]

    chests: Annotated[dict[str, Chest], IOAttrs('c')]


class DisplayItemTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TICKETS = 't'
    TOKENS = 'k'
    TEST = 's'
    CHEST = 'c'


class DisplayItem(IOMultiType[DisplayItemTypeID]):
    """Some amount of something that can be shown or described.

    Used to depict chest contents or other rewards or prices.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DisplayItemTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: DisplayItemTypeID) -> type[DisplayItem]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = DisplayItemTypeID
        if type_id is t.UNKNOWN:
            return UnknownDisplayItem
        if type_id is t.TICKETS:
            return TicketsDisplayItem
        if type_id is t.TOKENS:
            return TokensDisplayItem
        if type_id is t.TEST:
            return TestDisplayItem
        if type_id is t.CHEST:
            return ChestDisplayItem

        # Important to make sure we provide all types.
        assert_never(type_id)

    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        """Return a string description and subs for the item.

        These decriptions are baked into the DisplayItemWrapper and
        should be accessed from there by the client. This should only be
        called on the server side when doing said baking.
        """
        raise NotImplementedError()

    # Implement fallbacks so client can digest item lists even if they
    # contain unrecognized stuff. DisplayItemWrapper contains basic
    # baked down info that they can still use in such cases.
    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> DisplayItem:
        return UnknownDisplayItem()


@ioprepped
@dataclass
class UnknownDisplayItem(DisplayItem):
    """Something we don't know how to display."""

    @override
    @classmethod
    def get_type_id(cls) -> DisplayItemTypeID:
        return DisplayItemTypeID.UNKNOWN

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        import logging

        # Make noise but don't break.
        logging.exception(
            'UnknownDisplayItem.get_description() should never be called.'
            ' Always access descriptions on the DisplayItemWrapper.'
        )
        return 'Unknown', []


@ioprepped
@dataclass
class TicketsDisplayItem(DisplayItem):
    """Some amount of tickets."""

    count: Annotated[int, IOAttrs('c')]

    @override
    @classmethod
    def get_type_id(cls) -> DisplayItemTypeID:
        return DisplayItemTypeID.TICKETS

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return '${C} Tickets', [('${C}', str(self.count))]


@ioprepped
@dataclass
class TokensDisplayItem(DisplayItem):
    """Some amount of tokens."""

    count: Annotated[int, IOAttrs('c')]

    @override
    @classmethod
    def get_type_id(cls) -> DisplayItemTypeID:
        return DisplayItemTypeID.TOKENS

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return '${C} Tokens', [('${C}', str(self.count))]


@ioprepped
@dataclass
class TestDisplayItem(DisplayItem):
    """Fills usable space for a display-item - good for calibration."""

    @override
    @classmethod
    def get_type_id(cls) -> DisplayItemTypeID:
        return DisplayItemTypeID.TEST

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return 'Test Display Item Here', []


@ioprepped
@dataclass
class ChestDisplayItem(DisplayItem):
    """Display a chest."""

    appearance: Annotated[ClassicChestAppearance, IOAttrs('a')]

    @override
    @classmethod
    def get_type_id(cls) -> DisplayItemTypeID:
        return DisplayItemTypeID.CHEST

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return '${TYPE} Chest', [('${TYPE}', self.appearance.name.capitalize())]


@ioprepped
@dataclass
class DisplayItemWrapper:
    """Wraps a DisplayItem and common info."""

    item: Annotated[DisplayItem, IOAttrs('i')]
    description: Annotated[str, IOAttrs('d')]
    description_subs: Annotated[list[str] | None, IOAttrs('s')]

    @classmethod
    def for_display_item(cls, item: DisplayItem) -> DisplayItemWrapper:
        """Convenience method to wrap a DisplayItem."""
        desc, subs = item.get_description()
        return DisplayItemWrapper(item, desc, pairs_to_flat(subs))


@ioprepped
@dataclass
class ChestInfoMessage(Message):
    """Request info about a chest."""

    chest_id: Annotated[str, IOAttrs('i')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ChestInfoResponse]


@ioprepped
@dataclass
class ChestInfoResponse(Response):
    """Here's that chest info you asked for, boss."""

    @dataclass
    class Chest:
        """A lovely chest."""

        @dataclass
        class PrizeSet:
            """A possible set of prizes for this chest."""

            weight: Annotated[float, IOAttrs('w')]
            contents: Annotated[list[DisplayItemWrapper], IOAttrs('c')]

        appearance: Annotated[
            ClassicChestAppearance,
            IOAttrs('a', enum_fallback=ClassicChestAppearance.UNKNOWN),
        ]

        # How much it costs to unlock *now*.
        unlock_tokens: Annotated[int, IOAttrs('tk')]

        # When it unlocks on its own.
        unlock_time: Annotated[datetime.datetime, IOAttrs('t')]

        # Possible prizes we contain.
        prizesets: Annotated[list[PrizeSet], IOAttrs('p')]

        # Are ads allowed now?
        ad_allow: Annotated[bool, IOAttrs('aa')]

    chest: Annotated[Chest | None, IOAttrs('c')]
    user_tokens: Annotated[int | None, IOAttrs('t')]


@ioprepped
@dataclass
class ChestActionMessage(Message):
    """Request action about a chest."""

    class Action(Enum):
        """Types of actions we can request."""

        # Unlocking (for free or with tokens).
        UNLOCK = 'u'

        # Watched an ad to reduce wait.
        AD = 'ad'

    action: Annotated[Action, IOAttrs('a')]

    # Tokens we are paying (only applies to unlock).
    token_payment: Annotated[int, IOAttrs('t')]

    chest_id: Annotated[str, IOAttrs('i')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ChestActionResponse]


@ioprepped
@dataclass
class ChestActionResponse(Response):
    """Here's the results of that action you asked for, boss."""

    # Tokens that were actually charged.
    tokens_charged: Annotated[int, IOAttrs('t')] = 0

    # If present, signifies the chest has been opened and we should show
    # the user this stuff that was in it.
    contents: Annotated[list[DisplayItemWrapper] | None, IOAttrs('c')] = None

    # If contents are present, which of the chest's prize-sets they
    # represent.
    prizeindex: Annotated[int, IOAttrs('i')] = 0

    # Printable error if something goes wrong.
    error: Annotated[str | None, IOAttrs('e')] = None

    # Printable warning. Shown in orange with an error sound. Does not
    # mean the action failed; only that there's something to tell the
    # users such as 'It looks like you are faking ad views; stop it or
    # you won't have ad options anymore.'
    warning: Annotated[str | None, IOAttrs('w')] = None

    # Printable success message. Shown in green with a cash-register
    # sound. Can be used for things like successful wait reductions via
    # ad views.
    success_msg: Annotated[str | None, IOAttrs('s')] = None


class ClientUITypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    BASIC = 'b'


class ClientUI(IOMultiType[ClientUITypeID]):
    """Defines some user interface on the client."""

    @override
    @classmethod
    def get_type_id(cls) -> ClientUITypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ClientUITypeID) -> type[ClientUI]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import
        out: type[ClientUI]

        t = ClientUITypeID
        if type_id is t.UNKNOWN:
            out = UnknownClientUI
        elif type_id is t.BASIC:
            out = BasicClientUI
        else:
            # Important to make sure we provide all types.
            assert_never(type_id)
        return out

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> ClientUI:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return UnknownClientUI()


@ioprepped
@dataclass
class UnknownClientUI(ClientUI):
    """Fallback type for unrecognized entries."""

    @override
    @classmethod
    def get_type_id(cls) -> ClientUITypeID:
        return ClientUITypeID.UNKNOWN


class BasicClientUIComponentTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TEXT = 't'
    LINK = 'l'
    BS_CLASSIC_TOURNEY_RESULT = 'ct'
    DISPLAY_ITEMS = 'di'


class BasicClientUIComponent(IOMultiType[BasicClientUIComponentTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> BasicClientUIComponentTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: BasicClientUIComponentTypeID
    ) -> type[BasicClientUIComponent]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = BasicClientUIComponentTypeID
        if type_id is t.UNKNOWN:
            return BasicClientUIComponentUnknown
        if type_id is t.TEXT:
            return BasicClientUIComponentText
        if type_id is t.LINK:
            return BasicClientUIComponentLink
        if type_id is t.BS_CLASSIC_TOURNEY_RESULT:
            return BasicClientUIBsClassicTourneyResult
        if type_id is t.DISPLAY_ITEMS:
            return BasicClientUIDisplayItems

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> BasicClientUIComponent:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return BasicClientUIComponentUnknown()


@ioprepped
@dataclass
class BasicClientUIComponentUnknown(BasicClientUIComponent):
    """An unknown basic client component type.

    In practice these should never show up since the master-server
    generates these on the fly for the client and so should not send
    clients one they can't digest.
    """

    @override
    @classmethod
    def get_type_id(cls) -> BasicClientUIComponentTypeID:
        return BasicClientUIComponentTypeID.UNKNOWN


@ioprepped
@dataclass
class BasicClientUIComponentText(BasicClientUIComponent):
    """Show some text in the inbox message."""

    text: Annotated[str, IOAttrs('t')]
    subs: Annotated[list[str], IOAttrs('s', store_default=False)] = field(
        default_factory=list
    )
    scale: Annotated[float, IOAttrs('sc', store_default=False)] = 1.0
    color: Annotated[
        tuple[float, float, float, float], IOAttrs('c', store_default=False)
    ] = (1.0, 1.0, 1.0, 1.0)
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> BasicClientUIComponentTypeID:
        return BasicClientUIComponentTypeID.TEXT


@ioprepped
@dataclass
class BasicClientUIComponentLink(BasicClientUIComponent):
    """Show a link in the inbox message."""

    url: Annotated[str, IOAttrs('u')]
    label: Annotated[str, IOAttrs('l')]
    subs: Annotated[list[str], IOAttrs('s', store_default=False)] = field(
        default_factory=list
    )
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> BasicClientUIComponentTypeID:
        return BasicClientUIComponentTypeID.LINK


@ioprepped
@dataclass
class BasicClientUIBsClassicTourneyResult(BasicClientUIComponent):
    """Show info about a classic tourney."""

    tournament_id: Annotated[str, IOAttrs('t')]
    game: Annotated[str, IOAttrs('g')]
    players: Annotated[int, IOAttrs('p')]
    rank: Annotated[int, IOAttrs('r')]
    trophy: Annotated[str | None, IOAttrs('tr')]
    prizes: Annotated[list[DisplayItemWrapper], IOAttrs('pr')]

    @override
    @classmethod
    def get_type_id(cls) -> BasicClientUIComponentTypeID:
        return BasicClientUIComponentTypeID.BS_CLASSIC_TOURNEY_RESULT


@ioprepped
@dataclass
class BasicClientUIDisplayItems(BasicClientUIComponent):
    """Show some display-items."""

    items: Annotated[list[DisplayItemWrapper], IOAttrs('d')]
    width: Annotated[float, IOAttrs('w')] = 100.0
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> BasicClientUIComponentTypeID:
        return BasicClientUIComponentTypeID.DISPLAY_ITEMS


@ioprepped
@dataclass
class BasicClientUI(ClientUI):
    """A basic UI for the client."""

    class ButtonLabel(Enum):
        """Distinct button labels we support."""

        UNKNOWN = 'u'
        OK = 'o'
        APPLY = 'a'
        CANCEL = 'c'
        ACCEPT = 'ac'
        DECLINE = 'dn'
        IGNORE = 'ig'
        CLAIM = 'cl'
        DISCARD = 'd'

    class InteractionStyle(Enum):
        """Overall interaction styles we support."""

        UNKNOWN = 'u'
        BUTTON_POSITIVE = 'p'
        BUTTON_POSITIVE_NEGATIVE = 'pn'

    components: Annotated[list[BasicClientUIComponent], IOAttrs('s')]

    interaction_style: Annotated[
        InteractionStyle, IOAttrs('i', enum_fallback=InteractionStyle.UNKNOWN)
    ] = InteractionStyle.BUTTON_POSITIVE

    button_label_positive: Annotated[
        ButtonLabel, IOAttrs('p', enum_fallback=ButtonLabel.UNKNOWN)
    ] = ButtonLabel.OK

    button_label_negative: Annotated[
        ButtonLabel, IOAttrs('n', enum_fallback=ButtonLabel.UNKNOWN)
    ] = ButtonLabel.CANCEL

    @override
    @classmethod
    def get_type_id(cls) -> ClientUITypeID:
        return ClientUITypeID.BASIC

    def contains_unknown_elements(self) -> bool:
        """Whether something within us is an unknown type or enum."""
        return (
            self.interaction_style is self.InteractionStyle.UNKNOWN
            or self.button_label_positive is self.ButtonLabel.UNKNOWN
            or self.button_label_negative is self.ButtonLabel.UNKNOWN
            or any(
                c.get_type_id() is BasicClientUIComponentTypeID.UNKNOWN
                for c in self.components
            )
        )


@ioprepped
@dataclass
class ClientUIWrapper:
    """Wrapper for a ClientUI and its common data."""

    id: Annotated[str, IOAttrs('i')]
    createtime: Annotated[datetime.datetime, IOAttrs('c')]
    ui: Annotated[ClientUI, IOAttrs('e')]


@ioprepped
@dataclass
class InboxRequestMessage(Message):
    """Message requesting our inbox."""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [InboxRequestResponse]


@ioprepped
@dataclass
class InboxRequestResponse(Response):
    """Here's that inbox contents you asked for, boss."""

    wrappers: Annotated[list[ClientUIWrapper], IOAttrs('w')]

    # Printable error if something goes wrong.
    error: Annotated[str | None, IOAttrs('e')] = None


class ClientUIAction(Enum):
    """Types of actions we can run."""

    BUTTON_PRESS_POSITIVE = 'p'
    BUTTON_PRESS_NEGATIVE = 'n'


class ClientEffectTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    SCREEN_MESSAGE = 'm'
    SOUND = 's'
    DELAY = 'd'


class ClientEffect(IOMultiType[ClientEffectTypeID]):
    """Something that can happen on the client.

    This can include screen messages, sounds, visual effects, etc.
    """

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ClientEffectTypeID) -> type[ClientEffect]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = ClientEffectTypeID
        if type_id is t.UNKNOWN:
            return ClientEffectUnknown
        if type_id is t.SCREEN_MESSAGE:
            return ClientEffectScreenMessage
        if type_id is t.SOUND:
            return ClientEffectSound
        if type_id is t.DELAY:
            return ClientEffectDelay

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> ClientEffect:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return ClientEffectUnknown()


@ioprepped
@dataclass
class ClientEffectUnknown(ClientEffect):
    """Fallback substitute for types we don't recognize."""

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.UNKNOWN


@ioprepped
@dataclass
class ClientEffectScreenMessage(ClientEffect):
    """Display a screen-message."""

    message: Annotated[str, IOAttrs('m')]
    subs: Annotated[list[str], IOAttrs('s')]
    color: Annotated[tuple[float, float, float], IOAttrs('c')] = (1.0, 1.0, 1.0)

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.SCREEN_MESSAGE


@ioprepped
@dataclass
class ClientEffectSound(ClientEffect):
    """Play a sound."""

    class Sound(Enum):
        """Sounds that can be made alongside the message."""

        UNKNOWN = 'u'
        CASH_REGISTER = 'c'
        ERROR = 'e'
        POWER_DOWN = 'p'
        GUN_COCKING = 'g'

    sound: Annotated[Sound, IOAttrs('s', enum_fallback=Sound.UNKNOWN)]
    volume: Annotated[float, IOAttrs('v')] = 1.0

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.SOUND


@ioprepped
@dataclass
class ClientEffectDelay(ClientEffect):
    """Delay effect processing."""

    seconds: Annotated[float, IOAttrs('s')]

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.DELAY


@ioprepped
@dataclass
class ClientUIActionMessage(Message):
    """Do something to a client ui."""

    id: Annotated[str, IOAttrs('i')]
    action: Annotated[ClientUIAction, IOAttrs('a')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ClientUIActionResponse]


@ioprepped
@dataclass
class ClientUIActionResponse(Response):
    """Did something to that inbox entry, boss."""

    class ErrorType(Enum):
        """Types of errors that may have occurred."""

        # Probably a future error type we don't recognize.
        UNKNOWN = 'u'

        # Something went wrong on the server, but specifics are not
        # relevant.
        INTERNAL = 'i'

        # The entry expired on the server. In various cases such as 'ok'
        # buttons this can generally be ignored.
        EXPIRED = 'e'

    error_type: Annotated[
        ErrorType | None, IOAttrs('et', enum_fallback=ErrorType.UNKNOWN)
    ]

    # User facing error message in the case of errors.
    error_message: Annotated[str | None, IOAttrs('em')]

    effects: Annotated[list[ClientEffect], IOAttrs('fx')]
