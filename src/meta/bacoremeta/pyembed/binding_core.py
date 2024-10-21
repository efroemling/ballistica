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
    logging.NOTSET,  # kLoggingLevelNotSet
    logging.DEBUG,  # kLoggingLevelDebug
    logging.INFO,  # kLoggingLevelInfo
    logging.WARNING,  # kLoggingLevelWarning
    logging.ERROR,  # kLoggingLevelError
    logging.CRITICAL,  # kLoggingLevelCritical
    logging.getLogger('root'),  # kLoggerRoot
    logging.getLogger('root').log,  # kLoggerRootLogCall
    logging.getLogger('ba'),  # kLoggerBa
    logging.getLogger('ba').log,  # kLoggerBaLogCall
    logging.getLogger('ba.audio'),  # kLoggerBaAudio
    logging.getLogger('ba.audio').log,  # kLoggerBaAudioLogCall
    logging.getLogger('ba.graphics'),  # kLoggerBaGraphics
    logging.getLogger('ba.graphics').log,  # kLoggerBaGraphicsLogCall
    logging.getLogger('ba.lifecycle'),  # kLoggerBaLifecycle
    logging.getLogger('ba.lifecycle').log,  # kLoggerBaLifecycleLogCall
    logging.getLogger('ba.assets'),  # kLoggerBaAssets
    logging.getLogger('ba.assets').log,  # kLoggerBaAssetsLogCall
    logging.getLogger('ba.input'),  # kLoggerBaInput
    logging.getLogger('ba.input').log,  # kLoggerBaInputLogCall
    logging.getLogger('ba.networking'),  # kLoggerBaNetworking
    logging.getLogger('ba.networking').log,  # kLoggerBaNetworkingLogCall
]
