# Released under the MIT License. See LICENSE for details.
#
"""Version 1 doc-ui types."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

import bacommon.displayitem as ditm
import bacommon.clienteffect as clfx
from bacommon.docui._docui import (
    DocUIRequest,
    DocUIRequestTypeID,
    DocUIResponse,
    DocUIResponseTypeID,
)


class RequestMethod(Enum):
    """Typeof of requests that can be made to doc-ui servers."""

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
class Request(DocUIRequest):
    """Full request to doc-ui."""

    path: Annotated[str, IOAttrs('p')]
    method: Annotated[
        RequestMethod,
        IOAttrs('m', store_default=False, enum_fallback=RequestMethod.UNKNOWN),
    ] = RequestMethod.GET
    args: Annotated[dict, IOAttrs('r', store_default=False)] = field(
        default_factory=dict
    )

    @override
    @classmethod
    def get_type_id(cls) -> DocUIRequestTypeID:
        return DocUIRequestTypeID.V1


class ActionTypeID(Enum):
    """Type ID for each of our subclasses."""

    BROWSE = 'b'
    REPLACE = 'r'
    LOCAL = 'l'
    UNKNOWN = 'u'


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
        if type_id is t.UNKNOWN:
            return UnknownAction

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Action:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownAction()


@ioprepped
@dataclass
class UnknownAction(Action):
    """Action type we don't recognize."""

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.UNKNOWN


