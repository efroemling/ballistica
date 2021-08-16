# Released under the MIT License. See LICENSE for details.
#
"""Network related data and functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from efro import entity
from efro.dataclassio import ioprepped

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


@ioprepped
@dataclass
class PrivateHostingState:
    """Combined state of whether we're hosting, whether we can, etc."""
    unavailable_error: Optional[str] = None
    party_code: Optional[str] = None
    tickets_to_host_now: int = 0
    minutes_until_free_host: Optional[float] = None
    free_host_minutes_remaining: Optional[float] = None


@ioprepped
@dataclass
class PrivateHostingConfig:
    """Config provided when hosting a private party."""
    session_type: str = 'ffa'
    playlist_name: str = 'Unknown'
    randomize: bool = False
    tutorial: bool = False
    custom_team_names: Optional[Tuple[str, str]] = None
    custom_team_colors: Optional[Tuple[Tuple[float, float, float],
                                       Tuple[float, float, float]]] = None
    playlist: Optional[List[Dict[str, Any]]] = None
    exit_minutes: float = 120.0
    exit_minutes_unclean: float = 180.0
    exit_minutes_idle: float = 10.0


@ioprepped
@dataclass
class PrivatePartyConnectResult:
    """Info about a server we get back when connecting."""
    error: Optional[str] = None
    addr: Optional[str] = None
    port: Optional[int] = None
    password: Optional[str] = None
