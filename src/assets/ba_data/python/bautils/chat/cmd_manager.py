# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

from __future__ import annotations

from typing import TYPE_CHECKING
import bascenev1 as bs

if TYPE_CHECKING:
    from .server_command import ServerCommand


class CommandManager:
    """Factory Managing server commands."""

    commands: dict[str, ServerCommand] = {}

    @classmethod
    def add_command(cls, command: ServerCommand) -> None:
        """
        Add a command to a command factory.

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
        """
        A custom hook connecting commands to the game chat.

        Args:
            msg (str): message content
            client_id (int): special ID of a player

        Returns:
            str | None: Returns back original message, ignores if None.
        """

        # get the beggining of the of the message and get command.
        # capitalize it to match all cases.
        command = cls.commands.get(msg.split()[0].upper())

        if command is not None:
            # set some attributes for abtraction
            command.client_id = client_id
            command.message = msg

            if command.admin_authentication():
                # check admins from loaded config file.
                if command.is_admin:
                    command()

                else:
                    bs.broadcastmessage(
                        "❌ Access Denied: Admins only!",
                        clients=[client_id],
                        transient=True,
                        color=(1, 0, 0),
                    )
            else:
                command()

            if not command.return_message():
                return None  # commands wont show up in chatbox
        return msg  # /<invalid_command_name> will be visible in chatbox
