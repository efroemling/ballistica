# Released under the MIT License. See LICENSE for details.
#
"""A command module handing moderation commands."""

from __future__ import annotations
from typing import override

import bascenev1 as bs

from bautils.chatutils import (
    ServerCommand,
    register_command,
    NoArgumentsProvidedError,
    IncorrectUsageError,
)


@register_command
class Maxplayers(ServerCommand):
    """/maxplayers <size> or /partysize <size>"""

    aliases = ["mp", "partysize"]

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                raise NoArgumentsProvidedError(
                    "Please provide neccesary arguments."
                )

            case [size] if size.isdigit():

                activity = bs.get_foreground_host_session()
                assert activity is not None

                # set max players in activity as well as party
                activity.max_players = int(size)
                bs.set_public_party_max_size(int(size))
                bs.broadcastmessage(f"Max players size set to {size}")

            case _:
                raise IncorrectUsageError


@register_command
class Party(ServerCommand):
    """/party <public | private>"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                raise NoArgumentsProvidedError(
                    "Please provide neccesary arguments."
                )

            case ["public"]:
                bs.set_public_party_enabled(True)
                bs.broadcastmessage("Party mode set to Public")

            case ["private"]:
                bs.set_public_party_enabled(False)
                bs.broadcastmessage("Party mode set to Private")

            case _:
                raise IncorrectUsageError
