# Released under the MIT License. See LICENSE for details.
#
"""Full UIs defined in the cloud - similar to a basic form of html"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.cloudui._cloudui import CloudUIPage, CloudUIPageTypeID


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
    max_width: Annotated[float, IOAttrs('w')]
    max_height: Annotated[float, IOAttrs('h', store_default=False)] = 32.0
    scale: Annotated[float, IOAttrs('s', store_default=False)] = 1.0
    h_align: Annotated[HAlign, IOAttrs('ha', store_default=False)] = (
        HAlign.CENTER
    )
    v_align: Annotated[VAlign, IOAttrs('va', store_default=False)] = (
        VAlign.CENTER
    )
    flatness: Annotated[float | None, IOAttrs('f', store_default=False)] = None
    shadow: Annotated[float | None, IOAttrs('sh', store_default=False)] = None

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

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.IMAGE


@ioprepped
@dataclass
class Button:
    """A button in our cloud ui."""

    #: Note that cloud-ui accepts only raw :class:`str` values for text;
    #: use :meth:`babase.Lstr.evaluate()` or whatnot for multi-language
    #: support.
    label: Annotated[str | None, IOAttrs('l', store_default=False)] = None
    size: Annotated[
        tuple[float, float] | None, IOAttrs('sz', store_default=False)
    ] = None
    color: Annotated[
        tuple[float, float, float] | None, IOAttrs('cl', store_default=False)
    ] = None
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
    scale: Annotated[float, IOAttrs('sc', store_default=False)] = 1.0
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 0.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 0.0
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 0.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 0.0
    decorations: Annotated[
        list[Decoration], IOAttrs('c', store_default=False)
    ] = field(default_factory=list)
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
    button_spacing: Annotated[float, IOAttrs('bs', store_default=False)] = 5.0
    padding_left: Annotated[float, IOAttrs('pl', store_default=False)] = 10.0
    padding_right: Annotated[float, IOAttrs('pr', store_default=False)] = 10.0
    padding_top: Annotated[float, IOAttrs('pt', store_default=False)] = 10.0
    padding_bottom: Annotated[float, IOAttrs('pb', store_default=False)] = 10.0
    center: Annotated[bool, IOAttrs('c', store_default=False)] = False

    #: If things disappear when scrolling left/right, turn this up.
    simple_culling_h: Annotated[float, IOAttrs('sch', store_default=False)] = (
        100.0
    )


@ioprepped
@dataclass
class Page(CloudUIPage):
    """Cloud-UI page version 1."""

    #: Note that cloud-ui accepts only raw :class:`str` values for text;
    #: use :meth:`babase.Lstr.evaluate()` or whatnot for multi-language
    #: support.
    title: Annotated[str, IOAttrs('t')]
    rows: Annotated[list[Row], IOAttrs('r')]

    #: If things disappear when scrolling up and down, turn this up.
    simple_culling_v: Annotated[float, IOAttrs('scv', store_default=False)] = (
        100.0
    )

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIPageTypeID:
        return CloudUIPageTypeID.V1
