# Released under the MIT License. See LICENSE for details.
#
"""Plugin related functionality."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass

import _ba

if TYPE_CHECKING:
    import ba


class PluginSubsystem:
    """Subsystem for plugin handling in the app.

    Category: **App Classes**

    Access the single shared instance of this class at `ba.app.plugins`.
    """

    def __init__(self) -> None:
        self.potential_plugins: list[ba.PotentialPlugin] = []
        self.active_plugins: dict[str, ba.Plugin] = {}

    def on_meta_scan_complete(self) -> None:
        """Should be called when meta-scanning is complete."""
        from ba._language import Lstr

        plugs = _ba.app.plugins
        config_changed = False
        found_new = False
        plugstates: dict[str, dict] = _ba.app.config.setdefault('Plugins', {})
        assert isinstance(plugstates, dict)

        results = _ba.app.meta.scanresults
        assert results is not None

        # Create a potential-plugin for each class we found in the scan.
        for class_path in results.exports_of_class(Plugin):
            plugs.potential_plugins.append(
                PotentialPlugin(
                    display_name=Lstr(value=class_path),
                    class_path=class_path,
                    available=True,
                )
            )
            if class_path not in plugstates:
                # Go ahead and enable new plugins by default, but we'll
                # inform the user that they need to restart to pick them up.
                # they can also disable them in settings so they never load.
                plugstates[class_path] = {'enabled': True}
                config_changed = True
                found_new = True

        plugs.potential_plugins.sort(key=lambda p: p.class_path)

        # Note: these days we complete meta-scan and immediately activate
        # plugins, so we don't need the message about 'restart to activate'
        # anymore.
        if found_new and bool(False):
            _ba.screenmessage(
                Lstr(resource='pluginsDetectedText'), color=(0, 1, 0)
            )
            _ba.playsound(_ba.getsound('ding'))

        if config_changed:
            _ba.app.config.commit()

    def on_app_running(self) -> None:
        """Should be called when the app reaches the running state."""
        # Load up our plugins and go ahead and call their on_app_running calls.
        self.load_plugins()
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_running()
            except Exception:
                from ba import _error

                _error.print_exception('Error in plugin on_app_running()')

    def on_app_pause(self) -> None:
        """Called when the app goes to a suspended state."""
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_pause()
            except Exception:
                from ba import _error

                _error.print_exception('Error in plugin on_app_pause()')

    def on_app_resume(self) -> None:
        """Run when the app resumes from a suspended state."""
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_resume()
            except Exception:
                from ba import _error

                _error.print_exception('Error in plugin on_app_resume()')

    def on_app_shutdown(self) -> None:
        """Called when the app is being closed."""
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_shutdown()
            except Exception:
                from ba import _error

                _error.print_exception('Error in plugin on_app_shutdown()')

    def load_plugins(self) -> None:
        """(internal)"""
        from ba._general import getclass
        from ba._language import Lstr

        # Note: the plugins we load is purely based on what's enabled
        # in the app config. Its not our job to look at meta stuff here.
        plugstates: dict[str, dict] = _ba.app.config.get('Plugins', {})
        assert isinstance(plugstates, dict)
        plugkeys: list[str] = sorted(
            key for key, val in plugstates.items() if val.get('enabled', False)
        )
        disappeared_plugs: set[str] = set()
        for plugkey in plugkeys:
            try:
                cls = getclass(plugkey, Plugin)
            except ModuleNotFoundError:
                disappeared_plugs.add(plugkey)
                continue
            except Exception as exc:
                _ba.playsound(_ba.getsound('error'))
                _ba.screenmessage(
                    Lstr(
                        resource='pluginClassLoadErrorText',
                        subs=[('${PLUGIN}', plugkey), ('${ERROR}', str(exc))],
                    ),
                    color=(1, 0, 0),
                )
                logging.exception("Error loading plugin class '%s'", plugkey)
                continue
            try:
                plugin = cls()
                assert plugkey not in self.active_plugins
                self.active_plugins[plugkey] = plugin
            except Exception as exc:
                from ba import _error

                _ba.playsound(_ba.getsound('error'))
                _ba.screenmessage(
                    Lstr(
                        resource='pluginInitErrorText',
                        subs=[('${PLUGIN}', plugkey), ('${ERROR}', str(exc))],
                    ),
                    color=(1, 0, 0),
                )
                _error.print_exception(f"Error initing plugin: '{plugkey}'.")

        # If plugins disappeared, let the user know gently and remove them
        # from the config so we'll again let the user know if they later
        # reappear. This makes it much smoother to switch between users
        # or workspaces.
        if disappeared_plugs:
            _ba.playsound(_ba.getsound('shieldDown'))
            _ba.screenmessage(
                Lstr(
                    resource='pluginsRemovedText',
                    subs=[('${NUM}', str(len(disappeared_plugs)))],
                ),
                color=(1, 1, 0),
            )
            plugnames = ', '.join(disappeared_plugs)
            logging.info(
                '%d plugin(s) no longer found: %s.',
                len(disappeared_plugs),
                plugnames,
            )
            for goneplug in disappeared_plugs:
                del _ba.app.config['Plugins'][goneplug]
            _ba.app.config.commit()


@dataclass
class PotentialPlugin:
    """Represents a ba.Plugin which can potentially be loaded.

    Category: **App Classes**

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

    Category: **App Classes**

    Plugins are discoverable by the meta-tag system
    and the user can select which ones they want to activate.
    Active plugins are then called at specific times as the
    app is running in order to modify its behavior in some way.
    """

    def on_app_running(self) -> None:
        """Called when the app reaches the running state."""

    def on_app_pause(self) -> None:
        """Called after pausing game activity."""

    def on_app_resume(self) -> None:
        """Called after the game continues."""

    def on_app_shutdown(self) -> None:
        """Called before closing the application."""

    def has_settings_ui(self) -> bool:
        """Called to ask if we have settings UI we can show."""
        return False

    def show_settings_ui(self, source_widget: ba.Widget | None) -> None:
        """Called to show our settings UI."""
