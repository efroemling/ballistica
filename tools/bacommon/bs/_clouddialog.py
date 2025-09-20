# Released under the MIT License. See LICENSE for details.
#
"""Simple cloud-defined UIs for things like notifications."""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.bs._displayitem import DisplayItemWrapper


class CloudDialogTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    BASIC = 'b'


class CloudDialog(IOMultiType[CloudDialogTypeID]):
    """Small self-contained ui bit provided by the cloud.

    These take care of updating and/or dismissing themselves based on
    user input. Useful for things such as inbox messages. For more
    complex UI construction, look at :class:`CloudUI`.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudDialogTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: CloudDialogTypeID) -> type[CloudDialog]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import
        out: type[CloudDialog]

        t = CloudDialogTypeID
        if type_id is t.UNKNOWN:
            out = UnknownCloudDialog
        elif type_id is t.BASIC:
            out = BasicCloudDialog
        else:
            # Important to make sure we provide all types.
            assert_never(type_id)
        return out

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> CloudDialog:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return UnknownCloudDialog()


@ioprepped
@dataclass
class UnknownCloudDialog(CloudDialog):
    """Fallback type for unrecognized entries."""

    @override
    @classmethod
    def get_type_id(cls) -> CloudDialogTypeID:
        return CloudDialogTypeID.UNKNOWN


class BasicCloudDialogComponentTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TEXT = 't'
    LINK = 'l'
    BS_CLASSIC_TOURNEY_RESULT = 'ct'
    DISPLAY_ITEMS = 'di'
    EXPIRE_TIME = 'd'


class BasicCloudDialogComponent(IOMultiType[BasicCloudDialogComponentTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudDialogComponentTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: BasicCloudDialogComponentTypeID
    ) -> type[BasicCloudDialogComponent]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = BasicCloudDialogComponentTypeID
        if type_id is t.UNKNOWN:
            return BasicCloudDialogComponentUnknown
        if type_id is t.TEXT:
            return BasicCloudDialogComponentText
        if type_id is t.LINK:
            return BasicCloudDialogComponentLink
        if type_id is t.BS_CLASSIC_TOURNEY_RESULT:
            return BasicCloudDialogBsClassicTourneyResult
        if type_id is t.DISPLAY_ITEMS:
            return BasicCloudDialogDisplayItems
        if type_id is t.EXPIRE_TIME:
            return BasicCloudDialogExpireTime

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> BasicCloudDialogComponent:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return BasicCloudDialogComponentUnknown()


@ioprepped
@dataclass
class BasicCloudDialogComponentUnknown(BasicCloudDialogComponent):
    """An unknown basic client component type.

    In practice these should never show up since the master-server
    generates these on the fly for the client and so should not send
    clients one they can't digest.
    """

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudDialogComponentTypeID:
        return BasicCloudDialogComponentTypeID.UNKNOWN


@ioprepped
@dataclass
class BasicCloudDialogComponentText(BasicCloudDialogComponent):
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
    def get_type_id(cls) -> BasicCloudDialogComponentTypeID:
        return BasicCloudDialogComponentTypeID.TEXT


@ioprepped
@dataclass
class BasicCloudDialogComponentLink(BasicCloudDialogComponent):
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
    def get_type_id(cls) -> BasicCloudDialogComponentTypeID:
        return BasicCloudDialogComponentTypeID.LINK


@ioprepped
@dataclass
class BasicCloudDialogBsClassicTourneyResult(BasicCloudDialogComponent):
    """Show info about a classic tourney."""

    tournament_id: Annotated[str, IOAttrs('t')]
    game: Annotated[str, IOAttrs('g')]
    players: Annotated[int, IOAttrs('p')]
    rank: Annotated[int, IOAttrs('r')]
    trophy: Annotated[str | None, IOAttrs('tr')]
    prizes: Annotated[list[DisplayItemWrapper], IOAttrs('pr')]

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudDialogComponentTypeID:
        return BasicCloudDialogComponentTypeID.BS_CLASSIC_TOURNEY_RESULT


@ioprepped
@dataclass
class BasicCloudDialogDisplayItems(BasicCloudDialogComponent):
    """Show some display-items."""

    items: Annotated[list[DisplayItemWrapper], IOAttrs('d')]
    width: Annotated[float, IOAttrs('w')] = 100.0
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudDialogComponentTypeID:
        return BasicCloudDialogComponentTypeID.DISPLAY_ITEMS


@ioprepped
@dataclass
class BasicCloudDialogExpireTime(BasicCloudDialogComponent):
    """Show expire-time."""

    time: Annotated[datetime.datetime, IOAttrs('d')]
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> BasicCloudDialogComponentTypeID:
        return BasicCloudDialogComponentTypeID.EXPIRE_TIME


@ioprepped
@dataclass
class BasicCloudDialog(CloudDialog):
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

    components: Annotated[list[BasicCloudDialogComponent], IOAttrs('s')]

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
    def get_type_id(cls) -> CloudDialogTypeID:
        return CloudDialogTypeID.BASIC

    def contains_unknown_elements(self) -> bool:
        """Whether something within us is an unknown type or enum."""
        return (
            self.interaction_style is self.InteractionStyle.UNKNOWN
            or self.button_label_positive is self.ButtonLabel.UNKNOWN
            or self.button_label_negative is self.ButtonLabel.UNKNOWN
            or any(
                c.get_type_id() is BasicCloudDialogComponentTypeID.UNKNOWN
                for c in self.components
            )
        )


@ioprepped
@dataclass
class CloudDialogWrapper:
    """Wrapper for a CloudDialog and its common data."""

    id: Annotated[str, IOAttrs('i')]
    createtime: Annotated[datetime.datetime, IOAttrs('c')]
    ui: Annotated[CloudDialog, IOAttrs('e')]


class CloudDialogAction(Enum):
    """Types of actions we can run."""

    BUTTON_PRESS_POSITIVE = 'p'
    BUTTON_PRESS_NEGATIVE = 'n'
