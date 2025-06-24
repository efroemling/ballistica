# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

from __future__ import annotations

from typing import TYPE_CHECKING

from abc import ABC, abstractmethod
from contextlib import contextmanager

import bascenev1 as bs
import babase

if TYPE_CHECKING:
    from bacommon.servermanager import ServerConfig


def register_command(cls: type[ServerCommand]) -> type[ServerCommand]:
    """
    Decorator to register a ServerCommand subclass into the registry.

    Args:
        cls: A subclass of ServerCommand to be registered.

    Returns:
        The class itself after registration.

    Example:
        @register_command
        class MyCommand(ServerCommand):
            ...
    """
    if not issubclass(cls, ServerCommand):
        raise TypeError("@register_command must be used on ServerCommand subclasses")

    CommandManager.add_command(cls())
    return cls


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
                if command.is_admin:
                    command()

                else:
                    bs.broadcastmessage(
                        "❌ Access Denied: Admins only!",
                        clients=[client_id],
                        transient=True,
                    )
            else:
                command()

            if not command.return_message():
                return None
        return msg


class ServerCommand(ABC):
    """
    ServerCommand is prototype command which should be inherited by all
    other commands. It provides additional functionality and makes it easy
    to implement new commands.

    Example:

    ```
    from bautils.chatutils.server_command import ServerCommand

    class MyCommand(ServerCommand):
        def __init__(self) -> None:
            self.wlm_message = 'welcome'

        def on_command_call() -> None:
            print(f'{self.wlm_message} {self.client_id}')

    MyCommand.register_command()
    ```

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
        """
        Method to overwrite to make message disappear.

        Returns:
            bool: Returns True to display message by default.
        """
        return True

    def command_prefix(self) -> str:
        """
        Method to overwrite default command prefix.

        Returns:
            str: Returns '/' as default prefix.
        """
        return "/"

    def admin_authentication(self) -> bool:
        """
        Method to overwrite if command is used by admins only.

        Returns:
            bool: Returns True to authenticate by default.
        """
        return True

    @property
    def is_admin(self) -> bool:
        "Returns True if the client is an admin."
        roaster = bs.get_game_roster()
        for player in roaster:
            if player["client_id"] == self.client_id:
                if player["account_id"] in self.serverconfig.admins:
                    return True
        return False

    @property
    def serverconfig(self) -> ServerConfig:
        """Returns loaded serverconfig."""

        # this seems only way to get serverconfig for now
        # hooking it won't work.
        assert babase.app.classic is not None
        assert babase.app.classic.server is not None

        return babase.app.classic.server.config

    def get_player(self, client_id: int | None = None) -> bs.Player:
        """Return the player associated with the given client ID."""

        client_id = client_id or self.client_id
        activity = bs.get_foreground_host_activity()

        for player in activity.players:
            if player.client_id == client_id:
                return player

        raise ValueError(f"No player found with client_id={client_id}")

    def __call__(self) -> None:
        with self._handle_errors():
            self.on_command_call()

    @contextmanager
    def _handle_errors(self):
        """
        Context manager to catch common argument-related errors and
        show helpful usage info.
        """
        try:
            yield
        except (TypeError, ValueError, IndexError) as e:
            bs.broadcastmessage(
                f"❌ Error: {e}", clients=[self.client_id], transient=True
            )
            bs.broadcastmessage(
                f"📌 Usage: {self.get_usage()}",
                clients=[self.client_id],
                transient=True,
            )

    def get_usage(self) -> str:
        """
        Extracts the first line of the docstring for usage help.
        """
        doc = self.__doc__
        if doc:
            return doc.strip().splitlines()[0]
        return "<no usage info>"
