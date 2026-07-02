# Released under the MIT License. See LICENSE for details.
#
"""Version 2 doc-ui types -- language-agnostic (l-string) text.

Where v1 carries pre-localized raw ``str`` text (optionally a JSON-encoded
legacy ``babase.Lstr`` via ``*_is_lstr`` flags) and expects the *server* to
localize, v2 text is always a language-agnostic
:class:`~bacommon.langstr.Lstr`. The server ships one response to every
client regardless of language; the client resolves the referenced
asset-packages in its own locale and decodes the strings at render time.

See ``docs/initiatives/docui-v2-lstrings.md`` (ballistica-internal). This is
the milestone-1 slice: a minimal but real subset of the v1 element set, with
text typed as ``Lstr`` (the name-based form -- subs are flat for now).
Non-text fields mirror v1's names/keys so client render code can stay close
to ``v1prep``.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.langstr import Lstr
from bacommon.assetref import TextureRef, MeshRef
from bacommon.docui._docui import (
    DocUIRequest,
    DocUIRequestTypeID,
    DocUIResponse,
    DocUIResponseTypeID,
)


class RequestMethod(Enum):
    """Type of requests that can be made to doc-ui servers."""

    #: An unknown request method (newer client -> older server).
    UNKNOWN = 'u'

    #: Fetch some resource. Retriable; results optionally cacheable.
    GET = 'g'

    #: Change some resource. Not implicitly retriable, not cacheable.
    POST = 'p'


@ioprepped
@dataclass
class Request(DocUIRequest):
    """Full request to doc-ui (v2)."""

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
        return DocUIRequestTypeID.V2


class ActionTypeID(Enum):
    """Type ID for each of our subclasses."""

    BROWSE = 'b'
    REPLACE = 'r'
    LOCAL = 'l'
    UNKNOWN = 'u'


class Action(IOMultiType[ActionTypeID]):
    """Something that happens when a button is pressed."""

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ActionTypeID) -> type[Action]:
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
        assert_never(type_id)

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Action:
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

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.BROWSE


@ioprepped
@dataclass
class Replace(Action):
    """Replace the current page with a new one (seamless transition)."""

    request: Annotated[Request, IOAttrs('r')]

    #: Plays a click if triggered by a button press.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.REPLACE


@ioprepped
@dataclass
class Local(Action):
    """Perform only local actions; no new requests or page changes."""

    close_window: Annotated[bool, IOAttrs('c', store_default=False)] = False

    #: Plays a swish if closing the window, else a click.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True

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
    """Top level class for our decoration multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
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
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Decoration:
        return UnknownDecoration()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownDecoration(Decoration):
    """An unknown decoration (should never reach a client in practice)."""

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.UNKNOWN


