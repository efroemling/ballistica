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
"""Provides a window for configuring play options."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba
from bastd.ui import popup

if TYPE_CHECKING:
    from typing import Any, Type, Tuple, Optional, Union


class PlayOptionsWindow(popup.PopupWindow):
    """A popup window for configuring play options."""

    def __init__(self,
                 sessiontype: Type[ba.Session],
                 playlist: str,
                 scale_origin: Tuple[float, float],
                 delegate: Any = None):
        # FIXME: Tidy this up.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from ba.internal import (getclass, have_pro,
                                 get_default_teams_playlist,
                                 get_default_free_for_all_playlist,
                                 filter_playlist)
        from ba.internal import get_map_class
        from bastd.ui.playlist import PlaylistTypeVars

        self._r = 'gameListWindow'
        self._delegate = delegate
        self._pvars = PlaylistTypeVars(sessiontype)
        self._transitioning_out = False

        self._do_randomize_val = (ba.app.config.get(
            self._pvars.config_name + ' Playlist Randomize', 0))

        self._sessiontype = sessiontype
        self._playlist = playlist

        self._width = 500.0
        self._height = 330.0 - 50.0

        # In teams games, show the custom names/colors button.
        if self._sessiontype is ba.DualTeamSession:
            self._height += 50.0

        self._row_height = 45.0

        # Grab our maps to display.
        model_opaque = ba.getmodel('level_select_button_opaque')
        model_transparent = ba.getmodel('level_select_button_transparent')
        mask_tex = ba.gettexture('mapPreviewMask')

        # Poke into this playlist and see if we can display some of its maps.
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
                if self._sessiontype is ba.FreeForAllSession:
                    plst = get_default_free_for_all_playlist()
                elif self._sessiontype is ba.DualTeamSession:
                    plst = get_default_teams_playlist()
                else:
                    raise TypeError('unrecognized session-type: ' +
                                    str(self._sessiontype))
            else:
                try:
                    plst = ba.app.config[self._pvars.config_name +
                                         ' Playlists'][name]
                except Exception:
                    print('ERROR INFO: self._config_name is:',
                          self._pvars.config_name)
                    print(
                        'ERROR INFO: playlist names are:',
                        list(ba.app.config[self._pvars.config_name +
                                           ' Playlists'].keys()))
                    raise
            plst = filter_playlist(plst,
                                   self._sessiontype,
                                   remove_unowned=False,
                                   mark_unowned=True)
            game_count = len(plst)
            for entry in plst:
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
            ba.print_exception('Error listing playlist maps.')

        show_shuffle_check_box = game_count > 1

        if show_shuffle_check_box:
            self._height += 40

        # Creates our _root_widget.
        uiscale = ba.app.ui.uiscale
        scale = (1.69 if uiscale is ba.UIScale.SMALL else
                 1.1 if uiscale is ba.UIScale.MEDIUM else 0.85)
        super().__init__(position=scale_origin,
                         size=(self._width, self._height),
                         scale=scale)

        playlist_name: Union[str, ba.Lstr] = (self._pvars.default_list_name
                                              if playlist == '__default__' else
                                              playlist)
        self._title_text = ba.textwidget(parent=self.root_widget,
                                         position=(self._width * 0.5,
                                                   self._height - 89 + 51),
                                         size=(0, 0),
                                         text=playlist_name,
                                         scale=1.4,
                                         color=(1, 1, 1),
                                         maxwidth=self._width * 0.7,
                                         h_align='center',
                                         v_align='center')

        self._cancel_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(25, self._height - 53),
            size=(50, 50),
            scale=0.7,
            label='',
            color=(0.42, 0.73, 0.2),
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=ba.gettexture('crossOut'),
            iconscale=1.2)

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
                    owned = not (('is_unowned_map' in entry
                                  and entry['is_unowned_map']) or
                                 ('is_unowned_game' in entry
                                  and entry['is_unowned_game']))

                    if owned:
                        self._have_at_least_one_owned = True

                    try:
                        desc = getclass(entry['type'],
                                        subclassof=ba.GameActivity
                                        ).get_settings_display_string(entry)
                        if not owned:
                            desc = ba.Lstr(
                                value='${DESC}\n${UNLOCK}',
                                subs=[
                                    ('${DESC}', desc),
                                    ('${UNLOCK}',
                                     ba.Lstr(
                                         resource='unlockThisInTheStoreText'))
                                ])
                        desc_color = (0, 1, 0) if owned else (1, 0, 0)
                    except Exception:
                        desc = ba.Lstr(value='(invalid)')
                        desc_color = (1, 0, 0)

                    btn = ba.buttonwidget(
                        parent=self.root_widget,
                        size=(scl * 240.0, scl * 120.0),
                        position=(h, v),
                        texture=ba.gettexture(tex_name if owned else 'empty'),
                        model_opaque=model_opaque if owned else None,
                        on_activate_call=ba.Call(ba.screenmessage, desc,
                                                 desc_color),
                        label='',
                        color=(1, 1, 1),
                        autoselect=True,
                        extra_touch_border_scale=0.0,
                        model_transparent=model_transparent if owned else None,
                        mask_texture=mask_tex if owned else None)
                    if row == 0 and col == 0:
                        ba.widget(edit=self._cancel_button, down_widget=btn)
                    if row == rows - 1:
                        bottom_row_buttons.append(btn)
                    if not owned:

                        # Ewww; buttons don't currently have alpha so in this
                        # case we draw an image over our button with an empty
                        # texture on it.
                        ba.imagewidget(parent=self.root_widget,
                                       size=(scl * 260.0, scl * 130.0),
                                       position=(h - 10.0 * scl,
                                                 v - 4.0 * scl),
                                       draw_controller=btn,
                                       color=(1, 1, 1),
                                       texture=ba.gettexture(tex_name),
                                       model_opaque=model_opaque,
                                       opacity=0.25,
                                       model_transparent=model_transparent,
                                       mask_texture=mask_tex)

                        ba.imagewidget(parent=self.root_widget,
                                       size=(scl * 100, scl * 100),
                                       draw_controller=btn,
                                       position=(h + scl * 70, v + scl * 10),
                                       texture=ba.gettexture('lock'))

        # Team names/colors.
        self._custom_colors_names_button: Optional[ba.Widget]
        if self._sessiontype is ba.DualTeamSession:
            y_offs = 50 if show_shuffle_check_box else 0
            self._custom_colors_names_button = ba.buttonwidget(
                parent=self.root_widget,
                position=(100, 200 + y_offs),
                size=(290, 35),
                on_activate_call=ba.WeakCall(self._custom_colors_names_press),
                autoselect=True,
                textcolor=(0.8, 0.8, 0.8),
                label=ba.Lstr(resource='teamNamesColorText'))
            if not have_pro():
                ba.imagewidget(
                    parent=self.root_widget,
                    size=(30, 30),
                    position=(95, 202 + y_offs),
                    texture=ba.gettexture('lock'),
                    draw_controller=self._custom_colors_names_button)
        else:
            self._custom_colors_names_button = None

        # Shuffle.
        def _cb_callback(val: bool) -> None:
            self._do_randomize_val = val
            cfg = ba.app.config
            cfg[self._pvars.config_name +
                ' Playlist Randomize'] = self._do_randomize_val
            cfg.commit()

        if show_shuffle_check_box:
            self._shuffle_check_box = ba.checkboxwidget(
                parent=self.root_widget,
                position=(110, 200),
                scale=1.0,
                size=(250, 30),
                autoselect=True,
                text=ba.Lstr(resource=self._r + '.shuffleGameOrderText'),
                maxwidth=300,
                textcolor=(0.8, 0.8, 0.8),
                value=self._do_randomize_val,
                on_value_change_call=_cb_callback)

        # Show tutorial.
        show_tutorial = bool(ba.app.config.get('Show Tutorial', True))

        def _cb_callback_2(val: bool) -> None:
            cfg = ba.app.config
            cfg['Show Tutorial'] = val
            cfg.commit()

        self._show_tutorial_check_box = ba.checkboxwidget(
            parent=self.root_widget,
            position=(110, 151),
            scale=1.0,
            size=(250, 30),
            autoselect=True,
            text=ba.Lstr(resource=self._r + '.showTutorialText'),
            maxwidth=300,
            textcolor=(0.8, 0.8, 0.8),
            value=show_tutorial,
            on_value_change_call=_cb_callback_2)

        # Grumble: current autoselect doesn't do a very good job
        # with checkboxes.
        if self._custom_colors_names_button is not None:
            for btn in bottom_row_buttons:
                ba.widget(edit=btn,
                          down_widget=self._custom_colors_names_button)
            if show_shuffle_check_box:
                ba.widget(edit=self._custom_colors_names_button,
                          down_widget=self._shuffle_check_box)
                ba.widget(edit=self._shuffle_check_box,
                          up_widget=self._custom_colors_names_button)
            else:
                ba.widget(edit=self._custom_colors_names_button,
                          down_widget=self._show_tutorial_check_box)
                ba.widget(edit=self._show_tutorial_check_box,
                          up_widget=self._custom_colors_names_button)

        self._play_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(70, 44),
            size=(200, 45),
            scale=1.8,
            text_res_scale=1.5,
            on_activate_call=self._on_play_press,
            autoselect=True,
            label=ba.Lstr(resource='playText'))

        ba.widget(edit=self._play_button,
                  up_widget=self._show_tutorial_check_box)

        ba.containerwidget(edit=self.root_widget,
                           start_button=self._play_button,
                           cancel_button=self._cancel_button,
                           selected_child=self._play_button)

        # Update now and once per second.
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      timetype=ba.TimeType.REAL,
                                      repeat=True)
        self._update()

    def _custom_colors_names_press(self) -> None:
        from ba.internal import have_pro
        from bastd.ui import account as accountui
        from bastd.ui import teamnamescolors
        from bastd.ui import purchase
        if not have_pro():
            if _ba.get_account_state() != 'signed_in':
                accountui.show_sign_in_prompt()
            else:
                purchase.PurchaseWindow(items=['pro'])
            self._transition_out()
            return
        assert self._custom_colors_names_button
        teamnamescolors.TeamNamesColorsWindow(
            scale_origin=self._custom_colors_names_button.
            get_screen_space_center())

    def _does_target_playlist_exist(self) -> bool:
        if self._playlist == '__default__':
            return True
        return self._playlist in ba.app.config.get(
            self._pvars.config_name + ' Playlists', {})

    def _update(self) -> None:
        # All we do here is make sure our targeted playlist still exists,
        # and close ourself if not.
        if not self._does_target_playlist_exist():
            self._transition_out()

    def _transition_out(self, transition: str = 'out_scale') -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition=transition)

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _on_play_press(self) -> None:

        # Disallow if our playlist has disappeared.
        if not self._does_target_playlist_exist():
            return

        # Disallow if we have no unlocked games.
        if not self._have_at_least_one_owned:
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource='playlistNoValidGamesErrorText'),
                             color=(1, 0, 0))
            return

        cfg = ba.app.config
        cfg[self._pvars.config_name + ' Playlist Selection'] = self._playlist
        cfg.commit()
        _ba.fade_screen(False, endcall=self._run_selected_playlist)
        _ba.lock_all_input()
        self._transition_out(transition='out_left')
        if self._delegate is not None:
            self._delegate.on_play_options_window_run_game()

    def _run_selected_playlist(self) -> None:
        _ba.unlock_all_input()
        try:
            _ba.new_host_session(self._sessiontype)
        except Exception:
            from bastd import mainmenu
            ba.print_exception('exception running session', self._sessiontype)

            # Drop back into a main menu session.
            _ba.new_host_session(mainmenu.MainMenuSession)
