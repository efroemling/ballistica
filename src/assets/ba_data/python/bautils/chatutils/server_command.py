# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

from __future__ import annotations

from typing import TYPE_CHECKING

from abc import ABC, abstractmethod
from contextlib import contextmanager

import bascenev1 as bs
import babase as ba

from .cmd_manager import CommandManager
from .errors import (
    IncorrectUsageError,
    NoArgumentsProvidedError,
    IncorrectArgumentsError,
    InvalidClientIDError,
    ActorNotFoundError,
)

if TYPE_CHECKING:
    from typing import Generator, Any
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
        raise TypeError(
            "@register_command must be used on ServerCommand subclasses"
        )

    CommandManager.add_command(cls())
    return cls


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
        return False

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
            if player["client_id"] == int(self.client_id):
                if player["account_id"] in self.serverconfig.admins:
                    return True
        return False

    @property
    def serverconfig(self) -> ServerConfig:
        """Returns loaded serverconfig."""

        # this seems only way to get serverconfig for now
        # hooking it won't work.
        assert ba.app.classic is not None
        assert ba.app.classic.server is not None

        return ba.app.classic.server.config

    @property
    def arguments(self) -> list[str]:
        """Returns arguments of given command with validation."""
        args = self.message.split()[1:]
        if args == [""]:
            raise IncorrectArgumentsError("Please provide neccesary arguments.")
        return args

    def filter_client_id(self, client_id: str | int) -> int:
        """Returns client_id with various checks."""

        _id = int(client_id)
        roster = bs.get_game_roster()
        for client in roster:
            if _id in client.values():
                return _id
        raise InvalidClientIDError(
            f"Invalid client-id: {client_id} is provided."
        )

    def get_session_player(
        self, client_id: int | None = None
    ) -> bs.SessionPlayer:
        """Return the player associated with the given client ID."""

        client_id = client_id or self.client_id
        session = bs.get_foreground_host_session()
        assert session is not None

        for player in session.sessionplayers:
            if player.inputdevice.client_id == int(client_id):
                return player

        raise InvalidClientIDError(
            f"No player found with client-id: {client_id}"
        )

    def get_activity_player(self, client_id: int | None = None) -> bs.Player:
        """Return the player associated with the given client ID."""

        client_id = client_id or self.client_id
        activity = bs.get_foreground_host_activity()
        assert activity is not None
        players: list[bs.Player] = activity.players

        with activity.context:
            for player in players:
                s_player = player.sessionplayer

                if s_player.inputdevice.client_id == int(client_id):
                    return player

        raise InvalidClientIDError(
            f"No player found with client-id: {client_id}"
        )

    def __call__(self) -> None:
        with self._handle_errors():
            self.on_command_call()

    @contextmanager
    def _handle_errors(self) -> Generator[None, Any, None]:
        """
        Context manager to catch common argument-related errors and
        show helpful usage info.
        """
        try:
            yield

        except (
            ValueError,
            IncorrectArgumentsError,
            NoArgumentsProvidedError,
            InvalidClientIDError,
            ActorNotFoundError,
        ) as exc:
            bs.broadcastmessage(
                f"❌ Error: {exc}",
                clients=[self.client_id],
                transient=True,
                color=(1, 0, 0),
            )

        except IncorrectUsageError:
            bs.broadcastmessage(
                f"📌 Usage: {self.get_usage()}",
                clients=[self.client_id],
                transient=True,
                color=(1, 0, 0),
            )

    def get_usage(self) -> str:
        """
        Extracts the first line of the docstring for usage help.
        """
        doc = self.__doc__
        if doc:
            return doc.strip().splitlines()[0]
        return "<no usage info>"
