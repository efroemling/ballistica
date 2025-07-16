# Released under the MIT License. See LICENSE for details.
#
"""A command module handing moderation commands."""

from __future__ import annotations
from typing import override

import bascenev1 as bs
import babase as ba

from bautils.chat import ServerCommand, register_command


@register_command
class Quit(ServerCommand):
    """/quit or /exit"""

    aliases = ["exit"]

    @override
    def on_command_call(self) -> None:
        ba.quit()


@register_command
class End(ServerCommand):
    """/end"""

    @override
    def on_command_call(self) -> None:
        activity = bs.get_foreground_host_activity()
        assert activity is not None

        with activity.context:
            # type checking
            if isinstance(activity, bs.GameActivity):
                activity.end_game()


@register_command
class Pause(ServerCommand):
    """/pause"""

    @override
    def on_command_call(self) -> None:

        activity = bs.get_foreground_host_activity()
        assert activity is not None

        with activity.context:
            if activity.globalsnode.paused:
                return

            activity.globalsnode.paused = True
            activity.paused_text = bs.NodeActor(
                bs.newnode(
                    "text",
                    attrs={
                        "text": bs.Lstr(resource="pausedByHostText"),
                        "client_only": True,
                        "flatness": 1.0,
                        "h_align": "center",
                    },
                )
            )


@register_command
class Resume(ServerCommand):
    """/resume or /play"""

    aliases = ["play"]

    @override
    def on_command_call(self) -> None:

        activity = bs.get_foreground_host_activity()
        assert activity is not None

        if not activity.globalsnode.paused:
            return

        activity.globalsnode.paused = False
        activity.paused_text = None


@register_command
class EpicMode(ServerCommand):
    """/epic, /epicmode /slow /sm"""

    aliases = ["epic", "slow", "sm"]

    def __init__(self) -> None:
        self.epic_mode_enabled = False

    @override
    def on_command_call(self) -> None:

        activity = bs.get_foreground_host_activity()
        assert activity is not None
        self.epic_mode_enabled = activity.globalsnode.slow_motion

        if self.epic_mode_enabled:
            activity.globalsnode.slow_motion = False
            self.epic_mode_enabled = False
        else:
            activity.globalsnode.slow_motion = True
            self.epic_mode_enabled = False


# @register_command
# class Tint(ServerCommand):
#     """"/tint <r: float> <g:float> <b:float>"""

#     def __init__(self) -> None:
#         self.original_tint: tuple[float, float, float] | None = None

#     @override
#     def on_command_call(self) -> None:

#         match self.arguments:

#             case [r, g, b] if r.isdigit() and g.isdigit() and b.isdigit():
#                 # convert them into float values
#                 r, g, b = float(r), float(g), float(b)
#                 activity = bs.get_foreground_host_activity()

#                 if self.original_tint is None:
#                     self.original_tint = activity.globalsnode.tint
#                     activity.globalsnode.tint = (r, g, b)
#                 else:
#                     activity.globalsnode.tint = self.original_tint
#                     self.original_tint = None

#             case _:
#                 raise ValueError("Please provide correct numerical values.")

# @register_command
# class NightMode(ServerCommand):
#     """/nv or /nightmode"""

#     def __init__(self) -> None:
#         self.nv_tint = (0.5, 0.5, 1.0)
#         self.nv_ambient = (1.5, 1.5, 1.5)

#     @override
#     def on_command_call(self) -> None:
#         activity = bs.get_foreground_host_activity()
#         if self.is_close(activity.globalsnode.tint, self.nv_tint):
#             activity.globalsnode.tint = (1, 1, 1)
#             activity.globalsnode.ambient_color = (1, 1, 1)
#         else:
#             activity.globalsnode.tint = self.nv_tint
#             activity.globalsnode.ambient_color = self.nv_ambient

#     def is_close(
#               self, a: tuple[float, float, float],
#                     b: tuple[float, float, float],
#                     tol=1e-5
#           ) -> bool:
#         """Compare two triple float tupples with eath other

#         Args:
#             a (tuple[float, float, float]): first tuple
#             b (tuple[float, float, float]): second tuple
#             tol (_type_, optional): precision. Defaults to 1e-5.

#         Returns:
#             bool: floating tuples are close
#         """
#         return all(abs(x - y) < tol for x, y in zip(a, b))
