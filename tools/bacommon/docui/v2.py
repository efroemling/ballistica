# Released under the MIT License. See LICENSE for details.
#
"""Version 2 doc-ui types -- language-agnostic (l-string) text.

Where v1 carries pre-localized raw ``str`` text (optionally a JSON-encoded
legacy ``babase.Lstr`` via ``*_is_lstr`` flags) and expects the *server* to
localize, v2 text is always a language-agnostic
:class:`~bacommon.langstr.LangStrSpec`. The server ships one response to every
client regardless of language; the client resolves the referenced
asset-packages in its own locale and decodes the strings at render time.

See ``docs/initiatives/docui-v2-lstrings.md`` (ballistica-internal). This is
the milestone-1 slice: a minimal but real subset of the v1 element set, with
text typed as ``LangStrSpec`` (the name-based form -- subs are flat for now).
Non-text fields mirror v1's names/keys so client render code can stay close
to ``v1prep``.
"""

# This is the doc-ui v2 wire format in its entirety, and it being one
# module is a feature: it is the spec that anyone producing or
# consuming doc-ui reads. Its types also refer to each other in both
# directions (rows hold actions; the row multitype hands back its row
# classes), so splitting it means either a module-level import cycle or
# scattering the public names across modules. So allow it to run long.
# pylint: disable=too-many-lines

from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

import bacommon.clienteffect as clfx
import bacommon.depiction
from bacommon.langstr import LangStrSpec
from bacommon.assetspec import TextureSpec, MeshSpec
from bacommon.assetpackage import ApverNum
from bacommon.docui._docui import (
    DocUIRequest,
    DocUIRequestTypeID,
    DocUIResponse,
    DocUIResponseTypeID,
)

if TYPE_CHECKING:
    from typing import Iterator, TypeIs


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

    #: Current state of the page this request was fired from (see
    #: :attr:`Page.state`), if it had any. Clients fill this in; page
    #: authors never set it directly.
    state: Annotated[dict | None, IOAttrs('s', store_default=False)] = None

    #: State key of the input whose value change fired this request,
    #: if that is what fired it.
    trigger: Annotated[str | None, IOAttrs('t', store_default=False)] = None

    @override
    @classmethod
    def get_type_id(cls) -> DocUIRequestTypeID:
        return DocUIRequestTypeID.V2


class ActionTypeID(Enum):
    """Type ID for each of our subclasses."""

    BROWSE = 'b'
    REPLACE = 'r'
    LOCAL = 'l'
    MENU = 'm'
    POPUP_TEXT = 'pt'
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
        if type_id is t.MENU:
            return Menu
        if type_id is t.POPUP_TEXT:
            return PopupText
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


class WindowLayout(Enum):
    """The overall shape of a doc-ui window.

    Chosen by whatever opens the window (see :attr:`Browse.layout`),
    since the window exists before its page arrives; pages replacing
    each other within a window share its layout. The client owns each
    layout's actual geometry per ui-scale.
    """

    #: A narrower, shorter window for simple list-style pages (settings
    #: and the like). At small ui-scale, where windows fill the screen,
    #: content is instead laid out in a centered column of limited
    #: width.
    SMALL = 's'

    #: A small layout's width, with a height between a small and a
    #: small-taller layout's. The same as a small layout at small
    #: ui-scale.
    SMALL_TALL = 'st'

    #: A small layout's width, but taller; for long list-style pages
    #: (options pages and the like). The same as a small layout at
    #: small ui-scale.
    SMALL_TALLER = 'str'

    #: A squat window for horizontally laid out content designed to
    #: fill the screen elegantly (a row of big buttons, say). Its pages
    #: get the same width and height at every ui-scale -- small
    #: ui-scale's on the narrowest screen -- so content sized to fit
    #: never scrolls and leaves little empty backing. Fills the screen
    #: at small ui-scale (full width, unlike a small layout).
    WIDE = 'w'

    #: A wide layout's height, but wider at medium/large ui-scale; for
    #: content expected to be wider than the screen (a long row of
    #: items, say), where showing as much as possible means less
    #: scrolling. The same as a wide layout at small ui-scale.
    WIDER = 'wr'

    #: The standard full-size window.
    LARGE = 'l'

    #: A small layout's column at the right of a full-size window, the
    #: rest to its left reserved for a viewer pane (a live character
    #: view, say).
    VIEWER = 'v'


@ioprepped
@dataclass
class Browse(Action):
    """Browse to a new page in a new window."""

    request: Annotated[Request, IOAttrs('r')]

    #: Plays a swish.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True

    #: Values to assign into the page's state before the request goes
    #: out (see :attr:`Page.state`).
    sets: Annotated[dict | None, IOAttrs('ss', store_default=False)] = None

    #: A complete state to send *instead of* the page's own; for
    #: handing state to a different page.
    state: Annotated[dict | None, IOAttrs('st', store_default=False)] = None

    #: The new window's layout. Note that the wire default is LARGE
    #: (an omitted value has always meant LARGE, and must keep doing
    #: so for older clients and servers), but routes' own default is
    #: WIDE (see :meth:`bacommon.docui.routes.DocUIRoute.browse`).
    layout: Annotated[
        WindowLayout,
        IOAttrs('lo', store_default=False, enum_fallback=WindowLayout.LARGE),
    ] = WindowLayout.LARGE

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

    #: Values to assign into the page's state before the request goes
    #: out (see :attr:`Page.state`).
    sets: Annotated[dict | None, IOAttrs('ss', store_default=False)] = None

    #: A complete state to send *instead of* the page's own; for
    #: handing state to a different page.
    state: Annotated[dict | None, IOAttrs('st', store_default=False)] = None

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

    #: Client-effects to run immediately when the button is pressed.
    #: Use the v2 effect forms (language-string text, asset-package
    #: sounds); the response's package manifest covers what they
    #: reference.
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

    #: Values to assign into the page's state (see :attr:`Page.state`).
    sets: Annotated[dict | None, IOAttrs('ss', store_default=False)] = None

    #: With :attr:`close_window`, values to assign into the state of the
    #: page being returned to, which then refreshes with them; how a
    #: picker opened in a window of its own hands back what was picked.
    #: Carries the state's type id (``_t``), and is applied only if the
    #: returned-to page's state is of that type. Build it with
    #: :meth:`bacommon.docui.routes.DocUIState.assign_on_return`.
    return_sets: Annotated[dict | None, IOAttrs('rs', store_default=False)] = (
        None
    )

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.LOCAL


@ioprepped
@dataclass
class MenuItem:
    """One entry in a :class:`Menu`."""

    label: Annotated[LangStrSpec | int, IOAttrs('l')]

    #: What picking this item does; anything a button's action can be
    #: except another :class:`Menu` (menus don't nest). The menu makes
    #: its own sound when something is picked, so the action's
    #: ``default_sound`` is not played.
    action: Annotated[Action | None, IOAttrs('a', store_default=False)] = None

    #: Shown in the menu but greyed out and not pickable.
    disabled: Annotated[bool, IOAttrs('d', store_default=False)] = False


@ioprepped
@dataclass
class Menu(Action):
    """Pop up a menu of items at the button; picking one runs its action.

    For buttons offering several things to do (a '...' button, say).
    Picking a *value* is a :class:`ChoiceRow`'s job instead. The button
    is drawn like any other; its label or icon is what says it opens
    a menu.

    Only buttons can open menus; one arriving anywhere else an action
    can go (an input row's ``on_change``, a timed action, a menu item)
    is ignored. Clients predating this type see an unknown action.
    """

    items: Annotated[list[MenuItem], IOAttrs('i')]

    #: Plays a swish.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.MENU


