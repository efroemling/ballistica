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
    """Return the logger-control-config used by the ballistica client."""

    # Just info for everything by default.
    return LoggerControlConfig(levels={'root': logging.INFO})
