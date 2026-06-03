{
// Python code from bascenev1meta/pyembed/binding_scene_v1.py:
const char* bindcode =
  "# Released under the MIT License. See LICENSE for details.\n"
  "# Where most of our python-c++ binding happens.\n"
  "# Python objects should be added here along with their associated c++ enum.\n"
  "# pylint: disable=useless-suppression, missing-module-docstring, line-too-long\n"
  "from __future__ import annotations\n"
  "\n"
  "from bascenev1 import _messages\n"
  "from bascenev1 import _hooks\n"
  "from bascenev1._player import Player\n"
  "from bascenev1._activity import Activity\n"
  "from bascenev1._session import Session\n"
  "from bascenev1._net import HostInfo\n"
  "import _bascenev1\n"
  "\n"
  "# The C++ layer looks for this variable:\n"
  "values = [\n"
  "    _hooks.launch_main_menu_session,  # kLaunchMainMenuSessionCall\n"
  "    _hooks.get_player_icon,  # kGetPlayerIconCall\n"
  "    _hooks.filter_chat_message,  # kFilterChatMessageCall\n"
  "    _hooks.local_chat_message,  # kHandleLocalChatMessageCall\n"
  "    _bascenev1.client_info_query_response,  # kClientInfoQueryResponseCall\n"
  "    _messages.ShouldShatterMessage,  # kShouldShatterMessageClass\n"
  "    _messages.ImpactDamageMessage,  # kImpactDamageMessageClass\n"
  "    _messages.PickedUpMessage,  # kPickedUpMessageClass\n"
  "    _messages.DroppedMessage,  # kDroppedMessageClass\n"
  "    _messages.OutOfBoundsMessage,  # kOutOfBoundsMessageClass\n"
  "    _messages.PickUpMessage,  # kPickUpMessageClass\n"
  "    _messages.DropMessage,  # kDropMessageClass\n"
  "    Player,  # kPlayerClass\n"
  "    Activity,  # kActivityClass\n"
  "    Session,  # kSceneV1SessionClass\n"
  "    HostInfo,  # kHostInfoClass\n"
  "]\n";

// Exec the Python code in an empty context.
auto ctx = PythonRef::Stolen(PyDict_New());
bool success = PythonCommand(bindcode, "binding_scene_v1.py").Exec(true, *ctx, *ctx);
if (!success) {
  FatalError("Error fetching required Python objects.");
}

// Grab the 'values' list that the binding code created.
auto bindvals = ctx.DictGetItem("values");
if (!bindvals.exists() || !PyList_Check(*bindvals)) {
  FatalError("Error binding required Python objects.");
}

// Pull our various obj_ values from the values list.
objs_.StoreCallable(ObjID::kLaunchMainMenuSessionCall, PyList_GET_ITEM(bindvals.get(), 0));
objs_.StoreCallable(ObjID::kGetPlayerIconCall, PyList_GET_ITEM(bindvals.get(), 1));
objs_.StoreCallable(ObjID::kFilterChatMessageCall, PyList_GET_ITEM(bindvals.get(), 2));
objs_.StoreCallable(ObjID::kHandleLocalChatMessageCall, PyList_GET_ITEM(bindvals.get(), 3));
objs_.StoreCallable(ObjID::kClientInfoQueryResponseCall, PyList_GET_ITEM(bindvals.get(), 4));
objs_.StoreCallable(ObjID::kShouldShatterMessageClass, PyList_GET_ITEM(bindvals.get(), 5));
objs_.StoreCallable(ObjID::kImpactDamageMessageClass, PyList_GET_ITEM(bindvals.get(), 6));
objs_.StoreCallable(ObjID::kPickedUpMessageClass, PyList_GET_ITEM(bindvals.get(), 7));
objs_.StoreCallable(ObjID::kDroppedMessageClass, PyList_GET_ITEM(bindvals.get(), 8));
objs_.StoreCallable(ObjID::kOutOfBoundsMessageClass, PyList_GET_ITEM(bindvals.get(), 9));
objs_.StoreCallable(ObjID::kPickUpMessageClass, PyList_GET_ITEM(bindvals.get(), 10));
objs_.StoreCallable(ObjID::kDropMessageClass, PyList_GET_ITEM(bindvals.get(), 11));
objs_.StoreCallable(ObjID::kPlayerClass, PyList_GET_ITEM(bindvals.get(), 12));
objs_.StoreCallable(ObjID::kActivityClass, PyList_GET_ITEM(bindvals.get(), 13));
objs_.StoreCallable(ObjID::kSceneV1SessionClass, PyList_GET_ITEM(bindvals.get(), 14));
objs_.StoreCallable(ObjID::kHostInfoClass, PyList_GET_ITEM(bindvals.get(), 15));
}
