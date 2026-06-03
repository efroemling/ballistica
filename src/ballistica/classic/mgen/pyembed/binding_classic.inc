{
// Python code from baclassicmeta/pyembed/binding_classic.py:
const char* bindcode =
  "# Released under the MIT License. See LICENSE for details.\n"
  "# Where most of our python-c++ binding happens.\n"
  "# Python objects should be added here along with their associated c++ enum.\n"
  "# pylint: disable=useless-suppression, missing-module-docstring, line-too-long\n"
  "from __future__ import annotations\n"
  "\n"
  "from baclassic._music import do_play_music\n"
  "from baclassic._input import get_input_device_mapped_value\n"
  "from baclassic._chest import (\n"
  "    CHEST_APPEARANCE_DISPLAY_INFOS,\n"
  "    CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,\n"
  ")\n"
  "from baclassic import _hooks\n"
  "\n"
  "# The C++ layer looks for this variable:\n"
  "values = [\n"
  "    do_play_music,  # kDoPlayMusicCall\n"
  "    get_input_device_mapped_value,  # kGetInputDeviceMappedValueCall\n"
  "    CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,  # kChestAppearanceDisplayInfoDefault\n"
  "    CHEST_APPEARANCE_DISPLAY_INFOS,  # kChestAppearanceDisplayInfos\n"
  "    _hooks.on_engine_will_reset,  # kOnEngineWillResetCall\n"
  "    _hooks.on_engine_did_reset,  # kOnEngineDidResetCall\n"
  "    _hooks.request_main_ui,  # kRequestMainUICall\n"
  "]\n";

// Exec the Python code in an empty context.
auto ctx = PythonRef::Stolen(PyDict_New());
bool success = PythonCommand(bindcode, "binding_classic.py").Exec(true, *ctx, *ctx);
if (!success) {
  FatalError("Error fetching required Python objects.");
}

// Grab the 'values' list that the binding code created.
auto bindvals = ctx.DictGetItem("values");
if (!bindvals.exists() || !PyList_Check(*bindvals)) {
  FatalError("Error binding required Python objects.");
}

// Pull our various obj_ values from the values list.
objs_.StoreCallable(ObjID::kDoPlayMusicCall, PyList_GET_ITEM(bindvals.get(), 0));
objs_.StoreCallable(ObjID::kGetInputDeviceMappedValueCall, PyList_GET_ITEM(bindvals.get(), 1));
objs_.Store(ObjID::kChestAppearanceDisplayInfoDefault, PyList_GET_ITEM(bindvals.get(), 2));
objs_.Store(ObjID::kChestAppearanceDisplayInfos, PyList_GET_ITEM(bindvals.get(), 3));
objs_.StoreCallable(ObjID::kOnEngineWillResetCall, PyList_GET_ITEM(bindvals.get(), 4));
objs_.StoreCallable(ObjID::kOnEngineDidResetCall, PyList_GET_ITEM(bindvals.get(), 5));
objs_.StoreCallable(ObjID::kRequestMainUICall, PyList_GET_ITEM(bindvals.get(), 6));
}
