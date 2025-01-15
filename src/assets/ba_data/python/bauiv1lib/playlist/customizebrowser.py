# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for viewing/creating/editing playlists."""

from __future__ import annotations

import copy
import time

# import logging
from typing import TYPE_CHECKING, override

# import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any

    import bascenev1 as bs

REQUIRE_PRO = False


class PlaylistCustomizeBrowserWindow(bui.MainWindow):
    """Window for viewing a playlist."""

    def __init__(
        self,
        sessiontype: type[bs.Session],
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        select_playlist: str | None = None,
    ):
        # Yes this needs tidying.
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        from bauiv1lib import playlist

        self._sessiontype = sessiontype
        self._pvars = playlist.PlaylistTypeVars(sessiontype)
        self._max_playlists = 30
        self._r = 'gameListWindow'
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 970.0 if uiscale is bui.UIScale.SMALL else 650.0
        x_inset = 100.0 if uiscale is bui.UIScale.SMALL else 0.0
        yoffs = -51 if uiscale is bui.UIScale.SMALL else 0.0
        self._height = (
            440.0
            if uiscale is bui.UIScale.SMALL
            else 420.0 if uiscale is bui.UIScale.MEDIUM else 500.0
        )

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    1.8
                    if uiscale is bui.UIScale.SMALL
                    else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        self._back_button: bui.Widget | None
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(43 + x_inset, self._height - 60 + yoffs),
                size=(160, 68),
                scale=0.77,
                autoselect=True,
                text_scale=1.3,
                label=bui.Lstr(resource='backText'),
                button_type='back',
            )
            bui.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                0,
                self._height
                - (47 if uiscale is bui.UIScale.SMALL else 47)
                + yoffs,
            ),
            size=(self._width, 25),
            text=bui.Lstr(
                resource=f'{self._r}.titleText',
                subs=[('${TYPE}', self._pvars.window_title_name)],
            ),
            color=bui.app.ui_v1.heading_color,
            maxwidth=290,
            h_align='center',
            v_align='center',
        )

        v = self._height - 59.0 + yoffs
        h = 41 + x_inset
        b_color = (0.6, 0.53, 0.63)
        b_textcolor = (0.75, 0.7, 0.8)
        self._lock_images: list[bui.Widget] = []
        lock_tex = bui.gettexture('lock')

        scl = (
            1.1
            if uiscale is bui.UIScale.SMALL
            else 1.27 if uiscale is bui.UIScale.MEDIUM else 1.57
        )
        scl *= 0.63
        v -= 65.0 * scl
        new_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._new_playlist,
            color=b_color,
            autoselect=True,
            button_type='square',
            textcolor=b_textcolor,
            text_scale=0.7,
            label=bui.Lstr(
                resource='newText', fallback_resource=f'{self._r}.newText'
            ),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 58.0 * scl - 28),
                texture=lock_tex,
            )
        )

        v -= 65.0 * scl
        self._edit_button = edit_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._edit_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=bui.Lstr(
                resource='editText', fallback_resource=f'{self._r}.editText'
            ),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 58.0 * scl - 28),
                texture=lock_tex,
            )
        )

        v -= 65.0 * scl
        duplicate_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._duplicate_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=bui.Lstr(
                resource='duplicateText',
                fallback_resource=f'{self._r}.duplicateText',
            ),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 58.0 * scl - 28),
                texture=lock_tex,
            )
        )

        v -= 65.0 * scl
        delete_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._delete_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=bui.Lstr(
                resource='deleteText', fallback_resource=f'{self._r}.deleteText'
            ),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 58.0 * scl - 28),
                texture=lock_tex,
            )
        )
        v -= 65.0 * scl
        self._import_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._import_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=bui.Lstr(resource='importText'),
        )
        v -= 65.0 * scl
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(90, 58.0 * scl),
            on_activate_call=self._share_playlist,
            color=b_color,
            autoselect=True,
            textcolor=b_textcolor,
            button_type='square',
            text_scale=0.7,
            label=bui.Lstr(resource='shareText'),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 58.0 * scl - 28),
                texture=lock_tex,
            )
        )

        v = self._height - 75 + yoffs
        self._scroll_height = self._height - (
            180 if uiscale is bui.UIScale.SMALL else 119
        )
        scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(140 + x_inset, v - self._scroll_height),
            size=(self._width - (180 + 2 * x_inset), self._scroll_height + 10),
            highlight=False,
            border_opacity=0.4,
        )
        if self._back_button is not None:
            bui.widget(edit=self._back_button, right_widget=scrollwidget)

        self._columnwidget = bui.columnwidget(
            parent=scrollwidget, border=2, margin=0
        )

        h = 145

        self._do_randomize_val = bui.app.config.get(
            self._pvars.config_name + ' Playlist Randomize', 0
        )

        h += 210

        for btn in [new_button, delete_button, edit_button, duplicate_button]:
            bui.widget(edit=btn, right_widget=scrollwidget)
        bui.widget(
            edit=scrollwidget,
            left_widget=new_button,
            right_widget=bui.get_special_widget('squad_button'),
        )

        # Make sure config exists.
        self._config_name_full = f'{self._pvars.config_name} Playlists'

        if self._config_name_full not in bui.app.config:
            bui.app.config[self._config_name_full] = {}

        self._selected_playlist_name: str | None = None
        self._selected_playlist_index: int | None = None
        self._playlist_widgets: list[bui.Widget] = []

        self._refresh(select_playlist=select_playlist)

        if self._back_button is not None:
            bui.buttonwidget(
                edit=self._back_button, on_activate_call=self.main_window_back
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        bui.containerwidget(edit=self._root_widget, selected_child=scrollwidget)

        # Keep our lock images up to date/etc.
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Avoid dereferencing self within the lambda or we'll keep
        # ourself alive indefinitely.
        stype = self._sessiontype

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                sessiontype=stype,
            )
        )

    @override
    def on_main_window_close(self) -> None:
        if self._selected_playlist_name is not None:
            cfg = bui.app.config
            cfg[f'{self._pvars.config_name} Playlist Selection'] = (
                self._selected_playlist_name
            )
            cfg.commit()

    def _update(self) -> None:
        assert bui.app.classic is not None
        have = bui.app.classic.accounts.have_pro_options()
        for lock in self._lock_images:
            bui.imagewidget(
                edit=lock, opacity=0.0 if (have or not REQUIRE_PRO) else 1.0
            )

    def _select(self, name: str, index: int) -> None:
        self._selected_playlist_name = name
        self._selected_playlist_index = index

    def _refresh(self, select_playlist: str | None = None) -> None:
        from efro.util import asserttype

        old_selection = self._selected_playlist_name

        # If there was no prev selection, look in prefs.
        if old_selection is None:
            old_selection = bui.app.config.get(
                self._pvars.config_name + ' Playlist Selection'
            )

        old_selection_index = self._selected_playlist_index

        # Delete old.
        while self._playlist_widgets:
            self._playlist_widgets.pop().delete()

        items = list(bui.app.config[self._config_name_full].items())

        # Make sure everything is unicode now.
        items = [
            (i[0].decode(), i[1]) if not isinstance(i[0], str) else i
            for i in items
        ]

        items.sort(key=lambda x: asserttype(x[0], str).lower())

        items = [['__default__', None]] + items  # Default is always first.
        index = 0
        for pname, _ in items:
            assert pname is not None
            txtw = bui.textwidget(
                parent=self._columnwidget,
                size=(self._width - 40, 30),
                maxwidth=440,
                text=self._get_playlist_display_name(pname),
                h_align='left',
                v_align='center',
                color=(
                    (0.6, 0.6, 0.7, 1.0)
                    if pname == '__default__'
                    else (0.85, 0.85, 0.85, 1)
                ),
                always_highlight=True,
                on_select_call=bui.Call(self._select, pname, index),
                on_activate_call=bui.Call(self._edit_button.activate),
                selectable=True,
            )
            bui.widget(edit=txtw, show_buffer_top=50, show_buffer_bottom=50)

            # Hitting up from top widget should jump to 'back'.
            if index == 0:
                bui.widget(
                    edit=txtw,
                    up_widget=(
                        self._back_button
                        if self._back_button is not None
                        else bui.get_special_widget('back_button')
                    ),
                )

            self._playlist_widgets.append(txtw)

            # Select this one if the user requested it.
            if select_playlist is not None:
                if pname == select_playlist:
                    bui.columnwidget(
                        edit=self._columnwidget,
                        selected_child=txtw,
                        visible_child=txtw,
                    )
            else:
                # Select this one if it was previously selected. Go by
                # index if there's one.
                if old_selection_index is not None:
                    if index == old_selection_index:
                        bui.columnwidget(
                            edit=self._columnwidget,
                            selected_child=txtw,
                            visible_child=txtw,
                        )
                else:  # Otherwise look by name.
                    if pname == old_selection:
                        bui.columnwidget(
                            edit=self._columnwidget,
                            selected_child=txtw,
                            visible_child=txtw,
                        )

            index += 1

    def _save_playlist_selection(self) -> None:
        # Store the selected playlist in prefs. This serves dual
        # purposes of letting us re-select it next time if we want and
        # also lets us pass it to the game (since we reset the whole
        # python environment that's not actually easy).
        cfg = bui.app.config
        cfg[self._pvars.config_name + ' Playlist Selection'] = (
            self._selected_playlist_name
        )
        cfg[self._pvars.config_name + ' Playlist Randomize'] = (
            self._do_randomize_val
        )
        cfg.commit()

    def _new_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist.editcontroller import PlaylistEditController
        from bauiv1lib.purchase import PurchaseWindow

        # No-op if we're not in control.
        if not self.main_window_has_control():
            return

        assert bui.app.classic is not None
        if REQUIRE_PRO and not bui.app.classic.accounts.have_pro_options():
            PurchaseWindow(items=['pro'])
            return

        # Clamp at our max playlist number.
        if len(bui.app.config[self._config_name_full]) > self._max_playlists:
            bui.screenmessage(
                bui.Lstr(
                    translate=(
                        'serverResponses',
                        'Max number of playlists reached.',
                    )
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # In case they cancel so we can return to this state.
        self._save_playlist_selection()

        # Kick off the edit UI.
        PlaylistEditController(sessiontype=self._sessiontype, from_window=self)

    def _edit_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist.editcontroller import PlaylistEditController
        from bauiv1lib.purchase import PurchaseWindow

        assert bui.app.classic is not None
        if REQUIRE_PRO and not bui.app.classic.accounts.have_pro_options():
            PurchaseWindow(items=['pro'])
            return
        if self._selected_playlist_name is None:
            return
        if self._selected_playlist_name == '__default__':
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantEditDefaultText')
            )
            return
        self._save_playlist_selection()
        PlaylistEditController(
            existing_playlist_name=self._selected_playlist_name,
            sessiontype=self._sessiontype,
            from_window=self,
        )

    def _do_delete_playlist(self) -> None:
        plus = bui.app.plus
        assert plus is not None
        plus.add_v1_account_transaction(
            {
                'type': 'REMOVE_PLAYLIST',
                'playlistType': self._pvars.config_name,
                'playlistName': self._selected_playlist_name,
            }
        )
        plus.run_v1_account_transactions()
        bui.getsound('shieldDown').play()

        # (we don't use len()-1 here because the default list adds one)
        assert self._selected_playlist_index is not None
        self._selected_playlist_index = min(
            self._selected_playlist_index,
            len(bui.app.config[self._pvars.config_name + ' Playlists']),
        )
        self._refresh()

    def _import_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist import share

        plus = bui.app.plus
        assert plus is not None

        # Gotta be signed in for this to work.
        if plus.get_v1_account_state() != 'signed_in':
            bui.screenmessage(
                bui.Lstr(resource='notSignedInErrorText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        share.SharePlaylistImportWindow(
            origin_widget=self._import_button,
            on_success_callback=bui.WeakCall(self._on_playlist_import_success),
        )

    def _on_playlist_import_success(self) -> None:
        self._refresh()

    def _on_share_playlist_response(self, name: str, response: Any) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist import share

        if response is None:
            bui.screenmessage(
                bui.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        share.SharePlaylistResultsWindow(name, response)

    def _share_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow

        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        if REQUIRE_PRO and not bui.app.classic.accounts.have_pro_options():
            PurchaseWindow(items=['pro'])
            return

        # Gotta be signed in for this to work.
        if plus.get_v1_account_state() != 'signed_in':
            bui.screenmessage(
                bui.Lstr(resource='notSignedInErrorText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return
        if self._selected_playlist_name == '__default__':
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantShareDefaultText'),
                color=(1, 0, 0),
            )
            return

        if self._selected_playlist_name is None:
            return

        plus.add_v1_account_transaction(
            {
                'type': 'SHARE_PLAYLIST',
                'expire_time': time.time() + 5,
                'playlistType': self._pvars.config_name,
                'playlistName': self._selected_playlist_name,
            },
            callback=bui.WeakCall(
                self._on_share_playlist_response, self._selected_playlist_name
            ),
        )
        plus.run_v1_account_transactions()
        bui.screenmessage(bui.Lstr(resource='sharingText'))

    def _delete_playlist(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow
        from bauiv1lib.confirm import ConfirmWindow

        assert bui.app.classic is not None
        if REQUIRE_PRO and not bui.app.classic.accounts.have_pro_options():
            PurchaseWindow(items=['pro'])
            return

        if self._selected_playlist_name is None:
            return
        if self._selected_playlist_name == '__default__':
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantDeleteDefaultText')
            )
        else:
            ConfirmWindow(
                bui.Lstr(
                    resource=f'{self._r}.deleteConfirmText',
                    subs=[('${LIST}', self._selected_playlist_name)],
                ),
                self._do_delete_playlist,
                450,
                150,
            )

    def _get_playlist_display_name(self, playlist: str) -> bui.Lstr:
        if playlist == '__default__':
            return self._pvars.default_list_name
        return (
            playlist
            if isinstance(playlist, bui.Lstr)
            else bui.Lstr(value=playlist)
        )

    def _duplicate_playlist(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow

        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        if REQUIRE_PRO and not bui.app.classic.accounts.have_pro_options():
            PurchaseWindow(items=['pro'])
            return
        if self._selected_playlist_name is None:
            return
        plst: list[dict[str, Any]] | None
        if self._selected_playlist_name == '__default__':
            plst = self._pvars.get_default_list_call()
        else:
            plst = bui.app.config[self._config_name_full].get(
                self._selected_playlist_name
            )
            if plst is None:
                bui.getsound('error').play()
                return

        # Clamp at our max playlist number.
        if len(bui.app.config[self._config_name_full]) > self._max_playlists:
            bui.screenmessage(
                bui.Lstr(
                    translate=(
                        'serverResponses',
                        'Max number of playlists reached.',
                    )
                ),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        copy_text = bui.Lstr(resource='copyOfText').evaluate()

        # Get just 'Copy' or whatnot.
        copy_word = copy_text.replace('${NAME}', '').strip()

        # Find a valid dup name that doesn't exist.
        test_index = 1
        base_name = self._get_playlist_display_name(
            self._selected_playlist_name
        ).evaluate()

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
            if test_name not in bui.app.config[self._config_name_full]:
                break
            test_index += 1

        plus.add_v1_account_transaction(
            {
                'type': 'ADD_PLAYLIST',
                'playlistType': self._pvars.config_name,
                'playlistName': test_name,
                'playlist': copy.deepcopy(plst),
            }
        )
        plus.run_v1_account_transactions()

        bui.getsound('gunCocking').play()
        self._refresh(select_playlist=test_name)
