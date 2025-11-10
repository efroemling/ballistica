# Released under the MIT License. See LICENSE for details.
#
"""Version 1 of our dec-ui system."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import override, assert_never, TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType
from bacommon.locale import Locale

if TYPE_CHECKING:
    pass


class DecUIRequestTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class DecUIRequest(IOMultiType[DecUIRequestTypeID]):
    """UI defined by the cloud.

    Conceptually similar to web pages, except using app UI.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DecUIRequestTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: DecUIRequestTypeID) -> type[DecUIRequest]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = DecUIRequestTypeID
        if type_id is t.UNKNOWN:
            return UnknownDecUIRequest
        if type_id is t.V1:
            from bacommon.decui.v1 import Request

            return Request

        # Make sure we cover all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> DecUIRequest:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownDecUIRequest()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownDecUIRequest(DecUIRequest):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder request.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DecUIRequestTypeID:
        return DecUIRequestTypeID.UNKNOWN


class DecUIResponseTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class DecUIResponse(IOMultiType[DecUIResponseTypeID]):
    """UI defined by the cloud.

    Conceptually similar to a basic html response, except using app UI.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DecUIResponseTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: DecUIResponseTypeID) -> type[DecUIResponse]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = DecUIResponseTypeID
        if type_id is t.UNKNOWN:
            return UnknownDecUIResponse
        if type_id is t.V1:
            from bacommon.decui.v1 import Response

            return Response

        # Make sure we cover all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> DecUIResponse:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownDecUIResponse()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownDecUIResponse(DecUIResponse):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder response.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DecUIResponseTypeID:
        return DecUIResponseTypeID.UNKNOWN


@ioprepped
@dataclass
class DecUIWebRequest:
    """Complete data sent for dec-ui http requests."""

    #: The wrapped dec-ui request.
    dec_ui_request: Annotated[DecUIRequest, IOAttrs('r')]

    #: The current locale of the client. Dec-ui generally deals in raw
    #: strings and expects localization to happen on the server.
    locale: Annotated[Locale, IOAttrs('l')]

    #: Engine build number. In some cases it may make sense to adjust
    #: responses depending on available engine features.
    engine_build_number: Annotated[int, IOAttrs('b')]


@ioprepped
@dataclass
class DecUIWebResponse:
    """Complete data returned for dec-ui http requests."""

    #: Human readable error string (if an error occurs). Either this or
    #: dec_ui_response should be set; not both.
    error: Annotated[str | None, IOAttrs('e', store_default=False)] = None

    #: Dec-ui response. Either this or error should be set; not both.
    dec_ui_response: Annotated[
        DecUIResponse | None,
        IOAttrs('r', store_default=False),
    ] = None
