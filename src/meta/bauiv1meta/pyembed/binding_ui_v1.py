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
    _hooks.ticket_icon_press,  # kTicketIconPressCall
    _hooks.trophy_icon_press,  # kTrophyIconPressCall
    _hooks.level_icon_press,  # kLevelIconPressCall
    _hooks.coin_icon_press,  # kCoinIconPressCall
    _hooks.empty_call,  # kEmptyCall
    _hooks.back_button_press,  # kBackButtonPressCall
    _hooks.friends_button_press,  # kFriendsButtonPressCall
    _hooks.party_icon_activate,  # kPartyIconActivateCall
    _hooks.quit_window,  # kQuitWindowCall
    _hooks.device_menu_press,  # kDeviceMenuPressCall
    _hooks.show_url_window,  # kShowURLWindowCall
    _hooks.double_transition_out_warning,  # kDoubleTransitionOutWarningCall
    TextWidgetStringEditAdapter,  # kTextWidgetStringEditAdapterClass
]
