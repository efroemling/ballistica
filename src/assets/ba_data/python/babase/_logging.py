# Released under the MIT License. See LICENSE for details.
#
"""Logging functionality."""

from __future__ import annotations

import logging

# Our standard set of loggers.
balog = logging.getLogger('ba')
applog = logging.getLogger('ba.app')
lifecyclelog = logging.getLogger('ba.lifecycle')
