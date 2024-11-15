# Released under the MIT License. See LICENSE for details.
#
"""Plugin related functionality."""

from __future__ import annotations

import logging
import importlib.util
from typing import TYPE_CHECKING, override

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

        # Info about plugins that we are aware of. This may include
        # plugins discovered through meta-scanning as well as plugins
        # registered in the app-config. This may include plugins that
        # cannot be loaded for various reasons or that have been
        # intentionally disabled.
        self.plugin_specs: dict[str, babase.PluginSpec] = {}

        # The set of live active plugin objects.
        self.active_plugins: list[babase.Plugin] = []

    def on_meta_scan_complete(self) -> None:
        """Called when meta-scanning is complete."""
        from babase._language import Lstr

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

        assert not self.plugin_specs
        assert not self.active_plugins

        # Create a plugin-spec for each plugin class we found in the
        # meta-scan.
        for class_path in results.exports_of_class(Plugin):
            assert class_path not in self.plugin_specs
            plugspec = self.plugin_specs[class_path] = PluginSpec(
                class_path=class_path, loadable=True
            )

            # Auto-enable new ones if desired.
            if auto_enable_new_plugins:
                if class_path not in plugstates:
                    plugspec.enabled = True
                    config_changed = True
                    found_new = True

        # If we're *not* auto-enabling, simply let the user know if we
        # found new ones.
        if found_new and not auto_enable_new_plugins:
            _babase.screenmessage(
                Lstr(resource='pluginsDetectedText'), color=(0, 1, 0)
            )
            _babase.getsimplesound('ding').play()

        # Ok, now go through all plugins registered in the app-config
        # that weren't covered by the meta stuff above, either creating
        # plugin-specs for them or clearing them out. This covers
        # plugins with api versions not matching ours, plugins without
        # ba_*meta tags, and plugins that have since disappeared.
        assert isinstance(plugstates, dict)
        wrong_api_prefixes = [f'{m}.' for m in results.incorrect_api_modules]

        disappeared_plugs: set[str] = set()

        for class_path in sorted(plugstates.keys()):
            # Already have a spec for it; nothing to be done.
            if class_path in self.plugin_specs:
                continue

            # If this plugin corresponds to any modules that we've
            # identified as having incorrect api versions, we'll take
            # note of its existence but we won't try to load it.
            if any(
                class_path.startswith(prefix) for prefix in wrong_api_prefixes
            ):
                plugspec = self.plugin_specs[class_path] = PluginSpec(
                    class_path=class_path, loadable=False
                )
                continue

            # Ok, it seems to be a class we have no metadata for. Look
            # to see if it appears to be an actual class we could
            # theoretically load. If so, we'll try. If not, we consider
            # the plugin to have disappeared and inform the user as
            # such.
            try:
                spec = importlib.util.find_spec(
                    '.'.join(class_path.split('.')[:-1])
                )
            except Exception:
                spec = None

            if spec is None:
                disappeared_plugs.add(class_path)
                continue

        # If plugins disappeared, let the user know gently and remove
        # them from the config so we'll again let the user know if they
        # later reappear. This makes it much smoother to switch between
        # users or workspaces.
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

        if config_changed:
            _babase.app.config.commit()

    @override
    def on_app_running(self) -> None:
        # Load up our plugins and go ahead and call their on_app_running
        # calls.
        self.load_plugins()
        for plugin in self.active_plugins:
            try:
                plugin.on_app_running()
            except Exception:
                from babase import _error

                _error.print_exception('Error in plugin on_app_running()')

    @override
    def on_app_suspend(self) -> None:
        for plugin in self.active_plugins:
            try:
                plugin.on_app_suspend()
            except Exception:
                from babase import _error

                _error.print_exception('Error in plugin on_app_suspend()')

    @override
    def on_app_unsuspend(self) -> None:
        for plugin in self.active_plugins:
            try:
                plugin.on_app_unsuspend()
            except Exception:
                from babase import _error

                _error.print_exception('Error in plugin on_app_unsuspend()')

    @override
    def on_app_shutdown(self) -> None:
        for plugin in self.active_plugins:
            try:
                plugin.on_app_shutdown()
            except Exception:
                from babase import _error

                _error.print_exception('Error in plugin on_app_shutdown()')

    @override
    def on_app_shutdown_complete(self) -> None:
        for plugin in self.active_plugins:
            try:
                plugin.on_app_shutdown_complete()
            except Exception:
                from babase import _error

                _error.print_exception(
                    'Error in plugin on_app_shutdown_complete()'
                )

    def load_plugins(self) -> None:
        """(internal)"""

        # Load plugins from any specs that are enabled & able to.
        for _class_path, plug_spec in sorted(self.plugin_specs.items()):
            plugin = plug_spec.attempt_load_if_enabled()
            if plugin is not None:
                self.active_plugins.append(plugin)


