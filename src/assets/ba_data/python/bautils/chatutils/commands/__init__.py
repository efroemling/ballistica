# Released under the MIT License. See LICENSE for details.
#
"""All Server commands are defined in this directory."""

# ba_meta require api 9

import bascenev1 as bs
from .moderation import (
    End,
)

__commands__ = [
    End,
]


# ba_meta export plugin
class RegisterCommands(bs.Plugin):
    """Register all commands in this module."""

    def on_app_running(self) -> None:
        for command in __commands__:
            command.register_command()
