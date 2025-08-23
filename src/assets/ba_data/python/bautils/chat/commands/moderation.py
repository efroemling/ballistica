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
from bautils.tools import Color


@register_command
class Kick(ServerCommand):
    """/kick <client_id> [ban_time=60sec] [reason]"""

    @override
    def on_command_call(self) -> None:

        user = self.get_session_player(self.client_id)

        match self.arguments:

            case []:
                raise NoArgumentsProvidedError(
                    "Please provide neccesary arguments."
                )

            case [client_id, ban_time, *reason] if (
                client_id.isdigit() and ban_time.isdigit()
            ):
                _id = self.filter_client_id(client_id)
                target = self.get_session_player(_id)
                bs.broadcastmessage(
                    f"{user.getname()} kicked {target.getname()} "
                    f"for {ban_time} seconds. Reason: {' '.join(reason)}.",
                    color=Color.GREEN.float,
                    transient=True,
                    clients=None,
                )
                self._disconnect(
                    client_id=_id, ban_time=int(ban_time), reason=reason
                )

            case [client_id, *reason] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                target = self.get_session_player(_id)
                bs.broadcastmessage(
                    f"{user.getname()} kicked {target.getname()}. "
                    f"Reason: {' '.join(reason)}.",
                    color=Color.GREEN.float,
                    transient=True,
                    clients=None,
                )
                self._disconnect(client_id=_id, reason=reason)

            case _:
                raise IncorrectUsageError

    def _disconnect(
        self,
        client_id: int,
        ban_time: int = 60 * 5,
        reason: list[str] | None = None,
    ) -> None:

        if ban_time <= 0:
            raise ValueError("Ban time must be a positive number.")

        reason_str = " ".join(reason) if reason else "Reason not provided"
        client = self.get_session_player(client_id)

        bs.disconnect_client(client_id=client_id, ban_time=ban_time)


@register_command
class Remove(ServerCommand):
    """/remove <client_id> | all or /rm <client_id> | all"""

    aliases = ["rm"]

    @override
    def on_command_call(self) -> None:

        user = self.get_session_player(self.client_id)

        match self.arguments:

            case []:
                raise NoArgumentsProvidedError(
                    "Please provide neccesary arguments."
                )

            case ["all"]:
                roaster = bs.get_game_roster()
                username = user.getname()
                for client in roaster:
                    try:
                        self._remove_player(client["client_id"])
                    except:
                        continue  # should skip host n players who dint join da game
                bs.broadcastmessage(
                    f"{username} removed all players.",
                    color=Color.GREEN.float,
                    transient=True,
                    clients=None,
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                target = self.get_session_player(_id)
                bs.broadcastmessage(
                    f"{user.getname()} removed {target.getname()}.",
                    color=Color.GREEN.float,
                    transient=True,
                    clients=None,
                )
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
