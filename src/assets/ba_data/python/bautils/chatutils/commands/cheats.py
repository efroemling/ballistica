# Released under the MIT License. See LICENSE for details.
#
"""A command module handing cheat commands."""

from __future__ import annotations
from typing import override

import bascenev1 as bs
from bascenev1lib.actor.playerspaz import PlayerSpaz

from bautils.chatutils import (
    ServerCommand,
    register_command,
    IncorrectUsageError,
    ActorNotFoundError,
)

cyan = (0.0, 0.5, 1.0)


@register_command
class Kill(ServerCommand):
    """/kill or /kill <client_id>"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                user = self.get_session_player(self.client_id)
                self.kill_player(self.client_id)
                bs.broadcastmessage(
                    f"{user.getname()} commited sucide.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case ["all"]:
                user = self.get_session_player(self.client_id)
                roster = bs.get_game_roster()
                for client in roster:
                    if client["client_id"] == -1:
                        continue
                    self.kill_player(client["client_id"])
                bs.broadcastmessage(
                    f"{user.getname()} killed everyone.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                user = self.get_session_player(self.client_id)
                target = self.get_session_player(client_id)
                self.kill_player(_id)
                bs.broadcastmessage(
                    f"{user.getname()} killed {target.getname()}.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case _:
                raise IncorrectUsageError

    def kill_player(self, client_id: int) -> None:
        """Kills the player having given client id."""

        player = self.get_activity_player(client_id)
        if player.actor is None:
            raise ActorNotFoundError("Please wait for the game to start.")

        # this seems only way for making it type safe for now
        if isinstance(player.actor, PlayerSpaz):
            player.actor.node.handlemessage(bs.DieMessage())


@register_command
class Curse(ServerCommand):
    """/curse or /curse <client_id>"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                self.curse_player(self.client_id)
                user = self.get_session_player(self.client_id)
                bs.broadcastmessage(
                    f"{user.getname()} cursed themselves.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case ["all"]:
                user = self.get_session_player(self.client_id)
                roster = bs.get_game_roster()
                for client in roster:
                    if client["client_id"] == -1:
                        continue
                    self.curse_player(client["client_id"])
                bs.broadcastmessage(
                    f"{user.getname()} cursed everyone.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                user = self.get_session_player(self.client_id)
                target = self.get_session_player(client_id)
                self.curse_player(_id)
                bs.broadcastmessage(
                    f"{user.getname()} cursed {target.getname()}.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case _:
                raise IncorrectUsageError

    def curse_player(self, client_id: int) -> None:
        """Curses the player having given client id."""

        player = self.get_activity_player(client_id)
        if player.actor is None:
            raise ActorNotFoundError("Please wait for the game to start.")

        if isinstance(player.actor, PlayerSpaz):
            player.actor.node.handlemessage(
                bs.PowerupMessage(poweruptype="curse")
            )


@register_command
class Heal(ServerCommand):
    """/heal or /heal <client_id>"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                self.heal_player(self.client_id)
                user = self.get_session_player(self.client_id)
                bs.broadcastmessage(
                    f"{user.getname()} healed themselves.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case ["all"]:
                user = self.get_session_player(self.client_id)
                roster = bs.get_game_roster()
                for client in roster:
                    if client["client_id"] == -1:
                        continue
                    self.heal_player(client["client_id"])
                bs.broadcastmessage(
                    f"{user.getname()} healed everyone.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                user = self.get_session_player(self.client_id)
                target = self.get_session_player(client_id)
                self.heal_player(_id)
                bs.broadcastmessage(
                    f"{user.getname()} healed {target.getname()}.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case _:
                raise IncorrectUsageError

    def heal_player(self, client_id: int) -> None:
        """Heals the player having given client id."""

        player = self.get_activity_player(client_id)
        if player.actor is None:
            raise ActorNotFoundError("Please wait for the game to start.")

        if isinstance(player.actor, PlayerSpaz):
            player.actor.node.handlemessage(
                bs.PowerupMessage(poweruptype="health")
            )


@register_command
class Gloves(ServerCommand):
    """/gloves or /gloves <client_id>"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                self.give_gloves(self.client_id)
                user = self.get_session_player(self.client_id)
                bs.broadcastmessage(
                    f"{user.getname()} gave themselves gloves.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case ["all"]:
                user = self.get_session_player(self.client_id)
                roster = bs.get_game_roster()
                for client in roster:
                    if client["client_id"] == -1:
                        continue
                    self.give_gloves(client["client_id"])
                bs.broadcastmessage(
                    f"{user.getname()} gave everyone gloves.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                user = self.get_session_player(self.client_id)
                target = self.get_session_player(client_id)
                self.give_gloves(_id)
                bs.broadcastmessage(
                    f"{user.getname()} gave gloves to {target.getname()}.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case _:
                raise IncorrectUsageError

    def give_gloves(self, client_id: int) -> None:
        """Give gloves to the player having given client id."""

        player = self.get_activity_player(client_id)
        if player.actor is None:
            raise ActorNotFoundError("Please wait for the game to start.")

        if isinstance(player.actor, PlayerSpaz):
            player.actor.node.handlemessage(
                bs.PowerupMessage(poweruptype="punch")
            )


@register_command
class Shield(ServerCommand):
    """/shield or /shield <client_id>"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                self.give_shield(self.client_id)
                user = self.get_session_player(self.client_id)
                bs.broadcastmessage(
                    f"{user.getname()} gave themselves a shield.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case ["all"]:
                user = self.get_session_player(self.client_id)
                roster = bs.get_game_roster()
                for client in roster:
                    if client["client_id"] == -1:
                        continue
                    self.give_shield(client["client_id"])
                bs.broadcastmessage(
                    f"{user.getname()} gave everyone a shield.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                user = self.get_session_player(self.client_id)
                target = self.get_session_player(client_id)
                self.give_shield(_id)
                bs.broadcastmessage(
                    f"{user.getname()} gave a shield to {target.getname()}.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case _:
                raise IncorrectUsageError

    def give_shield(self, client_id: int) -> None:
        """Give shield to the player having given client id."""

        player = self.get_activity_player(client_id)
        if player.actor is None:
            raise ActorNotFoundError("Please wait for the game to start.")

        if isinstance(player.actor, PlayerSpaz):
            player.actor.node.handlemessage(
                bs.PowerupMessage(poweruptype="shield")
            )


@register_command
class Freeze(ServerCommand):
    """/freeze or /freeze <client_id>"""

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                self.freeze_player(self.client_id)
                user = self.get_session_player(self.client_id)
                bs.broadcastmessage(
                    f"{user.getname()} froze themselves.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case ["all"]:
                user = self.get_session_player(self.client_id)
                roster = bs.get_game_roster()
                for client in roster:
                    if client["client_id"] == -1:
                        continue
                    self.freeze_player(client["client_id"])
                bs.broadcastmessage(
                    f"{user.getname()} froze everyone.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                user = self.get_session_player(self.client_id)
                target = self.get_session_player(client_id)
                self.freeze_player(_id)
                bs.broadcastmessage(
                    f"{user.getname()} froze {target.getname()}.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case _:
                raise IncorrectUsageError

    def freeze_player(self, client_id: int) -> None:
        """Freezes the player having given client id."""

        player = self.get_activity_player(client_id)
        if player.actor is None:
            raise ActorNotFoundError("Please wait for the game to start.")

        if isinstance(player.actor, PlayerSpaz):
            player.actor.node.handlemessage(bs.FreezeMessage())


@register_command
class Thaw(ServerCommand):
    """/unfree or /unfreeze <client_id> | /thaw or /thaw <client_id>"""

    aliases = ["unfreeze"]

    @override
    def on_command_call(self) -> None:

        match self.arguments:

            case []:
                self.thaw_player(self.client_id)
                user = self.get_session_player(self.client_id)
                bs.broadcastmessage(
                    f"{user.getname()} thawed themselves.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case ["all"]:
                user = self.get_session_player(self.client_id)
                roster = bs.get_game_roster()
                for client in roster:
                    if client["client_id"] == -1:
                        continue
                    self.thaw_player(client["client_id"])
                bs.broadcastmessage(
                    f"{user.getname()} thawed everyone.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case [client_id] if client_id.isdigit():
                _id = self.filter_client_id(client_id)
                user = self.get_session_player(self.client_id)
                target = self.get_session_player(client_id)
                self.thaw_player(_id)
                bs.broadcastmessage(
                    f"{user.getname()} thawed {target.getname()}.",
                    clients=None,
                    transient=True,
                    color=cyan,
                )

            case _:
                raise IncorrectUsageError

    def thaw_player(self, client_id: int) -> None:
        """Thaws the player having given client id."""

        player = self.get_activity_player(client_id)
        if player.actor is None:
            raise ActorNotFoundError("Please wait for the game to start.")

        if isinstance(player.actor, PlayerSpaz):
            player.actor.node.handlemessage(bs.ThawMessage())
