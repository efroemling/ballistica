# Released under the MIT License. See LICENSE for details.
#
"""Defines AppDelegate class for handling high level app functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
    import ba


class AppDelegate:
    """Defines handlers for high level app functionality.

    Category: App Classes
    """

    def create_default_game_settings_ui(
        self,
        gameclass: type[ba.GameActivity],
        sessiontype: type[ba.Session],
        settings: dict | None,
        completion_call: Callable[[dict | None], None],
    ) -> None:
        """Launch a UI to configure the given game config.

        It should manipulate the contents of config and call completion_call
        when done.
        """
        del gameclass, sessiontype, settings, completion_call  # Unused.
        from ba import _error

        _error.print_error(
            "create_default_game_settings_ui needs to be overridden"
        )
