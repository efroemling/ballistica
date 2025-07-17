# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations

import uuid
import json
import copy
import logging
import sys

# IMPORTANT: The logger names we grab below are defined in
# bacommon.logging, but we need to grab our logger objects here in core
# before we are able to import modules, so we need to just hard code
# values here and keep them synced up.


def _uuid() -> str:
    return str(uuid.uuid4())


# The C++ layer looks for this variable:
values = [
    sys.modules['__main__'].__dict__,  # kMainDict
    tuple(),  # kEmptyTuple
    copy.deepcopy,  # kDeepCopyCall
    copy.copy,  # kShallowCopyCall
    json.dumps,  # kJsonDumpsCall
    json.loads,  # kJsonLoadsCall
    _uuid,  # kUUIDStrCall
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
    logging.getLogger('ba.app'),  # kLoggerBaApp
    logging.getLogger('ba.app').log,  # kLoggerBaAppLogCall
    logging.getLogger('ba.assets'),  # kLoggerBaAssets
    logging.getLogger('ba.assets').log,  # kLoggerBaAssetsLogCall
    logging.getLogger('ba.audio'),  # kLoggerBaAudio
    logging.getLogger('ba.audio').log,  # kLoggerBaAudioLogCall
    logging.getLogger('ba.displaytime'),  # kLoggerBaDisplayTime
    logging.getLogger('ba.displaytime').log,  # kLoggerBaDisplayTimeLogCall
    logging.getLogger('ba.gfx'),  # kLoggerBaGraphics
    logging.getLogger('ba.gfx').log,  # kLoggerBaGraphicsLogCall
    logging.getLogger('ba.perf'),  # kLoggerBaPerformance
    logging.getLogger('ba.perf').log,  # kLoggerBaPerformanceLogCall
    logging.getLogger('ba.input'),  # kLoggerBaInput
    logging.getLogger('ba.input').log,  # kLoggerBaInputLogCall
    logging.getLogger('ba.lifecycle'),  # kLoggerBaLifecycle
    logging.getLogger('ba.lifecycle').log,  # kLoggerBaLifecycleLogCall
    logging.getLogger('ba.net'),  # kLoggerBaNetworking
    logging.getLogger('ba.net').log,  # kLoggerBaNetworkingLogCall
]
