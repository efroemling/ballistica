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
"""Implements the main menu window."""
# pylint: disable=too-many-lines

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import _ba

if TYPE_CHECKING:
    from typing import Any, Callable, List, Dict, Tuple, Optional, Union


class MainMenuWindow(ba.Window):
    """The main menu window, both in-game and in the main menu session."""

    def __init__(self, transition: Optional[str] = 'in_right'):
        # pylint: disable=cyclic-import
        import threading
        from bastd.mainmenu import MainMenuSession
        self._in_game = not isinstance(_ba.get_foreground_host_session(),
                                       MainMenuSession)

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        threading.Thread(target=self._preload_modules).start()

        if not self._in_game:
            ba.set_analytics_screen('Main Menu')
            self._show_remote_app_info_on_first_launch()

        # Make a vanilla container; we'll modify it to our needs in refresh.
        super().__init__(root_widget=ba.containerwidget(
            transition=transition,
            toolbar_visibility='menu_minimal_no_back' if self.
            _in_game else 'menu_minimal_no_back'))

        self._is_kiosk = ba.app.kiosk_mode
        self._tdelay = 0.0
        self._t_delay_inc = 0.02
        self._t_delay_play = 1.7
        self._p_index = 0
        self._use_autoselect = True
        self._button_width = 200.0
        self._button_height = 45.0
        self._width = 100.0
        self._height = 100.0
        self._demo_menu_button: Optional[ba.Widget] = None
        self._gather_button: Optional[ba.Widget] = None
        self._start_button: Optional[ba.Widget] = None
        self._watch_button: Optional[ba.Widget] = None
        self._gc_button: Optional[ba.Widget] = None
        self._how_to_play_button: Optional[ba.Widget] = None
        self._credits_button: Optional[ba.Widget] = None

        self._store_char_tex = self._get_store_char_tex()

        self._refresh()
        self._restore_state()

        # Keep an eye on a few things and refresh if they change.
        self._account_state = _ba.get_account_state()
        self._account_state_num = _ba.get_account_state_num()
        self._account_type = (_ba.get_account_type()
                              if self._account_state == 'signed_in' else None)
        self._refresh_timer = ba.Timer(1.0,
                                       ba.WeakCall(self._check_refresh),
                                       repeat=True,
                                       timetype=ba.TimeType.REAL)

    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use (called in bg thread)."""
        import bastd.ui.getremote as _unused
        import bastd.ui.confirm as _unused2
        import bastd.ui.store.button as _unused3
        import bastd.ui.kiosk as _unused4
        import bastd.ui.account.settings as _unused5
        import bastd.ui.store.browser as _unused6
        import bastd.ui.creditslist as _unused7
        import bastd.ui.helpui as _unused8
        import bastd.ui.settings.allsettings as _unused9
        import bastd.ui.gather as _unused10
        import bastd.ui.watch as _unused11
        import bastd.ui.play as _unused12

    def _show_remote_app_info_on_first_launch(self) -> None:
        # The first time the non-in-game menu pops up, we might wanna show
        # a 'get-remote-app' dialog in front of it.
        if ba.app.first_main_menu:
            ba.app.first_main_menu = False
            try:
                app = ba.app
                force_test = False
                _ba.get_local_active_input_devices_count()
                if (((app.on_tv or app.platform == 'mac')
                     and ba.app.config.get('launchCount', 0) <= 1)
                        or force_test):

                    def _check_show_bs_remote_window() -> None:
                        try:
                            from bastd.ui.getremote import GetBSRemoteWindow
                            ba.playsound(ba.getsound('swish'))
                            GetBSRemoteWindow()
                        except Exception:
                            ba.print_exception(
                                'Error showing get-remote window.')

                    ba.timer(2.5,
                             _check_show_bs_remote_window,
                             timetype=ba.TimeType.REAL)
            except Exception:
                ba.print_exception('Error showing get-remote-app info')

    def _get_store_char_tex(self) -> str:
        return ('storeCharacterXmas' if _ba.get_account_misc_read_val(
            'xmas', False) else
                'storeCharacterEaster' if _ba.get_account_misc_read_val(
                    'easter', False) else 'storeCharacter')

    def _check_refresh(self) -> None:
        if not self._root_widget:
            return

        # Don't refresh for the first few seconds the game is up so we don't
        # interrupt the transition in.
        ba.app.main_menu_window_refresh_check_count += 1
        if ba.app.main_menu_window_refresh_check_count < 4:
            return

        store_char_tex = self._get_store_char_tex()
        account_state_num = _ba.get_account_state_num()
        if (account_state_num != self._account_state_num
                or store_char_tex != self._store_char_tex):
            self._store_char_tex = store_char_tex
            self._account_state_num = account_state_num
            account_state = self._account_state = (_ba.get_account_state())
            self._account_type = (_ba.get_account_type()
                                  if account_state == 'signed_in' else None)
            self._save_state()
            self._refresh()
            self._restore_state()

    def get_play_button(self) -> Optional[ba.Widget]:
        """Return the play button."""
        return self._start_button

    def _refresh(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bastd.ui.confirm import QuitWindow
        from bastd.ui.store.button import StoreButton

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

        app = ba.app
        self._have_quit_button = (app.ui.uiscale is ba.UIScale.LARGE
                                  or (app.platform == 'windows'
                                      and app.subplatform == 'oculus'))

        self._have_store_button = not self._in_game

        self._have_settings_button = ((not self._in_game
                                       or not app.toolbar_test)
                                      and not self._is_kiosk)

        self._input_device = input_device = _ba.get_ui_input_device()
        self._input_player = input_device.player if input_device else None
        self._connected_to_remote_player = (
            input_device.is_connected_to_remote_player()
            if input_device else False)

        positions: List[Tuple[float, float, float]] = []
        self._p_index = 0

        if self._in_game:
            h, v, scale = self._refresh_in_game(positions)
        else:
            h, v, scale = self._refresh_not_in_game(positions)

        if self._have_settings_button:
            h, v, scale = positions[self._p_index]
            self._p_index += 1
            self._settings_button = ba.buttonwidget(
                parent=self._root_widget,
                position=(h - self._button_width * 0.5 * scale, v),
                size=(self._button_width, self._button_height),
                scale=scale,
                autoselect=self._use_autoselect,
                label=ba.Lstr(resource=self._r + '.settingsText'),
                transition_delay=self._tdelay,
                on_activate_call=self._settings)

        # Scattered eggs on easter.
        if _ba.get_account_misc_read_val('easter',
                                         False) and not self._in_game:
            icon_size = 34
            ba.imagewidget(parent=self._root_widget,
                           position=(h - icon_size * 0.5 - 15,
                                     v + self._button_height * scale -
                                     icon_size * 0.24 + 1.5),
                           transition_delay=self._tdelay,
                           size=(icon_size, icon_size),
                           texture=ba.gettexture('egg3'),
                           tilt_scale=0.0)

        self._tdelay += self._t_delay_inc

        if self._in_game:
            h, v, scale = positions[self._p_index]
            self._p_index += 1

            # If we're in a replay, we have a 'Leave Replay' button.
            if _ba.is_in_replay():
                ba.buttonwidget(parent=self._root_widget,
                                position=(h - self._button_width * 0.5 * scale,
                                          v),
                                scale=scale,
                                size=(self._button_width, self._button_height),
                                autoselect=self._use_autoselect,
                                label=ba.Lstr(resource='replayEndText'),
                                on_activate_call=self._confirm_end_replay)
            elif _ba.get_foreground_host_session() is not None:
                ba.buttonwidget(
                    parent=self._root_widget,
                    position=(h - self._button_width * 0.5 * scale, v),
                    scale=scale,
                    size=(self._button_width, self._button_height),
                    autoselect=self._use_autoselect,
                    label=ba.Lstr(resource=self._r + '.endGameText'),
                    on_activate_call=self._confirm_end_game)
            # Assume we're in a client-session.
            else:
                ba.buttonwidget(
                    parent=self._root_widget,
                    position=(h - self._button_width * 0.5 * scale, v),
                    scale=scale,
                    size=(self._button_width, self._button_height),
                    autoselect=self._use_autoselect,
                    label=ba.Lstr(resource=self._r + '.leavePartyText'),
                    on_activate_call=self._confirm_leave_party)

        self._store_button: Optional[ba.Widget]
        if self._have_store_button:
            this_b_width = self._button_width
            h, v, scale = positions[self._p_index]
            self._p_index += 1

            sbtn = self._store_button_instance = StoreButton(
                parent=self._root_widget,
                position=(h - this_b_width * 0.5 * scale, v),
                size=(this_b_width, self._button_height),
                scale=scale,
                on_activate_call=ba.WeakCall(self._on_store_pressed),
                sale_scale=1.3,
                transition_delay=self._tdelay)
            self._store_button = store_button = sbtn.get_button()
            uiscale = ba.app.ui.uiscale
            icon_size = (55 if uiscale is ba.UIScale.SMALL else
                         55 if uiscale is ba.UIScale.MEDIUM else 70)
            ba.imagewidget(
                parent=self._root_widget,
                position=(h - icon_size * 0.5,
                          v + self._button_height * scale - icon_size * 0.23),
                transition_delay=self._tdelay,
                size=(icon_size, icon_size),
                texture=ba.gettexture(self._store_char_tex),
                tilt_scale=0.0,
                draw_controller=store_button)

            self._tdelay += self._t_delay_inc
        else:
            self._store_button = None

        self._quit_button: Optional[ba.Widget]
        if not self._in_game and self._have_quit_button:
            h, v, scale = positions[self._p_index]
            self._p_index += 1
            self._quit_button = quit_button = ba.buttonwidget(
                parent=self._root_widget,
                autoselect=self._use_autoselect,
                position=(h - self._button_width * 0.5 * scale, v),
                size=(self._button_width, self._button_height),
                scale=scale,
                label=ba.Lstr(resource=self._r +
                              ('.quitText' if 'Mac' in
                               ba.app.user_agent_string else '.exitGameText')),
                on_activate_call=self._quit,
                transition_delay=self._tdelay)

            # Scattered eggs on easter.
            if _ba.get_account_misc_read_val('easter', False):
                icon_size = 30
                ba.imagewidget(parent=self._root_widget,
                               position=(h - icon_size * 0.5 + 25,
                                         v + self._button_height * scale -
                                         icon_size * 0.24 + 1.5),
                               transition_delay=self._tdelay,
                               size=(icon_size, icon_size),
                               texture=ba.gettexture('egg1'),
                               tilt_scale=0.0)

            ba.containerwidget(edit=self._root_widget,
                               cancel_button=quit_button)
            self._tdelay += self._t_delay_inc
        else:
            self._quit_button = None

            # If we're not in-game, have no quit button, and this is android,
            # we want back presses to quit our activity.
            if (not self._in_game and not self._have_quit_button
                    and ba.app.platform == 'android'):

                def _do_quit() -> None:
                    QuitWindow(swish=True, back=True)

                ba.containerwidget(edit=self._root_widget,
                                   on_cancel_call=_do_quit)

        # Add speed-up/slow-down buttons for replays.
        # (ideally this should be part of a fading-out playback bar like most
        # media players but this works for now).
        if _ba.is_in_replay():
            b_size = 50.0
            b_buffer = 10.0
            t_scale = 0.75
            uiscale = ba.app.ui.uiscale
            if uiscale is ba.UIScale.SMALL:
                b_size *= 0.6
                b_buffer *= 1.0
                v_offs = -40
                t_scale = 0.5
            elif uiscale is ba.UIScale.MEDIUM:
                v_offs = -70
            else:
                v_offs = -100
            self._replay_speed_text = ba.textwidget(
                parent=self._root_widget,
                text=ba.Lstr(resource='watchWindow.playbackSpeedText',
                             subs=[('${SPEED}', str(1.23))]),
                position=(h, v + v_offs + 7 * t_scale),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=t_scale)

            # Update to current value.
            self._change_replay_speed(0)

            # Keep updating in a timer in case it gets changed elsewhere.
            self._change_replay_speed_timer = ba.Timer(
                0.25,
                ba.WeakCall(self._change_replay_speed, 0),
                timetype=ba.TimeType.REAL,
                repeat=True)
            btn = ba.buttonwidget(parent=self._root_widget,
                                  position=(h - b_size - b_buffer,
                                            v - b_size - b_buffer + v_offs),
                                  button_type='square',
                                  size=(b_size, b_size),
                                  label='',
                                  autoselect=True,
                                  on_activate_call=ba.Call(
                                      self._change_replay_speed, -1))
            ba.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                text='-',
                position=(h - b_size * 0.5 - b_buffer,
                          v - b_size * 0.5 - b_buffer + 5 * t_scale + v_offs),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=3.0 * t_scale)
            btn = ba.buttonwidget(
                parent=self._root_widget,
                position=(h + b_buffer, v - b_size - b_buffer + v_offs),
                button_type='square',
                size=(b_size, b_size),
                label='',
                autoselect=True,
                on_activate_call=ba.Call(self._change_replay_speed, 1))
            ba.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                text='+',
                position=(h + b_size * 0.5 + b_buffer,
                          v - b_size * 0.5 - b_buffer + 5 * t_scale + v_offs),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=3.0 * t_scale)

    def _refresh_not_in_game(
        self, positions: List[Tuple[float, float,
                                    float]]) -> Tuple[float, float, float]:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        if not ba.app.did_menu_intro:
            self._tdelay = 2.0
            self._t_delay_inc = 0.02
            self._t_delay_play = 1.7
            ba.app.did_menu_intro = True
        self._width = 400.0
        self._height = 200.0
        enable_account_button = True
        account_type_name: Union[str, ba.Lstr]
        if _ba.get_account_state() == 'signed_in':
            account_type_name = _ba.get_account_display_string()
            account_type_icon = None
            account_textcolor = (1.0, 1.0, 1.0)
        else:
            account_type_name = ba.Lstr(
                resource='notSignedInText',
                fallback_resource='accountSettingsWindow.titleText')
            account_type_icon = None
            account_textcolor = (1.0, 0.2, 0.2)
        account_type_icon_color = (1.0, 1.0, 1.0)
        account_type_call = self._show_account_window
        account_type_enable_button_sound = True
        b_count = 4  # play, help, credits, settings
        if enable_account_button:
            b_count += 1
        if self._have_quit_button:
            b_count += 1
        if self._have_store_button:
            b_count += 1
        uiscale = ba.app.ui.uiscale
        if uiscale is ba.UIScale.SMALL:
            root_widget_scale = 1.6
            play_button_width = self._button_width * 0.65
            play_button_height = self._button_height * 1.1
            small_button_scale = 0.51 if b_count > 6 else 0.63
            button_y_offs = -20.0
            button_y_offs2 = -60.0
            self._button_height *= 1.3
            button_spacing = 1.04
        elif uiscale is ba.UIScale.MEDIUM:
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
        ba.containerwidget(edit=self._root_widget,
                           size=(self._width, self._height),
                           background=False,
                           scale=root_widget_scale)
        assert not positions
        positions.append((self._width * 0.5, button_y_offs, 1.7))
        x_offs = self._width * 0.5 - (spc * (b_count - 1) * 0.5) + (spc * 0.5)
        for i in range(b_count - 1):
            positions.append(
                (x_offs + spc * i - 1.0, button_y_offs + button_y_offs2,
                 small_button_scale))
        # In kiosk mode, provide a button to get back to the kiosk menu.
        if ba.app.kiosk_mode:
            h, v, scale = positions[self._p_index]
            this_b_width = self._button_width * 0.4 * scale
            demo_menu_delay = 0.0 if self._t_delay_play == 0.0 else max(
                0, self._t_delay_play + 0.1)
            self._demo_menu_button = ba.buttonwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 - this_b_width * 0.5, v + 90),
                size=(this_b_width, 45),
                autoselect=True,
                color=(0.45, 0.55, 0.45),
                textcolor=(0.7, 0.8, 0.7),
                label=ba.Lstr(resource=self._r + '.demoMenuText'),
                transition_delay=demo_menu_delay,
                on_activate_call=self._demo_menu_press)
        else:
            self._demo_menu_button = None
        uiscale = ba.app.ui.uiscale
        foof = (-1 if uiscale is ba.UIScale.SMALL else
                1 if uiscale is ba.UIScale.MEDIUM else 3)
        h, v, scale = positions[self._p_index]
        v = v + foof
        gather_delay = 0.0 if self._t_delay_play == 0.0 else max(
            0.0, self._t_delay_play + 0.1)
        assert play_button_width is not None
        assert play_button_height is not None
        this_h = h - play_button_width * 0.5 * scale - 40 * scale
        this_b_width = self._button_width * 0.25 * scale
        this_b_height = self._button_height * 0.82 * scale
        self._gather_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(this_h - this_b_width * 0.5, v),
            size=(this_b_width, this_b_height),
            autoselect=self._use_autoselect,
            button_type='square',
            label='',
            transition_delay=gather_delay,
            on_activate_call=self._gather_press)
        ba.textwidget(parent=self._root_widget,
                      position=(this_h, v + self._button_height * 0.33),
                      size=(0, 0),
                      scale=0.75,
                      transition_delay=gather_delay,
                      draw_controller=btn,
                      color=(0.75, 1.0, 0.7),
                      maxwidth=self._button_width * 0.33,
                      text=ba.Lstr(resource='gatherWindow.titleText'),
                      h_align='center',
                      v_align='center')
        icon_size = this_b_width * 0.6
        ba.imagewidget(parent=self._root_widget,
                       size=(icon_size, icon_size),
                       draw_controller=btn,
                       transition_delay=gather_delay,
                       position=(this_h - 0.5 * icon_size,
                                 v + 0.31 * this_b_height),
                       texture=ba.gettexture('usersButton'))

        # Play button.
        h, v, scale = positions[self._p_index]
        self._p_index += 1
        self._start_button = start_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(h - play_button_width * 0.5 * scale, v),
            size=(play_button_width, play_button_height),
            autoselect=self._use_autoselect,
            scale=scale,
            text_res_scale=2.0,
            label=ba.Lstr(resource='playText'),
            transition_delay=self._t_delay_play,
            on_activate_call=self._play_press)
        ba.containerwidget(edit=self._root_widget,
                           start_button=start_button,
                           selected_child=start_button)
        v = v + foof
        watch_delay = 0.0 if self._t_delay_play == 0.0 else max(
            0.0, self._t_delay_play - 0.1)
        this_h = h + play_button_width * 0.5 * scale + 40 * scale
        this_b_width = self._button_width * 0.25 * scale
        this_b_height = self._button_height * 0.82 * scale
        self._watch_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(this_h - this_b_width * 0.5, v),
            size=(this_b_width, this_b_height),
            autoselect=self._use_autoselect,
            button_type='square',
            label='',
            transition_delay=watch_delay,
            on_activate_call=self._watch_press)
        ba.textwidget(parent=self._root_widget,
                      position=(this_h, v + self._button_height * 0.33),
                      size=(0, 0),
                      scale=0.75,
                      transition_delay=watch_delay,
                      color=(0.75, 1.0, 0.7),
                      draw_controller=btn,
                      maxwidth=self._button_width * 0.33,
                      text=ba.Lstr(resource='watchWindow.titleText'),
                      h_align='center',
                      v_align='center')
        icon_size = this_b_width * 0.55
        ba.imagewidget(parent=self._root_widget,
                       size=(icon_size, icon_size),
                       draw_controller=btn,
                       transition_delay=watch_delay,
                       position=(this_h - 0.5 * icon_size,
                                 v + 0.33 * this_b_height),
                       texture=ba.gettexture('tv'))
        if not self._in_game and enable_account_button:
            this_b_width = self._button_width
            h, v, scale = positions[self._p_index]
            self._p_index += 1
            self._gc_button = ba.buttonwidget(
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
                enable_sound=account_type_enable_button_sound)

            # Scattered eggs on easter.
            if _ba.get_account_misc_read_val('easter',
                                             False) and not self._in_game:
                icon_size = 32
                ba.imagewidget(parent=self._root_widget,
                               position=(h - icon_size * 0.5 + 35,
                                         v + self._button_height * scale -
                                         icon_size * 0.24 + 1.5),
                               transition_delay=self._tdelay,
                               size=(icon_size, icon_size),
                               texture=ba.gettexture('egg2'),
                               tilt_scale=0.0)
            self._tdelay += self._t_delay_inc
        else:
            self._gc_button = None

        # How-to-play button.
        h, v, scale = positions[self._p_index]
        self._p_index += 1
        btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h - self._button_width * 0.5 * scale, v),
            scale=scale,
            autoselect=self._use_autoselect,
            size=(self._button_width, self._button_height),
            label=ba.Lstr(resource=self._r + '.howToPlayText'),
            transition_delay=self._tdelay,
            on_activate_call=self._howtoplay)
        self._how_to_play_button = btn

        # Scattered eggs on easter.
        if _ba.get_account_misc_read_val('easter',
                                         False) and not self._in_game:
            icon_size = 28
            ba.imagewidget(parent=self._root_widget,
                           position=(h - icon_size * 0.5 + 30,
                                     v + self._button_height * scale -
                                     icon_size * 0.24 + 1.5),
                           transition_delay=self._tdelay,
                           size=(icon_size, icon_size),
                           texture=ba.gettexture('egg4'),
                           tilt_scale=0.0)
        # Credits button.
        self._tdelay += self._t_delay_inc
        h, v, scale = positions[self._p_index]
        self._p_index += 1
        self._credits_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(h - self._button_width * 0.5 * scale, v),
            size=(self._button_width, self._button_height),
            autoselect=self._use_autoselect,
            label=ba.Lstr(resource=self._r + '.creditsText'),
            scale=scale,
            transition_delay=self._tdelay,
            on_activate_call=self._credits)
        self._tdelay += self._t_delay_inc
        return h, v, scale

    def _refresh_in_game(
        self, positions: List[Tuple[float, float,
                                    float]]) -> Tuple[float, float, float]:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        custom_menu_entries: List[Dict[str, Any]] = []
        session = _ba.get_foreground_host_session()
        if session is not None:
            try:
                custom_menu_entries = session.get_custom_menu_entries()
                for cme in custom_menu_entries:
                    if (not isinstance(cme, dict) or 'label' not in cme
                            or not isinstance(cme['label'], (str, ba.Lstr))
                            or 'call' not in cme or not callable(cme['call'])):
                        raise ValueError('invalid custom menu entry: ' +
                                         str(cme))
            except Exception:
                custom_menu_entries = []
                ba.print_exception(
                    f'Error getting custom menu entries for {session}')
        self._width = 250.0
        self._height = 250.0 if self._input_player else 180.0
        if self._is_kiosk and self._input_player:
            self._height -= 40
        if not self._have_settings_button:
            self._height -= 50
        if self._connected_to_remote_player:
            # In this case we have a leave *and* a disconnect button.
            self._height += 50
        self._height += 50 * (len(custom_menu_entries))
        uiscale = ba.app.ui.uiscale
        ba.containerwidget(
            edit=self._root_widget,
            size=(self._width, self._height),
            scale=(2.15 if uiscale is ba.UIScale.SMALL else
                   1.6 if uiscale is ba.UIScale.MEDIUM else 1.0))
        h = 125.0
        v = (self._height - 80.0 if self._input_player else self._height - 60)
        h_offset = 0
        d_h_offset = 0
        v_offset = -50
        for _i in range(6 + len(custom_menu_entries)):
            positions.append((h, v, 1.0))
            v += v_offset
            h += h_offset
            h_offset += d_h_offset
        self._start_button = None
        ba.app.pause()

        # Player name if applicable.
        if self._input_player:
            player_name = self._input_player.getname()
            h, v, scale = positions[self._p_index]
            v += 35
            ba.textwidget(parent=self._root_widget,
                          position=(h - self._button_width / 2, v),
                          size=(self._button_width, self._button_height),
                          color=(1, 1, 1, 0.5),
                          scale=0.7,
                          h_align='center',
                          text=ba.Lstr(value=player_name))
        else:
            player_name = ''
        h, v, scale = positions[self._p_index]
        self._p_index += 1
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(h - self._button_width / 2, v),
                              size=(self._button_width, self._button_height),
                              scale=scale,
                              label=ba.Lstr(resource=self._r + '.resumeText'),
                              autoselect=self._use_autoselect,
                              on_activate_call=self._resume)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        # Add any custom options defined by the current game.
        for entry in custom_menu_entries:
            h, v, scale = positions[self._p_index]
            self._p_index += 1

            # Ask the entry whether we should resume when we call
            # it (defaults to true).
            resume = bool(entry.get('resume_on_call', True))

            if resume:
                call = ba.Call(self._resume_and_call, entry['call'])
            else:
                call = ba.Call(entry['call'], ba.WeakCall(self._resume))

            ba.buttonwidget(parent=self._root_widget,
                            position=(h - self._button_width / 2, v),
                            size=(self._button_width, self._button_height),
                            scale=scale,
                            on_activate_call=call,
                            label=entry['label'],
                            autoselect=self._use_autoselect)
        # Add a 'leave' button if the menu-owner has a player.
        if ((self._input_player or self._connected_to_remote_player)
                and not self._is_kiosk):
            h, v, scale = positions[self._p_index]
            self._p_index += 1
            btn = ba.buttonwidget(parent=self._root_widget,
                                  position=(h - self._button_width / 2, v),
                                  size=(self._button_width,
                                        self._button_height),
                                  scale=scale,
                                  on_activate_call=self._leave,
                                  label='',
                                  autoselect=self._use_autoselect)

            if (player_name != '' and player_name[0] != '<'
                    and player_name[-1] != '>'):
                txt = ba.Lstr(resource=self._r + '.justPlayerText',
                              subs=[('${NAME}', player_name)])
            else:
                txt = ba.Lstr(value=player_name)
            ba.textwidget(parent=self._root_widget,
                          position=(h, v + self._button_height *
                                    (0.64 if player_name != '' else 0.5)),
                          size=(0, 0),
                          text=ba.Lstr(resource=self._r + '.leaveGameText'),
                          scale=(0.83 if player_name != '' else 1.0),
                          color=(0.75, 1.0, 0.7),
                          h_align='center',
                          v_align='center',
                          draw_controller=btn,
                          maxwidth=self._button_width * 0.9)
            ba.textwidget(parent=self._root_widget,
                          position=(h, v + self._button_height * 0.27),
                          size=(0, 0),
                          text=txt,
                          color=(0.75, 1.0, 0.7),
                          h_align='center',
                          v_align='center',
                          draw_controller=btn,
                          scale=0.45,
                          maxwidth=self._button_width * 0.9)
        return h, v, scale

    def _change_replay_speed(self, offs: int) -> None:
        if not self._replay_speed_text:
            if ba.do_once():
                print('_change_replay_speed called without widget')
            return
        _ba.set_replay_speed_exponent(_ba.get_replay_speed_exponent() + offs)
        actual_speed = pow(2.0, _ba.get_replay_speed_exponent())
        ba.textwidget(edit=self._replay_speed_text,
                      text=ba.Lstr(resource='watchWindow.playbackSpeedText',
                                   subs=[('${SPEED}', str(actual_speed))]))

    def _quit(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.confirm import QuitWindow
        QuitWindow(origin_widget=self._quit_button)

    def _demo_menu_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.kiosk import KioskWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            KioskWindow(transition='in_left').get_root_widget())

    def _show_account_window(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account.settings import AccountSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            AccountSettingsWindow(
                origin_widget=self._gc_button).get_root_widget())

    def _on_store_pressed(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.store.browser import StoreBrowserWindow
        from bastd.ui.account import show_sign_in_prompt
        if _ba.get_account_state() != 'signed_in':
            show_sign_in_prompt()
            return
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            StoreBrowserWindow(
                origin_widget=self._store_button).get_root_widget())

    def _confirm_end_game(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.confirm import ConfirmWindow
        # FIXME: Currently we crash calling this on client-sessions.

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(ba.Lstr(resource=self._r + '.exitToMenuText'),
                      self._end_game,
                      cancel_is_selected=True)

    def _confirm_end_replay(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.confirm import ConfirmWindow

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(ba.Lstr(resource=self._r + '.exitToMenuText'),
                      self._end_game,
                      cancel_is_selected=True)

    def _confirm_leave_party(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.confirm import ConfirmWindow

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(ba.Lstr(resource=self._r + '.leavePartyConfirmText'),
                      self._leave_party,
                      cancel_is_selected=True)

    def _leave_party(self) -> None:
        _ba.disconnect_from_host()

    def _end_game(self) -> None:
        if not self._root_widget:
            return
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.return_to_main_menu_session_gracefully(reset_ui=False)

    def _leave(self) -> None:
        if self._input_player:
            self._input_player.remove_from_game()
        elif self._connected_to_remote_player:
            if self._input_device:
                self._input_device.remove_remote_player_from_game()
        self._resume()

    def _credits(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.creditslist import CreditsListWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            CreditsListWindow(
                origin_widget=self._credits_button).get_root_widget())

    def _howtoplay(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.helpui import HelpWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            HelpWindow(
                main_menu=True,
                origin_widget=self._how_to_play_button).get_root_widget())

    def _settings(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.allsettings import AllSettingsWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            AllSettingsWindow(
                origin_widget=self._settings_button).get_root_widget())

    def _resume_and_call(self, call: Callable[[], Any]) -> None:
        self._resume()
        call()

    def _do_game_service_press(self) -> None:
        self._save_state()
        _ba.show_online_score_ui()

    def _save_state(self) -> None:

        # Don't do this for the in-game menu.
        if self._in_game:
            return
        sel = self._root_widget.get_selected_child()
        if sel == self._start_button:
            ba.app.ui.main_menu_selection = 'Start'
        elif sel == self._gather_button:
            ba.app.ui.main_menu_selection = 'Gather'
        elif sel == self._watch_button:
            ba.app.ui.main_menu_selection = 'Watch'
        elif sel == self._how_to_play_button:
            ba.app.ui.main_menu_selection = 'HowToPlay'
        elif sel == self._credits_button:
            ba.app.ui.main_menu_selection = 'Credits'
        elif sel == self._settings_button:
            ba.app.ui.main_menu_selection = 'Settings'
        elif sel == self._gc_button:
            ba.app.ui.main_menu_selection = 'GameService'
        elif sel == self._store_button:
            ba.app.ui.main_menu_selection = 'Store'
        elif sel == self._quit_button:
            ba.app.ui.main_menu_selection = 'Quit'
        elif sel == self._demo_menu_button:
            ba.app.ui.main_menu_selection = 'DemoMenu'
        else:
            print('unknown widget in main menu store selection:', sel)
            ba.app.ui.main_menu_selection = 'Start'

    def _restore_state(self) -> None:
        # pylint: disable=too-many-branches

        # Don't do this for the in-game menu.
        if self._in_game:
            return
        sel_name = ba.app.ui.main_menu_selection
        sel: Optional[ba.Widget]
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
        elif sel_name == 'GameService':
            sel = self._gc_button
        elif sel_name == 'Store':
            sel = self._store_button
        elif sel_name == 'Quit':
            sel = self._quit_button
        elif sel_name == 'DemoMenu':
            sel = self._demo_menu_button
        else:
            sel = self._start_button
        if sel is not None:
            ba.containerwidget(edit=self._root_widget, selected_child=sel)

    def _gather_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.gather import GatherWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            GatherWindow(origin_widget=self._gather_button).get_root_widget())

    def _watch_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.watch import WatchWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            WatchWindow(origin_widget=self._watch_button).get_root_widget())

    def _play_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.play import PlayWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            PlayWindow(origin_widget=self._start_button).get_root_widget())

    def _resume(self) -> None:
        ba.app.resume()
        if self._root_widget:
            ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.clear_main_menu_window()

        # If there's callbacks waiting for this window to go away, call them.
        for call in ba.app.main_menu_resume_callbacks:
            call()
        del ba.app.main_menu_resume_callbacks[:]
