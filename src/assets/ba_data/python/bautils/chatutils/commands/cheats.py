# Released under the MIT License. See LICENSE for details.
#
"""A command module handing cheat commands."""

from __future__ import annotations
from typing import override

# import bascenev1 as bs
# import babase as ba
from bautils.chatutils import ServerCommand, register_command


# activity = bs.get_foreground_host_activity()

#     try:
#         target = msg.split(" ")[1]

#         if target == "all":
#             for player in activity.players:
#                 with activity.context:
#                     player.actor.equip_boxing_gloves()
#         else:
#             target_id = int(target)
#             entity = get_entity(target_id)
#             spaz = get_player(entity)

#             try:
#                 with activity.context:
#                     spaz.actor.equip_boxing_gloves()
#             except Exception as e:
#                 print(e)
#     except Exception as e:
#         print(e)


@register_command
class Gloves(ServerCommand):
    """/gloves or /gloves <client_id>"""

    @override
    def on_command_call(self) -> None:
        raise NotImplementedError


@register_command
class Sheild(ServerCommand):
    """/shield or /shield <client_id>"""

    @override
    def on_command_call(self) -> None:
        raise NotImplementedError


@register_command
class Freeze(ServerCommand):
    """/freeze or /freeze <client_id>"""

    @override
    def on_command_call(self) -> None:
        raise NotImplementedError
