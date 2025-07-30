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
balog = logging.getLogger(ClientLoggerName.BA.value)
applog = logging.getLogger(ClientLoggerName.APP.value)
assetslog = logging.getLogger(ClientLoggerName.ASSETS.value)
audiolog = logging.getLogger(ClientLoggerName.AUDIO.value)
cachelog = logging.getLogger(ClientLoggerName.CACHE.value)
displaytimelog = logging.getLogger(ClientLoggerName.DISPLAYTIME.value)
gc_log = logging.getLogger(ClientLoggerName.GARBAGE_COLLECTION.value)
gfxlog = logging.getLogger(ClientLoggerName.GRAPHICS.value)
perflog = logging.getLogger(ClientLoggerName.PERFORMANCE.value)
inputlog = logging.getLogger(ClientLoggerName.INPUT.value)
lifecyclelog = logging.getLogger(ClientLoggerName.LIFECYCLE.value)
netlog = logging.getLogger(ClientLoggerName.NETWORKING.value)
connectivitylog = logging.getLogger(ClientLoggerName.CONNECTIVITY.value)
v2transportlog = logging.getLogger(ClientLoggerName.V2TRANSPORT.value)
cloudsublog = logging.getLogger(ClientLoggerName.CLOUD_SUBSCRIPTION.value)
accountlog = logging.getLogger(ClientLoggerName.ACCOUNT.value)
accountclientv2log = logging.getLogger(ClientLoggerName.ACCOUNT_CLIENT_V2.value)
loginadapterlog = logging.getLogger(ClientLoggerName.LOGIN_ADAPTER.value)


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
