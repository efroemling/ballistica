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
"""UI functionality for running the game in kiosk mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Optional


class KioskWindow(ba.Window):
    """Kiosk mode window."""

    def __init__(self, transition: str = 'in_right'):
        # pylint: disable=too-many-locals, too-many-statements
        from bastd.ui.confirm import QuitWindow
        self._width = 720.0
        self._height = 340.0

        def _do_cancel() -> None:
            QuitWindow(swish=True, back=True)

        super().__init__(
            root_widget=ba.containerwidget(size=(self._width, self._height),
                                           transition=transition,
                                           on_cancel_call=_do_cancel,
                                           background=False,
                                           stack_offset=(0, -130)))

        self._r = 'kioskWindow'

        self._show_multiplayer = False

        # Let's reset all random player names every time we hit the main menu.
        _ba.reset_random_player_names()

        # Reset achievements too (at least locally).
        ba.app.config['Achievements'] = {}

        t_delay_base = 0.0
        t_delay_scale = 0.0
        if not ba.app.did_menu_intro:
            t_delay_base = 1.0
            t_delay_scale = 1.0

        model_opaque = ba.getmodel('level_select_button_opaque')
        model_transparent = ba.getmodel('level_select_button_transparent')
        mask_tex = ba.gettexture('mapPreviewMask')

        y_extra = 130.0 + (0.0 if self._show_multiplayer else -130.0)
        b_width = 250.0
        b_height = 200.0
        b_space = 280.0
        b_v = 80.0 + y_extra
        label_height = 130.0 + y_extra
        img_width = 180.0
        img_v = 158.0 + y_extra

        if self._show_multiplayer:
            tdelay = t_delay_base + t_delay_scale * 1.3
            ba.textwidget(
                parent=self._root_widget,
                size=(0, 0),
                position=(self._width * 0.5, self._height + y_extra - 44),
                transition_delay=tdelay,
                text=ba.Lstr(resource=self._r + '.singlePlayerExamplesText'),
                flatness=1.0,
                scale=1.2,
                h_align='center',
                v_align='center',
                shadow=1.0)
        else:
            tdelay = t_delay_base + t_delay_scale * 0.7
            ba.textwidget(
                parent=self._root_widget,
                size=(0, 0),
                position=(self._width * 0.5, self._height + y_extra - 34),
                transition_delay=tdelay,
                text=ba.Lstr(resource='demoText',
                             fallback_resource='mainMenu.demoMenuText'),
                flatness=1.0,
                scale=1.2,
                h_align='center',
                v_align='center',
                shadow=1.0)
        h = self._width * 0.5 - b_space
        tdelay = t_delay_base + t_delay_scale * 0.7
        self._b1 = btn = ba.buttonwidget(parent=self._root_widget,
                                         autoselect=True,
                                         size=(b_width, b_height),
                                         on_activate_call=ba.Call(
                                             self._do_game, 'easy'),
                                         transition_delay=tdelay,
                                         position=(h - b_width * 0.5, b_v),
                                         label='',
                                         button_type='square')
        ba.textwidget(parent=self._root_widget,
                      draw_controller=btn,
                      transition_delay=tdelay,
                      size=(0, 0),
                      position=(h, label_height),
                      maxwidth=b_width * 0.7,
                      text=ba.Lstr(resource=self._r + '.easyText'),
                      scale=1.3,
                      h_align='center',
                      v_align='center')
        ba.imagewidget(parent=self._root_widget,
                       draw_controller=btn,
                       size=(img_width, 0.5 * img_width),
                       transition_delay=tdelay,
                       position=(h - img_width * 0.5, img_v),
                       texture=ba.gettexture('doomShroomPreview'),
                       model_opaque=model_opaque,
                       model_transparent=model_transparent,
                       mask_texture=mask_tex)
        h = self._width * 0.5
        tdelay = t_delay_base + t_delay_scale * 0.65
        self._b2 = btn = ba.buttonwidget(parent=self._root_widget,
                                         autoselect=True,
                                         size=(b_width, b_height),
                                         on_activate_call=ba.Call(
                                             self._do_game, 'medium'),
                                         position=(h - b_width * 0.5, b_v),
                                         label='',
                                         button_type='square',
                                         transition_delay=tdelay)
        ba.textwidget(parent=self._root_widget,
                      draw_controller=btn,
                      transition_delay=tdelay,
                      size=(0, 0),
                      position=(h, label_height),
                      maxwidth=b_width * 0.7,
                      text=ba.Lstr(resource=self._r + '.mediumText'),
                      scale=1.3,
                      h_align='center',
                      v_align='center')
        ba.imagewidget(parent=self._root_widget,
                       draw_controller=btn,
                       size=(img_width, 0.5 * img_width),
                       transition_delay=tdelay,
                       position=(h - img_width * 0.5, img_v),
                       texture=ba.gettexture('footballStadiumPreview'),
                       model_opaque=model_opaque,
                       model_transparent=model_transparent,
                       mask_texture=mask_tex)
        h = self._width * 0.5 + b_space
        tdelay = t_delay_base + t_delay_scale * 0.6
        self._b3 = btn = ba.buttonwidget(parent=self._root_widget,
                                         autoselect=True,
                                         size=(b_width, b_height),
                                         on_activate_call=ba.Call(
                                             self._do_game, 'hard'),
                                         transition_delay=tdelay,
                                         position=(h - b_width * 0.5, b_v),
                                         label='',
                                         button_type='square')
        ba.textwidget(parent=self._root_widget,
                      draw_controller=btn,
                      transition_delay=tdelay,
                      size=(0, 0),
                      position=(h, label_height),
                      maxwidth=b_width * 0.7,
                      text='Hard',
                      scale=1.3,
                      h_align='center',
                      v_align='center')
        ba.imagewidget(parent=self._root_widget,
                       draw_controller=btn,
                       transition_delay=tdelay,
                       size=(img_width, 0.5 * img_width),
                       position=(h - img_width * 0.5, img_v),
                       texture=ba.gettexture('courtyardPreview'),
                       model_opaque=model_opaque,
                       model_transparent=model_transparent,
                       mask_texture=mask_tex)
        if not ba.app.did_menu_intro:
            ba.app.did_menu_intro = True

        self._b4: Optional[ba.Widget]
        self._b5: Optional[ba.Widget]
        self._b6: Optional[ba.Widget]

        if bool(False):
            ba.textwidget(
                parent=self._root_widget,
                size=(0, 0),
                position=(self._width * 0.5, self._height + y_extra - 44),
                transition_delay=tdelay,
                text=ba.Lstr(resource=self._r + '.versusExamplesText'),
                flatness=1.0,
                scale=1.2,
                h_align='center',
                v_align='center',
                shadow=1.0)
            h = self._width * 0.5 - b_space
            tdelay = t_delay_base + t_delay_scale * 0.7
            self._b4 = btn = ba.buttonwidget(parent=self._root_widget,
                                             autoselect=True,
                                             size=(b_width, b_height),
                                             on_activate_call=ba.Call(
                                                 self._do_game, 'ctf'),
                                             transition_delay=tdelay,
                                             position=(h - b_width * 0.5, b_v),
                                             label='',
                                             button_type='square')
            ba.textwidget(parent=self._root_widget,
                          draw_controller=btn,
                          transition_delay=tdelay,
                          size=(0, 0),
                          position=(h, label_height),
                          maxwidth=b_width * 0.7,
                          text=ba.Lstr(translate=('gameNames',
                                                  'Capture the Flag')),
                          scale=1.3,
                          h_align='center',
                          v_align='center')
            ba.imagewidget(parent=self._root_widget,
                           draw_controller=btn,
                           size=(img_width, 0.5 * img_width),
                           transition_delay=tdelay,
                           position=(h - img_width * 0.5, img_v),
                           texture=ba.gettexture('bridgitPreview'),
                           model_opaque=model_opaque,
                           model_transparent=model_transparent,
                           mask_texture=mask_tex)

            h = self._width * 0.5
            tdelay = t_delay_base + t_delay_scale * 0.65
            self._b5 = btn = ba.buttonwidget(parent=self._root_widget,
                                             autoselect=True,
                                             size=(b_width, b_height),
                                             on_activate_call=ba.Call(
                                                 self._do_game, 'hockey'),
                                             position=(h - b_width * 0.5, b_v),
                                             label='',
                                             button_type='square',
                                             transition_delay=tdelay)
            ba.textwidget(parent=self._root_widget,
                          draw_controller=btn,
                          transition_delay=tdelay,
                          size=(0, 0),
                          position=(h, label_height),
                          maxwidth=b_width * 0.7,
                          text=ba.Lstr(translate=('gameNames', 'Hockey')),
                          scale=1.3,
                          h_align='center',
                          v_align='center')
            ba.imagewidget(parent=self._root_widget,
                           draw_controller=btn,
                           size=(img_width, 0.5 * img_width),
                           transition_delay=tdelay,
                           position=(h - img_width * 0.5, img_v),
                           texture=ba.gettexture('hockeyStadiumPreview'),
                           model_opaque=model_opaque,
                           model_transparent=model_transparent,
                           mask_texture=mask_tex)
            h = self._width * 0.5 + b_space
            tdelay = t_delay_base + t_delay_scale * 0.6
            self._b6 = btn = ba.buttonwidget(parent=self._root_widget,
                                             autoselect=True,
                                             size=(b_width, b_height),
                                             on_activate_call=ba.Call(
                                                 self._do_game, 'epic'),
                                             transition_delay=tdelay,
                                             position=(h - b_width * 0.5, b_v),
                                             label='',
                                             button_type='square')
            ba.textwidget(parent=self._root_widget,
                          draw_controller=btn,
                          transition_delay=tdelay,
                          size=(0, 0),
                          position=(h, label_height),
                          maxwidth=b_width * 0.7,
                          text=ba.Lstr(resource=self._r + '.epicModeText'),
                          scale=1.3,
                          h_align='center',
                          v_align='center')
            ba.imagewidget(parent=self._root_widget,
                           draw_controller=btn,
                           transition_delay=tdelay,
                           size=(img_width, 0.5 * img_width),
                           position=(h - img_width * 0.5, img_v),
                           texture=ba.gettexture('tipTopPreview'),
                           model_opaque=model_opaque,
                           model_transparent=model_transparent,
                           mask_texture=mask_tex)
        else:
            self._b4 = self._b5 = self._b6 = None

        self._b7: Optional[ba.Widget]
        uiscale = ba.app.ui.uiscale
        if bool(False):
            self._b7 = ba.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                size=(b_width, 50),
                color=(0.45, 0.55, 0.45),
                textcolor=(0.7, 0.8, 0.7),
                scale=0.5,
                position=((self._width * 0.5 - 37.5,
                           y_extra + 120) if not self._show_multiplayer else
                          (self._width + 100, y_extra +
                           (140 if uiscale is ba.UIScale.SMALL else 120))),
                transition_delay=tdelay,
                label=ba.Lstr(resource=self._r + '.fullMenuText'),
                on_activate_call=self._do_full_menu)
        else:
            self._b7 = None
        self._restore_state()
        self._update()
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      timetype=ba.TimeType.REAL,
                                      repeat=True)

    def _restore_state(self) -> None:
        sel_name = ba.app.ui.window_states.get(self.__class__.__name__)
        sel: Optional[ba.Widget]
        if sel_name == 'b1':
            sel = self._b1
        elif sel_name == 'b2':
            sel = self._b2
        elif sel_name == 'b3':
            sel = self._b3
        elif sel_name == 'b4':
            sel = self._b4
        elif sel_name == 'b5':
            sel = self._b5
        elif sel_name == 'b6':
            sel = self._b6
        elif sel_name == 'b7':
            sel = self._b7
        else:
            sel = self._b1
        if sel:
            ba.containerwidget(edit=self._root_widget, selected_child=sel)

    def _save_state(self) -> None:
        sel = self._root_widget.get_selected_child()
        if sel == self._b1:
            sel_name = 'b1'
        elif sel == self._b2:
            sel_name = 'b2'
        elif sel == self._b3:
            sel_name = 'b3'
        elif sel == self._b4:
            sel_name = 'b4'
        elif sel == self._b5:
            sel_name = 'b5'
        elif sel == self._b6:
            sel_name = 'b6'
        elif sel == self._b7:
            sel_name = 'b7'
        else:
            sel_name = 'b1'
        ba.app.ui.window_states[self.__class__.__name__] = sel_name

    def _update(self) -> None:
        # Kiosk-mode is designed to be used signed-out... try for force
        # the issue.
        if _ba.get_account_state() == 'signed_in':
            # _bs.sign_out()
            # FIXME: Try to delete player profiles here too.
            pass
        else:
            # Also make sure there's no player profiles.
            appconfig = ba.app.config
            appconfig['Player Profiles'] = {}

    def _do_game(self, mode: str) -> None:
        self._save_state()
        if mode in ['epic', 'ctf', 'hockey']:
            appconfig = ba.app.config
            if 'Team Tournament Playlists' not in appconfig:
                appconfig['Team Tournament Playlists'] = {}
            if 'Free-for-All Playlists' not in appconfig:
                appconfig['Free-for-All Playlists'] = {}
            appconfig['Show Tutorial'] = False
            if mode == 'epic':
                appconfig['Free-for-All Playlists']['Just Epic Elim'] = [{
                    'settings': {
                        'Epic Mode': 1,
                        'Lives Per Player': 1,
                        'Respawn Times': 1.0,
                        'Time Limit': 0,
                        'map': 'Tip Top'
                    },
                    'type': 'bs_elimination.EliminationGame'
                }]
                appconfig['Free-for-All Playlist Selection'] = 'Just Epic Elim'
                _ba.fade_screen(False,
                                endcall=ba.Call(
                                    ba.pushcall,
                                    ba.Call(_ba.new_host_session,
                                            ba.FreeForAllSession)))
            else:
                if mode == 'ctf':
                    appconfig['Team Tournament Playlists']['Just CTF'] = [{
                        'settings': {
                            'Epic Mode': False,
                            'Flag Idle Return Time': 30,
                            'Flag Touch Return Time': 0,
                            'Respawn Times': 1.0,
                            'Score to Win': 3,
                            'Time Limit': 0,
                            'map': 'Bridgit'
                        },
                        'type': 'bs_capture_the_flag.CTFGame'
                    }]
                    appconfig[
                        'Team Tournament Playlist Selection'] = 'Just CTF'
                else:
                    appconfig['Team Tournament Playlists']['Just Hockey'] = [{
                        'settings': {
                            'Respawn Times': 1.0,
                            'Score to Win': 1,
                            'Time Limit': 0,
                            'map': 'Hockey Stadium'
                        },
                        'type': 'bs_hockey.HockeyGame'
                    }]
                    appconfig['Team Tournament Playlist Selection'] = (
                        'Just Hockey')
                _ba.fade_screen(False,
                                endcall=ba.Call(
                                    ba.pushcall,
                                    ba.Call(_ba.new_host_session,
                                            ba.DualTeamSession)))
            ba.containerwidget(edit=self._root_widget, transition='out_left')
            return

        game = ('Easy:Onslaught Training'
                if mode == 'easy' else 'Easy:Rookie Football'
                if mode == 'medium' else 'Easy:Uber Onslaught')
        cfg = ba.app.config
        cfg['Selected Coop Game'] = game
        cfg.commit()
        if ba.app.launch_coop_game(game, force=True):
            ba.containerwidget(edit=self._root_widget, transition='out_left')

    def _do_full_menu(self) -> None:
        from bastd.ui.mainmenu import MainMenuWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.did_menu_intro = True  # prevent delayed transition-in
        ba.app.ui.set_main_menu_window(MainMenuWindow().get_root_widget())
