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
"""Provides a window for editing individual game playlists."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import ba
import _ba

if TYPE_CHECKING:
    from typing import Optional, List
    from bastd.ui.playlist.editcontroller import PlaylistEditController


class PlaylistEditWindow(ba.Window):
    """Window for editing an individual game playlist."""

    def __init__(self,
                 editcontroller: PlaylistEditController,
                 transition: str = 'in_right'):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        prev_selection: Optional[str]
        self._editcontroller = editcontroller
        self._r = 'editGameListWindow'
        prev_selection = self._editcontroller.get_edit_ui_selection()

        uiscale = ba.app.ui.uiscale
        self._width = 770 if uiscale is ba.UIScale.SMALL else 670
        x_inset = 50 if uiscale is ba.UIScale.SMALL else 0
        self._height = (400 if uiscale is ba.UIScale.SMALL else
                        470 if uiscale is ba.UIScale.MEDIUM else 540)

        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            scale=(2.0 if uiscale is ba.UIScale.SMALL else
                   1.3 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -16) if uiscale is ba.UIScale.SMALL else (0, 0)))
        cancel_button = ba.buttonwidget(parent=self._root_widget,
                                        position=(35 + x_inset,
                                                  self._height - 60),
                                        scale=0.8,
                                        size=(175, 60),
                                        autoselect=True,
                                        label=ba.Lstr(resource='cancelText'),
                                        text_scale=1.2)
        save_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(self._width - (195 + x_inset), self._height - 60),
            scale=0.8,
            size=(190, 60),
            autoselect=True,
            left_widget=cancel_button,
            label=ba.Lstr(resource='saveText'),
            text_scale=1.2)

        if ba.app.ui.use_toolbars:
            ba.widget(edit=btn,
                      right_widget=_ba.get_special_widget('party_button'))

        ba.widget(edit=cancel_button,
                  left_widget=cancel_button,
                  right_widget=save_button)

        ba.textwidget(parent=self._root_widget,
                      position=(-10, self._height - 50),
                      size=(self._width, 25),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      color=ba.app.ui.title_color,
                      scale=1.05,
                      h_align='center',
                      v_align='center',
                      maxwidth=270)

        v = self._height - 115.0

        self._scroll_width = self._width - (205 + 2 * x_inset)

        ba.textwidget(parent=self._root_widget,
                      text=ba.Lstr(resource=self._r + '.listNameText'),
                      position=(196 + x_inset, v + 31),
                      maxwidth=150,
                      color=(0.8, 0.8, 0.8, 0.5),
                      size=(0, 0),
                      scale=0.75,
                      h_align='right',
                      v_align='center')

        self._text_field = ba.textwidget(
            parent=self._root_widget,
            position=(210 + x_inset, v + 7),
            size=(self._scroll_width - 53, 43),
            text=self._editcontroller.getname(),
            h_align='left',
            v_align='center',
            max_chars=40,
            autoselect=True,
            color=(0.9, 0.9, 0.9, 1.0),
            description=ba.Lstr(resource=self._r + '.listNameText'),
            editable=True,
            padding=4,
            on_return_press_call=self._save_press_with_sound)
        ba.widget(edit=cancel_button, down_widget=self._text_field)

        self._list_widgets: List[ba.Widget] = []

        h = 40 + x_inset
        v = self._height - 172.0

        b_color = (0.6, 0.53, 0.63)
        b_textcolor = (0.75, 0.7, 0.8)

        v -= 2.0
        v += 63

        scl = (1.03 if uiscale is ba.UIScale.SMALL else
               1.36 if uiscale is ba.UIScale.MEDIUM else 1.74)
        v -= 63.0 * scl

        add_game_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, 61.0 * scl),
            on_activate_call=self._add,
            on_select_call=ba.Call(self._set_ui_selection, 'add_button'),
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label=ba.Lstr(resource=self._r + '.addGameText'))
        ba.widget(edit=add_game_button, up_widget=self._text_field)
        v -= 63.0 * scl

        self._edit_button = edit_game_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, 61.0 * scl),
            on_activate_call=self._edit,
            on_select_call=ba.Call(self._set_ui_selection, 'editButton'),
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label=ba.Lstr(resource=self._r + '.editGameText'))
        v -= 63.0 * scl

        remove_game_button = ba.buttonwidget(parent=self._root_widget,
                                             position=(h, v),
                                             size=(110, 61.0 * scl),
                                             text_scale=0.8,
                                             on_activate_call=self._remove,
                                             autoselect=True,
                                             button_type='square',
                                             color=b_color,
                                             textcolor=b_textcolor,
                                             label=ba.Lstr(resource=self._r +
                                                           '.removeGameText'))
        v -= 40
        h += 9
        ba.buttonwidget(parent=self._root_widget,
                        position=(h, v),
                        size=(42, 35),
                        on_activate_call=self._move_up,
                        label=ba.charstr(ba.SpecialChar.UP_ARROW),
                        button_type='square',
                        color=b_color,
                        textcolor=b_textcolor,
                        autoselect=True,
                        repeat=True)
        h += 52
        ba.buttonwidget(parent=self._root_widget,
                        position=(h, v),
                        size=(42, 35),
                        on_activate_call=self._move_down,
                        autoselect=True,
                        button_type='square',
                        color=b_color,
                        textcolor=b_textcolor,
                        label=ba.charstr(ba.SpecialChar.DOWN_ARROW),
                        repeat=True)

        v = self._height - 100
        scroll_height = self._height - 155
        scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            position=(160 + x_inset, v - scroll_height),
            highlight=False,
            on_select_call=ba.Call(self._set_ui_selection, 'gameList'),
            size=(self._scroll_width, (scroll_height - 15)))
        ba.widget(edit=scrollwidget,
                  left_widget=add_game_button,
                  right_widget=scrollwidget)
        self._columnwidget = ba.columnwidget(parent=scrollwidget,
                                             border=2,
                                             margin=0)
        ba.widget(edit=self._columnwidget, up_widget=self._text_field)

        for button in [add_game_button, edit_game_button, remove_game_button]:
            ba.widget(edit=button,
                      left_widget=button,
                      right_widget=scrollwidget)

        self._refresh()

        ba.buttonwidget(edit=cancel_button, on_activate_call=self._cancel)
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=cancel_button,
                           selected_child=scrollwidget)

        ba.buttonwidget(edit=save_button, on_activate_call=self._save_press)
        ba.containerwidget(edit=self._root_widget, start_button=save_button)

        if prev_selection == 'add_button':
            ba.containerwidget(edit=self._root_widget,
                               selected_child=add_game_button)
        elif prev_selection == 'editButton':
            ba.containerwidget(edit=self._root_widget,
                               selected_child=edit_game_button)
        elif prev_selection == 'gameList':
            ba.containerwidget(edit=self._root_widget,
                               selected_child=scrollwidget)

    def _set_ui_selection(self, selection: str) -> None:
        self._editcontroller.set_edit_ui_selection(selection)

    def _cancel(self) -> None:
        from bastd.ui.playlist.customizebrowser import (
            PlaylistCustomizeBrowserWindow)
        ba.playsound(ba.getsound('powerdown01'))
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            PlaylistCustomizeBrowserWindow(
                transition='in_left',
                sessiontype=self._editcontroller.get_session_type(),
                select_playlist=self._editcontroller.
                get_existing_playlist_name()).get_root_widget())

    def _add(self) -> None:
        # Store list name then tell the session to perform an add.
        self._editcontroller.setname(
            cast(str, ba.textwidget(query=self._text_field)))
        self._editcontroller.add_game_pressed()

    def _edit(self) -> None:
        # Store list name then tell the session to perform an add.
        self._editcontroller.setname(
            cast(str, ba.textwidget(query=self._text_field)))
        self._editcontroller.edit_game_pressed()

    def _save_press(self) -> None:
        from bastd.ui.playlist.customizebrowser import (
            PlaylistCustomizeBrowserWindow)
        new_name = cast(str, ba.textwidget(query=self._text_field))
        if (new_name != self._editcontroller.get_existing_playlist_name()
                and new_name
                in ba.app.config[self._editcontroller.get_config_name() +
                                 ' Playlists']):
            ba.screenmessage(
                ba.Lstr(resource=self._r + '.cantSaveAlreadyExistsText'))
            ba.playsound(ba.getsound('error'))
            return
        if not new_name:
            ba.playsound(ba.getsound('error'))
            return
        if not self._editcontroller.get_playlist():
            ba.screenmessage(
                ba.Lstr(resource=self._r + '.cantSaveEmptyListText'))
            ba.playsound(ba.getsound('error'))
            return

        # We couldn't actually replace the default list anyway, but disallow
        # using its exact name to avoid confusion.
        if new_name == self._editcontroller.get_default_list_name().evaluate():
            ba.screenmessage(
                ba.Lstr(resource=self._r + '.cantOverwriteDefaultText'))
            ba.playsound(ba.getsound('error'))
            return

        # If we had an old one, delete it.
        if self._editcontroller.get_existing_playlist_name() is not None:
            _ba.add_transaction({
                'type':
                    'REMOVE_PLAYLIST',
                'playlistType':
                    self._editcontroller.get_config_name(),
                'playlistName':
                    self._editcontroller.get_existing_playlist_name()
            })

        _ba.add_transaction({
            'type': 'ADD_PLAYLIST',
            'playlistType': self._editcontroller.get_config_name(),
            'playlistName': new_name,
            'playlist': self._editcontroller.get_playlist()
        })
        _ba.run_transactions()

        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.playsound(ba.getsound('gunCocking'))
        ba.app.ui.set_main_menu_window(
            PlaylistCustomizeBrowserWindow(
                transition='in_left',
                sessiontype=self._editcontroller.get_session_type(),
                select_playlist=new_name).get_root_widget())

    def _save_press_with_sound(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._save_press()

    def _select(self, index: int) -> None:
        self._editcontroller.set_selected_index(index)

    def _refresh(self) -> None:
        from ba.internal import getclass

        # Need to grab this here as rebuilding the list will
        # change it otherwise.
        old_selection_index = self._editcontroller.get_selected_index()

        while self._list_widgets:
            self._list_widgets.pop().delete()
        for index, pentry in enumerate(self._editcontroller.get_playlist()):

            try:
                cls = getclass(pentry['type'], subclassof=ba.GameActivity)
                desc = cls.get_settings_display_string(pentry)
            except Exception:
                ba.print_exception()
                desc = "(invalid: '" + pentry['type'] + "')"

            txtw = ba.textwidget(parent=self._columnwidget,
                                 size=(self._width - 80, 30),
                                 on_select_call=ba.Call(self._select, index),
                                 always_highlight=True,
                                 color=(0.8, 0.8, 0.8, 1.0),
                                 padding=0,
                                 maxwidth=self._scroll_width * 0.93,
                                 text=desc,
                                 on_activate_call=self._edit_button.activate,
                                 v_align='center',
                                 selectable=True)
            ba.widget(edit=txtw, show_buffer_top=50, show_buffer_bottom=50)

            # Wanna be able to jump up to the text field from the top one.
            if index == 0:
                ba.widget(edit=txtw, up_widget=self._text_field)
            self._list_widgets.append(txtw)
            if old_selection_index == index:
                ba.columnwidget(edit=self._columnwidget,
                                selected_child=txtw,
                                visible_child=txtw)

    def _move_down(self) -> None:
        playlist = self._editcontroller.get_playlist()
        index = self._editcontroller.get_selected_index()
        if index >= len(playlist) - 1:
            return
        tmp = playlist[index]
        playlist[index] = playlist[index + 1]
        playlist[index + 1] = tmp
        index += 1
        self._editcontroller.set_playlist(playlist)
        self._editcontroller.set_selected_index(index)
        self._refresh()

    def _move_up(self) -> None:
        playlist = self._editcontroller.get_playlist()
        index = self._editcontroller.get_selected_index()
        if index < 1:
            return
        tmp = playlist[index]
        playlist[index] = (playlist[index - 1])
        playlist[index - 1] = tmp
        index -= 1
        self._editcontroller.set_playlist(playlist)
        self._editcontroller.set_selected_index(index)
        self._refresh()

    def _remove(self) -> None:
        playlist = self._editcontroller.get_playlist()
        index = self._editcontroller.get_selected_index()
        if not playlist:
            return
        del playlist[index]
        if index >= len(playlist):
            index = len(playlist) - 1
        self._editcontroller.set_playlist(playlist)
        self._editcontroller.set_selected_index(index)
        ba.playsound(ba.getsound('shieldDown'))
        self._refresh()
