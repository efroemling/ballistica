# Released under the MIT License. See LICENSE for details.
#
"""DisplayItem related functionality."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Annotated, override, assert_never

from efro.util import pairs_to_flat
from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.bs._chest import ClassicChestAppearance


class DisplayItemTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TICKETS = 't'
    TOKENS = 'k'
    TEST = 's'
    CHEST = 'c'


class DisplayItem(IOMultiType[DisplayItemTypeID]):
    """Some amount of something that can be shown or described.

    Used to depict chest contents, inventory, rewards, etc.
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
        should be accessed from there when available. This allows
        clients to give descriptions even for newer display items they
        don't recognize.
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
        return self.appearance.pretty_name, []


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
