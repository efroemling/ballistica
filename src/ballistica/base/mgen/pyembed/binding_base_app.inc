{
// Python code from babasemeta/pyembed/binding_base_app.py:
const char* bindcode =
  "# Released under the MIT License. See LICENSE for details.\n"
  "# Where most of our python-c++ binding happens.\n"
  "# Python objects should be added here along with their associated c++ enum.\n"
  "# pylint: disable=useless-suppression, missing-module-docstring, line-too-long\n"
  "from __future__ import annotations\n"
  "from babase import app\n"
  "\n"
  "# The C++ layer looks for this variable:\n"
  "values = [\n"
  "    app,  # kApp\n"
  "    app.handle_deep_link,  # kAppHandleDeepLinkCall\n"
  "    app.lang.get_resource,  # kGetResourceCall\n"
  "    app.lang.translate,  # kTranslateCall\n"
  "    app.push_apply_app_config,  # kAppPushApplyAppConfigCall\n"
  "    app.on_native_start,  # kAppOnNativeStartCall\n"
  "    app.on_native_bootstrapping_complete,  # kAppOnNativeBootstrappingCompleteCall\n"
  "    app.on_native_suspend,  # kAppOnNativeSuspendCall\n"
  "    app.on_native_unsuspend,  # kAppOnNativeUnsuspendCall\n"
  "    app.on_native_shutdown,  # kAppOnNativeShutdownCall\n"
  "    app.on_native_shutdown_complete,  # kAppOnNativeShutdownCompleteCall\n"
  "    app.shutdown_fault_handler_arm,  # kAppShutdownFaultHandlerArmCall\n"
  "    app.shutdown_fault_handler_disarm,  # kAppShutdownFaultHandlerDisarmCall\n"
  "    app.on_native_active_changed,  # kAppOnNativeActiveChangedCall\n"
  "    app.devconsole.do_refresh_tab,  # kAppDevConsoleDoRefreshTabCall\n"
  "    app.devconsole.save_tab,  # kAppDevConsoleSaveTabCall\n"
  "    app.on_screen_size_change,  # kAppOnScreenSizeChangeCall\n"
  "    app.gc.collect,  # kAppGCCollectCall\n"
  "]\n";

// Exec the Python code in an empty context.
auto ctx = PythonRef::Stolen(PyDict_New());
bool success = PythonCommand(bindcode, "binding_base_app.py").Exec(true, *ctx, *ctx);
if (!success) {
  FatalError("Error fetching required Python objects.");
}

// Grab the 'values' list that the binding code created.
auto bindvals = ctx.DictGetItem("values");
if (!bindvals.exists() || !PyList_Check(*bindvals)) {
  FatalError("Error binding required Python objects.");
}

// Pull our various obj_ values from the values list.
objs_.Store(ObjID::kApp, PyList_GET_ITEM(bindvals.get(), 0));
objs_.StoreCallable(ObjID::kAppHandleDeepLinkCall, PyList_GET_ITEM(bindvals.get(), 1));
objs_.StoreCallable(ObjID::kGetResourceCall, PyList_GET_ITEM(bindvals.get(), 2));
objs_.StoreCallable(ObjID::kTranslateCall, PyList_GET_ITEM(bindvals.get(), 3));
objs_.StoreCallable(ObjID::kAppPushApplyAppConfigCall, PyList_GET_ITEM(bindvals.get(), 4));
objs_.StoreCallable(ObjID::kAppOnNativeStartCall, PyList_GET_ITEM(bindvals.get(), 5));
objs_.StoreCallable(ObjID::kAppOnNativeBootstrappingCompleteCall, PyList_GET_ITEM(bindvals.get(), 6));
objs_.StoreCallable(ObjID::kAppOnNativeSuspendCall, PyList_GET_ITEM(bindvals.get(), 7));
objs_.StoreCallable(ObjID::kAppOnNativeUnsuspendCall, PyList_GET_ITEM(bindvals.get(), 8));
objs_.StoreCallable(ObjID::kAppOnNativeShutdownCall, PyList_GET_ITEM(bindvals.get(), 9));
objs_.StoreCallable(ObjID::kAppOnNativeShutdownCompleteCall, PyList_GET_ITEM(bindvals.get(), 10));
objs_.StoreCallable(ObjID::kAppShutdownFaultHandlerArmCall, PyList_GET_ITEM(bindvals.get(), 11));
objs_.StoreCallable(ObjID::kAppShutdownFaultHandlerDisarmCall, PyList_GET_ITEM(bindvals.get(), 12));
objs_.StoreCallable(ObjID::kAppOnNativeActiveChangedCall, PyList_GET_ITEM(bindvals.get(), 13));
objs_.StoreCallable(ObjID::kAppDevConsoleDoRefreshTabCall, PyList_GET_ITEM(bindvals.get(), 14));
objs_.StoreCallable(ObjID::kAppDevConsoleSaveTabCall, PyList_GET_ITEM(bindvals.get(), 15));
objs_.StoreCallable(ObjID::kAppOnScreenSizeChangeCall, PyList_GET_ITEM(bindvals.get(), 16));
objs_.StoreCallable(ObjID::kAppGCCollectCall, PyList_GET_ITEM(bindvals.get(), 17));
}
