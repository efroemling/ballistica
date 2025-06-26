# Released under the MIT License. See LICENSE for details.
#
"""A command module handing moderation commands."""

from __future__ import annotations
from typing import override

# import bascenev1 as bs
# import babase as ba
from bautils.chatutils import ServerCommand, register_command


@register_command
class Maxplayers(ServerCommand):
    """/maxplayers <size> or /partysize <size>"""

    aliases = ["mp", "partysize"]

    @override
    def on_command_call(self) -> None:
        raise NotImplementedError
