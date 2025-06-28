# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to cloud functionality."""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override

from efro.message import Message, Response
from efro.dataclassio import ioprepped, IOAttrs
from bacommon.securedata import SecureDataChecker
from bacommon.transfer import DirectoryManifest
from bacommon.login import LoginType

if TYPE_CHECKING:
    pass


class WebLocation(Enum):
    """Set of places we can be directed on ballistica.net."""

    ACCOUNT_EDITOR = 'e'
    ACCOUNT_DELETE_SECTION = 'd'


@ioprepped
@dataclass
class CloudVals:
    """Engine config values provided by the master server.

    Used to convey things such as debug logging.
    """

    #: Fully qualified type names we should emit extra debug logs for
    #: when garbage-collected (for debugging ref loops).
    gc_debug_types: Annotated[
        list[str], IOAttrs('gct', store_default=False)
    ] = field(default_factory=list)

    #: Max number of objects of a given type to emit debug logs for.
    gc_debug_type_limit: Annotated[int, IOAttrs('gdl', store_default=False)] = 2


@ioprepped
@dataclass
class LoginProxyRequestMessage(Message):
    """Request send to the cloud to ask for a login-proxy."""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [LoginProxyRequestResponse]


@ioprepped
@dataclass
class LoginProxyRequestResponse(Response):
    """Response to a request for a login proxy."""

    # URL to direct the user to for sign in.
    url: Annotated[str, IOAttrs('u')]

    # URL to use for overlay-web-browser sign ins.
    url_overlay: Annotated[str, IOAttrs('uo')]

    # Proxy-Login id for querying results.
    proxyid: Annotated[str, IOAttrs('p')]

    # Proxy-Login key for querying results.
    proxykey: Annotated[str, IOAttrs('k')]


