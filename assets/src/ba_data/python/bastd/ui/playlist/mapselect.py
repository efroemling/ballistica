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
"""Provides UI for selecting maps in playlists."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Type, Any, Callable, Dict, List, Tuple, Optional


class PlaylistMapSelectWindow(ba.Window):
    """Window to select a map."""

    def __init__(self,
                 gameclass: Type[ba.GameActivity],
                 sessiontype: Type[ba.Session],
                 config: Dict[str, Any],
                 edit_info: Dict[str, Any],
                 completion_call: Callable[[Optional[Dict[str, Any]]], Any],
                 transition: str = 'in_right'):
        from ba.internal import get_filtered_map_name
        self._gameclass = gameclass
        self._sessiontype = sessiontype
        self._config = config
        self._completion_call = completion_call
        self._edit_info = edit_info
        self._maps: List[Tuple[str, ba.Texture]] = []
        try:
            self._previous_map = get_filtered_map_name(
                config['settings']['map'])
        except Exception:
            self._previous_map = ''

        uiscale = ba.app.ui.uiscale
        width = 715 if uiscale is ba.UIScale.SMALL else 615
        x_inset = 50 if uiscale is ba.UIScale.SMALL else 0
        height = (400 if uiscale is ba.UIScale.SMALL else
                  480 if uiscale is ba.UIScale.MEDIUM else 600)

        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height + top_extra),
            transition=transition,
            scale=(2.17 if uiscale is ba.UIScale.SMALL else
                   1.3 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -27) if uiscale is ba.UIScale.SMALL else (0, 0)))

        self._cancel_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(38 + x_inset, height - 67),
            size=(140, 50),
            scale=0.9,
            text_scale=1.0,
            autoselect=True,
            label=ba.Lstr(resource='cancelText'),
            on_activate_call=self._cancel)

        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, height - 46),
                      size=(0, 0),
                      maxwidth=260,
                      scale=1.1,
                      text=ba.Lstr(resource='mapSelectTitleText',
                                   subs=[('${GAME}',
                                          self._gameclass.get_display_string())
                                         ]),
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='center')
        v = height - 70
        self._scroll_width = width - (80 + 2 * x_inset)
        self._scroll_height = height - 140

        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            position=(40 + x_inset, v - self._scroll_height),
            size=(self._scroll_width, self._scroll_height))
        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._scrollwidget)
        ba.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._subcontainer: Optional[ba.Widget] = None
        self._refresh()

    def _refresh(self, select_get_more_maps_button: bool = False) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        from ba.internal import (get_unowned_maps, get_map_class,
                                 get_map_display_string)

        # Kill old.
        if self._subcontainer is not None:
            self._subcontainer.delete()

        model_opaque = ba.getmodel('level_select_button_opaque')
        model_transparent = ba.getmodel('level_select_button_transparent')

        self._maps = []
        map_list = self._gameclass.get_supported_maps(self._sessiontype)
        map_list_sorted = list(map_list)
        map_list_sorted.sort()
        unowned_maps = get_unowned_maps()

        for mapname in map_list_sorted:

            # Disallow ones we don't own.
            if mapname in unowned_maps:
                continue
            map_tex_name = (get_map_class(mapname).get_preview_texture_name())
            if map_tex_name is not None:
                try:
                    map_tex = ba.gettexture(map_tex_name)
                    self._maps.append((mapname, map_tex))
                except Exception:
                    print(f'Invalid map preview texture: "{map_tex_name}".')
            else:
                print('Error: no map preview texture for map:', mapname)

        count = len(self._maps)
        columns = 2
        rows = int(math.ceil(float(count) / columns))
        button_width = 220
        button_height = button_width * 0.5
        button_buffer_h = 16
        button_buffer_v = 19
        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 5 + rows * (button_height +
                                       2 * button_buffer_v) + 100
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False)
        index = 0
        mask_texture = ba.gettexture('mapPreviewMask')
        h_offs = 130 if len(self._maps) == 1 else 0
        for y in range(rows):
            for x in range(columns):
                pos = (x * (button_width + 2 * button_buffer_h) +
                       button_buffer_h + h_offs, self._sub_height - (y + 1) *
                       (button_height + 2 * button_buffer_v) + 12)
                btn = ba.buttonwidget(parent=self._subcontainer,
                                      button_type='square',
                                      size=(button_width, button_height),
                                      autoselect=True,
                                      texture=self._maps[index][1],
                                      mask_texture=mask_texture,
                                      model_opaque=model_opaque,
                                      model_transparent=model_transparent,
                                      label='',
                                      color=(1, 1, 1),
                                      on_activate_call=ba.Call(
                                          self._select_with_delay,
                                          self._maps[index][0]),
                                      position=pos)
                if x == 0:
                    ba.widget(edit=btn, left_widget=self._cancel_button)
                if y == 0:
                    ba.widget(edit=btn, up_widget=self._cancel_button)
                if x == columns - 1 and ba.app.ui.use_toolbars:
                    ba.widget(
                        edit=btn,
                        right_widget=_ba.get_special_widget('party_button'))

                ba.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)
                if self._maps[index][0] == self._previous_map:
                    ba.containerwidget(edit=self._subcontainer,
                                       selected_child=btn,
                                       visible_child=btn)
                name = get_map_display_string(self._maps[index][0])
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
        self._get_more_maps_button = btn = ba.buttonwidget(
            parent=self._subcontainer,
            size=(self._sub_width * 0.8, 60),
            position=(self._sub_width * 0.1, 30),
            label=ba.Lstr(resource='mapSelectGetMoreMapsText'),
            on_activate_call=self._on_store_press,
            color=(0.6, 0.53, 0.63),
            textcolor=(0.75, 0.7, 0.8),
            autoselect=True)
        ba.widget(edit=btn, show_buffer_top=30, show_buffer_bottom=30)
        if select_get_more_maps_button:
            ba.containerwidget(edit=self._subcontainer,
                               selected_child=btn,
                               visible_child=btn)

    def _on_store_press(self) -> None:
        from bastd.ui import account
        from bastd.ui.store import browser
        if _ba.get_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return
        browser.StoreBrowserWindow(modal=True,
                                   show_tab='maps',
                                   on_close_call=self._on_store_close,
                                   origin_widget=self._get_more_maps_button)

    def _on_store_close(self) -> None:
        self._refresh(select_get_more_maps_button=True)

    def _select(self, map_name: str) -> None:
        from bastd.ui.playlist.editgame import PlaylistEditGameWindow
        self._config['settings']['map'] = map_name
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            PlaylistEditGameWindow(
                self._gameclass,
                self._sessiontype,
                self._config,
                self._completion_call,
                default_selection='map',
                transition='in_left',
                edit_info=self._edit_info).get_root_widget())

    def _select_with_delay(self, map_name: str) -> None:
        _ba.lock_all_input()
        ba.timer(0.1, _ba.unlock_all_input, timetype=ba.TimeType.REAL)
        ba.timer(0.1,
                 ba.WeakCall(self._select, map_name),
                 timetype=ba.TimeType.REAL)

    def _cancel(self) -> None:
        from bastd.ui.playlist.editgame import PlaylistEditGameWindow
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            PlaylistEditGameWindow(
                self._gameclass,
                self._sessiontype,
                self._config,
                self._completion_call,
                default_selection='map',
                transition='in_left',
                edit_info=self._edit_info).get_root_widget())
