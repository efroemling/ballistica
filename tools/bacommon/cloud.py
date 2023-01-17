# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to cloud functionality."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated
from enum import Enum

from efro.message import Message, Response
from efro.dataclassio import ioprepped, IOAttrs
from bacommon.transfer import DirectoryManifest
from bacommon.login import LoginType

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class LoginProxyRequestMessage(Message):
    """Request send to the cloud to ask for a login-proxy."""

    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [LoginProxyRequestResponse]


@ioprepped
@dataclass
class LoginProxyRequestResponse(Response):
    """Response to a request for a login proxy."""

    # URL to direct the user to for login.
    url: Annotated[str, IOAttrs('u')]

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

    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ManageAccountResponse]


@ioprepped
@dataclass
class ManageAccountResponse(Response):
    """Here's that sign-in result you asked for, boss."""

    url: Annotated[str | None, IOAttrs('u')]
