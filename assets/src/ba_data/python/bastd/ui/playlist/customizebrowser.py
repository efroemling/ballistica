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
"""Provides UI for viewing/creating/editing playlists."""

from __future__ import annotations

import copy
import time
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Type, Optional, Tuple, List, Dict


class PlaylistCustomizeBrowserWindow(ba.Window):
    """Window for viewing a playlist."""

    def __init__(self,
                 sessiontype: Type[ba.Session],
                 transition: str = 'in_right',
                 select_playlist: str = None,
                 origin_widget: ba.Widget = None):
        # Yes this needs tidying.
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        from bastd.ui import playlist
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._sessiontype = sessiontype
        self._pvars = playlist.PlaylistTypeVars(sessiontype)
        self._max_playlists = 30
        self._r = 'gameListWindow'
        uiscale = ba.app.ui.uiscale
        self._width = 750.0 if uiscale is ba.UIScale.SMALL else 650.0
        x_inset = 50.0 if uiscale is ba.UIScale.SMALL else 0.0
        self._height = (380.0 if uiscale is ba.UIScale.SMALL else
                        420.0 if uiscale is ba.UIScale.MEDIUM else 500.0)
        top_extra = 20.0 if uiscale is ba.UIScale.SMALL else 0.0

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            scale_origin_stack_offset=scale_origin,
            scale=(2.05 if uiscale is ba.UIScale.SMALL else
                   1.5 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -10) if uiscale is ba.UIScale.SMALL else (0, 0)))

        self._back_button = back_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(43 + x_inset, self._height - 60),
            size=(160, 68),
            scale=0.77,
            autoselect=True,
            text_scale=1.3,
            label=ba.Lstr(resource='backText'),
            button_type='back')

        ba.textwidget(parent=self._root_widget,
                      position=(0, self._height - 47),
                      size=(self._width, 25),
                      text=ba.Lstr(resource=self._r + '.titleText',
                                   subs=[('${TYPE}',
                                          self._pvars.window_title_name)]),
                      color=ba.app.ui.heading_color,
                      maxwidth=290,
                      h_align='center',
                      v_align='center')

        ba.buttonwidget(edit=btn,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        v = self._height - 59.0
        h = 41 + x_inset
        b_color = (0.6, 0.53, 0.63)
        b_textcolor = (0.75, 0.7, 0.8)
        self._lock_images: List[ba.Widget] = []
        lock_tex = ba.gettexture('lock')

        scl = (1.1 if uiscale is ba.UIScale.SMALL else
               1.27 if uiscale is ba.UIScale.MEDIUM else 1.57)
        scl *= 0.63
        v -= 65.0 * scl
        new_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._new_playlist,
            color=b_color,
            autoselect=True,
            button_type='square',
            textcolor=b_textcolor,
            text_scale=0.7,
            label=ba.Lstr(resource='newText',
                          fallback_resource=self._r + '.newText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 58.0 * scl - 28),
                           texture=lock_tex))

        v -= 65.0 * scl
        self._edit_button = edit_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._edit_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=ba.Lstr(resource='editText',
                          fallback_resource=self._r + '.editText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 58.0 * scl - 28),
                           texture=lock_tex))

        v -= 65.0 * scl
        duplicate_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._duplicate_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=ba.Lstr(resource='duplicateText',
                          fallback_resource=self._r + '.duplicateText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 58.0 * scl - 28),
                           texture=lock_tex))

        v -= 65.0 * scl
        delete_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._delete_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=ba.Lstr(resource='deleteText',
                          fallback_resource=self._r + '.deleteText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 58.0 * scl - 28),
                           texture=lock_tex))
        v -= 65.0 * scl
        self._import_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._import_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=ba.Lstr(resource='importText'))
        v -= 65.0 * scl
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(h, v),
                              size=(90, 58.0 * scl),
                              on_activate_call=self._share_playlist,
                              color=b_color,
                              autoselect=True,
                              textcolor=b_textcolor,
                              button_type='square',
                              text_scale=0.7,
                              label=ba.Lstr(resource='shareText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 58.0 * scl - 28),
                           texture=lock_tex))

        v = self._height - 75
        self._scroll_height = self._height - 119
        scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                       position=(140 + x_inset,
                                                 v - self._scroll_height),
                                       size=(self._width - (180 + 2 * x_inset),
                                             self._scroll_height + 10),
                                       highlight=False)
        ba.widget(edit=back_button, right_widget=scrollwidget)
        self._columnwidget = ba.columnwidget(parent=scrollwidget,
                                             border=2,
                                             margin=0)

        h = 145

        self._do_randomize_val = ba.app.config.get(
            self._pvars.config_name + ' Playlist Randomize', 0)

        h += 210

        for btn in [new_button, delete_button, edit_button, duplicate_button]:
            ba.widget(edit=btn, right_widget=scrollwidget)
        ba.widget(edit=scrollwidget,
                  left_widget=new_button,
                  right_widget=_ba.get_special_widget('party_button')
                  if ba.app.ui.use_toolbars else None)

        # make sure config exists
        self._config_name_full = self._pvars.config_name + ' Playlists'

        if self._config_name_full not in ba.app.config:
            ba.app.config[self._config_name_full] = {}

        self._selected_playlist_name: Optional[str] = None
        self._selected_playlist_index: Optional[int] = None
        self._playlist_widgets: List[ba.Widget] = []

        self._refresh(select_playlist=select_playlist)

        ba.buttonwidget(edit=back_button, on_activate_call=self._back)
        ba.containerwidget(edit=self._root_widget, cancel_button=back_button)

        ba.containerwidget(edit=self._root_widget, selected_child=scrollwidget)

        # Keep our lock images up to date/etc.
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      timetype=ba.TimeType.REAL,
                                      repeat=True)
        self._update()

    def _update(self) -> None:
        from ba.internal import have_pro_options
        have = have_pro_options()
        for lock in self._lock_images:
            ba.imagewidget(edit=lock, opacity=0.0 if have else 1.0)

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.playlist import browser
        if self._selected_playlist_name is not None:
            cfg = ba.app.config
            cfg[self._pvars.config_name +
                ' Playlist Selection'] = self._selected_playlist_name
            cfg.commit()

        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            browser.PlaylistBrowserWindow(
                transition='in_left',
                sessiontype=self._sessiontype).get_root_widget())

    def _select(self, name: str, index: int) -> None:
        self._selected_playlist_name = name
        self._selected_playlist_index = index

    def _run_selected_playlist(self) -> None:
        # pylint: disable=cyclic-import
        _ba.unlock_all_input()
        try:
            _ba.new_host_session(self._sessiontype)
        except Exception:
            from bastd import mainmenu
            ba.print_exception(f'Error running session {self._sessiontype}.')

            # Drop back into a main menu session.
            _ba.new_host_session(mainmenu.MainMenuSession)

    def _choose_playlist(self) -> None:
        if self._selected_playlist_name is None:
            return
        self._save_playlist_selection()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        _ba.fade_screen(False, endcall=self._run_selected_playlist)
        _ba.lock_all_input()

    def _refresh(self, select_playlist: str = None) -> None:
        old_selection = self._selected_playlist_name

        # If there was no prev selection, look in prefs.
        if old_selection is None:
            old_selection = ba.app.config.get(self._pvars.config_name +
                                              ' Playlist Selection')

        old_selection_index = self._selected_playlist_index

        # Delete old.
        while self._playlist_widgets:
            self._playlist_widgets.pop().delete()

        items = list(ba.app.config[self._config_name_full].items())

        # Make sure everything is unicode now.
        items = [(i[0].decode(), i[1]) if not isinstance(i[0], str) else i
                 for i in items]

        items.sort(key=lambda x: x[0].lower())

        items = [['__default__', None]] + items  # Default is always first.
        index = 0
        for pname, _ in items:
            assert pname is not None
            txtw = ba.textwidget(
                parent=self._columnwidget,
                size=(self._width - 40, 30),
                maxwidth=self._width - 110,
                text=self._get_playlist_display_name(pname),
                h_align='left',
                v_align='center',
                color=(0.6, 0.6, 0.7, 1.0) if pname == '__default__' else
                (0.85, 0.85, 0.85, 1),
                always_highlight=True,
                on_select_call=ba.Call(self._select, pname, index),
                on_activate_call=ba.Call(self._edit_button.activate),
                selectable=True)
            ba.widget(edit=txtw, show_buffer_top=50, show_buffer_bottom=50)

            # Hitting up from top widget should jump to 'back'
            if index == 0:
                ba.widget(edit=txtw, up_widget=self._back_button)

            self._playlist_widgets.append(txtw)

            # Select this one if the user requested it.
            if select_playlist is not None:
                if pname == select_playlist:
                    ba.columnwidget(edit=self._columnwidget,
                                    selected_child=txtw,
                                    visible_child=txtw)
            else:
                # Select this one if it was previously selected.
                # Go by index if there's one.
                if old_selection_index is not None:
                    if index == old_selection_index:
                        ba.columnwidget(edit=self._columnwidget,
                                        selected_child=txtw,
                                        visible_child=txtw)
                else:  # Otherwise look by name.
                    if pname == old_selection:
                        ba.columnwidget(edit=self._columnwidget,
                                        selected_child=txtw,
                                        visible_child=txtw)

            index += 1

    def _save_playlist_selection(self) -> None:
        # Store the selected playlist in prefs.
        # This serves dual purposes of letting us re-select it next time
        # if we want and also lets us pass it to the game (since we reset
        # the whole python environment that's not actually easy).
        cfg = ba.app.config
        cfg[self._pvars.config_name +
            ' Playlist Selection'] = self._selected_playlist_name
        cfg[self._pvars.config_name +
            ' Playlist Randomize'] = self._do_randomize_val
        cfg.commit()

    def _new_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui.playlist import editcontroller
        from bastd.ui import purchase
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return

        # Clamp at our max playlist number.
        if len(ba.app.config[self._config_name_full]) > self._max_playlists:
            ba.screenmessage(
                ba.Lstr(translate=('serverResponses',
                                   'Max number of playlists reached.')),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        # In case they cancel so we can return to this state.
        self._save_playlist_selection()

        # Kick off the edit UI.
        editcontroller.PlaylistEditController(sessiontype=self._sessiontype)
        ba.containerwidget(edit=self._root_widget, transition='out_left')

    def _edit_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui.playlist import editcontroller
        from bastd.ui import purchase
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return
        if self._selected_playlist_name is None:
            return
        if self._selected_playlist_name == '__default__':
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource=self._r +
                                     '.cantEditDefaultText'))
            return
        self._save_playlist_selection()
        editcontroller.PlaylistEditController(
            existing_playlist_name=self._selected_playlist_name,
            sessiontype=self._sessiontype)
        ba.containerwidget(edit=self._root_widget, transition='out_left')

    def _do_delete_playlist(self) -> None:
        _ba.add_transaction({
            'type': 'REMOVE_PLAYLIST',
            'playlistType': self._pvars.config_name,
            'playlistName': self._selected_playlist_name
        })
        _ba.run_transactions()
        ba.playsound(ba.getsound('shieldDown'))

        # (we don't use len()-1 here because the default list adds one)
        assert self._selected_playlist_index is not None
        if self._selected_playlist_index > len(
                ba.app.config[self._pvars.config_name + ' Playlists']):
            self._selected_playlist_index = len(
                ba.app.config[self._pvars.config_name + ' Playlists'])
        self._refresh()

    def _import_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.playlist import share

        # Gotta be signed in for this to work.
        if _ba.get_account_state() != 'signed_in':
            ba.screenmessage(ba.Lstr(resource='notSignedInErrorText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        share.SharePlaylistImportWindow(origin_widget=self._import_button,
                                        on_success_callback=ba.WeakCall(
                                            self._on_playlist_import_success))

    def _on_playlist_import_success(self) -> None:
        self._refresh()

    def _on_share_playlist_response(self, name: str, response: Any) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.playlist import share
        if response is None:
            ba.screenmessage(
                ba.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return
        share.SharePlaylistResultsWindow(name, response)

    def _share_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui import purchase
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return

        # Gotta be signed in for this to work.
        if _ba.get_account_state() != 'signed_in':
            ba.screenmessage(ba.Lstr(resource='notSignedInErrorText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return
        if self._selected_playlist_name == '__default__':
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource=self._r +
                                     '.cantShareDefaultText'),
                             color=(1, 0, 0))
            return

        if self._selected_playlist_name is None:
            return

        _ba.add_transaction(
            {
                'type': 'SHARE_PLAYLIST',
                'expire_time': time.time() + 5,
                'playlistType': self._pvars.config_name,
                'playlistName': self._selected_playlist_name
            },
            callback=ba.WeakCall(self._on_share_playlist_response,
                                 self._selected_playlist_name))
        _ba.run_transactions()
        ba.screenmessage(ba.Lstr(resource='sharingText'))

    def _delete_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui import purchase
        from bastd.ui import confirm
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return

        if self._selected_playlist_name is None:
            return
        if self._selected_playlist_name == '__default__':
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(
                ba.Lstr(resource=self._r + '.cantDeleteDefaultText'))
        else:
            confirm.ConfirmWindow(
                ba.Lstr(resource=self._r + '.deleteConfirmText',
                        subs=[('${LIST}', self._selected_playlist_name)]),
                self._do_delete_playlist, 450, 150)

    def _get_playlist_display_name(self, playlist: str) -> ba.Lstr:
        if playlist == '__default__':
            return self._pvars.default_list_name
        return playlist if isinstance(playlist, ba.Lstr) else ba.Lstr(
            value=playlist)

    def _duplicate_playlist(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui import purchase
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return
        if self._selected_playlist_name is None:
            return
        plst: Optional[List[Dict[str, Any]]]
        if self._selected_playlist_name == '__default__':
            plst = self._pvars.get_default_list_call()
        else:
            plst = ba.app.config[self._config_name_full].get(
                self._selected_playlist_name)
            if plst is None:
                ba.playsound(ba.getsound('error'))
                return

        # clamp at our max playlist number
        if len(ba.app.config[self._config_name_full]) > self._max_playlists:
            ba.screenmessage(
                ba.Lstr(translate=('serverResponses',
                                   'Max number of playlists reached.')),
                color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        copy_text = ba.Lstr(resource='copyOfText').evaluate()
        # get just 'Copy' or whatnot
        copy_word = copy_text.replace('${NAME}', '').strip()
        # find a valid dup name that doesn't exist

        test_index = 1
        base_name = self._get_playlist_display_name(
            self._selected_playlist_name).evaluate()

        # If it looks like a copy, strip digits and spaces off the end.
        if copy_word in base_name:
            while base_name[-1].isdigit() or base_name[-1] == ' ':
                base_name = base_name[:-1]
        while True:
            if copy_word in base_name:
                test_name = base_name
            else:
                test_name = copy_text.replace('${NAME}', base_name)
            if test_index > 1:
                test_name += ' ' + str(test_index)
            if test_name not in ba.app.config[self._config_name_full]:
                break
            test_index += 1

        _ba.add_transaction({
            'type': 'ADD_PLAYLIST',
            'playlistType': self._pvars.config_name,
            'playlistName': test_name,
            'playlist': copy.deepcopy(plst)
        })
        _ba.run_transactions()

        ba.playsound(ba.getsound('gunCocking'))
        self._refresh(select_playlist=test_name)
