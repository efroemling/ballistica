# Released under the MIT License. See LICENSE for details.
#
"""Functionality for displaying currencies, prizes, owned items, etc.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Annotated, override, assert_never

from efro.util import pairs_to_flat
from efro.dataclassio import ioprepped, IOAttrs, IOMultiType


class ItemTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TICKETS = 't'
    TICKETS_PURPLE = 'tp'
    TOKENS = 'k'
    TEST = 's'
    CHEST = 'c'


class Item(IOMultiType[ItemTypeID]):
    """Some amount of something that can be shown or described.

    Used to depict chest contents, inventory, rewards, etc.
    """

    @override
    @classmethod
    def get_type_id(cls) -> ItemTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ItemTypeID) -> type[Item]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = ItemTypeID
        if type_id is t.UNKNOWN:
            return Unknown
        if type_id is t.TICKETS:
            return Tickets
        if type_id is t.TICKETS_PURPLE:
            return PurpleTickets
        if type_id is t.TOKENS:
            return Tokens
        if type_id is t.TEST:
            return Test
        if type_id is t.CHEST:
            from bacommon.classic._chest import ClassicChestDisplayItem

            return ClassicChestDisplayItem

        # Important to make sure we provide all types.
        assert_never(type_id)

    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        """Return a string description and subs for the item.

        Will be translated on the client using the 'displayItemNames'
        Lstr category.

        These decriptions are baked into the display-item wrapper and
        should be accessed from there when available. This allows
        clients to give descriptions even for newer display item types
        they don't recognize.
        """
        raise NotImplementedError()

    # Implement fallbacks so client can digest item lists even if they
    # contain unrecognized stuff. The wrapper contains basic
    # baked down info that they can still use in such cases.
    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Item:
        return Unknown()


@ioprepped
@dataclass
class Unknown(Item):
    """Something we don't know how to display."""

    @override
    @classmethod
    def get_type_id(cls) -> ItemTypeID:
        return ItemTypeID.UNKNOWN

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        import logging

        # Make noise but don't break.
        logging.exception(
            'Unknown.get_description() should never be called.'
            ' Always access descriptions on the display-item wrapper.'
        )
        return 'Unknown', []


@ioprepped
@dataclass
class Tickets(Item):
    """Some amount of tickets."""

    count: Annotated[int, IOAttrs('c')]

    @override
    @classmethod
    def get_type_id(cls) -> ItemTypeID:
        return ItemTypeID.TICKETS

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return '${C} Tickets', [('${C}', str(self.count))]


@ioprepped
@dataclass
class PurpleTickets(Item):
    """Some amount of purple tickets."""

    count: Annotated[int, IOAttrs('c')]

    @override
    @classmethod
    def get_type_id(cls) -> ItemTypeID:
        return ItemTypeID.TICKETS_PURPLE

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return '${C} Purple Tickets', [('${C}', str(self.count))]


@ioprepped
@dataclass
class Tokens(Item):
    """Some amount of tokens."""

    count: Annotated[int, IOAttrs('c')]

    @override
    @classmethod
    def get_type_id(cls) -> ItemTypeID:
        return ItemTypeID.TOKENS

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return '${C} Tokens', [('${C}', str(self.count))]


@ioprepped
@dataclass
class Test(Item):
    """Fills usable space for a display-item - good for calibration."""

    @override
    @classmethod
    def get_type_id(cls) -> ItemTypeID:
        return ItemTypeID.TEST

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return 'Test', []


@ioprepped
@dataclass
class Wrapper:
    """Wraps a display-item and some baked out info.

    This allows clients to at least give descriptions of new
    display-item types they may not have locally.
    """

    item: Annotated[Item, IOAttrs('i')]
    description: Annotated[str, IOAttrs('d')]
    description_subs: Annotated[list[str] | None, IOAttrs('s')]

    @classmethod
    def for_item(cls, item: Item) -> Wrapper:
        """Convenience method to wrap a display-item."""
        desc, subs = item.get_description()
        return Wrapper(item, desc, pairs_to_flat(subs))
