# Released under the MIT License. See LICENSE for details.
# This code is used to grab a bunch of Python objects for use in C++.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations

import bauiv1.onscreenkeyboard
from bauiv1 import _hooks
from bauiv1._uitypes import TextWidgetStringEditAdapter

# The C++ layer looks for this variable:
values = [
    bauiv1.onscreenkeyboard.OnScreenKeyboardWindow,  # kOnScreenKeyboardClass
    _hooks.empty_call,  # kEmptyCall
    _hooks.root_ui_account_button_press,  # kRootUIAccountButtonPressCall
    _hooks.root_ui_inbox_button_press,  # kRootUIInboxButtonPressCall
    _hooks.root_ui_settings_button_press,  # kRootUISettingsButtonPressCall
    _hooks.root_ui_achievements_button_press,  # kRootUIAchievementsButtonPressCall
    _hooks.root_ui_store_button_press,  # kRootUIStoreButtonPressCall
    _hooks.root_ui_chest_slot_0_press,  # kRootUIChestSlot0PressCall
    _hooks.root_ui_chest_slot_1_press,  # kRootUIChestSlot1PressCall
    _hooks.root_ui_chest_slot_2_press,  # kRootUIChestSlot2PressCall
    _hooks.root_ui_chest_slot_3_press,  # kRootUIChestSlot3PressCall
    _hooks.root_ui_inventory_button_press,  # kRootUIInventoryButtonPressCall
    _hooks.root_ui_ticket_icon_press,  # kRootUITicketIconPressCall
    _hooks.root_ui_get_tokens_button_press,  # kRootUIGetTokensButtonPressCall
    _hooks.root_ui_tokens_meter_press,  # kRootUITokensMeterPressCall
    _hooks.root_ui_trophy_meter_press,  # kRootUITrophyMeterPressCall
    _hooks.root_ui_level_icon_press,  # kRootUILevelIconPressCall
    _hooks.root_ui_menu_button_press,  # kRootUIMenuButtonPressCall
    _hooks.root_ui_back_button_press,  # kRootUIBackButtonPressCall
    _hooks.root_ui_squad_button_press,  # kRootUISquadButtonPressCall
    _hooks.quit_window,  # kQuitWindowCall
    _hooks.show_url_window,  # kShowURLWindowCall
    _hooks.double_transition_out_warning,  # kDoubleTransitionOutWarningCall
    TextWidgetStringEditAdapter,  # kTextWidgetStringEditAdapterClass
]
