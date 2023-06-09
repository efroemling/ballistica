# Released under the MIT License. See LICENSE for details.
#
"""Provides a button showing league rank."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class LeagueRankButton:
    """Button showing league rank."""

    def __init__(
        self,
        parent: bui.Widget,
        position: tuple[float, float],
        size: tuple[float, float],
        scale: float,
        on_activate_call: Callable[[], Any] | None = None,
        transition_delay: float | None = None,
        color: tuple[float, float, float] | None = None,
        textcolor: tuple[float, float, float] | None = None,
        smooth_update_delay: float | None = None,
    ):
        if on_activate_call is None:
            on_activate_call = bui.WeakCall(self._default_on_activate_call)
        self._on_activate_call = on_activate_call
        if smooth_update_delay is None:
            smooth_update_delay = 1.0
        self._smooth_update_delay = smooth_update_delay
        self._size = size
        self._scale = scale
        if color is None:
            color = (0.5, 0.6, 0.5)
        if textcolor is None:
            textcolor = (1, 1, 1)
        self._color = color
        self._textcolor = textcolor
        self._header_color = (0.8, 0.8, 2.0)
        self._parent = parent
        self._position: tuple[float, float] = (0.0, 0.0)

        self._button = bui.buttonwidget(
            parent=parent,
            size=size,
            label='',
            button_type='square',
            scale=scale,
            autoselect=True,
            on_activate_call=self._on_activate,
            transition_delay=transition_delay,
            color=color,
        )

        self._title_text = bui.textwidget(
            parent=parent,
            size=(0, 0),
            draw_controller=self._button,
            h_align='center',
            v_align='center',
            maxwidth=size[0] * scale * 0.85,
            text=bui.Lstr(
                resource='league.leagueRankText',
                fallback_resource='coopSelectWindow.powerRankingText',
            ),
            color=self._header_color,
            flatness=1.0,
            shadow=1.0,
            scale=scale * 0.5,
            transition_delay=transition_delay,
        )

        self._value_text = bui.textwidget(
            parent=parent,
            size=(0, 0),
            h_align='center',
            v_align='center',
            maxwidth=size[0] * scale * 0.85,
            text='-',
            draw_controller=self._button,
            big=True,
            scale=scale,
            transition_delay=transition_delay,
            color=textcolor,
        )

        plus = bui.app.plus
        assert plus is not None

        self._smooth_percent: float | None = None
        self._percent: int | None = None
        self._smooth_rank: float | None = None
        self._rank: int | None = None
        self._ticking_sound: bui.Sound | None = None
        self._smooth_increase_speed = 1.0
        self._league: str | None = None
        self._improvement_text: str | None = None

        self._smooth_update_timer: bui.AppTimer | None = None

        # Take note of our account state; we'll refresh later if this changes.
        self._account_state_num = plus.get_v1_account_state_num()
        self._last_power_ranking_query_time: float | None = None
        self._doing_power_ranking_query = False
        self.set_position(position)
        self._bg_flash = False
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update()

        # If we've got cached power-ranking data already, apply it.
        assert bui.app.classic is not None
        data = bui.app.classic.accounts.get_cached_league_rank_data()
        if data is not None:
            self._update_for_league_rank_data(data)

    def _on_activate(self) -> None:
        bui.increment_analytics_count('League rank button press')
        self._on_activate_call()

    def __del__(self) -> None:
        if self._ticking_sound is not None:
            self._ticking_sound.stop()
            self._ticking_sound = None

    def _start_smooth_update(self) -> None:
        self._smooth_update_timer = bui.AppTimer(
            0.05, bui.WeakCall(self._smooth_update), repeat=True
        )

    def _smooth_update(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        try:
            if not self._button:
                return
            if self._ticking_sound is None:
                self._ticking_sound = bui.getsound('scoreIncrease')
                self._ticking_sound.play()
            self._bg_flash = not self._bg_flash
            color_used = (
                (self._color[0] * 2, self._color[1] * 2, self._color[2] * 2)
                if self._bg_flash
                else self._color
            )
            textcolor_used = (1, 1, 1) if self._bg_flash else self._textcolor
            header_color_used = (
                (1, 1, 1) if self._bg_flash else self._header_color
            )

            if self._rank is not None:
                assert self._smooth_rank is not None
                self._smooth_rank -= 1.0 * self._smooth_increase_speed
                finished = int(self._smooth_rank) <= self._rank
            elif self._smooth_percent is not None:
                self._smooth_percent += 1.0 * self._smooth_increase_speed
                assert self._percent is not None
                finished = int(self._smooth_percent) >= self._percent
            else:
                finished = True
            if finished:
                if self._rank is not None:
                    self._smooth_rank = float(self._rank)
                elif self._percent is not None:
                    self._smooth_percent = float(self._percent)
                color_used = self._color
                textcolor_used = self._textcolor
                self._smooth_update_timer = None
                if self._ticking_sound is not None:
                    self._ticking_sound.stop()
                    self._ticking_sound = None
                bui.getsound('cashRegister2').play()
                assert self._improvement_text is not None
                diff_text = bui.textwidget(
                    parent=self._parent,
                    size=(0, 0),
                    h_align='center',
                    v_align='center',
                    text='+' + self._improvement_text + '!',
                    position=(
                        self._position[0] + self._size[0] * 0.5 * self._scale,
                        self._position[1] + self._size[1] * -0.2 * self._scale,
                    ),
                    color=(0, 1, 0),
                    flatness=1.0,
                    shadow=0.0,
                    scale=self._scale * 0.7,
                )

                def safe_delete(widget: bui.Widget) -> None:
                    if widget:
                        widget.delete()

                bui.apptimer(2.0, bui.Call(safe_delete, diff_text))
            status_text: str | bui.Lstr
            if self._rank is not None:
                assert self._smooth_rank is not None
                status_text = bui.Lstr(
                    resource='numberText',
                    subs=[('${NUMBER}', str(int(self._smooth_rank)))],
                )
            elif self._smooth_percent is not None:
                status_text = str(int(self._smooth_percent)) + '%'
            else:
                status_text = '-'
            bui.textwidget(
                edit=self._value_text, text=status_text, color=textcolor_used
            )
            bui.textwidget(edit=self._title_text, color=header_color_used)
            bui.buttonwidget(edit=self._button, color=color_used)

        except Exception:
            logging.exception('Error doing smooth update.')
            self._smooth_update_timer = None

    def _update_for_league_rank_data(self, data: dict[str, Any] | None) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        plus = bui.app.plus
        assert plus is not None

        # If our button has died, ignore.
        if not self._button:
            return

        status_text: str | bui.Lstr

        in_top = data is not None and data['rank'] is not None
        do_percent = False
        if data is None or plus.get_v1_account_state() != 'signed_in':
            self._percent = self._rank = None
            status_text = '-'
        elif in_top:
            self._percent = None
            self._rank = data['rank']
            prev_league = self._league
            self._league = data['l']

            # If this is the first set, league has changed, or rank has gotten
            # worse, snap the smooth value immediately.
            assert self._rank is not None
            if (
                self._smooth_rank is None
                or prev_league != self._league
                or self._rank > int(self._smooth_rank)
            ):
                self._smooth_rank = float(self._rank)
            status_text = bui.Lstr(
                resource='numberText',
                subs=[('${NUMBER}', str(int(self._smooth_rank)))],
            )
        else:
            try:
                if not data['scores'] or data['scores'][-1][1] <= 0:
                    self._percent = self._rank = None
                    status_text = '-'
                else:
                    assert bui.app.classic is not None
                    our_points = (
                        bui.app.classic.accounts.get_league_rank_points(data)
                    )
                    progress = float(our_points) / data['scores'][-1][1]
                    self._percent = int(progress * 100.0)
                    self._rank = None
                    do_percent = True
                    prev_league = self._league
                    self._league = data['l']

                    # If this is the first set, league has changed, or percent
                    # has decreased, snap the smooth value immediately.
                    if (
                        self._smooth_percent is None
                        or prev_league != self._league
                        or self._percent < int(self._smooth_percent)
                    ):
                        self._smooth_percent = float(self._percent)
                    status_text = str(int(self._smooth_percent)) + '%'

            except Exception:
                logging.exception('Error updating power ranking.')
                self._percent = self._rank = None
                status_text = '-'

        # If we're doing a smooth update, set a timer.
        if (
            self._rank is not None
            and self._smooth_rank is not None
            and int(self._smooth_rank) != self._rank
        ):
            self._improvement_text = str(
                -(int(self._rank) - int(self._smooth_rank))
            )
            diff = abs(self._rank - self._smooth_rank)
            if diff > 100:
                self._smooth_increase_speed = diff / 80.0
            elif diff > 50:
                self._smooth_increase_speed = diff / 70.0
            elif diff > 25:
                self._smooth_increase_speed = diff / 55.0
            else:
                self._smooth_increase_speed = diff / 40.0
            self._smooth_increase_speed = max(0.4, self._smooth_increase_speed)
            bui.apptimer(
                self._smooth_update_delay,
                bui.WeakCall(self._start_smooth_update),
            )

        if (
            self._percent is not None
            and self._smooth_percent is not None
            and int(self._smooth_percent) != self._percent
        ):
            self._improvement_text = str(
                (int(self._percent) - int(self._smooth_percent))
            )
            self._smooth_increase_speed = 0.3
            bui.apptimer(
                self._smooth_update_delay,
                bui.WeakCall(self._start_smooth_update),
            )

        if do_percent:
            bui.textwidget(
                edit=self._title_text,
                text=bui.Lstr(resource='coopSelectWindow.toRankedText'),
            )
        else:
            try:
                assert data is not None
                txt = bui.Lstr(
                    resource='league.leagueFullText',
                    subs=[
                        (
                            '${NAME}',
                            bui.Lstr(translate=('leagueNames', data['l']['n'])),
                        ),
                    ],
                )
                t_color = data['l']['c']
            except Exception:
                txt = bui.Lstr(
                    resource='league.leagueRankText',
                    fallback_resource='coopSelectWindow.powerRankingText',
                )
                assert bui.app.classic is not None
                t_color = bui.app.ui_v1.title_color
            bui.textwidget(edit=self._title_text, text=txt, color=t_color)
        bui.textwidget(edit=self._value_text, text=status_text)

    def _on_power_ranking_query_response(
        self, data: dict[str, Any] | None
    ) -> None:
        self._doing_power_ranking_query = False
        assert bui.app.classic is not None
        bui.app.classic.accounts.cache_league_rank_data(data)
        self._update_for_league_rank_data(data)

    def _update(self) -> None:
        cur_time = bui.apptime()

        plus = bui.app.plus
        assert plus is not None

        # If our account state has changed, refresh our UI.
        account_state_num = plus.get_v1_account_state_num()
        if account_state_num != self._account_state_num:
            self._account_state_num = account_state_num

            # And power ranking too...
            if not self._doing_power_ranking_query:
                self._last_power_ranking_query_time = None

        # Send off a new power-ranking query if its been
        # long enough or whatnot.
        if not self._doing_power_ranking_query and (
            self._last_power_ranking_query_time is None
            or cur_time - self._last_power_ranking_query_time > 30.0
        ):
            self._last_power_ranking_query_time = cur_time
            self._doing_power_ranking_query = True
            plus.power_ranking_query(
                callback=bui.WeakCall(self._on_power_ranking_query_response)
            )

    def _default_on_activate_call(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.league.rankwindow import LeagueRankWindow

        LeagueRankWindow(modal=True, origin_widget=self._button)

    def set_position(self, position: tuple[float, float]) -> None:
        """Set the button's position."""
        self._position = position
        if not self._button:
            return
        bui.buttonwidget(edit=self._button, position=self._position)
        bui.textwidget(
            edit=self._title_text,
            position=(
                self._position[0] + self._size[0] * 0.5 * self._scale,
                self._position[1] + self._size[1] * 0.82 * self._scale,
            ),
        )
        bui.textwidget(
            edit=self._value_text,
            position=(
                self._position[0] + self._size[0] * 0.5 * self._scale,
                self._position[1] + self._size[1] * 0.36 * self._scale,
            ),
        )

    def get_button(self) -> bui.Widget:
        """Return the underlying button bui.Widget>"""
        return self._button
