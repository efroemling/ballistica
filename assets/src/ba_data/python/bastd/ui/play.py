# Released under the MIT License. See LICENSE for details.
#
"""Provides the top level play window."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import ba.internal

if TYPE_CHECKING:
    pass


class PlayWindow(ba.Window):
    """Window for selecting overall play type."""

    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: ba.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        import threading

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        threading.Thread(target=self._preload_modules).start()

        # We can currently be used either for main menu duty or for selecting
        # playlists (should make this more elegant/general).
        self._is_main_menu = not ba.app.ui.selecting_private_party_playlist

        uiscale = ba.app.ui.uiscale
        width = 1000 if uiscale is ba.UIScale.SMALL else 800
        x_offs = 100 if uiscale is ba.UIScale.SMALL else 0
        height = 550
        button_width = 400

        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._r = 'playWindow'

        super().__init__(
            root_widget=ba.containerwidget(
                size=(width, height),
                transition=transition,
                toolbar_visibility='menu_full',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    1.6
                    if uiscale is ba.UIScale.SMALL
                    else 0.9
                    if uiscale is ba.UIScale.MEDIUM
                    else 0.8
                ),
                stack_offset=(0, 0) if uiscale is ba.UIScale.SMALL else (0, 0),
            )
        )
        self._back_button = back_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(55 + x_offs, height - 132),
            size=(120, 60),
            scale=1.1,
            text_res_scale=1.5,
            text_scale=1.2,
            autoselect=True,
            label=ba.Lstr(resource='backText'),
            button_type='back',
        )

        txt = ba.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, height - 101),
            # position=(width * 0.5, height -
            #           (101 if main_menu else 61)),
            size=(0, 0),
            text=ba.Lstr(
                resource=(self._r + '.titleText')
                if self._is_main_menu
                else 'playlistsText'
            ),
            scale=1.7,
            res_scale=2.0,
            maxwidth=400,
            color=ba.app.ui.heading_color,
            h_align='center',
            v_align='center',
        )

        ba.buttonwidget(
            edit=btn,
            button_type='backSmall',
            size=(60, 60),
            label=ba.charstr(ba.SpecialChar.BACK),
        )
        if ba.app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
            ba.textwidget(edit=txt, text='')

        v = height - (110 if self._is_main_menu else 90)
        v -= 100
        clr = (0.6, 0.7, 0.6, 1.0)
        v -= 280 if self._is_main_menu else 180
        v += 30 if ba.app.ui.use_toolbars and uiscale is ba.UIScale.SMALL else 0
        hoffs = x_offs + 80 if self._is_main_menu else x_offs - 100
        scl = 1.13 if self._is_main_menu else 0.68

        self._lineup_tex = ba.gettexture('playerLineup')
        angry_computer_transparent_model = ba.getmodel(
            'angryComputerTransparent'
        )
        self._lineup_1_transparent_model = ba.getmodel(
            'playerLineup1Transparent'
        )
        self._lineup_2_transparent_model = ba.getmodel(
            'playerLineup2Transparent'
        )
        self._lineup_3_transparent_model = ba.getmodel(
            'playerLineup3Transparent'
        )
        self._lineup_4_transparent_model = ba.getmodel(
            'playerLineup4Transparent'
        )
        self._eyes_model = ba.getmodel('plasticEyesTransparent')

        self._coop_button: ba.Widget | None = None

        # Only show coop button in main-menu variant.
        if self._is_main_menu:
            self._coop_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=(hoffs, v + (scl * 15 if self._is_main_menu else 0)),
                size=(
                    scl * button_width,
                    scl * (300 if self._is_main_menu else 360),
                ),
                extra_touch_border_scale=0.1,
                autoselect=True,
                label='',
                button_type='square',
                text_scale=1.13,
                on_activate_call=self._coop,
            )

            if ba.app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
                ba.widget(
                    edit=btn,
                    left_widget=ba.internal.get_special_widget('back_button'),
                )
                ba.widget(
                    edit=btn,
                    up_widget=ba.internal.get_special_widget('account_button'),
                )
                ba.widget(
                    edit=btn,
                    down_widget=ba.internal.get_special_widget(
                        'settings_button'
                    ),
                )

            self._draw_dude(
                0,
                btn,
                hoffs,
                v,
                scl,
                position=(140, 30),
                color=(0.72, 0.4, 1.0),
            )
            self._draw_dude(
                1,
                btn,
                hoffs,
                v,
                scl,
                position=(185, 53),
                color=(0.71, 0.5, 1.0),
            )
            self._draw_dude(
                2,
                btn,
                hoffs,
                v,
                scl,
                position=(220, 27),
                color=(0.67, 0.44, 1.0),
            )
            self._draw_dude(
                3, btn, hoffs, v, scl, position=(255, 57), color=(0.7, 0.3, 1.0)
            )
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(hoffs + scl * 230, v + scl * 153),
                size=(scl * 115, scl * 115),
                texture=self._lineup_tex,
                model_transparent=angry_computer_transparent_model,
            )

            ba.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(hoffs + scl * (-10), v + scl * 95),
                size=(scl * button_width, scl * 50),
                text=ba.Lstr(
                    resource='playModes.singlePlayerCoopText',
                    fallback_resource='playModes.coopText',
                ),
                maxwidth=scl * button_width * 0.7,
                res_scale=1.5,
                h_align='center',
                v_align='center',
                color=(0.7, 0.9, 0.7, 1.0),
                scale=scl * 2.3,
            )

            ba.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(hoffs + scl * (-10), v + (scl * 54)),
                size=(scl * button_width, scl * 30),
                text=ba.Lstr(resource=self._r + '.oneToFourPlayersText'),
                h_align='center',
                v_align='center',
                scale=0.83 * scl,
                flatness=1.0,
                maxwidth=scl * button_width * 0.7,
                color=clr,
            )

        scl = 0.5 if self._is_main_menu else 0.68
        hoffs += 440 if self._is_main_menu else 216
        v += 180 if self._is_main_menu else -68

        self._teams_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(hoffs, v + (scl * 15 if self._is_main_menu else 0)),
            size=(
                scl * button_width,
                scl * (300 if self._is_main_menu else 360),
            ),
            extra_touch_border_scale=0.1,
            autoselect=True,
            label='',
            button_type='square',
            text_scale=1.13,
            on_activate_call=self._team_tourney,
        )

        if ba.app.ui.use_toolbars:
            ba.widget(
                edit=btn,
                up_widget=ba.internal.get_special_widget('tickets_plus_button'),
                right_widget=ba.internal.get_special_widget('party_button'),
            )

        xxx = -14
        self._draw_dude(
            2,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 148, 30),
            color=(0.2, 0.4, 1.0),
        )
        self._draw_dude(
            3,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 181, 53),
            color=(0.3, 0.4, 1.0),
        )
        self._draw_dude(
            1,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 216, 33),
            color=(0.3, 0.5, 1.0),
        )
        self._draw_dude(
            0,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 245, 57),
            color=(0.3, 0.5, 1.0),
        )

        xxx = 155
        self._draw_dude(
            0,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 151, 30),
            color=(1.0, 0.5, 0.4),
        )
        self._draw_dude(
            1,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 189, 53),
            color=(1.0, 0.58, 0.58),
        )
        self._draw_dude(
            3,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 223, 27),
            color=(1.0, 0.5, 0.5),
        )
        self._draw_dude(
            2,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 257, 57),
            color=(1.0, 0.5, 0.5),
        )

        ba.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            position=(hoffs + scl * (-10), v + scl * 95),
            size=(scl * button_width, scl * 50),
            text=ba.Lstr(
                resource='playModes.teamsText', fallback_resource='teamsText'
            ),
            res_scale=1.5,
            maxwidth=scl * button_width * 0.7,
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
            scale=scl * 2.3,
        )
        ba.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            position=(hoffs + scl * (-10), v + (scl * 54)),
            size=(scl * button_width, scl * 30),
            text=ba.Lstr(resource=self._r + '.twoToEightPlayersText'),
            h_align='center',
            v_align='center',
            res_scale=1.5,
            scale=0.9 * scl,
            flatness=1.0,
            maxwidth=scl * button_width * 0.7,
            color=clr,
        )

        hoffs += 0 if self._is_main_menu else 300
        v -= 155 if self._is_main_menu else 0
        self._free_for_all_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(hoffs, v + (scl * 15 if self._is_main_menu else 0)),
            size=(
                scl * button_width,
                scl * (300 if self._is_main_menu else 360),
            ),
            extra_touch_border_scale=0.1,
            autoselect=True,
            label='',
            button_type='square',
            text_scale=1.13,
            on_activate_call=self._free_for_all,
        )

        xxx = -5
        self._draw_dude(
            0,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 140, 30),
            color=(0.4, 1.0, 0.4),
        )
        self._draw_dude(
            3,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 185, 53),
            color=(1.0, 0.4, 0.5),
        )
        self._draw_dude(
            1,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 220, 27),
            color=(0.4, 0.5, 1.0),
        )
        self._draw_dude(
            2,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 255, 57),
            color=(0.5, 1.0, 0.4),
        )
        xxx = 140
        self._draw_dude(
            2,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 148, 30),
            color=(1.0, 0.9, 0.4),
        )
        self._draw_dude(
            0,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 182, 53),
            color=(0.7, 1.0, 0.5),
        )
        self._draw_dude(
            3,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 233, 27),
            color=(0.7, 0.5, 0.9),
        )
        self._draw_dude(
            1,
            btn,
            hoffs,
            v,
            scl,
            position=(xxx + 266, 53),
            color=(0.4, 0.5, 0.8),
        )
        ba.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            position=(hoffs + scl * (-10), v + scl * 95),
            size=(scl * button_width, scl * 50),
            text=ba.Lstr(
                resource='playModes.freeForAllText',
                fallback_resource='freeForAllText',
            ),
            maxwidth=scl * button_width * 0.7,
            h_align='center',
            v_align='center',
            color=(0.7, 0.9, 0.7, 1.0),
            scale=scl * 1.9,
        )
        ba.textwidget(
            parent=self._root_widget,
            draw_controller=btn,
            position=(hoffs + scl * (-10), v + (scl * 54)),
            size=(scl * button_width, scl * 30),
            text=ba.Lstr(resource=self._r + '.twoToEightPlayersText'),
            h_align='center',
            v_align='center',
            scale=0.9 * scl,
            flatness=1.0,
            maxwidth=scl * button_width * 0.7,
            color=clr,
        )

        if ba.app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
            back_button.delete()
            ba.containerwidget(
                edit=self._root_widget,
                on_cancel_call=self._back,
                selected_child=self._coop_button
                if self._is_main_menu
                else self._teams_button,
            )
        else:
            ba.buttonwidget(edit=back_button, on_activate_call=self._back)
            ba.containerwidget(
                edit=self._root_widget,
                cancel_button=back_button,
                selected_child=self._coop_button
                if self._is_main_menu
                else self._teams_button,
            )

        self._restore_state()

    # noinspection PyUnresolvedReferences
    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use (called in bg thread)."""
        import bastd.ui.mainmenu as _unused1
        import bastd.ui.account as _unused2
        import bastd.ui.coop.browser as _unused3
        import bastd.ui.playlist.browser as _unused4

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        if self._is_main_menu:
            from bastd.ui.mainmenu import MainMenuWindow

            self._save_state()
            ba.app.ui.set_main_menu_window(
                MainMenuWindow(transition='in_left').get_root_widget()
            )
            ba.containerwidget(
                edit=self._root_widget, transition=self._transition_out
            )
        else:
            from bastd.ui.gather import GatherWindow

            self._save_state()
            ba.app.ui.set_main_menu_window(
                GatherWindow(transition='in_left').get_root_widget()
            )
            ba.containerwidget(
                edit=self._root_widget, transition=self._transition_out
            )

    def _coop(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account import show_sign_in_prompt
        from bastd.ui.coop.browser import CoopBrowserWindow

        if ba.internal.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            CoopBrowserWindow(origin_widget=self._coop_button).get_root_widget()
        )

    def _team_tourney(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.playlist.browser import PlaylistBrowserWindow

        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            PlaylistBrowserWindow(
                origin_widget=self._teams_button, sessiontype=ba.DualTeamSession
            ).get_root_widget()
        )

    def _free_for_all(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.playlist.browser import PlaylistBrowserWindow

        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            PlaylistBrowserWindow(
                origin_widget=self._free_for_all_button,
                sessiontype=ba.FreeForAllSession,
            ).get_root_widget()
        )

    def _draw_dude(
        self,
        i: int,
        btn: ba.Widget,
        hoffs: float,
        v: float,
        scl: float,
        position: tuple[float, float],
        color: tuple[float, float, float],
    ) -> None:
        h_extra = -100
        v_extra = 130
        eye_color = (
            0.7 * 1.0 + 0.3 * color[0],
            0.7 * 1.0 + 0.3 * color[1],
            0.7 * 1.0 + 0.3 * color[2],
        )
        if i == 0:
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0]),
                    v + scl * (v_extra + position[1]),
                ),
                size=(scl * 60, scl * 80),
                color=color,
                texture=self._lineup_tex,
                model_transparent=self._lineup_1_transparent_model,
            )
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0] + 12),
                    v + scl * (v_extra + position[1] + 53),
                ),
                size=(scl * 36, scl * 18),
                texture=self._lineup_tex,
                color=eye_color,
                model_transparent=self._eyes_model,
            )
        elif i == 1:
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0]),
                    v + scl * (v_extra + position[1]),
                ),
                size=(scl * 45, scl * 90),
                color=color,
                texture=self._lineup_tex,
                model_transparent=self._lineup_2_transparent_model,
            )
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0] + 5),
                    v + scl * (v_extra + position[1] + 67),
                ),
                size=(scl * 32, scl * 16),
                texture=self._lineup_tex,
                color=eye_color,
                model_transparent=self._eyes_model,
            )
        elif i == 2:
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0]),
                    v + scl * (v_extra + position[1]),
                ),
                size=(scl * 45, scl * 90),
                color=color,
                texture=self._lineup_tex,
                model_transparent=self._lineup_3_transparent_model,
            )
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0] + 5),
                    v + scl * (v_extra + position[1] + 59),
                ),
                size=(scl * 34, scl * 17),
                texture=self._lineup_tex,
                color=eye_color,
                model_transparent=self._eyes_model,
            )
        elif i == 3:
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0]),
                    v + scl * (v_extra + position[1]),
                ),
                size=(scl * 48, scl * 96),
                color=color,
                texture=self._lineup_tex,
                model_transparent=self._lineup_4_transparent_model,
            )
            ba.imagewidget(
                parent=self._root_widget,
                draw_controller=btn,
                position=(
                    hoffs + scl * (h_extra + position[0] + 2),
                    v + scl * (v_extra + position[1] + 62),
                ),
                size=(scl * 38, scl * 19),
                texture=self._lineup_tex,
                color=eye_color,
                model_transparent=self._eyes_model,
            )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._teams_button:
                sel_name = 'Team Games'
            elif self._coop_button is not None and sel == self._coop_button:
                sel_name = 'Co-op Games'
            elif sel == self._free_for_all_button:
                sel_name = 'Free-for-All Games'
            elif sel == self._back_button:
                sel_name = 'Back'
            else:
                raise ValueError(f'unrecognized selection {sel}')
            ba.app.ui.window_states[type(self)] = sel_name
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(type(self))
            if sel_name == 'Team Games':
                sel = self._teams_button
            elif sel_name == 'Co-op Games' and self._coop_button is not None:
                sel = self._coop_button
            elif sel_name == 'Free-for-All Games':
                sel = self._free_for_all_button
            elif sel_name == 'Back':
                sel = self._back_button
            else:
                sel = (
                    self._coop_button
                    if self._coop_button is not None
                    else self._teams_button
                )
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')
