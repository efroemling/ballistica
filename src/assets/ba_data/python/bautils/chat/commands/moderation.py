# Released under the MIT License. See LICENSE for details.
#
"""A command module handing moderation commands."""

from __future__ import annotations
from typing import override

import bascenev1 as bs

from bautils.chat import (
    ServerCommand,
    register_command,
    NoArgumentsProvidedError,
    IncorrectUsageError,
    InvalidClientIDError,
)


@register_command
class Kick(ServerCommand):
    """/kick <client_id> [ban_time=60sec] [reason]"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                raise NoArgumentsProvidedError(
                    "Please provide neccesary arguments."
                )

            case [client_id, ban_time, *reason] if (
                client_id.isdigit() and ban_time.isdigit()
            ):
                _id = self.filter_client_id(client_id)
                self._disconnect(
                    client_id=_id, ban_time=int(ban_time), reason=reason
                )

            case [client_id, *reason] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                self._disconnect(client_id=_id, reason=reason)

            case _:
                raise IncorrectUsageError

    def _disconnect(
        self,
        client_id: int,
        ban_time: int = 60 * 5,
        reason: list[str] | None = None,
    ) -> None:

        if client_id == self.client_id:
            raise InvalidClientIDError("You can't kick yourself.")

        if ban_time <= 0:
            raise ValueError("Ban time must be a positive number.")

        reason_str = " ".join(reason) if reason else "Reason not provided"
        client = self.get_session_player(client_id)

        kick_msg = f"Kicking {client.getname()}."
        if reason:
            kick_msg += f" Reason: {reason_str}"

        bs.broadcastmessage(kick_msg)
        bs.disconnect_client(client_id=client_id, ban_time=ban_time)


@register_command
class Remove(ServerCommand):
    """/remove <client_id> | all or /rm <client_id> | all"""

    aliases = ["rm"]

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                raise NoArgumentsProvidedError(
                    "Please provide neccesary arguments."
                )

            case ["all"]:
                roaster = bs.get_game_roster()
                for client in roaster:
                    self._remove_player(client["client_id"])

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                self._remove_player(_id)

            case _:
                raise IncorrectUsageError

    def _remove_player(self, client_id: int) -> None:
        s_player = self.get_session_player(client_id)
        s_player.remove_from_game()


@register_command
class Ban(ServerCommand):
    """/ban"""

    @override
    def on_command_call(self) -> None:
        raise NotImplementedError
