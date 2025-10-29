# Released under the MIT License. See LICENSE for details.
#
"""Full UIs defined in the cloud - similar to a basic form of html"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import override, assert_never, TYPE_CHECKING

from efro.dataclassio import ioprepped, IOMultiType

if TYPE_CHECKING:
    pass


class CloudUIRequestTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class CloudUIRequest(IOMultiType[CloudUIRequestTypeID]):
    """UI defined by the cloud.

    Conceptually similar to a basic html request, except using app UI.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIRequestTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: CloudUIRequestTypeID) -> type[CloudUIRequest]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = CloudUIRequestTypeID
        if type_id is t.UNKNOWN:
            return UnknownCloudUIRequest
        if type_id is t.V1:
            from bacommon.cloudui.v1 import Request

            return Request

        # Make sure we cover all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> CloudUIRequest:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownCloudUIRequest()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownCloudUIRequest(CloudUIRequest):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder request.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIRequestTypeID:
        return CloudUIRequestTypeID.UNKNOWN


class CloudUIResponseTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class CloudUIResponse(IOMultiType[CloudUIResponseTypeID]):
    """UI defined by the cloud.

    Conceptually similar to a basic html response, except using app UI.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIResponseTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: CloudUIResponseTypeID) -> type[CloudUIResponse]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = CloudUIResponseTypeID
        if type_id is t.UNKNOWN:
            return UnknownCloudUIResponse
        if type_id is t.V1:
            from bacommon.cloudui.v1 import Response

            return Response

        # Make sure we cover all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> CloudUIResponse:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownCloudUIResponse()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownCloudUIResponse(CloudUIResponse):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder response.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIResponseTypeID:
        return CloudUIResponseTypeID.UNKNOWN
