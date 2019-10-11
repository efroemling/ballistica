# Copyright (c) 2011-2019 Eric Froemling
"""Defines AppDelegate class for handling high level app functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Type, Optional, Any, Dict, Callable
    import ba


class AppDelegate:
    """Defines handlers for high level app functionality."""

    def create_default_game_config_ui(
            self, gameclass: Type[ba.GameActivity],
            sessionclass: Type[ba.Session], config: Optional[Dict[str, Any]],
            completion_call: Callable[[Optional[Dict[str, Any]]], None]
    ) -> None:
        """Launch a UI to configure the given game config.

        It should manipulate the contents of config and call completion_call
        when done.
        """
        del gameclass, sessionclass, config, completion_call  # unused
        from ba import _error
        _error.print_error(
            "create_default_game_config_ui needs to be overridden")
