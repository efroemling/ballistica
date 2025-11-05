# Released under the MIT License. See LICENSE for details.
#
"""Full UIs defined in the cloud - similar to a basic form of html"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.bs import ClientEffect
from bacommon.cloudui._cloudui import (
    CloudUIRequest,
    CloudUIRequestTypeID,
    CloudUIResponse,
    CloudUIResponseTypeID,
)


class RequestMethod(Enum):
    """Typeof of requests that can be made to cloud-ui servers."""

    #: An unknown request method. This can appear if a newer client is
    #: requesting some method from an older server that is not known to
    #: the server.
    UNKNOWN = 'u'

    #: Fetch some resource. This can be retried and its results can
    #: optionally be cached for some amount of time.
    GET = 'g'

    #: Change some resource. This cannot be implicitly retried (at least
    #: without deduplication), nor can it be cached.
    POST = 'p'


@ioprepped
@dataclass
class Request(CloudUIRequest):
    """Full request to cloud-ui."""

    path: Annotated[str, IOAttrs('p')]
    method: Annotated[
        RequestMethod,
        IOAttrs('m', store_default=False, enum_fallback=RequestMethod.UNKNOWN),
    ] = RequestMethod.GET
    params: Annotated[dict, IOAttrs('r', store_default=False)] = field(
        default_factory=dict
    )

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIRequestTypeID:
        return CloudUIRequestTypeID.V1


class ActionTypeID(Enum):
    """Type ID for each of our subclasses."""

    BROWSE = 'b'
    REPLACE = 'r'
    LOCAL = 'l'


class Action(IOMultiType[ActionTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ActionTypeID) -> type[Action]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = ActionTypeID
        if type_id is t.BROWSE:
            return Browse
        if type_id is t.REPLACE:
            return Replace
        if type_id is t.LOCAL:
            return Local

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class Browse(Action):
    """Browse to a new page in a new window."""

    request: Annotated[Request, IOAttrs('r')]

    #: Plays a swish.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True
    immediate_effects: Annotated[
        list[ClientEffect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.BROWSE


@ioprepped
@dataclass
class Replace(Action):
    """Replace current page with a new one.

    Should be used to effectively 'modify' existing UIs by replacing
    them with something slightly different. Things like scroll position
    and selection will be carried across to the new layout when possible
    to make for a seamless transition.
    """

    request: Annotated[Request, IOAttrs('r')]

    #: Plays a click if triggered by a button press.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True

    #: Client-effects to run immediately when the button is pressed.
    immediate_client_effects: Annotated[
        list[ClientEffect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    #: Local action to run immediately when the button is pressed. Will
    #: be handled by
    #: :meth:`bauiv1lib.cloudui.CloudUIController.local_action()`.
    immediate_local_action: Annotated[
        str | None, IOAttrs('a', store_default=False)
    ] = None
    immediate_local_action_params: Annotated[
        dict | None, IOAttrs('ap', store_default=False)
    ] = None

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.REPLACE


@ioprepped
@dataclass
class Local(Action):
    """Perform only local actions; no new requests or page changes."""

    close_window: Annotated[bool, IOAttrs('c', store_default=False)] = False

    #: Plays a swish if closing the window or a click if triggered by a
    #: button press.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True

    #: Client-effects to run immediately when the button is pressed.
    immediate_client_effects: Annotated[
        list[ClientEffect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    #: Local action to run immediately when the button is pressed. Will
    #: be handled by
    #: :meth:`bauiv1lib.cloudui.CloudUIController.local_action()`.
    immediate_local_action: Annotated[
        str | None, IOAttrs('a', store_default=False)
    ] = None
    immediate_local_action_params: Annotated[
        dict | None, IOAttrs('ap', store_default=False)
    ] = None

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.LOCAL


class HAlign(Enum):
    """Horizontal alignment."""

    LEFT = 'l'
    CENTER = 'c'
    RIGHT = 'r'


class VAlign(Enum):
    """Vertical alignment."""

    TOP = 't'
    CENTER = 'c'
    BOTTOM = 'b'


class DecorationTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TEXT = 't'
    IMAGE = 'i'


class Decoration(IOMultiType[DecorationTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: DecorationTypeID) -> type[Decoration]:
        # pylint: disable=cyclic-import

        t = DecorationTypeID
        if type_id is t.UNKNOWN:
            return UnknownDecoration
        if type_id is t.TEXT:
            return Text
        if type_id is t.IMAGE:
            return Image

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Decoration:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownDecoration()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownDecoration(Decoration):
    """An unknown decoration.

    In practice these should never show up since the master-server
    generates these on the fly for the client and so should not send
    clients one they can't digest.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.UNKNOWN


