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
"""Provides UI for test settings."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Dict, List


class TestingWindow(ba.Window):
    """Window for conveniently testing various settings."""

    def __init__(self,
                 title: ba.Lstr,
                 entries: List[Dict[str, Any]],
                 transition: str = 'in_right'):
        uiscale = ba.app.ui.uiscale
        self._width = 600
        self._height = 324 if uiscale is ba.UIScale.SMALL else 400
        self._entries = copy.deepcopy(entries)
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition=transition,
            scale=(2.5 if uiscale is ba.UIScale.SMALL else
                   1.2 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -28) if uiscale is ba.UIScale.SMALL else (0, 0)))
        self._back_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(65, self._height - 59),
            size=(130, 60),
            scale=0.8,
            text_scale=1.2,
            label=ba.Lstr(resource='backText'),
            button_type='back',
            on_activate_call=self._do_back)
        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 35),
                      size=(0, 0),
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='center',
                      maxwidth=245,
                      text=title)

        ba.buttonwidget(edit=self._back_button,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 75),
            size=(0, 0),
            color=ba.app.ui.infotextcolor,
            h_align='center',
            v_align='center',
            maxwidth=self._width * 0.75,
            text=ba.Lstr(resource='settingsWindowAdvanced.forTestingText'))
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        self._scroll_width = self._width - 130
        self._scroll_height = self._height - 140
        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            size=(self._scroll_width, self._scroll_height),
            highlight=False,
            position=((self._width - self._scroll_width) * 0.5, 40))
        ba.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._spacing = 50

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 50 + len(self._entries) * self._spacing + 60
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False)

        h = 230
        v = self._sub_height - 48

        for i, entry in enumerate(self._entries):

            entry_name = entry['name']

            # If we haven't yet, record the default value for this name so
            # we can reset if we want..
            if entry_name not in ba.app.value_test_defaults:
                ba.app.value_test_defaults[entry_name] = (
                    _ba.value_test(entry_name))

            ba.textwidget(parent=self._subcontainer,
                          position=(h, v),
                          size=(0, 0),
                          h_align='right',
                          v_align='center',
                          maxwidth=200,
                          text=entry['label'])
            btn = ba.buttonwidget(parent=self._subcontainer,
                                  position=(h + 20, v - 19),
                                  size=(40, 40),
                                  autoselect=True,
                                  repeat=True,
                                  left_widget=self._back_button,
                                  button_type='square',
                                  label='-',
                                  on_activate_call=ba.Call(
                                      self._on_minus_press, entry['name']))
            if i == 0:
                ba.widget(edit=btn, up_widget=self._back_button)
            entry['widget'] = ba.textwidget(parent=self._subcontainer,
                                            position=(h + 100, v),
                                            size=(0, 0),
                                            h_align='center',
                                            v_align='center',
                                            maxwidth=60,
                                            text='%.4g' %
                                            _ba.value_test(entry_name))
            btn = ba.buttonwidget(parent=self._subcontainer,
                                  position=(h + 140, v - 19),
                                  size=(40, 40),
                                  autoselect=True,
                                  repeat=True,
                                  button_type='square',
                                  label='+',
                                  on_activate_call=ba.Call(
                                      self._on_plus_press, entry['name']))
            if i == 0:
                ba.widget(edit=btn, up_widget=self._back_button)
            v -= self._spacing
        v -= 35
        ba.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            size=(200, 50),
            position=(self._sub_width * 0.5 - 100, v),
            label=ba.Lstr(resource='settingsWindowAdvanced.resetText'),
            right_widget=btn,
            on_activate_call=self._on_reset_press)

    def _get_entry(self, name: str) -> Dict[str, Any]:
        for entry in self._entries:
            if entry['name'] == name:
                return entry
        raise ba.NotFoundError(f'Entry not found: {name}')

    def _on_reset_press(self) -> None:
        for entry in self._entries:
            _ba.value_test(entry['name'],
                           absolute=ba.app.value_test_defaults[entry['name']])
            ba.textwidget(edit=entry['widget'],
                          text='%.4g' % _ba.value_test(entry['name']))

    def _on_minus_press(self, entry_name: str) -> None:
        entry = self._get_entry(entry_name)
        _ba.value_test(entry['name'], change=-entry['increment'])
        ba.textwidget(edit=entry['widget'],
                      text='%.4g' % _ba.value_test(entry['name']))

    def _on_plus_press(self, entry_name: str) -> None:
        entry = self._get_entry(entry_name)
        _ba.value_test(entry['name'], change=entry['increment'])
        ba.textwidget(edit=entry['widget'],
                      text='%.4g' % _ba.value_test(entry['name']))

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import
        import bastd.ui.settings.advanced
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            bastd.ui.settings.advanced.AdvancedSettingsWindow(
                transition='in_left').get_root_widget())
