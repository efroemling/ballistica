# Released under the MIT License. See LICENSE for details.
#
"""Basic cloud-dialog."""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

import bacommon.displayitem as ditm
from bacommon.clouddialog._clouddialog import CloudDialog, CloudDialogTypeID


class ComponentTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TEXT = 't'
    LINK = 'l'
    BS_CLASSIC_TOURNEY_RESULT = 'ct'
    DISPLAY_ITEMS = 'di'
    EXPIRE_TIME = 'd'


class Component(IOMultiType[ComponentTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> ComponentTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ComponentTypeID) -> type[Component]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = ComponentTypeID
        if type_id is t.UNKNOWN:
            return Unknown
        if type_id is t.TEXT:
            return Text
        if type_id is t.LINK:
            return Link
        if type_id is t.BS_CLASSIC_TOURNEY_RESULT:
            return ClassicTourneyResult
        if type_id is t.DISPLAY_ITEMS:
            return DisplayItems
        if type_id is t.EXPIRE_TIME:
            return ExpireTime

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Component:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return Unknown()


@ioprepped
@dataclass
class Unknown(Component):
    """An unknown basic client component type.

    In practice these should never show up since the master-server
    generates these on the fly for the client and so should not send
    clients one they can't digest.
    """

    @override
    @classmethod
    def get_type_id(cls) -> ComponentTypeID:
        return ComponentTypeID.UNKNOWN


@ioprepped
@dataclass
class Text(Component):
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
    def get_type_id(cls) -> ComponentTypeID:
        return ComponentTypeID.TEXT


@ioprepped
@dataclass
class Link(Component):
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
    def get_type_id(cls) -> ComponentTypeID:
        return ComponentTypeID.LINK


@ioprepped
@dataclass
class ClassicTourneyResult(Component):
    """Show info about a classic tourney."""

    tournament_id: Annotated[str, IOAttrs('t')]
    game: Annotated[str, IOAttrs('g')]
    players: Annotated[int, IOAttrs('p')]
    rank: Annotated[int, IOAttrs('r')]
    trophy: Annotated[str | None, IOAttrs('tr')]
    prizes: Annotated[list[ditm.Wrapper], IOAttrs('pr')]

    @override
    @classmethod
    def get_type_id(cls) -> ComponentTypeID:
        return ComponentTypeID.BS_CLASSIC_TOURNEY_RESULT


@ioprepped
@dataclass
class DisplayItems(Component):
    """Show some display-items."""

    items: Annotated[list[ditm.Wrapper], IOAttrs('d')]
    width: Annotated[float, IOAttrs('w')] = 100.0
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> ComponentTypeID:
        return ComponentTypeID.DISPLAY_ITEMS


@ioprepped
@dataclass
class ExpireTime(Component):
    """Show expire-time."""

    time: Annotated[datetime.datetime, IOAttrs('d')]
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    @override
    @classmethod
    def get_type_id(cls) -> ComponentTypeID:
        return ComponentTypeID.EXPIRE_TIME


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


@ioprepped
@dataclass
class BasicCloudDialog(CloudDialog):
    """A basic UI for the client."""

    components: Annotated[list[Component], IOAttrs('s')]

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
            self.interaction_style is InteractionStyle.UNKNOWN
            or self.button_label_positive is ButtonLabel.UNKNOWN
            or self.button_label_negative is ButtonLabel.UNKNOWN
            or any(
                c.get_type_id() is ComponentTypeID.UNKNOWN
                for c in self.components
            )
        )
