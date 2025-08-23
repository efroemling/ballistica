# Released under the MIT License. See LICENSE for details.
#
"""A command module handing moderation commands."""

from __future__ import annotations
from typing import override

import bascenev1 as bs

from bautils.chat import (
    ServerCommand,
    register_command,
    IncorrectUsageError,
)
from bautils.tools import Color


@register_command
class Maxplayers(ServerCommand):
    """/maxplayers <size> or /partysize <size>"""

    aliases = ["mp", "partysize"]

    @override
    def on_command_call(self) -> None:

        user = self.get_session_player(self.client_id)
        match self.arguments:

            case [size] if size.isdigit():
                size_int = int(size)
                if not 2 <= size_int <= 99:
                    bs.broadcastmessage(
                        "Max players size must be between 2 and 99.",
                        transient=True,
                        clients=[self.client_id],
                        color=Color.RED.float,
                    )
                    return

                activity = bs.get_foreground_host_session()
                assert activity is not None

                # set max players in activity as well as party
                activity.max_players = size_int
                bs.set_public_party_max_size(size_int)
                bs.broadcastmessage(
                    f"{user.getname()} set max players to {size_int}.",
                    color=Color.GREEN.float,
                    transient=True,
                    clients=None,
                )

            case _:
                raise IncorrectUsageError


@register_command
class Party(ServerCommand):
    """/party <public | private>"""

    @override
    def on_command_call(self) -> None:

        user = self.get_session_player(self.client_id)
        match self.arguments:

            case ["public"] | ["pub"]:
                bs.set_public_party_enabled(True)
                bs.broadcastmessage(
                    f"{user.getname()} set party mode to Public",
                    transient=True,
                    color=Color.GREEN.float,
                    clients=None,
                )

            case ["private"] | ["pvt"]:
                bs.set_public_party_enabled(False)
                bs.broadcastmessage(
                    f"{user.getname()} set party mode to Private",
                    transient=True,
                    color=Color.GREEN.float,
                    clients=None,
                )

            case _:
                raise IncorrectUsageError
