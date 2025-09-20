# Released under the MIT License. See LICENSE for details.
#
"""BombSquad specific bits."""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override

from efro.dataclassio import ioprepped, IOAttrs
from efro.message import Message, Response

from bacommon.bs._displayitem import DisplayItemWrapper
from bacommon.bs._clienteffect import ClientEffect
from bacommon.bs._clouddialog import CloudDialogAction, CloudDialogWrapper
from bacommon.bs._chest import ClassicChestAppearance


@ioprepped
@dataclass
class ChestActionMessage(Message):
    """Request action about a chest."""

    class Action(Enum):
        """Types of actions we can request."""

        # Unlocking (for free or with tokens).
        UNLOCK = 'u'

        # Watched an ad to reduce wait.
        AD = 'ad'

    action: Annotated[Action, IOAttrs('a')]

    # Tokens we are paying (only applies to unlock).
    token_payment: Annotated[int, IOAttrs('t')]

    chest_id: Annotated[str, IOAttrs('i')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ChestActionResponse]


@ioprepped
@dataclass
class ChestActionResponse(Response):
    """Here's the results of that action you asked for, boss."""

    # Tokens that were actually charged.
    tokens_charged: Annotated[int, IOAttrs('t')] = 0

    # If present, signifies the chest has been opened and we should show
    # the user this stuff that was in it.
    contents: Annotated[list[DisplayItemWrapper] | None, IOAttrs('c')] = None

    # If contents are present, which of the chest's prize-sets they
    # represent.
    prizeindex: Annotated[int, IOAttrs('i')] = 0

    # Printable error if something goes wrong.
    error: Annotated[str | None, IOAttrs('e')] = None

    # Printable warning. Shown in orange with an error sound. Does not
    # mean the action failed; only that there's something to tell the
    # users such as 'It looks like you are faking ad views; stop it or
    # you won't have ad options anymore.'
    warning: Annotated[str | None, IOAttrs('w', store_default=False)] = None

    # Printable success message. Shown in green with a cash-register
    # sound. Can be used for things like successful wait reductions via
    # ad views. Used in builds earlier than 22311; can remove once
    # 22311+ is ubiquitous.
    success_msg: Annotated[str | None, IOAttrs('s', store_default=False)] = None

    # Effects to show on the client. Replaces warning and success_msg in
    # build 22311 or newer.
    effects: Annotated[
        list[ClientEffect], IOAttrs('fx', store_default=False)
    ] = field(default_factory=list)


@ioprepped
@dataclass
class CloudDialogActionMessage(Message):
    """Do something to a client ui."""

    id: Annotated[str, IOAttrs('i')]
    action: Annotated[CloudDialogAction, IOAttrs('a')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [CloudDialogActionResponse]


@ioprepped
@dataclass
class CloudDialogActionResponse(Response):
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

    effects: Annotated[list[ClientEffect], IOAttrs('fx')]


@ioprepped
@dataclass
class GetClassicPurchasesMessage(Message):
    """Asking for current account's classic purchases."""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [GetClassicPurchasesResponse]


@ioprepped
@dataclass
class GetClassicPurchasesResponse(Response):
    """Here's those classic purchases ya asked for boss."""

    purchases: Annotated[set[str], IOAttrs('p')]


@ioprepped
@dataclass
class GlobalProfileCheckMessage(Message):
    """Is this global profile name available?"""

    name: Annotated[str, IOAttrs('n')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [GlobalProfileCheckResponse]


@ioprepped
@dataclass
class GlobalProfileCheckResponse(Response):
    """Here's that profile check ya asked for boss."""

    available: Annotated[bool, IOAttrs('a')]
    ticket_cost: Annotated[int, IOAttrs('tc')]


@ioprepped
@dataclass
class InboxRequestMessage(Message):
    """Message requesting our inbox."""

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [InboxRequestResponse]


@ioprepped
@dataclass
class InboxRequestResponse(Response):
    """Here's that inbox contents you asked for, boss."""

    wrappers: Annotated[list[CloudDialogWrapper], IOAttrs('w')]

    # Printable error if something goes wrong.
    error: Annotated[str | None, IOAttrs('e')] = None


@ioprepped
@dataclass
class LegacyRequest(Message):
    """A generic request for the legacy master server."""

    request: Annotated[str, IOAttrs('r')]
    request_type: Annotated[str, IOAttrs('t')]
    user_agent_string: Annotated[str, IOAttrs('u')]
    data: Annotated[str, IOAttrs('d')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [LegacyResponse]


@ioprepped
@dataclass
class LegacyResponse(Response):
    """Response for generic legacy request."""

    data: Annotated[str | None, IOAttrs('d')]
    zipped: Annotated[bool, IOAttrs('z')]


@ioprepped
@dataclass
class ChestInfoMessage(Message):
    """Request info about a chest."""

    chest_id: Annotated[str, IOAttrs('i')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ChestInfoResponse]


@ioprepped
@dataclass
class ChestInfoResponse(Response):
    """Here's that chest info you asked for, boss."""

    @dataclass
    class Chest:
        """A lovely chest."""

        @dataclass
        class PrizeSet:
            """A possible set of prizes for this chest."""

            weight: Annotated[float, IOAttrs('w')]
            contents: Annotated[list[DisplayItemWrapper], IOAttrs('c')]

        appearance: Annotated[
            ClassicChestAppearance,
            IOAttrs('a', enum_fallback=ClassicChestAppearance.UNKNOWN),
        ]

        # How much it costs to unlock *now*.
        unlock_tokens: Annotated[int, IOAttrs('tk')]

        # When it unlocks on its own.
        unlock_time: Annotated[datetime.datetime, IOAttrs('t')]

        # Possible prizes we contain.
        prizesets: Annotated[list[PrizeSet], IOAttrs('p')]

        # Are ads allowed now?
        ad_allow: Annotated[bool, IOAttrs('aa')]

    chest: Annotated[Chest | None, IOAttrs('c')]
    user_tokens: Annotated[int | None, IOAttrs('t')]


@ioprepped
@dataclass
class PrivatePartyMessage(Message):
    """Message asking about info we need for private-party UI."""

    need_datacode: Annotated[bool, IOAttrs('d')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [PrivatePartyResponse]


@ioprepped
@dataclass
class PrivatePartyResponse(Response):
    """Here's that private party UI info you asked for, boss."""

    success: Annotated[bool, IOAttrs('s')]
    tokens: Annotated[int, IOAttrs('t')]
    gold_pass: Annotated[bool, IOAttrs('g')]
    datacode: Annotated[str | None, IOAttrs('d')]


@ioprepped
@dataclass
class ScoreSubmitMessage(Message):
    """Let the server know we got some score in something."""

    score_token: Annotated[str, IOAttrs('t')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [ScoreSubmitResponse]


@ioprepped
@dataclass
class ScoreSubmitResponse(Response):
    """Did something to that inbox entry, boss."""

    # Things we should show on our end.
    effects: Annotated[list[ClientEffect], IOAttrs('fx')]


@ioprepped
@dataclass
class SendInfoMessage(Message):
    """User is using the send-info function."""

    description: Annotated[str, IOAttrs('c')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [SendInfoResponse]


@ioprepped
@dataclass
class SendInfoResponse(Response):
    """Response to sending info to the server."""

    handled: Annotated[bool, IOAttrs('v')]
    message: Annotated[str | None, IOAttrs('m', store_default=False)] = None
    effects: Annotated[
        list[ClientEffect], IOAttrs('e', store_default=False)
    ] = field(default_factory=list)
    legacy_code: Annotated[str | None, IOAttrs('l', store_default=False)] = None
