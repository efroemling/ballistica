# Released under the MIT License. See LICENSE for details.
#
"""Keyboard settings related UI functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


class ConfigKeyboardWindow(bui.Window):
    """Window for configuring keyboards."""

    def __init__(self, c: bs.InputDevice, transition: str = 'in_right'):
        self._r = 'configKeyboardWindow'
        self._input = c
        self._name = self._input.name
        self._unique_id = self._input.unique_identifier
        dname_raw = self._name
        if self._unique_id != '#1':
            dname_raw += ' ' + self._unique_id.replace('#', 'P')
        self._displayname = bui.Lstr(translate=('inputDeviceNames', dname_raw))
        self._width = 700
        if self._unique_id != '#1':
            self._height = 480
        else:
            self._height = 375
        self._spacing = 40
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    1.6
                    if uiscale is bui.UIScale.SMALL
                    else 1.3
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
                stack_offset=(0, 5) if uiscale is bui.UIScale.SMALL else (0, 0),
                transition=transition,
            )
        )

        self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        assert bui.app.classic is not None

        for widget in self._root_widget.get_children():
            widget.delete()

        # Fill our temp config with present values.
        self._settings: dict[str, int] = {}
        for button in [
            'buttonJump',
            'buttonPunch',
            'buttonBomb',
            'buttonPickUp',
            'buttonStart',
            'buttonStart2',
            'buttonUp',
            'buttonDown',
            'buttonLeft',
            'buttonRight',
        ]:
            self._settings[
                button
            ] = bui.app.classic.get_input_device_mapped_value(
                self._input, button
            )

        cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(38, self._height - 85),
            size=(170, 60),
            label=bui.Lstr(resource='cancelText'),
            scale=0.9,
            on_activate_call=self._cancel,
        )
        save_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(self._width - 190, self._height - 85),
            size=(180, 60),
            label=bui.Lstr(resource='saveText'),
            scale=0.9,
            text_scale=0.9,
            on_activate_call=self._save,
        )
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=cancel_button,
            start_button=save_button,
        )

        bui.widget(edit=cancel_button, right_widget=save_button)
        bui.widget(edit=save_button, left_widget=cancel_button)

        v = self._height - 74.0
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, v + 15),
            size=(0, 0),
            text=bui.Lstr(
                resource=self._r + '.configuringText',
                subs=[('${DEVICE}', self._displayname)],
            ),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            maxwidth=270,
            scale=0.83,
        )
        v -= 20

        if self._unique_id != '#1':
            v -= 20
            v -= self._spacing
            bui.textwidget(
                parent=self._root_widget,
                position=(0, v + 19),
                size=(self._width, 50),
                text=bui.Lstr(resource=self._r + '.keyboard2NoteText'),
                scale=0.7,
                maxwidth=self._width * 0.75,
                max_height=110,
                color=bui.app.ui_v1.infotextcolor,
                h_align='center',
                v_align='top',
            )
            v -= 40
        v -= 10
        v -= self._spacing * 2.2
        v += 25
        v -= 42
        h_offs = 160
        dist = 70
        d_color = (0.4, 0.4, 0.8)
        self._capture_button(
            pos=(h_offs, v + 0.95 * dist),
            color=d_color,
            button='buttonUp',
            texture=bui.gettexture('upButton'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs - 1.2 * dist, v),
            color=d_color,
            button='buttonLeft',
            texture=bui.gettexture('leftButton'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs + 1.2 * dist, v),
            color=d_color,
            button='buttonRight',
            texture=bui.gettexture('rightButton'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs, v - 0.95 * dist),
            color=d_color,
            button='buttonDown',
            texture=bui.gettexture('downButton'),
            scale=1.0,
        )

        if self._unique_id == '#2':
            self._capture_button(
                pos=(self._width * 0.5, v + 0.1 * dist),
                color=(0.4, 0.4, 0.6),
                button='buttonStart',
                texture=bui.gettexture('startButton'),
                scale=0.8,
            )

        h_offs = self._width - 160

        self._capture_button(
            pos=(h_offs, v + 0.95 * dist),
            color=(0.6, 0.4, 0.8),
            button='buttonPickUp',
            texture=bui.gettexture('buttonPickUp'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs - 1.2 * dist, v),
            color=(0.7, 0.5, 0.1),
            button='buttonPunch',
            texture=bui.gettexture('buttonPunch'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs + 1.2 * dist, v),
            color=(0.5, 0.2, 0.1),
            button='buttonBomb',
            texture=bui.gettexture('buttonBomb'),
            scale=1.0,
        )
        self._capture_button(
            pos=(h_offs, v - 0.95 * dist),
            color=(0.2, 0.5, 0.2),
            button='buttonJump',
            texture=bui.gettexture('buttonJump'),
            scale=1.0,
        )

    def _pretty_button_name(self, button_name: str) -> bui.Lstr:
        button_id = self._settings[button_name]
        if button_id == -1:
            return bs.Lstr(resource='configGamepadWindow.unsetText')
        return self._input.get_button_name(button_id)

    def _capture_button(
        self,
        pos: tuple[float, float],
        color: tuple[float, float, float],
        texture: bui.Texture,
        button: str,
        scale: float = 1.0,
    ) -> None:
        base_size = 79
        btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(
                pos[0] - base_size * 0.5 * scale,
                pos[1] - base_size * 0.5 * scale,
            ),
            size=(base_size * scale, base_size * scale),
            texture=texture,
            label='',
            color=color,
        )

        # Do this deferred so it shows up on top of other buttons. (ew.)
        def doit() -> None:
            if not self._root_widget:
                return
            uiscale = 0.66 * scale * 2.0
            maxwidth = 76.0 * scale
            txt = bui.textwidget(
                parent=self._root_widget,
                position=(pos[0] + 0.0 * scale, pos[1] - (57.0 - 18.0) * scale),
                color=(1, 1, 1, 0.3),
                size=(0, 0),
                h_align='center',
                v_align='top',
                scale=uiscale,
                maxwidth=maxwidth,
                text=self._pretty_button_name(button),
            )
            bui.buttonwidget(
                edit=btn,
                autoselect=True,
                on_activate_call=bui.Call(
                    AwaitKeyboardInputWindow, button, txt, self._settings
                ),
            )

        bui.pushcall(doit)

    def _cancel(self) -> None:
        from bauiv1lib.settings.controls import ControlsSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(edit=self._root_widget, transition='out_right')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            ControlsSettingsWindow(transition='in_left').get_root_widget(),
            from_window=self._root_widget,
        )

    def _save(self) -> None:
        from bauiv1lib.settings.controls import ControlsSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        assert bui.app.classic is not None
        bui.containerwidget(edit=self._root_widget, transition='out_right')
        bui.getsound('gunCocking').play()

        # There's a chance the device disappeared; handle that gracefully.
        if not self._input:
            return

        dst = bui.app.classic.get_input_device_config(
            self._input, default=False
        )
        dst2: dict[str, Any] = dst[0][dst[1]]
        dst2.clear()

        # Store any values that aren't -1.
        for key, val in list(self._settings.items()):
            if val != -1:
                dst2[key] = val

        # Send this config to the master-server so we can generate
        # more defaults in the future.
        if bui.app.classic is not None:
            bui.app.classic.master_server_v1_post(
                'controllerConfig',
                {
                    'ua': bui.app.classic.legacy_user_agent_string,
                    'name': self._name,
                    'b': bui.app.env.build_number,
                    'config': dst2,
                    'v': 2,
                },
            )
        bui.app.config.apply_and_commit()
        bui.app.ui_v1.set_main_menu_window(
            ControlsSettingsWindow(transition='in_left').get_root_widget(),
            from_window=self._root_widget,
        )


class AwaitKeyboardInputWindow(bui.Window):
    """Window for capturing a keypress."""

    def __init__(self, button: str, ui: bui.Widget, settings: dict):
        self._capture_button = button
        self._capture_key_ui = ui
        self._settings = settings

        width = 400
        height = 150
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition='in_right',
                scale=(
                    2.0
                    if uiscale is bui.UIScale.SMALL
                    else 1.5
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
            )
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 60),
            size=(width, 25),
            text=bui.Lstr(resource='pressAnyKeyText'),
            h_align='center',
            v_align='top',
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
            1.0, self._decrement, repeat=True
        )
        bs.capture_keyboard_input(bui.WeakCall(self._button_callback))

    def __del__(self) -> None:
        bs.release_keyboard_input()

    def _die(self) -> None:
        # This strong-refs us; killing it allows us to die now.
        self._decrement_timer = None
        if self._root_widget:
            bui.containerwidget(edit=self._root_widget, transition='out_left')

    def _button_callback(self, event: dict[str, Any]) -> None:
        self._settings[self._capture_button] = event['button']
        if event['type'] == 'BUTTONDOWN':
            bname = event['input_device'].get_button_name(event['button'])
            bui.textwidget(edit=self._capture_key_ui, text=bname)
            bui.getsound('gunCocking').play()
            self._die()

    def _decrement(self) -> None:
        self._counter -= 1
        if self._counter >= 1:
            bui.textwidget(edit=self._count_down_text, text=str(self._counter))
        else:
            self._die()
