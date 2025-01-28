# Released under the MIT License. See LICENSE for details.
#
"""Provides a window for configuring play options."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs
import bauiv1 as bui

from bauiv1lib.popup import PopupWindow

if TYPE_CHECKING:
    from typing import Any

    from bauiv1lib.play import PlaylistSelectContext

REQUIRE_PRO = False


class PlayOptionsWindow(PopupWindow):
    """A popup window for configuring play options."""

    def __init__(
        self,
        *,
        sessiontype: type[bs.Session],
        playlist: str,
        scale_origin: tuple[float, float],
        delegate: Any = None,
        playlist_select_context: PlaylistSelectContext | None = None,
    ):
        # FIXME: Tidy this up.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from bascenev1 import filter_playlist, get_map_class
        from bauiv1lib.playlist import PlaylistTypeVars
        from bauiv1lib.config import ConfigNumberEdit

        self._r = 'gameListWindow'
        self._delegate = delegate
        self._pvars = PlaylistTypeVars(sessiontype)
        self._transitioning_out = False

        self._playlist_select_context = playlist_select_context

        self._do_randomize_val = bui.app.config.get(
            self._pvars.config_name + ' Playlist Randomize', 0
        )

        self._sessiontype = sessiontype
        self._playlist = playlist

        self._width = 500.0
        self._height = 370.0 - 50.0

        # In teams games, show the custom names/colors button.
        if self._sessiontype is bs.DualTeamSession:
            self._height += 50.0

        self._row_height = 45.0

        # Grab our maps to display.
        mesh_opaque = bui.getmesh('level_select_button_opaque')
        mesh_transparent = bui.getmesh('level_select_button_transparent')
        mask_tex = bui.gettexture('mapPreviewMask')

        # Poke into this playlist and see if we can display some of its
        # maps.
        map_textures = []
        map_texture_entries = []
        rows = 0
        columns = 0
        game_count = 0
        scl = 0.35
        c_width_total = 0.0
        try:
            max_columns = 5
            name = playlist
            if name == '__default__':
                plst = self._pvars.get_default_list_call()
            else:
                try:
                    plst = bui.app.config[
                        self._pvars.config_name + ' Playlists'
                    ][name]
                except Exception:
                    print(
                        'ERROR INFO: self._config_name is:',
                        self._pvars.config_name,
                    )
                    print(
                        'ERROR INFO: playlist names are:',
                        list(
                            bui.app.config[
                                self._pvars.config_name + ' Playlists'
                            ].keys()
                        ),
                    )
                    raise
            plst = filter_playlist(
                plst,
                self._sessiontype,
                remove_unowned=False,
                mark_unowned=True,
                name=name,
            )
            game_count = len(plst)
            for entry in plst:
                mapname = entry['settings']['map']
                maptype: type[bs.Map] | None
                try:
                    maptype = get_map_class(mapname)
                except bui.NotFoundError:
                    maptype = None
                if maptype is not None:
                    tex_name = maptype.get_preview_texture_name()
                    if tex_name is not None:
                        map_textures.append(tex_name)
                        map_texture_entries.append(entry)
            rows = (max(0, len(map_textures) - 1) // max_columns) + 1
            columns = min(max_columns, len(map_textures))

            if len(map_textures) == 1:
                scl = 1.1
            elif len(map_textures) == 2:
                scl = 0.7
            elif len(map_textures) == 3:
                scl = 0.55
            else:
                scl = 0.35
            self._row_height = 128.0 * scl
            c_width_total = scl * 250.0 * columns
            if map_textures:
                self._height += self._row_height * rows

        except Exception:
            logging.exception('Error listing playlist maps.')

        show_shuffle_check_box = game_count > 1

        if show_shuffle_check_box:
            self._height += 40

        uiscale = bui.app.ui_v1.uiscale
        scale = (
            1.69
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.85
        )
        # Creates our _root_widget.
        super().__init__(
            position=scale_origin, size=(self._width, self._height), scale=scale
        )

        playlist_name: str | bui.Lstr = (
            self._pvars.default_list_name
            if playlist == '__default__'
            else playlist
        )
        self._title_text = bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 89 + 51),
            size=(0, 0),
            text=playlist_name,
            scale=1.4,
            color=(1, 1, 1),
            maxwidth=self._width * 0.7,
            h_align='center',
            v_align='center',
        )

        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(25, self._height - 53),
            size=(50, 50),
            scale=0.7,
            label='',
            color=(0.42, 0.73, 0.2),
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        h_offs_img = self._width * 0.5 - c_width_total * 0.5
        v_offs_img = self._height - 118 - scl * 125.0 + 50
        bottom_row_buttons = []
        self._have_at_least_one_owned = False

        for row in range(rows):
            for col in range(columns):
                tex_index = row * columns + col
                if tex_index < len(map_textures):
                    tex_name = map_textures[tex_index]
                    h = h_offs_img + scl * 250 * col
                    v = v_offs_img - self._row_height * row
                    entry = map_texture_entries[tex_index]
                    owned = not (
                        ('is_unowned_map' in entry and entry['is_unowned_map'])
                        or (
                            'is_unowned_game' in entry
                            and entry['is_unowned_game']
                        )
                    )

                    if owned:
                        self._have_at_least_one_owned = True

                    try:
                        desc = bui.getclass(
                            entry['type'], subclassof=bs.GameActivity
                        ).get_settings_display_string(entry)
                        if not owned:
                            desc = bui.Lstr(
                                value='${DESC}\n${UNLOCK}',
                                subs=[
                                    ('${DESC}', desc),
                                    (
                                        '${UNLOCK}',
                                        bui.Lstr(
                                            resource='unlockThisInTheStoreText'
                                        ),
                                    ),
                                ],
                            )
                        desc_color = (0, 1, 0) if owned else (1, 0, 0)
                    except Exception:
                        desc = bui.Lstr(value='(invalid)')
                        desc_color = (1, 0, 0)

                    btn = bui.buttonwidget(
                        parent=self.root_widget,
                        size=(scl * 240.0, scl * 120.0),
                        position=(h, v),
                        texture=bui.gettexture(tex_name if owned else 'empty'),
                        mesh_opaque=mesh_opaque if owned else None,
                        on_activate_call=bui.Call(
                            bui.screenmessage, desc, desc_color
                        ),
                        label='',
                        color=(1, 1, 1),
                        autoselect=True,
                        extra_touch_border_scale=0.0,
                        mesh_transparent=mesh_transparent if owned else None,
                        mask_texture=mask_tex if owned else None,
                    )
                    if row == 0 and col == 0:
                        bui.widget(edit=self._cancel_button, down_widget=btn)
                    if row == rows - 1:
                        bottom_row_buttons.append(btn)
                    if not owned:
                        # Ewww; buttons don't currently have alpha so in this
                        # case we draw an image over our button with an empty
                        # texture on it.
                        bui.imagewidget(
                            parent=self.root_widget,
                            size=(scl * 260.0, scl * 130.0),
                            position=(h - 10.0 * scl, v - 4.0 * scl),
                            draw_controller=btn,
                            color=(1, 1, 1),
                            texture=bui.gettexture(tex_name),
                            mesh_opaque=mesh_opaque,
                            opacity=0.25,
                            mesh_transparent=mesh_transparent,
                            mask_texture=mask_tex,
                        )

                        bui.imagewidget(
                            parent=self.root_widget,
                            size=(scl * 100, scl * 100),
                            draw_controller=btn,
                            position=(h + scl * 70, v + scl * 10),
                            texture=bui.gettexture('lock'),
                        )

        y_offs = 50 if show_shuffle_check_box else 0

        # Series Length
        y_offs2 = 40 if self._sessiontype is bs.DualTeamSession else 0
        self._series_length_numedit = ConfigNumberEdit(
            parent=self.root_widget,
            position=(100, 200 + y_offs + y_offs2),
            configkey=(
                'FFA' if self._sessiontype is bs.FreeForAllSession else 'Teams'
            )
            + ' Series Length',
            displayname=bui.Lstr(
                resource=self._r
                + (
                    '.pointsToWinText'
                    if self._sessiontype is bs.FreeForAllSession
                    else '.seriesLengthText'
                )
            ),
            minval=1.0,
            maxval=100.0 if self._sessiontype is bs.FreeForAllSession else 99.0,
            increment=1.0 if self._sessiontype is bs.FreeForAllSession else 2.0,
            fallback_value=(
                24 if self._sessiontype is bs.FreeForAllSession else 7
            ),
            f=0,
        )

        # Team names/colors.
        self._custom_colors_names_button: bui.Widget | None
        if self._sessiontype is bs.DualTeamSession:
            self._custom_colors_names_button = bui.buttonwidget(
                parent=self.root_widget,
                position=(100, 195 + y_offs),
                size=(290, 35),
                on_activate_call=bui.WeakCall(self._custom_colors_names_press),
                autoselect=True,
                textcolor=(0.8, 0.8, 0.8),
                label=bui.Lstr(resource='teamNamesColorText'),
            )
            assert bui.app.classic is not None
            if REQUIRE_PRO and not bui.app.classic.accounts.have_pro():
                bui.imagewidget(
                    parent=self.root_widget,
                    size=(30, 30),
                    position=(95, 202 + y_offs),
                    texture=bui.gettexture('lock'),
                    draw_controller=self._custom_colors_names_button,
                )
        else:
            self._custom_colors_names_button = None

        # Shuffle.
        def _cb_callback(val: bool) -> None:
            self._do_randomize_val = val
            cfg = bui.app.config
            cfg[self._pvars.config_name + ' Playlist Randomize'] = (
                self._do_randomize_val
            )
            cfg.commit()

        if show_shuffle_check_box:
            self._shuffle_check_box = bui.checkboxwidget(
                parent=self.root_widget,
                position=(110, 200),
                scale=1.0,
                size=(250, 30),
                autoselect=True,
                text=bui.Lstr(resource=f'{self._r}.shuffleGameOrderText'),
                maxwidth=300,
                textcolor=(0.8, 0.8, 0.8),
                value=self._do_randomize_val,
                on_value_change_call=_cb_callback,
            )

        # Show tutorial.
        show_tutorial = bool(bui.app.config.get('Show Tutorial', True))

        def _cb_callback_2(val: bool) -> None:
            cfg = bui.app.config
            cfg['Show Tutorial'] = val
            cfg.commit()

        self._show_tutorial_check_box = bui.checkboxwidget(
            parent=self.root_widget,
            position=(110, 151),
            scale=1.0,
            size=(250, 30),
            autoselect=True,
            text=bui.Lstr(resource=f'{self._r}.showTutorialText'),
            maxwidth=300,
            textcolor=(0.8, 0.8, 0.8),
            value=show_tutorial,
            on_value_change_call=_cb_callback_2,
        )

        # Grumble: current autoselect doesn't do a very good job
        # with checkboxes.
        if self._custom_colors_names_button is not None:
            for btn in bottom_row_buttons:
                bui.widget(
                    edit=btn, down_widget=self._custom_colors_names_button
                )
            if show_shuffle_check_box:
                bui.widget(
                    edit=self._custom_colors_names_button,
                    down_widget=self._shuffle_check_box,
                )
                bui.widget(
                    edit=self._shuffle_check_box,
                    up_widget=self._custom_colors_names_button,
                )
            else:
                bui.widget(
                    edit=self._custom_colors_names_button,
                    down_widget=self._show_tutorial_check_box,
                )
                bui.widget(
                    edit=self._show_tutorial_check_box,
                    up_widget=self._custom_colors_names_button,
                )

        self._ok_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(70, 44),
            size=(200, 45),
            scale=1.8,
            text_res_scale=1.5,
            on_activate_call=self._on_ok_press,
            autoselect=True,
            label=bui.Lstr(
                resource=(
                    'okText'
                    if self._playlist_select_context is not None
                    else 'playText'
                )
            ),
        )

        bui.widget(
            edit=self._ok_button, up_widget=self._show_tutorial_check_box
        )

        bui.containerwidget(
            edit=self.root_widget,
            start_button=self._ok_button,
            cancel_button=self._cancel_button,
            selected_child=self._ok_button,
        )

        # Update now and once per second.
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update()

    def _custom_colors_names_press(self) -> None:
        from bauiv1lib.account.signin import show_sign_in_prompt
        from bauiv1lib.teamnamescolors import TeamNamesColorsWindow
        from bauiv1lib.purchase import PurchaseWindow

        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        if REQUIRE_PRO and not bui.app.classic.accounts.have_pro():
            if plus.get_v1_account_state() != 'signed_in':
                show_sign_in_prompt()
            else:
                PurchaseWindow(items=['pro'])
            self._transition_out()
            return
        assert self._custom_colors_names_button
        TeamNamesColorsWindow(
            scale_origin=(
                self._custom_colors_names_button.get_screen_space_center()
            )
        )

    def _does_target_playlist_exist(self) -> bool:
        if self._playlist == '__default__':
            return True
        return self._playlist in bui.app.config.get(
            self._pvars.config_name + ' Playlists', {}
        )

    def _update(self) -> None:
        # All we do here is make sure our targeted playlist still exists,
        # and close ourself if not.
        if not self._does_target_playlist_exist():
            self._transition_out()

    def _transition_out(self, transition: str = 'out_scale') -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition=transition)

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _on_ok_press(self) -> None:
        # no-op if our underlying widget is dead or on its way out.
        if not self.root_widget or self.root_widget.transitioning_out:
            return

        # Disallow if our playlist has disappeared.
        if not self._does_target_playlist_exist():
            return

        # Disallow if we have no unlocked games.
        if not self._have_at_least_one_owned:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource='playlistNoValidGamesErrorText'),
                color=(1, 0, 0),
            )
            return

        cfg = bui.app.config
        cfg[self._pvars.config_name + ' Playlist Selection'] = self._playlist

        # Head back to the gather window in playlist-select mode or
        # start the game in regular mode.
        if self._playlist_select_context is not None:
            # from bauiv1lib.gather import GatherWindow

            if self._sessiontype is bs.FreeForAllSession:
                typename = 'ffa'
            elif self._sessiontype is bs.DualTeamSession:
                typename = 'teams'
            else:
                raise RuntimeError('Only teams and ffa currently supported')
            cfg['Private Party Host Session Type'] = typename
            bui.getsound('gunCocking').play()

            self._transition_out(transition='out_left')
            if self._delegate is not None:
                self._delegate.on_play_options_window_run_game()
        else:
            bui.fade_screen(False, endcall=self._run_selected_playlist)
            bui.lock_all_input()
            self._transition_out(transition='out_left')
            if self._delegate is not None:
                self._delegate.on_play_options_window_run_game()

        cfg.commit()

    def _run_selected_playlist(self) -> None:
        bui.unlock_all_input()

        # Save our place in the UI that we'll return to when done.
        if bs.app.classic is not None:
            bs.app.classic.save_ui_state()

        try:
            bs.new_host_session(self._sessiontype)
        except Exception:
            from bascenev1lib import mainmenu

            logging.exception('Error running session %s.', self._sessiontype)

            # Drop back into a main menu session.
            bs.new_host_session(mainmenu.MainMenuSession)