class PluginSpec:
    """Represents a plugin the engine knows about.

    Category: **App Classes**

    The 'enabled' attr represents whether this plugin is set to load.
    Getting or setting that attr affects the corresponding app-config
    key. Remember to commit the app-config after making any changes.

    The 'attempted_load' attr will be True if the engine has attempted
    to load the plugin. If 'attempted_load' is True for a PluginSpec
    but the 'plugin' attr is None, it means there was an error loading
    the plugin. If a plugin's api-version does not match the running
    app, if a new plugin is detected with auto-enable-plugins disabled,
    or if the user has explicitly disabled a plugin, the engine will not
    even attempt to load it.
    """

    def __init__(self, class_path: str, loadable: bool):
        self.class_path = class_path
        self.loadable = loadable
        self.attempted_load = False
        self.plugin: Plugin | None = None

    @property
    def enabled(self) -> bool:
        """Whether the user wants this plugin to load."""
        plugstates: dict[str, dict] = _babase.app.config.get('Plugins', {})
        assert isinstance(plugstates, dict)
        val = plugstates.get(self.class_path, {}).get('enabled', False) is True
        return val

    @enabled.setter
    def enabled(self, val: bool) -> None:
        plugstates: dict[str, dict] = _babase.app.config.setdefault(
            'Plugins', {}
        )
        assert isinstance(plugstates, dict)
        plugstate = plugstates.setdefault(self.class_path, {})
        plugstate['enabled'] = val

    def attempt_load_if_enabled(self) -> Plugin | None:
        """Possibly load the plugin and log any errors."""
        from babase._general import getclass
        from babase._language import Lstr

        assert not self.attempted_load
        assert self.plugin is None

        if not self.enabled:
            return None
        self.attempted_load = True
        if not self.loadable:
            return None
        try:
            cls = getclass(self.class_path, Plugin, True)
        except Exception as exc:
            _babase.getsimplesound('error').play()
            _babase.screenmessage(
                Lstr(
                    resource='pluginClassLoadErrorText',
                    subs=[
                        ('${PLUGIN}', self.class_path),
                        ('${ERROR}', str(exc)),
                    ],
                ),
                color=(1, 0, 0),
            )
            logging.exception(
                "Error loading plugin class '%s'.", self.class_path
            )
            return None
        try:
            self.plugin = cls()
            return self.plugin
        except Exception as exc:
            from babase import _error

            _babase.getsimplesound('error').play()
            _babase.screenmessage(
                Lstr(
                    resource='pluginInitErrorText',
                    subs=[
                        ('${PLUGIN}', self.class_path),
                        ('${ERROR}', str(exc)),
                    ],
                ),
                color=(1, 0, 0),
            )
            logging.exception(
                "Error initing plugin class: '%s'.", self.class_path
            )
        return None


class Plugin:
    """A plugin to alter app behavior in some way.

    Category: **App Classes**

    Plugins are discoverable by the meta-tag system
    and the user can select which ones they want to enable.
    Enabled plugins are then called at specific times as the
    app is running in order to modify its behavior in some way.
    """

    def on_app_running(self) -> None:
        """Called when the app reaches the running state."""

    def on_app_suspend(self) -> None:
        """Called when the app enters the suspended state."""

    def on_app_unsuspend(self) -> None:
        """Called when the app exits the suspended state."""

    def on_app_shutdown(self) -> None:
        """Called when the app is beginning the shutdown process."""

    def on_app_shutdown_complete(self) -> None:
        """Called when the app has completed the shutdown process."""

    def has_settings_ui(self) -> bool:
        """Called to ask if we have settings UI we can show."""
        return False

    def show_settings_ui(self, source_widget: Any | None) -> None:
        """Called to show our settings UI."""
