# Released under the MIT License. See LICENSE for details.
#
"""Full UIs defined in the cloud - similar to a basic form of html"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType


class CloudUITypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class CloudUI(IOMultiType[CloudUITypeID]):
    """UI defined by the cloud.

    Conceptually similar to a basic html page, except using app UI.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUITypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: CloudUITypeID) -> type[CloudUI]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import
        out: type[CloudUI]

        t = CloudUITypeID
        if type_id is t.UNKNOWN:
            out = UnknownCloudUI
        elif type_id is t.V1:
            out = V1CloudUI
        else:
            # Important to make sure we provide all types.
            assert_never(type_id)
        return out

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> CloudUI:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return UnknownCloudUI()


@ioprepped
@dataclass
class UnknownCloudUI(CloudUI):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder page.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUITypeID:
        return CloudUITypeID.UNKNOWN


class V1CloudUIComponentTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    TEXT = 't'


class V1CloudUIComponent(IOMultiType[V1CloudUIComponentTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> V1CloudUIComponentTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: V1CloudUIComponentTypeID
    ) -> type[V1CloudUIComponent]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = V1CloudUIComponentTypeID
        if type_id is t.UNKNOWN:
            return V1CloudUIComponentUnknown
        if type_id is t.TEXT:
            return V1CloudUIComponentText

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> V1CloudUIComponent:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return V1CloudUIComponentUnknown()


@ioprepped
@dataclass
class V1CloudUIComponentUnknown(V1CloudUIComponent):
    """An unknown basic client component type.

    In practice these should never show up since the master-server
    generates these on the fly for the client and so should not send
    clients one they can't digest.
    """

    @override
    @classmethod
    def get_type_id(cls) -> V1CloudUIComponentTypeID:
        return V1CloudUIComponentTypeID.UNKNOWN


@ioprepped
@dataclass
class V1CloudUIComponentText(V1CloudUIComponent):
    """Show some text over a button."""

    text: Annotated[str, IOAttrs('t')]
    # position: Annotated[float, IOAttrs('p', store_default=False)] = 1.0
    # scale: Annotated[float, IOAttrs('s', store_default=False)] = 1.0
    # color: Annotated[
    #     tuple[float, float, float, float], IOAttrs('c', store_default=False)
    # ] = (1.0, 1.0, 1.0, 1.0)

    @override
    @classmethod
    def get_type_id(cls) -> V1CloudUIComponentTypeID:
        return V1CloudUIComponentTypeID.TEXT


@ioprepped
@dataclass
class V1CloudUIButton:
    """A button in our cloud ui."""

    color: Annotated[tuple[float, float, float], IOAttrs('cl')]
    size: Annotated[tuple[float, float], IOAttrs('sz')]
    components: Annotated[list[V1CloudUIComponent], IOAttrs('c')]
    scale: Annotated[float, IOAttrs('sc', store_default=False)] = 1.0


@ioprepped
@dataclass
class V1CloudUIRow:
    """A row in our cloud ui."""

    buttons: Annotated[list[V1CloudUIButton], IOAttrs('b')]


@ioprepped
@dataclass
class V1CloudUI(CloudUI):
    """Version 1 of our cloud-defined UI type."""

    rows: Annotated[list[V1CloudUIRow], IOAttrs('r')]

    @override
    @classmethod
    def get_type_id(cls) -> CloudUITypeID:
        return CloudUITypeID.V1
