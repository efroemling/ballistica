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
    def get_response_types(cls) -> list[type[Response]]:
        """Return all message types this Message can result in when sent.

        The default implementation specifies EmptyResponse, so messages with
        no particular response needs can leave this untouched.
        Note that ErrorMessage is handled as a special case and does not
        need to be specified here.
        """
        return [EmptyResponse]


class Response:
    """Base class for responses to messages."""


# Some standard response types:


@ioprepped
@dataclass
class ErrorResponse(Response):
    """Message saying some error has occurred on the other end.

    This type is unique in that it is not returned to the user; it
    instead results in a local exception being raised.
    """

    class ErrorType(Enum):
        """Type of error that occurred in remote message handling."""
        OTHER = 0
        CLEAN = 1
        LOCAL = 2
        COMMUNICATION = 3

    error_message: Annotated[str, IOAttrs('m')]
    error_type: Annotated[ErrorType, IOAttrs('e')] = ErrorType.OTHER


@ioprepped
@dataclass
class EmptyResponse(Response):
    """The response equivalent of None."""


# TODO: could allow handlers to deal in raw values for these
# types similar to how we allow None in place of EmptyResponse.
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
