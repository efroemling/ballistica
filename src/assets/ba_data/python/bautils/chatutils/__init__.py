# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

# ba_meta require api 9

from .cmd_manager import CommandManager
from .server_command import ServerCommand, register_command
from .errors import (
    IncorrectUsageError,
    NoArgumentsProvidedError,
    IncorrectArgumentsError,
    InvalidClientIDError,
    ActorNotFoundError,
)


__all__ = [
    "CommandManager",
    "ServerCommand",
    "register_command",
    "IncorrectUsageError",
    "NoArgumentsProvidedError",
    "IncorrectArgumentsError",
    "InvalidClientIDError",
    "ActorNotFoundError",
]
