# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to cloud functionality."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Optional
from enum import Enum

from efro.message import Message, Response
from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class LoginProxyRequestMessage(Message):
    """Request send to the cloud to ask for a login-proxy."""

    @classmethod
    def get_response_types(cls) -> list[type[Response]]:
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
    def get_response_types(cls) -> list[type[Response]]:
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
    credentials: Annotated[Optional[str], IOAttrs('tk')]


@ioprepped
@dataclass
class LoginProxyCompleteMessage(Message):
    """Just so you know, we're done with this proxy."""
    proxyid: Annotated[str, IOAttrs('p')]


@ioprepped
@dataclass
class AccountSessionReleaseMessage(Message):
    """We're done using this particular session."""
    token: Annotated[str, IOAttrs('tk')]


@ioprepped
@dataclass
class CredentialsCheckMessage(Message):
    """Are our current credentials valid?"""

    @classmethod
    def get_response_types(cls) -> list[type[Response]]:
        return [CredentialsCheckResponse]


@ioprepped
@dataclass
class CredentialsCheckResponse(Response):
    """Info returned when checking credentials."""

    verified: Annotated[bool, IOAttrs('v')]

    # Current account tag (good time to check if it has changed).
    tag: Annotated[str, IOAttrs('t')]
