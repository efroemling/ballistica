# Released under the MIT License. See LICENSE for details.

"""Functionality related to discord sdk integration"""
from __future__ import annotations

from typing import TYPE_CHECKING, override
import _babase
from babase._appsubsystem import AppSubsystem

if TYPE_CHECKING:
    from typing import Any

# Add a config key preferably for this
ENABLE_DISCORD = True  # disable this for now


class DiscordSubsystem(AppSubsystem):
    """Discord SDK integration class.
    Access the single shared instance of this class via the
    :attr:`~babase.App.discord` attr on the :class:`~babase.App` class."""

    # pylint: disable=too-many-positional-arguments
    def __init__(self) -> None:
        self.details: str | None = None
        self.state: str | None = None
        self.large_image_key: str | None = None
        self.small_image_key: str | None = None
        self.large_image_text: str | None = None
        self.small_image_text: str | None = None
        self.start_timestamp: float | None = None
        self.end_timestamp: float | None = None
        if not ENABLE_DISCORD:
            return
        if not self.is_available():
            return
        _babase.discord_start()

    @override
    def on_app_shutdown(self) -> None:
        """Called when the app is shutting down."""
        _babase.discord_shutdown()

    @staticmethod
    def is_available() -> bool:
        """Check if the Discord SDK is available.
        _babase.discord_is_ready() returns None if not available."""
        return _babase.discord_is_ready() is not None

    @property
    def is_ready(self) -> bool:
        """Check if the Discord SDK is ready."""
        return _babase.discord_is_ready()

    def set_presence(
        self,
        state: str | None = None,
        details: str | None = None,
        start_timestamp: float | None = None,
        end_timestamp: float | None = None,
        large_image_key: str | None = None,
        small_image_key: str | None = None,
        large_image_text: str | None = None,
        small_image_text: str | None = None,
        party_id: str | None = None,
        party_size: tuple[int, int] | None = None,
    ) -> None:
        """Set Discord rich presence state.

        Args:
            state: Current game state (e.g. "In Match", "Main Menu")
            details: Additional details about current activity
            start_timestamp: Activity start time (epoch timestamp)
            end_timestamp: Activity end time (epoch timestamp)
            large_image_key: Key/Url for large image asset
            large_image_text: Hover text for large image
            small_image_key: Key/Url for small image asset
            small_image_text: Hover text for small image
            party_id: Current party ID for join/spectate
            party_size: Tuple of (current_size, max_size)
        """
        if not self.is_available():
            return

        # Build presence dict with only non-None values
        presence: dict[str, Any] = {}
        if state is not None:
            self.state = state
            presence['state'] = state
        if details is not None:
            self.details = details
            presence['details'] = details
        if start_timestamp is not None:
            self.start_timestamp = start_timestamp
            presence['start_timestamp'] = start_timestamp
        if end_timestamp is not None:
            self.end_timestamp = end_timestamp
            presence['end_timestamp'] = end_timestamp
        if large_image_key is not None:
            self.large_image_key = large_image_key
            presence['large_image_key'] = large_image_key
        if small_image_key is not None:
            self.small_image_key = small_image_key
            presence['small_image_key'] = small_image_key
        if large_image_text is not None:
            self.large_image_text = large_image_text
            presence['large_image_text'] = large_image_text
        if small_image_text is not None:
            self.small_image_text = small_image_text
            presence['small_image_text'] = small_image_text

        # Set party info if provided
        if party_id is not None:
            _babase.discord_set_party(party_id=party_id)
        if party_size is not None:
            _babase.discord_set_party(
                current_party_size=party_size[0], max_party_size=party_size[1]
            )

        # Update rich presence
        if presence:
            _babase.discord_richpresence(**presence)
