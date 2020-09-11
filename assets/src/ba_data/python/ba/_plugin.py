# Released under the MIT License. See LICENSE for details.
#
"""Plugin related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    import ba


@dataclass
class PotentialPlugin:
    """Represents a ba.Plugin which can potentially be loaded.

    Category: App Classes

    These generally represent plugins which were detected by the
    meta-tag scan. However they may also represent plugins which
    were previously set to be loaded but which were unable to be
    for some reason. In that case, 'available' will be set to False.
    """
    display_name: ba.Lstr
    class_path: str
    available: bool


class Plugin:
    """A plugin to alter app behavior in some way.

    Category: App Classes

    Plugins are discoverable by the meta-tag system
    and the user can select which ones they want to activate.
    Active plugins are then called at specific times as the
    app is running in order to modify its behavior in some way.
    """

    def on_app_launch(self) -> None:
        """Called when the app is being launched."""