@ioprepped
@dataclass
class PopupText(Action):
    """Pop up a bit of text at the button, with an ok button to close it.

    For informational text (a small '?' button explaining something,
    say). The popup is sized to fit the text, which wraps to a
    client-chosen maximum width. A press of its ok button or anywhere
    outside it closes it.

    Like a :class:`Menu`, only a press can open one: a button's, or a
    menu item's (the popup then comes from the menu's button). One
    arriving anywhere else an action can go (an input row's
    ``on_change``, a timed action) is ignored. Clients predating this
    type see an unknown action.
    """

    text: Annotated[LangStrSpec | int, IOAttrs('t')]

    #: Plays a swish.
    default_sound: Annotated[bool, IOAttrs('ds', store_default=False)] = True

    @override
    @classmethod
    def get_type_id(cls) -> ActionTypeID:
        return ActionTypeID.POPUP_TEXT


class HAlign(Enum):
    """Horizontal alignment.

    Fields of this type carry an ``enum_fallback`` (each field's own
    default; ``LEFT`` for the optional row alignments), so a value
    added here later decodes as that on builds predating it instead
    of failing the whole response.
    """

    LEFT = 'l'
    CENTER = 'c'
    RIGHT = 'r'


class VAlign(Enum):
    """Vertical alignment.

    Fields of this type carry an ``enum_fallback`` (``CENTER``), so a
    value added here later decodes as that on builds predating it
    instead of failing the whole response.
    """

    TOP = 't'
    CENTER = 'c'
    BOTTOM = 'b'


class DecorationTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TEXT = 't'
    IMAGE = 'i'
    DEPICTION = 'd'


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
        if type_id is t.DEPICTION:
            return Depiction
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
class TextImage:
    """An image fixed to one end of a :class:`Text` decoration.

    For things like a price: a count with its currency icon beside it,
    measured, fitted, and aligned as one unit. The producer cannot do
    that itself because it cannot know the text's rendered width; the
    client measures it while laying out the text.

    Sizes and offsets are in *text units* -- they are multiplied by the
    text's effective scale -- so the image grows and shrinks with its
    text. The image's layout box (its size less its :attr:`insets`)
    sits butted against its end of the text and vertically centered on
    the line; spacing from the text therefore comes from the insets,
    not from anything the producer adds.

    Meant for single-line text; on multi-line text the images center
    against the whole block.
    """

    #: The image's texture. An ``int`` is the indexed form; see
    #: :attr:`Image.texture`.
    texture: Annotated[TextureSpec | int, IOAttrs('t')]

    #: Size in text units.
    size: Annotated[tuple[float, float], IOAttrs('s')]

    #: A purely visual shift in text units, positive being right/up. It
    #: moves where the image draws and nothing else, like CSS relative
    #: positioning; measuring, fitting, and alignment ignore it. For
    #: small optical corrections -- spacing belongs in :attr:`insets`.
    offset: Annotated[
        tuple[float, float], IOAttrs('o', store_default=False)
    ] = (
        0.0,
        0.0,
    )

    #: Color and opacity. Deliberately separate from the text's color:
    #: a coin should not turn green because its count is.
    color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('c', store_default=False),
    ] = None

    #: The image's layout box, as fractions of its size trimmed from
    #: each edge, in (left, bottom, right, top) order. Layout uses only
    #: this box -- for butting against the text, centering on the line,
    #: and measuring the unit -- while the full image still draws.
    #: Typically trims most of the art's transparent padding, leaving in
    #: whatever spacing the art wants beside text -- the way a font
    #: glyph carries its own side bearings. A negative inset extends the
    #: box past the image instead (like a CSS margin), for art with less
    #: padding than the spacing it wants. Fractions rather than units
    #: because this is a fact of the art, true at any size.
    insets: Annotated[
        tuple[float, float, float, float],
        IOAttrs('i', store_default=False),
    ] = (0.0, 0.0, 0.0, 0.0)


@ioprepped
@dataclass
class Text(Decoration):
    """Text decoration.

    ``text`` is a language-agnostic :class:`~bacommon.langstr.LangStrSpec`.

    With :attr:`image_left` or :attr:`image_right` set, the text and its
    images are measured, shrunk to fit :attr:`size` (never grown), and
    aligned as a single unit.
    """

    #: The text. An ``int`` is the indexed form -- a flat index
    #: into the string domain of :attr:`Response.packages` (see
    #: ``bacommon.langstr._flatindex``); the client unfolds it
    #: into the two-integer form the native decoder consumes while
    #: resolving. Strings carrying substitutions never fold.
    text: Annotated[LangStrSpec | int, IOAttrs('t')]
    position: Annotated[tuple[float, float], IOAttrs('p')]

    #: Effectively max-width and max-height.
    size: Annotated[tuple[float, float], IOAttrs('i')]

    scale: Annotated[float, IOAttrs('s', store_default=False)] = 1.0
    h_align: Annotated[
        HAlign, IOAttrs('ha', store_default=False, enum_fallback=HAlign.CENTER)
    ] = HAlign.CENTER
    v_align: Annotated[
        VAlign, IOAttrs('va', store_default=False, enum_fallback=VAlign.CENTER)
    ] = VAlign.CENTER
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

    #: An image fixed to the left end of the text.
    image_left: Annotated[
        TextImage | None, IOAttrs('il', store_default=False)
    ] = None

    #: An image fixed to the right end of the text.
    image_right: Annotated[
        TextImage | None, IOAttrs('ir', store_default=False)
    ] = None

    #: Lets client-effects animate this decoration (see
    #: ``bacommon.clienteffect.KeyframeAnimation``). Everything in
    #: a page sharing an id animates together.
    anim_id: Annotated[str | None, IOAttrs('ai', store_default=False)] = None

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.TEXT


@ioprepped
@dataclass
class ImageNinePatch:
    """Draws an :class:`Image` as a 9-patch filling its box exactly.

    The texture splits into corners, edges and a middle; corners keep
    their drawn size, edges and middle fill what's between. Tint and
    mask textures share the texture's layout.
    """

    #: Where the texture splits, as fractions of its width/height from
    #: the left, bottom, right and top. 0.5 on each side of an axis
    #: makes that axis's middle a single texel line.
    insets: Annotated[tuple[float, float, float, float], IOAttrs('i')]

    #: How big those edges draw, in the image's own units (as its
    #: ``size``), same order. A pair too big for the box shrinks to fit.
    borders: Annotated[tuple[float, float, float, float], IOAttrs('b')]

    #: Repeat the horizontal (``tile_h``) or vertical (``tile_v``) middle
    #: at the corners' scale -- fitted to a whole number of copies --
    #: rather than stretching it. Its art must tile seamlessly.
    tile_h: Annotated[bool, IOAttrs('th', store_default=False)] = False
    tile_v: Annotated[bool, IOAttrs('tv', store_default=False)] = False


