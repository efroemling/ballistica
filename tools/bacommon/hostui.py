# Released under the MIT License. See LICENSE for details.
#
"""Wire types for host-defined ui (host doc-ui and party notices).

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.

A game host can give connected clients buttons in their in-game menu
and party window, serve the doc-ui pages those buttons open, and post
a party notice. Everything here rides the per-connection json message
channel between host and client (``BA_JMESSAGE_HOST_UI``), never the
scene stream: it is per client, not per activity, and never recorded
into replays. Design: ``docs/initiatives/host-docui.md``.

These shapes go between game builds, so once a build speaking them
ships, storage names and type-id values may never be repurposed.
Add rather than change.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.langstr import LangStrSpec
from bacommon.docui import DocUIRequest, DocUIResponse
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    from typing import Any

#: First engine build that speaks host-ui messages. Hosts send them only
#: to peers at least this new, and clients send requests only to hosts
#: at least this new. Must match ``BA_HOST_UI_MIN_BUILD`` in the
#: engine's ``networking.h``, which enforces the same gate natively.
HOST_UI_MIN_BUILD = 23067

#: Largest request (serialized) a client will send a host. Hosts kick
#: clients whose messages exceed 50000 bytes, so stay well under that.
MAX_REQUEST_BYTES = 40000

#: Largest response message (as sent, so compressed) a host will send or
#: a client accept. Pages share the reliable ordered message stream with
#: game traffic, so keep them modest.
MAX_RESPONSE_BYTES = 32000

#: Largest a response may be once decompressed. Pages compress several
#: times over; this bounds what a small message can expand into.
MAX_RESPONSE_DECOMPRESSED_BYTES = 512 * 1024

#: Most buttons a client shows from a host in any one placement (any
#: more are dropped). Menus only have room for a few.
MAX_BUTTONS_PER_PLACEMENT = 8

#: Largest button label a client shows from a host, as encoded json.
MAX_LABEL_BYTES = 400

#: Largest party notice a client shows from a host, as encoded json.
MAX_NOTICE_BYTES = 1000

#: Requests a host serves a client in a burst before rate limiting.
REQUEST_BURST = 8

#: Requests per second a host serves a client once its burst is spent.
REQUESTS_PER_SECOND = 2.0

#: Requests a host has in progress for any one client at a time (async
#: handlers can take a while).
MAX_REQUESTS_IN_FLIGHT = 4


# (Any: arbitrary json, as json.loads() itself returns.)
def loads_untrusted(data: str | bytes) -> Any:
    """Parse json from a peer, refusing non-finite numbers.

    Plain :func:`json.loads` accepts ``NaN`` and ``Infinity`` (and turns
    huge literals such as ``1e999`` into infinity); none of those are
    anything a peer has reason to send, and they can upset layout code.
    Raises :class:`ValueError` for them.
    """
    import json
    import math

    def _float(val: str) -> float:
        out = float(val)
        if not math.isfinite(out):
            raise ValueError(f'Non-finite number {val!r}.')
        return out

    def _constant(val: str) -> float:
        raise ValueError(f'Non-finite number {val!r}.')

    return json.loads(data, parse_float=_float, parse_constant=_constant)


class ButtonPlacement(Enum):
    """Where a host-defined button shows up on clients."""

    #: A placement this client doesn't know (from a newer host). Such
    #: buttons are not shown.
    UNKNOWN = 'u'

    #: The in-game menu, grouped with any other custom entries between
    #: Resume and Leave/End.
    IN_GAME_MENU = 'g'

    #: The party window's '...' menu, after the built-in choices.
    PARTY_MENU = 'p'


@ioprepped
@dataclass
class Button:
    """A host-defined button that opens a host-served doc-ui page."""

    #: The button's label. Must be a literal or come from a package in
    #: the host's universe (clients refuse anything else).
    label: Annotated[LangStrSpec, IOAttrs('l')]

    #: Where the button goes.
    placement: Annotated[
        ButtonPlacement,
        IOAttrs('p', enum_fallback=ButtonPlacement.UNKNOWN),
    ]

    #: The page to open; sent back to the host when pressed.
    request: Annotated[dui2.Request, IOAttrs('r')]

    #: The window layout to open the page in. (Defaults to wide, like
    #: routes do.)
    layout: Annotated[
        dui2.WindowLayout,
        IOAttrs(
            'w',
            store_default=False,
            enum_fallback=dui2.WindowLayout.WIDE,
        ),
    ] = dui2.WindowLayout.WIDE


@ioprepped
@dataclass
class KickTarget:
    """Where a host takes clients who ask to kick a player.

    Clients offer a kick option on party members only when their host
    sends one of these; choosing it opens the page for :attr:`request`
    with the chosen player's client id put in its args under
    :attr:`client_id_arg`.
    """

    #: The page to open (its client-id arg gets filled in).
    request: Annotated[dui2.Request, IOAttrs('r')]

    #: The key in the request's args that takes the player's client id.
    client_id_arg: Annotated[str, IOAttrs('a')]


@ioprepped
@dataclass
class State:
    """Everything a host currently declares to one client.

    Always sent whole; each one replaces the last. The notice and
    flashes are timed: each carries the time it has left, so a client
    joining partway through sees the rest of it, and nothing stays up
    forever if a host forgets about it.
    """

    buttons: Annotated[list[Button], IOAttrs('b', store_default=False)] = field(
        default_factory=list
    )

    #: Text shown below the party icon, for :attr:`notice_time_left`
    #: seconds.
    notice: Annotated[LangStrSpec | None, IOAttrs('n', store_default=False)] = (
        None
    )

    #: Seconds the notice has left, as of sending.
    notice_time_left: Annotated[float, IOAttrs('nt', store_default=False)] = 0.0

    #: Seconds the party icon has left to flash, as of sending.
    party_icon_flash_time_left: Annotated[
        float, IOAttrs('fi', store_default=False)
    ] = 0.0

    #: Seconds the party window's '...' button has left to flash, as of
    #: sending.
    party_menu_flash_time_left: Annotated[
        float, IOAttrs('fm', store_default=False)
    ] = 0.0

    #: Where to take clients who ask to kick a party member (None: the
    #: host offers no kicking).
    kick: Annotated[KickTarget | None, IOAttrs('k', store_default=False)] = None


class MessageTypeID(Enum):
    """Type ids for host-ui messages."""

    UNKNOWN = 'u'
    STATE = 's'
    DOCUI_REQUEST = 'q'
    DOCUI_RESPONSE = 'r'


class Message(IOMultiType[MessageTypeID]):
    """A host-ui message (either direction)."""

    @override
    @classmethod
    def get_type_id(cls) -> MessageTypeID:
        # Require child classes to supply this themselves.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: MessageTypeID) -> type[Message]:
        t = MessageTypeID
        if type_id is t.UNKNOWN:
            return UnknownMessage
        if type_id is t.STATE:
            return StateMessage
        if type_id is t.DOCUI_REQUEST:
            return DocUIRequestMessage
        if type_id is t.DOCUI_RESPONSE:
            return DocUIResponseMessage
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Message:
        return UnknownMessage()


@ioprepped
@dataclass
class UnknownMessage(Message):
    """Stands in for a message type we don't know (from a newer peer)."""

    @override
    @classmethod
    def get_type_id(cls) -> MessageTypeID:
        return MessageTypeID.UNKNOWN


