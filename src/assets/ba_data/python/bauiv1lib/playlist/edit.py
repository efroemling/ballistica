# Released under the MIT License. See LICENSE for details.
#
"""Provides a window for editing individual game playlists."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast, override

import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from bauiv1lib.playlist.editcontroller import PlaylistEditController


class PlaylistEditWindow(bui.MainWindow):
    """Window for editing an individual game playlist."""

    def __init__(
        self,
        editcontroller: PlaylistEditController,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        prev_selection: str | None
        self._editcontroller = editcontroller
        self._r = 'editGameListWindow'
        prev_selection = self._editcontroller.get_edit_ui_selection()

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 870 if uiscale is bui.UIScale.SMALL else 670
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            500
            if uiscale is bui.UIScale.SMALL
            else 470 if uiscale is bui.UIScale.MEDIUM else 540
        )
        yoffs = -68 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    2.0
                    if uiscale is bui.UIScale.SMALL
                    else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(35 + x_inset, self._height - 60 + yoffs),
            scale=0.8,
            size=(175, 60),
            autoselect=True,
            label=bui.Lstr(resource='cancelText'),
            text_scale=1.2,
        )
        save_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - (195 + x_inset), self._height - 60 + yoffs),
            scale=0.8,
            size=(190, 60),
            autoselect=True,
            left_widget=cancel_button,
            label=bui.Lstr(resource='saveText'),
            text_scale=1.2,
        )

        bui.widget(
            edit=btn,
            right_widget=bui.get_special_widget('squad_button'),
        )

        bui.widget(
            edit=cancel_button,
            left_widget=cancel_button,
            right_widget=save_button,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(-10, self._height - 50 + yoffs),
            size=(self._width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            scale=1.05,
            h_align='center',
            v_align='center',
            maxwidth=270,
        )

        v = self._height - 115.0 + yoffs

        self._scroll_width = self._width - (205 + 2 * x_inset)

        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource=f'{self._r}.listNameText'),
            position=(196 + x_inset, v + 31),
            maxwidth=150,
            color=(0.8, 0.8, 0.8, 0.5),
            size=(0, 0),
            scale=0.75,
            h_align='right',
            v_align='center',
        )

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(210 + x_inset, v + 7),
            size=(self._scroll_width - 53, 43),
            text=self._editcontroller.getname(),
            h_align='left',
            v_align='center',
            max_chars=40,
            maxwidth=380,
            autoselect=True,
            color=(0.9, 0.9, 0.9, 1.0),
            description=bui.Lstr(resource=f'{self._r}.listNameText'),
            editable=True,
            padding=4,
            on_return_press_call=self._save_press_with_sound,
        )
        bui.widget(edit=cancel_button, down_widget=self._text_field)

        self._list_widgets: list[bui.Widget] = []

        h = 40 + x_inset
        v = self._height - 172.0 + yoffs

        b_color = (0.6, 0.53, 0.63)
        b_textcolor = (0.75, 0.7, 0.8)

        v -= 2.0
        v += 63

        scl = (
            1.03
            if uiscale is bui.UIScale.SMALL
            else 1.36 if uiscale is bui.UIScale.MEDIUM else 1.74
        )
        v -= 63.0 * scl

        add_game_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, 61.0 * scl),
            on_activate_call=self._add,
            on_select_call=bui.Call(self._set_ui_selection, 'add_button'),
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label=bui.Lstr(resource=f'{self._r}.addGameText'),
        )
        bui.widget(edit=add_game_button, up_widget=self._text_field)
        v -= 63.0 * scl

        self._edit_button = edit_game_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, 61.0 * scl),
            on_activate_call=self._edit,
            on_select_call=bui.Call(self._set_ui_selection, 'editButton'),
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.8,
            label=bui.Lstr(resource=f'{self._r}.editGameText'),
        )
        v -= 63.0 * scl

        remove_game_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(110, 61.0 * scl),
            text_scale=0.8,
            on_activate_call=self._remove,
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            label=bui.Lstr(resource=f'{self._r}.removeGameText'),
        )
        v -= 40
        h += 9
        bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(42, 35),
            on_activate_call=self._move_up,
            label=bui.charstr(bui.SpecialChar.UP_ARROW),
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            autoselect=True,
            repeat=True,
        )
        h += 52
        bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(42, 35),
            on_activate_call=self._move_down,
            autoselect=True,
            button_type='square',
            color=b_color,
            textcolor=b_textcolor,
            label=bui.charstr(bui.SpecialChar.DOWN_ARROW),
            repeat=True,
        )

        v = self._height - 100 + yoffs
        scroll_height = self._height - (
            250 if uiscale is bui.UIScale.SMALL else 155
        )
        scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(160 + x_inset, v - scroll_height),
            highlight=False,
            on_select_call=bui.Call(self._set_ui_selection, 'gameList'),
            size=(self._scroll_width, (scroll_height - 15)),
            border_opacity=0.4,
        )
        bui.widget(
            edit=scrollwidget,
            left_widget=add_game_button,
            right_widget=scrollwidget,
        )
        self._columnwidget = bui.columnwidget(
            parent=scrollwidget, border=2, margin=0
        )
        bui.widget(edit=self._columnwidget, up_widget=self._text_field)

        for button in [add_game_button, edit_game_button, remove_game_button]:
            bui.widget(
                edit=button, left_widget=button, right_widget=scrollwidget
            )

        self._refresh()

        bui.buttonwidget(edit=cancel_button, on_activate_call=self._cancel)
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=cancel_button,
            selected_child=scrollwidget,
        )

        bui.buttonwidget(edit=save_button, on_activate_call=self._save_press)
        bui.containerwidget(edit=self._root_widget, start_button=save_button)

        if prev_selection == 'add_button':
            bui.containerwidget(
                edit=self._root_widget, selected_child=add_game_button
            )
        elif prev_selection == 'editButton':
            bui.containerwidget(
                edit=self._root_widget, selected_child=edit_game_button
            )
        elif prev_selection == 'gameList':
            bui.containerwidget(
                edit=self._root_widget, selected_child=scrollwidget
            )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        editcontroller = self._editcontroller

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                editcontroller=editcontroller,
            )
        )

    def _set_ui_selection(self, selection: str) -> None:
        self._editcontroller.set_edit_ui_selection(selection)

    def _cancel(self) -> None:

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.getsound('powerdown01').play()
        self.main_window_back()

    def _add(self) -> None:
        # Store list name then tell the session to perform an add.
        self._editcontroller.setname(
            cast(str, bui.textwidget(query=self._text_field))
        )
        self._editcontroller.add_game_pressed(from_window=self)

    def _edit(self) -> None:
        # Store list name then tell the session to perform an add.
        self._editcontroller.setname(
            cast(str, bui.textwidget(query=self._text_field))
        )
        self._editcontroller.edit_game_pressed(from_window=self)

    def _save_press(self) -> None:

        # No-op if we're not in control.
        if not self.main_window_has_control():
            return

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        plus = bui.app.plus
        assert plus is not None

        new_name = cast(str, bui.textwidget(query=self._text_field))
        if (
            new_name != self._editcontroller.get_existing_playlist_name()
            and new_name
            in bui.app.config[
                self._editcontroller.get_config_name() + ' Playlists'
            ]
        ):
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantSaveAlreadyExistsText')
            )
            bui.getsound('error').play()
            return
        if not new_name:
            bui.getsound('error').play()
            return
        if not self._editcontroller.get_playlist():
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantSaveEmptyListText')
            )
            bui.getsound('error').play()
            return

        # We couldn't actually replace the default list anyway, but disallow
        # using its exact name to avoid confusion.
        if new_name == self._editcontroller.get_default_list_name().evaluate():
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantOverwriteDefaultText')
            )
            bui.getsound('error').play()
            return

        # If we had an old one, delete it.
        if self._editcontroller.get_existing_playlist_name() is not None:
            plus.add_v1_account_transaction(
                {
                    'type': 'REMOVE_PLAYLIST',
                    'playlistType': self._editcontroller.get_config_name(),
                    'playlistName': (
                        self._editcontroller.get_existing_playlist_name()
                    ),
                }
            )

        plus.add_v1_account_transaction(
            {
                'type': 'ADD_PLAYLIST',
                'playlistType': self._editcontroller.get_config_name(),
                'playlistName': new_name,
                'playlist': self._editcontroller.get_playlist(),
            }
        )
        plus.run_v1_account_transactions()

        bui.getsound('gunCocking').play()

        self.main_window_back()

    def _save_press_with_sound(self) -> None:
        bui.getsound('swish').play()
        self._save_press()

    def _select(self, index: int) -> None:
        self._editcontroller.set_selected_index(index)

    def _refresh(self) -> None:
        # Need to grab this here as rebuilding the list will
        # change it otherwise.
        old_selection_index = self._editcontroller.get_selected_index()

        while self._list_widgets:
            self._list_widgets.pop().delete()
        for index, pentry in enumerate(self._editcontroller.get_playlist()):
            try:
                cls = bui.getclass(pentry['type'], subclassof=bs.GameActivity)
                desc = cls.get_settings_display_string(pentry)
            except Exception:
                logging.exception('Error in playlist refresh.')
                desc = "(invalid: '" + pentry['type'] + "')"

            txtw = bui.textwidget(
                parent=self._columnwidget,
                size=(self._width - 80, 30),
                on_select_call=bui.Call(self._select, index),
                always_highlight=True,
                color=(0.8, 0.8, 0.8, 1.0),
                padding=0,
                maxwidth=self._scroll_width * 0.93,
                text=desc,
                on_activate_call=self._edit_button.activate,
                v_align='center',
                selectable=True,
            )
            bui.widget(edit=txtw, show_buffer_top=50, show_buffer_bottom=50)

            # Wanna be able to jump up to the text field from the top one.
            if index == 0:
                bui.widget(edit=txtw, up_widget=self._text_field)
            self._list_widgets.append(txtw)
            if old_selection_index == index:
                bui.columnwidget(
                    edit=self._columnwidget,
                    selected_child=txtw,
                    visible_child=txtw,
                )

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
        playlist[index] = playlist[index - 1]
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
        bui.getsound('shieldDown').play()
        self._refresh()
