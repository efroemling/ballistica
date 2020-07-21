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
"""Keyboard settings related UI functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Dict, Tuple, Any, Optional


class ConfigKeyboardWindow(ba.Window):
    """Window for configuring keyboards."""

    def __init__(self, c: ba.InputDevice, transition: str = 'in_right'):
        self._r = 'configKeyboardWindow'
        self._input = c
        self._name = self._input.name
        self._unique_id = self._input.unique_identifier
        dname_raw = self._name
        if self._unique_id != '#1':
            dname_raw += ' ' + self._unique_id.replace('#', 'P')
        self._displayname = ba.Lstr(translate=('inputDeviceNames', dname_raw))
        self._width = 700
        if self._unique_id != '#1':
            self._height = 480
        else:
            self._height = 375
        self._spacing = 40
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            scale=(1.6 if uiscale is ba.UIScale.SMALL else
                   1.3 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, 5) if uiscale is ba.UIScale.SMALL else (0, 0),
            transition=transition))

        self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        from ba.internal import get_device_value
        for widget in self._root_widget.get_children():
            widget.delete()

        # Fill our temp config with present values.
        self._settings: Dict[str, int] = {}
        for button in [
                'buttonJump', 'buttonPunch', 'buttonBomb', 'buttonPickUp',
                'buttonStart', 'buttonStart2', 'buttonUp', 'buttonDown',
                'buttonLeft', 'buttonRight'
        ]:
            self._settings[button] = get_device_value(self._input, button)

        cancel_button = ba.buttonwidget(parent=self._root_widget,
                                        autoselect=True,
                                        position=(38, self._height - 85),
                                        size=(170, 60),
                                        label=ba.Lstr(resource='cancelText'),
                                        scale=0.9,
                                        on_activate_call=self._cancel)
        save_button = ba.buttonwidget(parent=self._root_widget,
                                      autoselect=True,
                                      position=(self._width - 190,
                                                self._height - 85),
                                      size=(180, 60),
                                      label=ba.Lstr(resource='saveText'),
                                      scale=0.9,
                                      text_scale=0.9,
                                      on_activate_call=self._save)
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=cancel_button,
                           start_button=save_button)

        ba.widget(edit=cancel_button, right_widget=save_button)
        ba.widget(edit=save_button, left_widget=cancel_button)

        v = self._height - 74.0
        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, v + 15),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.configuringText',
                                   subs=[('${DEVICE}', self._displayname)]),
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='center',
                      maxwidth=270,
                      scale=0.83)
        v -= 20

        if self._unique_id != '#1':
            v -= 20
            v -= self._spacing
            ba.textwidget(parent=self._root_widget,
                          position=(0, v + 19),
                          size=(self._width, 50),
                          text=ba.Lstr(resource=self._r +
                                       '.keyboard2NoteText'),
                          scale=0.7,
                          maxwidth=self._width * 0.75,
                          max_height=110,
                          color=ba.app.ui.infotextcolor,
                          h_align='center',
                          v_align='top')
            v -= 40
        v -= 10
        v -= self._spacing * 2.2
        v += 25
        v -= 42
        h_offs = 160
        dist = 70
        d_color = (0.4, 0.4, 0.8)
        self._capture_button(pos=(h_offs, v + 0.95 * dist),
                             color=d_color,
                             button='buttonUp',
                             texture=ba.gettexture('upButton'),
                             scale=1.0)
        self._capture_button(pos=(h_offs - 1.2 * dist, v),
                             color=d_color,
                             button='buttonLeft',
                             texture=ba.gettexture('leftButton'),
                             scale=1.0)
        self._capture_button(pos=(h_offs + 1.2 * dist, v),
                             color=d_color,
                             button='buttonRight',
                             texture=ba.gettexture('rightButton'),
                             scale=1.0)
        self._capture_button(pos=(h_offs, v - 0.95 * dist),
                             color=d_color,
                             button='buttonDown',
                             texture=ba.gettexture('downButton'),
                             scale=1.0)

        if self._unique_id == '#2':
            self._capture_button(pos=(self._width * 0.5, v + 0.1 * dist),
                                 color=(0.4, 0.4, 0.6),
                                 button='buttonStart',
                                 texture=ba.gettexture('startButton'),
                                 scale=0.8)

        h_offs = self._width - 160

        self._capture_button(pos=(h_offs, v + 0.95 * dist),
                             color=(0.6, 0.4, 0.8),
                             button='buttonPickUp',
                             texture=ba.gettexture('buttonPickUp'),
                             scale=1.0)
        self._capture_button(pos=(h_offs - 1.2 * dist, v),
                             color=(0.7, 0.5, 0.1),
                             button='buttonPunch',
                             texture=ba.gettexture('buttonPunch'),
                             scale=1.0)
        self._capture_button(pos=(h_offs + 1.2 * dist, v),
                             color=(0.5, 0.2, 0.1),
                             button='buttonBomb',
                             texture=ba.gettexture('buttonBomb'),
                             scale=1.0)
        self._capture_button(pos=(h_offs, v - 0.95 * dist),
                             color=(0.2, 0.5, 0.2),
                             button='buttonJump',
                             texture=ba.gettexture('buttonJump'),
                             scale=1.0)

    def _capture_button(self,
                        pos: Tuple[float, float],
                        color: Tuple[float, float, float],
                        texture: ba.Texture,
                        button: str,
                        scale: float = 1.0) -> None:
        base_size = 79
        btn = ba.buttonwidget(parent=self._root_widget,
                              autoselect=True,
                              position=(pos[0] - base_size * 0.5 * scale,
                                        pos[1] - base_size * 0.5 * scale),
                              size=(base_size * scale, base_size * scale),
                              texture=texture,
                              label='',
                              color=color)

        # Do this deferred so it shows up on top of other buttons. (ew.)
        def doit() -> None:
            if not self._root_widget:
                return
            uiscale = 0.66 * scale * 2.0
            maxwidth = 76.0 * scale
            txt = ba.textwidget(parent=self._root_widget,
                                position=(pos[0] + 0.0 * scale,
                                          pos[1] - (57.0 - 18.0) * scale),
                                color=(1, 1, 1, 0.3),
                                size=(0, 0),
                                h_align='center',
                                v_align='top',
                                scale=uiscale,
                                maxwidth=maxwidth,
                                text=self._input.get_button_name(
                                    self._settings[button]))
            ba.buttonwidget(edit=btn,
                            autoselect=True,
                            on_activate_call=ba.Call(AwaitKeyboardInputWindow,
                                                     button, txt,
                                                     self._settings))

        ba.pushcall(doit)

    def _cancel(self) -> None:
        from bastd.ui.settings.controls import ControlsSettingsWindow
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            ControlsSettingsWindow(transition='in_left').get_root_widget())

    def _save(self) -> None:
        from bastd.ui.settings.controls import ControlsSettingsWindow
        from ba.internal import (get_input_device_config,
                                 should_submit_debug_info, master_server_post)

        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.playsound(ba.getsound('gunCocking'))
        dst = get_input_device_config(self._input, default=False)
        dst2: Dict[str, Any] = dst[0][dst[1]]
        dst2.clear()

        # Store any values that aren't -1.
        for key, val in list(self._settings.items()):
            if val != -1:
                dst2[key] = val

        # If we're allowed to phone home, send this config so we can generate
        # more defaults in the future.
        if should_submit_debug_info():
            master_server_post(
                'controllerConfig', {
                    'ua': ba.app.user_agent_string,
                    'name': self._name,
                    'b': ba.app.build_number,
                    'config': dst2,
                    'v': 2
                })
        ba.app.config.apply_and_commit()
        ba.app.ui.set_main_menu_window(
            ControlsSettingsWindow(transition='in_left').get_root_widget())


class AwaitKeyboardInputWindow(ba.Window):
    """Window for capturing a keypress."""

    def __init__(self, button: str, ui: ba.Widget, settings: dict):

        self._capture_button = button
        self._capture_key_ui = ui
        self._settings = settings

        width = 400
        height = 150
        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition='in_right',
            scale=(2.0 if uiscale is ba.UIScale.SMALL else
                   1.5 if uiscale is ba.UIScale.MEDIUM else 1.0)))
        ba.textwidget(parent=self._root_widget,
                      position=(0, height - 60),
                      size=(width, 25),
                      text=ba.Lstr(resource='pressAnyKeyText'),
                      h_align='center',
                      v_align='top')

        self._counter = 5
        self._count_down_text = ba.textwidget(parent=self._root_widget,
                                              h_align='center',
                                              position=(0, height - 110),
                                              size=(width, 25),
                                              color=(1, 1, 1, 0.3),
                                              text=str(self._counter))
        self._decrement_timer: Optional[ba.Timer] = ba.Timer(
            1.0, self._decrement, repeat=True, timetype=ba.TimeType.REAL)
        _ba.capture_keyboard_input(ba.WeakCall(self._button_callback))

    def __del__(self) -> None:
        _ba.release_keyboard_input()

    def _die(self) -> None:
        # This strong-refs us; killing it allows us to die now.
        self._decrement_timer = None
        if self._root_widget:
            ba.containerwidget(edit=self._root_widget, transition='out_left')

    def _button_callback(self, event: Dict[str, Any]) -> None:
        self._settings[self._capture_button] = event['button']
        if event['type'] == 'BUTTONDOWN':
            bname = event['input_device'].get_button_name(event['button'])
            ba.textwidget(edit=self._capture_key_ui, text=bname)
            ba.playsound(ba.getsound('gunCocking'))
            self._die()

    def _decrement(self) -> None:
        self._counter -= 1
        if self._counter >= 1:
            ba.textwidget(edit=self._count_down_text, text=str(self._counter))
        else:
            self._die()