@ioprepped
@dataclass
class Text(Decoration):
    """Text decoration."""

    #: Note that cloud-ui accepts only raw :class:`str` values for text;
    #: use :meth:`babase.Lstr.evaluate()` or whatnot for multi-language
    #: support.
    text: Annotated[str, IOAttrs('t')]
    position: Annotated[tuple[float, float], IOAttrs('p')]

    #: Note that this effectively is max-width and max-height.
    size: Annotated[tuple[float, float], IOAttrs('i')]
    scale: Annotated[float, IOAttrs('s', store_default=False)] = 1.0
    h_align: Annotated[HAlign, IOAttrs('ha', store_default=False)] = (
        HAlign.CENTER
    )
    v_align: Annotated[VAlign, IOAttrs('va', store_default=False)] = (
        VAlign.CENTER
    )
    color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('c', store_default=False),
    ] = None
    flatness: Annotated[float | None, IOAttrs('f', store_default=False)] = None
    shadow: Annotated[float | None, IOAttrs('sh', store_default=False)] = None

    is_lstr: Annotated[bool, IOAttrs('l', store_default=False)] = False

    highlight: Annotated[bool, IOAttrs('h', store_default=False)] = True
    depth_range: Annotated[tuple[float, float] | None, IOAttrs('z')] = None

    #: Show max-width/height bounds; useful during development.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.TEXT


@ioprepped
@dataclass
class Image(Decoration):
    """Image decoration."""

    texture: Annotated[str, IOAttrs('t')]
    position: Annotated[tuple[float, float], IOAttrs('p')]
    size: Annotated[tuple[float, float], IOAttrs('s')]
    color: Annotated[
        tuple[float, float, float] | None, IOAttrs('c', store_default=False)
    ] = None
    opacity: Annotated[float | None, IOAttrs('o', store_default=False)] = None
    h_align: Annotated[HAlign, IOAttrs('ha', store_default=False)] = (
        HAlign.CENTER
    )
    v_align: Annotated[VAlign, IOAttrs('va', store_default=False)] = (
        VAlign.CENTER
    )
    tint_texture: Annotated[str | None, IOAttrs('tt', store_default=False)] = (
        None
    )
    tint_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc1', store_default=False)
    ] = None
    tint2_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc2', store_default=False)
    ] = None
    mask_texture: Annotated[str | None, IOAttrs('mt', store_default=False)] = (
        None
    )
    mesh_opaque: Annotated[str | None, IOAttrs('mo', store_default=False)] = (
        None
    )
    mesh_transparent: Annotated[
        str | None, IOAttrs('mn', store_default=False)
    ] = None
    highlight: Annotated[bool, IOAttrs('h', store_default=False)] = True
    depth_range: Annotated[tuple[float, float] | None, IOAttrs('z')] = None

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.IMAGE


class ButtonStyle(Enum):
    """Styles a button can be."""

    SQUARE = 'q'
    TAB = 't'
    SMALL = 's'
    MEDIUM = 'm'
    LARGE = 'l'
    LARGER = 'xl'


@ioprepped
@dataclass
class Button:
    """A button in our cloud ui.

    Note that size, padding, and all decorations are scaled consistently
    with 'scale'.
    """

    #: Note that cloud-ui accepts only raw :class:`str` values for text;
    #: use :meth:`babase.Lstr.evaluate()` or whatnot for multi-language
    #: support.
    label: Annotated[str | None, IOAttrs('l', store_default=False)] = None

    action: Annotated[Action | None, IOAttrs('a', store_default=False)] = None

    size: Annotated[
        tuple[float, float] | None, IOAttrs('sz', store_default=False)
    ] = None
    color: Annotated[
        tuple[float, float, float] | None, IOAttrs('cl', store_default=False)
    ] = None
    opacity: Annotated[float | None, IOAttrs('o', store_default=False)] = None
    text_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('tc', store_default=False),
    ] = None
    text_flatness: Annotated[
        float | None, IOAttrs('tf', store_default=False)
    ] = None
    text_scale: Annotated[float | None, IOAttrs('ts', store_default=False)] = (
        None
    )
    texture: Annotated[str | None, IOAttrs('tex', store_default=False)] = None
    scale: Annotated[float, IOAttrs('sc', store_default=False)] = 1.0
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 0.0
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 0.0
    decorations: Annotated[
        list[Decoration], IOAttrs('c', store_default=False)
    ] = field(default_factory=list)
    text_is_lstr: Annotated[bool, IOAttrs('tl', store_default=False)] = False
    style: Annotated[ButtonStyle, IOAttrs('y', store_default=False)] = (
        ButtonStyle.SQUARE
    )
    default: Annotated[bool, IOAttrs('df', store_default=False)] = False
    selected: Annotated[bool, IOAttrs('sel', store_default=False)] = False

    icon: Annotated[str | None, IOAttrs('icn', store_default=False)] = None
    icon_scale: Annotated[float | None, IOAttrs('is', store_default=False)] = (
        None
    )
    icon_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('ic', store_default=False),
    ] = None
    depth_range: Annotated[tuple[float, float] | None, IOAttrs('z')] = None

    #: Draw bounds of the button.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