@ioprepped
@dataclass
class Browse(Action):
    """Browse to a new page in a new window."""

    request: Annotated[Request, IOAttrs('r')]

    #: Plays a swish.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True

    #: Client-effects to run immediately when the button is pressed.
    #:
    #: :meta private:
    immediate_client_effects: Annotated[
        list[clfx.Effect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    #: Local action to run immediately when the button is pressed. Will
    #: be handled by
    #: :meth:`bauiv1lib.docui.DocUIController.local_action()`.
    immediate_local_action: Annotated[
        str | None, IOAttrs('a', store_default=False)
    ] = None
    immediate_local_action_args: Annotated[
        dict | None, IOAttrs('aa', store_default=False)
    ] = None

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
    #:
    #: :meta private:
    immediate_client_effects: Annotated[
        list[clfx.Effect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    #: Local action to run immediately when the button is pressed. Will
    #: be handled by
    #: :meth:`bauiv1lib.docui.DocUIController.local_action()`.
    immediate_local_action: Annotated[
        str | None, IOAttrs('a', store_default=False)
    ] = None
    immediate_local_action_args: Annotated[
        dict | None, IOAttrs('aa', store_default=False)
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
    #:
    #: :meta private:
    immediate_client_effects: Annotated[
        list[clfx.Effect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    #: Local action to run immediately when the button is pressed. Will
    #: be handled by
    #: :meth:`bauiv1lib.docui.DocUIController.local_action()`.
    immediate_local_action: Annotated[
        str | None, IOAttrs('a', store_default=False)
    ] = None
    immediate_local_action_args: Annotated[
        dict | None, IOAttrs('aa', store_default=False)
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
    DISPLAY_ITEM = 'd'


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
        if type_id is t.DISPLAY_ITEM:
            return DisplayItem

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

    #: Note that doc-ui accepts only raw :class:`str` values for text;
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
        tuple[float, float, float, float] | None,
        IOAttrs('c', store_default=False),
    ] = None
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


class DisplayItemStyle(Enum):
    """Styles a display-item can be drawn in."""

    #: Shows graphics and/or text fully conveying what the item is. Fits
    #: in to a 4:3 box and works best with large-ish displays.
    FULL = 'f'

    #: Graphics and/or text fully conveying what the item is, but
    #: condensed to fit in a 2:1 box displayed at small sizes.
    COMPACT = 'c'

    #: A graphics-only representation of the item (though text may be
    #: used in fallback cases). Does not fully convey what the item is,
    #: but instead is intended to be used alongside the item's textual
    #: description. For example, some number of coins may simply display
    #: a coin graphic here without the number. Draws in a 1:1 box and
    #: works for large or small display.
    ICON = 'i'


@ioprepped
@dataclass
class DisplayItem(Decoration):
    """DisplayItem decoration."""

    wrapper: Annotated[ditm.Wrapper, IOAttrs('w')]
    position: Annotated[tuple[float, float], IOAttrs('p')]
    size: Annotated[tuple[float, float], IOAttrs('s')]
    style: Annotated[DisplayItemStyle, IOAttrs('t', store_default=False)] = (
        DisplayItemStyle.FULL
    )
    text_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('c', store_default=False)
    ] = None
    highlight: Annotated[bool, IOAttrs('h', store_default=False)] = True
    depth_range: Annotated[tuple[float, float] | None, IOAttrs('z')] = None
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.DISPLAY_ITEM


class ButtonStyle(Enum):
    """Styles a button can be."""

    SQUARE = 'q'
    TAB = 't'
    SMALL = 's'
    MEDIUM = 'm'
    LARGE = 'l'
    LARGER = 'xl'
    BACK = 'b'
    BACK_SMALL = 'bs'
    SQUARE_WIDE = 'w'


@ioprepped
@dataclass
class Button:
    """A button in our doc-ui.

    Note that size, padding, and all decorations are scaled consistently
    with 'scale'.
    """

    #: Note that doc-ui accepts only raw :class:`str` values for text;
    #: use :meth:`babase.Lstr.evaluate()` or whatnot for multi-language
    #: support.
    label: Annotated[str | None, IOAttrs('l', store_default=False)] = None

    action: Annotated[Action | None, IOAttrs('a', store_default=False)] = None

    size: Annotated[
        tuple[float, float] | None, IOAttrs('sz', store_default=False)
    ] = None
    color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('cl', store_default=False),
    ] = None
    label_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('lc', store_default=False),
    ] = None
    label_flatness: Annotated[
        float | None, IOAttrs('lf', store_default=False)
    ] = None
    label_scale: Annotated[float | None, IOAttrs('ls', store_default=False)] = (
        None
    )
    label_is_lstr: Annotated[bool, IOAttrs('ll', store_default=False)] = False
    texture: Annotated[str | None, IOAttrs('tex', store_default=False)] = None
    scale: Annotated[float, IOAttrs('sc', store_default=False)] = 1.0
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 0.0
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 0.0
    decorations: Annotated[
        list[Decoration] | None, IOAttrs('c', store_default=False)
    ] = None
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
    depth_range: Annotated[
        tuple[float, float] | None, IOAttrs('z', store_default=None)
    ] = None

    #: Custom widget id. Will be prefixed with window id, but must be
    #: unique within the window.
    widget_id: Annotated[str | None, IOAttrs('i', store_default=False)] = None

    #: Draw bounds of the button.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


class RowTypeID(Enum):
    """Type ID for each of our subclasses."""

    BUTTON_ROW = 'b'
    UNKNOWN = 'u'


class Row(IOMultiType[RowTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: RowTypeID) -> type[Row]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = RowTypeID
        if type_id is t.UNKNOWN:
            return UnknownRow
        if type_id is t.BUTTON_ROW:
            return ButtonRow

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Row:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownRow()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownRow(Row):
    """A row type we don't have."""

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.UNKNOWN


@ioprepped
@dataclass
class ButtonRow(Row):
    """A row consisting of buttons."""

    buttons: Annotated[list[Button], IOAttrs('b')]

    header_height: Annotated[float, IOAttrs('h', store_default=False)] = 0.0
    header_scale: Annotated[float, IOAttrs('hs', store_default=False)] = 1.0
    header_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('hdl', store_default=False)
    ] = None
    header_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('hdc', store_default=False)
    ] = None
    header_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('hdr', store_default=False)
    ] = None

    #: Note that doc-ui accepts only raw :class:`str` values for text;
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

    #: Spacing between all buttons in the row.
    button_spacing: Annotated[float, IOAttrs('bs', store_default=False)] = 15.0

    #: Padding on the left of the row's horizonally-scrollable area.
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 10.0
    #: Padding on the right of the row's horizonally-scrollable area.
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 10.0
    #: Padding on the top of the row's horizonally-scrollable area.
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 10.0
    #: Padding on the bottom of the row's horizonally-scrollable area.
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 10.0

    #: Extra space above the row's horizontally-scrollable area.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0

    #: Extra space below the row's horizontally-scrollable area.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

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

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.BUTTON_ROW


@ioprepped
@dataclass
class Page:
    """Doc-UI page version 1."""

    #: Note that doc-ui accepts only raw :class:`str` values for text;
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
    #: doc-ui translation should be handled server-side, but this can
    #: allow client-side translation.
    title_is_lstr: Annotated[bool, IOAttrs('tl', store_default=False)] = False

    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 0.0
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 0.0
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0


class ResponseStatus(Enum):
    """The overall result of a request."""

    SUCCESS = 0

    #: Something went wrong. That's all we know.
    UNKNOWN_ERROR = 1

    #: Something went wrong talking to the server. A 'Retry' button may
    #: be appropriate to show here (for GET requests at least).
    COMMUNICATION_ERROR = 2

    #: This requires the user to be signed in, and they aint.
    NOT_SIGNED_IN_ERROR = 3


@ioprepped
@dataclass
class Response(DocUIResponse):
    """Full docui response."""

    page: Annotated[Page, IOAttrs('p')]
    status: Annotated[ResponseStatus, IOAttrs('s', store_default=False)] = (
        ResponseStatus.SUCCESS
    )

    #: Effects to run on the client when this response is initially
    #: received. Note that these effects will not re-run if the page is
    #: automatically refreshed later (due to window resizing, back
    #: navigation, etc).
    #:
    #: :meta private:
    client_effects: Annotated[
        list[clfx.Effect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    #: Local action to run after this response is initially received.
    #: Will be handled by
    #: :meth:`bauiv1lib.docui.DocUIController.local_action()`. Note that
    #: these actions will not re-run if the page is automatically
    #: refreshed later (due to window resizing, back navigation, etc).
    local_action: Annotated[str | None, IOAttrs('a', store_default=False)] = (
        None
    )
    local_action_args: Annotated[
        dict | None, IOAttrs('aa', store_default=False)
    ] = None

    #: New overall action to have the client schedule after this
    #: response is received. Useful for redirecting to other pages or
    #: closing the doc-ui window.
    timed_action: Annotated[
        Action | None, IOAttrs('ta', store_default=False)
    ] = None
    timed_action_delay: Annotated[
        float, IOAttrs('tad', store_default=False)
    ] = 0.0

    #: If provided, error on builds older than this (can be used to gate
    #: functionality without bumping entire docui version).
    minimum_engine_build: Annotated[
        int | None, IOAttrs('b', store_default=False)
    ] = None

    #: The client maintains some persistent state (such as widget
    #: selection) for all pages viewed. The default index for these
    #: states is the path of the request. If a server returns a
    #: significant variety of responses for a single path, however,
    #: (based on args, etc) then it may make sense for the server to
    #: provide explicit state ids for those different variations.
    shared_state_id: Annotated[
        str | None, IOAttrs('t', store_default=False)
    ] = None

    @override
    @classmethod
    def get_type_id(cls) -> DocUIResponseTypeID:
        return DocUIResponseTypeID.V1
