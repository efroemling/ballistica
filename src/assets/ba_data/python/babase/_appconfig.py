# Released under the MIT License. See LICENSE for details.
#
"""Provides the AppConfig class."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from typing import Any

_g_pending_apply = False  # pylint: disable=invalid-name


class AppConfig(dict):
    """A special dict that holds the game's persistent configuration values.

    Category: **App Classes**

    It also provides methods for fetching values with app-defined fallback
    defaults, applying contained values to the game, and committing the
    config to storage.

    Call babase.appconfig() to get the single shared instance of this class.

    AppConfig data is stored as json on disk on so make sure to only place
    json-friendly values in it (dict, list, str, float, int, bool).
    Be aware that tuples will be quietly converted to lists when stored.
    """

    def resolve(self, key: str) -> Any:
        """Given a string key, return a config value (type varies).

        This will substitute application defaults for values not present in
        the config dict, filter some invalid values, etc.  Note that these
        values do not represent the state of the app; simply the state of its
        config. Use babase.App to access actual live state.

        Raises an Exception for unrecognized key names. To get the list of keys
        supported by this method, use babase.AppConfig.builtin_keys(). Note
        that it is perfectly legal to store other data in the config; it just
        needs to be accessed through standard dict methods and missing values
        handled manually.
        """
        return _babase.resolve_appconfig_value(key)

    def default_value(self, key: str) -> Any:
        """Given a string key, return its predefined default value.

        This is the value that will be returned by babase.AppConfig.resolve()
        if the key is not present in the config dict or of an incompatible
        type.

        Raises an Exception for unrecognized key names. To get the list of keys
        supported by this method, use babase.AppConfig.builtin_keys(). Note
        that it is perfectly legal to store other data in the config; it just
        needs to be accessed through standard dict methods and missing values
        handled manually.
        """
        return _babase.get_appconfig_default_value(key)

    def builtin_keys(self) -> list[str]:
        """Return the list of valid key names recognized by babase.AppConfig.

        This set of keys can be used with resolve(), default_value(), etc.
        It does not vary across platforms and may include keys that are
        obsolete or not relevant on the current running version. (for instance,
        VR related keys on non-VR platforms). This is to minimize the amount
        of platform checking necessary)

        Note that it is perfectly legal to store arbitrary named data in the
        config, but in that case it is up to the user to test for the existence
        of the key in the config dict, fall back to consistent defaults, etc.
        """
        return _babase.get_appconfig_builtin_keys()

    def apply(self) -> None:
        """Apply config values to the running app.

        This call is thread-safe and asynchronous; changes will happen
        in the next logic event loop cycle.
        """
        _babase.app.push_apply_app_config()

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


def commit_app_config() -> None:
    """Commit the config to persistent storage.

    Category: **General Utility Functions**

    (internal)
    """
    # FIXME - this should not require plus.
    plus = _babase.app.plus
    assert plus is not None

    plus.mark_config_dirty()
