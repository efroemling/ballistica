# Released under the MIT License. See LICENSE for details.
#
"""Plugin related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from ba import print_exception
import _ba

if TYPE_CHECKING:
    from typing import List, Dict
    import ba


class PluginSubsystem:
    """Subsystem for plugin handling in the app.

    Category: App Classes

    Access the single shared instance of this class at 'ba.app.plugins'.
    """

    def __init__(self) -> None:
        self.potential_plugins: List[ba.PotentialPlugin] = []
        self.active_plugins: Dict[str, ba.Plugin] = {}

    def on_app_launch(self) -> None:
        """Should be called at app launch time."""
        # Load up our plugins and go ahead and call their on_app_launch calls.
        self.load_plugins()
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_launch()
            except Exception:
                print_exception('Error in plugin on_app_launch()')

    def on_app_pause(self) -> None:
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_pause()
            except Exception:
                print_exception('Error in plugin on_app_pause()')

    def on_app_resume(self) -> None:
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_resume()
            except Exception:
                print_exception('Error in plugin on_app_resume()')

    def on_app_shutdown(self) -> None:
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_shutdown()
            except Exception:
                print_exception('Error in plugin on_app_shutdown()')

    def load_plugins(self) -> None:
        """(internal)"""
        from ba._general import getclass

        # Note: the plugins we load is purely based on what's enabled
        # in the app config. Our meta-scan gives us a list of available
        # plugins, but that is only used to give the user a list of plugins
        # that they can enable. (we wouldn't want to look at meta-scan here
        # anyway because it may not be done yet at this point in the launch)
        plugstates: Dict[str, Dict] = _ba.app.config.get('Plugins', {})
        assert isinstance(plugstates, dict)
        plugkeys: List[str] = sorted(key for key, val in plugstates.items()
                                     if val.get('enabled', False))
        for plugkey in plugkeys:
            try:
                cls = getclass(plugkey, Plugin)
            except Exception as exc:
                _ba.log(f"Error loading plugin class '{plugkey}': {exc}",
                        to_server=False)
                continue
            try:
                plugin = cls()
                assert plugkey not in self.active_plugins
                self.active_plugins[plugkey] = plugin
            except Exception:
                print_exception(f'Error loading plugin: {plugkey}')


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

    def on_app_pause(self) -> None:
        """Сalled after pausing game activity."""

    def on_app_resume(self) -> None:
        """Called after the game continues."""

    def on_app_shutdown(self) -> None:
        """Called before closing the application."""
