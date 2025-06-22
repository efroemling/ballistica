# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

from __future__ import annotations
from abc import ABC, abstractmethod


class CommandManager:
    """Factory Managing server commands."""

    commands: dict[str, ServerCommand] = {}

    @classmethod
    def add_command(cls, command: ServerCommand) -> None:
        """Add a command to a command factory.

        Args:
            command (ServerCommand): Command class must inherit this
            class to execute.
        """
        # Get the class name if name is not provided
        if command.name is None:
            command.name = command.__class__.__name__

        cls.commands[command.command_prefix() + command.name.upper()] = command
        for alias in command.aliases:
            cls.commands[command.command_prefix() + alias.upper()] = command

    @classmethod
    def listen(cls, msg: str, client_id: int) -> str | None:
        """A custom hook connecting commands to the game chat.

        Args:
            msg (str): message content
            client_id (int): special ID of a player

        Returns:
            str | None: Returns back original message, ignores if None.
        """

        # get the beggining of the of the message and get command.
        # capitalize it to match all cases.
        cmd = cls.commands.get(msg.split()[0].upper())

        if cmd is not None:
            # set some attributes for abtraction
            cmd.client_id = client_id
            cmd.message = msg

            cmd.on_command_call()

            if not cmd.return_message():
                return None
        return msg


class ServerCommand(ABC):
    """
    ServerCommand is prototype command which should be inherited by all
    other commands. It provides additional functionality and makes it easy
    to implement new commands.

    Example:

    class MyCommand(ServerCommand):
        def __init__(self) -> None:
            self.wlm_message = 'welcome'

        def on_command_call() -> None:
            print(f'{self.wlm_message} {self.client_id}')

    """

    name: str | None = None
    aliases: list[str] = []
    message: str = ""
    client_id: int = -999

    @abstractmethod
    def on_command_call(self) -> None:
        """This method gets called out when command is called."""

    @classmethod
    def register_command(cls) -> None:
        """Register the command to the server."""
        CommandManager.add_command(cls())

    def return_message(self) -> bool:
        """Method to overwrite to make message disappear.

        Returns:
            bool: Returns True to display message by default.
        """
        return True

    def command_prefix(self) -> str:
        """Method to overwrite default command prefix.

        Returns:
            str: Returns '/' as default prefix.
        """
        return "/"
