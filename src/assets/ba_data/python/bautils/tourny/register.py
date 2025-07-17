# Released under the MIT License. See LICENSE for details.
#
"""
Simple Player Registration System for BombSquad Server
Players can use /register command to store their UUID, PB ID, and V2 ID.
Data is stored using TinyDB with indexed entries.
Configuration:
- ENABLE_REGISTRATIONS: True/False to allow registrations
a watermelon!
"""
# ba_meta require api 9
from __future__ import annotations

from typing import TYPE_CHECKING, override

import os
import babase

if TYPE_CHECKING:
    import bascenev1 as bs

# Import TinyDB for database
try:
    from tinydb import TinyDB, Query  # type: ignore[import-not-found]
except ImportError:
    print("TinyDB not found. Install with: pip install tinydb")
    TinyDB = None
    Query = None

if TYPE_CHECKING:
    import bascenev1 as bs

# Configuration
ENABLE_REGISTRATIONS = False


def get_tourny_path() -> str:
    """Get the path to the tourny directory."""
    # Get the directory where this module is located (tourny folder)
    return os.path.dirname(os.path.abspath(__file__))


DATABASE_FILE = os.path.join(get_tourny_path(), "player_registrations.json")


class PlayerDatabase:
    """Simple TinyDB-based player registration database."""

    def __init__(self, db_file: str = DATABASE_FILE):
        if TinyDB is None:
            raise ImportError(
                "TinyDB is required. Install with: pip install tinydb"
            )

        # Use pretty formatting for JSON
        from tinydb.storages import JSONStorage  # type: ignore[import-not-found] # pylint: disable=import-error
        from tinydb.middlewares import CachingMiddleware  # type: ignore[import-not-found] # pylint: disable=import-error

        class PrettyJSONStorage(JSONStorage):  # type: ignore[misc,no-any-unimported]
            """JSON storage with pretty formatting."""

            def write(self, data: dict) -> None:
                """Write data with pretty formatting."""
                import json

                with open(self._handle.name, 'w', encoding='utf-8') as f:
                    json.dump(
                        data, f, indent=4, sort_keys=True, ensure_ascii=False
                    )

        self.db = TinyDB(db_file, storage=CachingMiddleware(PrettyJSONStorage))
        self.players_table = self.db.table('players')

    def register_player(
        self, uuid: str, pb_id: str, v2_id: str
    ) -> tuple[bool, int]:
        """Register a player. Returns (is_new, player_id)."""
        player_query = Query()

        # Check if already exists by any identifier
        existing = self.players_table.search(
            (player_query.uuid == uuid)
            | (player_query.pb_id == pb_id)
            | (player_query.v2_id == v2_id)
        )

        if existing:
            # Player already registered - don't update, just return existing ID
            player_data = existing[0]
            return False, player_data.doc_id

        # Insert new player
        player_id = self.players_table.insert(
            {'uuid': uuid, 'pb_id': pb_id, 'v2_id': v2_id}
        )

        return True, player_id

    def get_player_count(self) -> int:
        """Get total number of registered players."""
        return len(self.players_table)

    def close(self) -> None:
        """Close the database."""
        self.db.close()


class RegistrationPlugin(babase.Plugin):
    """Simple registration plugin."""

    def __init__(self) -> None:
        super().__init__()
        self.database = None

    def on_player_join(self, player: bs.Player) -> None:
        """Called when a player joins."""
        # Placeholder for plugin functionality
        return

    def on_player_leave(self, player: bs.Player) -> None:
        """Called when a player leaves."""
        # Placeholder for plugin functionality
        return

    @override
    def on_app_running(self) -> None:
        """Called when the app is running."""
        # Placeholder for plugin functionality
        return

    @override
    def on_app_suspend(self) -> None:
        """Called when the app is suspended."""
        # Placeholder for plugin functionality
        return

    @override
    def on_app_unsuspend(self) -> None:
        """Called when the app is unsuspended."""
        # Placeholder for plugin functionality
        return


# Global database instance
_global_database: PlayerDatabase | None = None


def get_global_database() -> PlayerDatabase | None:
    """Get the global database instance."""
    return _global_database


def is_registrations_enabled() -> bool:
    """Check if registrations are enabled."""
    return ENABLE_REGISTRATIONS
