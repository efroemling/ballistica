# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to advanced gamepad configuring."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any
    from bauiv1lib.settings.gamepad import (
        GamepadSettingsWindow,
        AwaitGamepadInputWindow,
    )


class GamepadAdvancedSettingsWindow(bui.Window):
    """Window for advanced gamepad configuration."""

    def __init__(self, parent_window: GamepadSettingsWindow):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        self._parent_window = parent_window

        app = bui.app

        self._r = parent_window.get_r()
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 900 if uiscale is bui.UIScale.SMALL else 700
        self._x_inset = x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        self._height = 402 if uiscale is bui.UIScale.SMALL else 512
        self._textwidgets: dict[str, bui.Widget] = {}
        advb = parent_window.get_advanced_button()
        super().__init__(
            root_widget=bui.containerwidget(
                transition='in_scale',
                size=(self._width, self._height),
                scale=1.06
                * (
                    1.6
                    if uiscale is bui.UIScale.SMALL
                    else 1.35 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, -25) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
                scale_origin_stack_offset=(advb.get_screen_space_center()),
            )
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                self._height - (40 if uiscale is bui.UIScale.SMALL else 34),
            ),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.advancedTitleText'),
            maxwidth=320,
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(
                self._width - (176 + x_inset),
                self._height - (60 if uiscale is bui.UIScale.SMALL else 55),
            ),
            size=(120, 48),
            text_scale=0.8,
            label=bui.Lstr(resource='doneText'),
            on_activate_call=self._done,
        )
        bui.containerwidget(
            edit=self._root_widget,
            start_button=btn,
            on_cancel_call=btn.activate,
        )

        self._scroll_width = self._width - (100 + 2 * x_inset)
        self._scroll_height = self._height - 110
        self._sub_width = self._scroll_width - 20
        self._sub_height = (
            940 if self._parent_window.get_is_secondary() else 1040
        )
        if app.env.vr:
            self._sub_height += 50
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(
                (self._width - self._scroll_width) * 0.5,
                self._height - 65 - self._scroll_height,
            ),
            size=(self._scroll_width, self._scroll_height),
            claims_left_right=True,
            selection_loops_to_parent=True,
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )

        h = 30
        v = self._sub_height - 10

        h2 = h + 12

        # don't allow secondary joysticks to handle unassigned buttons
        if not self._parent_window.get_is_secondary():
            v -= 40
            cb1 = bui.checkboxwidget(
                parent=self._subcontainer,
                position=(h + 70, v),
                size=(500, 30),
                text=bui.Lstr(resource=f'{self._r}.unassignedButtonsRunText'),
                textcolor=(0.8, 0.8, 0.8),
                maxwidth=330,
                scale=1.0,
                on_value_change_call=(
                    self._parent_window.set_unassigned_buttons_run_value
                ),
                autoselect=True,
                value=self._parent_window.get_unassigned_buttons_run_value(),
            )
            bui.widget(edit=cb1, up_widget=back_button)
        v -= 60
        capb = self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.runButton1Text'),
            control='buttonRun1' + self._parent_window.get_ext(),
        )
        if self._parent_window.get_is_secondary():
            for widget in capb:
                bui.widget(edit=widget, up_widget=back_button)
        v -= 42
        self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.runButton2Text'),
            control='buttonRun2' + self._parent_window.get_ext(),
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v - 24),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.runTriggerDescriptionText'),
            color=(0.7, 1, 0.7, 0.6),
            maxwidth=self._sub_width * 0.8,
            scale=0.7,
            h_align='center',
            v_align='center',
        )

        v -= 85

        self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.runTrigger1Text'),
            control='triggerRun1' + self._parent_window.get_ext(),
            message=bui.Lstr(resource=f'{self._r}.pressAnyAnalogTriggerText'),
        )
        v -= 42
        self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.runTrigger2Text'),
            control='triggerRun2' + self._parent_window.get_ext(),
            message=bui.Lstr(resource=f'{self._r}.pressAnyAnalogTriggerText'),
        )

        # in vr mode, allow assigning a reset-view button
        if app.env.vr:
            v -= 50
            self._capture_button(
                pos=(h2, v),
                name=bui.Lstr(resource=f'{self._r}.vrReorientButtonText'),
                control='buttonVRReorient' + self._parent_window.get_ext(),
            )

        v -= 60
        self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.extraStartButtonText'),
            control='buttonStart2' + self._parent_window.get_ext(),
        )
        v -= 60
        self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.ignoredButton1Text'),
            control='buttonIgnored' + self._parent_window.get_ext(),
        )
        v -= 42
        self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.ignoredButton2Text'),
            control='buttonIgnored2' + self._parent_window.get_ext(),
        )
        v -= 42
        self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.ignoredButton3Text'),
            control='buttonIgnored3' + self._parent_window.get_ext(),
        )
        v -= 42
        self._capture_button(
            pos=(h2, v),
            name=bui.Lstr(resource=f'{self._r}.ignoredButton4Text'),
            control='buttonIgnored4' + self._parent_window.get_ext(),
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v - 14),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.ignoredButtonDescriptionText'),
            color=(0.7, 1, 0.7, 0.6),
            scale=0.8,
            maxwidth=self._sub_width * 0.8,
            h_align='center',
            v_align='center',
        )

        v -= 80
        pwin = self._parent_window
        bui.checkboxwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(h + 50, v),
            size=(400, 30),
            text=bui.Lstr(
                resource=f'{self._r}.startButtonActivatesDefaultText'
            ),
            textcolor=(0.8, 0.8, 0.8),
            maxwidth=450,
            scale=0.9,
            on_value_change_call=(
                pwin.set_start_button_activates_default_widget_value
            ),
            value=pwin.get_start_button_activates_default_widget_value(),
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v - 12),
            size=(0, 0),
            text=bui.Lstr(
                resource=f'{self._r}.startButtonActivatesDefaultDescriptionText'
            ),
            color=(0.7, 1, 0.7, 0.6),
            maxwidth=self._sub_width * 0.8,
            scale=0.7,
            h_align='center',
            v_align='center',
        )

        v -= 80
        bui.checkboxwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(h + 50, v),
            size=(400, 30),
            text=bui.Lstr(resource=f'{self._r}.uiOnlyText'),
            textcolor=(0.8, 0.8, 0.8),
            maxwidth=450,
            scale=0.9,
            on_value_change_call=self._parent_window.set_ui_only_value,
            value=self._parent_window.get_ui_only_value(),
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v - 12),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.uiOnlyDescriptionText'),
            color=(0.7, 1, 0.7, 0.6),
            maxwidth=self._sub_width * 0.8,
            scale=0.7,
            h_align='center',
            v_align='center',
        )

        v -= 80
        bui.checkboxwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(h + 50, v),
            size=(400, 30),
            text=bui.Lstr(resource=f'{self._r}.ignoreCompletelyText'),
            textcolor=(0.8, 0.8, 0.8),
            maxwidth=450,
            scale=0.9,
            on_value_change_call=pwin.set_ignore_completely_value,
            value=self._parent_window.get_ignore_completely_value(),
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v - 12),
            size=(0, 0),
            text=bui.Lstr(
                resource=f'{self._r}.ignoreCompletelyDescriptionText'
            ),
            color=(0.7, 1, 0.7, 0.6),
            maxwidth=self._sub_width * 0.8,
            scale=0.7,
            h_align='center',
            v_align='center',
        )

        v -= 80

        cb1 = bui.checkboxwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(h + 50, v),
            size=(400, 30),
            text=bui.Lstr(resource=f'{self._r}.autoRecalibrateText'),
            textcolor=(0.8, 0.8, 0.8),
            maxwidth=450,
            scale=0.9,
            on_value_change_call=pwin.set_auto_recalibrate_analog_stick_value,
            value=self._parent_window.get_auto_recalibrate_analog_stick_value(),
        )
        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v - 12),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.autoRecalibrateDescriptionText'),
            color=(0.7, 1, 0.7, 0.6),
            maxwidth=self._sub_width * 0.8,
            scale=0.7,
            h_align='center',
            v_align='center',
        )
        v -= 80

        buttons = self._config_value_editor(
            bui.Lstr(resource=f'{self._r}.analogStickDeadZoneText'),
            control=('analogStickDeadZone' + self._parent_window.get_ext()),
            position=(h + 40, v),
            min_val=0,
            max_val=10.0,
            increment=0.1,
            x_offset=100,
        )
        bui.widget(edit=buttons[0], left_widget=cb1, up_widget=cb1)
        bui.widget(edit=cb1, right_widget=buttons[0], down_widget=buttons[0])

        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v - 12),
            size=(0, 0),
            text=bui.Lstr(
                resource=f'{self._r}.analogStickDeadZoneDescriptionText'
            ),
            color=(0.7, 1, 0.7, 0.6),
            maxwidth=self._sub_width * 0.8,
            scale=0.7,
            h_align='center',
            v_align='center',
        )
        v -= 100

        # child joysticks cant have child joysticks.. that's just
        # crazy talk
        if not self._parent_window.get_is_secondary():
            bui.buttonwidget(
                parent=self._subcontainer,
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.twoInOneSetupText'),
                position=(40, v),
                size=(self._sub_width - 80, 50),
                on_activate_call=self._parent_window.show_secondary_editor,
                up_widget=buttons[0],
            )

        # set a bigger bottom show-buffer for the widgets we just made
        # so we can see the text below them when navigating with
        # a gamepad
        for child in self._subcontainer.get_children():
            bui.widget(edit=child, show_buffer_bottom=30, show_buffer_top=30)

    def _capture_button(
        self,
        pos: tuple[float, float],
        name: bui.Lstr,
        control: str,
        message: bui.Lstr | None = None,
    ) -> tuple[bui.Widget, bui.Widget]:
        if message is None:
            message = bui.Lstr(
                resource=self._parent_window.get_r() + '.pressAnyButtonText'
            )
        btn = bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(pos[0], pos[1]),
            label=name,
            size=(250, 60),
            scale=0.7,
        )
        btn2 = bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(pos[0] + 400, pos[1] + 2),
            left_widget=btn,
            color=(0.45, 0.4, 0.5),
            textcolor=(0.65, 0.6, 0.7),
            label=bui.Lstr(resource=f'{self._r}.clearText'),
            size=(110, 50),
            scale=0.7,
            on_activate_call=bui.Call(self._clear_control, control),
        )
        bui.widget(edit=btn, right_widget=btn2)

        # make this in a timer so that it shows up on top of all
        # other buttons

        def doit() -> None:
            from bauiv1lib.settings.gamepad import AwaitGamepadInputWindow

            txt = bui.textwidget(
                parent=self._subcontainer,
                position=(pos[0] + 285, pos[1] + 20),
                color=(1, 1, 1, 0.3),
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=0.7,
                text=self._parent_window.get_control_value_name(control),
                maxwidth=200,
            )
            self._textwidgets[control] = txt
            bui.buttonwidget(
                edit=btn,
                on_activate_call=bui.Call(
                    AwaitGamepadInputWindow,
                    self._parent_window.get_input(),
                    control,
                    self._gamepad_event,
                    message,
                ),
            )

        bui.pushcall(doit)
        return btn, btn2

    def _inc(
        self, control: str, min_val: float, max_val: float, inc: float
    ) -> None:
        val = self._parent_window.get_settings().get(control, 1.0)
        val = min(max_val, max(min_val, val + inc))
        if abs(1.0 - val) < 0.001:
            if control in self._parent_window.get_settings():
                del self._parent_window.get_settings()[control]
        else:
            self._parent_window.get_settings()[control] = round(val, 1)
        bui.textwidget(
            edit=self._textwidgets[control],
            text=self._parent_window.get_control_value_name(control),
        )

    def _config_value_editor(
        self,
        name: bui.Lstr,
        control: str,
        position: tuple[float, float],
        *,
        min_val: float = 0.0,
        max_val: float = 100.0,
        increment: float = 1.0,
        change_sound: bool = True,
        x_offset: float = 0.0,
        displayname: bui.Lstr | None = None,
    ) -> tuple[bui.Widget, bui.Widget]:
        if displayname is None:
            displayname = name
        bui.textwidget(
            parent=self._subcontainer,
            position=position,
            size=(100, 30),
            text=displayname,
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='left',
            v_align='center',
            scale=1.0,
            maxwidth=280,
        )
        self._textwidgets[control] = bui.textwidget(
            parent=self._subcontainer,
            position=(246.0 + x_offset, position[1]),
            size=(60, 28),
            editable=False,
            color=(0.3, 1.0, 0.3, 1.0),
            h_align='right',
            v_align='center',
            text=self._parent_window.get_control_value_name(control),
            padding=2,
        )
        btn = bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(330 + x_offset, position[1] + 4),
            size=(28, 28),
            label='-',
            on_activate_call=bui.Call(
                self._inc, control, min_val, max_val, -increment
            ),
            repeat=True,
            enable_sound=(change_sound is True),
        )
        btn2 = bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(380 + x_offset, position[1] + 4),
            size=(28, 28),
            label='+',
            on_activate_call=bui.Call(
                self._inc, control, min_val, max_val, increment
            ),
            repeat=True,
            enable_sound=(change_sound is True),
        )
        return btn, btn2

    def _clear_control(self, control: str) -> None:
        if control in self._parent_window.get_settings():
            del self._parent_window.get_settings()[control]
        bui.textwidget(
            edit=self._textwidgets[control],
            text=self._parent_window.get_control_value_name(control),
        )

    def _gamepad_event(
        self,
        control: str,
        event: dict[str, Any],
        dialog: AwaitGamepadInputWindow,
    ) -> None:
        ext = self._parent_window.get_ext()
        if control in ['triggerRun1' + ext, 'triggerRun2' + ext]:
            if event['type'] == 'AXISMOTION':
                # ignore small values or else we might get triggered
                # by noise
                if abs(event['value']) > 0.5:
                    self._parent_window.get_settings()[control] = event['axis']
                    # update the button's text widget
                    if self._textwidgets[control]:
                        bui.textwidget(
                            edit=self._textwidgets[control],
                            text=self._parent_window.get_control_value_name(
                                control
                            ),
                        )
                    bui.getsound('gunCocking').play()
                    dialog.die()
        else:
            if event['type'] == 'BUTTONDOWN':
                value = event['button']
                self._parent_window.get_settings()[control] = value
                # update the button's text widget
                if self._textwidgets[control]:
                    bui.textwidget(
                        edit=self._textwidgets[control],
                        text=self._parent_window.get_control_value_name(
                            control
                        ),
                    )
                bui.getsound('gunCocking').play()
                dialog.die()

    def _done(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
