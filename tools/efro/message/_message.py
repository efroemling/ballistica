# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from dataclasses import dataclass
from enum import Enum

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


class UnregisteredMessageIDError(Exception):
    """A message or response id is not covered by our protocol."""


class Message:
    """Base class for messages."""

    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        """Return all Response types this Message can return when sent.

        The default implementation specifies a None return type.
        """
        return [None]


class Response:
    """Base class for responses to messages."""


class SysResponse:
    """Base class for system-responses to messages.

    These are only sent/handled by the messaging system itself;
    users of the api never see them.
    """

    def set_local_exception(self, exc: Exception) -> None:
        """Attach a local exception to facilitate better logging/handling.

        Be aware that this data does not get serialized and only
        exists on the local object.
        """
        setattr(self, '_sr_local_exception', exc)

    def get_local_exception(self) -> Exception | None:
        """Fetch a local attached exception."""
        value = getattr(self, '_sr_local_exception', None)
        assert isinstance(value, Exception | None)
        return value


# Some standard response types:


@ioprepped
@dataclass
class ErrorSysResponse(SysResponse):
    """SysResponse saying some error has occurred for the send.

    This generally results in an Exception being raised for the caller.
    """

    class ErrorType(Enum):
        """Type of error that occurred while sending a message."""

        REMOTE = 0
        REMOTE_CLEAN = 1
        LOCAL = 2
        COMMUNICATION = 3
        REMOTE_COMMUNICATION = 4

    error_message: Annotated[str, IOAttrs('m')]
    error_type: Annotated[ErrorType, IOAttrs('e')] = ErrorType.REMOTE


@ioprepped
@dataclass
class EmptySysResponse(SysResponse):
    """The response equivalent of None."""


# TODO: could allow handlers to deal in raw values for these
# types similar to how we allow None in place of EmptySysResponse.
# Though not sure if they are widely used enough to warrant the
# extra code complexity.
@ioprepped
@dataclass
class BoolResponse(Response):
    """A simple bool value response."""

    value: Annotated[bool, IOAttrs('v')]


@ioprepped
@dataclass
class StringResponse(Response):
    """A simple string value response."""

    value: Annotated[str, IOAttrs('v')]
