# Released under the MIT License. See LICENSE for details.
#
"""Full UIs defined in the cloud - similar to a basic form of html"""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.bs._displayitem import DisplayItemWrapper


class CloudUITypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class CloudUI(IOMultiType[CloudUITypeID]):
    """UI defined by the cloud.

    Conceptually similar to a basic html page, except using app UI.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUITypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: CloudUITypeID) -> type[CloudUI]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import
        out: type[CloudUI]

        t = CloudUITypeID
        if type_id is t.UNKNOWN:
            out = UnknownCloudUI
        elif type_id is t.V1:
            out = BasicCloudUI
        else:
            # Important to make sure we provide all types.
            assert_never(type_id)
        return out

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> CloudUI:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return UnknownCloudUI()


@ioprepped
@dataclass
class UnknownCloudUI(CloudUI):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder page.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUITypeID:
        return CloudUITypeID.UNKNOWN


class BasicCloudUIComponentTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TEXT = 't'
    LINK = 'l'
    BS_CLASSIC_TOURNEY_RESULT = 'ct'
    DISPLAY_ITEMS = 'di'
    EXPIRE_TIME = 'd'


class BasicCloudUIComponent(IOMultiType[BasicCloudUIComponentTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudUIComponentTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: BasicCloudUIComponentTypeID
    ) -> type[BasicCloudUIComponent]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = BasicCloudUIComponentTypeID
        if type_id is t.UNKNOWN:
            return BasicCloudUIComponentUnknown
        if type_id is t.TEXT:
            return BasicCloudUIComponentText
        if type_id is t.LINK:
            return BasicCloudUIComponentLink
        if type_id is t.BS_CLASSIC_TOURNEY_RESULT:
            return BasicCloudUIBsClassicTourneyResult
        if type_id is t.DISPLAY_ITEMS:
            return BasicCloudUIDisplayItems
        if type_id is t.EXPIRE_TIME:
            return BasicCloudUIExpireTime

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> BasicCloudUIComponent:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return BasicCloudUIComponentUnknown()


@ioprepped
@dataclass
class BasicCloudUIComponentUnknown(BasicCloudUIComponent):
    """An unknown basic client component type.

    In practice these should never show up since the master-server
    generates these on the fly for the client and so should not send
    clients one they can't digest.
    """

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudUIComponentTypeID:
        return BasicCloudUIComponentTypeID.UNKNOWN


@ioprepped
@dataclass
class BasicCloudUIComponentText(BasicCloudUIComponent):
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
    def get_type_id(cls) -> BasicCloudUIComponentTypeID:
        return BasicCloudUIComponentTypeID.TEXT


@ioprepped
@dataclass
class BasicCloudUIComponentLink(BasicCloudUIComponent):
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
    def get_type_id(cls) -> BasicCloudUIComponentTypeID:
        return BasicCloudUIComponentTypeID.LINK


@ioprepped
@dataclass
class BasicCloudUIBsClassicTourneyResult(BasicCloudUIComponent):
    """Show info about a classic tourney."""

    tournament_id: Annotated[str, IOAttrs('t')]
    game: Annotated[str, IOAttrs('g')]
    players: Annotated[int, IOAttrs('p')]
    rank: Annotated[int, IOAttrs('r')]
    trophy: Annotated[str | None, IOAttrs('tr')]
    prizes: Annotated[list[DisplayItemWrapper], IOAttrs('pr')]

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudUIComponentTypeID:
        return BasicCloudUIComponentTypeID.BS_CLASSIC_TOURNEY_RESULT


@ioprepped
@dataclass
class BasicCloudUIDisplayItems(BasicCloudUIComponent):
    """Show some display-items."""

    items: Annotated[list[DisplayItemWrapper], IOAttrs('d')]
    width: Annotated[float, IOAttrs('w')] = 100.0
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudUIComponentTypeID:
        return BasicCloudUIComponentTypeID.DISPLAY_ITEMS


@ioprepped
@dataclass
class BasicCloudUIExpireTime(BasicCloudUIComponent):
    """Show expire-time."""

    time: Annotated[datetime.datetime, IOAttrs('d')]
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudUIComponentTypeID:
        return BasicCloudUIComponentTypeID.EXPIRE_TIME


@ioprepped
@dataclass
class BasicCloudUI(CloudUI):
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

    components: Annotated[list[BasicCloudUIComponent], IOAttrs('s')]

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
    def get_type_id(cls) -> CloudUITypeID:
        return CloudUITypeID.V1

    def contains_unknown_elements(self) -> bool:
        """Whether something within us is an unknown type or enum."""
        return (
            self.interaction_style is self.InteractionStyle.UNKNOWN
            or self.button_label_positive is self.ButtonLabel.UNKNOWN
            or self.button_label_negative is self.ButtonLabel.UNKNOWN
            or any(
                c.get_type_id() is BasicCloudUIComponentTypeID.UNKNOWN
                for c in self.components
            )
        )


@ioprepped
@dataclass
class CloudUIWrapper:
    """Wrapper for a CloudUI and its common data."""

    id: Annotated[str, IOAttrs('i')]
    createtime: Annotated[datetime.datetime, IOAttrs('c')]
    ui: Annotated[CloudUI, IOAttrs('e')]


class CloudUIAction(Enum):
    """Types of actions we can run."""

    BUTTON_PRESS_POSITIVE = 'p'
    BUTTON_PRESS_NEGATIVE = 'n'
