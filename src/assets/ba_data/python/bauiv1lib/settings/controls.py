# Released under the MIT License. See LICENSE for details.
#
"""Provides a top level control settings window."""

from __future__ import annotations

from typing import override

import bascenev1 as bs
import bauiv1 as bui


class ControlsSettingsWindow(bui.MainWindow):
    """Top level control settings window."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # FIXME: should tidy up here.
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import

        self._have_selected_child = False

        self._r = 'configControllersWindow'
        uiscale = bui.app.ui_v1.uiscale
        app = bui.app
        assert app.classic is not None

        spacing = 50.0
        button_width = 350.0
        width = 1200.0 if uiscale is bui.UIScale.SMALL else 560.0
        height = 800 if uiscale is bui.UIScale.SMALL else 400.0

        # yoffs = -60 if uiscale is bui.UIScale.SMALL else 0
        space_height = spacing * 0.3

        buttons_height = 0.0

        # FIXME: should create vis settings under platform or
        # app-adapter to determine whether to show this stuff; not
        # hard-code it.

        show_gamepads = False
        platform = app.classic.platform
        subplatform = app.classic.subplatform
        non_vr_windows = platform == 'windows' and (
            subplatform != 'oculus' or not app.env.vr
        )
        if platform in ('linux', 'android', 'mac') or non_vr_windows:
            show_gamepads = True
            buttons_height += spacing

        show_touch = False
        if bs.have_touchscreen_input():
            show_touch = True
            buttons_height += spacing

        show_space_1 = False
        if show_gamepads or show_touch:
            show_space_1 = True
            buttons_height += space_height

        show_keyboard = False
        if bs.getinputdevice('Keyboard', '#1', doraise=False) is not None:
            show_keyboard = True
            buttons_height += spacing
        show_keyboard_p2 = False if app.env.vr else show_keyboard
        if show_keyboard_p2:
            buttons_height += spacing

        show_space_2 = False
        if show_keyboard:
            show_space_2 = True
            buttons_height += space_height

        if bool(True):
            show_remote = True
            buttons_height += spacing
        else:
            show_remote = False

        # On windows (outside of oculus/vr), show an option to disable
        # xinput.
        show_xinput_toggle = False
        if platform == 'windows' and not app.env.vr:
            show_xinput_toggle = True

        if show_xinput_toggle:
            buttons_height += spacing

        assert bui.app.classic is not None

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(width - 60, screensize[0] / scale)
        target_height = min(height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                scale=scale,
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        self._back_button: bui.Widget | None
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(35, height - 60),
                size=(60, 60),
                scale=0.8,
                text_scale=1.2,
                autoselect=True,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        # We need these vars to exist even if the buttons don't.
        self._gamepads_button: bui.Widget | None = None
        self._touch_button: bui.Widget | None = None
        self._keyboard_button: bui.Widget | None = None
        self._keyboard_2_button: bui.Widget | None = None
        self._idevices_button: bui.Widget | None = None

        bui.textwidget(
            parent=self._root_widget,
            position=(
                width * 0.5,
                yoffs - (52 if uiscale is bui.UIScale.SMALL else 32),
            ),
            maxwidth=260,
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        # Roughly center the rest of our stuff.
        v = height * 0.5 + buttons_height * 0.5 - 10
        v -= spacing

        if show_touch:
            self._touch_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2, v),
                size=(button_width, 43),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.configureTouchText'),
                on_activate_call=self._do_touchscreen,
            )
            bui.widget(
                edit=btn,
                right_widget=bui.get_special_widget('squad_button'),
            )
            if not self._have_selected_child:
                bui.containerwidget(
                    edit=self._root_widget, selected_child=self._touch_button
                )
                if self._back_button is not None:
                    bui.widget(
                        edit=self._back_button, down_widget=self._touch_button
                    )
                self._have_selected_child = True
            v -= spacing

        if show_gamepads:
            self._gamepads_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 - 7, v),
                size=(button_width, 43),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.configureControllersText'),
                on_activate_call=self._do_gamepads,
            )
            bui.widget(
                edit=btn,
                right_widget=bui.get_special_widget('squad_button'),
            )
            if not self._have_selected_child:
                bui.containerwidget(
                    edit=self._root_widget, selected_child=self._gamepads_button
                )
                if self._back_button is not None:
                    bui.widget(
                        edit=self._back_button,
                        down_widget=self._gamepads_button,
                    )
                self._have_selected_child = True
            v -= spacing
        else:
            self._gamepads_button = None

        if show_space_1:
            v -= space_height

        if show_keyboard:
            self._keyboard_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 - 5, v),
                size=(button_width, 43),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.configureKeyboardText'),
                on_activate_call=self._config_keyboard,
            )
            bui.widget(
                edit=self._keyboard_button, left_widget=self._keyboard_button
            )
            bui.widget(
                edit=btn,
                right_widget=bui.get_special_widget('squad_button'),
            )
            if not self._have_selected_child:
                bui.containerwidget(
                    edit=self._root_widget, selected_child=self._keyboard_button
                )
                if self._back_button is not None:
                    bui.widget(
                        edit=self._back_button,
                        down_widget=self._keyboard_button,
                    )
                self._have_selected_child = True
            v -= spacing
        if show_keyboard_p2:
            self._keyboard_2_button = bui.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 - 3, v),
                size=(button_width, 43),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.configureKeyboard2Text'),
                on_activate_call=self._config_keyboard2,
            )
            v -= spacing
            bui.widget(
                edit=self._keyboard_2_button,
                left_widget=self._keyboard_2_button,
            )
        if show_space_2:
            v -= space_height
        if show_remote:
            self._idevices_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=((width - button_width) / 2 - 5, v),
                size=(button_width, 43),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.configureMobileText'),
                on_activate_call=self._do_mobile_devices,
            )
            bui.widget(
                edit=self._idevices_button, left_widget=self._idevices_button
            )
            bui.widget(
                edit=btn,
                right_widget=bui.get_special_widget('squad_button'),
            )
            if not self._have_selected_child:
                bui.containerwidget(
                    edit=self._root_widget, selected_child=self._idevices_button
                )
                if self._back_button is not None:
                    bui.widget(
                        edit=self._back_button,
                        down_widget=self._idevices_button,
                    )
                self._have_selected_child = True
            v -= spacing

        if show_xinput_toggle:

            def do_toggle(value: bool) -> None:
                bui.screenmessage(
                    bui.Lstr(resource='settingsWindowAdvanced.mustRestartText'),
                    color=(1, 1, 0),
                )
                bui.getsound('gunCocking').play()
                bui.set_low_level_config_value('enablexinput', not value)

            xinput_checkbox = bui.checkboxwidget(
                parent=self._root_widget,
                position=(
                    width * (0.35 if uiscale is bui.UIScale.SMALL else 0.25),
                    v + 3,
                ),
                size=(120, 30),
                value=(not bui.get_low_level_config_value('enablexinput', 1)),
                maxwidth=200,
                on_value_change_call=do_toggle,
                text=bui.Lstr(resource='disableXInputText'),
                autoselect=True,
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(width * 0.5, v - 5),
                size=(0, 0),
                text=bui.Lstr(resource='disableXInputDescriptionText'),
                scale=0.5,
                h_align='center',
                v_align='center',
                color=bui.app.ui_v1.infotextcolor,
                maxwidth=width * 0.8,
            )
            bui.widget(
                edit=xinput_checkbox,
                left_widget=xinput_checkbox,
                right_widget=xinput_checkbox,
            )
            v -= spacing

        self._restore_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _set_mac_controller_subsystem(self, val: str) -> None:
        cfg = bui.app.config
        cfg['Mac Controller Subsystem'] = val
        cfg.apply_and_commit()

    def _config_keyboard(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.keyboard import ConfigKeyboardWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            ConfigKeyboardWindow(bs.getinputdevice('Keyboard', '#1'))
        )

    def _config_keyboard2(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.keyboard import ConfigKeyboardWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            ConfigKeyboardWindow(bs.getinputdevice('Keyboard', '#2'))
        )

    def _do_mobile_devices(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.remoteapp import RemoteAppSettingsWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(RemoteAppSettingsWindow())

    def _do_gamepads(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.gamepadselect import GamepadSelectWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(GamepadSelectWindow())

    def _do_touchscreen(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.touchscreen import TouchscreenSettingsWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(TouchscreenSettingsWindow())

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
        else:
            sel_name = 'Back'
        assert bui.app.classic is not None
        bui.app.ui_v1.window_states[type(self)] = sel_name

    def _restore_state(self) -> None:
        assert bui.app.classic is not None
        sel_name = bui.app.ui_v1.window_states.get(type(self))
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
        elif sel_name == 'Back':
            sel = self._back_button
        else:
            sel = (
                self._gamepads_button
                if self._gamepads_button is not None
                else self._back_button
            )
        bui.containerwidget(edit=self._root_widget, selected_child=sel)