@ioprepped
@dataclass
class Text(Decoration):
    """Text decoration. ``text`` is a language-agnostic :class:`Lstr`."""

    text: Annotated[Lstr, IOAttrs('t')]
    position: Annotated[tuple[float, float], IOAttrs('p')]

    #: Effectively max-width and max-height.
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
    """Image decoration. Textures/meshes are language-independent refs.

    Unlike text, image assets need no per-locale decode; each ref
    (:class:`TextureRef` / :class:`MeshRef`) is resolved by the client and
    rendered directly.
    """

    texture: Annotated[TextureRef, IOAttrs('t')]
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
    tint_texture: Annotated[
        TextureRef | None, IOAttrs('tt', store_default=False)
    ] = None
    tint_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc1', store_default=False)
    ] = None
    tint2_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc2', store_default=False)
    ] = None
    mask_texture: Annotated[
        TextureRef | None, IOAttrs('mt', store_default=False)
    ] = None
    mesh_opaque: Annotated[
        MeshRef | None, IOAttrs('mo', store_default=False)
    ] = None
    mesh_transparent: Annotated[
        MeshRef | None, IOAttrs('mn', store_default=False)
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
    BACK = 'b'
    BACK_SMALL = 'bs'
    SQUARE_WIDE = 'w'


@ioprepped
@dataclass
class Button:
    """A button in our doc-ui. ``label`` is a language-agnostic :class:`Lstr`.

    Size, padding, and all decorations scale consistently with ``scale``.
    """

    label: Annotated[Lstr | None, IOAttrs('l', store_default=False)] = None
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
    label_scale: Annotated[float | None, IOAttrs('ls', store_default=False)] = (
        None
    )
    texture: Annotated[
        TextureRef | None, IOAttrs('tex', store_default=False)
    ] = None
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
    depth_range: Annotated[
        tuple[float, float] | None, IOAttrs('z', store_default=None)
    ] = None

    #: Custom widget id. Prefixed with the window id; unique within window.
    widget_id: Annotated[str | None, IOAttrs('i', store_default=False)] = None

    #: Draw bounds of the button.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


class RowTypeID(Enum):
    """Type ID for each of our subclasses."""

    BUTTON_ROW = 'b'
    UNKNOWN = 'u'


class Row(IOMultiType[RowTypeID]):
    """Top level class for our row multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: RowTypeID) -> type[Row]:
        # pylint: disable=cyclic-import
        t = RowTypeID
        if type_id is t.UNKNOWN:
            return UnknownRow
        if type_id is t.BUTTON_ROW:
            return ButtonRow
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Row:
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
    """A row consisting of buttons. ``title``/``subtitle`` are :class:`Lstr`."""

    buttons: Annotated[list[Button], IOAttrs('b')]

    title: Annotated[Lstr | None, IOAttrs('t', store_default=False)] = None
    title_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('tc', store_default=False),
    ] = None
    subtitle: Annotated[Lstr | None, IOAttrs('s', store_default=False)] = None
    subtitle_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('sc', store_default=False),
    ] = None

    #: Spacing between all buttons in the row.
    button_spacing: Annotated[float, IOAttrs('bs', store_default=False)] = 15.0

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

    #: Draw bounds of the row and its button columns.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.BUTTON_ROW


@ioprepped
@dataclass
class Page:
    """Doc-UI page version 2. ``title`` is a language-agnostic :class:`Lstr`."""

    title: Annotated[Lstr, IOAttrs('t')]
    rows: Annotated[list[Row], IOAttrs('r')]

    #: Center content vertically when it's smaller than the available height.
    center_vertically: Annotated[bool, IOAttrs('cv', store_default=False)] = (
        False
    )
    row_spacing: Annotated[float, IOAttrs('s', store_default=False)] = 10.0

    #: If things disappear when scrolling up/down, turn this up.
    simple_culling_v: Annotated[float, IOAttrs('scv', store_default=False)] = (
        100.0
    )

    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 0.0
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 0.0
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0


class ResponseStatus(Enum):
    """The overall result of a request."""

    SUCCESS = 0

    #: Something went wrong. That's all we know.
    UNKNOWN_ERROR = 1

    #: Something went wrong talking to the server. A 'Retry' may be apt.
    COMMUNICATION_ERROR = 2

    #: This requires the user to be signed in, and they aint.
    NOT_SIGNED_IN_ERROR = 3


@ioprepped
@dataclass
class Response(DocUIResponse):
    """Full docui response (v2)."""

    page: Annotated[Page, IOAttrs('p')]
    status: Annotated[ResponseStatus, IOAttrs('s', store_default=False)] = (
        ResponseStatus.SUCCESS
    )

    #: If provided, error on builds older than this.
    minimum_engine_build: Annotated[
        int | None, IOAttrs('b', store_default=False)
    ] = None

    #: Explicit shared-state id (defaults to the request path client-side).
    shared_state_id: Annotated[
        str | None, IOAttrs('ssi', store_default=False)
    ] = None

    @override
    @classmethod
    def get_type_id(cls) -> DocUIResponseTypeID:
        return DocUIResponseTypeID.V2
