# Released under the MIT License. See LICENSE for details.
#
"""Version 1 of our cloud-ui system."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import override, assert_never, TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType
from bacommon.locale import Locale

if TYPE_CHECKING:
    pass


class CloudUIRequestTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class CloudUIRequest(IOMultiType[CloudUIRequestTypeID]):
    """UI defined by the cloud.

    Conceptually similar to web pages, except using app UI.
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


@ioprepped
@dataclass
class CloudUIWebRequest:
    """Complete data sent for cloud-ui http requests."""

    #: The wrapped cloud-ui request.
    cloud_ui_request: Annotated[CloudUIRequest, IOAttrs('r')]

    #: The current locale of the client. Cloud-ui generally deals in raw
    #: strings and expects localization to happen on the server.
    locale: Annotated[Locale, IOAttrs('l')]

    #: Engine build number. In some cases it may make sense to adjust
    #: responses depending on available engine features.
    engine_build_number: Annotated[int, IOAttrs('b')]


@ioprepped
@dataclass
class CloudUIWebResponse:
    """Complete data returned for cloud-ui http requests."""

    #: Human readable error string (if an error occurs). Either this or
    #: cloud_ui_response should be set; not both.
    error: Annotated[str | None, IOAttrs('e', store_default=False)] = None

    #: Cloud-ui response. Either this or error should be set; not both.
    cloud_ui_response: Annotated[
        CloudUIResponse | None,
        IOAttrs('r', store_default=False),
    ] = None
