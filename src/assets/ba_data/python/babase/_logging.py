# Released under the MIT License. See LICENSE for details.
#
"""Logging functionality."""

from __future__ import annotations

import logging

from bacommon.logging import ClientLoggerName

# Keep a dict of logger descriptions so lookup is speedy, but lazy-init
# it since most users won't need it.
_g_logger_descs: dict[str, str] | None = None

# Common loggers we may want convenient access to.

#: Top-level Ballistica :class:`~logging.Logger` — use this to
#: adjust verbosity across everything Ballistica logs.
balog = logging.getLogger(ClientLoggerName.BA.value)

#: Logger for general app operation; ``INFO`` is visible by default.
applog = logging.getLogger(ClientLoggerName.APP.value)

#: Logger for asset loading — textures, sounds, models, etc.
assetslog = logging.getLogger(ClientLoggerName.ASSETS.value)

#: Logger for sound and music playback.
audiolog = logging.getLogger(ClientLoggerName.AUDIO.value)

#: Logger for the on-disk cache (pycache, downloaded assets, etc.).
cachelog = logging.getLogger(ClientLoggerName.CACHE.value)

#: Logger for display-time machinery (smooth animation timing).
displaytimelog = logging.getLogger(ClientLoggerName.DISPLAYTIME.value)

#: Logger for garbage-collection activity — useful for debugging
#: memory leaks and reference cycles.
gc_log = logging.getLogger(ClientLoggerName.GARBAGE_COLLECTION.value)

#: Logger for graphics-related messages.
gfxlog = logging.getLogger(ClientLoggerName.GRAPHICS.value)

#: Logger for performance investigations — render speed, hitches, etc.
perflog = logging.getLogger(ClientLoggerName.PERFORMANCE.value)

#: Logger for input devices — keyboards, touchscreens, gamepads, etc.
inputlog = logging.getLogger(ClientLoggerName.INPUT.value)

#: Logger for app lifecycle events — bootstrapping, pausing,
#: resuming, shutdown, etc.
lifecyclelog = logging.getLogger(ClientLoggerName.LIFECYCLE.value)

#: Logger for general networking activity.
netlog = logging.getLogger(ClientLoggerName.NETWORKING.value)

#: Logger for connectivity bring-up — picking the nearest/best
#: regional server.
connectivitylog = logging.getLogger(ClientLoggerName.CONNECTIVITY.value)

#: Logger for persistent v2 transport connections to regional
#: servers.
v2transportlog = logging.getLogger(ClientLoggerName.V2TRANSPORT.value)

#: Logger for cloud-subscription updates — live values fed from
#: regional servers.
cloudsublog = logging.getLogger(ClientLoggerName.CLOUD_SUBSCRIPTION.value)

#: Logger for account functionality.
accountlog = logging.getLogger(ClientLoggerName.ACCOUNT.value)

#: Logger for v2-account server communication.
accountclientv2log = logging.getLogger(ClientLoggerName.ACCOUNT_CLIENT_V2.value)

#: Logger for login-adapter support (per login-type plumbing).
loginadapterlog = logging.getLogger(ClientLoggerName.LOGIN_ADAPTER.value)

#: Logger for user-interface activity.
uilog = logging.getLogger(ClientLoggerName.UI.value)


def description_for_logger(logger: str) -> str | None:
    """Return a short description for a given logger.

    Used to populate the logger control dev console tab.
    """

    global _g_logger_descs  # pylint: disable=global-statement
    if _g_logger_descs is None:
        # Describe a few specific loggers here and also include our
        # client logger descriptions.
        _g_logger_descs = {
            'root': 'top level Python logger - use to adjust everything',
            'asyncio': 'Python\'s async/await functionality',
        }
        for clientlogger in ClientLoggerName:
            _g_logger_descs[clientlogger.value] = clientlogger.description

    return _g_logger_descs.get(logger)
