# Released under the MIT License. See LICENSE for details.
#
"""Implements the main menu window."""
# pylint: disable=too-many-lines

from __future__ import annotations

from typing import TYPE_CHECKING
import logging

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Callable


class MainMenuWindow(bui.Window):
    """The main menu window, both in-game and in the main menu session."""

    def __init__(self, transition: str | None = 'in_right'):
        # pylint: disable=cyclic-import
        import threading
        from bascenev1lib.mainmenu import MainMenuSession

        plus = bui.app.plus
        assert plus is not None

        self._in_game = not isinstance(
            bs.get_foreground_host_session(),
            MainMenuSession,
        )

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        threading.Thread(target=self._preload_modules).start()

        if not self._in_game:
            bui.set_analytics_screen('Main Menu')
            self._show_remote_app_info_on_first_launch()

        # Make a vanilla container; we'll modify it to our needs in refresh.
        super().__init__(
            root_widget=bui.containerwidget(
                transition=transition,
                toolbar_visibility='menu_minimal_no_back'
                if self._in_game
                else 'menu_minimal_no_back',
            )
        )

        # Grab this stuff in case it changes.
        self._is_demo = bui.app.env.demo
        self._is_arcade = bui.app.env.arcade

        self._tdelay = 0.0
        self._t_delay_inc = 0.02
        self._t_delay_play = 1.7
        self._p_index = 0
        self._use_autoselect = True
        self._button_width = 200.0
        self._button_height = 45.0
        self._width = 100.0
        self._height = 100.0
        self._demo_menu_button: bui.Widget | None = None
        self._gather_button: bui.Widget | None = None
        self._start_button: bui.Widget | None = None
        self._watch_button: bui.Widget | None = None
        self._account_button: bui.Widget | None = None
        self._how_to_play_button: bui.Widget | None = None
        self._credits_button: bui.Widget | None = None
        self._settings_button: bui.Widget | None = None
        self._next_refresh_allow_time = 0.0

        self._store_char_tex = self._get_store_char_tex()

        self._refresh()
        self._restore_state()

        # Keep an eye on a few things and refresh if they change.
        self._account_state = plus.get_v1_account_state()
        self._account_state_num = plus.get_v1_account_state_num()
        self._account_type = (
            plus.get_v1_account_type()
            if self._account_state == 'signed_in'
            else None
        )
        self._refresh_timer = bui.AppTimer(
            0.27, bui.WeakCall(self._check_refresh), repeat=True
        )

    # noinspection PyUnresolvedReferences
    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use; avoids hitches (called in bg thread)."""
        import bauiv1lib.getremote as _unused
        import bauiv1lib.confirm as _unused2
        import bauiv1lib.store.button as _unused3
        import bauiv1lib.kiosk as _unused4
        import bauiv1lib.account.settings as _unused5
        import bauiv1lib.store.browser as _unused6
        import bauiv1lib.creditslist as _unused7
        import bauiv1lib.helpui as _unused8
        import bauiv1lib.settings.allsettings as _unused9
        import bauiv1lib.gather as _unused10
        import bauiv1lib.watch as _unused11
        import bauiv1lib.play as _unused12

    def _show_remote_app_info_on_first_launch(self) -> None:
        app = bui.app
        assert app.classic is not None
        # The first time the non-in-game menu pops up, we might wanna show
        # a 'get-remote-app' dialog in front of it.
        if app.classic.first_main_menu:
            app.classic.first_main_menu = False
            try:
                force_test = False
                bs.get_local_active_input_devices_count()
                if (
                    (app.env.tv or app.classic.platform == 'mac')
                    and bui.app.config.get('launchCount', 0) <= 1
                ) or force_test:

                    def _check_show_bs_remote_window() -> None:
                        try:
                            from bauiv1lib.getremote import GetBSRemoteWindow

                            bui.getsound('swish').play()
                            GetBSRemoteWindow()
                        except Exception:
                            logging.exception(
                                'Error showing get-remote window.'
                            )

                    bui.apptimer(2.5, _check_show_bs_remote_window)
            except Exception:
                logging.exception('Error showing get-remote-app info.')

    def _get_store_char_tex(self) -> str:
        plus = bui.app.plus
        assert plus is not None
        return (
            'storeCharacterXmas'
            if plus.get_v1_account_misc_read_val('xmas', False)
            else 'storeCharacterEaster'
            if plus.get_v1_account_misc_read_val('easter', False)
            else 'storeCharacter'
        )

    def _check_refresh(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        if not self._root_widget:
            return

        now = bui.apptime()
        if now < self._next_refresh_allow_time:
            return

        # Don't refresh for the first few seconds the game is up so we don't
        # interrupt the transition in.
        # bui.app.main_menu_window_refresh_check_count += 1
        # if bui.app.main_menu_window_refresh_check_count < 4:
        #     return

        store_char_tex = self._get_store_char_tex()
        account_state_num = plus.get_v1_account_state_num()
        if (
            account_state_num != self._account_state_num
            or store_char_tex != self._store_char_tex
        ):
            self._store_char_tex = store_char_tex
            self._account_state_num = account_state_num
            account_state = self._account_state = plus.get_v1_account_state()
            self._account_type = (
                plus.get_v1_account_type()
                if account_state == 'signed_in'
                else None
            )
            self._save_state()
            self._refresh()
            self._restore_state()

    def get_play_button(self) -> bui.Widget | None:
        """Return the play button."""
        return self._start_button

    def _refresh(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bauiv1lib.store.button import StoreButton

        plus = bui.app.plus
        assert plus is not None

        # Clear everything that was there.
        children = self._root_widget.get_children()
        for child in children:
            child.delete()

        self._tdelay = 0.0
        self._t_delay_inc = 0.0
        self._t_delay_play = 0.0
        self._button_width = 200.0
        self._button_height = 45.0

        self._r = 'mainMenu'

        app = bui.app
        assert app.classic is not None
        self._have_quit_button = app.ui_v1.uiscale is bui.UIScale.LARGE or (
            app.classic.platform == 'windows'
            and app.classic.subplatform == 'oculus'
        )

        self._have_store_button = not self._in_game

        self._have_settings_button = (
            not self._in_game or not app.ui_v1.use_toolbars
        ) and not (self._is_demo or self._is_arcade)

        self._input_device = input_device = bs.get_ui_input_device()

        # Are we connected to a local player?
        self._input_player = input_device.player if input_device else None

        # Are we connected to a remote player?.
        self._connected_to_remote_player = (
            input_device.is_attached_to_player()
            if (input_device and self._input_player is None)
            else False
        )

        positions: list[tuple[float, float, float]] = []
        self._p_index = 0

        if self._in_game:
            h, v, scale = self._refresh_in_game(positions)
        else:
            h, v, scale = self._refresh_not_in_game(positions)

        if self._have_settings_button:
            h, v, scale = positions[self._p_index]
            self._p_index += 1
            self._settings_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(h - self._button_width * 0.5 * scale, v),
                size=(self._button_width, self._button_height),
                scale=scale,
                autoselect=self._use_autoselect,
                label=bui.Lstr(resource=self._r + '.settingsText'),
                transition_delay=self._tdelay,
                on_activate_call=self._settings,
            )

        # Scattered eggs on easter.
        if (
            plus.get_v1_account_misc_read_val('easter', False)
            and not self._in_game
        ):
            icon_size = 34
            bui.imagewidget(
                parent=self._root_widget,
                position=(
                    h - icon_size * 0.5 - 15,
                    v + self._button_height * scale - icon_size * 0.24 + 1.5,
                ),
                transition_delay=self._tdelay,
                size=(icon_size, icon_size),
                texture=bui.gettexture('egg3'),
                tilt_scale=0.0,
            )

        self._tdelay += self._t_delay_inc

        if self._in_game:
            h, v, scale = positions[self._p_index]
            self._p_index += 1

            # If we're in a replay, we have a 'Leave Replay' button.
            if bs.is_in_replay():
                bui.buttonwidget(
                    parent=self._root_widget,
                    position=(h - self._button_width * 0.5 * scale, v),
                    scale=scale,
                    size=(self._button_width, self._button_height),
                    autoselect=self._use_autoselect,
                    label=bui.Lstr(resource='replayEndText'),
                    on_activate_call=self._confirm_end_replay,
                )
            elif bs.get_foreground_host_session() is not None:
                bui.buttonwidget(
                    parent=self._root_widget,
                    position=(h - self._button_width * 0.5 * scale, v),
                    scale=scale,
                    size=(self._button_width, self._button_height),
                    autoselect=self._use_autoselect,
                    label=bui.Lstr(
                        resource=self._r
                        + (
                            '.endTestText'
                            if self._is_benchmark()
                            else '.endGameText'
                        )
                    ),
                    on_activate_call=(
                        self._confirm_end_test
                        if self._is_benchmark()
                        else self._confirm_end_game
                    ),
                )
            else:
                # Assume we're in a client-session.
                bui.buttonwidget(
                    parent=self._root_widget,
                    position=(h - self._button_width * 0.5 * scale, v),
                    scale=scale,
                    size=(self._button_width, self._button_height),
                    autoselect=self._use_autoselect,
                    label=bui.Lstr(resource=self._r + '.leavePartyText'),
                    on_activate_call=self._confirm_leave_party,
                )

        self._store_button: bui.Widget | None
        if self._have_store_button:
            this_b_width = self._button_width
            h, v, scale = positions[self._p_index]
            self._p_index += 1

            sbtn = self._store_button_instance = StoreButton(
                parent=self._root_widget,
                position=(h - this_b_width * 0.5 * scale, v),
                size=(this_b_width, self._button_height),
                scale=scale,
                on_activate_call=bui.WeakCall(self._on_store_pressed),
                sale_scale=1.3,
                transition_delay=self._tdelay,
            )
            self._store_button = store_button = sbtn.get_button()
            assert bui.app.classic is not None
            uiscale = bui.app.ui_v1.uiscale
            icon_size = (
                55
                if uiscale is bui.UIScale.SMALL
                else 55
                if uiscale is bui.UIScale.MEDIUM
                else 70
            )
            bui.imagewidget(
                parent=self._root_widget,
                position=(
                    h - icon_size * 0.5,
                    v + self._button_height * scale - icon_size * 0.23,
                ),
                transition_delay=self._tdelay,
                size=(icon_size, icon_size),
                texture=bui.gettexture(self._store_char_tex),
                tilt_scale=0.0,
                draw_controller=store_button,
            )
            self._tdelay += self._t_delay_inc
        else:
            self._store_button = None

        self._quit_button: bui.Widget | None
        if not self._in_game and self._have_quit_button:
            h, v, scale = positions[self._p_index]
            self._p_index += 1
            self._quit_button = quit_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=self._use_autoselect,
                position=(h - self._button_width * 0.5 * scale, v),
                size=(self._button_width, self._button_height),
                scale=scale,
                label=bui.Lstr(
                    resource=self._r
                    + (
                        '.quitText'
                        if 'Mac' in app.classic.legacy_user_agent_string
                        else '.exitGameText'
                    )
                ),
                on_activate_call=self._quit,
                transition_delay=self._tdelay,
            )

            # Scattered eggs on easter.
            if plus.get_v1_account_misc_read_val('easter', False):
                icon_size = 30
                bui.imagewidget(
                    parent=self._root_widget,
                    position=(
                        h - icon_size * 0.5 + 25,
                        v
                        + self._button_height * scale
                        - icon_size * 0.24
                        + 1.5,
                    ),
                    transition_delay=self._tdelay,
                    size=(icon_size, icon_size),
                    texture=bui.gettexture('egg1'),
                    tilt_scale=0.0,
                )

            bui.containerwidget(
                edit=self._root_widget, cancel_button=quit_button
            )
            self._tdelay += self._t_delay_inc
        else:
            self._quit_button = None

            # If we're not in-game, have no quit button, and this is android,
            # we want back presses to quit our activity.
            if (
                not self._in_game
                and not self._have_quit_button
                and app.classic.platform == 'android'
            ):

                def _do_quit() -> None:
                    bui.quit(confirm=True, quit_type=bui.QuitType.BACK)

                bui.containerwidget(
                    edit=self._root_widget, on_cancel_call=_do_quit
                )

        # Add speed-up/slow-down buttons for replays.
        # (ideally this should be part of a fading-out playback bar like most
        # media players but this works for now).
        if bs.is_in_replay():
            b_size = 50.0
            b_buffer = 10.0
            t_scale = 0.75
            assert bui.app.classic is not None
            uiscale = bui.app.ui_v1.uiscale
            if uiscale is bui.UIScale.SMALL:
                b_size *= 0.6
                b_buffer *= 1.0
                v_offs = -40
                t_scale = 0.5
            elif uiscale is bui.UIScale.MEDIUM:
                v_offs = -70
            else:
                v_offs = -100
            self._replay_speed_text = bui.textwidget(
                parent=self._root_widget,
                text=bui.Lstr(
                    resource='watchWindow.playbackSpeedText',
                    subs=[('${SPEED}', str(1.23))],
                ),
                position=(h, v + v_offs + 7 * t_scale),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=t_scale,
            )

            # Update to current value.
            self._change_replay_speed(0)

            # Keep updating in a timer in case it gets changed elsewhere.
            self._change_replay_speed_timer = bui.AppTimer(
                0.25, bui.WeakCall(self._change_replay_speed, 0), repeat=True
            )
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    h - b_size - b_buffer,
                    v - b_size - b_buffer + v_offs,
                ),
                button_type='square',
                size=(b_size, b_size),
                label='',
                autoselect=True,
                on_activate_call=bui.Call(self._change_replay_speed, -1),
            )
            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                text='-',
                position=(
                    h - b_size * 0.5 - b_buffer,
                    v - b_size * 0.5 - b_buffer + 5 * t_scale + v_offs,
                ),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=3.0 * t_scale,
            )
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(h + b_buffer, v - b_size - b_buffer + v_offs),
                button_type='square',
                size=(b_size, b_size),
                label='',
                autoselect=True,
                on_activate_call=bui.Call(self._change_replay_speed, 1),
            )
            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                text='+',
                position=(
                    h + b_size * 0.5 + b_buffer,
                    v - b_size * 0.5 - b_buffer + 5 * t_scale + v_offs,
                ),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=3.0 * t_scale,
            )

    def _refresh_not_in_game(
        self, positions: list[tuple[float, float, float]]
    ) -> tuple[float, float, float]:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None
        if not bui.app.classic.did_menu_intro:
            self._tdelay = 2.0
            self._t_delay_inc = 0.02
            self._t_delay_play = 1.7

            def _set_allow_time() -> None:
                self._next_refresh_allow_time = bui.apptime() + 2.5

            # Slight hack: widget transitions currently only progress when
            # frames are being drawn, but this tends to get called before
            # frame drawing even starts, meaning we don't know exactly how
            # long we should wait before refreshing to avoid interrupting
            # the transition. To make things a bit better, let's do a
            # redundant set of the time in a deferred call which hopefully
            # happens closer to actual frame draw times.
            _set_allow_time()
            bui.pushcall(_set_allow_time)

            bui.app.classic.did_menu_intro = True
        self._width = 400.0
        self._height = 200.0
        enable_account_button = True
        account_type_name: str | bui.Lstr
        if plus.get_v1_account_state() == 'signed_in':
            account_type_name = plus.get_v1_account_display_string()
            account_type_icon = None
            account_textcolor = (1.0, 1.0, 1.0)
        else:
            account_type_name = bui.Lstr(
                resource='notSignedInText',
                fallback_resource='accountSettingsWindow.titleText',
            )
            account_type_icon = None
            account_textcolor = (1.0, 0.2, 0.2)
        account_type_icon_color = (1.0, 1.0, 1.0)
        account_type_call = self._show_account_window
        account_type_enable_button_sound = True
        b_count = 3  # play, help, credits
        if self._have_settings_button:
            b_count += 1
        if enable_account_button:
            b_count += 1
        if self._have_quit_button:
            b_count += 1
        if self._have_store_button:
            b_count += 1
        uiscale = bui.app.ui_v1.uiscale
        if uiscale is bui.UIScale.SMALL:
            root_widget_scale = 1.6
            play_button_width = self._button_width * 0.65
            play_button_height = self._button_height * 1.1
            small_button_scale = 0.51 if b_count > 6 else 0.63
            button_y_offs = -20.0
            button_y_offs2 = -60.0
            self._button_height *= 1.3
            button_spacing = 1.04
        elif uiscale is bui.UIScale.MEDIUM:
            root_widget_scale = 1.3
            play_button_width = self._button_width * 0.65
            play_button_height = self._button_height * 1.1
            small_button_scale = 0.6
            button_y_offs = -55.0
            button_y_offs2 = -75.0
            self._button_height *= 1.25
            button_spacing = 1.1
        else:
            root_widget_scale = 1.0
            play_button_width = self._button_width * 0.65
            play_button_height = self._button_height * 1.1
            small_button_scale = 0.75
            button_y_offs = -80.0
            button_y_offs2 = -100.0
            self._button_height *= 1.2
            button_spacing = 1.1
        spc = self._button_width * small_button_scale * button_spacing
        bui.containerwidget(
            edit=self._root_widget,
            size=(self._width, self._height),
            background=False,
            scale=root_widget_scale,
        )
        assert not positions
        positions.append((self._width * 0.5, button_y_offs, 1.7))
        x_offs = self._width * 0.5 - (spc * (b_count - 1) * 0.5) + (spc * 0.5)
        for i in range(b_count - 1):
            positions.append(
                (
                    x_offs + spc * i - 1.0,
                    button_y_offs + button_y_offs2,
                    small_button_scale,
                )
            )
        # In kiosk mode, provide a button to get back to the kiosk menu.
        if bui.app.env.demo or bui.app.env.arcade:
            h, v, scale = positions[self._p_index]
            this_b_width = self._button_width * 0.4 * scale
            demo_menu_delay = (
                0.0
                if self._t_delay_play == 0.0
                else max(0, self._t_delay_play + 0.1)
            )
            self._demo_menu_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 - this_b_width * 0.5, v + 90),
                size=(this_b_width, 45),
                autoselect=True,
                color=(0.45, 0.55, 0.45),
                textcolor=(0.7, 0.8, 0.7),
                label=bui.Lstr(
                    resource='modeArcadeText'
                    if bui.app.env.arcade
                    else 'modeDemoText'
                ),
                transition_delay=demo_menu_delay,
                on_activate_call=self._demo_menu_press,
            )
        else:
            self._demo_menu_button = None
        uiscale = bui.app.ui_v1.uiscale
        foof = (
            -1
            if uiscale is bui.UIScale.SMALL
            else 1
            if uiscale is bui.UIScale.MEDIUM
            else 3
        )
        h, v, scale = positions[self._p_index]
        v = v + foof
        gather_delay = (
            0.0
            if self._t_delay_play == 0.0
            else max(0.0, self._t_delay_play + 0.1)
        )
        assert play_button_width is not None
        assert play_button_height is not None
        this_h = h - play_button_width * 0.5 * scale - 40 * scale
        this_b_width = self._button_width * 0.25 * scale
        this_b_height = self._button_height * 0.82 * scale
        self._gather_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(this_h - this_b_width * 0.5, v),
            size=(this_b_width, this_b_height),
            autoselect=self._use_autoselect,
            button_type='square',
            label='',
            transition_delay=gather_delay,
            on_activate_call=self._gather_press,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(this_h, v + self._button_height * 0.33),
            size=(0, 0),
            scale=0.75,
            transition_delay=gather_delay,
            draw_controller=btn,
            color=(0.75, 1.0, 0.7),
            maxwidth=self._button_width * 0.33,
            text=bui.Lstr(resource='gatherWindow.titleText'),
            h_align='center',
            v_align='center',
        )
        icon_size = this_b_width * 0.6
        bui.imagewidget(
            parent=self._root_widget,
            size=(icon_size, icon_size),
            draw_controller=btn,
            transition_delay=gather_delay,
            position=(this_h - 0.5 * icon_size, v + 0.31 * this_b_height),
            texture=bui.gettexture('usersButton'),
        )

        # Play button.
        h, v, scale = positions[self._p_index]
        self._p_index += 1
        self._start_button = start_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - play_button_width * 0.5 * scale, v),
            size=(play_button_width, play_button_height),
            autoselect=self._use_autoselect,
            scale=scale,
            text_res_scale=2.0,
            label=bui.Lstr(resource='playText'),
            transition_delay=self._t_delay_play,
            on_activate_call=self._play_press,
        )
        bui.containerwidget(
            edit=self._root_widget,
            start_button=start_button,
            selected_child=start_button,
        )
        v = v + foof
        watch_delay = (
            0.0
            if self._t_delay_play == 0.0
            else max(0.0, self._t_delay_play - 0.1)
        )
        this_h = h + play_button_width * 0.5 * scale + 40 * scale
        this_b_width = self._button_width * 0.25 * scale
        this_b_height = self._button_height * 0.82 * scale
        self._watch_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(this_h - this_b_width * 0.5, v),
            size=(this_b_width, this_b_height),
            autoselect=self._use_autoselect,
            button_type='square',
            label='',
            transition_delay=watch_delay,
            on_activate_call=self._watch_press,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(this_h, v + self._button_height * 0.33),
            size=(0, 0),
            scale=0.75,
            transition_delay=watch_delay,
            color=(0.75, 1.0, 0.7),
            draw_controller=btn,
            maxwidth=self._button_width * 0.33,
            text=bui.Lstr(resource='watchWindow.titleText'),
            h_align='center',
            v_align='center',
        )
        icon_size = this_b_width * 0.55
        bui.imagewidget(
            parent=self._root_widget,
            size=(icon_size, icon_size),
            draw_controller=btn,
            transition_delay=watch_delay,
            position=(this_h - 0.5 * icon_size, v + 0.33 * this_b_height),
            texture=bui.gettexture('tv'),
        )
        if not self._in_game and enable_account_button:
            this_b_width = self._button_width
            h, v, scale = positions[self._p_index]
            self._p_index += 1
            self._account_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(h - this_b_width * 0.5 * scale, v),
                size=(this_b_width, self._button_height),
                scale=scale,
                label=account_type_name,
                autoselect=self._use_autoselect,
                on_activate_call=account_type_call,
                textcolor=account_textcolor,
                icon=account_type_icon,
                icon_color=account_type_icon_color,
                transition_delay=self._tdelay,
                enable_sound=account_type_enable_button_sound,
            )

            # Scattered eggs on easter.
            if (
                plus.get_v1_account_misc_read_val('easter', False)
                and not self._in_game
            ):
                icon_size = 32
                bui.imagewidget(
                    parent=self._root_widget,
                    position=(
                        h - icon_size * 0.5 + 35,
                        v
                        + self._button_height * scale
                        - icon_size * 0.24
                        + 1.5,
                    ),
                    transition_delay=self._tdelay,
                    size=(icon_size, icon_size),
                    texture=bui.gettexture('egg2'),
                    tilt_scale=0.0,
                )
            self._tdelay += self._t_delay_inc
        else:
            self._account_button = None

        # How-to-play button.
        h, v, scale = positions[self._p_index]
        self._p_index += 1
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - self._button_width * 0.5 * scale, v),
            scale=scale,
            autoselect=self._use_autoselect,
            size=(self._button_width, self._button_height),
            label=bui.Lstr(resource=self._r + '.howToPlayText'),
            transition_delay=self._tdelay,
            on_activate_call=self._howtoplay,
        )
        self._how_to_play_button = btn

        # Scattered eggs on easter.
        if (
            plus.get_v1_account_misc_read_val('easter', False)
            and not self._in_game
        ):
            icon_size = 28
            bui.imagewidget(
                parent=self._root_widget,
                position=(
                    h - icon_size * 0.5 + 30,
                    v + self._button_height * scale - icon_size * 0.24 + 1.5,
                ),
                transition_delay=self._tdelay,
                size=(icon_size, icon_size),
                texture=bui.gettexture('egg4'),
                tilt_scale=0.0,
            )
        # Credits button.
        self._tdelay += self._t_delay_inc
        h, v, scale = positions[self._p_index]
        self._p_index += 1
        self._credits_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - self._button_width * 0.5 * scale, v),
            size=(self._button_width, self._button_height),
            autoselect=self._use_autoselect,
            label=bui.Lstr(resource=self._r + '.creditsText'),
            scale=scale,
            transition_delay=self._tdelay,
            on_activate_call=self._credits,
        )
        self._tdelay += self._t_delay_inc
        return h, v, scale

    def _refresh_in_game(
        self, positions: list[tuple[float, float, float]]
    ) -> tuple[float, float, float]:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        assert bui.app.classic is not None
        custom_menu_entries: list[dict[str, Any]] = []
        session = bs.get_foreground_host_session()
        if session is not None:
            try:
                custom_menu_entries = session.get_custom_menu_entries()
                for cme in custom_menu_entries:
                    cme_any: Any = cme  # Type check may not hold true.
                    if (
                        not isinstance(cme_any, dict)
                        or 'label' not in cme
                        or not isinstance(cme['label'], (str, bui.Lstr))
                        or 'call' not in cme
                        or not callable(cme['call'])
                    ):
                        raise ValueError(
                            'invalid custom menu entry: ' + str(cme)
                        )
            except Exception:
                custom_menu_entries = []
                logging.exception(
                    'Error getting custom menu entries for %s.', session
                )
        self._width = 250.0
        self._height = 250.0 if self._input_player else 180.0
        if (self._is_demo or self._is_arcade) and self._input_player:
            self._height -= 40
        if not self._have_settings_button:
            self._height -= 50
        if self._connected_to_remote_player:
            # In this case we have a leave *and* a disconnect button.
            self._height += 50
        self._height += 50 * (len(custom_menu_entries))
        uiscale = bui.app.ui_v1.uiscale
        bui.containerwidget(
            edit=self._root_widget,
            size=(self._width, self._height),
            scale=(
                2.15
                if uiscale is bui.UIScale.SMALL
                else 1.6
                if uiscale is bui.UIScale.MEDIUM
                else 1.0
            ),
        )
        h = 125.0
        v = self._height - 80.0 if self._input_player else self._height - 60
        h_offset = 0
        d_h_offset = 0
        v_offset = -50
        for _i in range(6 + len(custom_menu_entries)):
            positions.append((h, v, 1.0))
            v += v_offset
            h += h_offset
            h_offset += d_h_offset
        self._start_button = None
        bui.app.classic.pause()

        # Player name if applicable.
        if self._input_player:
            player_name = self._input_player.getname()
            h, v, scale = positions[self._p_index]
            v += 35
            bui.textwidget(
                parent=self._root_widget,
                position=(h - self._button_width / 2, v),
                size=(self._button_width, self._button_height),
                color=(1, 1, 1, 0.5),
                scale=0.7,
                h_align='center',
                text=bui.Lstr(value=player_name),
            )
        else:
            player_name = ''
        h, v, scale = positions[self._p_index]
        self._p_index += 1
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h - self._button_width / 2, v),
            size=(self._button_width, self._button_height),
            scale=scale,
            label=bui.Lstr(resource=self._r + '.resumeText'),
            autoselect=self._use_autoselect,
            on_activate_call=self._resume,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        # Add any custom options defined by the current game.
        for entry in custom_menu_entries:
            h, v, scale = positions[self._p_index]
            self._p_index += 1

            # Ask the entry whether we should resume when we call
            # it (defaults to true).
            resume = bool(entry.get('resume_on_call', True))

            if resume:
                call = bui.Call(self._resume_and_call, entry['call'])
            else:
                call = bui.Call(entry['call'], bui.WeakCall(self._resume))

            bui.buttonwidget(
                parent=self._root_widget,
                position=(h - self._button_width / 2, v),
                size=(self._button_width, self._button_height),
                scale=scale,
                on_activate_call=call,
                label=entry['label'],
                autoselect=self._use_autoselect,
            )
        # Add a 'leave' button if the menu-owner has a player.
        if (self._input_player or self._connected_to_remote_player) and not (
            self._is_demo or self._is_arcade
        ):
            h, v, scale = positions[self._p_index]
            self._p_index += 1
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(h - self._button_width / 2, v),
                size=(self._button_width, self._button_height),
                scale=scale,
                on_activate_call=self._leave,
                label='',
                autoselect=self._use_autoselect,
            )

            if (
                player_name != ''
                and player_name[0] != '<'
                and player_name[-1] != '>'
            ):
                txt = bui.Lstr(
                    resource=self._r + '.justPlayerText',
                    subs=[('${NAME}', player_name)],
                )
            else:
                txt = bui.Lstr(value=player_name)
            bui.textwidget(
                parent=self._root_widget,
                position=(
                    h,
                    v
                    + self._button_height
                    * (0.64 if player_name != '' else 0.5),
                ),
                size=(0, 0),
                text=bui.Lstr(resource=self._r + '.leaveGameText'),
                scale=(0.83 if player_name != '' else 1.0),
                color=(0.75, 1.0, 0.7),
                h_align='center',
                v_align='center',
                draw_controller=btn,
                maxwidth=self._button_width * 0.9,
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(h, v + self._button_height * 0.27),
                size=(0, 0),
                text=txt,
                color=(0.75, 1.0, 0.7),
                h_align='center',
                v_align='center',
                draw_controller=btn,
                scale=0.45,
                maxwidth=self._button_width * 0.9,
            )
        return h, v, scale

    def _change_replay_speed(self, offs: int) -> None:
        if not self._replay_speed_text:
            if bui.do_once():
                print('_change_replay_speed called without widget')
            return
        bs.set_replay_speed_exponent(bs.get_replay_speed_exponent() + offs)
        actual_speed = pow(2.0, bs.get_replay_speed_exponent())
        bui.textwidget(
            edit=self._replay_speed_text,
            text=bui.Lstr(
                resource='watchWindow.playbackSpeedText',
                subs=[('${SPEED}', str(actual_speed))],
            ),
        )

    def _quit(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import QuitWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        # Note: Normally we should go through bui.quit(confirm=True) but
        # invoking the window directly lets us scale it up from the
        # button.
        QuitWindow(origin_widget=self._quit_button)

    def _demo_menu_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.kiosk import KioskWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_right')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            KioskWindow(transition='in_left').get_root_widget(),
            from_window=self._root_widget,
        )

    def _show_account_window(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.account.settings import AccountSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            AccountSettingsWindow(
                origin_widget=self._account_button
            ).get_root_widget(),
            from_window=self._root_widget,
        )

    def _on_store_pressed(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.store.browser import StoreBrowserWindow
        from bauiv1lib.account import show_sign_in_prompt

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            StoreBrowserWindow(
                origin_widget=self._store_button
            ).get_root_widget(),
            from_window=self._root_widget,
        )

    def _is_benchmark(self) -> bool:
        session = bs.get_foreground_host_session()
        return getattr(session, 'benchmark_type', None) == 'cpu' or (
            bui.app.classic is not None
            and bui.app.classic.stress_test_reset_timer is not None
        )

    def _confirm_end_game(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        # FIXME: Currently we crash calling this on client-sessions.

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(
            bui.Lstr(resource=self._r + '.exitToMenuText'),
            self._end_game,
            cancel_is_selected=True,
        )

    def _confirm_end_test(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(
            bui.Lstr(resource=self._r + '.exitToMenuText'),
            self._end_game,
            cancel_is_selected=True,
        )

    def _confirm_end_replay(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(
            bui.Lstr(resource=self._r + '.exitToMenuText'),
            self._end_game,
            cancel_is_selected=True,
        )

    def _confirm_leave_party(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(
            bui.Lstr(resource=self._r + '.leavePartyConfirmText'),
            self._leave_party,
            cancel_is_selected=True,
        )

    def _leave_party(self) -> None:
        bs.disconnect_from_host()

    def _end_game(self) -> None:
        assert bui.app.classic is not None

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(edit=self._root_widget, transition='out_left')
        bui.app.classic.return_to_main_menu_session_gracefully(reset_ui=False)

    def _leave(self) -> None:
        if self._input_player:
            self._input_player.remove_from_game()
        elif self._connected_to_remote_player:
            if self._input_device:
                self._input_device.detach_from_player()
        self._resume()

    def _credits(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.creditslist import CreditsListWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            CreditsListWindow(
                origin_widget=self._credits_button
            ).get_root_widget(),
            from_window=self._root_widget,
        )

    def _howtoplay(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.helpui import HelpWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            HelpWindow(
                main_menu=True, origin_widget=self._how_to_play_button
            ).get_root_widget(),
            from_window=self._root_widget,
        )

    def _settings(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.allsettings import AllSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            AllSettingsWindow(
                origin_widget=self._settings_button
            ).get_root_widget(),
            from_window=self._root_widget,
        )

    def _resume_and_call(self, call: Callable[[], Any]) -> None:
        self._resume()
        call()

    def _do_game_service_press(self) -> None:
        self._save_state()
        if bui.app.plus is not None:
            bui.app.plus.show_game_service_ui()
        else:
            logging.warning(
                'plus feature-set is required to show game service ui'
            )

    def _save_state(self) -> None:
        # Don't do this for the in-game menu.
        if self._in_game:
            return
        assert bui.app.classic is not None
        ui = bui.app.ui_v1
        sel = self._root_widget.get_selected_child()
        if sel == self._start_button:
            ui.main_menu_selection = 'Start'
        elif sel == self._gather_button:
            ui.main_menu_selection = 'Gather'
        elif sel == self._watch_button:
            ui.main_menu_selection = 'Watch'
        elif sel == self._how_to_play_button:
            ui.main_menu_selection = 'HowToPlay'
        elif sel == self._credits_button:
            ui.main_menu_selection = 'Credits'
        elif sel == self._settings_button:
            ui.main_menu_selection = 'Settings'
        elif sel == self._account_button:
            ui.main_menu_selection = 'Account'
        elif sel == self._store_button:
            ui.main_menu_selection = 'Store'
        elif sel == self._quit_button:
            ui.main_menu_selection = 'Quit'
        elif sel == self._demo_menu_button:
            ui.main_menu_selection = 'DemoMenu'
        else:
            print('unknown widget in main menu store selection:', sel)
            ui.main_menu_selection = 'Start'

    def _restore_state(self) -> None:
        # pylint: disable=too-many-branches

        # Don't do this for the in-game menu.
        if self._in_game:
            return
        assert bui.app.classic is not None
        sel_name = bui.app.ui_v1.main_menu_selection
        sel: bui.Widget | None
        if sel_name is None:
            sel_name = 'Start'
        if sel_name == 'HowToPlay':
            sel = self._how_to_play_button
        elif sel_name == 'Gather':
            sel = self._gather_button
        elif sel_name == 'Watch':
            sel = self._watch_button
        elif sel_name == 'Credits':
            sel = self._credits_button
        elif sel_name == 'Settings':
            sel = self._settings_button
        elif sel_name == 'Account':
            sel = self._account_button
        elif sel_name == 'Store':
            sel = self._store_button
        elif sel_name == 'Quit':
            sel = self._quit_button
        elif sel_name == 'DemoMenu':
            sel = self._demo_menu_button
        else:
            sel = self._start_button
        if sel is not None:
            bui.containerwidget(edit=self._root_widget, selected_child=sel)

    def _gather_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.gather import GatherWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            GatherWindow(origin_widget=self._gather_button).get_root_widget(),
            from_window=self._root_widget,
        )

    def _watch_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.watch import WatchWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            WatchWindow(origin_widget=self._watch_button).get_root_widget(),
            from_window=self._root_widget,
        )

    def _play_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.play import PlayWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')

        assert bui.app.classic is not None
        bui.app.ui_v1.selecting_private_party_playlist = False
        bui.app.ui_v1.set_main_menu_window(
            PlayWindow(origin_widget=self._start_button).get_root_widget(),
            from_window=self._root_widget,
        )

    def _resume(self) -> None:
        assert bui.app.classic is not None
        bui.app.classic.resume()
        if self._root_widget:
            bui.containerwidget(edit=self._root_widget, transition='out_right')
        bui.app.ui_v1.clear_main_menu_window(transition='out_right')

        # If there's callbacks waiting for this window to go away, call them.
        for call in bui.app.ui_v1.main_menu_resume_callbacks:
            call()
        del bui.app.ui_v1.main_menu_resume_callbacks[:]
