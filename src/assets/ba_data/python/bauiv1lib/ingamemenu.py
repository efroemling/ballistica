# Released under the MIT License. See LICENSE for details.
#
"""Implements the in-gmae menu window."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Callable


class InGameMenuWindow(bui.MainWindow):
    """The menu that can be invoked while in a game."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        # Make a vanilla container; we'll modify it to our needs in
        # refresh.
        super().__init__(
            root_widget=bui.containerwidget(
                toolbar_visibility=('menu_in_game')
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        # Grab this stuff in case it changes.
        # self._is_demo = bui.app.env.demo
        # self._is_arcade = bui.app.env.arcade

        self._p_index = 0
        self._use_autoselect = True
        self._button_width = 200.0
        self._button_height = 45.0
        self._width = 100.0
        self._height = 100.0

        self._refresh()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    def _refresh(self) -> None:

        # Clear everything that was there.
        children = self._root_widget.get_children()
        for child in children:
            child.delete()

        self._r = 'mainMenu'

        self._input_device = input_device = bs.get_main_ui_input_device()

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

        self._refresh_in_game(positions)

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
                label=bui.Lstr(resource=f'{self._r}.leavePartyText'),
                on_activate_call=self._confirm_leave_party,
            )

        # Add speed-up/slow-down buttons for replays. Ideally this
        # should be part of a fading-out playback bar like most media
        # players but this works for now.
        if bs.is_in_replay():
            b_size = 50.0
            b_buffer_1 = 50.0
            b_buffer_2 = 10.0
            t_scale = 0.75
            assert bui.app.classic is not None
            uiscale = bui.app.ui_v1.uiscale
            if uiscale is bui.UIScale.SMALL:
                b_size *= 0.6
                b_buffer_1 *= 0.8
                b_buffer_2 *= 1.0
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
                position=(h, v + v_offs + 15 * t_scale),
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
                    h - b_size - b_buffer_1,
                    v - b_size - b_buffer_2 + v_offs,
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
                    h - b_size * 0.5 - b_buffer_1,
                    v - b_size * 0.5 - b_buffer_2 + 5 * t_scale + v_offs,
                ),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=3.0 * t_scale,
            )
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(h + b_buffer_1, v - b_size - b_buffer_2 + v_offs),
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
                    h + b_size * 0.5 + b_buffer_1,
                    v - b_size * 0.5 - b_buffer_2 + 5 * t_scale + v_offs,
                ),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=3.0 * t_scale,
            )
            self._pause_resume_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(h - b_size * 0.5, v - b_size - b_buffer_2 + v_offs),
                button_type='square',
                size=(b_size, b_size),
                label=bui.charstr(
                    bui.SpecialChar.PLAY_BUTTON
                    if bs.is_replay_paused()
                    else bui.SpecialChar.PAUSE_BUTTON
                ),
                autoselect=True,
                on_activate_call=bui.Call(self._pause_or_resume_replay),
            )
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    h - b_size * 1.5 - b_buffer_1 * 2,
                    v - b_size - b_buffer_2 + v_offs,
                ),
                button_type='square',
                size=(b_size, b_size),
                label='',
                autoselect=True,
                on_activate_call=bui.WeakCall(self._rewind_replay),
            )
            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                # text='<<',
                text=bui.charstr(bui.SpecialChar.REWIND_BUTTON),
                position=(
                    h - b_size - b_buffer_1 * 2,
                    v - b_size * 0.5 - b_buffer_2 + 5 * t_scale + v_offs,
                ),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=2.0 * t_scale,
            )
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    h + b_size * 0.5 + b_buffer_1 * 2,
                    v - b_size - b_buffer_2 + v_offs,
                ),
                button_type='square',
                size=(b_size, b_size),
                label='',
                autoselect=True,
                on_activate_call=bui.WeakCall(self._forward_replay),
            )
            bui.textwidget(
                parent=self._root_widget,
                draw_controller=btn,
                # text='>>',
                text=bui.charstr(bui.SpecialChar.FAST_FORWARD_BUTTON),
                position=(
                    h + b_size + b_buffer_1 * 2,
                    v - b_size * 0.5 - b_buffer_2 + 5 * t_scale + v_offs,
                ),
                h_align='center',
                v_align='center',
                size=(0, 0),
                scale=2.0 * t_scale,
            )

    def _rewind_replay(self) -> None:
        bs.seek_replay(-2 * pow(2, bs.get_replay_speed_exponent()))

    def _forward_replay(self) -> None:
        bs.seek_replay(2 * pow(2, bs.get_replay_speed_exponent()))

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
        variant = bui.app.env.variant
        vart = type(variant)
        arcade_or_demo = variant is vart.ARCADE or variant is vart.DEMO

        self._width = 250.0
        self._height = 250.0 if self._input_player else 180.0
        if arcade_or_demo and self._input_player:
            self._height -= 40
        # if not self._have_settings_button:
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
                else 1.6 if uiscale is bui.UIScale.MEDIUM else 1.0
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
            label=bui.Lstr(resource=f'{self._r}.resumeText'),
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
            arcade_or_demo
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
                    resource=f'{self._r}.justPlayerText',
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
                text=bui.Lstr(resource=f'{self._r}.leaveGameText'),
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

    def _pause_or_resume_replay(self) -> None:
        if bs.is_replay_paused():
            bs.resume_replay()
            bui.buttonwidget(
                edit=self._pause_resume_button,
                label=bui.charstr(bui.SpecialChar.PAUSE_BUTTON),
            )
        else:
            bs.pause_replay()
            bui.buttonwidget(
                edit=self._pause_resume_button,
                label=bui.charstr(bui.SpecialChar.PLAY_BUTTON),
            )

    def _is_benchmark(self) -> bool:
        session = bs.get_foreground_host_session()
        return getattr(session, 'benchmark_type', None) == 'cpu' or (
            bui.app.classic is not None
            and bui.app.classic.stress_test_update_timer is not None
        )

    def _confirm_end_game(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        # FIXME: Currently we crash calling this on client-sessions.

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(
            bui.Lstr(resource=f'{self._r}.exitToMenuText'),
            self._end_game,
            cancel_is_selected=True,
        )

    def _confirm_end_test(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(
            bui.Lstr(resource=f'{self._r}.exitToMenuText'),
            self._end_game,
            cancel_is_selected=True,
        )

    def _confirm_end_replay(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(
            bui.Lstr(resource=f'{self._r}.exitToMenuText'),
            self._end_game,
            cancel_is_selected=True,
        )

    def _confirm_leave_party(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.confirm import ConfirmWindow

        # Select cancel by default; this occasionally gets called by accident
        # in a fit of button mashing and this will help reduce damage.
        ConfirmWindow(
            bui.Lstr(resource=f'{self._r}.leavePartyConfirmText'),
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

    def _resume_and_call(self, call: Callable[[], Any]) -> None:
        self._resume()
        call()

    def _resume(self) -> None:
        classic = bui.app.classic

        assert classic is not None
        classic.resume()

        bui.app.ui_v1.clear_main_window()

        # If there's callbacks waiting for us to resume, call them.
        for call in classic.main_menu_resume_callbacks:
            try:
                call()
            except Exception:
                logging.exception('Error in classic resume callback.')

        classic.main_menu_resume_callbacks.clear()

    # def __del__(self) -> None:
    #     self._resume()
