# Released under the MIT License. See LICENSE for details.
#
"""Full UIs defined in the cloud - similar to a basic form of html"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.cloudui._cloudui import CloudUI, CloudUITypeID


class DecorationTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TEXT = 't'


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
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = DecorationTypeID
        if type_id is t.UNKNOWN:
            return UnknownDecoration
        if type_id is t.TEXT:
            return Text

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Decoration:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownDecoration()


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

    text: Annotated[str, IOAttrs('t')]

    @override
    @classmethod
    def get_type_id(cls) -> DecorationTypeID:
        return DecorationTypeID.TEXT


@ioprepped
@dataclass
class Button:
    """A button in our cloud ui."""

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
    decorations: Annotated[
        list[Decoration], IOAttrs('c', store_default=False)
    ] = field(default_factory=list)
    scale: Annotated[float, IOAttrs('sc', store_default=False)] = 1.0


@ioprepped
@dataclass
class Row:
    """A row in our cloud ui."""

    buttons: Annotated[list[Button], IOAttrs('b')]
    title: Annotated[str | None, IOAttrs('t', store_default=False)] = None
    subtitle: Annotated[str | None, IOAttrs('s', store_default=False)] = None
    button_spacing: Annotated[float, IOAttrs('bs')] = 5.0
    padding_left: Annotated[float, IOAttrs('pl')] = 10.0
    padding_right: Annotated[float, IOAttrs('pr')] = 10.0
    padding_top: Annotated[float, IOAttrs('pt')] = 10.0
    padding_bottom: Annotated[float, IOAttrs('pb')] = 10.0
    center: Annotated[bool, IOAttrs('c', store_default=False)] = False


@ioprepped
@dataclass
class UI(CloudUI):
    """Version 1 of our cloud-defined UI type."""

    title: Annotated[str, IOAttrs('t')]
    rows: Annotated[list[Row], IOAttrs('r')]

    @override
    @classmethod
    def get_type_id(cls) -> CloudUITypeID:
        return CloudUITypeID.V1
