# Released under the MIT License. See LICENSE for details.
#
"""Choosing between cloud-provided and user-set logger levels.

The server can hand clients a logger-level config via persistent
cloud-vals (:attr:`bacommon.cloud.CloudValsPersistent.logger_control`).
Whether that config or the user's own manual levels are in effect is
the user's choice, via the ``'Cloud Logger Control'`` app-config
toggle (enabled by default; surfaced in the dev-console logging tab).

The chosen config is applied at launch by ``baenv._set_log_levels()``
(which reads the same app-config values this module does, before any
of babase exists); this module owns the runtime side: the toggle, the
mid-run re-applies, and the run-scoped :func:`cloud_controlled_logging`
flag that rides along with cloud log reports.
"""

import os
from typing import TYPE_CHECKING

import _babase
from babase._logging import applog

if TYPE_CHECKING:
    from bacommon.loggercontrol import LoggerControlConfig

#: App-config key for the user-facing toggle choosing whether the
#: cloud-provided logger config (True; the default when unset) or
#: their own manual levels drive logger levels. Also read at launch
#: by ``baenv._set_log_levels()`` - keep the two in sync.
CLOUD_LOGGER_CONTROL_CONFIG_KEY = 'Cloud Logger Control'

# Whether cloud logger control has been continuously in effect since
# launch (see cloud_controlled_logging()). None until first computed.
_g_cloud_controlled_logging: bool | None = None


def cloud_logger_control_enabled() -> bool:
    """Is the user's cloud-logger-control toggle currently enabled?

    :meta private:
    """
    val = _babase.app.config.get(CLOUD_LOGGER_CONTROL_CONFIG_KEY, True)
    return val if isinstance(val, bool) else True


def cloud_controlled_logging() -> bool:
    """Have logger levels been cloud-controlled for this whole run?

    True only if the cloud-logger-control toggle was enabled at launch
    and has never been switched off during this run, and no local
    override (the ``BA_LOG_LEVELS`` env var) is in effect. Toggling
    the control off even momentarily clears this for the rest of the
    run - a brief window of user-set levels means the run's log
    output can no longer be assumed to reflect the server's config.

    Rides along with cloud log reports so report consumers can filter
    for clients showing exactly the levels the server asked for.

    :meta private:
    """
    global _g_cloud_controlled_logging  # pylint: disable=global-statement

    if _g_cloud_controlled_logging is None:
        # Nothing can flip the toggle without coming through
        # set_cloud_logger_control_enabled() (which computes us
        # first), so a lazy first read here still reflects launch
        # state.
        _g_cloud_controlled_logging = (
            os.environ.get('BA_LOG_LEVELS') is None
            and cloud_logger_control_enabled()
        )
    return _g_cloud_controlled_logging


def set_cloud_logger_control_enabled(enabled: bool) -> None:
    """Set the cloud-logger-control toggle and re-apply levels.

    :meta private:
    """
    global _g_cloud_controlled_logging  # pylint: disable=global-statement

    # Lock in the launch-state flag *before* touching config; once
    # the control has been switched off, this run is permanently no
    # longer fully cloud-controlled (switching back on doesn't
    # restore it).
    cloud_controlled_logging()
    if not enabled:
        _g_cloud_controlled_logging = False

    appconfig = _babase.app.config
    appconfig[CLOUD_LOGGER_CONTROL_CONFIG_KEY] = enabled
    appconfig.commit()

    apply_effective_logger_config()


def handle_cloud_logger_config_changed() -> None:
    """Put a freshly arrived cloud logger config into effect.

    Called by the cloud subsystem when new persistent cloud-vals land
    mid-run, so a config change the server pushes takes effect without
    waiting for the next launch. No-op when the user has cloud
    control switched off or a ``BA_LOG_LEVELS`` env override (a
    launch-scoped total override) is active.

    :meta private:
    """
    if os.environ.get('BA_LOG_LEVELS') is not None:
        return
    if not cloud_logger_control_enabled():
        return
    apply_effective_logger_config()


def apply_effective_logger_config() -> None:
    """(Re)apply whichever logger config should currently be in effect.

    Cloud control enabled: the base client config plus the server's
    diff (or just the base config when the server hasn't provided
    one - base defaults are what the server 'wants' in that case).
    Disabled: the base config plus the user's own stored
    ``'Log Levels'`` diff. Mirrors the launch-time logic in
    ``baenv._set_log_levels()``.

    :meta private:
    """
    from bacommon.logging import get_base_logger_control_config_client
    from bacommon.loggercontrol import LoggerControlConfig

    baseconfig = get_base_logger_control_config_client()

    diff: LoggerControlConfig | None = None
    try:
        if cloud_logger_control_enabled():
            diff = _current_cloud_logger_config()
        else:
            levels = _babase.app.config.get('Log Levels')
            if isinstance(levels, dict) and all(
                isinstance(name, str) and isinstance(level, int)
                for name, level in levels.items()
            ):
                diff = LoggerControlConfig(levels=levels)
    except Exception:
        applog.exception('Error building effective logger config.')

    if diff is None:
        baseconfig.apply()
    else:
        baseconfig.apply_diff(diff).apply()

    # Let the native layer know that levels may have changed.
    _babase.update_internal_logger_levels()


def _current_cloud_logger_config() -> LoggerControlConfig | None:
    """The latest cloud-provided logger config, if any."""
    plus = _babase.app.plus
    if plus is None:
        return None
    # Note: assigning through a typed local here; in spinoffs built
    # without the plus feature-set, plus is a dummy-module and this
    # expression is untyped.
    config: LoggerControlConfig | None = (
        plus.cloud.vals_persistent.logger_control
    )
    return config
