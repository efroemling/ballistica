# Released under the MIT License. See LICENSE for details.
#
"""Payload types for the automation SmartSocket channel kind.

One root pair per channel kind (see the hierarchy-per-contract rule
in ``streamcall-smartsocket.md``): a driver sends
:class:`AutomationCommand` up, the device answers with
:class:`AutomationEvent`. The relay never decodes either -- a new
payload type must never require a basn rollout.

The channel is a sibling of the cloud console's, deliberately: both
carry code to a device and results back. What differs is *who may*
-- a console session is authorized by account ownership and ships in
every build, while this one is authorized by a device-minted key
(so a signed-out test device can be driven) and exists only in
developer builds. That difference is why the capability is separate
rather than an option on the console's.

**Client-visible**, so these definitions are a public wire contract
once a build speaking them ships: storage names and type-id values
may never be repurposed, and removed ones stay retired. Add rather
than change.
"""

from typing import Annotated, override
from enum import Enum
from dataclasses import dataclass, field

from efro.logging import LogEntry
from efro.dataclassio import ioprepped, IOMultiType, IOAttrs


class AutomationCommandTypeID(Enum):
    """Type IDs for driver-to-device payloads."""

    EXEC = 'e'
    SCREENSHOT = 's'
    HELLO = 'h'


class AutomationCommand(IOMultiType[AutomationCommandTypeID]):
    """Something a driver asked the device to do."""

    @override
    @classmethod
    def get_type_id(cls) -> AutomationCommandTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: AutomationCommandTypeID
    ) -> type[AutomationCommand]:
        out: type[AutomationCommand]
        if type_id is AutomationCommandTypeID.EXEC:
            out = ExecCommand
        elif type_id is AutomationCommandTypeID.SCREENSHOT:
            out = ScreenshotCommand
        elif type_id is AutomationCommandTypeID.HELLO:
            out = HelloCommand
        else:
            raise ValueError(f'Unrecognized type-id {type_id}.')
        return out


@ioprepped
@dataclass
class ExecCommand(AutomationCommand):
    """Run some Python on the device's logic thread.

    Runs on the device's logic thread, the way any driver-supplied
    code does.
    """

    code: Annotated[str, IOAttrs('c')]

    #: Echoed back on every event this command produces, so a driver
    #: can match answers to questions without assuming ordering.
    tag: Annotated[str, IOAttrs('t')] = ''

    @override
    @classmethod
    def get_type_id(cls) -> AutomationCommandTypeID:
        return AutomationCommandTypeID.EXEC


@ioprepped
@dataclass
class ScreenshotCommand(AutomationCommand):
    """Capture the device's screen and send the image back.

    Distinct from exec'ing a capture call: that writes a file on the
    *device*, which is no use to a driver somewhere else. This one
    answers with a :class:`ScreenshotEvent` carrying the bytes.
    """

    tag: Annotated[str, IOAttrs('t')] = ''

    #: Ask for lossless PNG instead of the default JPEG. Costs roughly
    #: an order of magnitude in size (measured 2.8MB vs 254KB on a
    #: 2048x1152 frame), so it is worth it only when pixel-perfect
    #: data is -- exact-color assertions and the like. Note a PNG of a
    #: large screen can exceed what one channel message may carry.
    lossless: Annotated[bool, IOAttrs('l')] = False

    @override
    @classmethod
    def get_type_id(cls) -> AutomationCommandTypeID:
        return AutomationCommandTypeID.SCREENSHOT


@ioprepped
@dataclass
class HelloCommand(AutomationCommand):
    """Ask the device to introduce itself.

    A driver sends this on attach rather than relying on the device
    having announced itself unprompted: the device's unsolicited
    hello goes out once, at channel birth, and is consumed by
    whichever driver was attached (or waiting) then. A second driver
    -- or the same one reattaching after the first exchange -- would
    otherwise wait forever for something already delivered.
    """

    @override
    @classmethod
    def get_type_id(cls) -> AutomationCommandTypeID:
        return AutomationCommandTypeID.HELLO


class AutomationEventTypeID(Enum):
    """Type IDs for device-to-driver payloads."""

    HELLO = 'h'
    RESULT = 'r'
    LOG_ENTRIES = 'l'
    SCREENSHOT = 's'
    GAP = 'g'
    CHUNK = 'c'


class AutomationEvent(IOMultiType[AutomationEventTypeID]):
    """Something the device is telling a driver."""

    @override
    @classmethod
    def get_type_id(cls) -> AutomationEventTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: AutomationEventTypeID) -> type[AutomationEvent]:
        out: type[AutomationEvent]
        if type_id is AutomationEventTypeID.HELLO:
            out = HelloEvent
        elif type_id is AutomationEventTypeID.RESULT:
            out = ResultEvent
        elif type_id is AutomationEventTypeID.LOG_ENTRIES:
            out = LogEntriesEvent
        elif type_id is AutomationEventTypeID.SCREENSHOT:
            out = ScreenshotEvent
        elif type_id is AutomationEventTypeID.GAP:
            out = GapEvent
        elif type_id is AutomationEventTypeID.CHUNK:
            out = ChunkEvent
        else:
            raise ValueError(f'Unrecognized type-id {type_id}.')
        return out


