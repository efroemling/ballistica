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
from bacommon.assetspec import TextureSpec


class DepictionTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    IMAGE = 'i'
    CHARACTER_ICON = 'ci'
    NAME = 'n'
    CHARACTER_VIEWER = 'cv'


class Depiction(IOMultiType[DepictionTypeID]):
    """Something for a client to draw; see the module docs."""

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: DepictionTypeID) -> type[Depiction]:
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
    """

    icon: Annotated[str, IOAttrs('j')]

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

    @override
    @classmethod
    def get_type_id(cls) -> DepictionTypeID:
        return DepictionTypeID.CHARACTER_VIEWER
