# Released under the MIT License. See LICENSE for details.
#
"""Network related data and functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

from typing_extensions import Annotated

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class ServerNodeEntry:
    """Information about a specific server."""
    region: Annotated[str, IOAttrs('r')]
    address: Annotated[str, IOAttrs('a')]
    port: Annotated[int, IOAttrs('p')]


@ioprepped
@dataclass
class ServerNodeQueryResponse:
    """A response to a query about server-nodes."""

    # If present, something went wrong, and this describes it.
    error: Annotated[Optional[str], IOAttrs('e', store_default=False)] = None

    # The set of servernodes.
    servers: Annotated[List[ServerNodeEntry],
                       IOAttrs('s', store_default=False)] = field(
                           default_factory=list)


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
