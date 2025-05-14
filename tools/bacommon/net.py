# Released under the MIT License. See LICENSE for details.
#
"""Network related data and functionality."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Annotated
from dataclasses import dataclass, field

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class ServerNodeEntry:
    """Information about a specific server."""

    zone: Annotated[str, IOAttrs('r')]

    # TODO: Remove soft_default after all master-servers upgraded.
    latlong: Annotated[
        tuple[float, float] | None, IOAttrs('ll', soft_default=None)
    ]
    address: Annotated[str, IOAttrs('a')]
    port: Annotated[int, IOAttrs('p')]


@ioprepped
@dataclass
class ServerNodeQueryResponse:
    """A response to a query about server-nodes."""

    # The current utc time on the master server.
    time: Annotated[datetime.datetime, IOAttrs('t')]

    # Where the master server sees the query as coming from.
    latlong: Annotated[tuple[float, float] | None, IOAttrs('ll')]

    ping_per_dist: Annotated[float, IOAttrs('ppd')]
    max_dist: Annotated[float, IOAttrs('md')]

    debug_log_seconds: Annotated[
        float | None, IOAttrs('d', store_default=False)
    ] = None

    # If present, something went wrong, and this describes it.
    error: Annotated[str | None, IOAttrs('e', store_default=False)] = None

    # The set of servernodes.
    servers: Annotated[
        list[ServerNodeEntry], IOAttrs('s', store_default=False)
    ] = field(default_factory=list)


@ioprepped
@dataclass
class PrivateHostingState:
    """Combined state of whether we're hosting, whether we can, etc."""

    unavailable_error: str | None = None
    party_code: str | None = None
    tickets_to_host_now: int = 0
    tokens_to_host_now: int = 0
    minutes_until_free_host: float | None = None
    free_host_minutes_remaining: float | None = None


@ioprepped
@dataclass
class PrivateHostingConfig:
    """Config provided when hosting a private party."""

    session_type: str = 'ffa'
    playlist_name: str = 'Unknown'
    randomize: bool = False
    tutorial: bool = False
    custom_team_names: tuple[str, str] | None = None
    custom_team_colors: (
        tuple[tuple[float, float, float], tuple[float, float, float]] | None
    ) = None
    playlist: list[dict[str, Any]] | None = None
    exit_minutes: float = 120.0
    exit_minutes_unclean: float = 180.0
    exit_minutes_idle: float = 10.0


@ioprepped
@dataclass
class PrivatePartyConnectResult:
    """Info about a server we get back when connecting."""

    error: str | None = None
    address4: Annotated[str | None, IOAttrs('addr')] = None
    address6: Annotated[str | None, IOAttrs('addr6')] = None
    port: int | None = None
    password: str | None = None