@ioprepped
@dataclass
class StateMessage(Message):
    """Host to client: the client's current declarations."""

    state: Annotated[State, IOAttrs('s')]

    @override
    @classmethod
    def get_type_id(cls) -> MessageTypeID:
        return MessageTypeID.STATE


@ioprepped
@dataclass
class DocUIRequestMessage(Message):
    """Client to host: a doc-ui request for a host-served page."""

    #: Echoed in the response so the client can match it up.
    request_id: Annotated[int, IOAttrs('i')]
    request: Annotated[DocUIRequest, IOAttrs('r')]

    @override
    @classmethod
    def get_type_id(cls) -> MessageTypeID:
        return MessageTypeID.DOCUI_REQUEST


@ioprepped
@dataclass
class DocUIResponseMessage(Message):
    """Host to client: the answer to a :class:`DocUIRequestMessage`.

    The response travels zstd-compressed (see :func:`encode_response`),
    which keeps big pages small on the wire and lets the receiver route
    the message cheaply and decode the response off its logic thread.
    """

    request_id: Annotated[int, IOAttrs('i')]

    #: The response, as :func:`encode_response` makes it.
    data: Annotated[bytes, IOAttrs('d')]

    @override
    @classmethod
    def get_type_id(cls) -> MessageTypeID:
        return MessageTypeID.DOCUI_RESPONSE


class ResponseTooLargeError(Exception):
    """A response is too large to send or accept."""


def encode_response(response: DocUIResponse) -> bytes:
    """Serialize and compress a response for a DocUIResponseMessage.

    Pure computation; fine to run off the logic thread. Raises
    :class:`ResponseTooLargeError` if it would decompress past
    :data:`MAX_RESPONSE_DECOMPRESSED_BYTES`.
    """
    from compression import zstd

    from efro.dataclassio import dataclass_to_json

    raw = dataclass_to_json(response).encode()
    if len(raw) > MAX_RESPONSE_DECOMPRESSED_BYTES:
        raise ResponseTooLargeError(
            f'Response is {len(raw)} bytes uncompressed'
            f' (max {MAX_RESPONSE_DECOMPRESSED_BYTES}).'
        )
    return zstd.compress(raw)


def decode_response(data: bytes) -> DocUIResponse:
    """Decompress and decode a response from a DocUIResponseMessage.

    Pure computation; fine to run off the logic thread. The data comes
    from an untrusted peer, so decompression is bounded: raises
    :class:`ResponseTooLargeError` past
    :data:`MAX_RESPONSE_DECOMPRESSED_BYTES` and other exceptions for
    anything malformed.
    """
    from compression import zstd

    from efro.dataclassio import dataclass_from_dict

    decompressor = zstd.ZstdDecompressor()
    raw = decompressor.decompress(
        data, max_length=MAX_RESPONSE_DECOMPRESSED_BYTES
    )
    if not decompressor.eof:
        raise ResponseTooLargeError(
            'Response is too large (or truncated) once decompressed.'
        )
    # Decoded lossy (a newer host may send types we don't know) via a
    # box, since lossy decoding flags the top-level object as not
    # writable and the response itself may get written out again.
    return dataclass_from_dict(
        _ResponseBox, {'r': loads_untrusted(raw)}, lossy=True
    ).response


@ioprepped
@dataclass
class _ResponseBox:
    response: Annotated[DocUIResponse, IOAttrs('r')]
