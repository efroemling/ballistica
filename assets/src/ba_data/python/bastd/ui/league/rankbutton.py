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
"""Provides a button showing league rank."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Tuple, Optional, Callable, Dict, Union


class LeagueRankButton:
    """Button showing league rank."""

    def __init__(self,
                 parent: ba.Widget,
                 position: Tuple[float, float],
                 size: Tuple[float, float],
                 scale: float,
                 on_activate_call: Callable[[], Any] = None,
                 transition_delay: float = None,
                 color: Tuple[float, float, float] = None,
                 textcolor: Tuple[float, float, float] = None,
                 smooth_update_delay: float = None):
        from ba.internal import get_cached_league_rank_data
        if on_activate_call is None:
            on_activate_call = ba.WeakCall(self._default_on_activate_call)
        self._on_activate_call = on_activate_call
        if smooth_update_delay is None:
            smooth_update_delay = 1000
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
        self._position: Tuple[float, float] = (0.0, 0.0)

        self._button = ba.buttonwidget(parent=parent,
                                       size=size,
                                       label='',
                                       button_type='square',
                                       scale=scale,
                                       autoselect=True,
                                       on_activate_call=self._on_activate,
                                       transition_delay=transition_delay,
                                       color=color)

        self._title_text = ba.textwidget(
            parent=parent,
            size=(0, 0),
            draw_controller=self._button,
            h_align='center',
            v_align='center',
            maxwidth=size[0] * scale * 0.85,
            text=ba.Lstr(
                resource='league.leagueRankText',
                fallback_resource='coopSelectWindow.powerRankingText'),
            color=self._header_color,
            flatness=1.0,
            shadow=1.0,
            scale=scale * 0.5,
            transition_delay=transition_delay)

        self._value_text = ba.textwidget(parent=parent,
                                         size=(0, 0),
                                         h_align='center',
                                         v_align='center',
                                         maxwidth=size[0] * scale * 0.85,
                                         text='-',
                                         draw_controller=self._button,
                                         big=True,
                                         scale=scale,
                                         transition_delay=transition_delay,
                                         color=textcolor)

        self._smooth_percent: Optional[float] = None
        self._percent: Optional[int] = None
        self._smooth_rank: Optional[float] = None
        self._rank: Optional[int] = None
        self._ticking_node: Optional[ba.Node] = None
        self._smooth_increase_speed = 1.0
        self._league: Optional[str] = None
        self._improvement_text: Optional[str] = None

        self._smooth_update_timer: Optional[ba.Timer] = None

        # Take note of our account state; we'll refresh later if this changes.
        self._account_state_num = _ba.get_account_state_num()
        self._last_power_ranking_query_time: Optional[float] = None
        self._doing_power_ranking_query = False
        self.set_position(position)
        self._bg_flash = False
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      timetype=ba.TimeType.REAL,
                                      repeat=True)
        self._update()

        # If we've got cached power-ranking data already, apply it.
        data = get_cached_league_rank_data()
        if data is not None:
            self._update_for_league_rank_data(data)

    def _on_activate(self) -> None:
        _ba.increment_analytics_count('League rank button press')
        self._on_activate_call()

    def __del__(self) -> None:
        if self._ticking_node is not None:
            self._ticking_node.delete()

    def _start_smooth_update(self) -> None:
        self._smooth_update_timer = ba.Timer(0.05,
                                             ba.WeakCall(self._smooth_update),
                                             repeat=True,
                                             timetype=ba.TimeType.REAL)

    def _smooth_update(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        try:
            if not self._button:
                return
            if self._ticking_node is None:
                with ba.Context('ui'):
                    self._ticking_node = ba.newnode(
                        'sound',
                        attrs={
                            'sound': ba.getsound('scoreIncrease'),
                            'positional': False
                        })
            self._bg_flash = (not self._bg_flash)
            color_used = ((self._color[0] * 2, self._color[1] * 2,
                           self._color[2] *
                           2) if self._bg_flash else self._color)
            textcolor_used = ((1, 1, 1) if self._bg_flash else self._textcolor)
            header_color_used = ((1, 1,
                                  1) if self._bg_flash else self._header_color)

            if self._rank is not None:
                assert self._smooth_rank is not None
                self._smooth_rank -= 1.0 * self._smooth_increase_speed
                finished = (int(self._smooth_rank) <= self._rank)
            elif self._smooth_percent is not None:
                self._smooth_percent += 1.0 * self._smooth_increase_speed
                assert self._percent is not None
                finished = (int(self._smooth_percent) >= self._percent)
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
                if self._ticking_node is not None:
                    self._ticking_node.delete()
                    self._ticking_node = None
                ba.playsound(ba.getsound('cashRegister2'))
                assert self._improvement_text is not None
                diff_text = ba.textwidget(
                    parent=self._parent,
                    size=(0, 0),
                    h_align='center',
                    v_align='center',
                    text='+' + self._improvement_text + '!',
                    position=(self._position[0] +
                              self._size[0] * 0.5 * self._scale,
                              self._position[1] +
                              self._size[1] * -0.2 * self._scale),
                    color=(0, 1, 0),
                    flatness=1.0,
                    shadow=0.0,
                    scale=self._scale * 0.7)

                def safe_delete(widget: ba.Widget) -> None:
                    if widget:
                        widget.delete()

                ba.timer(2.0,
                         ba.Call(safe_delete, diff_text),
                         timetype=ba.TimeType.REAL)
            status_text: Union[str, ba.Lstr]
            if self._rank is not None:
                assert self._smooth_rank is not None
                status_text = ba.Lstr(resource='numberText',
                                      subs=[('${NUMBER}',
                                             str(int(self._smooth_rank)))])
            elif self._smooth_percent is not None:
                status_text = str(int(self._smooth_percent)) + '%'
            else:
                status_text = '-'
            ba.textwidget(edit=self._value_text,
                          text=status_text,
                          color=textcolor_used)
            ba.textwidget(edit=self._title_text, color=header_color_used)
            ba.buttonwidget(edit=self._button, color=color_used)

        except Exception:
            ba.print_exception('Error doing smooth update.')
            self._smooth_update_timer = None

    def _update_for_league_rank_data(self, data: Optional[Dict[str,
                                                               Any]]) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        from ba.internal import get_league_rank_points

        # If our button has died, ignore.
        if not self._button:
            return

        status_text: Union[str, ba.Lstr]

        in_top = data is not None and data['rank'] is not None
        do_percent = False
        if data is None or _ba.get_account_state() != 'signed_in':
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
            if (self._smooth_rank is None or prev_league != self._league
                    or self._rank > int(self._smooth_rank)):
                self._smooth_rank = float(self._rank)
            status_text = ba.Lstr(resource='numberText',
                                  subs=[('${NUMBER}',
                                         str(int(self._smooth_rank)))])
        else:
            try:
                if not data['scores'] or data['scores'][-1][1] <= 0:
                    self._percent = self._rank = None
                    status_text = '-'
                else:
                    our_points = get_league_rank_points(data)
                    progress = float(our_points) / data['scores'][-1][1]
                    self._percent = int(progress * 100.0)
                    self._rank = None
                    do_percent = True
                    prev_league = self._league
                    self._league = data['l']

                    # If this is the first set, league has changed, or percent
                    # has decreased, snap the smooth value immediately.
                    if (self._smooth_percent is None
                            or prev_league != self._league
                            or self._percent < int(self._smooth_percent)):
                        self._smooth_percent = float(self._percent)
                    status_text = str(int(self._smooth_percent)) + '%'

            except Exception:
                ba.print_exception('Error updating power ranking.')
                self._percent = self._rank = None
                status_text = '-'

        # If we're doing a smooth update, set a timer.
        if (self._rank is not None and self._smooth_rank is not None
                and int(self._smooth_rank) != self._rank):
            self._improvement_text = str(-(int(self._rank) -
                                           int(self._smooth_rank)))
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
            ba.timer(self._smooth_update_delay,
                     ba.WeakCall(self._start_smooth_update),
                     timetype=ba.TimeType.REAL,
                     timeformat=ba.TimeFormat.MILLISECONDS)

        if (self._percent is not None and self._smooth_percent is not None
                and int(self._smooth_percent) != self._percent):
            self._improvement_text = str(
                (int(self._percent) - int(self._smooth_percent)))
            self._smooth_increase_speed = 0.3
            ba.timer(self._smooth_update_delay,
                     ba.WeakCall(self._start_smooth_update),
                     timetype=ba.TimeType.REAL,
                     timeformat=ba.TimeFormat.MILLISECONDS)

        if do_percent:
            ba.textwidget(
                edit=self._title_text,
                text=ba.Lstr(resource='coopSelectWindow.toRankedText'))
        else:
            try:
                assert data is not None
                txt = ba.Lstr(
                    resource='league.leagueFullText',
                    subs=[
                        (
                            '${NAME}',
                            ba.Lstr(translate=('leagueNames', data['l']['n'])),
                        ),
                    ],
                )
                t_color = data['l']['c']
            except Exception:
                txt = ba.Lstr(
                    resource='league.leagueRankText',
                    fallback_resource='coopSelectWindow.powerRankingText')
                t_color = ba.app.ui.title_color
            ba.textwidget(edit=self._title_text, text=txt, color=t_color)
        ba.textwidget(edit=self._value_text, text=status_text)

    def _on_power_ranking_query_response(
            self, data: Optional[Dict[str, Any]]) -> None:
        from ba.internal import cache_league_rank_data
        self._doing_power_ranking_query = False
        cache_league_rank_data(data)
        self._update_for_league_rank_data(data)

    def _update(self) -> None:
        cur_time = ba.time(ba.TimeType.REAL)

        # If our account state has changed, refresh our UI.
        account_state_num = _ba.get_account_state_num()
        if account_state_num != self._account_state_num:
            self._account_state_num = account_state_num

            # And power ranking too...
            if not self._doing_power_ranking_query:
                self._last_power_ranking_query_time = None

        # Send off a new power-ranking query if its been
        # long enough or whatnot.
        if not self._doing_power_ranking_query and (
                self._last_power_ranking_query_time is None
                or cur_time - self._last_power_ranking_query_time > 30.0):
            self._last_power_ranking_query_time = cur_time
            self._doing_power_ranking_query = True
            _ba.power_ranking_query(
                callback=ba.WeakCall(self._on_power_ranking_query_response))

    def _default_on_activate_call(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.league.rankwindow import LeagueRankWindow
        LeagueRankWindow(modal=True, origin_widget=self._button)

    def set_position(self, position: Tuple[float, float]) -> None:
        """Set the button's position."""
        self._position = position
        if not self._button:
            return
        ba.buttonwidget(edit=self._button, position=self._position)
        ba.textwidget(
            edit=self._title_text,
            position=(self._position[0] + self._size[0] * 0.5 * self._scale,
                      self._position[1] + self._size[1] * 0.82 * self._scale))
        ba.textwidget(
            edit=self._value_text,
            position=(self._position[0] + self._size[0] * 0.5 * self._scale,
                      self._position[1] + self._size[1] * 0.36 * self._scale))

    def get_button(self) -> ba.Widget:
        """Return the underlying button ba.Widget>"""
        return self._button
