# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

# ba_meta require api 9

from .server_command import CommandManager, ServerCommand, register_command

__all__ = [
    "CommandManager",
    "ServerCommand",
    "register_command"
]
