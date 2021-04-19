# Released under the MIT License. See LICENSE for details.
#
"""Network related data and functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

from efro import entity

if TYPE_CHECKING:
    pass


class ServerNodeEntry(entity.CompoundValue):
    """Information about a specific server."""
    region = entity.Field('r', entity.StringValue())
    address = entity.Field('a', entity.StringValue())
    port = entity.Field('p', entity.IntValue())


class ServerNodeQueryResponse(entity.Entity):
    """A response to a query about server-nodes."""

    # If present, something went wrong, and this describes it.
    error = entity.Field('e', entity.OptionalStringValue(store_default=False))

    # The set of servernodes.
    servers = entity.CompoundListField('s',
                                       ServerNodeEntry(),
                                       store_default=False)
