# Released under the MIT License. See LICENSE for details.
#
"""Snippets of code for use by the c++ layer."""
# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring
from __future__ import annotations

import logging
import inspect
from typing import TYPE_CHECKING

import _bauiv1

if TYPE_CHECKING:
    from typing import Sequence

    import babase
    import bauiv1


def empty_call() -> None:
    pass


def _root_ui_button_press(
    rootuitype: bauiv1.UIV1AppSubsystem.RootUIElement,
) -> None:
    import babase

    ui = babase.app.ui_v1
    call = ui.root_ui_calls.get(rootuitype)
    if call is not None:
        call()


def root_ui_account_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.ACCOUNT_BUTTON)


def root_ui_inbox_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.INBOX_BUTTON)


def root_ui_settings_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.SETTINGS_BUTTON)


def root_ui_achievements_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.ACHIEVEMENTS_BUTTON)


def root_ui_store_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.STORE_BUTTON)


def root_ui_chest_slot_0_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.CHEST_SLOT_0)


def root_ui_chest_slot_1_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.CHEST_SLOT_1)


def root_ui_chest_slot_2_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.CHEST_SLOT_2)


def root_ui_chest_slot_3_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.CHEST_SLOT_3)


def root_ui_inventory_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.INVENTORY_BUTTON)


def root_ui_ticket_icon_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.TICKETS_METER)


def root_ui_get_tokens_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.GET_TOKENS_BUTTON)


def root_ui_tokens_meter_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.TOKENS_METER)


def root_ui_trophy_meter_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.TROPHY_METER)


def root_ui_level_icon_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.LEVEL_METER)


def root_ui_menu_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.MENU_BUTTON)


def root_ui_back_button_press() -> None:
    # Native layer handles this directly. (technically we could wire
    # this up to not even come through Python).
    _bauiv1.root_ui_back_press()


def root_ui_squad_button_press() -> None:
    from bauiv1._appsubsystem import UIV1AppSubsystem

    _root_ui_button_press(UIV1AppSubsystem.RootUIElement.SQUAD_BUTTON)


def quit_window(quit_type: babase.QuitType) -> None:
    from babase import app

    if app.classic is None:
        logging.exception('Classic not present.')
        return

    app.classic.quit_window(quit_type)


def show_url_window(address: str) -> None:
    from babase import app

    if app.classic is None:
        logging.exception('Classic not present.')
        return

    app.classic.show_url_window(address)


def double_transition_out_warning() -> None:
    """Called if a widget is set to transition out twice."""
    caller_frame = inspect.stack()[1]
    caller_filename = caller_frame.filename
    caller_line_number = caller_frame.lineno
    logging.warning(
        'ContainerWidget was set to transition out twice;'
        ' this often implies buggy code (%s line %s).\n'
        ' Generally you should check the value of'
        ' _root_widget.transitioning_out and perform no actions if that'
        ' is True.',
        caller_filename,
        caller_line_number,
    )
