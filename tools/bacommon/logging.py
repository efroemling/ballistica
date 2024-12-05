# Released under the MIT License. See LICENSE for details.
#
"""Logging functionality."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from bacommon.loggercontrol import LoggerControlConfig

if TYPE_CHECKING:
    pass


def get_base_logger_control_config_client() -> LoggerControlConfig:
    """Return the logger-control-config used by the ballistica client.

    This should remain consistent since local logger configurations
    are stored relative to this.
    """

    # By default, go with WARNING on everything to keep things mostly
    # clean but show INFO for ba.app to get basic app startup messages
    # and whatnot.
    return LoggerControlConfig(
        levels={'root': logging.WARNING, 'ba.app': logging.INFO}
    )
