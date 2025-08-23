# Released under the MIT License. See LICENSE for details.
#
"""A command module handing user commands."""

from __future__ import annotations
from typing import override

import bascenev1 as bs
from bautils.chat import (
    ServerCommand,
    register_command,
    NoArgumentsProvidedError,
    IncorrectUsageError,
)
from bautils.tools import Color


# TODO: make it look more pretty, make characters icon appear in list
@register_command
class List(ServerCommand):
    """/l, /list or /clients"""

    aliases = ["l", "clients"]

    @override
    def on_command_call(self) -> None:

        # Build and broadcast a clean ASCII player list table.
        header = "{0:^4} | {1:<16} | {2:^8}"
        separator = "-" * 50

        lines = []
        lines.append(separator)
        lines.append(header.format("No.", "Name", "ClientID"))
        lines.append(separator)

        session = bs.get_foreground_host_session()
        assert session is not None

        for index, player in enumerate(session.sessionplayers, start=1):
            lines.append(
                header.format(
                    index,
                    player.getname(icon=True),
                    player.inputdevice.client_id,
                )
            )

        lines.append(separator)
        _list = "\n".join(lines)

        bs.broadcastmessage(_list, transient=True, clients=[self.client_id])

    @override
    def admin_authentication(self) -> bool:
        return False


@register_command
class Info(ServerCommand):
    """/info <client_id> — show the target client's player profiles."""

    aliases: list[str] = ["gp", "profiles"]

    @override
    def on_command_call(self) -> None:
        # Follow project style: use self.arguments with match/case
        match self.arguments:
            case []:
                # No args provided
                raise NoArgumentsProvidedError(
                    "Please provide neccesary arguments."
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                target = self.get_session_player(_id)

                # Build display message with profiles on that input device.
                try:
                    profiles = target.inputdevice.get_player_profiles()
                except Exception:
                    profiles = []

                header = f"{'Sr.no':<9} |    {'Name':<12}\n" + ("_" * 25) + "\n"
                lines = [header]
                for i, profile in enumerate(profiles, start=1):
                    try:
                        lines.append(f"{i:<9} {profile:<12}\n")
                    except Exception:
                        # Skip any odd encodings gracefully
                        continue

                message = (
                    "".join(lines) if len(lines) > 1 else "No profiles found."
                )
                bs.broadcastmessage(
                    message, transient=True, clients=[self.client_id]
                )

            case _:
                # Wrong usage/signature
                raise IncorrectUsageError

    @override
    def admin_authentication(self) -> bool:
        # Let anyone use /info
        return False
