# Released under the MIT License. See LICENSE for details.
#
"""Network related data and functionality.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Annotated
from dataclasses import dataclass, field

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class ClientRejection:
    """Tells a client to stop or slow its contact with the server.

    Carried on :class:`ServerNodeQueryResponse` so the client can
    notice at app launch (rather than after a failed WS handshake).
    """

    class Kind(Enum):
        """What the client should do in response."""

        #: Stop contacting the server from this build — nothing is
        #: going to change. Client should stop its reconnect loop.
        PERMANENT = 'p'

        #: Back off but keep retrying — the condition is expected to
        #: clear on its own.
        TRANSIENT = 't'

    kind: Annotated[Kind, IOAttrs('k')]

    #: Optional English text to show the user. Must be a key from the
    #: ``serverResponses`` translation catalog (so localized
    #: translations are already present). ``None`` means apply the
    #: behavior silently with no user-visible message.
    message: Annotated[str | None, IOAttrs('m', soft_default=None)] = None


@ioprepped
@dataclass
class ServerNodeEntry:
    """Information about a specific server."""

    zone: Annotated[str, IOAttrs('r')]
    latlong: Annotated[tuple[float, float] | None, IOAttrs('ll')]
    address: Annotated[str, IOAttrs('a')]
    port: Annotated[int, IOAttrs('p')]


@ioprepped
@dataclass
class InsecureDirectivePayload:
    """Payload of a signed ``InsecureDirective``.

    Serialized to JSON bytes and Ed25519-signed by the master server.
    Clients verify using a long-lived public key embedded at compile
    time.
    """

    #: Directs the client whether to use insecure (non-TLS) connections
    #: for this server. Intended for regions where TLS is actively
    #: interfered with by middleboxes (handshake blocking, forced
    #: termination, etc.) and secure connections to our infra are
    #: unreliable. Clients latch the first directive they see for the
    #: session, so the server's signal is take-it-or-leave-it-once
    #: rather than a continuously-consulted state. Storage-alias ``a``
    #: is retained so old signed payloads in flight continue to
    #: deserialize.
    use_insecure: Annotated[bool, IOAttrs('a')]


@ioprepped
@dataclass
class InsecureDirective:
    """A server-signed directive delivered over plain HTTP."""

    #: JSON-serialized :class:`InsecureDirectivePayload`.
    payload: Annotated[bytes, IOAttrs('p')]

    #: Ed25519 signature over ``payload`` bytes.
    signature: Annotated[bytes, IOAttrs('s')]


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

    # If this came from a bootstrap server, which zone was it in.
    bootstrap_zone: Annotated[str | None, IOAttrs('b', soft_default=None)]

    debug_log_seconds: Annotated[
        float | None, IOAttrs('d', store_default=False)
    ] = None

    # If present, something went wrong, and this describes it.
    error: Annotated[str | None, IOAttrs('e', store_default=False)] = None

    # The set of servernodes.
    servers: Annotated[
        list[ServerNodeEntry], IOAttrs('s', store_default=False)
    ] = field(default_factory=list)

    # Ranked basn hostnames for transport-agent connection. Ordered
    # by preference given the client's reported zones (via the
    # ``zones`` query param) with a geographic-proximity fallback.
    # Clients try these in order via ``wss://<host>/ws_transport``.
    hosts: Annotated[list[str], IOAttrs('h', store_default=False)] = field(
        default_factory=list
    )

    # Signed directive telling the client whether to allow insecure
    # (non-TLS) connections. Populated only on HTTP responses — HTTPS
    # responses rely on the TLS channel for authenticity. Clients
    # verify the embedded signature using a compile-time public key
    # before trusting the flag.
    insecure_directive: Annotated[
        InsecureDirective | None,
        IOAttrs('id', soft_default=None, store_default=False),
    ] = None

    # Instruct the client to stop or slow down — they are too old,
    # banned, waiting out a maintenance window, etc. See
    # :class:`ClientRejection`. ``None`` means no rejection.
    rejection: Annotated[
        ClientRejection | None,
        IOAttrs('rj', soft_default=None, store_default=False),
    ] = None


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
