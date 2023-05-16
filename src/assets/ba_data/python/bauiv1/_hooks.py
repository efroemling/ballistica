# Released under the MIT License. See LICENSE for details.
#
"""Snippets of code for use by the c++ layer."""
# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring
from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import _bauiv1

if TYPE_CHECKING:
    from typing import Sequence


def ticket_icon_press() -> None:
    # FIXME: move this into our package.
    from bastd.ui.resourcetypeinfo import ResourceTypeInfoWindow

    ResourceTypeInfoWindow(
        origin_widget=_bauiv1.get_special_widget('tickets_info_button')
    )


def trophy_icon_press() -> None:
    print('TROPHY ICON PRESSED')


def level_icon_press() -> None:
    print('LEVEL ICON PRESSED')


def coin_icon_press() -> None:
    print('COIN ICON PRESSED')


def empty_call() -> None:
    pass


def back_button_press() -> None:
    _bauiv1.back_press()


def friends_button_press() -> None:
    print('FRIEND BUTTON PRESSED!')


def party_icon_activate(origin: Sequence[float]) -> None:
    from bastd.ui.party import PartyWindow
    from babase import app

    assert not app.headless_mode

    assert app.classic is not None
    ui = app.classic.ui

    _bauiv1.getsound('swish').play()

    # If it exists, dismiss it; otherwise make a new one.
    if ui.party_window is not None and ui.party_window() is not None:
        ui.party_window().close()
    else:
        ui.party_window = weakref.ref(PartyWindow(origin=origin))


def quit_window() -> None:
    from bastd.ui.confirm import QuitWindow

    QuitWindow()


def device_menu_press(device_id: int | None) -> None:
    from bastd.ui.mainmenu import MainMenuWindow
    from babase import app
    from bauiv1 import set_ui_input_device

    assert app.classic is not None
    in_main_menu = app.classic.ui.has_main_menu_window()
    if not in_main_menu:
        set_ui_input_device(device_id)

        if not app.headless_mode:
            _bauiv1.getsound('swish').play()

        app.classic.ui.set_main_menu_window(MainMenuWindow().get_root_widget())


def show_url_window(address: str) -> None:
    from bastd.ui.url import ShowURLWindow

    ShowURLWindow(address)
