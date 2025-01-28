# Released under the MIT License. See LICENSE for details.
#
"""Provides a window for browsing and launching game playlists."""

from __future__ import annotations

import copy
import math
import logging
from typing import override, TYPE_CHECKING

import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from bauiv1lib.play import PlaylistSelectContext


class PlaylistBrowserWindow(bui.MainWindow):
    """Window for starting teams games."""

    def __init__(
        self,
        sessiontype: type[bs.Session],
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        playlist_select_context: PlaylistSelectContext | None = None,
    ):
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist import PlaylistTypeVars

        # Store state for when we exit the next game.
        if issubclass(sessiontype, bs.DualTeamSession):
            bui.set_analytics_screen('Teams Window')
        elif issubclass(sessiontype, bs.FreeForAllSession):
            bui.set_analytics_screen('FreeForAll Window')
        else:
            raise TypeError(f'Invalid sessiontype: {sessiontype}.')
        self._pvars = PlaylistTypeVars(sessiontype)

        self._sessiontype = sessiontype

        self._customize_button: bui.Widget | None = None
        self._sub_width: float | None = None
        self._sub_height: float | None = None
        self._playlist_select_context = playlist_select_context

        self._ensure_standard_playlists_exist()

        # Get the current selection (if any).
        self._selected_playlist = bui.app.config.get(
            self._pvars.config_name + ' Playlist Selection'
        )

        uiscale = bui.app.ui_v1.uiscale
        self._width = (
            1100.0
            if uiscale is bui.UIScale.SMALL
            else 800.0 if uiscale is bui.UIScale.MEDIUM else 1040
        )
        self._height = (
            600
            if uiscale is bui.UIScale.SMALL
            else 550 if uiscale is bui.UIScale.MEDIUM else 700
        )

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.85
            if uiscale is bui.UIScale.SMALL
            else 1.0 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 100, screensize[0] / scale)
        target_height = min(self._height - 100, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        self._scroll_width = target_width
        self._scroll_height = target_height - 31
        scroll_bottom = yoffs - 60 - self._scroll_height

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_minimal'
                    if (
                        uiscale is bui.UIScale.SMALL
                        or playlist_select_context is not None
                    )
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        self._back_button: bui.Widget | None
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self._on_back_press
            )
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(59, yoffs - 45),
                size=(60, 54),
                scale=1.0,
                on_activate_call=self._on_back_press,
                autoselect=True,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (45 if uiscale is bui.UIScale.SMALL else 20),
            ),
            size=(0, 0),
            text=self._pvars.window_title_name,
            scale=(0.8 if uiscale is bui.UIScale.SMALL else 1.3),
            res_scale=1.5,
            color=bui.app.ui_v1.heading_color,
            h_align='center',
            v_align='center',
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            position=(
                self._width * 0.5 - self._scroll_width * 0.5,
                scroll_bottom,
            ),
            border_opacity=0.4,
            center_small_content_horizontally=True,
        )
        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)
        self._subcontainer: bui.Widget | None = None
        self._config_name_full = self._pvars.config_name + ' Playlists'
        self._last_config = None

        # Update now and once per second (this should do our initial
        # refresh).
        self._update()
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull things out of self here; if we do it below in the lambda
        # then we keep self alive.
        sessiontype = self._sessiontype

        # Pull anything out of self here; if we do it in the lambda
        # we'll inadvertanly keep self alive.
        playlist_select_context = self._playlist_select_context

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                sessiontype=sessiontype,
                playlist_select_context=playlist_select_context,
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _ensure_standard_playlists_exist(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # On new installations, go ahead and create a few playlists
        # besides the hard-coded default one:
        if not plus.get_v1_account_misc_val('madeStandardPlaylists', False):
            plus.add_v1_account_transaction(
                {
                    'type': 'ADD_PLAYLIST',
                    'playlistType': 'Free-for-All',
                    'playlistName': bui.Lstr(
                        resource='singleGamePlaylistNameText'
                    )
                    .evaluate()
                    .replace(
                        '${GAME}',
                        bui.Lstr(
                            translate=('gameNames', 'Death Match')
                        ).evaluate(),
                    ),
                    'playlist': [
                        {
                            'type': 'bs_death_match.DeathMatchGame',
                            'settings': {
                                'Epic Mode': False,
                                'Kills to Win Per Player': 10,
                                'Respawn Times': 1.0,
                                'Time Limit': 300,
                                'map': 'Doom Shroom',
                            },
                        },
                        {
                            'type': 'bs_death_match.DeathMatchGame',
                            'settings': {
                                'Epic Mode': False,
                                'Kills to Win Per Player': 10,
                                'Respawn Times': 1.0,
                                'Time Limit': 300,
                                'map': 'Crag Castle',
                            },
                        },
                    ],
                }
            )
            plus.add_v1_account_transaction(
                {
                    'type': 'ADD_PLAYLIST',
                    'playlistType': 'Team Tournament',
                    'playlistName': bui.Lstr(
                        resource='singleGamePlaylistNameText'
                    )
                    .evaluate()
                    .replace(
                        '${GAME}',
                        bui.Lstr(
                            translate=('gameNames', 'Capture the Flag')
                        ).evaluate(),
                    ),
                    'playlist': [
                        {
                            'type': 'bs_capture_the_flag.CTFGame',
                            'settings': {
                                'map': 'Bridgit',
                                'Score to Win': 3,
                                'Flag Idle Return Time': 30,
                                'Flag Touch Return Time': 0,
                                'Respawn Times': 1.0,
                                'Time Limit': 600,
                                'Epic Mode': False,
                            },
                        },
                        {
                            'type': 'bs_capture_the_flag.CTFGame',
                            'settings': {
                                'map': 'Roundabout',
                                'Score to Win': 2,
                                'Flag Idle Return Time': 30,
                                'Flag Touch Return Time': 0,
                                'Respawn Times': 1.0,
                                'Time Limit': 600,
                                'Epic Mode': False,
                            },
                        },
                        {
                            'type': 'bs_capture_the_flag.CTFGame',
                            'settings': {
                                'map': 'Tip Top',
                                'Score to Win': 2,
                                'Flag Idle Return Time': 30,
                                'Flag Touch Return Time': 3,
                                'Respawn Times': 1.0,
                                'Time Limit': 300,
                                'Epic Mode': False,
                            },
                        },
                    ],
                }
            )
            plus.add_v1_account_transaction(
                {
                    'type': 'ADD_PLAYLIST',
                    'playlistType': 'Team Tournament',
                    'playlistName': bui.Lstr(
                        translate=('playlistNames', 'Just Sports')
                    ).evaluate(),
                    'playlist': [
                        {
                            'type': 'bs_hockey.HockeyGame',
                            'settings': {
                                'Time Limit': 0,
                                'map': 'Hockey Stadium',
                                'Score to Win': 1,
                                'Respawn Times': 1.0,
                            },
                        },
                        {
                            'type': 'bs_football.FootballTeamGame',
                            'settings': {
                                'Time Limit': 0,
                                'map': 'Football Stadium',
                                'Score to Win': 21,
                                'Respawn Times': 1.0,
                            },
                        },
                    ],
                }
            )
            plus.add_v1_account_transaction(
                {
                    'type': 'ADD_PLAYLIST',
                    'playlistType': 'Free-for-All',
                    'playlistName': bui.Lstr(
                        translate=('playlistNames', 'Just Epic')
                    ).evaluate(),
                    'playlist': [
                        {
                            'type': 'bs_elimination.EliminationGame',
                            'settings': {
                                'Time Limit': 120,
                                'map': 'Tip Top',
                                'Respawn Times': 1.0,
                                'Lives Per Player': 1,
                                'Epic Mode': 1,
                            },
                        }
                    ],
                }
            )
            plus.add_v1_account_transaction(
                {
                    'type': 'SET_MISC_VAL',
                    'name': 'madeStandardPlaylists',
                    'value': True,
                }
            )
            plus.run_v1_account_transactions()

    def _refresh(self) -> None:
        # FIXME: Should tidy this up.
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-nested-blocks
        from efro.util import asserttype
        from bascenev1 import get_map_class, filter_playlist

        if not self._root_widget:
            return
        if self._subcontainer is not None:
            self._save_state()
            self._subcontainer.delete()

        # Make sure config exists.
        if self._config_name_full not in bui.app.config:
            bui.app.config[self._config_name_full] = {}

        items = list(bui.app.config[self._config_name_full].items())

        # Make sure everything is unicode.
        items = [
            (i[0].decode(), i[1]) if not isinstance(i[0], str) else i
            for i in items
        ]

        items.sort(key=lambda x2: asserttype(x2[0], str).lower())
        items = [['__default__', None]] + items  # default is always first

        button_width = 230
        button_height = 230
        button_buffer_h = -3
        button_buffer_v = 0

        count = len(items)
        columns = max(
            1,
            math.floor(
                self._scroll_width / (button_width + 2 * button_buffer_h)
            ),
        )
        rows = int(math.ceil(float(count) / columns))

        self._sub_width = columns * button_width + 2 * button_buffer_h

        self._sub_height = (
            40.0 + rows * (button_height + 2 * button_buffer_v) + 90
        )
        assert self._sub_width is not None
        assert self._sub_height is not None
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
        )

        children = self._subcontainer.get_children()
        for child in children:
            child.delete()

        # On small ui-scale, nudge 'Playlists' text to the right when
        # we're small enough so that the back button doesn't partly
        # obscure it.
        uiscale = bui.app.ui_v1.uiscale
        screensize = bui.get_virtual_screen_size()
        xoffs = (
            40 if uiscale is bui.UIScale.SMALL and screensize[0] < 1400 else 0
        )

        assert bui.app.classic is not None
        bui.textwidget(
            parent=self._subcontainer,
            text=bui.Lstr(resource='playlistsText'),
            position=(40 + xoffs, self._sub_height - 26),
            size=(0, 0),
            scale=1.0,
            maxwidth=400,
            color=bui.app.ui_v1.title_color,
            h_align='left',
            v_align='center',
        )

        index = 0
        appconfig = bui.app.config

        mesh_opaque = bui.getmesh('level_select_button_opaque')
        mesh_transparent = bui.getmesh('level_select_button_transparent')
        mask_tex = bui.gettexture('mapPreviewMask')

        # h_offs = 225 if count == 1 else 115 if count == 2 else 0
        h_offs = 2
        h_offs_bottom = 0

        uiscale = bui.app.ui_v1.uiscale
        for y in range(rows):
            for x in range(columns):
                name = items[index][0]
                assert name is not None
                pos = (
                    x * (button_width + 2 * button_buffer_h)
                    + button_buffer_h
                    + 8
                    + h_offs,
                    self._sub_height
                    - 47
                    - (y + 1) * (button_height + 2 * button_buffer_v),
                )
                btn = bui.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    size=(button_width, button_height),
                    autoselect=True,
                    label='',
                    position=pos,
                )

                if x == 0 and uiscale is bui.UIScale.SMALL:
                    bui.widget(
                        edit=btn,
                        left_widget=bui.get_special_widget('back_button'),
                    )
                if x == columns - 1 and uiscale is bui.UIScale.SMALL:
                    bui.widget(
                        edit=btn,
                        right_widget=bui.get_special_widget('squad_button'),
                    )
                bui.buttonwidget(
                    edit=btn,
                    on_activate_call=bui.Call(
                        self._on_playlist_press, btn, name
                    ),
                    on_select_call=bui.Call(self._on_playlist_select, name),
                )

                # Top row biases things up more to show header above it.
                if y == 0:
                    bui.widget(
                        edit=btn, show_buffer_top=60, show_buffer_bottom=5
                    )
                else:
                    bui.widget(
                        edit=btn, show_buffer_top=30, show_buffer_bottom=30
                    )

                if self._selected_playlist == name:
                    bui.containerwidget(
                        edit=self._subcontainer,
                        selected_child=btn,
                        visible_child=btn,
                    )

                if self._back_button is not None:
                    if y == 0:
                        bui.widget(edit=btn, up_widget=self._back_button)
                    if x == 0:
                        bui.widget(edit=btn, left_widget=self._back_button)

                print_name: str | bui.Lstr | None
                if name == '__default__':
                    print_name = self._pvars.default_list_name
                else:
                    print_name = name
                bui.textwidget(
                    parent=self._subcontainer,
                    text=print_name,
                    position=(
                        pos[0] + button_width * 0.5,
                        pos[1] + button_height * 0.79,
                    ),
                    size=(0, 0),
                    scale=button_width * 0.003,
                    maxwidth=button_width * 0.7,
                    draw_controller=btn,
                    h_align='center',
                    v_align='center',
                )

                # Poke into this playlist and see if we can display some of
                # its maps.
                map_images = []
                try:
                    map_textures = []
                    map_texture_entries = []
                    if name == '__default__':
                        playlist = self._pvars.get_default_list_call()
                    else:
                        if (
                            name
                            not in appconfig[
                                self._pvars.config_name + ' Playlists'
                            ]
                        ):
                            print(
                                'NOT FOUND ERR',
                                appconfig[
                                    self._pvars.config_name + ' Playlists'
                                ],
                            )
                        playlist = appconfig[
                            self._pvars.config_name + ' Playlists'
                        ][name]
                    playlist = filter_playlist(
                        playlist,
                        self._sessiontype,
                        remove_unowned=False,
                        mark_unowned=True,
                        name=name,
                    )
                    for entry in playlist:
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
                        if len(map_textures) >= 6:
                            break

                    if len(map_textures) > 4:
                        img_rows = 3
                        img_columns = 2
                        scl = 0.33
                        h_offs_img = 30
                        v_offs_img = 126
                    elif len(map_textures) > 2:
                        img_rows = 2
                        img_columns = 2
                        scl = 0.35
                        h_offs_img = 24
                        v_offs_img = 110
                    elif len(map_textures) > 1:
                        img_rows = 2
                        img_columns = 1
                        scl = 0.5
                        h_offs_img = 47
                        v_offs_img = 105
                    else:
                        img_rows = 1
                        img_columns = 1
                        scl = 0.75
                        h_offs_img = 20
                        v_offs_img = 65

                    v = None
                    for row in range(img_rows):
                        for col in range(img_columns):
                            tex_index = row * img_columns + col
                            if tex_index < len(map_textures):
                                entry = map_texture_entries[tex_index]

                                owned = not (
                                    (
                                        'is_unowned_map' in entry
                                        and entry['is_unowned_map']
                                    )
                                    or (
                                        'is_unowned_game' in entry
                                        and entry['is_unowned_game']
                                    )
                                )

                                tex_name = map_textures[tex_index]
                                h = pos[0] + h_offs_img + scl * 250 * col
                                v = pos[1] + v_offs_img - scl * 130 * row
                                map_images.append(
                                    bui.imagewidget(
                                        parent=self._subcontainer,
                                        size=(scl * 250.0, scl * 125.0),
                                        position=(h, v),
                                        texture=bui.gettexture(tex_name),
                                        opacity=1.0 if owned else 0.25,
                                        draw_controller=btn,
                                        mesh_opaque=mesh_opaque,
                                        mesh_transparent=mesh_transparent,
                                        mask_texture=mask_tex,
                                    )
                                )
                                if not owned:
                                    bui.imagewidget(
                                        parent=self._subcontainer,
                                        size=(scl * 100.0, scl * 100.0),
                                        position=(h + scl * 75, v + scl * 10),
                                        texture=bui.gettexture('lock'),
                                        draw_controller=btn,
                                    )
                        if v is not None:
                            v -= scl * 130.0

                except Exception:
                    logging.exception('Error listing playlist maps.')

                if not map_images:
                    bui.textwidget(
                        parent=self._subcontainer,
                        text='???',
                        scale=1.5,
                        size=(0, 0),
                        color=(1, 1, 1, 0.5),
                        h_align='center',
                        v_align='center',
                        draw_controller=btn,
                        position=(
                            pos[0] + button_width * 0.5,
                            pos[1] + button_height * 0.5,
                        ),
                    )

                index += 1

                if index >= count:
                    break
            if index >= count:
                break
        self._customize_button = btn = bui.buttonwidget(
            parent=self._subcontainer,
            size=(100, 30),
            position=(34 + h_offs_bottom, 50),
            text_scale=0.6,
            label=bui.Lstr(resource='customizeText'),
            on_activate_call=self._on_customize_press,
            color=(0.54, 0.52, 0.67),
            textcolor=(0.7, 0.65, 0.7),
            autoselect=True,
        )
        bui.widget(edit=btn, show_buffer_top=22, show_buffer_bottom=28)
        self._restore_state()

    def on_play_options_window_run_game(self) -> None:
        """(internal)"""

        # No-op if we're not in control.
        if not self.main_window_has_control():
            # if not self._root_widget:
            return

        if self._playlist_select_context is not None:
            # Done doing a playlist selection; now back all the way out
            # of our selection windows to our stored starting point.
            if self._playlist_select_context.back_state is None:
                logging.error(
                    'No back state found'
                    ' after playlist select context completion.'
                )
            else:
                self.main_window_back_state = (
                    self._playlist_select_context.back_state
                )
            self.main_window_back()
        else:
            # Launching a regular game session; simply get our window
            # transitioning out.
            self.main_window_close(transition='out_left')

    def _on_playlist_select(self, playlist_name: str) -> None:
        self._selected_playlist = playlist_name

    def _update(self) -> None:
        # Make sure config exists.
        if self._config_name_full not in bui.app.config:
            bui.app.config[self._config_name_full] = {}

        cfg = bui.app.config[self._config_name_full]
        if cfg != self._last_config:
            self._last_config = copy.deepcopy(cfg)
            self._refresh()

    def _on_playlist_press(
        self, button: bui.Widget, playlist_name: str
    ) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playoptions import PlayOptionsWindow

        # Make sure the target playlist still exists.
        exists = (
            playlist_name == '__default__'
            or playlist_name in bui.app.config.get(self._config_name_full, {})
        )
        if not exists:
            return

        self._save_state()
        PlayOptionsWindow(
            sessiontype=self._sessiontype,
            scale_origin=button.get_screen_space_center(),
            playlist=playlist_name,
            delegate=self,
            playlist_select_context=self._playlist_select_context,
        )

    def _on_customize_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist.customizebrowser import (
            PlaylistCustomizeBrowserWindow,
        )

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            PlaylistCustomizeBrowserWindow(
                origin_widget=self._customize_button,
                sessiontype=self._sessiontype,
            )
        )

    def _on_back_press(self) -> None:
        # pylint: disable=cyclic-import
        # from bauiv1lib.play import PlayWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        # Store our selected playlist if that's changed.
        if self._selected_playlist is not None:
            prev_sel = bui.app.config.get(
                self._pvars.config_name + ' Playlist Selection'
            )
            if self._selected_playlist != prev_sel:
                cfg = bui.app.config
                cfg[self._pvars.config_name + ' Playlist Selection'] = (
                    self._selected_playlist
                )
                cfg.commit()

        self.main_window_back()

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._back_button:
                sel_name = 'Back'
            elif sel == self._scrollwidget:
                assert self._subcontainer is not None
                subsel = self._subcontainer.get_selected_child()
                if subsel == self._customize_button:
                    sel_name = 'Customize'
                else:
                    sel_name = 'Scroll'
            else:
                raise RuntimeError('Unrecognized selected widget.')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = sel_name
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self))
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'Scroll':
                sel = self._scrollwidget
            elif sel_name == 'Customize':
                sel = self._scrollwidget
                bui.containerwidget(
                    edit=self._subcontainer,
                    selected_child=self._customize_button,
                    visible_child=self._customize_button,
                )
            else:
                sel = self._scrollwidget
            bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)
