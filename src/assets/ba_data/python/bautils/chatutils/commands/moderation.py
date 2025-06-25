# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

from __future__ import annotations
from typing import override

import bascenev1 as bs
from bautils.chatutils import ServerCommand, register_command


@register_command
class Kick(ServerCommand):
    """/kick <client_id> [ban_time=60sec] [reason]"""

    @override
    def on_command_call(self) -> None:
        match self.arguments:

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
                raise ValueError(
                    f"Invalid arguments: {" ".join(self.arguments)}"
                )

    def _disconnect(
        self,
        client_id: int,
        ban_time: int = 60 * 5,
        reason: list[str] | None = None,
    ) -> None:

        if client_id == self.client_id:
            raise ValueError("You can't kick yourself.")

        if ban_time <= 0:
            raise ValueError("Ban time must be a positive number.")

        reason_str = " ".join(reason) if reason else "Reason not provided"
        client = self.get_session_player(client_id)

        kick_msg = f"Kicking {client.getname()}."
        if reason:
            kick_msg += f" Reason: {reason_str}"

        bs.broadcastmessage(kick_msg)
        bs.disconnect_client(client_id=client_id, ban_time=ban_time)
