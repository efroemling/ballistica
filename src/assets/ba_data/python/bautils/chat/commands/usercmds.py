# Released under the MIT License. See LICENSE for details.
#
"""A command module handing user commands."""

from __future__ import annotations
from typing import override

import bascenev1 as bs
from bautils.tools.enums import Color
from bautils.chat import ServerCommand, register_command

# Simple inline registration system for testing
try:
    from tinydb import TinyDB, Query  # type: ignore[import-not-found]

    TINYDB_AVAILABLE = True
except ImportError:
    TinyDB = None
    Query = None
    TINYDB_AVAILABLE = False


# TODO: make it look more pretty, make characters icon appear in list
@register_command
class List(ServerCommand):
    """/l, /list or /clients"""

    aliases = ["l", "clients"]

    @override
    def on_command_call(self) -> None:

        # Build and broadcast a clean ASCII player list table.
        header = "{0:^4} | {1:<16} | {2:^8}"
        separator = "-" * 50

        lines = []
        lines.append(separator)
        lines.append(header.format("No.", "Name", "ClientID"))
        lines.append(separator)

        session = bs.get_foreground_host_session()
        assert session is not None

        for index, player in enumerate(session.sessionplayers, start=1):
            lines.append(
                header.format(
                    index,
                    player.getname(icon=True),
                    player.inputdevice.client_id,
                )
            )

        lines.append(separator)
        _list = "\n".join(lines)

        bs.broadcastmessage(_list, transient=True, clients=[self.client_id])

    @override
    def admin_authentication(self) -> bool:
        return False


@register_command
class Register(ServerCommand):
    """/register - Register yourself on this server"""

    def _check_registration_enabled(self) -> bool:
        """Check if registrations are enabled."""
        try:
            from bautils.tourny.register import ENABLE_REGISTRATIONS

            if not ENABLE_REGISTRATIONS:
                bs.broadcastmessage(
                    "Registration is currently disabled.",
                    color=Color.RED.float,
                    clients=[self.client_id],
                    transient=True,
                )
                return False
            return True
        except ImportError as e:
            print(f"[REGISTRATION] Could not import registration settings: {e}")
            bs.broadcastmessage(
                "Registration system not available.",
                color=Color.RED.float,
                clients=[self.client_id],
                transient=True,
            )
            return False
        except Exception as e:
            print(f"[REGISTRATION] Error checking registration settings: {e}")
            return False

    def _get_player_uuid(self, device) -> str:  # type: ignore[no-untyped-def]
        """Get player UUID."""
        try:
            uuid_result = bs.get_client_public_device_uuid(self.client_id)  # type: ignore[attr-defined]
            return str(uuid_result)
        except Exception:
            return str(getattr(device, "unique_id", "unknown"))

    def _get_player_pb_id(self, player, device) -> str:  # type: ignore[no-untyped-def]
        """Get player PB ID."""
        try:
            if hasattr(player, "get_v1_account_id"):
                result = player.get_v1_account_id()
                return str(result) if result else "unknown"
            if hasattr(device, "get_v1_account_id"):
                result = device.get_v1_account_id()
                return str(result) if result else "unknown"
        except Exception:
            pass

        # Fallback to roster account_id
        try:
            roster = bs.get_game_roster()
            for client_entry in roster:
                if client_entry.get('client_id') == self.client_id:
                    account_id = client_entry.get('account_id', 'unknown')
                    return str(account_id)
        except Exception:
            pass
        return "unknown"

    def _get_player_v2_id(self) -> str:
        """Get player V2 ID from roster spec_string."""
        try:
            roster = bs.get_game_roster()
            for client_entry in roster:
                if client_entry.get('client_id') == self.client_id:
                    spec_string = client_entry.get('spec_string', '')
                    if spec_string:
                        import json

                        spec_data = json.loads(spec_string)
                        v2_name = spec_data.get('n', 'unknown')
                        return str(v2_name)
        except Exception as e:
            print(f"Error parsing spec_string: {e}")
        return "unknown"

    def _register_in_database(self, uuid: str, pb_id: str, v2_id: str) -> bool:
        """Register player in database."""
        try:
            import os

            tourny_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'tourny'
            )
            db_path = os.path.join(tourny_path, "player_registrations.json")
            os.makedirs(tourny_path, exist_ok=True)

            db = TinyDB(db_path)
            players_table = db.table('players')
            player_query = Query()

            print(f"Current players in DB: {len(players_table.all())}")

            # Check if already exists
            existing = players_table.search(player_query.pb_id == pb_id)

            if existing:
                player_id = existing[0].doc_id
                bs.broadcastmessage(
                    f"Already registered! Your player ID: #{player_id}",
                    color=Color.YELLOW.float,
                    clients=[self.client_id],
                    transient=True,
                )
                return False
            else:
                # Insert new player
                player_id = players_table.insert(
                    {'uuid': uuid, 'pb_id': pb_id, 'v2_id': v2_id}
                )

                bs.broadcastmessage(
                    f"Registration successful! Your player ID: #{player_id}",
                    color=Color.GREEN.float,
                    clients=[self.client_id],
                    transient=True,
                )
                print(
                    f"New registration: ID #{player_id}, "
                    f"Total players: {len(players_table.all())}"
                )
                return True

        except Exception as e:
            print(f"Database error: {e}")
            bs.broadcastmessage(
                "Registration failed due to database error.",
                color=Color.RED.float,
                clients=[self.client_id],
                transient=True,
            )
            return False

    @override
    def on_command_call(self) -> None:
        if not self._check_registration_enabled():
            return

        if not TINYDB_AVAILABLE:
            print("TinyDB not installed.")
            return

        # Get player info
        player = self._get_player()
        if not player:
            bs.broadcastmessage(
                "Could not find player information, join the game first.",
                color=Color.RED.float,
                clients=[self.client_id],
                transient=True,
            )
            return

        # Extract identifiers
        device = player.inputdevice
        uuid = self._get_player_uuid(device)
        pb_id = self._get_player_pb_id(player, device)
        v2_id = self._get_player_v2_id()

        # Debug output
        print(f"UUID: {uuid}")
        print(f"PB_ID: {pb_id}")
        print(f"V2_ID: {v2_id}")

        # Register in database
        self._register_in_database(uuid, pb_id, v2_id)

    def _get_player(self) -> bs.SessionPlayer | None:
        """Get player by client ID."""
        try:
            session = bs.get_foreground_host_session()
            if not session:
                return None

            for player in session.sessionplayers:
                if player.inputdevice.client_id == self.client_id:
                    return player
            return None
        except Exception:
            return None

    @override
    def admin_authentication(self) -> bool:
        """Allow all players to use this command."""
        return False
