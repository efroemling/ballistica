# Released under the MIT License. See LICENSE for details.
#
"""Provides the AppConfig class."""

import json
import logging
from typing import TYPE_CHECKING

from efro.util import strip_exception_tracebacks

import _babase

if TYPE_CHECKING:
    from typing import Any

# How long we wait for changes to stop coming in before writing the
# config to disk (batches rapid change streams into a single write).
_COMMIT_QUIET_SECONDS = 5.0

# ...but never delay a write longer than this after the oldest
# uncommitted change, even if changes keep coming in.
_COMMIT_MAX_DELAY_SECONDS = 20.0


class AppConfig(dict):
    """A special dict that holds persistent app configuration values.

    It also provides methods for fetching values with app-defined
    fallback defaults, applying contained values to the game, and
    committing the config to storage.

    Access the single shared instance of this config via the
    :attr:`~babase.App.config` attr on the :class:`~babase.App` class.

    App-config data is stored as json on disk on so make sure to only
    place json-friendly values in it (``dict``, ``list``, ``str``,
    ``float``, ``int``, ``bool``). Be aware that tuples will be quietly
    converted to lists when stored.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._oldest_dirty_time: float | None = None
        self._newest_dirty_time: float | None = None
        self._commit_timer_pending = False

    def resolve(self, key: str) -> Any:
        """Given a string key, return a config value (type varies).

        This will substitute application defaults for values not present
        in the config dict, filter some invalid values, etc. Note that
        these values do not represent the state of the app; simply the
        state of its config. Use the :class:`~babase.App` class to
        access actual live state.

        Raises an :class:`KeyError` for unrecognized key names. To get
        the list of keys supported by this method, use
        :meth:`builtin_keys()`. Note that it is perfectly legal to store
        other data in the config; it just needs to be accessed through
        standard dict methods and missing values handled manually.
        """
        return _babase.resolve_appconfig_value(key)

    def default_value(self, key: str) -> Any:
        """Given a string key, return its predefined default value.

        This is the value that will be returned by :meth:`resolve()` if
        the key is not present in the config dict or of an incompatible
        type.

        Raises an Exception for unrecognized key names. To get the list
        of keys supported by this method, use
        babase.AppConfig.builtin_keys(). Note that it is perfectly legal
        to store other data in the config; it just needs to be accessed
        through standard dict methods and missing values handled
        manually.
        """
        return _babase.get_appconfig_default_value(key)

    def builtin_keys(self) -> list[str]:
        """Return the list of valid key names recognized by this class.

        This set of keys can be used with :meth:`resolve()`,
        :meth:`default_value()`, etc. It does not vary across platforms
        and may include keys that are obsolete or not relevant on the
        current running version. (for instance, VR related keys on
        non-VR platforms). This is to minimize the amount of platform
        checking necessary)

        Note that it is perfectly legal to store arbitrary named data in
        the config, but in that case it is up to the user to test for
        the existence of the key in the config dict, fall back to
        consistent defaults, etc.
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

        Note that this call is asynchronous so the actual write to disk
        may not occur immediately.
        """
        commit_app_config()

    def apply_and_commit(self) -> None:
        """Shortcut to run :meth:`apply()` followed by :meth:`commit()`.

        This way the :meth:`commit()` will not occur if :meth:`apply()`
        hits invalid data, which is generally desirable.
        """
        self.apply()
        self.commit()

    def mark_dirty(self) -> None:
        """Schedule an asynchronous write of the config to disk.

        The write happens once changes stop coming in for a few
        seconds (or after a fixed maximum delay if they don't stop).
        A write is also triggered by app-suspend and app-shutdown, so
        no changes should be lost even if the app is killed shortly
        after a change.

        :meta private:
        """
        assert _babase.in_logic_thread()
        now = _babase.apptime()
        if self._oldest_dirty_time is None:
            self._oldest_dirty_time = now
        self._newest_dirty_time = now
        if not self._commit_timer_pending:
            self._commit_timer_pending = True
            # Use an empty context so our timer doesn't die with
            # whatever game context we happen to be called under.
            with _babase.ContextRef.empty():
                _babase.apptimer(
                    _COMMIT_QUIET_SECONDS + 0.01, self._commit_timer_cb
                )

    def commit_if_dirty(self) -> None:
        """Immediately write the config to disk if changes are pending.

        Called by the app at suspend/shutdown time; changes are
        normally written via the asynchronous :meth:`mark_dirty()`
        machinery.

        :meta private:
        """
        assert _babase.in_logic_thread()
        if self._oldest_dirty_time is None:
            return
        self._commit_to_disk()

    def _commit_timer_cb(self) -> None:
        self._commit_timer_pending = False
        if self._oldest_dirty_time is None:
            # Something else (suspend/shutdown) already wrote us.
            return
        now = _babase.apptime()
        assert self._newest_dirty_time is not None
        if (
            now - self._newest_dirty_time >= _COMMIT_QUIET_SECONDS
            or now - self._oldest_dirty_time >= _COMMIT_MAX_DELAY_SECONDS
        ):
            self._commit_to_disk()
            return
        # Changes are still coming in; check again when the next
        # threshold will be hit.
        delay = min(
            self._newest_dirty_time + _COMMIT_QUIET_SECONDS - now,
            self._oldest_dirty_time + _COMMIT_MAX_DELAY_SECONDS - now,
        )
        self._commit_timer_pending = True
        with _babase.ContextRef.empty():
            _babase.apptimer(max(delay, 0.0) + 0.01, self._commit_timer_cb)

    def _commit_to_disk(self) -> None:
        self._oldest_dirty_time = None
        self._newest_dirty_time = None
        try:
            cfgs = json.dumps(self, indent=1, sort_keys=True)
        except Exception as exc:
            # This is almost always a mod having stored a
            # non-json-friendly value in the config. Prominently name
            # exactly what we're dropping (the paths are what identify
            # the culprit) and write the config without those entries
            # so one bad value doesn't break config saving forever.
            # Dropping beats coercing here; a mod finding its data
            # absent falls back to defaults, while finding it subtly
            # mangled leads to confusing misbehavior.
            strip_exception_tracebacks(exc)
            dropped: list[str] = []
            pruned = _pruned_json(dict(self), 'config', dropped)
            if len(dropped) > 10:
                droppeddesc = (
                    '; '.join(dropped[:10]) + f'; (+{len(dropped) - 10} more)'
                )
            elif dropped:
                droppeddesc = '; '.join(dropped)
            else:
                droppeddesc = '<unable to determine offenders>'
            logging.error(
                'Unable to fully serialize app config; writing it with'
                ' non-json-friendly entries removed (%s).'
                ' This usually means a mod or plugin stored a'
                ' non-json-friendly value in the config.',
                droppeddesc,
            )
            # (No sort_keys here; a mixed-key-type dict would break it.)
            cfgs = json.dumps(pruned, indent=1)
        _babase.commit_app_config(cfgs)


# Sentinel used by _pruned_json() to signal 'remove this value'.
_DROPPED = object()


def _pruned_json(data: Any, path: str, dropped: list[str]) -> Any:
    """Return a copy of a data structure with non-json-friendly bits removed.

    Containers are copied with offending children removed; an offending
    value itself yields the module-private ``_DROPPED`` sentinel. Paths
    of removed entries are appended to ``dropped``.
    """
    # (Any in/out since arbitrary values can be present anywhere in the
    # structure; that is the problem we're solving.)
    if isinstance(data, (str, int, float, bool, type(None))):
        return data
    if isinstance(data, dict):
        outdict: dict = {}
        for key, val in list(data.items()):
            # These key types are handled natively by json (coerced to
            # strings); anything else gets its entry dropped.
            if isinstance(key, (str, int, float, bool, type(None))):
                keypath = f'{path}[{key!r}]'
                pval = _pruned_json(val, keypath, dropped)
                if pval is _DROPPED:
                    dropped.append(keypath)
                else:
                    outdict[key] = pval
            else:
                dropped.append(f'{path} (key {key!r})')
        return outdict
    if isinstance(data, (list, tuple)):
        outlist: list = []
        for i, val in enumerate(data):
            pval = _pruned_json(val, f'{path}[{i}]', dropped)
            if pval is _DROPPED:
                dropped.append(f'{path}[{i}]')
            else:
                outlist.append(pval)
        return outlist
    return _DROPPED


def commit_app_config() -> None:
    """Commit the config to persistent storage.

    :meta private:
    """
    _babase.app.config.mark_dirty()
