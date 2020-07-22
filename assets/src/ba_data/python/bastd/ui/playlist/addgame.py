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
"""Provides a window for selecting a game type to add to a playlist."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Type, Optional
    from bastd.ui.playlist.editcontroller import PlaylistEditController


class PlaylistAddGameWindow(ba.Window):
    """Window for selecting a game type to add to a playlist."""

    def __init__(self,
                 editcontroller: PlaylistEditController,
                 transition: str = 'in_right'):
        self._editcontroller = editcontroller
        self._r = 'addGameWindow'
        uiscale = ba.app.ui.uiscale
        self._width = 750 if uiscale is ba.UIScale.SMALL else 650
        x_inset = 50 if uiscale is ba.UIScale.SMALL else 0
        self._height = (346 if uiscale is ba.UIScale.SMALL else
                        380 if uiscale is ba.UIScale.MEDIUM else 440)
        top_extra = 30 if uiscale is ba.UIScale.SMALL else 20
        self._scroll_width = 210

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            scale=(2.17 if uiscale is ba.UIScale.SMALL else
                   1.5 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, 1) if uiscale is ba.UIScale.SMALL else (0, 0)))

        self._back_button = ba.buttonwidget(parent=self._root_widget,
                                            position=(58 + x_inset,
                                                      self._height - 53),
                                            size=(165, 70),
                                            scale=0.75,
                                            text_scale=1.2,
                                            label=ba.Lstr(resource='backText'),
                                            autoselect=True,
                                            button_type='back',
                                            on_activate_call=self._back)
        self._select_button = select_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(self._width - (172 + x_inset), self._height - 50),
            autoselect=True,
            size=(160, 60),
            scale=0.75,
            text_scale=1.2,
            label=ba.Lstr(resource='selectText'),
            on_activate_call=self._add)

        if ba.app.ui.use_toolbars:
            ba.widget(edit=select_button,
                      right_widget=_ba.get_special_widget('party_button'))

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 28),
                      size=(0, 0),
                      scale=1.0,
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      h_align='center',
                      color=ba.app.ui.title_color,
                      maxwidth=250,
                      v_align='center')
        v = self._height - 64

        self._selected_title_text = ba.textwidget(
            parent=self._root_widget,
            position=(x_inset + self._scroll_width + 50 + 30, v - 15),
            size=(0, 0),
            scale=1.0,
            color=(0.7, 1.0, 0.7, 1.0),
            maxwidth=self._width - self._scroll_width - 150 - x_inset * 2,
            h_align='left',
            v_align='center')
        v -= 30

        self._selected_description_text = ba.textwidget(
            parent=self._root_widget,
            position=(x_inset + self._scroll_width + 50 + 30, v),
            size=(0, 0),
            scale=0.7,
            color=(0.5, 0.8, 0.5, 1.0),
            maxwidth=self._width - self._scroll_width - 150 - x_inset * 2,
            h_align='left')

        scroll_height = self._height - 100

        v = self._height - 60

        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             position=(x_inset + 61,
                                                       v - scroll_height),
                                             size=(self._scroll_width,
                                                   scroll_height),
                                             highlight=False)
        ba.widget(edit=self._scrollwidget,
                  up_widget=self._back_button,
                  left_widget=self._back_button,
                  right_widget=select_button)
        self._column: Optional[ba.Widget] = None

        v -= 35
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._back_button,
                           start_button=select_button)
        self._selected_game_type: Optional[Type[ba.GameActivity]] = None

        ba.containerwidget(edit=self._root_widget,
                           selected_child=self._scrollwidget)

        self._refresh()

    def _refresh(self, select_get_more_games_button: bool = False) -> None:
        from ba.internal import get_game_types

        if self._column is not None:
            self._column.delete()

        self._column = ba.columnwidget(parent=self._scrollwidget,
                                       border=2,
                                       margin=0)

        gametypes = [
            gt for gt in get_game_types() if gt.supports_session_type(
                self._editcontroller.get_session_type())
        ]

        # Sort in the current language.
        gametypes.sort(key=lambda g: g.get_display_string().evaluate())

        for i, gametype in enumerate(gametypes):

            def _doit() -> None:
                if self._select_button:
                    ba.timer(0.1,
                             self._select_button.activate,
                             timetype=ba.TimeType.REAL)

            txt = ba.textwidget(parent=self._column,
                                position=(0, 0),
                                size=(self._width - 88, 24),
                                text=gametype.get_display_string(),
                                h_align='left',
                                v_align='center',
                                color=(0.8, 0.8, 0.8, 1.0),
                                maxwidth=self._scroll_width * 0.8,
                                on_select_call=ba.Call(
                                    self._set_selected_game_type, gametype),
                                always_highlight=True,
                                selectable=True,
                                on_activate_call=_doit)
            if i == 0:
                ba.widget(edit=txt, up_widget=self._back_button)

        self._get_more_games_button = ba.buttonwidget(
            parent=self._column,
            autoselect=True,
            label=ba.Lstr(resource=self._r + '.getMoreGamesText'),
            color=(0.54, 0.52, 0.67),
            textcolor=(0.7, 0.65, 0.7),
            on_activate_call=self._on_get_more_games_press,
            size=(178, 50))
        if select_get_more_games_button:
            ba.containerwidget(edit=self._column,
                               selected_child=self._get_more_games_button,
                               visible_child=self._get_more_games_button)

    def _on_get_more_games_press(self) -> None:
        from bastd.ui import account
        from bastd.ui.store import browser
        if _ba.get_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return
        browser.StoreBrowserWindow(modal=True,
                                   show_tab='minigames',
                                   on_close_call=self._on_store_close,
                                   origin_widget=self._get_more_games_button)

    def _on_store_close(self) -> None:
        self._refresh(select_get_more_games_button=True)

    def _add(self) -> None:
        _ba.lock_all_input()  # Make sure no more commands happen.
        ba.timer(0.1, _ba.unlock_all_input, timetype=ba.TimeType.REAL)
        assert self._selected_game_type is not None
        self._editcontroller.add_game_type_selected(self._selected_game_type)

    def _set_selected_game_type(self, gametype: Type[ba.GameActivity]) -> None:
        self._selected_game_type = gametype
        ba.textwidget(edit=self._selected_title_text,
                      text=gametype.get_display_string())
        ba.textwidget(edit=self._selected_description_text,
                      text=gametype.get_description_display_string(
                          self._editcontroller.get_session_type()))

    def _back(self) -> None:
        self._editcontroller.add_game_cancelled()
