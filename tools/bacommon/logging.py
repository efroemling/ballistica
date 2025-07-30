# Released under the MIT License. See LICENSE for details.
#
"""Logging functionality."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, assert_never
from bacommon.loggercontrol import LoggerControlConfig

if TYPE_CHECKING:
    pass


# IMPORTANT: If making any changes here, be sure to update
# binding_core.py and baenv.py where some of these same values are
# hard-coded at engine init (when they don't yet have access to this
# module).


class ClientLoggerName(Enum):
    """Logger names used on the Ballistica client."""

    BA = 'ba'
    ENV = 'ba.env'
    APP = 'ba.app'
    ASSETS = 'ba.assets'
    AUDIO = 'ba.audio'
    CACHE = 'ba.cache'
    DISPLAYTIME = 'ba.displaytime'
    GARBAGE_COLLECTION = 'ba.gc'
    GRAPHICS = 'ba.gfx'
    PERFORMANCE = 'ba.perf'
    INPUT = 'ba.input'
    LIFECYCLE = 'ba.lifecycle'
    NETWORKING = 'ba.net'
    CONNECTIVITY = 'ba.connectivity'
    V2TRANSPORT = 'ba.v2transport'
    CLOUD_SUBSCRIPTION = 'ba.cloudsub'
    ACCOUNT_CLIENT_V2 = 'ba.accountclientv2'
    ACCOUNT = 'ba.account'
    LOGIN_ADAPTER = 'ba.loginadapter'

    @property
    def description(self) -> str:
        """Return a short description for the logger."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        cls = type(self)
        if self is cls.BA:
            return 'top level Ballistica logger - use to adjust everything'
        if self is cls.ENV:
            return 'engine environment bootstrapping'
        if self is cls.APP:
            return 'general app operation - INFO is visible by default'
        if self is cls.ASSETS:
            return 'textures, sounds, models, etc.'
        if self is cls.AUDIO:
            return 'sound and music playback'
        if self is cls.CACHE:
            return 'cache dir - holds pycache, assets, etc.'
        if self is cls.DISPLAYTIME:
            return 'timing for smooth animation display'
        if self is cls.GARBAGE_COLLECTION:
            return 'garbage collection - debug memory leaks/etc.'
        if self is cls.GRAPHICS:
            return 'anything graphics related'
        if self is cls.PERFORMANCE:
            return 'debug rendering speed, hitches, etc.'
        if self is cls.INPUT:
            return 'keyboards, touchscreens, game-controllers, etc.'
        if self is cls.LIFECYCLE:
            return 'bootstrapping, pausing, resuming, shutdown, etc.'
        if self is cls.NETWORKING:
            return 'anything network related'
        if self is cls.CONNECTIVITY:
            return 'determining nearest/best regional servers'
        if self is cls.V2TRANSPORT:
            return 'persistent connections to regional servers'
        if self is cls.CLOUD_SUBSCRIPTION:
            return 'live values fed from regional server'
        if self is cls.ACCOUNT_CLIENT_V2:
            return 'server communication for v2 accounts'
        if self is cls.ACCOUNT:
            return 'account functionality'
        if self is cls.LOGIN_ADAPTER:
            return 'support for particular login types'
        assert_never(self)


def get_base_logger_control_config_client() -> LoggerControlConfig:
    """Return the logger-control-config used by the Ballistica client.

    This should remain consistent since local logger configurations
    are stored relative to this.
    """

    # By default, go with WARNING on everything to keep things mostly
    # clean but show INFO for ba.app to get basic app startup messages
    # and whatnot.
    return LoggerControlConfig(
        levels={
            'root': logging.WARNING,
            ClientLoggerName.APP.value: logging.INFO,
        }
    )
