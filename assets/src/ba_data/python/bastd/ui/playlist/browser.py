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
"""Provides a window for browsing and launching game playlists."""

from __future__ import annotations

import copy
import math
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Type, Optional, Tuple, Union


class PlaylistBrowserWindow(ba.Window):
    """Window for starting teams games."""

    def __init__(self,
                 sessiontype: Type[ba.Session],
                 transition: Optional[str] = 'in_right',
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        from bastd.ui.playlist import PlaylistTypeVars

        # If they provided an origin-widget, scale up from that.
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        # Store state for when we exit the next game.
        if issubclass(sessiontype, ba.DualTeamSession):
            ba.app.ui.set_main_menu_location('Team Game Select')
            ba.set_analytics_screen('Teams Window')
        elif issubclass(sessiontype, ba.FreeForAllSession):
            ba.app.ui.set_main_menu_location('Free-for-All Game Select')
            ba.set_analytics_screen('FreeForAll Window')
        else:
            raise TypeError(f'Invalid sessiontype: {sessiontype}.')
        self._pvars = PlaylistTypeVars(sessiontype)

        self._sessiontype = sessiontype

        self._customize_button: Optional[ba.Widget] = None
        self._sub_width: Optional[float] = None
        self._sub_height: Optional[float] = None

        # On new installations, go ahead and create a few playlists
        # besides the hard-coded default one:
        if not _ba.get_account_misc_val('madeStandardPlaylists', False):
            _ba.add_transaction({
                'type':
                    'ADD_PLAYLIST',
                'playlistType':
                    'Free-for-All',
                'playlistName':
                    ba.Lstr(resource='singleGamePlaylistNameText'
                            ).evaluate().replace(
                                '${GAME}',
                                ba.Lstr(translate=('gameNames',
                                                   'Death Match')).evaluate()),
                'playlist': [
                    {
                        'type': 'bs_death_match.DeathMatchGame',
                        'settings': {
                            'Epic Mode': False,
                            'Kills to Win Per Player': 10,
                            'Respawn Times': 1.0,
                            'Time Limit': 300,
                            'map': 'Doom Shroom'
                        }
                    },
                    {
                        'type': 'bs_death_match.DeathMatchGame',
                        'settings': {
                            'Epic Mode': False,
                            'Kills to Win Per Player': 10,
                            'Respawn Times': 1.0,
                            'Time Limit': 300,
                            'map': 'Crag Castle'
                        }
                    },
                ]
            })
            _ba.add_transaction({
                'type':
                    'ADD_PLAYLIST',
                'playlistType':
                    'Team Tournament',
                'playlistName':
                    ba.Lstr(
                        resource='singleGamePlaylistNameText'
                    ).evaluate().replace(
                        '${GAME}',
                        ba.Lstr(translate=('gameNames',
                                           'Capture the Flag')).evaluate()),
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
                            'Epic Mode': False
                        }
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
                            'Epic Mode': False
                        }
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
                            'Epic Mode': False
                        }
                    },
                ]
            })
            _ba.add_transaction({
                'type':
                    'ADD_PLAYLIST',
                'playlistType':
                    'Team Tournament',
                'playlistName':
                    ba.Lstr(translate=('playlistNames', 'Just Sports')
                            ).evaluate(),
                'playlist': [
                    {
                        'type': 'bs_hockey.HockeyGame',
                        'settings': {
                            'Time Limit': 0,
                            'map': 'Hockey Stadium',
                            'Score to Win': 1,
                            'Respawn Times': 1.0
                        }
                    },
                    {
                        'type': 'bs_football.FootballTeamGame',
                        'settings': {
                            'Time Limit': 0,
                            'map': 'Football Stadium',
                            'Score to Win': 21,
                            'Respawn Times': 1.0
                        }
                    },
                ]
            })
            _ba.add_transaction({
                'type':
                    'ADD_PLAYLIST',
                'playlistType':
                    'Free-for-All',
                'playlistName':
                    ba.Lstr(translate=('playlistNames', 'Just Epic')
                            ).evaluate(),
                'playlist': [{
                    'type': 'bs_elimination.EliminationGame',
                    'settings': {
                        'Time Limit': 120,
                        'map': 'Tip Top',
                        'Respawn Times': 1.0,
                        'Lives Per Player': 1,
                        'Epic Mode': 1
                    }
                }]
            })
            _ba.add_transaction({
                'type': 'SET_MISC_VAL',
                'name': 'madeStandardPlaylists',
                'value': True
            })
            _ba.run_transactions()

        # Get the current selection (if any).
        self._selected_playlist = ba.app.config.get(self._pvars.config_name +
                                                    ' Playlist Selection')

        uiscale = ba.app.ui.uiscale
        self._width = 900 if uiscale is ba.UIScale.SMALL else 800
        x_inset = 50 if uiscale is ba.UIScale.SMALL else 0
        self._height = (480 if uiscale is ba.UIScale.SMALL else
                        510 if uiscale is ba.UIScale.MEDIUM else 580)

        top_extra = 20 if uiscale is ba.UIScale.SMALL else 0

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            toolbar_visibility='menu_full',
            scale_origin_stack_offset=scale_origin,
            scale=(1.69 if uiscale is ba.UIScale.SMALL else
                   1.05 if uiscale is ba.UIScale.MEDIUM else 0.9),
            stack_offset=(0, -26) if uiscale is ba.UIScale.SMALL else (0, 0)))

        self._back_button: Optional[ba.Widget] = ba.buttonwidget(
            parent=self._root_widget,
            position=(59 + x_inset, self._height - 70),
            size=(120, 60),
            scale=1.0,
            on_activate_call=self._on_back_press,
            autoselect=True,
            label=ba.Lstr(resource='backText'),
            button_type='back')
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._back_button)
        txt = self._title_text = ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 41),
            size=(0, 0),
            text=self._pvars.window_title_name,
            scale=1.3,
            res_scale=1.5,
            color=ba.app.ui.heading_color,
            h_align='center',
            v_align='center')
        if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
            ba.textwidget(edit=txt, text='')

        ba.buttonwidget(edit=self._back_button,
                        button_type='backSmall',
                        size=(60, 54),
                        position=(59 + x_inset, self._height - 67),
                        label=ba.charstr(ba.SpecialChar.BACK))

        if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
            self._back_button.delete()
            self._back_button = None
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._on_back_press)
            scroll_offs = 33
        else:
            scroll_offs = 0
        self._scroll_width = self._width - (100 + 2 * x_inset)
        self._scroll_height = (self._height -
                               (146 if uiscale is ba.UIScale.SMALL
                                and ba.app.ui.use_toolbars else 136))
        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            position=((self._width - self._scroll_width) * 0.5,
                      65 + scroll_offs))
        ba.containerwidget(edit=self._scrollwidget, claims_left_right=True)
        self._subcontainer: Optional[ba.Widget] = None
        self._config_name_full = self._pvars.config_name + ' Playlists'
        self._last_config = None

        # Update now and once per second.
        # (this should do our initial refresh)
        self._update()
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      timetype=ba.TimeType.REAL,
                                      repeat=True)

    def _refresh(self) -> None:
        # FIXME: Should tidy this up.
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-nested-blocks
        from ba.internal import (get_map_class,
                                 get_default_free_for_all_playlist,
                                 get_default_teams_playlist, filter_playlist)
        if not self._root_widget:
            return
        if self._subcontainer is not None:
            self._save_state()
            self._subcontainer.delete()

        # Make sure config exists.
        if self._config_name_full not in ba.app.config:
            ba.app.config[self._config_name_full] = {}

        items = list(ba.app.config[self._config_name_full].items())

        # Make sure everything is unicode.
        items = [(i[0].decode(), i[1]) if not isinstance(i[0], str) else i
                 for i in items]

        items.sort(key=lambda x2: x2[0].lower())
        items = [['__default__', None]] + items  # default is always first

        count = len(items)
        columns = 3
        rows = int(math.ceil(float(count) / columns))
        button_width = 230
        button_height = 230
        button_buffer_h = -3
        button_buffer_v = 0

        self._sub_width = self._scroll_width
        self._sub_height = 40 + rows * (button_height +
                                        2 * button_buffer_v) + 90
        assert self._sub_width is not None
        assert self._sub_height is not None
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False)

        children = self._subcontainer.get_children()
        for child in children:
            child.delete()

        ba.textwidget(parent=self._subcontainer,
                      text=ba.Lstr(resource='playlistsText'),
                      position=(40, self._sub_height - 26),
                      size=(0, 0),
                      scale=1.0,
                      maxwidth=400,
                      color=ba.app.ui.title_color,
                      h_align='left',
                      v_align='center')

        index = 0
        appconfig = ba.app.config

        model_opaque = ba.getmodel('level_select_button_opaque')
        model_transparent = ba.getmodel('level_select_button_transparent')
        mask_tex = ba.gettexture('mapPreviewMask')

        h_offs = 225 if count == 1 else 115 if count == 2 else 0
        h_offs_bottom = 0

        uiscale = ba.app.ui.uiscale
        for y in range(rows):
            for x in range(columns):
                name = items[index][0]
                assert name is not None
                pos = (x * (button_width + 2 * button_buffer_h) +
                       button_buffer_h + 8 + h_offs, self._sub_height - 47 -
                       (y + 1) * (button_height + 2 * button_buffer_v))
                btn = ba.buttonwidget(parent=self._subcontainer,
                                      button_type='square',
                                      size=(button_width, button_height),
                                      autoselect=True,
                                      label='',
                                      position=pos)

                if (x == 0 and ba.app.ui.use_toolbars
                        and uiscale is ba.UIScale.SMALL):
                    ba.widget(
                        edit=btn,
                        left_widget=_ba.get_special_widget('back_button'))
                if (x == columns - 1 and ba.app.ui.use_toolbars
                        and uiscale is ba.UIScale.SMALL):
                    ba.widget(
                        edit=btn,
                        right_widget=_ba.get_special_widget('party_button'))
                ba.buttonwidget(
                    edit=btn,
                    on_activate_call=ba.Call(self._on_playlist_press, btn,
                                             name),
                    on_select_call=ba.Call(self._on_playlist_select, name))
                ba.widget(edit=btn, show_buffer_top=50, show_buffer_bottom=50)

                if self._selected_playlist == name:
                    ba.containerwidget(edit=self._subcontainer,
                                       selected_child=btn,
                                       visible_child=btn)

                if self._back_button is not None:
                    if y == 0:
                        ba.widget(edit=btn, up_widget=self._back_button)
                    if x == 0:
                        ba.widget(edit=btn, left_widget=self._back_button)

                print_name: Optional[Union[str, ba.Lstr]]
                if name == '__default__':
                    print_name = self._pvars.default_list_name
                else:
                    print_name = name
                ba.textwidget(parent=self._subcontainer,
                              text=print_name,
                              position=(pos[0] + button_width * 0.5,
                                        pos[1] + button_height * 0.79),
                              size=(0, 0),
                              scale=button_width * 0.003,
                              maxwidth=button_width * 0.7,
                              draw_controller=btn,
                              h_align='center',
                              v_align='center')

                # Poke into this playlist and see if we can display some of
                # its maps.
                map_images = []
                try:
                    map_textures = []
                    map_texture_entries = []
                    if name == '__default__':
                        if self._sessiontype is ba.FreeForAllSession:
                            playlist = (get_default_free_for_all_playlist())
                        elif self._sessiontype is ba.DualTeamSession:
                            playlist = get_default_teams_playlist()
                        else:
                            raise Exception('unrecognized session-type: ' +
                                            str(self._sessiontype))
                    else:
                        if name not in appconfig[self._pvars.config_name +
                                                 ' Playlists']:
                            print(
                                'NOT FOUND ERR',
                                appconfig[self._pvars.config_name +
                                          ' Playlists'])
                        playlist = appconfig[self._pvars.config_name +
                                             ' Playlists'][name]
                    playlist = filter_playlist(playlist,
                                               self._sessiontype,
                                               remove_unowned=False,
                                               mark_unowned=True)
                    for entry in playlist:
                        mapname = entry['settings']['map']
                        maptype: Optional[Type[ba.Map]]
                        try:
                            maptype = get_map_class(mapname)
                        except ba.NotFoundError:
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

                                owned = not (('is_unowned_map' in entry
                                              and entry['is_unowned_map']) or
                                             ('is_unowned_game' in entry
                                              and entry['is_unowned_game']))

                                tex_name = map_textures[tex_index]
                                h = pos[0] + h_offs_img + scl * 250 * col
                                v = pos[1] + v_offs_img - scl * 130 * row
                                map_images.append(
                                    ba.imagewidget(
                                        parent=self._subcontainer,
                                        size=(scl * 250.0, scl * 125.0),
                                        position=(h, v),
                                        texture=ba.gettexture(tex_name),
                                        opacity=1.0 if owned else 0.25,
                                        draw_controller=btn,
                                        model_opaque=model_opaque,
                                        model_transparent=model_transparent,
                                        mask_texture=mask_tex))
                                if not owned:
                                    ba.imagewidget(
                                        parent=self._subcontainer,
                                        size=(scl * 100.0, scl * 100.0),
                                        position=(h + scl * 75, v + scl * 10),
                                        texture=ba.gettexture('lock'),
                                        draw_controller=btn)
                        if v is not None:
                            v -= scl * 130.0

                except Exception:
                    ba.print_exception('Error listing playlist maps.')

                if not map_images:
                    ba.textwidget(parent=self._subcontainer,
                                  text='???',
                                  scale=1.5,
                                  size=(0, 0),
                                  color=(1, 1, 1, 0.5),
                                  h_align='center',
                                  v_align='center',
                                  draw_controller=btn,
                                  position=(pos[0] + button_width * 0.5,
                                            pos[1] + button_height * 0.5))

                index += 1

                if index >= count:
                    break
            if index >= count:
                break
        self._customize_button = btn = ba.buttonwidget(
            parent=self._subcontainer,
            size=(100, 30),
            position=(34 + h_offs_bottom, 50),
            text_scale=0.6,
            label=ba.Lstr(resource='customizeText'),
            on_activate_call=self._on_customize_press,
            color=(0.54, 0.52, 0.67),
            textcolor=(0.7, 0.65, 0.7),
            autoselect=True)
        ba.widget(edit=btn, show_buffer_top=22, show_buffer_bottom=28)
        self._restore_state()

    def on_play_options_window_run_game(self) -> None:
        """(internal)"""
        if not self._root_widget:
            return
        ba.containerwidget(edit=self._root_widget, transition='out_left')

    def _on_playlist_select(self, playlist_name: str) -> None:
        self._selected_playlist = playlist_name

    def _update(self) -> None:

        # make sure config exists
        if self._config_name_full not in ba.app.config:
            ba.app.config[self._config_name_full] = {}

        cfg = ba.app.config[self._config_name_full]
        if cfg != self._last_config:
            self._last_config = copy.deepcopy(cfg)
            self._refresh()

    def _on_playlist_press(self, button: ba.Widget,
                           playlist_name: str) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.playoptions import PlayOptionsWindow

        # Make sure the target playlist still exists.
        exists = (playlist_name == '__default__'
                  or playlist_name in ba.app.config.get(
                      self._config_name_full, {}))
        if not exists:
            return

        self._save_state()
        PlayOptionsWindow(sessiontype=self._sessiontype,
                          scale_origin=button.get_screen_space_center(),
                          playlist=playlist_name,
                          delegate=self)

    def _on_customize_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.playlist.customizebrowser import (
            PlaylistCustomizeBrowserWindow)
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            PlaylistCustomizeBrowserWindow(
                origin_widget=self._customize_button,
                sessiontype=self._sessiontype).get_root_widget())

    def _on_back_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.play import PlayWindow

        # Store our selected playlist if that's changed.
        if self._selected_playlist is not None:
            prev_sel = ba.app.config.get(self._pvars.config_name +
                                         ' Playlist Selection')
            if self._selected_playlist != prev_sel:
                cfg = ba.app.config
                cfg[self._pvars.config_name +
                    ' Playlist Selection'] = self._selected_playlist
                cfg.commit()

        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            PlayWindow(transition='in_left').get_root_widget())

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
                raise Exception('unrecognized selected widget')
            ba.app.ui.window_states[self.__class__.__name__] = sel_name
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(self.__class__.__name__)
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'Scroll':
                sel = self._scrollwidget
            elif sel_name == 'Customize':
                sel = self._scrollwidget
                ba.containerwidget(edit=self._subcontainer,
                                   selected_child=self._customize_button,
                                   visible_child=self._customize_button)
            else:
                sel = self._scrollwidget
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')
