# Released under the MIT License. See LICENSE for details.
#
"""BombSquad specific bits."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Annotated, override

from efro.dataclassio import ioprepped, IOAttrs
from efro.message import Message, Response

import bacommon.displayitem as ditm
import bacommon.clouddialog as cdlg
import bacommon.clienteffect as clfx
from bacommon.classic._chest import ClassicChestAppearance


@ioprepped
@dataclass
class GetClassicLeaguePresidentButtonInfoMessage(Message):
    """Curious who is president of my league?.."""

    season: Annotated[str | None, IOAttrs('s')]

    @override
    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [GetClassicLeaguePresidentButtonInfoResponse]


@ioprepped
@dataclass
class GetClassicLeaguePresidentButtonInfoResponse(Response):
    """Here's that info about the president you asked for boss."""

    # Lstr for the name shown on the button.
    name: Annotated[str | None, IOAttrs('n')]


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

    wrappers: Annotated[list[cdlg.Wrapper], IOAttrs('w')]

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
            contents: Annotated[list[ditm.Wrapper], IOAttrs('c')]

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
    effects: Annotated[list[clfx.Effect], IOAttrs('fx')]


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
    effects: Annotated[list[clfx.Effect], IOAttrs('e', store_default=False)] = (
        field(default_factory=list)
    )
    legacy_code: Annotated[str | None, IOAttrs('l', store_default=False)] = None
