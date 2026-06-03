{
// Python code from bauiv1meta/pyembed/binding_ui_v1.py:
const char* bindcode =
  "# Released under the MIT License. See LICENSE for details.\n"
  "# This code is used to grab a bunch of Python objects for use in C++.\n"
  "# Python objects should be added here along with their associated c++ enum.\n"
  "# pylint: disable=useless-suppression, missing-module-docstring, line-too-long\n"
  "from __future__ import annotations\n"
  "\n"
  "import bauiv1.onscreenkeyboard\n"
  "from bauiv1 import _hooks\n"
  "from bauiv1._uitypes import TextWidgetStringEditAdapter\n"
  "\n"
  "# The C++ layer looks for this variable:\n"
  "values = [\n"
  "    bauiv1.onscreenkeyboard.OnScreenKeyboardWindow,  # kOnScreenKeyboardClass\n"
  "    _hooks.empty_call,  # kEmptyCall\n"
  "    _hooks.root_ui_account_button_press,  # kRootUIAccountButtonPressCall\n"
  "    _hooks.root_ui_inbox_button_press,  # kRootUIInboxButtonPressCall\n"
  "    _hooks.root_ui_settings_button_press,  # kRootUISettingsButtonPressCall\n"
  "    _hooks.root_ui_achievements_button_press,  # kRootUIAchievementsButtonPressCall\n"
  "    _hooks.root_ui_store_button_press,  # kRootUIStoreButtonPressCall\n"
  "    _hooks.root_ui_chest_slot_0_press,  # kRootUIChestSlot0PressCall\n"
  "    _hooks.root_ui_chest_slot_1_press,  # kRootUIChestSlot1PressCall\n"
  "    _hooks.root_ui_chest_slot_2_press,  # kRootUIChestSlot2PressCall\n"
  "    _hooks.root_ui_chest_slot_3_press,  # kRootUIChestSlot3PressCall\n"
  "    _hooks.root_ui_inventory_button_press,  # kRootUIInventoryButtonPressCall\n"
  "    _hooks.root_ui_ticket_icon_press,  # kRootUITicketIconPressCall\n"
  "    _hooks.root_ui_get_tokens_button_press,  # kRootUIGetTokensButtonPressCall\n"
  "    _hooks.root_ui_tokens_meter_press,  # kRootUITokensMeterPressCall\n"
  "    _hooks.root_ui_trophy_meter_press,  # kRootUITrophyMeterPressCall\n"
  "    _hooks.root_ui_level_icon_press,  # kRootUILevelIconPressCall\n"
  "    _hooks.root_ui_menu_button_press,  # kRootUIMenuButtonPressCall\n"
  "    _hooks.root_ui_back_button_press,  # kRootUIBackButtonPressCall\n"
  "    _hooks.root_ui_squad_button_press,  # kRootUISquadButtonPressCall\n"
  "    _hooks.quit_window,  # kQuitWindowCall\n"
  "    _hooks.show_url_window,  # kShowURLWindowCall\n"
  "    _hooks.double_transition_out_warning,  # kDoubleTransitionOutWarningCall\n"
  "    TextWidgetStringEditAdapter,  # kTextWidgetStringEditAdapterClass\n"
  "]\n";

// Exec the Python code in an empty context.
auto ctx = PythonRef::Stolen(PyDict_New());
bool success = PythonCommand(bindcode, "binding_ui_v1.py").Exec(true, *ctx, *ctx);
if (!success) {
  FatalError("Error fetching required Python objects.");
}

// Grab the 'values' list that the binding code created.
auto bindvals = ctx.DictGetItem("values");
if (!bindvals.exists() || !PyList_Check(*bindvals)) {
  FatalError("Error binding required Python objects.");
}

// Pull our various obj_ values from the values list.
objs_.StoreCallable(ObjID::kOnScreenKeyboardClass, PyList_GET_ITEM(bindvals.get(), 0));
objs_.StoreCallable(ObjID::kEmptyCall, PyList_GET_ITEM(bindvals.get(), 1));
objs_.StoreCallable(ObjID::kRootUIAccountButtonPressCall, PyList_GET_ITEM(bindvals.get(), 2));
objs_.StoreCallable(ObjID::kRootUIInboxButtonPressCall, PyList_GET_ITEM(bindvals.get(), 3));
objs_.StoreCallable(ObjID::kRootUISettingsButtonPressCall, PyList_GET_ITEM(bindvals.get(), 4));
objs_.StoreCallable(ObjID::kRootUIAchievementsButtonPressCall, PyList_GET_ITEM(bindvals.get(), 5));
objs_.StoreCallable(ObjID::kRootUIStoreButtonPressCall, PyList_GET_ITEM(bindvals.get(), 6));
objs_.StoreCallable(ObjID::kRootUIChestSlot0PressCall, PyList_GET_ITEM(bindvals.get(), 7));
objs_.StoreCallable(ObjID::kRootUIChestSlot1PressCall, PyList_GET_ITEM(bindvals.get(), 8));
objs_.StoreCallable(ObjID::kRootUIChestSlot2PressCall, PyList_GET_ITEM(bindvals.get(), 9));
objs_.StoreCallable(ObjID::kRootUIChestSlot3PressCall, PyList_GET_ITEM(bindvals.get(), 10));
objs_.StoreCallable(ObjID::kRootUIInventoryButtonPressCall, PyList_GET_ITEM(bindvals.get(), 11));
objs_.StoreCallable(ObjID::kRootUITicketIconPressCall, PyList_GET_ITEM(bindvals.get(), 12));
objs_.StoreCallable(ObjID::kRootUIGetTokensButtonPressCall, PyList_GET_ITEM(bindvals.get(), 13));
objs_.StoreCallable(ObjID::kRootUITokensMeterPressCall, PyList_GET_ITEM(bindvals.get(), 14));
objs_.StoreCallable(ObjID::kRootUITrophyMeterPressCall, PyList_GET_ITEM(bindvals.get(), 15));
objs_.StoreCallable(ObjID::kRootUILevelIconPressCall, PyList_GET_ITEM(bindvals.get(), 16));
objs_.StoreCallable(ObjID::kRootUIMenuButtonPressCall, PyList_GET_ITEM(bindvals.get(), 17));
objs_.StoreCallable(ObjID::kRootUIBackButtonPressCall, PyList_GET_ITEM(bindvals.get(), 18));
objs_.StoreCallable(ObjID::kRootUISquadButtonPressCall, PyList_GET_ITEM(bindvals.get(), 19));
objs_.StoreCallable(ObjID::kQuitWindowCall, PyList_GET_ITEM(bindvals.get(), 20));
objs_.StoreCallable(ObjID::kShowURLWindowCall, PyList_GET_ITEM(bindvals.get(), 21));
objs_.StoreCallable(ObjID::kDoubleTransitionOutWarningCall, PyList_GET_ITEM(bindvals.get(), 22));
objs_.StoreCallable(ObjID::kTextWidgetStringEditAdapterClass, PyList_GET_ITEM(bindvals.get(), 23));
}