@ioprepped
@dataclass
class Row:
    """A row in our cloud ui."""

    buttons: Annotated[list[Button], IOAttrs('b')]
    #: Note that cloud-ui accepts only raw :class:`str` values for text;
    #: use :meth:`babase.Lstr.evaluate()` or whatnot for multi-language
    #: support.
    title: Annotated[str | None, IOAttrs('t', store_default=False)] = None
    title_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('tc', store_default=False),
    ] = None
    title_flatness: Annotated[
        float | None, IOAttrs('tf', store_default=False)
    ] = None
    title_shadow: Annotated[
        float | None, IOAttrs('ts', store_default=False)
    ] = None
    title_is_lstr: Annotated[bool, IOAttrs('tl', store_default=False)] = False
    subtitle: Annotated[str | None, IOAttrs('s', store_default=False)] = None
    subtitle_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('sc', store_default=False),
    ] = None
    subtitle_flatness: Annotated[
        float | None, IOAttrs('sf', store_default=False)
    ] = None
    subtitle_shadow: Annotated[
        float | None, IOAttrs('ss', store_default=False)
    ] = None
    subtitle_is_lstr: Annotated[bool, IOAttrs('sl', store_default=False)] = (
        False
    )
    button_spacing: Annotated[float, IOAttrs('bs', store_default=False)] = 5.0
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 10.0
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 10.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 10.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 10.0
    center_content: Annotated[bool, IOAttrs('c', store_default=False)] = False
    center_title: Annotated[bool, IOAttrs('ct', store_default=False)] = False

    #: If things disappear when scrolling left/right, turn this up.
    simple_culling_h: Annotated[float, IOAttrs('sch', store_default=False)] = (
        100.0
    )

    #: Draw bounds of the overall row and individual button columns
    #: (including padding). The UI will scroll to keep these areas
    #: visible in their entirety when changing selection via directional
    #: controls, so try to make sure all decorations for a button are
    #: within these bounds.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


@ioprepped
@dataclass
class Page:
    """Cloud-UI page version 1."""

    #: Note that cloud-ui accepts only raw :class:`str` values for text;
    #: use :meth:`babase.Lstr.evaluate()` or whatnot for multi-language
    #: support.
    title: Annotated[str, IOAttrs('t')]
    rows: Annotated[list[Row], IOAttrs('r')]

    #: If True, content smaller than the available height will be
    #: centered vertically. This can look natural for certain types of
    #: content such as confirmation dialogs.
    center_vertically: Annotated[bool, IOAttrs('cv', store_default=False)] = (
        False
    )

    row_spacing: Annotated[float, IOAttrs('s', store_default=False)] = 10.0

    #: If things disappear when scrolling up and down, turn this up.
    simple_culling_v: Annotated[float, IOAttrs('scv', store_default=False)] = (
        100.0
    )

    #: Whether the title is a json dict representing an Lstr. Generally
    #: cloud-ui translation should be handled server-side, but this can
    #: allow client-side translation.
    title_is_lstr: Annotated[bool, IOAttrs('tl', store_default=False)] = False


class StatusCode(Enum):
    """The overall result of a request."""

    SUCCESS = 0
    UNKNOWN_ERROR = 1


@ioprepped
@dataclass
class Response(CloudUIResponse):
    """Full cloudui response."""

    page: Annotated[Page, IOAttrs('p')]
    status: Annotated[StatusCode, IOAttrs('s', store_default=False)] = (
        StatusCode.SUCCESS
    )

    #: Effects to run on the client when this response is initially
    #: received. Note that these effects will not re-run if the page is
    #: automatically refreshed later (due to window resizing, back
    #: navigation, etc).
    client_effects: Annotated[
        list[ClientEffect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    #: Local action to run after this response is initially received.
    #: Will be handled by
    #: :meth:`bauiv1lib.cloudui.CloudUIController.local_action()`. Note
    #: that these actions will not re-run if the page is automatically
    #: refreshed later (due to window resizing, back navigation, etc).
    local_action: Annotated[str | None, IOAttrs('a', store_default=False)] = (
        None
    )
    local_action_params: Annotated[
        dict | None, IOAttrs('ap', store_default=False)
    ] = None

    #: New overall action to have the client schedule after this response
    #: is received. Useful for redirecting to other pages or closing the
    #: cloud-ui window.
    timed_action: Annotated[
        Action | None, IOAttrs('ta', store_default=False)
    ] = None
    timed_action_delay: Annotated[
        float, IOAttrs('tad', store_default=False)
    ] = 0.0

    #: If provided, error on builds older than this (can be used to gate
    #: functionality without bumping entire cloudui version).
    minimum_engine_build: Annotated[
        int | None, IOAttrs('b', store_default=False)
    ] = None

    #: The client maintains some persistent state (such as widget
    #: selection) for all pages viewed. The default index for these
    #: states is the path of the request. If a server returns a
    #: significant variety of responses for a single path, however,
    #: (based on params, etc) then it may make sense for the server to
    #: provide explicit state ids for those different variations.
    shared_state_id: Annotated[
        str | None, IOAttrs('t', store_default=False)
    ] = None

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIResponseTypeID:
        return CloudUIResponseTypeID.V1
