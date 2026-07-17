# Released under the MIT License. See LICENSE for details.
#
"""Version 1 of our doc-ui system."""

from enum import Enum
from dataclasses import dataclass
from typing import override, assert_never, TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType
from bacommon.locale import Locale

if TYPE_CHECKING:
    pass


class DocUIRequestTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'
    V2 = 'v2'


class DocUIRequest(IOMultiType[DocUIRequestTypeID]):
    """A request for some UI."""

    @override
    @classmethod
    def get_type_id(cls) -> DocUIRequestTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: DocUIRequestTypeID) -> type[DocUIRequest]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = DocUIRequestTypeID
        if type_id is t.UNKNOWN:
            return UnknownDocUIRequest
        if type_id is t.V1:
            from bacommon.docui.v1 import Request

            return Request
        if type_id is t.V2:
            from bacommon.docui.v2 import Request as RequestV2

            return RequestV2

        # Make sure we cover all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> DocUIRequest:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownDocUIRequest()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownDocUIRequest(DocUIRequest):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder request.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DocUIRequestTypeID:
        return DocUIRequestTypeID.UNKNOWN


@ioprepped
@dataclass
class WrapParams:
    """Constraints for splitting a text value into lines client-side.

    Mirrors the engine's simple equal-width line splitter
    (``babase.split_text_into_lines()``): text is broken only at valid
    line-break opportunities, using the fewest lines that keep every
    line within :attr:`max_chars_per_line` (when provided) while
    staying between :attr:`min_lines` and :attr:`max_lines` (``None``
    means unlimited), with line lengths balanced within that count. So
    ``max_chars_per_line`` alone gives basic wrapping and ``min_lines``
    alone gives an exact line count. Constraints are best-effort.

    In v2 documents this can accompany any text field (via its
    ``*_wrap`` companion field); wrapping applies on the client after
    the text decodes in its locale, replacing the hand-placed newlines
    v1 documents bake into pre-localized strings.
    """

    min_lines: Annotated[int, IOAttrs('mn', store_default=False)] = 1
    max_lines: Annotated[int | None, IOAttrs('mx', store_default=False)] = None
    max_chars_per_line: Annotated[
        int | None, IOAttrs('mc', store_default=False)
    ] = None


class DocUIResponseTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'
    V2 = 'v2'


class DocUIResponse(IOMultiType[DocUIResponseTypeID]):
    """A UI provied in response to a :class:`DocUIRequest`."""

    @override
    @classmethod
    def get_type_id(cls) -> DocUIResponseTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: DocUIResponseTypeID) -> type[DocUIResponse]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = DocUIResponseTypeID
        if type_id is t.UNKNOWN:
            return UnknownDocUIResponse
        if type_id is t.V1:
            from bacommon.docui.v1 import Response

            return Response
        if type_id is t.V2:
            from bacommon.docui.v2 import Response as ResponseV2

            return ResponseV2

        # Make sure we cover all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> DocUIResponse:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownDocUIResponse()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownDocUIResponse(DocUIResponse):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder response.
    """

    @override
    @classmethod
    def get_type_id(cls) -> DocUIResponseTypeID:
        return DocUIResponseTypeID.UNKNOWN


@ioprepped
@dataclass
class DocUIWebRequest:
    """Complete data sent for doc-ui http requests."""

    #: The wrapped doc-ui request.
    doc_ui_request: Annotated[DocUIRequest, IOAttrs('r')]

    #: The current locale of the client. doc-ui generally deals in raw
    #: strings and expects localization to happen on the server.
    locale: Annotated[Locale, IOAttrs('l')]

    #: Engine build number. In some cases it may make sense to adjust
    #: responses depending on available engine features.
    engine_build_number: Annotated[int, IOAttrs('b')]


@ioprepped
@dataclass
class DocUIWebResponse:
    """Complete data returned for doc-ui http requests."""

    #: Human readable error string (if an error occurs). Either this or
    #: doc_ui_response should be set; not both.
    error: Annotated[str | None, IOAttrs('e', store_default=False)] = None

    #: doc-ui response. Either this or error should be set; not both.
    doc_ui_response: Annotated[
        DocUIResponse | None,
        IOAttrs('r', store_default=False),
    ] = None
