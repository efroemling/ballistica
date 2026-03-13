# Released under the MIT License. See LICENSE for details.
#
"""Simple cloud-defined UIs for things like notifications.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType
from efro.message import Message, Response

import bacommon.clienteffect as clfx


class CloudDialogTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    BASIC = 'b'


class CloudDialog(IOMultiType[CloudDialogTypeID]):
    """Small self-contained ui bit provided by the cloud.

    These take care of updating and/or dismissing themselves based on
    user input. Useful for things such as inbox messages. For more
    complex UI construction, look at :mod:`bacommon.docui`.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudDialogTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: CloudDialogTypeID) -> type[CloudDialog]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = CloudDialogTypeID

        if type_id is t.UNKNOWN:
            return Unknown

        if type_id is t.BASIC:
            from bacommon.clouddialog.basic import BasicCloudDialog

            return BasicCloudDialog

        # Make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> CloudDialog:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return Unknown()


@ioprepped
@dataclass
class Unknown(CloudDialog):
    """Fallback type for unrecognized entries."""

    @override
    @classmethod
    def get_type_id(cls) -> CloudDialogTypeID:
        return CloudDialogTypeID.UNKNOWN


@ioprepped
@dataclass
class Wrapper:
    """Wrapper for a CloudDialog and its common data."""

    id: Annotated[str, IOAttrs('i')]
    createtime: Annotated[datetime.datetime, IOAttrs('c')]
    ui: Annotated[CloudDialog, IOAttrs('e')]


class Action(Enum):
    """Types of actions we can run."""

    BUTTON_PRESS_POSITIVE = 'p'
    BUTTON_PRESS_NEGATIVE = 'n'


@ioprepped
@dataclass
class ActionMessage(Message):
    """Do something to a client ui."""

    id: Annotated[str, IOAttrs('i')]
    action: Annotated[Action, IOAttrs('a')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ActionResponse]


@ioprepped
@dataclass
class ActionResponse(Response):
    """Did something to that inbox entry, boss."""

    class ErrorType(Enum):
        """Types of errors that may have occurred."""

        # Probably a future error type we don't recognize.
        UNKNOWN = 'u'

        # Something went wrong on the server, but specifics are not
        # relevant.
        INTERNAL = 'i'

        # The entry expired on the server. In various cases such as 'ok'
        # buttons this can generally be ignored.
        EXPIRED = 'e'

    error_type: Annotated[
        ErrorType | None, IOAttrs('et', enum_fallback=ErrorType.UNKNOWN)
    ]

    # User facing error message in the case of errors.
    error_message: Annotated[str | None, IOAttrs('em')]

    effects: Annotated[list[clfx.Effect], IOAttrs('fx')]
