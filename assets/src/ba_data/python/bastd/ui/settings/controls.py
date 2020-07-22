# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Provides a top level control settings window."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Tuple, Optional


class ControlsSettingsWindow(ba.Window):
    """Top level control settings window."""

    def __init__(self,
                 transition: str = 'in_right',
                 origin_widget: ba.Widget = None):
        # FIXME: should tidy up here.
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bastd.ui import popup as popup_ui
        self._have_selected_child = False

        scale_origin: Optional[Tuple[float, float]]

        # If they provided an origin-widget, scale up from that.
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._r = 'configControllersWindow'
        app = ba.app

        # is_fire_tv = _ba.is_running_on_fire_tv()

        spacing = 50.0
        button_width = 350.0
        width = 460.0
        height = 130.0

        space_height = spacing * 0.3

        # FIXME: should create vis settings in platform for these,
        #  not hard code them here.

        show_gamepads = False
        platform = app.platform
        subplatform = app.subplatform
        non_vr_windows = (platform == 'windows'
                          and (subplatform != 'oculus' or not app.vr_mode))
        if platform in ('linux', 'android', 'mac') or non_vr_windows:
            show_gamepads = True
            height += spacing

        show_touch = False
        if _ba.have_touchscreen_input():
            show_touch = True
            height += spacing

        show_space_1 = False
        if show_gamepads or show_touch:
            show_space_1 = True
            height += space_height

        show_keyboard = False
        if _ba.getinputdevice('Keyboard', '#1', doraise=False) is not None:
            show_keyboard = True
            height += spacing
        show_keyboard_p2 = False if app.vr_mode else show_keyboard
        if show_keyboard_p2:
            height += spacing

        show_space_2 = False
        if show_keyboard:
            show_space_2 = True
            height += space_height

        if bool(True):
            show_remote = True
            height += spacing
        else:
            show_remote = False

        show_ps3 = False
        # if platform == 'mac':
        #     show_ps3 = True
        #     height += spacing

        show360 = False
        # if platform == 'mac' or is_fire_tv:
        #     show360 = True
        #     height += spacing

        show_mac_wiimote = False
        # if platform == 'mac' and _ba.is_xcode_build():
        #     show_mac_wiimote = True
        #     height += spacing

        # On windows (outside of oculus/vr), show an option to disable xinput.
        show_xinput_toggle = False
        if platform == 'windows' and not app.vr_mode:
            show_xinput_toggle = True

        # On mac builds, show an option to switch between generic and
        # made-for-iOS/Mac systems
        # (we can run into problems where devices register as one of each
        # type otherwise)..
        show_mac_controller_subsystem = False
        if platform == 'mac' and _ba.is_xcode_build():
            show_mac_controller_subsystem = True

        if show_mac_controller_subsystem:
            height += spacing * 1.5

        if show_xinput_toggle:
            height += spacing

        uiscale = ba.app.ui.uiscale
        smallscale = (1.7 if show_keyboard else 2.2)
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition=transition,
            scale_origin_stack_offset=scale_origin,
            stack_offset=((0, -10) if uiscale is ba.UIScale.SMALL else (0, 0)),
            scale=(smallscale if uiscale is ba.UIScale.SMALL else
                   1.5 if uiscale is ba.UIScale.MEDIUM else 1.0)))
        self._back_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(35, height - 60),
            size=(140, 65),
            scale=0.8,
            text_scale=1.2,
            autoselect=True,
            label=ba.Lstr(resource='backText'),
            button_type='back',
            on_activate_call=self._back)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        # We need these vars to exist even if the buttons don't.
        self._gamepads_button: Optional[ba.Widget] = None
        self._touch_button: Optional[ba.Widget] = None
        self._keyboard_button: Optional[ba.Widget] = None
        self._keyboard_2_button: Optional[ba.Widget] = None
        self._idevices_button: Optional[ba.Widget] = None
        self._ps3_button: Optional[ba.Widget] = None
        self._xbox_360_button: Optional[ba.Widget] = None
        self._wiimotes_button: Optional[ba.Widget] = None

        ba.textwidget(parent=self._root_widget,
                      position=(0, height - 49),
                      size=(width, 25),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='top')
        ba.buttonwidget(edit=btn,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        v = height - 75
        v -= spacing

        if show_touch:
            self._touch_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2, v),
                size=(button_width, 43),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.configureTouchText'),
                on_activate_call=self._do_touchscreen)
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            if not self._have_selected_child:
                ba.containerwidget(edit=self._root_widget,
                                   selected_child=self._touch_button)
                ba.widget(edit=self._back_button,
                          down_widget=self._touch_button)
                self._have_selected_child = True
            v -= spacing

        if show_gamepads:
            self._gamepads_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 - 7, v),
                size=(button_width, 43),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.configureControllersText'),
                on_activate_call=self._do_gamepads)
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            if not self._have_selected_child:
                ba.containerwidget(edit=self._root_widget,
                                   selected_child=self._gamepads_button)
                ba.widget(edit=self._back_button,
                          down_widget=self._gamepads_button)
                self._have_selected_child = True
            v -= spacing
        else:
            self._gamepads_button = None

        if show_space_1:
            v -= space_height

        if show_keyboard:
            self._keyboard_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 + 5, v),
                size=(button_width, 43),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.configureKeyboardText'),
                on_activate_call=self._config_keyboard)
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            if not self._have_selected_child:
                ba.containerwidget(edit=self._root_widget,
                                   selected_child=self._keyboard_button)
                ba.widget(edit=self._back_button,
                          down_widget=self._keyboard_button)
                self._have_selected_child = True
            v -= spacing
        if show_keyboard_p2:
            self._keyboard_2_button = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 - 3, v),
                size=(button_width, 43),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.configureKeyboard2Text'),
                on_activate_call=self._config_keyboard2)
            v -= spacing
        if show_space_2:
            v -= space_height
        if show_remote:
            self._idevices_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 - 5, v),
                size=(button_width, 43),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.configureMobileText'),
                on_activate_call=self._do_mobile_devices)
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            if not self._have_selected_child:
                ba.containerwidget(edit=self._root_widget,
                                   selected_child=self._idevices_button)
                ba.widget(edit=self._back_button,
                          down_widget=self._idevices_button)
                self._have_selected_child = True
            v -= spacing
        if show_ps3:
            self._ps3_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 + 5, v),
                size=(button_width, 43),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.ps3Text'),
                on_activate_call=self._do_ps3_controllers)
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            v -= spacing
        if show360:
            self._xbox_360_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 - 1, v),
                size=(button_width, 43),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.xbox360Text'),
                on_activate_call=self._do_360_controllers)
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            v -= spacing
        if show_mac_wiimote:
            self._wiimotes_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 + 5, v),
                size=(button_width, 43),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.wiimotesText'),
                on_activate_call=self._do_wiimotes)
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            v -= spacing

        if show_xinput_toggle:

            def do_toggle(value: bool) -> None:
                ba.screenmessage(
                    ba.Lstr(resource='settingsWindowAdvanced.mustRestartText'),
                    color=(1, 1, 0))
                ba.playsound(ba.getsound('gunCocking'))
                _ba.set_low_level_config_value('enablexinput', not value)

            ba.checkboxwidget(
                parent=self._root_widget,
                position=(100, v + 3),
                size=(120, 30),
                value=(not _ba.get_low_level_config_value('enablexinput', 1)),
                maxwidth=200,
                on_value_change_call=do_toggle,
                text=ba.Lstr(resource='disableXInputText'),
                autoselect=True)
            ba.textwidget(
                parent=self._root_widget,
                position=(width * 0.5, v - 5),
                size=(0, 0),
                text=ba.Lstr(resource='disableXInputDescriptionText'),
                scale=0.5,
                h_align='center',
                v_align='center',
                color=ba.app.ui.infotextcolor,
                maxwidth=width * 0.8)
            v -= spacing
        if show_mac_controller_subsystem:
            popup_ui.PopupMenu(
                parent=self._root_widget,
                position=(260, v - 10),
                width=160,
                button_size=(150, 50),
                scale=1.5,
                choices=['Classic', 'MFi', 'Both'],
                choices_display=[
                    ba.Lstr(resource='macControllerSubsystemClassicText'),
                    ba.Lstr(resource='macControllerSubsystemMFiText'),
                    ba.Lstr(resource='macControllerSubsystemBothText')
                ],
                current_choice=ba.app.config.resolve(
                    'Mac Controller Subsystem'),
                on_value_change_call=self._set_mac_controller_subsystem)
            ba.textwidget(
                parent=self._root_widget,
                position=(245, v + 13),
                size=(0, 0),
                text=ba.Lstr(resource='macControllerSubsystemTitleText'),
                scale=1.0,
                h_align='right',
                v_align='center',
                color=ba.app.ui.infotextcolor,
                maxwidth=180)
            ba.textwidget(
                parent=self._root_widget,
                position=(width * 0.5, v - 20),
                size=(0, 0),
                text=ba.Lstr(resource='macControllerSubsystemDescriptionText'),
                scale=0.5,
                h_align='center',
                v_align='center',
                color=ba.app.ui.infotextcolor,
                maxwidth=width * 0.8)
            v -= spacing * 1.5
        self._restore_state()

    def _set_mac_controller_subsystem(self, val: str) -> None:
        cfg = ba.app.config
        cfg['Mac Controller Subsystem'] = val
        cfg.apply_and_commit()

    def _config_keyboard(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.keyboard import ConfigKeyboardWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            ConfigKeyboardWindow(_ba.getinputdevice('Keyboard',
                                                    '#1')).get_root_widget())

    def _config_keyboard2(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.keyboard import ConfigKeyboardWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            ConfigKeyboardWindow(_ba.getinputdevice('Keyboard',
                                                    '#2')).get_root_widget())

    def _do_mobile_devices(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.remoteapp import RemoteAppSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            RemoteAppSettingsWindow().get_root_widget())

    def _do_ps3_controllers(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.ps3controller import PS3ControllerSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            PS3ControllerSettingsWindow().get_root_widget())

    def _do_360_controllers(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.xbox360controller import (
            XBox360ControllerSettingsWindow)
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            XBox360ControllerSettingsWindow().get_root_widget())

    def _do_wiimotes(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.wiimote import WiimoteSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            WiimoteSettingsWindow().get_root_widget())

    def _do_gamepads(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.gamepadselect import GamepadSelectWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(GamepadSelectWindow().get_root_widget())

    def _do_touchscreen(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.touchscreen import TouchscreenSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            TouchscreenSettingsWindow().get_root_widget())

    def _save_state(self) -> None:
        sel = self._root_widget.get_selected_child()
        if sel == self._gamepads_button:
            sel_name = 'GamePads'
        elif sel == self._touch_button:
            sel_name = 'Touch'
        elif sel == self._keyboard_button:
            sel_name = 'Keyboard'
        elif sel == self._keyboard_2_button:
            sel_name = 'Keyboard2'
        elif sel == self._idevices_button:
            sel_name = 'iDevices'
        elif sel == self._ps3_button:
            sel_name = 'PS3'
        elif sel == self._xbox_360_button:
            sel_name = 'xbox360'
        elif sel == self._wiimotes_button:
            sel_name = 'Wiimotes'
        else:
            sel_name = 'Back'
        ba.app.ui.window_states[self.__class__.__name__] = sel_name

    def _restore_state(self) -> None:
        sel_name = ba.app.ui.window_states.get(self.__class__.__name__)
        if sel_name == 'GamePads':
            sel = self._gamepads_button
        elif sel_name == 'Touch':
            sel = self._touch_button
        elif sel_name == 'Keyboard':
            sel = self._keyboard_button
        elif sel_name == 'Keyboard2':
            sel = self._keyboard_2_button
        elif sel_name == 'iDevices':
            sel = self._idevices_button
        elif sel_name == 'PS3':
            sel = self._ps3_button
        elif sel_name == 'xbox360':
            sel = self._xbox_360_button
        elif sel_name == 'Wiimotes':
            sel = self._wiimotes_button
        elif sel_name == 'Back':
            sel = self._back_button
        else:
            sel = (self._gamepads_button
                   if self._gamepads_button is not None else self._back_button)
        ba.containerwidget(edit=self._root_widget, selected_child=sel)

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.allsettings import AllSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            AllSettingsWindow(transition='in_left').get_root_widget())
