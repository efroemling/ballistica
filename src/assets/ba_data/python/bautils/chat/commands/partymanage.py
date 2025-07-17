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
from bautils.tools.enums import Color


@register_command
class Maxplayers(ServerCommand):
    """/maxplayers <size> or /partysize <size>"""

    aliases = ["mp", "partysize"]

    @override
    def on_command_call(self) -> None:

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
                    f"Max players size set to {size}",
                    color=Color.CYAN.float,
                )

            case _:
                raise IncorrectUsageError


@register_command
class Party(ServerCommand):
    """/party <public | private>"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case ["public"] | ["pub"]:
                bs.set_public_party_enabled(True)
                bs.broadcastmessage(
                    "Party mode set to Public",
                    transient=True,
                    color=Color.CYAN.float,
                )

            case ["private"] | ["pvt"]:
                bs.set_public_party_enabled(False)
                bs.broadcastmessage(
                    "Party mode set to Private",
                    transient=True,
                    color=Color.CYAN.float,
                )

            case _:
                raise IncorrectUsageError
