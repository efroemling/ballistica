# Released under the MIT License. See LICENSE for details.
#
"""Depictions: self-sufficient things for clients to draw.

A depiction describes something to show -- a character's icon, a
name, a character in 3D, an image -- that a client draws natively
wherever it is hosted: a doc-ui page (see
:class:`bacommon.docui.v2.Depiction`), a page's viewer pane, and later
widgets and in-game nodes. The host decides where and how big; the
depiction decides what is drawn there.

Depictions are **self-sufficient**: each carries whatever package
references it needs, and never adds packages to whatever contains it.
Art that isn't local yet shows as a standin and upgrades in place when
it arrives; the container never waits on it.

A client that doesn't recognize a depiction's kind draws a placeholder
(an outlined box with a question mark) and warns once, since producers
should only send kinds a client understands. Any finer-grained
degradation -- a name drawing plain text when its styling is too new
for the client, say -- is each kind's own business.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.assetpackage import ApverNum
from bacommon.assetspec import CubeMapTextureSpec, MeshSpec, TextureSpec


class DepictionTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    IMAGE = 'i'
    CHARACTER_ICON = 'ci'
    NAME = 'n'
    CHARACTER_VIEWER = 'cv'
    MESH_VIEWER = 'mv'
    BLANK = 'bl'


class Depiction(IOMultiType[DepictionTypeID]):
    """Something for a client to draw; see the module docs.

    Every kind carries an optional ``color_override``: one rgb color
    imposed on the depiction, baked in. It is the static form of the
    color override a host can impose live (a display node's
    ``color_override``, say), and a host's wins where both are set.
    Each kind decides what it applies to (a name's text and whatever
    its capsule routes it to, a character icon's main color); kinds
    with nothing to apply it to ignore it. A player's icon in a teams
    game carries its team's color this way, so it shows in that color
    wherever it is drawn.

    Every kind likewise carries ``team_coloring``: the depiction's main
    color is a team's and should stay its clearly dominant one. Each
    kind decides what that means, toning its other colors down (a
    character icon's highlights; the parts of a name its override isn't
    routed to); kinds with nothing to tone ignore it. The main color is
    the color override if there is one, else whatever the kind takes as
    its own. Hosts can also turn it on live (a display node's
    ``team_coloring``).

    (Both are declared on each kind rather than here, as this base
    holds no fields; they are ``co`` and ``tco`` on the wire for all.)
    """

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: DepictionTypeID) -> type[Depiction]:
        # pylint: disable=too-many-return-statements
        t = DepictionTypeID
        if type_id is t.UNKNOWN:
            return UnknownDepiction
        if type_id is t.IMAGE:
            return ImageDepiction
        if type_id is t.CHARACTER_ICON:
            return CharacterIconDepiction
        if type_id is t.NAME:
            return NameDepiction
        if type_id is t.CHARACTER_VIEWER:
            return CharacterViewerDepiction
        if type_id is t.MESH_VIEWER:
            return MeshViewerDepiction
        if type_id is t.BLANK:
            return BlankDepiction
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Depiction:
        return UnknownDepiction()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownDepiction(Depiction):
    """A depiction of a kind this client doesn't know.

    Drawn as a placeholder (an outlined box with a question mark), with
    a one-time warning.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        return DepictionTypeID.UNKNOWN


@ioprepped
@dataclass
class BlankDepiction(Depiction):
    """Nothing at all: an empty doc-ui viewer pane, say.

    Whatever its host draws around it (a viewer pane's background and
    frame) is what shows. A doc-ui page wanting an empty pane beside
    its rows shows one of these, since a page with no viewer at all
    gets no pane (see :attr:`bacommon.docui.v2.Page.viewer`). Clients
    before :data:`bacommon.docui.v2.PAGE_DRIVEN_VIEWER_BUILD` don't
    know it (see :func:`bacommon.docui.v2.blank_viewer`).
    """

    #: See :class:`Depiction`. (Ignored; there's nothing to color.)
    color_override: Annotated[
        tuple[float, float, float] | None, IOAttrs('co', store_default=False)
    ] = None

    #: See :class:`Depiction`. (Ignored, as above.)
    team_coloring: Annotated[bool, IOAttrs('tco', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        return DepictionTypeID.BLANK


@ioprepped
@dataclass
class ImageDepiction(Depiction):
    """A texture, fetched on demand, optionally masked and tinted.

    For art that must be self-sufficient -- anything whose package the
    page (or other container) should not have to resolve first -- such
    as the main toolbar's chests. Page art that resolves with its page
    is better served by the :class:`bacommon.docui.v2.Image` decoration.

    Texture slots take a full spec or, in the compact wire form, an
    integer index into the index domain laid out over :attr:`packages`
    (as character components do); producers send the compact form,
    with :attr:`domain_digest` guarding the indices.
    """

    texture: Annotated[TextureSpec | int, IOAttrs('t')]

    #: Width over height. Stated here rather than taken from the loaded
    #: texture so the standin shown until the art arrives has the same
    #: shape, and nothing shifts when it does.
    aspect: Annotated[float, IOAttrs('a', store_default=False)] = 1.0

    #: Draws the image this much bigger or smaller about its box's
    #: center, for art with glows or other extras that should spill
    #: past where it is placed. Only the drawing changes: the box (and
    #: so layout and what counts as a press) stays put. Clients clamp
    #: this to 0-2; ones before this field draw at 1.
    scale: Annotated[float, IOAttrs('s', store_default=False)] = 1.0

    color: Annotated[
        tuple[float, float, float, float] | None,
        IOAttrs('c', store_default=False),
    ] = None
    mask_texture: Annotated[
        TextureSpec | int | None, IOAttrs('mt', store_default=False)
    ] = None
    tint_texture: Annotated[
        TextureSpec | int | None, IOAttrs('tt', store_default=False)
    ] = None
    tint_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc1', store_default=False)
    ] = None
    tint2_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc2', store_default=False)
    ] = None

    #: Tint through the tint texture's blue channel (as
    #: :attr:`tint_color` is red and :attr:`tint2_color` green). Clients
    #: before this field ignore it.
    tint3_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('tc3', store_default=False)
    ] = None

    #: Packages laid out (in order) as the index domain integer texture
    #: slots index into; None when every slot is a full spec. (A plain
    #: None default rather than a list factory: a factory default breaks
    #: Sphinx's signature rendering of this class.)
    packages: Annotated[
        list[ApverNum] | None, IOAttrs('pk', store_default=False)
    ] = None

    #: Producer's (prefix) digest of that domain, checked by the client
    #: before resolving indices (see
    #: :func:`bacommon.assetspec.wire_digest`).
    domain_digest: Annotated[str | None, IOAttrs('dg', store_default=False)] = (
        None
    )

    #: See :class:`Depiction`. (Images ignore it for now.)
    color_override: Annotated[
        tuple[float, float, float] | None, IOAttrs('co', store_default=False)
    ] = None

    #: See :class:`Depiction`.
    team_coloring: Annotated[bool, IOAttrs('tco', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        return DepictionTypeID.IMAGE


@ioprepped
@dataclass
class CharacterIconDepiction(Depiction):
    """A character's icon, drawn square.

    ``icon`` is an opaque, cloud-composed icon definition (a
    character's icon component on its own; the schema is server-private,
    see bamaster ``baserver/character.py``), tinted by its own colors. A
    standard-character standin shows while the art isn't local.

    A color override replaces the icon's main color, the way a team's
    color replaces a character's own on its spaz; highlights stay the
    icon's own.
    """

    icon: Annotated[str, IOAttrs('j')]

    #: See :class:`Depiction`.
    color_override: Annotated[
        tuple[float, float, float] | None, IOAttrs('co', store_default=False)
    ] = None

    #: See :class:`Depiction`.
    team_coloring: Annotated[bool, IOAttrs('tco', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        return DepictionTypeID.CHARACTER_ICON


@ioprepped
@dataclass
class NameDepiction(Depiction):
    """A name: an in-game name, an account name, a character's name.

    ``name`` is an opaque, cloud-composed name definition (the same form
    a character's name component takes; the schema is server-private,
    see bamaster ``baserver/character.py``). Its basic form is colored
    text; richer forms (a capsule with an icon, as account names are
    shown) fall back to it on clients that don't understand them. Its
    shape is its measured text (or capsule), fitted into the box by the
    alignment.
    """

    name: Annotated[str, IOAttrs('j')]

    #: See :class:`Depiction`.
    color_override: Annotated[
        tuple[float, float, float] | None, IOAttrs('co', store_default=False)
    ] = None

    #: See :class:`Depiction`.
    team_coloring: Annotated[bool, IOAttrs('tco', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        return DepictionTypeID.NAME


@ioprepped
@dataclass
class CharacterViewerDepiction(Depiction):
    """A character standing in a little scene of its own, live in 3D.

    ``spaz`` is an opaque, cloud-composed spaz definition (a character's
    in-game form on its own; see :class:`CharacterIconDepiction`); it
    alone decides how the character looks, colors included. A host keeps
    the viewer running across updates, so a changed definition (an
    editor's draft, say) updates the picture in place rather than
    starting it over.
    """

    spaz: Annotated[str, IOAttrs('j')]

    #: How much the camera's hand-held wobble moves, relative to the
    #: usual: 2.0 wobbles twice as much, 0 (or less) holds it still, and
    #: 10 is the most there is (more counts as 10). (Still regardless
    #: while the viewer has camera shake disabled.)
    camera_shake: Annotated[float, IOAttrs('cs', store_default=False)] = 1.0

    #: How far turning the device (on devices with a gyro) swings the
    #: camera around the character, relative to the usual: 2.0 swings
    #: twice as far, 0 (or less) not at all, and 10 is the most there is
    #: (more counts as 10). (Not at all regardless while the viewer has
    #: camera gyro disabled.)
    camera_gyro: Annotated[float, IOAttrs('cg', store_default=False)] = 1.0

    #: See :class:`Depiction`. (Viewers ignore it; the definition alone
    #: decides the character's colors.)
    color_override: Annotated[
        tuple[float, float, float] | None, IOAttrs('co', store_default=False)
    ] = None

    #: See :class:`Depiction`.
    team_coloring: Annotated[bool, IOAttrs('tco', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        return DepictionTypeID.CHARACTER_VIEWER


@ioprepped
@dataclass
class MeshViewerEntry:
    """One mesh shown by a :class:`MeshViewerDepiction`, and where."""

    #: The mesh, as a full spec or an index into the depiction's
    #: :attr:`~MeshViewerDepiction.packages` domain.
    mesh: Annotated[MeshSpec | int, IOAttrs('m')]

    #: Its texture, likewise; with none it draws in :attr:`color`
    #: alone.
    texture: Annotated[
        TextureSpec | int | None, IOAttrs('t', store_default=False)
    ] = None

    #: Multiplied into its texture (or its whole color, untextured):
    #: rgba. Alpha only shows when :attr:`transparent`.
    color: Annotated[
        tuple[float, float, float, float], IOAttrs('c', store_default=False)
    ] = (1.0, 1.0, 1.0, 1.0)

    #: Whether it's blended (by :attr:`color`'s alpha and its texture's)
    #: rather than solid. Blended entries draw after every solid one.
    #: Blending and tinting don't combine: a blended entry's tint is
    #: ignored (with a warning).
    transparent: Annotated[bool, IOAttrs('tr', store_default=False)] = False

    #: A cube map it reflects (a full spec or an index); None for none.
    reflection: Annotated[
        CubeMapTextureSpec | int | None, IOAttrs('rf', store_default=False)
    ] = None

    #: Multiplied into what it reflects (rgb).
    reflection_scale: Annotated[
        tuple[float, float, float], IOAttrs('rs', store_default=False)
    ] = (1.0, 1.0, 1.0)

    #: A texture whose red, green and blue channels say where
    #: :attr:`tint_color`, :attr:`tint2_color` and :attr:`tint3_color`
    #: apply (a character's color mask, say); None for no tinting.
    tint_texture: Annotated[
        TextureSpec | int | None, IOAttrs('tt', store_default=False)
    ] = None

    #: Tint through the tint texture's red channel.
    tint_color: Annotated[
        tuple[float, float, float], IOAttrs('tc1', store_default=False)
    ] = (1.0, 1.0, 1.0)

    #: Tint through the tint texture's green channel.
    tint2_color: Annotated[
        tuple[float, float, float], IOAttrs('tc2', store_default=False)
    ] = (1.0, 1.0, 1.0)

    #: Tint through the tint texture's blue channel.
    tint3_color: Annotated[
        tuple[float, float, float], IOAttrs('tc3', store_default=False)
    ] = (1.0, 1.0, 1.0)

    #: Where it sits, relative to the others.
    position: Annotated[
        tuple[float, float, float], IOAttrs('p', store_default=False)
    ] = (0.0, 0.0, 0.0)

    #: How it's turned, in degrees about x, then y, then z.
    rotation: Annotated[
        tuple[float, float, float], IOAttrs('r', store_default=False)
    ] = (0.0, 0.0, 0.0)

    #: How it's stretched along each axis.
    scale: Annotated[
        tuple[float, float, float], IOAttrs('s', store_default=False)
    ] = (1.0, 1.0, 1.0)


@ioprepped
@dataclass
class MeshViewerCameraPose:
    """Where a :class:`MeshViewerCamera` is at some moment.

    In the depiction's own space: the same one its entries'
    :attr:`~MeshViewerEntry.position` values place them in.
    """

    #: Where it looks from.
    position: Annotated[tuple[float, float, float], IOAttrs('p')]

    #: What it looks at.
    target: Annotated[tuple[float, float, float], IOAttrs('t')]

    #: Its vertical field of view, in degrees (between 0 and 180).
    fov_y: Annotated[float, IOAttrs('f')]


class MeshViewerCameraTypeID(Enum):
    """Type ID for each kind of :class:`MeshViewerCamera`."""

    UNKNOWN = 'u'
    STILL = 's'
    PING_PONG = 'pp'


class MeshViewerCamera(IOMultiType[MeshViewerCameraTypeID]):
    """A :class:`MeshViewerDepiction`'s camera, placed by hand.

    Either held in one place (:class:`MeshViewerStillCamera`) or moving
    (:class:`MeshViewerPingPongCamera`). A client that doesn't know a
    kind frames things automatically, as with no camera at all.
    """

    @override
    @classmethod
    def get_type_id(cls) -> MeshViewerCameraTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: MeshViewerCameraTypeID
    ) -> type[MeshViewerCamera]:
        t = MeshViewerCameraTypeID
        if type_id is t.UNKNOWN:
            return MeshViewerUnknownCamera
        if type_id is t.STILL:
            return MeshViewerStillCamera
        if type_id is t.PING_PONG:
            return MeshViewerPingPongCamera
        assert_never(type_id)

    @override
    @classmethod
    def get_default_type_id(cls) -> MeshViewerCameraTypeID:
        # Still cameras predate kinds (they were the only camera in
        # 1.8.3), so they go without a type id; this must never change.
        return MeshViewerCameraTypeID.STILL

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> MeshViewerCamera:
        return MeshViewerUnknownCamera()


@ioprepped
@dataclass
class MeshViewerUnknownCamera(MeshViewerCamera):
    """A camera of a kind this client doesn't know.

    Treated as no camera at all: things are framed automatically.
    """

    @override
    @classmethod
    def get_type_id(cls) -> MeshViewerCameraTypeID:
        return MeshViewerCameraTypeID.UNKNOWN


@ioprepped
@dataclass
class MeshViewerStillCamera(MeshViewerCamera):
    """A camera held in one place.

    In the depiction's own space (see :class:`MeshViewerCameraPose`,
    whose fields these are).
    """

    #: Where it looks from.
    position: Annotated[tuple[float, float, float], IOAttrs('p')]

    #: What it looks at.
    target: Annotated[tuple[float, float, float], IOAttrs('t')]

    #: Its vertical field of view, in degrees (between 0 and 180).
    fov_y: Annotated[float, IOAttrs('f')]

    @override
    @classmethod
    def get_type_id(cls) -> MeshViewerCameraTypeID:
        return MeshViewerCameraTypeID.STILL


@ioprepped
@dataclass
class MeshViewerPingPongCamera(MeshViewerCamera):
    """A camera moving back and forth between two poses.

    It starts at :attr:`a`, sways over to :attr:`b`, and sways back,
    over and over: one smooth sine wave, fastest midway and easing
    into each turnaround (position, target and field of view all move
    together, in straight lines). Time only passes while the viewer is
    shown, and an update leaving the camera as it was carries on
    without starting over.
    """

    #: Where it starts.
    a: Annotated[MeshViewerCameraPose, IOAttrs('a')]

    #: Where it goes.
    b: Annotated[MeshViewerCameraPose, IOAttrs('b')]

    #: Seconds each way.
    travel_time: Annotated[float, IOAttrs('d')]

    #: Whether it keeps going back and forth. Off, it eases over to
    #: :attr:`b` just once (with the same timing) and stays there.
    loop: Annotated[bool, IOAttrs('l', store_default=False)] = True

    @override
    @classmethod
    def get_type_id(cls) -> MeshViewerCameraTypeID:
        return MeshViewerCameraTypeID.PING_PONG


@ioprepped
@dataclass
class MeshViewerDepiction(Depiction):
    """A few meshes, live in 3D and slowly turning.

    Its :attr:`entries` are placed relative to one another; the client
    frames them all to fill the picture (by the bounds meshes carry),
    turns them slowly, and lets them be swung around by dragging, much
    as the asset browser's mesh preview does. On devices with a gyro,
    turning the device swings the view around what the camera looks at
    (see :attr:`camera_gyro`). A host keeps the viewer running across
    updates, so changed entries reframe in place.
    """

    entries: Annotated[list[MeshViewerEntry], IOAttrs('e')]

    #: Whether it turns on its own. (When it doesn't, it always shows
    #: exactly its :attr:`view_yaw` to start with.)
    spin: Annotated[bool, IOAttrs('sp', store_default=False)] = True

    #: Whether dragging on it swings it around. Off, with :attr:`spin`
    #: off too, it's a completely fixed view.
    draggable: Annotated[bool, IOAttrs('dr', store_default=False)] = True

    #: How big an area it frames, relative to the bounds of everything
    #: in it (about the same center): 2.0 frames twice as much, so its
    #: meshes look half as big. Meant for shrinking (1 and up); below 1
    #: crops in (and well below, the camera ends up in among them).
    bounds_scale: Annotated[float, IOAttrs('bs', store_default=False)] = 1.0

    #: Degrees the turntable starts turned (about the vertical axis);
    #: with :attr:`spin` off, the side that faces the camera.
    view_yaw: Annotated[float, IOAttrs('vy', store_default=False)] = 0.0

    #: Degrees the camera starts looking down at what it frames (0 head
    #: on, up to just short of 90 straight down; negative looks up);
    #: None for the usual, about 29.
    view_pitch: Annotated[float | None, IOAttrs('vp', store_default=False)] = (
        None
    )

    #: A camera placed by hand, for a set shot (held still or moving;
    #: see :class:`MeshViewerCamera`). When given, nothing is
    #: framed automatically (:attr:`bounds_scale` and :attr:`view_pitch`
    #: don't apply) and dragging up and down does nothing. The turntable
    #: still turns everything about the origin (with :attr:`spin`,
    #: :attr:`view_yaw`, and side to side drags).
    camera: Annotated[
        MeshViewerCamera | None, IOAttrs('cam', store_default=False)
    ] = None

    #: How much the camera's hand-held wobble moves, as
    #: :attr:`CharacterViewerDepiction.camera_shake` does: 1.0 is the
    #: character viewer's usual, 0 (or less) holds it still, and 10 is
    #: the most there is. None for the default: 1.0 with a
    #: :attr:`camera` placed by hand (a set shot), else 0.
    camera_shake: Annotated[
        float | None, IOAttrs('cs', store_default=False)
    ] = None

    #: How far turning the device (on devices with a gyro) swings the
    #: camera around what it looks at, relative to the usual: 2.0 swings
    #: twice as far, 0 (or less) not at all, and 10 is the most there is
    #: (more counts as 10). The usual is a generous
    #: swing for framed views and a subtler one (a third as far) under a
    #: :attr:`camera` placed by hand. (Not at all regardless while the
    #: viewer has camera gyro disabled.)
    camera_gyro: Annotated[float, IOAttrs('cg', store_default=False)] = 1.0

    #: What shows behind the meshes; None for the host's usual viewer
    #: background (a doc-ui viewer pane's own blank color, say).
    background_color: Annotated[
        tuple[float, float, float] | None, IOAttrs('bg', store_default=False)
    ] = None

    #: Packages laid out (in order) as the index domain integer slots
    #: index into; None when every slot is a full spec (see
    #: :class:`ImageDepiction`).
    packages: Annotated[
        list[ApverNum] | None, IOAttrs('pk', store_default=False)
    ] = None

    #: Producer's (prefix) digest of that domain (see
    #: :class:`ImageDepiction`).
    domain_digest: Annotated[str | None, IOAttrs('dg', store_default=False)] = (
        None
    )

    #: See :class:`Depiction`. (Ignored; entries carry their own
    #: colors.)
    color_override: Annotated[
        tuple[float, float, float] | None, IOAttrs('co', store_default=False)
    ] = None

    #: See :class:`Depiction`. (Ignored, as above.)
    team_coloring: Annotated[bool, IOAttrs('tco', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        return DepictionTypeID.MESH_VIEWER
