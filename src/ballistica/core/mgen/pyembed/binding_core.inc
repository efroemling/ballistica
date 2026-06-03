{
// Python code from bacoremeta/pyembed/binding_core.py:
const char* bindcode =
  "# Released under the MIT License. See LICENSE for details.\n"
  "# Where most of our python-c++ binding happens.\n"
  "# Python objects should be added here along with their associated c++ enum.\n"
  "# pylint: disable=useless-suppression, missing-module-docstring, line-too-long\n"
  "from __future__ import annotations\n"
  "\n"
  "import uuid\n"
  "import json\n"
  "import copy\n"
  "import logging\n"
  "import sys\n"
  "\n"
  "# IMPORTANT: The logger names we grab below are defined in\n"
  "# bacommon.logging, but we need to grab our logger objects here in core\n"
  "# before we are able to import modules, so we need to just hard code\n"
  "# values here and keep them synced up.\n"
  "\n"
  "\n"
  "def _uuid() -> str:\n"
  "    return str(uuid.uuid4())\n"
  "\n"
  "\n"
  "# The C++ layer looks for this variable:\n"
  "values = [\n"
  "    sys.modules['__main__'].__dict__,  # kMainDict\n"
  "    tuple(),  # kEmptyTuple\n"
  "    copy.deepcopy,  # kDeepCopyCall\n"
  "    copy.copy,  # kShallowCopyCall\n"
  "    json.dumps,  # kJsonDumpsCall\n"
  "    json.loads,  # kJsonLoadsCall\n"
  "    _uuid,  # kUUIDStrCall\n"
  "    logging.NOTSET,  # kLoggingLevelNotSet\n"
  "    logging.DEBUG,  # kLoggingLevelDebug\n"
  "    logging.INFO,  # kLoggingLevelInfo\n"
  "    logging.WARNING,  # kLoggingLevelWarning\n"
  "    logging.ERROR,  # kLoggingLevelError\n"
  "    logging.CRITICAL,  # kLoggingLevelCritical\n"
  "    logging.getLogger('root'),  # kLoggerRoot\n"
  "    logging.getLogger('root').log,  # kLoggerRootLogCall\n"
  "    logging.getLogger('ba'),  # kLoggerBa\n"
  "    logging.getLogger('ba').log,  # kLoggerBaLogCall\n"
  "    logging.getLogger('ba.app'),  # kLoggerBaApp\n"
  "    logging.getLogger('ba.app').log,  # kLoggerBaAppLogCall\n"
  "    logging.getLogger('ba.assets'),  # kLoggerBaAssets\n"
  "    logging.getLogger('ba.assets').log,  # kLoggerBaAssetsLogCall\n"
  "    logging.getLogger('ba.account'),  # kLoggerBaAccount\n"
  "    logging.getLogger('ba.account').log,  # kLoggerBaAccountLogCall\n"
  "    logging.getLogger('ba.audio'),  # kLoggerBaAudio\n"
  "    logging.getLogger('ba.audio').log,  # kLoggerBaAudioLogCall\n"
  "    logging.getLogger('ba.displaytime'),  # kLoggerBaDisplayTime\n"
  "    logging.getLogger('ba.displaytime').log,  # kLoggerBaDisplayTimeLogCall\n"
  "    logging.getLogger('ba.gfx'),  # kLoggerBaGraphics\n"
  "    logging.getLogger('ba.gfx').log,  # kLoggerBaGraphicsLogCall\n"
  "    logging.getLogger('ba.perf'),  # kLoggerBaPerformance\n"
  "    logging.getLogger('ba.perf').log,  # kLoggerBaPerformanceLogCall\n"
  "    logging.getLogger('ba.input'),  # kLoggerBaInput\n"
  "    logging.getLogger('ba.input').log,  # kLoggerBaInputLogCall\n"
  "    logging.getLogger('ba.ui'),  # kLoggerBaUI\n"
  "    logging.getLogger('ba.ui').log,  # kLoggerBaUILogCall\n"
  "    logging.getLogger('ba.lifecycle'),  # kLoggerBaLifecycle\n"
  "    logging.getLogger('ba.lifecycle').log,  # kLoggerBaLifecycleLogCall\n"
  "    logging.getLogger('ba.net'),  # kLoggerBaNetworking\n"
  "    logging.getLogger('ba.net').log,  # kLoggerBaNetworkingLogCall\n"
  "    logging.getLogger('ba.discord'),  # kLoggerBaDiscord\n"
  "    logging.getLogger('ba.discord').log,  # kLoggerBaDiscordLogCall\n"
  "]\n";

// Exec the Python code in an empty context.
auto ctx = PythonRef::Stolen(PyDict_New());
bool success = PythonCommand(bindcode, "binding_core.py").Exec(true, *ctx, *ctx);
if (!success) {
  FatalError("Error fetching required Python objects.");
}

// Grab the 'values' list that the binding code created.
auto bindvals = ctx.DictGetItem("values");
if (!bindvals.exists() || !PyList_Check(*bindvals)) {
  FatalError("Error binding required Python objects.");
}

// Pull our various obj_ values from the values list.
objs_.Store(ObjID::kMainDict, PyList_GET_ITEM(bindvals.get(), 0));
objs_.Store(ObjID::kEmptyTuple, PyList_GET_ITEM(bindvals.get(), 1));
objs_.StoreCallable(ObjID::kDeepCopyCall, PyList_GET_ITEM(bindvals.get(), 2));
objs_.StoreCallable(ObjID::kShallowCopyCall, PyList_GET_ITEM(bindvals.get(), 3));
objs_.StoreCallable(ObjID::kJsonDumpsCall, PyList_GET_ITEM(bindvals.get(), 4));
objs_.StoreCallable(ObjID::kJsonLoadsCall, PyList_GET_ITEM(bindvals.get(), 5));
objs_.StoreCallable(ObjID::kUUIDStrCall, PyList_GET_ITEM(bindvals.get(), 6));
objs_.Store(ObjID::kLoggingLevelNotSet, PyList_GET_ITEM(bindvals.get(), 7));
objs_.Store(ObjID::kLoggingLevelDebug, PyList_GET_ITEM(bindvals.get(), 8));
objs_.Store(ObjID::kLoggingLevelInfo, PyList_GET_ITEM(bindvals.get(), 9));
objs_.Store(ObjID::kLoggingLevelWarning, PyList_GET_ITEM(bindvals.get(), 10));
objs_.Store(ObjID::kLoggingLevelError, PyList_GET_ITEM(bindvals.get(), 11));
objs_.Store(ObjID::kLoggingLevelCritical, PyList_GET_ITEM(bindvals.get(), 12));
objs_.Store(ObjID::kLoggerRoot, PyList_GET_ITEM(bindvals.get(), 13));
objs_.StoreCallable(ObjID::kLoggerRootLogCall, PyList_GET_ITEM(bindvals.get(), 14));
objs_.Store(ObjID::kLoggerBa, PyList_GET_ITEM(bindvals.get(), 15));
objs_.StoreCallable(ObjID::kLoggerBaLogCall, PyList_GET_ITEM(bindvals.get(), 16));
objs_.Store(ObjID::kLoggerBaApp, PyList_GET_ITEM(bindvals.get(), 17));
objs_.StoreCallable(ObjID::kLoggerBaAppLogCall, PyList_GET_ITEM(bindvals.get(), 18));
objs_.Store(ObjID::kLoggerBaAssets, PyList_GET_ITEM(bindvals.get(), 19));
objs_.StoreCallable(ObjID::kLoggerBaAssetsLogCall, PyList_GET_ITEM(bindvals.get(), 20));
objs_.Store(ObjID::kLoggerBaAccount, PyList_GET_ITEM(bindvals.get(), 21));
objs_.StoreCallable(ObjID::kLoggerBaAccountLogCall, PyList_GET_ITEM(bindvals.get(), 22));
objs_.Store(ObjID::kLoggerBaAudio, PyList_GET_ITEM(bindvals.get(), 23));
objs_.StoreCallable(ObjID::kLoggerBaAudioLogCall, PyList_GET_ITEM(bindvals.get(), 24));
objs_.Store(ObjID::kLoggerBaDisplayTime, PyList_GET_ITEM(bindvals.get(), 25));
objs_.StoreCallable(ObjID::kLoggerBaDisplayTimeLogCall, PyList_GET_ITEM(bindvals.get(), 26));
objs_.Store(ObjID::kLoggerBaGraphics, PyList_GET_ITEM(bindvals.get(), 27));
objs_.StoreCallable(ObjID::kLoggerBaGraphicsLogCall, PyList_GET_ITEM(bindvals.get(), 28));
objs_.Store(ObjID::kLoggerBaPerformance, PyList_GET_ITEM(bindvals.get(), 29));
objs_.StoreCallable(ObjID::kLoggerBaPerformanceLogCall, PyList_GET_ITEM(bindvals.get(), 30));
objs_.Store(ObjID::kLoggerBaInput, PyList_GET_ITEM(bindvals.get(), 31));
objs_.StoreCallable(ObjID::kLoggerBaInputLogCall, PyList_GET_ITEM(bindvals.get(), 32));
objs_.Store(ObjID::kLoggerBaUI, PyList_GET_ITEM(bindvals.get(), 33));
objs_.StoreCallable(ObjID::kLoggerBaUILogCall, PyList_GET_ITEM(bindvals.get(), 34));
objs_.Store(ObjID::kLoggerBaLifecycle, PyList_GET_ITEM(bindvals.get(), 35));
objs_.StoreCallable(ObjID::kLoggerBaLifecycleLogCall, PyList_GET_ITEM(bindvals.get(), 36));
objs_.Store(ObjID::kLoggerBaNetworking, PyList_GET_ITEM(bindvals.get(), 37));
objs_.StoreCallable(ObjID::kLoggerBaNetworkingLogCall, PyList_GET_ITEM(bindvals.get(), 38));
objs_.Store(ObjID::kLoggerBaDiscord, PyList_GET_ITEM(bindvals.get(), 39));
objs_.StoreCallable(ObjID::kLoggerBaDiscordLogCall, PyList_GET_ITEM(bindvals.get(), 40));
}