@ioprepped
@dataclass
class Image(Decoration):
    """Image decoration. Textures/meshes are language-independent refs.

    Unlike text, image assets need no per-locale decode; each ref
    (:class:`~bacommon.assetspec.TextureSpec` /
    :class:`~bacommon.assetspec.MeshSpec`) is resolved by the client and
    rendered directly.
    """

    #: The image's texture. An ``int`` is the indexed form -- a flat
    #: index into the textures domain of :attr:`Response.packages` (see
    #: ``bacommon.assetspec._index``); the client swaps it for a
    #: :class:`~bacommon.assetspec.TextureSpec` while resolving, so
    #: everything downstream of resolve sees only specs. Old clients are
    #: served the spec form.
    texture: Annotated[TextureSpec | int, IOAttrs('t')]
    position: Annotated[tuple[float, float], IOAttrs('p')]
    size: Annotated[tuple[float, float], IOAttrs('s')]
    color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('c', store_default=False),
    ] = None
    h_align: Annotated[
        HAlign, IOAttrs('ha', store_default=False, enum_fallback=HAlign.CENTER)
    ] = HAlign.CENTER
    v_align: Annotated[
        VAlign, IOAttrs('va', store_default=False, enum_fallback=VAlign.CENTER)
    ] = VAlign.CENTER
    tint_texture: Annotated[
        TextureSpec | int | None, IOAttrs('tt', store_default=False)
    ] = None
    tint_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc1', store_default=False)
    ] = None
    tint2_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc2', store_default=False)
    ] = None
    mask_texture: Annotated[
        TextureSpec | int | None, IOAttrs('mt', store_default=False)
    ] = None
    mesh_opaque: Annotated[
        MeshSpec | int | None, IOAttrs('mo', store_default=False)
    ] = None
    mesh_transparent: Annotated[
        MeshSpec | int | None, IOAttrs('mn', store_default=False)
    ] = None
    highlight: Annotated[bool, IOAttrs('h', store_default=False)] = True
    depth_range: Annotated[tuple[float, float] | None, IOAttrs('z')] = None

    #: Tint through the tint texture's blue channel (as
    #: :attr:`tint_color` is red and :attr:`tint2_color` green). Clients
    #: before this field ignore it.
    tint3_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc3', store_default=False)
    ] = None

    #: Draw as a 9-patch (see :class:`ImageNinePatch`). Clients before
    #: this field ignore it and stretch the whole texture over the box.
    nine_patch: Annotated[
        ImageNinePatch | None, IOAttrs('np', store_default=False)
    ] = None

    #: Show this image's bounds; useful during development. Worth
    #: having separately from the art because a texture with a
    #: transparent margin gives no clue where its box really is.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    #: Lets client-effects animate this decoration (see
    #: ``bacommon.clienteffect.KeyframeAnimation``). Everything in
    #: a page sharing an id animates together.
    anim_id: Annotated[str | None, IOAttrs('ai', store_default=False)] = None

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.IMAGE


@ioprepped
@dataclass
class Depiction(Decoration):
    """A :class:`bacommon.depiction.Depiction`, drawn in a box.

    ``position`` is the box's center and ``size`` its size. A depiction
    with a shape of its own (a square icon, an image's aspect) is fitted
    inside the box and placed by ``h_align``/``v_align``; one without
    (a name) fills the box.

    Depictions are self-sufficient: whatever packages one references
    contribute **nothing** to the page's own :attr:`Response.packages`.
    Art that isn't local yet shows as a standin, never a blocked page.
    """

    depiction: Annotated[bacommon.depiction.Depiction, IOAttrs('dp')]
    position: Annotated[tuple[float, float], IOAttrs('p')]
    size: Annotated[tuple[float, float], IOAttrs('s')]
    h_align: Annotated[
        HAlign, IOAttrs('ha', store_default=False, enum_fallback=HAlign.CENTER)
    ] = HAlign.CENTER
    v_align: Annotated[
        VAlign, IOAttrs('va', store_default=False, enum_fallback=VAlign.CENTER)
    ] = VAlign.CENTER

    #: Whether to follow the button this decorates -- brightening as
    #: it's hovered, pressed, or selected, and drawing faded and greyed
    #: while it's disabled.
    highlight: Annotated[bool, IOAttrs('h', store_default=False)] = True
    depth_range: Annotated[tuple[float, float] | None, IOAttrs('z')] = None
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    #: Lets client-effects animate this decoration (see
    #: ``bacommon.clienteffect.KeyframeAnimation``). Everything in
    #: a page sharing an id animates together.
    anim_id: Annotated[str | None, IOAttrs('ai', store_default=False)] = None

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.DEPICTION