@ioprepped
@dataclass
class LoginProxyStateQueryMessage(Message):
    """Soo.. how is that login proxy going?"""

    proxyid: Annotated[str, IOAttrs('p')]
    proxykey: Annotated[str, IOAttrs('k')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [LoginProxyStateQueryResponse]


@ioprepped
@dataclass
class LoginProxyStateQueryResponse(Response):
    """Here's the info on that login-proxy you asked about, boss."""

    class State(Enum):
        """States a login-proxy can be in."""

        WAITING = 'waiting'
        SUCCESS = 'success'
        FAIL = 'fail'

    state: Annotated[State, IOAttrs('s')]

    # On success, these will be filled out.
    credentials: Annotated[str | None, IOAttrs('tk')]


@ioprepped
@dataclass
class LoginProxyCompleteMessage(Message):
    """Just so you know, we're done with this proxy."""

    proxyid: Annotated[str, IOAttrs('p')]


@ioprepped
@dataclass
class PingMessage(Message):
    """Standard ping."""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [PingResponse]


@ioprepped
@dataclass
class PingResponse(Response):
    """pong."""


@ioprepped
@dataclass
class TestMessage(Message):
    """Can I get some of that workspace action?"""

    testfoo: Annotated[int, IOAttrs('f')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [TestResponse]


@ioprepped
@dataclass
class TestResponse(Response):
    """Here's that workspace you asked for, boss."""

    testfoo: Annotated[int, IOAttrs('f')]


@ioprepped
@dataclass
class SendInfoMessage(Message):
    """User is using the send-info function"""

    description: Annotated[str, IOAttrs('c')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [SendInfoResponse]


@ioprepped
@dataclass
class SendInfoResponse(Response):
    """Response to sending into the server."""

    handled: Annotated[bool, IOAttrs('v')]
    message: Annotated[str | None, IOAttrs('m', store_default=False)] = None
    legacy_code: Annotated[str | None, IOAttrs('l', store_default=False)] = None


@ioprepped
@dataclass
class WorkspaceFetchState:
    """Common state data for a workspace fetch."""

    manifest: Annotated[DirectoryManifest, IOAttrs('m')]
    iteration: Annotated[int, IOAttrs('i')] = 0
    total_deletes: Annotated[int, IOAttrs('tdels')] = 0
    total_downloads: Annotated[int, IOAttrs('tdlds')] = 0
    total_up_to_date: Annotated[int | None, IOAttrs('tunmd')] = None


@ioprepped
@dataclass
class WorkspaceFetchMessage(Message):
    """Can I get some of that workspace action?"""

    workspaceid: Annotated[str, IOAttrs('w')]
    state: Annotated[WorkspaceFetchState, IOAttrs('s')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [WorkspaceFetchResponse]


@ioprepped
@dataclass
class WorkspaceFetchResponse(Response):
    """Here's that workspace you asked for, boss."""

    state: Annotated[WorkspaceFetchState, IOAttrs('s')]
    deletes: Annotated[list[str], IOAttrs('dlt', store_default=False)] = field(
        default_factory=list
    )
    downloads_inline: Annotated[
        dict[str, bytes], IOAttrs('dinl', store_default=False)
    ] = field(default_factory=dict)

    done: Annotated[bool, IOAttrs('d')] = False


@ioprepped
@dataclass
class MerchAvailabilityMessage(Message):
    """Can we show merch link?"""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [MerchAvailabilityResponse]


@ioprepped
@dataclass
class MerchAvailabilityResponse(Response):
    """About that merch..."""

    url: Annotated[str | None, IOAttrs('u')]


@ioprepped
@dataclass
class SignInMessage(Message):
    """Can I sign in please?"""

    login_type: Annotated[LoginType, IOAttrs('l')]
    sign_in_token: Annotated[str, IOAttrs('t')]

    # For debugging. Can remove soft_default once build 20988+ is ubiquitous.
    description: Annotated[str, IOAttrs('d', soft_default='-')]
    apptime: Annotated[float, IOAttrs('at', soft_default=-1.0)]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [SignInResponse]


@ioprepped
@dataclass
class SignInResponse(Response):
    """Here's that sign-in result you asked for, boss."""

    credentials: Annotated[str | None, IOAttrs('c')]


@ioprepped
@dataclass
class ManageAccountMessage(Message):
    """Message asking for a manage-account url."""

    weblocation: Annotated[WebLocation, IOAttrs('l')] = (
        WebLocation.ACCOUNT_EDITOR
    )

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ManageAccountResponse]


@ioprepped
@dataclass
class ManageAccountResponse(Response):
    """Here's that sign-in result you asked for, boss."""

    url: Annotated[str | None, IOAttrs('u')]


@ioprepped
@dataclass
class StoreQueryMessage(Message):
    """Message asking about purchasable stuff and store related state."""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [StoreQueryResponse]


@ioprepped
@dataclass
class StoreQueryResponse(Response):
    """Here's that store info you asked for, boss."""

    class Result(Enum):
        """Our overall result."""

        SUCCESS = 's'
        ERROR = 'e'

    @dataclass
    class Purchase:
        """Info about a purchasable thing."""

        purchaseid: Annotated[str, IOAttrs('id')]

    # Overall result; all data is undefined if not SUCCESS.
    result: Annotated[Result, IOAttrs('r')]

    tokens: Annotated[int, IOAttrs('t')]
    gold_pass: Annotated[bool, IOAttrs('g')]

    available_purchases: Annotated[list[Purchase], IOAttrs('p')]
    token_info_url: Annotated[str, IOAttrs('tiu')]


@ioprepped
@dataclass
class SecureDataCheckMessage(Message):
    """Was this data signed by the master-server?."""

    data: Annotated[bytes, IOAttrs('d')]
    signature: Annotated[bytes, IOAttrs('s')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [SecureDataCheckResponse]


@ioprepped
@dataclass
class SecureDataCheckResponse(Response):
    """Here's the result of that data check, boss."""

    # Whether the data signature was valid.
    result: Annotated[bool, IOAttrs('v')]


@ioprepped
@dataclass
class SecureDataCheckerRequest(Message):
    """Can I get a checker over here?."""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [SecureDataCheckerResponse]


@ioprepped
@dataclass
class SecureDataCheckerResponse(Response):
    """Here's that checker ya asked for, boss."""

    checker: Annotated[SecureDataChecker, IOAttrs('c')]


@ioprepped
@dataclass
class CloudValsRequest(Message):
    """Can a fella get some cloud vals around here?."""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [CloudValsResponse]


@ioprepped
@dataclass
class CloudValsResponse(Response):
    """Here's them cloud vals ya asked for, boss."""

    vals: Annotated[CloudVals, IOAttrs('v')]
