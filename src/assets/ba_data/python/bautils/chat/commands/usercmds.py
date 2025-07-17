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
    from tinydb import TinyDB, Query

    TINYDB_AVAILABLE = True
    print("[USERCMDS] TinyDB imported successfully")
except ImportError:
    print("[USERCMDS] TinyDB not available")
    TINYDB_AVAILABLE = False
    TinyDB = None
    Query = None


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

    @override
    def on_command_call(self) -> None:
        # Check if registrations are enabled
        try:
            from bautils.tourny.register import ENABLE_REGISTRATIONS

            # print(f"[REGISTRATION] ENABLE_REGISTRATIONS value: {ENABLE_REGISTRATIONS}")
            if not ENABLE_REGISTRATIONS:
                bs.broadcastmessage(
                    "Registration is currently disabled.",
                    color=Color.RED.float,
                    clients=[self.client_id],
                    transient=True,
                )
                # print("[REGISTRATION] Registration blocked - disabled in settings")
                return
        except ImportError as e:
            print(f"[REGISTRATION] Could not import registration settings: {e}")
            # If we can't import settings, assume disabled for safety
            bs.broadcastmessage(
                "Registration system not available.",
                color=Color.RED.float,
                clients=[self.client_id],
                transient=True,
            )
            return
        except Exception as e:
            print(f"[REGISTRATION] Error checking registration settings: {e}")
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

        # Get proper UUID using BombSquad API
        try:

            uuid = bs.get_client_public_device_uuid(self.client_id)
        except:
            uuid = getattr(device, "unique_id", "unknown")

        # Get PB ID using get_v1_account_id method
        pb_id = "unknown"
        try:
            if hasattr(player, "get_v1_account_id"):
                pb_id = player.get_v1_account_id() or "unknown"
            elif hasattr(device, "get_v1_account_id"):
                pb_id = device.get_v1_account_id() or "unknown"
        except:
            # Fallback to roster account_id
            try:
                roster = bs.get_game_roster()
                for client_entry in roster:
                    if client_entry.get('client_id') == self.client_id:
                        pb_id = client_entry.get('account_id', 'unknown')
                        break
            except:
                pass

        # Get V2 ID from roster spec_string
        v2_id = "unknown"
        try:
            roster = bs.get_game_roster()
            for client_entry in roster:
                if client_entry.get('client_id') == self.client_id:
                    spec_string = client_entry.get('spec_string', '')
                    if spec_string:
                        import json

                        spec_data = json.loads(spec_string)
                        v2_id = spec_data.get(
                            'n', 'unknown'
                        )  # 'n' field contains the V2 account name
                    break
        except Exception as e:
            print(f"Error parsing spec_string: {e}")
            pass

        # Debug output to see what we're getting
        print(f"UUID: {uuid}")
        print(f"PB_ID: {pb_id}")
        print(f"V2_ID: {v2_id}")

        # Debug roster info
        # try:
        #     roster = bs.get_game_roster()
        #     for client_entry in roster:
        #         if client_entry.get('client_id') == self.client_id:
        #             print(f"[REGISTRATION] Roster entry: {client_entry}")
        #             break
        # except:
        #     print("[REGISTRATION] Could not get roster info")

        # Create/use database
        try:
            # Get path to tourny folder
            import os

            tourny_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'tourny'
            )
            db_path = os.path.join(tourny_path, "player_registrations.json")

            # Create tourny directory if it doesn't exist
            os.makedirs(tourny_path, exist_ok=True)

            # Use default TinyDB storage (no custom formatting for now)
            db = TinyDB(db_path)
            players_table = db.table('players')
            Player = Query()

            # print(f"[REGISTRATION] Database path: {db_path}")
            print(f"Current players in DB: {len(players_table.all())}")

            # Check if already exists - only check PB ID
            existing = players_table.search(Player.pb_id == pb_id)

            if existing:
                player_id = existing[0].doc_id
                bs.broadcastmessage(
                    f"You are already registered! ID: #{player_id}",
                    color=Color.CYAN.float,
                    clients=[self.client_id],
                    transient=True,
                )
                print(
                    f"Player #{player_id} already registered with PB ID: {pb_id}"
                )
            else:
                # Insert new player (this will append, not replace)
                player_id = players_table.insert(
                    {'uuid': uuid, 'pb_id': pb_id, 'v2_id': v2_id}
                )

                print(f"Inserted player with ID: {player_id}")
                print(f"Total players now: {len(players_table.all())}")

                bs.broadcastmessage(
                    f"Registered successfully! ID: #{player_id}",
                    color=Color.CYAN.float,
                    clients=[self.client_id],
                    transient=True,
                )
                print(f"New player #{player_id} registered with PB ID: {pb_id}")

            db.close()

            # Optional: Pretty format the JSON file after closing the database
            try:
                import json

                with open(db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump(
                        data, f, indent=4, sort_keys=True, ensure_ascii=False
                    )
            except Exception as format_error:
                print(
                    f"JSON formatting failed (but data saved): {format_error}"
                )

        except Exception as e:
            bs.broadcastmessage(
                "Registration failed. Please try again.",
                color=Color.RED.float,
                clients=[self.client_id],
                transient=True,
            )
            print(f"[REGISTRATION] Error: {e}")

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
        except:
            return None

    @override
    def admin_authentication(self) -> bool:
        """Allow all players to use this command."""
        return False
