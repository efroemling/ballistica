# Released under the MIT License. See LICENSE for details.
#
"""Provides the AppConfig class."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any


class AppConfig(dict):
    """A special dict that holds the game's persistent configuration values.

    Category: **App Classes**

    It also provides methods for fetching values with app-defined fallback
    defaults, applying contained values to the game, and committing the
    config to storage.

    Call ba.appconfig() to get the single shared instance of this class.

    AppConfig data is stored as json on disk on so make sure to only place
    json-friendly values in it (dict, list, str, float, int, bool).
    Be aware that tuples will be quietly converted to lists when stored.
    """

    def resolve(self, key: str) -> Any:
        """Given a string key, return a config value (type varies).

        This will substitute application defaults for values not present in
        the config dict, filter some invalid values, etc.  Note that these
        values do not represent the state of the app; simply the state of its
        config. Use ba.App to access actual live state.

        Raises an Exception for unrecognized key names. To get the list of keys
        supported by this method, use ba.AppConfig.builtin_keys(). Note that it
        is perfectly legal to store other data in the config; it just needs to
        be accessed through standard dict methods and missing values handled
        manually.
        """
        return _ba.resolve_appconfig_value(key)

    def default_value(self, key: str) -> Any:
        """Given a string key, return its predefined default value.

        This is the value that will be returned by ba.AppConfig.resolve() if
        the key is not present in the config dict or of an incompatible type.

        Raises an Exception for unrecognized key names. To get the list of keys
        supported by this method, use ba.AppConfig.builtin_keys(). Note that it
        is perfectly legal to store other data in the config; it just needs to
        be accessed through standard dict methods and missing values handled
        manually.
        """
        return _ba.get_appconfig_default_value(key)

    def builtin_keys(self) -> list[str]:
        """Return the list of valid key names recognized by ba.AppConfig.

        This set of keys can be used with resolve(), default_value(), etc.
        It does not vary across platforms and may include keys that are
        obsolete or not relevant on the current running version. (for instance,
        VR related keys on non-VR platforms). This is to minimize the amount
        of platform checking necessary)

        Note that it is perfectly legal to store arbitrary named data in the
        config, but in that case it is up to the user to test for the existence
        of the key in the config dict, fall back to consistent defaults, etc.
        """
        return _ba.get_appconfig_builtin_keys()

    def apply(self) -> None:
        """Apply config values to the running app."""
        _ba.apply_config()

    def commit(self) -> None:
        """Commits the config to local storage.

        Note that this call is asynchronous so the actual write to disk may not
        occur immediately.
        """
        commit_app_config()

    def apply_and_commit(self) -> None:
        """Run apply() followed by commit(); for convenience.

        (This way the commit() will not occur if apply() hits invalid data)
        """
        self.apply()
        self.commit()


def read_config() -> tuple[AppConfig, bool]:
    """Read the game config."""
    import os
    import json
    from ba._generated.enums import TimeType

    config_file_healthy = False

    # NOTE: it is assumed that this only gets called once and the
    # config object will not change from here on out
    config_file_path = _ba.app.config_file_path
    config_contents = ''
    try:
        if os.path.exists(config_file_path):
            with open(config_file_path, encoding='utf-8') as infile:
                config_contents = infile.read()
            config = AppConfig(json.loads(config_contents))
        else:
            config = AppConfig()
        config_file_healthy = True

    except Exception as exc:
        print(
            (
                'error reading config file at time '
                + str(_ba.time(TimeType.REAL))
                + ': \''
                + config_file_path
                + '\':\n'
            ),
            exc,
        )

        # Whenever this happens lets back up the broken one just in case it
        # gets overwritten accidentally.
        print(
            (
                'backing up current config file to \''
                + config_file_path
                + ".broken\'"
            )
        )
        try:
            import shutil

            shutil.copyfile(config_file_path, config_file_path + '.broken')
        except Exception as exc2:
            print('EXC copying broken config:', exc2)
        config = AppConfig()

        # Now attempt to read one of our 'prev' backup copies.
        prev_path = config_file_path + '.prev'
        try:
            if os.path.exists(prev_path):
                with open(prev_path, encoding='utf-8') as infile:
                    config_contents = infile.read()
                config = AppConfig(json.loads(config_contents))
            else:
                config = AppConfig()
            config_file_healthy = True
            print('successfully read backup config.')
        except Exception as exc2:
            print('EXC reading prev backup config:', exc2)
    return config, config_file_healthy


def commit_app_config(force: bool = False) -> None:
    """Commit the config to persistent storage.

    Category: **General Utility Functions**

    (internal)
    """
    from ba._internal import mark_config_dirty

    if not _ba.app.config_file_healthy and not force:
        print(
            'Current config file is broken; '
            'skipping write to avoid losing settings.'
        )
        return
    mark_config_dirty()
