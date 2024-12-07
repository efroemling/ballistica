# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for running the game in kiosk mode."""

from __future__ import annotations

from typing import override

import bascenev1 as bs
import bauiv1 as bui


class KioskWindow(bui.MainWindow):
    """Kiosk mode window."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals, too-many-statements
        from bauiv1lib.confirm import QuitWindow

        assert bui.app.classic is not None

        self._width = 720.0
        self._height = 340.0

        def _do_cancel() -> None:
            QuitWindow(swish=True, quit_type=bui.QuitType.BACK)

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                # transition=transition,
                on_cancel_call=_do_cancel,
                background=False,
                stack_offset=(0, -130),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        self._r = 'kioskWindow'

        self._show_multiplayer = False

        # Let's reset all random player names every time we hit the main menu.
        bs.reset_random_player_names()

        # Reset achievements too (at least locally).
        bui.app.config['Achievements'] = {}

        t_delay_base = 0.0
        t_delay_scale = 0.0
        if not bui.app.classic.did_menu_intro:
            t_delay_base = 1.0
            t_delay_scale = 1.0

        mesh_opaque = bui.getmesh('level_select_button_opaque')
        mesh_transparent = bui.getmesh('level_select_button_transparent')
        mask_tex = bui.gettexture('mapPreviewMask')

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
            bui.textwidget(
                parent=self._root_widget,
                size=(0, 0),
                position=(self._width * 0.5, self._height + y_extra - 44),
                transition_delay=tdelay,
                text=bui.Lstr(resource=f'{self._r}.singlePlayerExamplesText'),
                flatness=1.0,
                scale=1.2,
                h_align='center',
                v_align='center',
                shadow=1.0,
            )
        else:
            tdelay = t_delay_base + t_delay_scale * 0.7
            bui.textwidget(
                parent=self._root_widget,
                size=(0, 0),
                position=(self._width * 0.5, self._height + y_extra - 34),
                transition_delay=tdelay,
                text=(
                    bui.Lstr(
                        resource='demoText',
                        fallback_resource='mainMenu.demoMenuText',
                    )
                    if bui.app.env.demo
                    else 'ARCADE'
                ),
                flatness=1.0,
                scale=1.2,
                h_align='center',
                v_align='center',
                shadow=1.0,
            )
        h = self._width * 0.5 - b_space
        tdelay = t_delay_base + t_delay_scale * 0.7
        self._b1 = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            size=(b_width, b_height),
            on_activate_call=bui.Call(self._do_game, 'easy'),
            transition_delay=tdelay,
            position=(h - b_width * 0.5, b_v),
            label='',
            button_type='square',
        )
        bui.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            transition_delay=tdelay,
            size=(0, 0),
            position=(h, label_height),
            maxwidth=b_width * 0.7,
            text=bui.Lstr(resource=f'{self._r}.easyText'),
            scale=1.3,
            h_align='center',
            v_align='center',
        )
        bui.imagewidget(
            parent=self._root_widget,
            draw_controller=btn,
            size=(img_width, 0.5 * img_width),
            transition_delay=tdelay,
            position=(h - img_width * 0.5, img_v),
            texture=bui.gettexture('doomShroomPreview'),
            mesh_opaque=mesh_opaque,
            mesh_transparent=mesh_transparent,
            mask_texture=mask_tex,
        )
        h = self._width * 0.5
        tdelay = t_delay_base + t_delay_scale * 0.65
        self._b2 = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            size=(b_width, b_height),
            on_activate_call=bui.Call(self._do_game, 'medium'),
            position=(h - b_width * 0.5, b_v),
            label='',
            button_type='square',
            transition_delay=tdelay,
        )
        bui.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            transition_delay=tdelay,
            size=(0, 0),
            position=(h, label_height),
            maxwidth=b_width * 0.7,
            text=bui.Lstr(resource=f'{self._r}.mediumText'),
            scale=1.3,
            h_align='center',
            v_align='center',
        )
        bui.imagewidget(
            parent=self._root_widget,
            draw_controller=btn,
            size=(img_width, 0.5 * img_width),
            transition_delay=tdelay,
            position=(h - img_width * 0.5, img_v),
            texture=bui.gettexture('footballStadiumPreview'),
            mesh_opaque=mesh_opaque,
            mesh_transparent=mesh_transparent,
            mask_texture=mask_tex,
        )
        h = self._width * 0.5 + b_space
        tdelay = t_delay_base + t_delay_scale * 0.6
        self._b3 = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            size=(b_width, b_height),
            on_activate_call=bui.Call(self._do_game, 'hard'),
            transition_delay=tdelay,
            position=(h - b_width * 0.5, b_v),
            label='',
            button_type='square',
        )
        bui.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            transition_delay=tdelay,
            size=(0, 0),
            position=(h, label_height),
            maxwidth=b_width * 0.7,
            text='Hard',
            scale=1.3,
            h_align='center',
            v_align='center',
        )
        bui.imagewidget(
            parent=self._root_widget,
            draw_controller=btn,
            transition_delay=tdelay,
            size=(img_width, 0.5 * img_width),
            position=(h - img_width * 0.5, img_v),
            texture=bui.gettexture('courtyardPreview'),
            mesh_opaque=mesh_opaque,
            mesh_transparent=mesh_transparent,
            mask_texture=mask_tex,
        )
        if not bui.app.classic.did_menu_intro:
            bui.app.classic.did_menu_intro = True

        self._b4: bui.Widget | None
        self._b5: bui.Widget | None
        self._b6: bui.Widget | None

        if bool(False):
            bui.textwidget(
                parent=self._root_widget,
                size=(0, 0),
                position=(self._width * 0.5, self._height + y_extra - 44),
                transition_delay=tdelay,
                text=bui.Lstr(resource=f'{self._r}.versusExamplesText'),
                flatness=1.0,
                scale=1.2,
                h_align='center',
                v_align='center',
                shadow=1.0,
            )
            h = self._width * 0.5 - b_space
            tdelay = t_delay_base + t_delay_scale * 0.7
            self._b4 = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                size=(b_width, b_height),
                on_activate_call=bui.Call(self._do_game, 'ctf'),
                transition_delay=tdelay,
                position=(h - b_width * 0.5, b_v),
                label='',
                button_type='square',
            )
            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                transition_delay=tdelay,
                size=(0, 0),
                position=(h, label_height),
                maxwidth=b_width * 0.7,
                text=bui.Lstr(translate=('gameNames', 'Capture the Flag')),
                scale=1.3,
                h_align='center',
                v_align='center',
            )
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                size=(img_width, 0.5 * img_width),
                transition_delay=tdelay,
                position=(h - img_width * 0.5, img_v),
                texture=bui.gettexture('bridgitPreview'),
                mesh_opaque=mesh_opaque,
                mesh_transparent=mesh_transparent,
                mask_texture=mask_tex,
            )

            h = self._width * 0.5
            tdelay = t_delay_base + t_delay_scale * 0.65
            self._b5 = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                size=(b_width, b_height),
                on_activate_call=bui.Call(self._do_game, 'hockey'),
                position=(h - b_width * 0.5, b_v),
                label='',
                button_type='square',
                transition_delay=tdelay,
            )
            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                transition_delay=tdelay,
                size=(0, 0),
                position=(h, label_height),
                maxwidth=b_width * 0.7,
                text=bui.Lstr(translate=('gameNames', 'Hockey')),
                scale=1.3,
                h_align='center',
                v_align='center',
            )
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                size=(img_width, 0.5 * img_width),
                transition_delay=tdelay,
                position=(h - img_width * 0.5, img_v),
                texture=bui.gettexture('hockeyStadiumPreview'),
                mesh_opaque=mesh_opaque,
                mesh_transparent=mesh_transparent,
                mask_texture=mask_tex,
            )
            h = self._width * 0.5 + b_space
            tdelay = t_delay_base + t_delay_scale * 0.6
            self._b6 = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                size=(b_width, b_height),
                on_activate_call=bui.Call(self._do_game, 'epic'),
                transition_delay=tdelay,
                position=(h - b_width * 0.5, b_v),
                label='',
                button_type='square',
            )
            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                transition_delay=tdelay,
                size=(0, 0),
                position=(h, label_height),
                maxwidth=b_width * 0.7,
                text=bui.Lstr(resource=f'{self._r}.epicModeText'),
                scale=1.3,
                h_align='center',
                v_align='center',
            )
            bui.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                transition_delay=tdelay,
                size=(img_width, 0.5 * img_width),
                position=(h - img_width * 0.5, img_v),
                texture=bui.gettexture('tipTopPreview'),
                mesh_opaque=mesh_opaque,
                mesh_transparent=mesh_transparent,
                mask_texture=mask_tex,
            )
        else:
            self._b4 = self._b5 = self._b6 = None

        self._b7: bui.Widget | None
        if bui.app.env.arcade:
            self._b7 = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                size=(b_width, 50),
                color=(0.45, 0.55, 0.45),
                textcolor=(0.7, 0.8, 0.7),
                scale=0.5,
                position=(self._width * 0.5 - 60.0, b_v - 70.0),
                transition_delay=tdelay,
                label=bui.Lstr(resource=f'{self._r}.fullMenuText'),
                on_activate_call=self._do_full_menu,
            )
        else:
            self._b7 = None
        self._restore_state()
        self._update()
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _restore_state(self) -> None:
        assert bui.app.classic is not None
        sel_name = bui.app.ui_v1.window_states.get(type(self))
        sel: bui.Widget | None
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
            bui.containerwidget(edit=self._root_widget, selected_child=sel)

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
        assert bui.app.classic is not None
        bui.app.ui_v1.window_states[type(self)] = sel_name

    def _update(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # Kiosk-mode is designed to be used signed-out... try for force
        # the issue.
        if plus.get_v1_account_state() == 'signed_in':
            # _bs.sign_out()
            # FIXME: Try to delete player profiles here too.
            pass
        else:
            # Also make sure there's no player profiles.
            appconfig = bui.app.config
            appconfig['Player Profiles'] = {}

    def _do_game(self, mode: str) -> None:
        assert bui.app.classic is not None
        self._save_state()
        if mode in ['epic', 'ctf', 'hockey']:
            appconfig = bui.app.config
            if 'Team Tournament Playlists' not in appconfig:
                appconfig['Team Tournament Playlists'] = {}
            if 'Free-for-All Playlists' not in appconfig:
                appconfig['Free-for-All Playlists'] = {}
            appconfig['Show Tutorial'] = False
            if mode == 'epic':
                appconfig['Free-for-All Playlists']['Just Epic Elim'] = [
                    {
                        'settings': {
                            'Epic Mode': 1,
                            'Lives Per Player': 1,
                            'Respawn Times': 1.0,
                            'Time Limit': 0,
                            'map': 'Tip Top',
                        },
                        'type': 'bs_elimination.EliminationGame',
                    }
                ]
                appconfig['Free-for-All Playlist Selection'] = 'Just Epic Elim'
                bui.fade_screen(
                    False,
                    endcall=bui.Call(
                        bui.pushcall,
                        bui.Call(bs.new_host_session, bs.FreeForAllSession),
                    ),
                )
            else:
                if mode == 'ctf':
                    appconfig['Team Tournament Playlists']['Just CTF'] = [
                        {
                            'settings': {
                                'Epic Mode': False,
                                'Flag Idle Return Time': 30,
                                'Flag Touch Return Time': 0,
                                'Respawn Times': 1.0,
                                'Score to Win': 3,
                                'Time Limit': 0,
                                'map': 'Bridgit',
                            },
                            'type': 'bs_capture_the_flag.CTFGame',
                        }
                    ]
                    appconfig['Team Tournament Playlist Selection'] = 'Just CTF'
                else:
                    appconfig['Team Tournament Playlists']['Just Hockey'] = [
                        {
                            'settings': {
                                'Respawn Times': 1.0,
                                'Score to Win': 1,
                                'Time Limit': 0,
                                'map': 'Hockey Stadium',
                            },
                            'type': 'bs_hockey.HockeyGame',
                        }
                    ]
                    appconfig['Team Tournament Playlist Selection'] = (
                        'Just Hockey'
                    )
                bui.fade_screen(
                    False,
                    endcall=bui.Call(
                        bui.pushcall,
                        bui.Call(bs.new_host_session, bs.DualTeamSession),
                    ),
                )
            bui.containerwidget(edit=self._root_widget, transition='out_left')
            return

        game = (
            'Easy:Onslaught Training'
            if mode == 'easy'
            else (
                'Easy:Rookie Football'
                if mode == 'medium'
                else 'Easy:Uber Onslaught'
            )
        )
        cfg = bui.app.config
        cfg['Selected Coop Game'] = game
        cfg.commit()
        if bui.app.classic.launch_coop_game(game, force=True):
            bui.containerwidget(edit=self._root_widget, transition='out_left')

    def _do_full_menu(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.mainmenu import MainMenuWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        assert bui.app.classic is not None

        self._save_state()
        bui.app.classic.did_menu_intro = True  # prevent delayed transition-in

        self.main_window_replace(MainMenuWindow())
