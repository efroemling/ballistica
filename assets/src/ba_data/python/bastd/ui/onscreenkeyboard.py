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
"""Provides the built-in on screen keyboard UI."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import _ba
import ba
from ba import charstr
from ba import SpecialChar as SpCh

if TYPE_CHECKING:
    from typing import List, Tuple, Optional


class OnScreenKeyboardWindow(ba.Window):
    """Simple built-in on-screen keyboard."""

    def __init__(self, textwidget: ba.Widget, label: str, max_chars: int):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        self._target_text = textwidget
        self._width = 700
        self._height = 400
        uiscale = ba.app.ui.uiscale
        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0
        super().__init__(root_widget=ba.containerwidget(
            parent=_ba.get_special_widget('overlay_stack'),
            size=(self._width, self._height + top_extra),
            transition='in_scale',
            scale_origin_stack_offset=self._target_text.
            get_screen_space_center(),
            scale=(2.0 if uiscale is ba.UIScale.SMALL else
                   1.5 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, 0) if uiscale is ba.UIScale.SMALL else (
                0, 0) if uiscale is ba.UIScale.MEDIUM else (0, 0)))
        self._done_button = ba.buttonwidget(parent=self._root_widget,
                                            position=(self._width - 200, 44),
                                            size=(140, 60),
                                            autoselect=True,
                                            label=ba.Lstr(resource='doneText'),
                                            on_activate_call=self._done)
        ba.containerwidget(edit=self._root_widget,
                           on_cancel_call=self._cancel,
                           start_button=self._done_button)

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 41),
                      size=(0, 0),
                      scale=0.95,
                      text=label,
                      maxwidth=self._width - 140,
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='center')

        self._text_field = ba.textwidget(
            parent=self._root_widget,
            position=(70, self._height - 116),
            max_chars=max_chars,
            text=cast(str, ba.textwidget(query=self._target_text)),
            on_return_press_call=self._done,
            autoselect=True,
            size=(self._width - 140, 55),
            v_align='center',
            editable=True,
            maxwidth=self._width - 175,
            force_internal_editing=True,
            always_show_carat=True)

        self._shift_button = None
        self._double_press_shift = False
        self._num_mode_button = None
        self._emoji_button = None
        self._char_keys: List[ba.Widget] = []
        self._mode = 'normal'
        self._last_mode = 'normal'

        v = self._height - 180
        key_width = 46
        key_height = 46
        self._key_color_lit = (1.4, 1.2, 1.4)
        self._key_color = key_color = (0.69, 0.6, 0.74)
        self._key_color_dark = key_color_dark = (0.55, 0.55, 0.71)
        key_textcolor = (1, 1, 1)
        row_starts = (69, 95, 151)

        self._click_sound = ba.getsound('click01')

        # kill prev char keys
        for key in self._char_keys:
            key.delete()
        self._char_keys = []

        # dummy data just used for row/column lengths... we don't actually
        # set things until refresh
        chars: List[Tuple[str, ...]] = [
            ('q', 'u', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'),
            ('a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'),
            ('z', 'x', 'c', 'v', 'b', 'n', 'm')
        ]

        for row_num, row in enumerate(chars):
            h = row_starts[row_num]
            # shift key before row 3
            if row_num == 2:
                self._shift_button = ba.buttonwidget(
                    parent=self._root_widget,
                    position=(h - key_width * 2.0, v),
                    size=(key_width * 1.7, key_height),
                    autoselect=True,
                    textcolor=key_textcolor,
                    color=key_color_dark,
                    label=charstr(SpCh.SHIFT),
                    enable_sound=False,
                    extra_touch_border_scale=0.3,
                    button_type='square',
                )

            for _ in row:
                btn = ba.buttonwidget(
                    parent=self._root_widget,
                    position=(h, v),
                    size=(key_width, key_height),
                    autoselect=True,
                    enable_sound=False,
                    textcolor=key_textcolor,
                    color=key_color,
                    label='',
                    button_type='square',
                    extra_touch_border_scale=0.1,
                )
                self._char_keys.append(btn)
                h += key_width + 10

            # Add delete key at end of third row.
            if row_num == 2:
                ba.buttonwidget(parent=self._root_widget,
                                position=(h + 4, v),
                                size=(key_width * 1.8, key_height),
                                autoselect=True,
                                enable_sound=False,
                                repeat=True,
                                textcolor=key_textcolor,
                                color=key_color_dark,
                                label=charstr(SpCh.DELETE),
                                button_type='square',
                                on_activate_call=self._del)
            v -= (key_height + 9)
            # Do space bar and stuff.
            if row_num == 2:
                if self._num_mode_button is None:
                    self._num_mode_button = ba.buttonwidget(
                        parent=self._root_widget,
                        position=(112, v - 8),
                        size=(key_width * 2, key_height + 5),
                        enable_sound=False,
                        button_type='square',
                        extra_touch_border_scale=0.3,
                        autoselect=True,
                        textcolor=key_textcolor,
                        color=key_color_dark,
                        label='',
                    )
                if self._emoji_button is None:
                    self._emoji_button = ba.buttonwidget(
                        parent=self._root_widget,
                        position=(56, v - 8),
                        size=(key_width, key_height + 5),
                        autoselect=True,
                        enable_sound=False,
                        textcolor=key_textcolor,
                        color=key_color_dark,
                        label=charstr(SpCh.LOGO_FLAT),
                        extra_touch_border_scale=0.3,
                        button_type='square',
                    )
                btn1 = self._num_mode_button
                btn2 = ba.buttonwidget(parent=self._root_widget,
                                       position=(210, v - 12),
                                       size=(key_width * 6.1, key_height + 15),
                                       extra_touch_border_scale=0.3,
                                       enable_sound=False,
                                       autoselect=True,
                                       textcolor=key_textcolor,
                                       color=key_color_dark,
                                       label=ba.Lstr(resource='spaceKeyText'),
                                       on_activate_call=ba.Call(
                                           self._type_char, ' '))
                btn3 = self._emoji_button
                ba.widget(edit=btn1, right_widget=btn2, left_widget=btn3)
                ba.widget(edit=btn2,
                          left_widget=btn1,
                          right_widget=self._done_button)
                ba.widget(edit=btn3, left_widget=btn1)
                ba.widget(edit=self._done_button, left_widget=btn2)

        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._char_keys[14])

        self._refresh()

    def _refresh(self) -> None:
        chars: Optional[List[str]] = None
        if self._mode in ['normal', 'caps']:
            chars = [
                'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'a', 's',
                'd', 'f', 'g', 'h', 'j', 'k', 'l', 'z', 'x', 'c', 'v', 'b',
                'n', 'm'
            ]
            if self._mode == 'caps':
                chars = [c.upper() for c in chars]
            ba.buttonwidget(edit=self._shift_button,
                            color=self._key_color_lit
                            if self._mode == 'caps' else self._key_color_dark,
                            label=charstr(SpCh.SHIFT),
                            on_activate_call=self._shift)
            ba.buttonwidget(edit=self._num_mode_button,
                            label='123#&*',
                            on_activate_call=self._num_mode)
            ba.buttonwidget(edit=self._emoji_button,
                            color=self._key_color_dark,
                            label=charstr(SpCh.LOGO_FLAT),
                            on_activate_call=self._emoji_mode)
        elif self._mode == 'num':
            chars = [
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '/',
                ':', ';', '(', ')', '$', '&', '@', '"', '.', ',', '?', '!',
                '\'', '_'
            ]
            ba.buttonwidget(edit=self._shift_button,
                            color=self._key_color_dark,
                            label='',
                            on_activate_call=self._null_press)
            ba.buttonwidget(edit=self._num_mode_button,
                            label='abc',
                            on_activate_call=self._abc_mode)
            ba.buttonwidget(edit=self._emoji_button,
                            color=self._key_color_dark,
                            label=charstr(SpCh.LOGO_FLAT),
                            on_activate_call=self._emoji_mode)

        elif self._mode in ['emoji', 'emoji2']:
            chars = [
                '💣', '💥', '🙂', '😄', '😆', '😅', '😂', '☺', '😀', '😉', '😇', '😎',
                '😰', '😠', '😈', '😨', '😛', '😜', '😝', '😐', '😑', '😵', '😬', '😡',
                '😌', '😍'
            ]
            if self._mode == 'emoji2':
                chars = [
                    '😔', '😥', '😭', '😖', '😓', '😉', '😴', '😷', '👋', '💯', '🙏', '💪',
                    '👀', '💬', '💀', '☠', '💩', '👻', '👽', '👾', '❤', '💛', '💚', '💙',
                    '💜', '💔'
                ]
            ba.buttonwidget(edit=self._shift_button,
                            color=self._key_color_lit if self._mode == 'emoji2'
                            else self._key_color_dark,
                            label=charstr(SpCh.SHIFT),
                            on_activate_call=self._emoji_mode_2)
            ba.buttonwidget(edit=self._emoji_button,
                            color=self._key_color_lit,
                            label=charstr(SpCh.LOGO_FLAT),
                            on_activate_call=self._emoji_mode)

        for i, btn in enumerate(self._char_keys):
            assert chars is not None
            ba.buttonwidget(edit=btn,
                            label=chars[i],
                            on_activate_call=ba.Call(self._type_char,
                                                     chars[i]))

    def _null_press(self) -> None:
        ba.playsound(self._click_sound)

    def _abc_mode(self) -> None:
        ba.playsound(self._click_sound)
        self._mode = 'normal'
        self._refresh()

    def _num_mode(self) -> None:
        ba.playsound(self._click_sound)
        self._mode = 'num'
        self._refresh()

    def _emoji_mode(self) -> None:
        ba.playsound(self._click_sound)
        if self._mode in ['normal', 'caps', 'num']:
            self._last_mode = self._mode
            self._mode = 'emoji'
        elif self._mode == 'emoji' or self._mode == 'emoji2':
            self._mode = self._last_mode
        self._refresh()

    def _emoji_mode_2(self) -> None:
        ba.playsound(self._click_sound)
        if self._mode == 'emoji':
            self._mode = 'emoji2'
        elif self._mode == 'emoji2':
            self._mode = 'emoji'
        self._refresh()

    def _shift(self) -> None:
        ba.playsound(self._click_sound)
        if self._mode == 'normal':
            self._mode = 'caps'
            self._double_press_shift = False
        elif self._mode == 'caps':
            if not self._double_press_shift:
                self._double_press_shift = True
            else:
                self._mode = 'normal'
        self._refresh()

    def _del(self) -> None:
        ba.playsound(self._click_sound)
        txt = cast(str, ba.textwidget(query=self._text_field))
        # pylint: disable=unsubscriptable-object
        txt = txt[:-1]
        ba.textwidget(edit=self._text_field, text=txt)

    def _type_char(self, char: str) -> None:
        ba.playsound(self._click_sound)
        # operate in unicode so we don't do anything funky like chop utf-8
        # chars in half
        txt = cast(str, ba.textwidget(query=self._text_field))
        txt += char
        ba.textwidget(edit=self._text_field, text=txt)
        # if we were caps,
        # go back only if not Shift is pressed twice
        if self._mode == 'caps' and not self._double_press_shift:
            self._mode = 'normal'
        self._refresh()

    def _cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        ba.containerwidget(edit=self._root_widget, transition='out_scale')

    def _done(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_scale')
        if self._target_text:
            ba.textwidget(edit=self._target_text,
                          text=cast(str,
                                    ba.textwidget(query=self._text_field)))
