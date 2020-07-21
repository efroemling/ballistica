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
"""Provides a picker for characters."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import _ba
import ba
from bastd.ui import popup

if TYPE_CHECKING:
    from typing import Any, Tuple, Sequence


class CharacterPicker(popup.PopupWindow):
    """Popup window for selecting characters."""

    def __init__(self,
                 parent: ba.Widget,
                 position: Tuple[float, float] = (0.0, 0.0),
                 delegate: Any = None,
                 scale: float = None,
                 offset: Tuple[float, float] = (0.0, 0.0),
                 tint_color: Sequence[float] = (1.0, 1.0, 1.0),
                 tint2_color: Sequence[float] = (1.0, 1.0, 1.0),
                 selected_character: str = None):
        # pylint: disable=too-many-locals
        from bastd.actor import spazappearance
        del parent  # unused here
        uiscale = ba.app.ui.uiscale
        if scale is None:
            scale = (1.85 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)

        self._delegate = delegate
        self._transitioning_out = False

        # make a list of spaz icons
        self._spazzes = spazappearance.get_appearances()
        self._spazzes.sort()
        self._icon_textures = [
            ba.gettexture(ba.app.spaz_appearances[s].icon_texture)
            for s in self._spazzes
        ]
        self._icon_tint_textures = [
            ba.gettexture(ba.app.spaz_appearances[s].icon_mask_texture)
            for s in self._spazzes
        ]

        count = len(self._spazzes)

        columns = 3
        rows = int(math.ceil(float(count) / columns))

        button_width = 100
        button_height = 100
        button_buffer_h = 10
        button_buffer_v = 15

        self._width = (10 + columns * (button_width + 2 * button_buffer_h) *
                       (1.0 / 0.95) * (1.0 / 0.8))
        self._height = self._width * (0.8
                                      if uiscale is ba.UIScale.SMALL else 1.06)

        self._scroll_width = self._width * 0.8
        self._scroll_height = self._height * 0.8
        self._scroll_position = ((self._width - self._scroll_width) * 0.5,
                                 (self._height - self._scroll_height) * 0.5)

        # creates our _root_widget
        popup.PopupWindow.__init__(self,
                                   position=position,
                                   size=(self._width, self._height),
                                   scale=scale,
                                   bg_color=(0.5, 0.5, 0.5),
                                   offset=offset,
                                   focus_position=self._scroll_position,
                                   focus_size=(self._scroll_width,
                                               self._scroll_height))

        self._scrollwidget = ba.scrollwidget(parent=self.root_widget,
                                             size=(self._scroll_width,
                                                   self._scroll_height),
                                             color=(0.55, 0.55, 0.55),
                                             highlight=False,
                                             position=self._scroll_position)
        ba.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 5 + rows * (button_height +
                                       2 * button_buffer_v) + 100
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False)
        index = 0
        mask_texture = ba.gettexture('characterIconMask')
        for y in range(rows):
            for x in range(columns):
                pos = (x * (button_width + 2 * button_buffer_h) +
                       button_buffer_h, self._sub_height - (y + 1) *
                       (button_height + 2 * button_buffer_v) + 12)
                btn = ba.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    size=(button_width, button_height),
                    autoselect=True,
                    texture=self._icon_textures[index],
                    tint_texture=self._icon_tint_textures[index],
                    mask_texture=mask_texture,
                    label='',
                    color=(1, 1, 1),
                    tint_color=tint_color,
                    tint2_color=tint2_color,
                    on_activate_call=ba.Call(self._select_character,
                                             self._spazzes[index]),
                    position=pos)
                ba.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)
                if self._spazzes[index] == selected_character:
                    ba.containerwidget(edit=self._subcontainer,
                                       selected_child=btn,
                                       visible_child=btn)
                name = ba.Lstr(translate=('characterNames',
                                          self._spazzes[index]))
                ba.textwidget(parent=self._subcontainer,
                              text=name,
                              position=(pos[0] + button_width * 0.5,
                                        pos[1] - 12),
                              size=(0, 0),
                              scale=0.5,
                              maxwidth=button_width,
                              draw_controller=btn,
                              h_align='center',
                              v_align='center',
                              color=(0.8, 0.8, 0.8, 0.8))
                index += 1

                if index >= count:
                    break
            if index >= count:
                break
        self._get_more_characters_button = btn = ba.buttonwidget(
            parent=self._subcontainer,
            size=(self._sub_width * 0.8, 60),
            position=(self._sub_width * 0.1, 30),
            label=ba.Lstr(resource='editProfileWindow.getMoreCharactersText'),
            on_activate_call=self._on_store_press,
            color=(0.6, 0.6, 0.6),
            textcolor=(0.8, 0.8, 0.8),
            autoselect=True)
        ba.widget(edit=btn, show_buffer_top=30, show_buffer_bottom=30)

    def _on_store_press(self) -> None:
        from bastd.ui import account
        from bastd.ui.store import browser
        if _ba.get_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return
        self._transition_out()
        browser.StoreBrowserWindow(
            modal=True,
            show_tab='characters',
            origin_widget=self._get_more_characters_button)

    def _select_character(self, character: str) -> None:
        if self._delegate is not None:
            self._delegate.on_character_picker_pick(character)
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()