class ButtonStyle(Enum):
    """Styles a button can be.

    :attr:`Button.style` carries an ``enum_fallback`` (``SQUARE``), so
    a style added here later draws as a square button on builds
    predating it instead of failing the whole response.
    """

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

    ``label`` is a language-agnostic :class:`~bacommon.langstr.LangStrSpec`.
    Size, padding, and all decorations scale consistently with ``scale``.
    """

    label: Annotated[
        LangStrSpec | int | None, IOAttrs('l', store_default=False)
    ] = None

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
    label_flatness: Annotated[
        float | None, IOAttrs('lf', store_default=False)
    ] = None
    texture: Annotated[
        TextureSpec | int | None, IOAttrs('tex', store_default=False)
    ] = None
    scale: Annotated[float, IOAttrs('sc', store_default=False)] = 1.0
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 0.0
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 0.0
    decorations: Annotated[
        list[Decoration] | None, IOAttrs('c', store_default=False)
    ] = None
    style: Annotated[
        ButtonStyle,
        IOAttrs('y', store_default=False, enum_fallback=ButtonStyle.SQUARE),
    ] = ButtonStyle.SQUARE
    default: Annotated[bool, IOAttrs('df', store_default=False)] = False
    selected: Annotated[bool, IOAttrs('sel', store_default=False)] = False

    #: Drawn greyed out and not activatable (a press plays an error
    #: sound instead of running ``action``). Still selectable, so
    #: navigation around it is unaffected. Clients predating this field
    #: show it as a normal button.
    disabled: Annotated[bool, IOAttrs('dis', store_default=False)] = False

    icon: Annotated[
        TextureSpec | int | None, IOAttrs('icn', store_default=False)
    ] = None
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

    #: A depiction drawn as the button's body, in place of its texture
    #: or style's look, filling the button's box (its size, at its
    #: scale). One with a shape of its own is fitted inside the box by
    #: :attr:`depiction_h_align` / :attr:`depiction_v_align`. The label,
    #: icon and decorations still draw over it, and it brightens,
    #: pulses and greys out with the button. To show a depiction
    #: elsewhere on a button, use a :class:`Depiction` decoration.
    #: Clients predating this field show the button's usual look.
    depiction: Annotated[
        bacommon.depiction.Depiction | None,
        IOAttrs('dp', store_default=False),
    ] = None
    depiction_h_align: Annotated[
        HAlign, IOAttrs('dha', store_default=False, enum_fallback=HAlign.CENTER)
    ] = HAlign.CENTER
    depiction_v_align: Annotated[
        VAlign, IOAttrs('dva', store_default=False, enum_fallback=VAlign.CENTER)
    ] = VAlign.CENTER

    #: With a :attr:`depiction`, have mouse and touch land on the
    #: button only where the depiction actually draws (an icon hugging
    #: one end of a wide button, a short name in a box sized for long
    #: ones) rather than anywhere in its box. The client grows that area
    #: to a minimum size so small depictions stay easy to tap; keyboard
    #: and controller selection are unaffected. Clients predating this
    #: field take presses anywhere in the box.
    depiction_hit_area: Annotated[
        bool, IOAttrs('dhit', store_default=False)
    ] = False

    #: Custom widget id. Prefixed with the window id; unique within window.
    widget_id: Annotated[str | None, IOAttrs('i', store_default=False)] = None

    #: Lets client-effects animate this button (see
    #: ``bacommon.clienteffect.KeyframeAnimation``); give its
    #: decorations the same id to have them move with it.
    anim_id: Annotated[str | None, IOAttrs('ai', store_default=False)] = None

    #: Draw bounds of the button.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False


class RowTypeID(Enum):
    """Type ID for each of our subclasses."""

    BUTTON_ROW = 'b'
    CHECKBOX_ROW = 'c'
    TEXT_INPUT_ROW = 't'
    CHOICE_ROW = 'h'
    COLOR_ROW = 'k'
    SLIDER_ROW = 's'
    NUMBER_ROW = 'n'
    BUTTON_CONTROL_ROW = 'bc'
    SECTION = 'sc'
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
        rowtype: type[Row]
        match type_id:
            case t.UNKNOWN:
                rowtype = UnknownRow
            case t.BUTTON_ROW:
                rowtype = ButtonRow
            case t.CHECKBOX_ROW:
                rowtype = CheckboxRow
            case t.TEXT_INPUT_ROW:
                rowtype = TextInputRow
            case t.CHOICE_ROW:
                rowtype = ChoiceRow
            case t.COLOR_ROW:
                rowtype = ColorRow
            case t.SLIDER_ROW:
                rowtype = SliderRow
            case t.NUMBER_ROW:
                rowtype = NumberRow
            case t.BUTTON_CONTROL_ROW:
                rowtype = ButtonControlRow
            case t.SECTION:
                rowtype = Section
            case _:
                assert_never(type_id)
        return rowtype

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


class ButtonRowLayout(Enum):
    """How a :class:`ButtonRow` handles the row's width.

    :attr:`ButtonRow.layout` carries an ``enum_fallback`` (``SCROLL``),
    so a layout added here later scrolls on builds predating it
    instead of failing the whole response.
    """

    #: Buttons at their own sizes in a strip that scrolls sideways when
    #: they don't all fit. The strip clips what it holds (vertically
    #: too, so a button growing as it's pressed can lose its top and
    #: bottom edges); its scroll bar fades in over the bottom of its
    #: padding.
    SCROLL = 's'

    #: Buttons at their own sizes, placed straight on the page (so
    #: nothing about them is clipped), aligned in the row like a
    #: scrolling row's are. If they don't all fit, they all shrink
    #: together until they do.
    FIXED = 'x'

    #: Buttons sharing the row's full width, spanning exactly what a
    #: control row's contents do (from where control rows' labels start
    #: to where their controls end), so the row lines up with control
    #: rows around it. Each button's width is its share of that, in
    #: proportion to its own ``size`` width (equal sizes for equal
    #: buttons); everything else about each button, height included, is
    #: its own. Like ``FIXED``, placed straight on the page.
    FILL = 'f'


@ioprepped
@dataclass
class ButtonRow(Row):
    """A row consisting of buttons.

    ``title``/``subtitle`` are :class:`~bacommon.langstr.LangStrSpec`.
    How the buttons use the row's width is up to ``layout``.
    """

    buttons: Annotated[list[Button], IOAttrs('b')]

    #: How the buttons use the row's width. Builds older than this field
    #: always scroll.
    layout: Annotated[
        ButtonRowLayout,
        IOAttrs(
            'lo', store_default=False, enum_fallback=ButtonRowLayout.SCROLL
        ),
    ] = ButtonRowLayout.SCROLL

    #: Height of an optional band above the row (above its title too)
    #: holding free-form, non-interactive decorations; 0 for none. Each
    #: of the three decoration lists is positioned relative to a point
    #: on the band's vertical midline -- its left edge (inset like row
    #: titles), its center, and its right edge. Every row type has one.
    header_height: Annotated[float, IOAttrs('h', store_default=False)] = 0.0

    #: Scales the header band's height and everything in it.
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

    #: The header band's mirror image -- the same thing, below the row
    #: (below its footnote too). Every row type has one.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0

    #: Scales the footer band's height and everything in it.
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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

    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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

    #: Small explanatory text drawn below the row's content, aligned
    #: like its title; the row grows to make room for it.
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow; None for the defaults it
    #: shares with the subtitle. Independent of the subtitle's own
    #: overrides.
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: Spacing between all buttons in the row.
    button_spacing: Annotated[float, IOAttrs('bs', store_default=False)] = 15.0

    #: Space around the buttons; None for the layout's default (see
    #: :meth:`get_padding`). Left/right are from the column's edges
    #: (``SCROLL`` and ``FIXED``) or from where control rows' contents
    #: start/end (``FILL``).
    padding_left: Annotated[
        float | None, IOAttrs('pl', store_default=False)
    ] = None
    padding_right: Annotated[
        float | None, IOAttrs('pr', store_default=False)
    ] = None
    padding_top: Annotated[float | None, IOAttrs('pt', store_default=False)] = (
        None
    )
    padding_bottom: Annotated[
        float | None, IOAttrs('pb', store_default=False)
    ] = None

    #: Extra space above the whole row (outside its header and title).
    #: May be negative to pull rows together. Every row type has one.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0

    #: Extra space below the whole row (outside its footnote and
    #: footer). Every row type has one.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    #: Extra space between the title/subtitle and the row's content
    #: (no effect without either). Titles normally hug their content;
    #: pushing one away makes it read as a heading for a group of rows
    #: rather than a label for this one. Builds older than this field
    #: ignore it. Every row type has one.
    spacing_title: Annotated[float, IOAttrs('stl', store_default=False)] = 0.0

    #: Extra space between the row's content and its footnote (no
    #: effect without one); the footnote's counterpart to
    #: :attr:`spacing_title`. Builds older than this field ignore it.
    #: Every row type has one.
    spacing_footnote: Annotated[float, IOAttrs('sfn', store_default=False)] = (
        0.0
    )

    center_content: Annotated[bool, IOAttrs('c', store_default=False)] = False
    center_title: Annotated[bool, IOAttrs('ct', store_default=False)] = False

    #: Horizontal alignment of buttons when they don't fill the row's
    #: width (a ``SCROLL`` row with more than that simply scrolls; a
    #: ``FIXED`` one shrinks to fit; ``FILL`` rows always fill it).
    #: Overrides ``center_content`` when set. Builds older than this
    #: field ignore it (and thus left-align unless ``center_content`` is
    #: also set).
    content_align: Annotated[
        HAlign | None,
        IOAttrs('ca', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: Shifts a ``FIXED`` row's buttons sideways as a group (positive
    #: is right). They lay out exactly as they otherwise would -- same
    #: order, spacing and shrink-to-fit -- and then the whole group
    #: moves this far, but never past the row's edges (it slides back
    #: in instead). Centered content thus centers on the row's center
    #: plus this offset: the same point header and footer decorations
    #: at that x are placed from, which is the way to line a button up
    #: with band art regardless of the layout's width or insets.
    #: Ignored by ``SCROLL`` and ``FILL`` rows. Builds older than this
    #: field ignore it.
    content_offset: Annotated[float, IOAttrs('cxo', store_default=False)] = 0.0

    #: Horizontal alignment of the title and subtitle. Overrides
    #: ``center_title`` when set; same older-build caveat as
    #: ``content_align``.
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: If things disappear when scrolling left/right, turn this up
    #: (``SCROLL`` only).
    simple_culling_h: Annotated[float, IOAttrs('sch', store_default=False)] = (
        100.0
    )

    #: Whether the row's horizontal scroll bar is drawn (and grabbable
    #: by the mouse). Off, the row still scrolls every other way (drag,
    #: wheel, keys, page buttons) and keeps the same layout; only the
    #: bar goes. Builds older than this field always show it.
    #: (``SCROLL`` only.)
    show_scrollbar: Annotated[bool, IOAttrs('ssb', store_default=False)] = True

    #: Draw bounds of the row and its button columns.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    def get_padding(self) -> tuple[float, float, float, float]:
        """Our (left, right, top, bottom) padding, defaults applied.

        A scrolling row's bottom default leaves room for the strip its
        scroll bar fades in over; the others need none.
        """
        left, right, top, bottom = self._default_padding(self.layout)
        return (
            left if self.padding_left is None else self.padding_left,
            right if self.padding_right is None else self.padding_right,
            top if self.padding_top is None else self.padding_top,
            bottom if self.padding_bottom is None else self.padding_bottom,
        )

    @staticmethod
    def _default_padding(
        layout: ButtonRowLayout,
    ) -> tuple[float, float, float, float]:
        match layout:
            case ButtonRowLayout.SCROLL:
                # (The room below is the strip the bar fades in over.)
                return 10.0, 10.0, 4.0, 16.0
            case ButtonRowLayout.FIXED:
                return 10.0, 10.0, 4.0, 4.0
            case ButtonRowLayout.FILL:
                return 0.0, 0.0, 4.0, 4.0
            case _:
                assert_never(layout)

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.BUTTON_ROW


@ioprepped
@dataclass
class CheckboxRow(Row):
    """A row consisting of a single checkbox.

    Label at the left edge of the row; box at the right. Its value
    lives in the page's state (see :attr:`Page.state`) under ``name``,
    which must not start with an underscore and must hold a bool.
    """

    #: Key in the page's state holding our value.
    name: Annotated[str, IOAttrs('n')]

    label: Annotated[
        LangStrSpec | int | None, IOAttrs('l', store_default=False)
    ] = None

    #: Fired when the value changes, after the new value has been
    #: written to the page's state. Without one, a changed value simply
    #: goes out with whatever request the page fires next. Actions
    #: opening new windows are not allowed here.
    on_change: Annotated[Action | None, IOAttrs('oc', store_default=False)] = (
        None
    )

    #: Shown dimmed and not toggleable (a press plays an error sound).
    #: Still selectable, so navigation around it is unaffected. Clients
    #: predating this field show it as a normal row.
    disabled: Annotated[bool, IOAttrs('dis', store_default=False)] = False

    #: Section title shown above the row (with an optional subtitle),
    #: styled and placed exactly as a :class:`ButtonRow`'s.
    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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
    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: Small explanatory text drawn below the row's content, aligned
    #: like its title; the row grows to make room for it.
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow; None for the defaults it
    #: shares with the subtitle. Independent of the subtitle's own
    #: overrides.
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: Extra inset for the label, which otherwise starts where row
    #: titles do.
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0

    #: Extra inset for the box, which otherwise ends where the last
    #: button of a right-aligned row does.
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 4.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 4.0

    #: See :attr:`ButtonRow.header_height`.
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

    #: See :attr:`ButtonRow.footer_height`.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.spacing_top`.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_bottom`.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_title`.
    spacing_title: Annotated[float, IOAttrs('stl', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_footnote`.
    spacing_footnote: Annotated[float, IOAttrs('sfn', store_default=False)] = (
        0.0
    )

    #: Draw bounds of the row.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.CHECKBOX_ROW


@ioprepped
@dataclass
class TextInputRow(Row):
    """A row consisting of a single editable line of text.

    Label at the left edge of the row, taking up to half of its width
    (and squished to fit if it wants more); the editable text gets the
    rest. Its value lives in the page's state (see :attr:`Page.state`)
    under ``name``, which must not start with an underscore and must
    hold a str.
    """

    #: Key in the page's state holding our value.
    name: Annotated[str, IOAttrs('n')]

    label: Annotated[
        LangStrSpec | int | None, IOAttrs('l', store_default=False)
    ] = None

    #: What is being edited, for places that ask for text by way of a
    #: separate dialog (on-screen keyboards and such). The label gets
    #: used when this is not provided.
    description: Annotated[
        LangStrSpec | int | None, IOAttrs('ds', store_default=False)
    ] = None

    max_chars: Annotated[int, IOAttrs('mc', store_default=False)] = 64

    #: Fired when an edit is applied (a text-entry dialog closing with
    #: a value, inline editing ending, the clear button; NOT per
    #: character) with a changed value, after that value has been
    #: written to the page's state. Without one, a changed value simply
    #: goes out with whatever request the page fires next. Actions
    #: opening new windows are not allowed here.
    on_change: Annotated[Action | None, IOAttrs('oc', store_default=False)] = (
        None
    )

    #: Fired when the user submits the field (return/enter while
    #: editing inline, or a text-entry dialog's submit), after the value
    #: has been applied to the page's state. For forms where typing and
    #: hitting return should do what the page's main button does. Any
    #: action is allowed.
    on_submit: Annotated[Action | None, IOAttrs('os', store_default=False)] = (
        None
    )

    #: Shown dimmed and not editable. Still selectable, so navigation
    #: around it is unaffected. Clients predating this field show it as
    #: a normal editable row.
    disabled: Annotated[bool, IOAttrs('dis', store_default=False)] = False

    #: Section title shown above the row (with an optional subtitle),
    #: styled and placed exactly as a :class:`ButtonRow`'s.
    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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
    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: Small explanatory text drawn below the row's content, aligned
    #: like its title; the row grows to make room for it.
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow; None for the defaults it
    #: shares with the subtitle. Independent of the subtitle's own
    #: overrides.
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: Extra inset for the label, which otherwise starts where row
    #: titles do.
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0

    #: Extra inset for the text box, which otherwise ends where the
    #: last button of a right-aligned row does.
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 4.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 4.0

    #: See :attr:`ButtonRow.header_height`.
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

    #: See :attr:`ButtonRow.footer_height`.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.spacing_top`.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_bottom`.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_title`.
    spacing_title: Annotated[float, IOAttrs('stl', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_footnote`.
    spacing_footnote: Annotated[float, IOAttrs('sfn', store_default=False)] = (
        0.0
    )

    #: Draw bounds of the row.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.TEXT_INPUT_ROW


@ioprepped
@dataclass
class Choice:
    """One option in a :class:`ChoiceRow`."""

    #: The value stored in the page's state when this is chosen. None
    #: is a legitimate choice value (an optional's 'nothing' option) --
    #: it lands in state as a null, distinct from the key being absent.
    value: Annotated[str | None, IOAttrs('v')]

    label: Annotated[LangStrSpec | int, IOAttrs('l')]

    #: Shown in the menu but greyed out and not pickable (an option this
    #: device can't use, say). Clients predating this field show it as
    #: a normal choice.
    disabled: Annotated[bool, IOAttrs('d', store_default=False)] = False


@ioprepped
@dataclass
class ChoiceRow(Row):
    """A row consisting of a single pick-one-of-these control.

    Label at the left edge of the row; a popup-menu button showing the
    current choice at the right. Its value lives in the page's state
    (see :attr:`Page.state`) under ``name``, which must not start with
    an underscore and must hold the ``value`` of one of ``choices``.
    """

    #: Key in the page's state holding our value.
    name: Annotated[str, IOAttrs('n')]

    choices: Annotated[list[Choice], IOAttrs('c')]

    label: Annotated[
        LangStrSpec | int | None, IOAttrs('l', store_default=False)
    ] = None

    #: Fired when a choice is picked, after the new value has been
    #: written to the page's state. Without one, a changed value simply
    #: goes out with whatever request the page fires next. Actions
    #: opening new windows are not allowed here.
    on_change: Annotated[Action | None, IOAttrs('oc', store_default=False)] = (
        None
    )

    #: The whole row shown dimmed with its menu unopenable (a press plays
    #: an error sound instead). Still selectable, so navigation around it
    #: is unaffected. Distinct from :attr:`Choice.disabled`, which greys
    #: individual options in a working menu. Clients predating this field
    #: show it as a normal row.
    disabled: Annotated[bool, IOAttrs('dis', store_default=False)] = False

    #: Section title shown above the row (with an optional subtitle),
    #: styled and placed exactly as a :class:`ButtonRow`'s.
    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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
    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: Small explanatory text drawn below the row's content, aligned
    #: like its title; the row grows to make room for it.
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow; None for the defaults it
    #: shares with the subtitle. Independent of the subtitle's own
    #: overrides.
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: Extra inset for the label, which otherwise starts where row
    #: titles do.
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0

    #: Extra inset for the button, which otherwise ends where the last
    #: button of a right-aligned row does.
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 4.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 4.0

    #: See :attr:`ButtonRow.header_height`.
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

    #: See :attr:`ButtonRow.footer_height`.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.spacing_top`.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_bottom`.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_title`.
    spacing_title: Annotated[float, IOAttrs('stl', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_footnote`.
    spacing_footnote: Annotated[float, IOAttrs('sfn', store_default=False)] = (
        0.0
    )

    #: Draw bounds of the row.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.CHOICE_ROW


@ioprepped
@dataclass
class ColorRow(Row):
    """A row consisting of a single color-picking control.

    Label at the left edge of the row; a swatch button showing the
    current color at the right, which opens a color picker. Its value
    lives in the page's state (see :attr:`Page.state`) under ``name``,
    which must not start with an underscore and must hold an
    ``[r, g, b]`` list of floats in the 0-1 range.
    """

    #: Key in the page's state holding our value.
    name: Annotated[str, IOAttrs('n')]

    label: Annotated[
        LangStrSpec | int | None, IOAttrs('l', store_default=False)
    ] = None

    #: Fired when the picker closes with a changed color, after the new
    #: value has been written to the page's state. (Not on every
    #: intermediate change; the exact-color picker streams those.)
    #: Without one, a changed value simply goes out with whatever
    #: request the page fires next. Actions opening new windows are not
    #: allowed here.
    on_change: Annotated[Action | None, IOAttrs('oc', store_default=False)] = (
        None
    )

    #: Shown dimmed (the swatch greyed like any disabled button) with its
    #: picker unopenable (a press plays an error sound). Still
    #: selectable, so navigation around it is unaffected. Clients
    #: predating this field show it as a normal row.
    disabled: Annotated[bool, IOAttrs('dis', store_default=False)] = False

    #: Section title shown above the row (with an optional subtitle),
    #: styled and placed exactly as a :class:`ButtonRow`'s.
    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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
    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: Small explanatory text drawn below the row's content, aligned
    #: like its title; the row grows to make room for it.
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow; None for the defaults it
    #: shares with the subtitle. Independent of the subtitle's own
    #: overrides.
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: Extra inset for the label, which otherwise starts where row
    #: titles do.
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0

    #: Extra inset for the swatch, which otherwise ends where the last
    #: button of a right-aligned row does.
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 4.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 4.0

    #: See :attr:`ButtonRow.header_height`.
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

    #: See :attr:`ButtonRow.footer_height`.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.spacing_top`.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_bottom`.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_title`.
    spacing_title: Annotated[float, IOAttrs('stl', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_footnote`.
    spacing_footnote: Annotated[float, IOAttrs('sfn', store_default=False)] = (
        0.0
    )

    #: Draw bounds of the row.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.COLOR_ROW


@ioprepped
@dataclass
class SliderRow(Row):
    """A row consisting of a single slider control.

    Label at the left (right-aligned toward the control), the current
    value as text, then the slider itself at the row's right. Its value
    lives in the page's state (see :attr:`Page.state`) under ``name``,
    which must not start with an underscore and must hold a float
    between ``min_value`` and ``max_value``.
    """

    #: Key in the page's state holding our value.
    name: Annotated[str, IOAttrs('n')]

    min_value: Annotated[float, IOAttrs('mn')]
    max_value: Annotated[float, IOAttrs('mx')]
    increment: Annotated[float, IOAttrs('i')]

    label: Annotated[
        LangStrSpec | int | None, IOAttrs('l', store_default=False)
    ] = None

    #: Show the value as a whole percentage (``0.5`` -> ``50%``) rather
    #: than to ``decimals`` places.
    as_percent: Annotated[bool, IOAttrs('ap', store_default=False)] = False
    decimals: Annotated[int, IOAttrs('dc', store_default=False)] = 2

    #: Fired when a value is settled on -- the nub released after a
    #: drag, or a run of key/controller steps going quiet (half a
    #: second after the last step, or at once on deselection) -- after
    #: the value has been written to the page's state. Without one, a changed
    #: value simply goes out with whatever request the page fires next.
    #: Actions opening new windows are not allowed here.
    on_change: Annotated[Action | None, IOAttrs('oc', store_default=False)] = (
        None
    )

    #: Fired *while* the nub is being dragged (key/controller steps
    #: count as dragging), at most every
    #: ``drag_interval`` seconds and not before ``drag_delay`` into the
    #: drag, with the page's state already holding the value so far;
    #: also once for the settled value if the drag's last apply missed
    #: it. Local only (typed so): whatever needs to track the value
    #: live -- a volume being set -- happens client side, with no
    #: request until the value settles.
    on_drag: Annotated[Local | None, IOAttrs('od', store_default=False)] = None
    drag_interval: Annotated[float, IOAttrs('di', store_default=False)] = 0.25
    drag_delay: Annotated[float, IOAttrs('dd', store_default=False)] = 0.0

    #: Shown dimmed and not adjustable. Still selectable, so navigation
    #: around it is unaffected. Clients predating this field show it as
    #: a normal adjustable row.
    disabled: Annotated[bool, IOAttrs('dis', store_default=False)] = False

    #: Section title shown above the row (with an optional subtitle),
    #: styled and placed exactly as a :class:`ButtonRow`'s.
    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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
    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: Small explanatory text drawn below the row's content, aligned
    #: like its title; the row grows to make room for it.
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow; None for the defaults it
    #: shares with the subtitle. Independent of the subtitle's own
    #: overrides.
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: Extra inset for the label, which otherwise starts where row
    #: titles do.
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0

    #: Extra inset for the slider, which otherwise ends where the last
    #: button of a right-aligned row does.
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 4.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 4.0

    #: See :attr:`ButtonRow.header_height`.
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

    #: See :attr:`ButtonRow.footer_height`.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.spacing_top`.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_bottom`.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_title`.
    spacing_title: Annotated[float, IOAttrs('stl', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_footnote`.
    spacing_footnote: Annotated[float, IOAttrs('sfn', store_default=False)] = (
        0.0
    )

    #: Draw bounds of the row.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.SLIDER_ROW


@ioprepped
@dataclass
class NumberRow(Row):
    """A row editing a number with a '-' and a '+' button.

    Label at the left, then at the row's right the current value as
    text followed by the two buttons. Each press steps the value by
    ``increment`` within ``min_value``/``max_value`` (holding a button
    repeats). Its value lives in the page's state (see
    :attr:`Page.state`) under ``name``, which must not start with an
    underscore and must hold a float between ``min_value`` and
    ``max_value``.

    For a value with many steps, :class:`SliderRow` is usually the
    better fit; this suits short ranges where each step is a distinct
    setting.
    """

    #: Key in the page's state holding our value.
    name: Annotated[str, IOAttrs('n')]

    min_value: Annotated[float, IOAttrs('mn')]
    max_value: Annotated[float, IOAttrs('mx')]
    increment: Annotated[float, IOAttrs('i')]

    label: Annotated[
        LangStrSpec | int | None, IOAttrs('l', store_default=False)
    ] = None

    #: Show the value as a whole percentage (``0.5`` -> ``50%``) rather
    #: than to ``decimals`` places.
    as_percent: Annotated[bool, IOAttrs('ap', store_default=False)] = False
    decimals: Annotated[int, IOAttrs('dc', store_default=False)] = 0

    #: Fired on each press that changes the value, after it has been
    #: written to the page's state. Without one, a changed value simply
    #: goes out with whatever request the page fires next. Actions
    #: opening new windows are not allowed here.
    on_change: Annotated[Action | None, IOAttrs('oc', store_default=False)] = (
        None
    )

    #: Shown dimmed and not adjustable (both buttons disabled). Still
    #: selectable, so navigation around it is unaffected. Clients
    #: predating this field show it as a normal adjustable row.
    disabled: Annotated[bool, IOAttrs('dis', store_default=False)] = False

    #: Section title shown above the row (with an optional subtitle),
    #: styled and placed exactly as a :class:`ButtonRow`'s.
    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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
    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: Small explanatory text drawn below the row's content, aligned
    #: like its title; the row grows to make room for it.
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow; None for the defaults it
    #: shares with the subtitle. Independent of the subtitle's own
    #: overrides.
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: Extra inset for the label, which otherwise starts where row
    #: titles do.
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0

    #: Extra inset for the '+' button, which otherwise ends where the
    #: last button of a right-aligned row does.
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 4.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 4.0

    #: See :attr:`ButtonRow.header_height`.
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

    #: See :attr:`ButtonRow.footer_height`.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.spacing_top`.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_bottom`.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_title`.
    spacing_title: Annotated[float, IOAttrs('stl', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_footnote`.
    spacing_footnote: Annotated[float, IOAttrs('sfn', store_default=False)] = (
        0.0
    )

    #: Draw bounds of the row.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.NUMBER_ROW


@ioprepped
@dataclass
class ButtonControlRow(Row):
    """A control row whose control is a single button.

    Label at the left edge of the row; ``button`` at the right, drawn
    as it would be in a :class:`ButtonRow`. Laid out like the other
    control rows, so it sits naturally in a column of them, but unlike
    them it holds no value: the button shows whatever the page draws on it
    (an icon or preview of a current selection, say) and does whatever
    its action says (browse to a page for picking a new one, say).

    The button can be any size; the row grows to fit it, its label
    stays centered beside it (squished to fit the space the button
    leaves), and its title and footnote keep clear of it.
    """

    #: The button. Its ``default`` and ``selected`` flags work as they
    #: do in a :class:`ButtonRow`.
    button: Annotated[Button, IOAttrs('b')]

    label: Annotated[
        LangStrSpec | int | None, IOAttrs('l', store_default=False)
    ] = None

    #: The whole row shown dimmed, with its button disabled (as by
    #: :attr:`Button.disabled`, which on its own leaves the label
    #: alone).
    disabled: Annotated[bool, IOAttrs('dis', store_default=False)] = False

    #: Section title shown above the row (with an optional subtitle),
    #: styled and placed exactly as a :class:`ButtonRow`'s.
    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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
    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: Small explanatory text drawn below the row's content, aligned
    #: like its title; the row grows to make room for it.
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow; None for the defaults it
    #: shares with the subtitle. Independent of the subtitle's own
    #: overrides.
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: Extra inset for the label, which otherwise starts where row
    #: titles do.
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0

    #: Extra inset for the button, which otherwise ends where the last
    #: button of a right-aligned row does.
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 4.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 4.0

    #: See :attr:`ButtonRow.header_height`.
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

    #: See :attr:`ButtonRow.footer_height`.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.spacing_top`.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_bottom`.
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_title`.
    spacing_title: Annotated[float, IOAttrs('stl', store_default=False)] = 0.0
    #: See :attr:`ButtonRow.spacing_footnote`.
    spacing_footnote: Annotated[float, IOAttrs('sfn', store_default=False)] = (
        0.0
    )

    #: Draw bounds of the row.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.BUTTON_CONTROL_ROW


@ioprepped
@dataclass
class SectionBacking:
    """A backing for a :class:`Section`, and the layout that goes with it.

    A backed section is a card: a rect of ``max_width`` at most (else
    the column's full width), centered in the column, from the top of
    the section's heading (else its first row) to the bottom of its
    note (else its last row) plus ``padding_top``/``padding_bottom``.
    Its button rows clip at the rect's left and right edges, and its
    content lays out inside it as a page's does in its column: button
    rows' buttons ``content_inset`` in from those edges, text (heading
    and note text, row titles, labels) and control and fill rows a few
    units further in to line up with buttons' visible edges, and
    centered things centered on the card. All of that holds whatever
    width the section gets.

    The rect is drawn as ``texture`` (tinted by ``color``) or, with no
    texture, a flat ``color`` fill; an alpha of 0 draws nothing, which
    leaves just the layout.

    A texture's visible shape usually sits inside soft or shadowed
    margins; the pins say where. ``h_pin`` (left, right) is how far
    in from each side of the image, as a fraction of its width (0 to
    0.5), the shape's edge falls: the image is stretched so those
    points land on the rect's edges. ``v_pin`` (top, bottom) does the
    same vertically. Pins are a property of the texture alone, so one
    calibration holds at every width. They don't apply to flat fills.
    """

    texture: Annotated[
        TextureSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
    color: Annotated[
        tuple[float, float, float, float], IOAttrs('c', store_default=False)
    ] = (1.0, 1.0, 1.0, 1.0)
    h_pin: Annotated[
        tuple[float, float], IOAttrs('hp', store_default=False)
    ] = (0.0, 0.0)
    v_pin: Annotated[
        tuple[float, float], IOAttrs('vp', store_default=False)
    ] = (0.0, 0.0)

    #: Widest the card gets; None to take the column's full width.
    max_width: Annotated[float | None, IOAttrs('mw', store_default=False)] = (
        None
    )

    #: How far in from the card's edges its button rows' buttons sit
    #: (both sides; a page's sit 28 in from its column's).
    content_inset: Annotated[float, IOAttrs('ci', store_default=False)] = 0.0

    #: Room inside the card above its first content and below its last.
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 0.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 0.0


@ioprepped
@dataclass
class Section(Row):
    """A group of rows, with an optional heading, note and backing.

    Its rows lay out exactly as they would directly in the page; the
    section adds around them a heading (header band, title, subtitle)
    above, a note (footnote, footer band) below, and optionally a
    backing (see :class:`SectionBacking`), which turns it into a card
    with a layout of its own. With none of those it just stands its
    rows a little apart from what comes before and after, so the
    grouping reads at a glance.

    The heading is drawn like a row's own titles but a bit larger, so
    it reads as heading the group rather than labeling one row; the
    note likewise. Neither is selectable: selecting the section's first
    selectable row scrolls its heading into view too, and its last its
    note.

    Sections don't nest; a section among a section's rows is ignored
    (the client logs an error). Builds older than this row type skip a
    section entirely, rows included.

    ``title``/``subtitle``/``footnote`` are
    :class:`~bacommon.langstr.LangStrSpec`.
    """

    #: The rows in the section.
    rows: Annotated[list[Row], IOAttrs('r')]

    #: Make the section a card (see :class:`SectionBacking`).
    backing: Annotated[
        SectionBacking | None, IOAttrs('b', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.header_height`.
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

    title: Annotated[
        LangStrSpec | int | None, IOAttrs('t', store_default=False)
    ] = None
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

    subtitle: Annotated[
        LangStrSpec | int | None, IOAttrs('s', store_default=False)
    ] = None
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

    #: See :attr:`ButtonRow.title_align`; the footnote follows it too.
    #: Left by default.
    title_align: Annotated[
        HAlign | None,
        IOAttrs('ta', store_default=False, enum_fallback=HAlign.LEFT),
    ] = None

    #: The note under the section's rows (drawn like a subtitle).
    footnote: Annotated[
        LangStrSpec | int | None, IOAttrs('fn', store_default=False)
    ] = None
    #: The footnote's color/flatness/shadow (drawn like a subtitle).
    footnote_color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('fnc', store_default=False),
    ] = None
    footnote_flatness: Annotated[
        float | None, IOAttrs('fnf', store_default=False)
    ] = None
    footnote_shadow: Annotated[
        float | None, IOAttrs('fns', store_default=False)
    ] = None

    #: See :attr:`ButtonRow.footer_height`.
    footer_height: Annotated[float, IOAttrs('fh', store_default=False)] = 0.0
    footer_scale: Annotated[float, IOAttrs('fs', store_default=False)] = 1.0
    footer_decorations_left: Annotated[
        list[Decoration] | None, IOAttrs('fdl', store_default=False)
    ] = None
    footer_decorations_center: Annotated[
        list[Decoration] | None, IOAttrs('fdc', store_default=False)
    ] = None
    footer_decorations_right: Annotated[
        list[Decoration] | None, IOAttrs('fdr', store_default=False)
    ] = None

    #: Extra space above the section (outside its header band) and
    #: below it (outside its footer band), on top of the standing room
    #: it keeps from its neighbors; either may be negative. See
    #: :attr:`ButtonRow.spacing_top`.
    spacing_top: Annotated[float, IOAttrs('st', store_default=False)] = 0.0
    spacing_bottom: Annotated[float, IOAttrs('sb', store_default=False)] = 0.0

    #: Outline the section's heading and note (as rows' debug does).
    #: Its rows have their own debug flags.
    debug: Annotated[bool, IOAttrs('d', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> RowTypeID:
        return RowTypeID.SECTION


def all_rows(rows: list[Row]) -> Iterator[Row]:
    """Yield rows depth-first: each row, and a section's rows after it.

    For code that visits every row wherever it sits (string and action
    walkers, validation). Sections don't nest, but this simply recurses
    if one does.
    """
    for row in rows:
        yield row
        if isinstance(row, Section):
            yield from all_rows(row.rows)


#: Union of the input-row types: the control rows holding a value,
#: bound to a page-state key (see :attr:`Page.state`).
type AnyInputRow = (
    CheckboxRow | TextInputRow | ChoiceRow | ColorRow | SliderRow | NumberRow
)

#: Union of the control-row types: rows holding a single control,
#: label at the left and control at the right. That is the input rows
#: plus :class:`ButtonControlRow`, which holds no value.
type AnyControlRow = AnyInputRow | ButtonControlRow

_INPUT_ROW_TYPES = (
    CheckboxRow,
    TextInputRow,
    ChoiceRow,
    ColorRow,
    SliderRow,
    NumberRow,
)

_CONTROL_ROW_TYPES = _INPUT_ROW_TYPES + (ButtonControlRow,)


def is_input_row(
    row: Row,
) -> TypeIs[AnyInputRow]:
    """Is this row one of the input-row types (:data:`AnyInputRow`)?

    Everything concerned with the values rows hold keys off this
    rather than listing them; it narrows the type in both branches.
    """
    return isinstance(row, _INPUT_ROW_TYPES)


def is_control_row(
    row: Row,
) -> TypeIs[AnyControlRow]:
    """Is this row one of the control-row types (:data:`AnyControlRow`)?

    Everything that lays control rows out alike keys off this rather
    than listing them; it narrows the type in both branches.
    """
    return isinstance(row, _CONTROL_ROW_TYPES)


@ioprepped
@dataclass
class Page:
    """Doc-UI page version 2.

    ``title`` is a language-agnostic :class:`~bacommon.langstr.LangStrSpec`.
    """

    title: Annotated[LangStrSpec | int, IOAttrs('t')]
    rows: Annotated[list[Row], IOAttrs('r')]

    #: Values belonging to the page as a whole -- what input rows show
    #: and edit, plus anything else the page wants handed back. The
    #: client sends the current values along with every request fired
    #: from the page (see :attr:`Request.state`), and whatever page
    #: comes back replaces them with its own.
    #:
    #: A flat dict of json values. Keys starting with an underscore
    #: are reserved; ``_t`` optionally names the type of state this is
    #: so that state reaching a page expecting some other type can be
    #: recognized as such and ignored.
    state: Annotated[dict | None, IOAttrs('st', store_default=False)] = None

    #: What the window's viewer pane shows, for windows at the
    #: :attr:`WindowLayout.VIEWER` layout (ignored elsewhere): usually a
    #: :class:`bacommon.depiction.CharacterViewerDepiction`. The client
    #: keeps what the pane shows running across pages, so a page re-sent
    #: with a changed depiction (an editor's draft, say) updates the
    #: picture in place. Without one the pane is left blank.
    viewer: Annotated[
        bacommon.depiction.Depiction | None, IOAttrs('v', store_default=False)
    ] = None

    #: Center content vertically when it's smaller than the available height.
    center_vertically: Annotated[bool, IOAttrs('cv', store_default=False)] = (
        False
    )

    #: Whether the page's vertical scroll bar is drawn (and grabbable by
    #: the mouse). Off, the page still scrolls every other way (drag,
    #: wheel, keys) and keeps the same layout; only the bar goes. Builds
    #: older than this field always show it.
    show_scrollbar: Annotated[bool, IOAttrs('ssb', store_default=False)] = True
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

    #: The client is too old for this; it needs an update. Set by a
    #: server declining a request on those grounds, so clients can show
    #: their standard update prompt (and composite pages can say so in
    #: their own words) without reading the page's text.
    #: :attr:`Response.minimum_engine_build` may name the build when
    #: the server knows it.
    NEED_UPDATE_ERROR = 4


@ioprepped
@dataclass
class Response(DocUIResponse):
    """Full docui response (v2)."""

    page: Annotated[Page, IOAttrs('p')]
    #: (A status this build doesn't know decodes as
    #: :attr:`ResponseStatus.UNKNOWN_ERROR`, so statuses can be added
    #: without older clients failing to decode the response. Builds
    #: before 23021 lack this fallback: a server must not send them
    #: :attr:`ResponseStatus.NEED_UPDATE_ERROR` or anything newer.)
    status: Annotated[
        ResponseStatus,
        IOAttrs(
            's',
            store_default=False,
            enum_fallback=ResponseStatus.UNKNOWN_ERROR,
        ),
    ] = ResponseStatus.SUCCESS

    #: The engine build this response was built for, as a sanity check:
    #: responses can be tailored per-build (client-effect forms etc.),
    #: so a consumer seeing a mismatch with its own build should treat
    #: the response as stale (e.g. toss cached data) rather than use it.
    for_build: Annotated[int | None, IOAttrs('fb', store_default=False)] = None

    #: Asset-package-versions the response's integer-indexed
    #: language-strings resolve against (position = package index).
    #: Present only on wire responses finalized to the indexed form by
    #: the server; its presence declares the page + contained client
    #: effects fully indexed (consumers may flag resource-form leaks),
    #: and it doubles as the client's resolve/pre-warm manifest.
    #: Locally-authored responses never carry it (indexing is a wire
    #: compression; local pages stay in the authored resource form).
    packages: Annotated[list[ApverNum], IOAttrs('pk', store_default=False)] = (
        field(default_factory=list)
    )

    #: Digest of the exact asset-index domain the producer indexed
    #: against, from
    #: :meth:`~bacommon.assetspec.AssetIndexContext.domain_digest`. The
    #: two ends build that domain from different sources, and a
    #: disagreement is invisible on its own -- an index that is wrong
    #: but still in range simply names a different asset, so the page
    #: renders with the wrong art and nothing logs. A consumer whose
    #: own digest differs must refuse to de-index rather than trust it;
    #: leaving the integers in place makes the failure loud and names
    #: the packages involved. Set only when asset refs were indexed.
    asset_index_digest: Annotated[
        str | None, IOAttrs('adg', store_default=False)
    ] = None

    #: The same guard for folded language-string references, from
    #: :meth:`~bacommon.langstr.LangStrFlatIndexContext.domain_digest`.
    #: Separate from the asset digest so a mismatch says which of the
    #: two domains drifted. Set only when string refs were folded.
    langstr_index_digest: Annotated[
        str | None, IOAttrs('ldg', store_default=False)
    ] = None

    #: Effects to run on the client when this response is initially
    #: received (not re-run on automatic page refreshes). Use the v2
    #: effect forms (language-string text, asset-package sounds); the
    #: response's package manifest covers what they reference.
    #:
    #: :meta private:
    client_effects: Annotated[
        list[clfx.Effect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)

    #: Local action to run after this response is initially received
    #: (not re-run on automatic page refreshes). Will be handled by
    #: :meth:`bauiv1lib.docui.DocUIController.local_action()`.
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
