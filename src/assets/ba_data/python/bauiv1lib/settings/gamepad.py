# Released under the MIT License. See LICENSE for details.
#
"""Settings UI functionality related to gamepads."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class GamepadSettingsWindow(bui.Window):
    """Window for configuring a gamepad."""

    def __init__(
        self,
        gamepad: bs.InputDevice,
        is_main_menu: bool = True,
        transition: str = 'in_right',
        transition_out: str = 'out_right',
        settings: dict | None = None,
    ):
        self._input = gamepad

        # If our input-device went away, just return an empty zombie.
        if not self._input:
            return

        self._name = self._input.name

        self._r = 'configGamepadWindow'
        self._settings = settings
        self._transition_out = transition_out

        # We're a secondary gamepad if supplied with settings.
        self._is_secondary = settings is not None
        self._ext = '_B' if self._is_secondary else ''
        self._is_main_menu = is_main_menu
        self._displayname = self._name
        self._width = 700 if self._is_secondary else 730
        self._height = 440 if self._is_secondary else 450
        self._spacing = 40
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    1.63
                    if uiscale is bui.UIScale.SMALL
                    else 1.35
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
                stack_offset=(-20, -16)
                if uiscale is bui.UIScale.SMALL
                else (0, 0),
                transition=transition,
            )
        )

        # Don't ask to config joysticks while we're in here.
        self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        assert bui.app.classic is not None

        # Clear existing UI.
        for widget in self._root_widget.get_children():
            widget.delete()

        self._textwidgets: dict[str, bui.Widget] = {}

        # If we were supplied with settings, we're a secondary joystick and
        # just operate on that. in the other (normal) case we make our own.
        if not self._is_secondary:
            # Fill our temp config with present values (for our primary and
            # secondary controls).
            self._settings = {}
            for skey in [
                'buttonJump',
                'buttonJump_B',
                'buttonPunch',
                'buttonPunch_B',
                'buttonBomb',
                'buttonBomb_B',
                'buttonPickUp',
                'buttonPickUp_B',
                'buttonStart',
                'buttonStart_B',
                'buttonStart2',
                'buttonStart2_B',
                'buttonUp',
                'buttonUp_B',
                'buttonDown',
                'buttonDown_B',
                'buttonLeft',
                'buttonLeft_B',
                'buttonRight',
                'buttonRight_B',
                'buttonRun1',
                'buttonRun1_B',
                'buttonRun2',
                'buttonRun2_B',
                'triggerRun1',
                'triggerRun1_B',
                'triggerRun2',
                'triggerRun2_B',
                'buttonIgnored',
                'buttonIgnored_B',
                'buttonIgnored2',
                'buttonIgnored2_B',
                'buttonIgnored3',
                'buttonIgnored3_B',
                'buttonIgnored4',
                'buttonIgnored4_B',
                'buttonVRReorient',
                'buttonVRReorient_B',
                'analogStickDeadZone',
                'analogStickDeadZone_B',
                'dpad',
                'dpad_B',
                'unassignedButtonsRun',
                'unassignedButtonsRun_B',
                'startButtonActivatesDefaultWidget',
                'startButtonActivatesDefaultWidget_B',
                'uiOnly',
                'uiOnly_B',
                'ignoreCompletely',
                'ignoreCompletely_B',
                'autoRecalibrateAnalogStick',
                'autoRecalibrateAnalogStick_B',
                'analogStickLR',
                'analogStickLR_B',
                'analogStickUD',
                'analogStickUD_B',
                'enableSecondary',
            ]:
                val = bui.app.classic.get_input_device_mapped_value(
                    self._input, skey
                )
                if val != -1:
                    self._settings[skey] = val

        back_button: bui.Widget | None

        if self._is_secondary:
            back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(self._width - 180, self._height - 65),
                autoselect=True,
                size=(160, 60),
                label=bui.Lstr(resource='doneText'),
                scale=0.9,
                on_activate_call=self._save,
            )
            bui.containerwidget(
                edit=self._root_widget,
                start_button=back_button,
                on_cancel_call=back_button.activate,
            )
            cancel_button = None
        else:
            cancel_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(51, self._height - 65),
                autoselect=True,
                size=(160, 60),
                label=bui.Lstr(resource='cancelText'),
                scale=0.9,
                on_activate_call=self._cancel,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=cancel_button
            )

        save_button: bui.Widget | None
        if not self._is_secondary:
            save_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(self._width - 195, self._height - 65),
                size=(180, 60),
                autoselect=True,
                label=bui.Lstr(resource='saveText'),
                scale=0.9,
                on_activate_call=self._save,
            )
            bui.containerwidget(
                edit=self._root_widget, start_button=save_button
            )
        else:
            save_button = None

        if not self._is_secondary:
            v = self._height - 59
            bui.textwidget(
                parent=self._root_widget,
                position=(0, v + 5),
                size=(self._width, 25),
                text=bui.Lstr(resource=self._r + '.titleText'),
                color=bui.app.ui_v1.title_color,
                maxwidth=310,
                h_align='center',
                v_align='center',
            )
            v -= 48

            bui.textwidget(
                parent=self._root_widget,
                position=(0, v + 3),
                size=(self._width, 25),
                text=self._name,
                color=bui.app.ui_v1.infotextcolor,
                maxwidth=self._width * 0.9,
                h_align='center',
                v_align='center',
            )
            v -= self._spacing * 1

            bui.textwidget(
                parent=self._root_widget,
                position=(50, v + 10),
                size=(self._width - 100, 30),
                text=bui.Lstr(resource=self._r + '.appliesToAllText'),
                maxwidth=330,
                scale=0.65,
                color=(0.5, 0.6, 0.5, 1.0),
                h_align='center',
                v_align='center',
            )
            v -= 70
            self._enable_check_box = None
        else:
            v = self._height - 49
            bui.textwidget(
                parent=self._root_widget,
                position=(0, v + 5),
                size=(self._width, 25),
                text=bui.Lstr(resource=self._r + '.secondaryText'),
                color=bui.app.ui_v1.title_color,
                maxwidth=300,
                h_align='center',
                v_align='center',
            )
            v -= self._spacing * 1

            bui.textwidget(
                parent=self._root_widget,
                position=(50, v + 10),
                size=(self._width - 100, 30),
                text=bui.Lstr(resource=self._r + '.secondHalfText'),
                maxwidth=300,
                scale=0.65,
                color=(0.6, 0.8, 0.6, 1.0),
                h_align='center',
            )
            self._enable_check_box = bui.checkboxwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 - 80, v - 73),
                value=self.get_enable_secondary_value(),
                autoselect=True,
                on_value_change_call=self._enable_check_box_changed,
                size=(200, 30),
                text=bui.Lstr(resource=self._r + '.secondaryEnableText'),
                scale=1.2,
            )
            v = self._height - 205

        h_offs = 160
        dist = 70
        d_color = (0.4, 0.4, 0.8)
        sclx = 1.2
        scly = 0.98
        dpm = bui.Lstr(resource=self._r + '.pressAnyButtonOrDpadText')
        dpm2 = bui.Lstr(resource=self._r + '.ifNothingHappensTryAnalogText')
        self._capture_button(
            pos=(h_offs, v + scly * dist),
            color=d_color,
            button='buttonUp' + self._ext,
            texture=bui.gettexture('upButton'),
            scale=1.0,
            message=dpm,
            message2=dpm2,
        )
        self._capture_button(
            pos=(h_offs - sclx * dist, v),
            color=d_color,
            button='buttonLeft' + self._ext,
            texture=bui.gettexture('leftButton'),
            scale=1.0,
            message=dpm,
            message2=dpm2,
        )
        self._capture_button(
            pos=(h_offs + sclx * dist, v),
            color=d_color,
            button='buttonRight' + self._ext,
            texture=bui.gettexture('rightButton'),
            scale=1.0,
            message=dpm,
            message2=dpm2,
        )
        self._capture_button(
            pos=(h_offs, v - scly * dist),
            color=d_color,
            button='buttonDown' + self._ext,
            texture=bui.gettexture('downButton'),
            scale=1.0,
            message=dpm,
            message2=dpm2,
        )

        dpm3 = bui.Lstr(resource=self._r + '.ifNothingHappensTryDpadText')
        self._capture_button(
            pos=(h_offs + 130, v - 125),
            color=(0.4, 0.4, 0.6),
            button='analogStickLR' + self._ext,
            maxwidth=140,
            texture=bui.gettexture('analogStick'),
            scale=1.2,
            message=bui.Lstr(resource=self._r + '.pressLeftRightText'),
            message2=dpm3,
        )

        self._capture_button(
            pos=(self._width * 0.5, v),
            color=(0.4, 0.4, 0.6),
            button='buttonStart' + self._ext,
            texture=bui.gettexture('startButton'),
            scale=0.7,
        )

        h_offs = self._width - 160

        self._capture_button(
            pos=(h_offs, v + scly * dist),
            color=(0.6, 0.4, 0.8),
            button='buttonPickUp' + self._ext,
            texture=bui.gettexture('buttonPickUp'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs - sclx * dist, v),
            color=(0.7, 0.5, 0.1),
            button='buttonPunch' + self._ext,
            texture=bui.gettexture('buttonPunch'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs + sclx * dist, v),
            color=(0.5, 0.2, 0.1),
            button='buttonBomb' + self._ext,
            texture=bui.gettexture('buttonBomb'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs, v - scly * dist),
            color=(0.2, 0.5, 0.2),
            button='buttonJump' + self._ext,
            texture=bui.gettexture('buttonJump'),
            scale=1.0,
        )

        self._advanced_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            label=bui.Lstr(resource=self._r + '.advancedText'),
            text_scale=0.9,
            color=(0.45, 0.4, 0.5),
            textcolor=(0.65, 0.6, 0.7),
            position=(self._width - 300, 30),
            size=(130, 40),
            on_activate_call=self._do_advanced,
        )

        try:
            if cancel_button is not None and save_button is not None:
                bui.widget(edit=cancel_button, right_widget=save_button)
                bui.widget(edit=save_button, left_widget=cancel_button)
        except Exception:
            logging.exception('Error wiring up gamepad config window.')

    def get_r(self) -> str:
        """(internal)"""
        return self._r

    def get_advanced_button(self) -> bui.Widget:
        """(internal)"""
        return self._advanced_button

    def get_is_secondary(self) -> bool:
        """(internal)"""
        return self._is_secondary

    def get_settings(self) -> dict[str, Any]:
        """(internal)"""
        assert self._settings is not None
        return self._settings

    def get_ext(self) -> str:
        """(internal)"""
        return self._ext

    def get_input(self) -> bs.InputDevice:
        """(internal)"""
        return self._input

    def _do_advanced(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings import gamepadadvanced

        gamepadadvanced.GamepadAdvancedSettingsWindow(self)

    def _enable_check_box_changed(self, value: bool) -> None:
        assert self._settings is not None
        if value:
            self._settings['enableSecondary'] = 1
        else:
            # Just clear since this is default.
            if 'enableSecondary' in self._settings:
                del self._settings['enableSecondary']

    def get_unassigned_buttons_run_value(self) -> bool:
        """(internal)"""
        assert self._settings is not None
        val = self._settings.get('unassignedButtonsRun', True)
        assert isinstance(val, bool)
        return val

    def set_unassigned_buttons_run_value(self, value: bool) -> None:
        """(internal)"""
        assert self._settings is not None
        if value:
            if 'unassignedButtonsRun' in self._settings:
                # Clear since this is default.
                del self._settings['unassignedButtonsRun']
                return
        self._settings['unassignedButtonsRun'] = False

    def get_start_button_activates_default_widget_value(self) -> bool:
        """(internal)"""
        assert self._settings is not None
        val = self._settings.get('startButtonActivatesDefaultWidget', True)
        assert isinstance(val, bool)
        return val

    def set_start_button_activates_default_widget_value(
        self, value: bool
    ) -> None:
        """(internal)"""
        assert self._settings is not None
        if value:
            if 'startButtonActivatesDefaultWidget' in self._settings:
                # Clear since this is default.
                del self._settings['startButtonActivatesDefaultWidget']
                return
        self._settings['startButtonActivatesDefaultWidget'] = False

    def get_ui_only_value(self) -> bool:
        """(internal)"""
        assert self._settings is not None
        val = self._settings.get('uiOnly', False)
        assert isinstance(val, bool)
        return val

    def set_ui_only_value(self, value: bool) -> None:
        """(internal)"""
        assert self._settings is not None
        if not value:
            if 'uiOnly' in self._settings:
                # Clear since this is default.
                del self._settings['uiOnly']
                return
        self._settings['uiOnly'] = True

    def get_ignore_completely_value(self) -> bool:
        """(internal)"""
        assert self._settings is not None
        val = self._settings.get('ignoreCompletely', False)
        assert isinstance(val, bool)
        return val

    def set_ignore_completely_value(self, value: bool) -> None:
        """(internal)"""
        assert self._settings is not None
        if not value:
            if 'ignoreCompletely' in self._settings:
                # Clear since this is default.
                del self._settings['ignoreCompletely']
                return
        self._settings['ignoreCompletely'] = True

    def get_auto_recalibrate_analog_stick_value(self) -> bool:
        """(internal)"""
        assert self._settings is not None
        val = self._settings.get('autoRecalibrateAnalogStick', False)
        assert isinstance(val, bool)
        return val

    def set_auto_recalibrate_analog_stick_value(self, value: bool) -> None:
        """(internal)"""
        assert self._settings is not None
        if not value:
            if 'autoRecalibrateAnalogStick' in self._settings:
                # Clear since this is default.
                del self._settings['autoRecalibrateAnalogStick']
        else:
            self._settings['autoRecalibrateAnalogStick'] = True

    def get_enable_secondary_value(self) -> bool:
        """(internal)"""
        assert self._settings is not None
        if not self._is_secondary:
            raise RuntimeError('Enable value only applies to secondary editor.')
        val = self._settings.get('enableSecondary', False)
        assert isinstance(val, bool)
        return val

    def show_secondary_editor(self) -> None:
        """(internal)"""
        GamepadSettingsWindow(
            self._input,
            is_main_menu=False,
            settings=self._settings,
            transition='in_scale',
            transition_out='out_scale',
        )

    def get_control_value_name(self, control: str) -> str | bui.Lstr:
        """(internal)"""
        # pylint: disable=too-many-return-statements
        assert self._settings is not None
        if control == 'analogStickLR' + self._ext:
            # This actually shows both LR and UD.
            sval1 = (
                self._settings['analogStickLR' + self._ext]
                if 'analogStickLR' + self._ext in self._settings
                else 5
                if self._is_secondary
                else None
            )
            sval2 = (
                self._settings['analogStickUD' + self._ext]
                if 'analogStickUD' + self._ext in self._settings
                else 6
                if self._is_secondary
                else None
            )
            assert isinstance(sval1, (int, type(None)))
            assert isinstance(sval2, (int, type(None)))
            if sval1 is not None and sval2 is not None:
                return (
                    self._input.get_axis_name(sval1)
                    + ' / '
                    + self._input.get_axis_name(sval2)
                )
            return bui.Lstr(resource=self._r + '.unsetText')

        # If they're looking for triggers.
        if control in ['triggerRun1' + self._ext, 'triggerRun2' + self._ext]:
            if control in self._settings:
                return self._input.get_axis_name(self._settings[control])
            return bui.Lstr(resource=self._r + '.unsetText')

        # Dead-zone.
        if control == 'analogStickDeadZone' + self._ext:
            if control in self._settings:
                return str(self._settings[control])
            return str(1.0)

        # For dpad buttons: show individual buttons if any are set.
        # Otherwise show whichever dpad is set.
        dpad_buttons = [
            'buttonLeft' + self._ext,
            'buttonRight' + self._ext,
            'buttonUp' + self._ext,
            'buttonDown' + self._ext,
        ]
        if control in dpad_buttons:
            # If *any* dpad buttons are assigned, show only button assignments.
            if any(b in self._settings for b in dpad_buttons):
                if control in self._settings:
                    return self._input.get_button_name(self._settings[control])
                return bui.Lstr(resource=self._r + '.unsetText')

            # No dpad buttons - show the dpad number for all 4.
            dpadnum = (
                self._settings['dpad' + self._ext]
                if 'dpad' + self._ext in self._settings
                else 2
                if self._is_secondary
                else None
            )
            assert isinstance(dpadnum, (int, type(None)))
            if dpadnum is not None:
                return bui.Lstr(
                    value='${A} ${B}',
                    subs=[
                        ('${A}', bui.Lstr(resource=self._r + '.dpadText')),
                        (
                            '${B}',
                            str(dpadnum),
                        ),
                    ],
                )
            return bui.Lstr(resource=self._r + '.unsetText')

        # Other buttons.
        if control in self._settings:
            return self._input.get_button_name(self._settings[control])
        return bui.Lstr(resource=self._r + '.unsetText')

    def _gamepad_event(
        self,
        control: str,
        event: dict[str, Any],
        dialog: AwaitGamepadInputWindow,
    ) -> None:
        # pylint: disable=too-many-branches
        assert self._settings is not None
        ext = self._ext

        # For our dpad-buttons we're looking for either a button-press or a
        # hat-switch press.
        if control in [
            'buttonUp' + ext,
            'buttonLeft' + ext,
            'buttonDown' + ext,
            'buttonRight' + ext,
        ]:
            if event['type'] in ['BUTTONDOWN', 'HATMOTION']:
                # If its a button-down.
                if event['type'] == 'BUTTONDOWN':
                    value = event['button']
                    self._settings[control] = value

                # If its a dpad.
                elif event['type'] == 'HATMOTION':
                    # clear out any set dir-buttons
                    for btn in [
                        'buttonUp' + ext,
                        'buttonLeft' + ext,
                        'buttonRight' + ext,
                        'buttonDown' + ext,
                    ]:
                        if btn in self._settings:
                            del self._settings[btn]
                    if event['hat'] == (2 if self._is_secondary else 1):
                        self._settings['dpad' + ext] = event['hat']

                # Update the 4 dpad button txt widgets.
                bui.textwidget(
                    edit=self._textwidgets['buttonUp' + ext],
                    text=self.get_control_value_name('buttonUp' + ext),
                )
                bui.textwidget(
                    edit=self._textwidgets['buttonLeft' + ext],
                    text=self.get_control_value_name('buttonLeft' + ext),
                )
                bui.textwidget(
                    edit=self._textwidgets['buttonRight' + ext],
                    text=self.get_control_value_name('buttonRight' + ext),
                )
                bui.textwidget(
                    edit=self._textwidgets['buttonDown' + ext],
                    text=self.get_control_value_name('buttonDown' + ext),
                )
                bui.getsound('gunCocking').play()
                dialog.die()

        elif control == 'analogStickLR' + ext:
            if event['type'] == 'AXISMOTION':
                # Ignore small values or else we might get triggered by noise.
                if abs(event['value']) > 0.5:
                    axis = event['axis']
                    if axis == (5 if self._is_secondary else 1):
                        self._settings['analogStickLR' + ext] = axis
                    bui.textwidget(
                        edit=self._textwidgets['analogStickLR' + ext],
                        text=self.get_control_value_name('analogStickLR' + ext),
                    )
                    bui.getsound('gunCocking').play()
                    dialog.die()

                    # Now launch the up/down listener.
                    AwaitGamepadInputWindow(
                        self._input,
                        'analogStickUD' + ext,
                        self._gamepad_event,
                        bui.Lstr(resource=self._r + '.pressUpDownText'),
                    )

        elif control == 'analogStickUD' + ext:
            if event['type'] == 'AXISMOTION':
                # Ignore small values or else we might get triggered by noise.
                if abs(event['value']) > 0.5:
                    axis = event['axis']

                    # Ignore our LR axis.
                    if 'analogStickLR' + ext in self._settings:
                        lr_axis = self._settings['analogStickLR' + ext]
                    else:
                        lr_axis = 5 if self._is_secondary else 1
                    if axis != lr_axis:
                        if axis == (6 if self._is_secondary else 2):
                            self._settings['analogStickUD' + ext] = axis
                        bui.textwidget(
                            edit=self._textwidgets['analogStickLR' + ext],
                            text=self.get_control_value_name(
                                'analogStickLR' + ext
                            ),
                        )
                        bui.getsound('gunCocking').play()
                        dialog.die()
        else:
            # For other buttons we just want a button-press.
            if event['type'] == 'BUTTONDOWN':
                value = event['button']
                self._settings[control] = value

                # Update the button's text widget.
                bui.textwidget(
                    edit=self._textwidgets[control],
                    text=self.get_control_value_name(control),
                )
                bui.getsound('gunCocking').play()
                dialog.die()

    def _capture_button(
        self,
        pos: tuple[float, float],
        color: tuple[float, float, float],
        texture: bui.Texture,
        button: str,
        scale: float = 1.0,
        message: bui.Lstr | None = None,
        message2: bui.Lstr | None = None,
        maxwidth: float = 80.0,
    ) -> bui.Widget:
        if message is None:
            message = bui.Lstr(resource=self._r + '.pressAnyButtonText')
        base_size = 79
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                pos[0] - base_size * 0.5 * scale,
                pos[1] - base_size * 0.5 * scale,
            ),
            autoselect=True,
            size=(base_size * scale, base_size * scale),
            texture=texture,
            label='',
            color=color,
        )

        # Make this in a timer so that it shows up on top of all other buttons.

        def doit() -> None:
            uiscale = 0.9 * scale
            txt = bui.textwidget(
                parent=self._root_widget,
                position=(pos[0] + 0.0 * scale, pos[1] - 58.0 * scale),
                color=(1, 1, 1, 0.3),
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=uiscale,
                text=self.get_control_value_name(button),
                maxwidth=maxwidth,
            )
            self._textwidgets[button] = txt
            bui.buttonwidget(
                edit=btn,
                on_activate_call=bui.Call(
                    AwaitGamepadInputWindow,
                    self._input,
                    button,
                    self._gamepad_event,
                    message,
                    message2,
                ),
            )

        bui.pushcall(doit)
        return btn

    def _cancel(self) -> None:
        from bauiv1lib.settings.controls import ControlsSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        if self._is_main_menu:
            assert bui.app.classic is not None
            bui.app.ui_v1.set_main_menu_window(
                ControlsSettingsWindow(transition='in_left').get_root_widget(),
                from_window=self._root_widget,
            )

    def _save(self) -> None:
        classic = bui.app.classic
        assert classic is not None

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

        # If we're a secondary editor we just go away (we were editing our
        # parent's settings dict).
        if self._is_secondary:
            return

        assert self._settings is not None
        if self._input:
            dst = classic.get_input_device_config(self._input, default=True)
            dst2: dict[str, Any] = dst[0][dst[1]]
            dst2.clear()

            # Store any values that aren't -1.
            for key, val in list(self._settings.items()):
                if val != -1:
                    dst2[key] = val

            # If we're allowed to phone home, send this config so we can
            # generate more defaults in the future.
            inputhash = classic.get_input_device_map_hash(self._input)
            classic.master_server_v1_post(
                'controllerConfig',
                {
                    'ua': classic.legacy_user_agent_string,
                    'b': bui.app.env.build_number,
                    'name': self._name,
                    'inputMapHash': inputhash,
                    'config': dst2,
                    'v': 2,
                },
            )
            bui.app.config.apply_and_commit()
            bui.getsound('gunCocking').play()
        else:
            bui.getsound('error').play()

        if self._is_main_menu:
            from bauiv1lib.settings.controls import ControlsSettingsWindow

            assert bui.app.classic is not None
            bui.app.ui_v1.set_main_menu_window(
                ControlsSettingsWindow(transition='in_left').get_root_widget(),
                from_window=self._root_widget,
            )


class AwaitGamepadInputWindow(bui.Window):
    """Window for capturing a gamepad button press."""

    def __init__(
        self,
        gamepad: bs.InputDevice,
        button: str,
        callback: Callable[[str, dict[str, Any], AwaitGamepadInputWindow], Any],
        message: bui.Lstr | None = None,
        message2: bui.Lstr | None = None,
    ):
        if message is None:
            print('AwaitGamepadInputWindow message is None!')
            # Shouldn't get here.
            message = bui.Lstr(value='Press any button...')
        self._callback = callback
        self._input = gamepad
        self._capture_button = button
        width = 400
        height = 150
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                scale=(
                    2.0
                    if uiscale is bui.UIScale.SMALL
                    else 1.9
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
                size=(width, height),
                transition='in_scale',
            ),
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(0, (height - 60) if message2 is None else (height - 50)),
            size=(width, 25),
            text=message,
            maxwidth=width * 0.9,
            h_align='center',
            v_align='center',
        )
        if message2 is not None:
            bui.textwidget(
                parent=self._root_widget,
                position=(width * 0.5, height - 60),
                size=(0, 0),
                text=message2,
                maxwidth=width * 0.9,
                scale=0.47,
                color=(0.7, 1.0, 0.7, 0.6),
                h_align='center',
                v_align='center',
            )
        self._counter = 5
        self._count_down_text = bui.textwidget(
            parent=self._root_widget,
            h_align='center',
            position=(0, height - 110),
            size=(width, 25),
            color=(1, 1, 1, 0.3),
            text=str(self._counter),
        )
        self._decrement_timer: bui.AppTimer | None = bui.AppTimer(
            1.0, bui.Call(self._decrement), repeat=True
        )
        bs.capture_gamepad_input(bui.WeakCall(self._event_callback))

    def __del__(self) -> None:
        pass

    def die(self) -> None:
        """Kill the window."""

        # This strong-refs us; killing it allow us to die now.
        self._decrement_timer = None
        bs.release_gamepad_input()
        if self._root_widget:
            bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def _event_callback(self, event: dict[str, Any]) -> None:
        input_device = event['input_device']
        assert isinstance(input_device, bs.InputDevice)

        # Update - we now allow *any* input device of this type.
        if (
            self._input
            and input_device
            and input_device.name == self._input.name
        ):
            self._callback(self._capture_button, event, self)

    def _decrement(self) -> None:
        self._counter -= 1
        if self._counter >= 1:
            if self._count_down_text:
                bui.textwidget(
                    edit=self._count_down_text, text=str(self._counter)
                )
        else:
            bui.getsound('error').play()
            self.die()
