# Released under the MIT License. See LICENSE for details.
#
"""Plugin related functionality."""

from __future__ import annotations

import logging
import importlib.util
from typing import TYPE_CHECKING
from dataclasses import dataclass

import _babase
from babase._appsubsystem import AppSubsystem

if TYPE_CHECKING:
    from typing import Any

    import babase


class PluginSubsystem(AppSubsystem):
    """Subsystem for plugin handling in the app.

    Category: **App Classes**

    Access the single shared instance of this class at `ba.app.plugins`.
    """

    AUTO_ENABLE_NEW_PLUGINS_CONFIG_KEY = 'Auto Enable New Plugins'
    AUTO_ENABLE_NEW_PLUGINS_DEFAULT = True

    def __init__(self) -> None:
        super().__init__()
        self.potential_plugins: list[babase.PotentialPlugin] = []
        self.active_plugins: dict[str, babase.Plugin] = {}

    def on_meta_scan_complete(self) -> None:
        """Should be called when meta-scanning is complete."""
        from babase._language import Lstr

        plugs = _babase.app.plugins
        config_changed = False
        found_new = False
        plugstates: dict[str, dict] = _babase.app.config.setdefault(
            'Plugins', {}
        )
        assert isinstance(plugstates, dict)

        results = _babase.app.meta.scanresults
        assert results is not None

        auto_enable_new_plugins = (
            _babase.app.config.get(
                self.AUTO_ENABLE_NEW_PLUGINS_CONFIG_KEY,
                self.AUTO_ENABLE_NEW_PLUGINS_DEFAULT,
            )
            is True
        )
        # Create a potential-plugin for each class we found in the scan.
        for class_path in results.exports_of_class(Plugin):
            plugs.potential_plugins.append(
                PotentialPlugin(
                    display_name=Lstr(value=class_path),
                    class_path=class_path,
                    available=True,
                )
            )
            if auto_enable_new_plugins:
                if class_path not in plugstates:
                    # Go ahead and enable new plugins by default, but we'll
                    # inform the user that they need to restart to pick them up.
                    # they can also disable them in settings so they never load.
                    plugstates[class_path] = {'enabled': True}
                    config_changed = True
                    found_new = True

        plugs.potential_plugins.sort(key=lambda p: p.class_path)

        # If we're *not* auto-enabling new plugins, at least let the
        # user know we found something new.
        if found_new and not auto_enable_new_plugins:
            _babase.screenmessage(
                Lstr(resource='pluginsDetectedText'), color=(0, 1, 0)
            )
            _babase.getsimplesound('ding').play()

        if config_changed:
            _babase.app.config.commit()

    def on_app_running(self) -> None:
        # Load up our plugins and go ahead and call their on_app_running calls.
        self.load_plugins()
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_running()
            except Exception:
                from babase import _error

                _error.print_exception('Error in plugin on_app_running()')

    def on_app_pause(self) -> None:
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_pause()
            except Exception:
                from babase import _error

                _error.print_exception('Error in plugin on_app_pause()')

    def on_app_resume(self) -> None:
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_resume()
            except Exception:
                from babase import _error

                _error.print_exception('Error in plugin on_app_resume()')

    def on_app_shutdown(self) -> None:
        for plugin in self.active_plugins.values():
            try:
                plugin.on_app_shutdown()
            except Exception:
                from babase import _error

                _error.print_exception('Error in plugin on_app_shutdown()')

    def load_plugins(self) -> None:
        """(internal)"""
        from babase._general import getclass
        from babase._language import Lstr

        # Note: the plugins we load is purely based on what's enabled
        # in the app config. Its not our job to look at meta stuff here.
        plugstates: dict[str, dict] = _babase.app.config.get('Plugins', {})
        assert isinstance(plugstates, dict)
        plugkeys: list[str] = sorted(
            key for key, val in plugstates.items() if val.get('enabled', False)
        )
        disappeared_plugs: set[str] = set()
        for plugkey in plugkeys:
            # Originally I was just catching ModuleNotFoundError on the
            # getclass() call to detect plugins disappearing. However
            # this breaks if the module *does* exist but itself imports
            # something that does not exist; in that case we would
            # incorrectly show that the plugin had disappeared.
            #
            # So now we're first explicitly asking Python if it can
            # locate the module, and if it can then we treat any further
            # errors including ModuleNotFound as problems with the
            # module's code; not ours.
            try:
                spec = importlib.util.find_spec(plugkey.split('.')[0])
            except Exception:
                spec = None

            if spec is None:
                disappeared_plugs.add(plugkey)
                continue

            # Ok; it seems that there's *something* there. Now try to load
            # it and treat any further errors as the module's fault.
            try:
                cls = getclass(plugkey, Plugin)
            except Exception as exc:
                _babase.getsimplesound('error').play()
                _babase.screenmessage(
                    Lstr(
                        resource='pluginClassLoadErrorText',
                        subs=[
                            ('${PLUGIN}', plugkey),
                            ('${ERROR}', str(exc)),
                        ],
                    ),
                    color=(1, 0, 0),
                )
                logging.exception("Error loading plugin class '%s'.", plugkey)
                continue
            try:
                plugin = cls()
                assert plugkey not in self.active_plugins
                self.active_plugins[plugkey] = plugin
            except Exception as exc:
                from babase import _error

                _babase.getsimplesound('error').play()
                _babase.screenmessage(
                    Lstr(
                        resource='pluginInitErrorText',
                        subs=[
                            ('${PLUGIN}', plugkey),
                            ('${ERROR}', str(exc)),
                        ],
                    ),
                    color=(1, 0, 0),
                )
                _error.print_exception(f"Error initing plugin: '{plugkey}'.")

        # If plugins disappeared, let the user know gently and remove them
        # from the config so we'll again let the user know if they later
        # reappear. This makes it much smoother to switch between users
        # or workspaces.
        if disappeared_plugs:
            _babase.getsimplesound('shieldDown').play()
            _babase.screenmessage(
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
                del _babase.app.config['Plugins'][goneplug]
            _babase.app.config.commit()


@dataclass
class PotentialPlugin:
    """Represents a babase.Plugin which can potentially be loaded.

    Category: **App Classes**

    These generally represent plugins which were detected by the
    meta-tag scan. However they may also represent plugins which
    were previously set to be loaded but which were unable to be
    for some reason. In that case, 'available' will be set to False.
    """

    display_name: babase.Lstr
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

    def show_settings_ui(self, source_widget: Any | None) -> None:
        """Called to show our settings UI."""
