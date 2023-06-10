# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations

import json
import copy
import logging
import sys

# The C++ layer looks for this variable:
values = [
    sys.modules['__main__'].__dict__,  # kMainDict
    tuple(),  # kEmptyTuple
    copy.deepcopy,  # kDeepCopyCall
    copy.copy,  # kShallowCopyCall
    json.dumps,  # kJsonDumpsCall
    json.loads,  # kJsonLoadsCall
    logging.debug,  # kLoggingDebugCall
    logging.info,  # kLoggingInfoCall
    logging.warning,  # kLoggingWarningCall
    logging.error,  # kLoggingErrorCall
    logging.critical,  # kLoggingCriticalCall
]