@ioprepped
@dataclass
class HelloEvent(AutomationEvent):
    """Who the driver has reached.

    Sent as the device's first message on every attach, so a driver
    that reconnects (or attaches to a channel it found in a log line
    minutes ago) can confirm what it is actually driving before
    sending anything.
    """

    #: Engine build number, so a driver can gate on capabilities.
    build_number: Annotated[int, IOAttrs('b')]

    #: Platform string as the engine reports it ('mac', 'android'...).
    platform: Annotated[str, IOAttrs('p')]

    #: The app instance this channel belongs to. Changes mean the app
    #: restarted and this is a different run.
    app_instance_id: Annotated[str, IOAttrs('i')]

    #: Whether UI-driving helpers are available (a gui build with the
    #: widget layer up), so a driver can fail loudly rather than
    #: waiting on a press that can never land.
    gui: Annotated[bool, IOAttrs('g')] = False

    @override
    @classmethod
    def get_type_id(cls) -> AutomationEventTypeID:
        return AutomationEventTypeID.HELLO


@ioprepped
@dataclass
class ResultEvent(AutomationEvent):
    """The structured form of an ``[automation]`` result line.

    Same three fields the ``[automation]`` log line has always carried
    (tag / status / payload), so driver-side habits and helpers
    transfer; this just delivers them over the wire instead of
    requiring somebody to be tailing the device's log.
    """

    tag: Annotated[str, IOAttrs('t')]
    status: Annotated[str, IOAttrs('s')]
    payload: Annotated[str, IOAttrs('p')] = ''

    @override
    @classmethod
    def get_type_id(cls) -> AutomationEventTypeID:
        return AutomationEventTypeID.RESULT


@ioprepped
@dataclass
class LogEntriesEvent(AutomationEvent):
    """A slice of the device's log.

    Structured entries rather than rendered text, matching the
    console channel: whoever displays them decides how.
    """

    entries: Annotated[list[LogEntry], IOAttrs('e')] = field(
        default_factory=list
    )

    @override
    @classmethod
    def get_type_id(cls) -> AutomationEventTypeID:
        return AutomationEventTypeID.LOG_ENTRIES


class ImageFormat(Enum):
    """Encoding of a delivered image."""

    JPEG = 'j'
    PNG = 'p'


@ioprepped
@dataclass
class ScreenshotEvent(AutomationEvent):
    """A captured frame, in answer to a :class:`ScreenshotCommand`."""

    tag: Annotated[str, IOAttrs('t')]

    #: The encoded image, base64. Base64 rather than raw bytes
    #: because the channel's frames are JSON text; it costs about a
    #: third in size, which is affordable precisely because captures
    #: default to JPEG.
    data: Annotated[str, IOAttrs('d')]

    image_format: Annotated[ImageFormat, IOAttrs('f')] = ImageFormat.JPEG

    #: Pixel dimensions of the capture. Note these are physical
    #: pixels, so a retina device reports twice its logical size.
    width: Annotated[int, IOAttrs('w')] = 0
    height: Annotated[int, IOAttrs('h')] = 0

    #: Virtual-screen size — the coordinate space synthesized input
    #: (``babase._automation.click_at()`` etc.) works in. Zero if the
    #: device could not supply mapping info (e.g. headless or a
    #: zero-size window).
    virtual_width: Annotated[float, IOAttrs('vw')] = 0.0
    virtual_height: Annotated[float, IOAttrs('vh')] = 0.0

    #: Where the game content sits within the image, as top-left-origin
    #: fractions [0..1] of the image (the rest is tv-border / aspect
    #: black bars). With this and the virtual size, an image pixel
    #: ``(px, py)`` maps to a virtual coord (bottom-left origin, y-up)::
    #:
    #:     vx = virtual_width  * ((px / width  - content_l) / content_w)
    #:     vy = virtual_height * (1 - (py / height - content_t) / content_h)
    #:
    #: Defaults describe the whole image as content (no borders).
    content_l: Annotated[float, IOAttrs('cl')] = 0.0
    content_t: Annotated[float, IOAttrs('ct')] = 0.0
    content_w: Annotated[float, IOAttrs('cw')] = 1.0
    content_h: Annotated[float, IOAttrs('ch')] = 1.0

    @override
    @classmethod
    def get_type_id(cls) -> AutomationEventTypeID:
        return AutomationEventTypeID.SCREENSHOT


@ioprepped
@dataclass
class GapEvent(AutomationEvent):
    """Log lines the driver will never see.

    The device's archive is bounded and it skips entries rather than
    letting a slow reader back up the channel -- loss is expressed
    here, in the application, so the channel itself stays gapless.
    """

    dropped: Annotated[int, IOAttrs('d')]

    @override
    @classmethod
    def get_type_id(cls) -> AutomationEventTypeID:
        return AutomationEventTypeID.GAP


@ioprepped
@dataclass
class ChunkEvent(AutomationEvent):
    """One ordered slice of an event too large for a single message.

    The transport caps a single message on purpose (see
    ``efro.smartsocket.MAX_MESSAGE_BYTES``), and exceeding it does not
    fail cleanly -- the relay retains and retries a message the far
    socket refuses. An event past the cap is therefore split here,
    above the transport, and rejoined by the driver before it decodes
    anything. A lossless screenshot is the case that motivated this;
    the mechanism is type-agnostic.

    No correlation id and no total-length field: the channel delivers
    gaplessly and in order, and the device handles one command at a
    time, so "collect until ``index == count - 1``" cannot interleave
    with another chunk sequence. Log traffic is never chunked -- it
    sheds as a :class:`GapEvent` instead -- so nothing else can start
    one either.

    ``data`` is a slice of the *serialized* event, not a serialized
    slice, so rejoining is string concatenation and the result decodes
    exactly as it would have unsplit.
    """

    #: Position of this slice, from zero.
    index: Annotated[int, IOAttrs('i')]

    #: How many slices the whole event was split into.
    count: Annotated[int, IOAttrs('n')]

    #: This slice of the serialized event.
    data: Annotated[str, IOAttrs('d')]

    @override
    @classmethod
    def get_type_id(cls) -> AutomationEventTypeID:
        return AutomationEventTypeID.CHUNK
