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
"""Functionality related to the final screen in free-for-all games."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.activity.multiteamscore import MultiTeamScoreScreenActivity

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Set, Tuple


class FreeForAllVictoryScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Score screen shown at after free-for-all rounds."""

    def __init__(self, settings: dict):
        super().__init__(settings=settings)

        # Keep prev activity alive while we fade in.
        self.transition_time = 0.5
        self._cymbal_sound = ba.getsound('cymbal')

    def on_begin(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bastd.actor.text import Text
        from bastd.actor.image import Image
        ba.set_analytics_screen('FreeForAll Score Screen')
        super().on_begin()

        y_base = 100.0
        ts_h_offs = -305.0
        tdelay = 1.0
        scale = 1.2
        spacing = 37.0

        # We include name and previous score in the sort to reduce the amount
        # of random jumping around the list we do in cases of ties.
        player_order_prev = list(self.players)
        player_order_prev.sort(
            reverse=True,
            key=lambda p: (
                p.team.sessionteam.customdata['previous_score'],
                p.getname(full=True),
            ))
        player_order = list(self.players)
        player_order.sort(reverse=True,
                          key=lambda p: (
                              p.team.sessionteam.customdata['score'],
                              p.team.sessionteam.customdata['score'],
                              p.getname(full=True),
                          ))

        v_offs = -74.0 + spacing * len(player_order_prev) * 0.5
        delay1 = 1.3 + 0.1
        delay2 = 2.9 + 0.1
        delay3 = 2.9 + 0.1
        order_change = player_order != player_order_prev

        if order_change:
            delay3 += 1.5

        ba.timer(0.3, ba.Call(ba.playsound, self._score_display_sound))
        results = self.settings_raw['results']
        assert isinstance(results, ba.GameResults)
        self.show_player_scores(delay=0.001,
                                results=results,
                                scale=1.2,
                                x_offset=-110.0)

        sound_times: Set[float] = set()

        def _scoretxt(text: str,
                      x_offs: float,
                      y_offs: float,
                      highlight: bool,
                      delay: float,
                      extrascale: float,
                      flash: bool = False) -> Text:
            return Text(text,
                        position=(ts_h_offs + x_offs * scale,
                                  y_base + (y_offs + v_offs + 2.0) * scale),
                        scale=scale * extrascale,
                        color=((1.0, 0.7, 0.3, 1.0) if highlight else
                               (0.7, 0.7, 0.7, 0.7)),
                        h_align=Text.HAlign.RIGHT,
                        transition=Text.Transition.IN_LEFT,
                        transition_delay=tdelay + delay,
                        flash=flash).autoretain()

        v_offs -= spacing
        slide_amt = 0.0
        transtime = 0.250
        transtime2 = 0.250

        session = self.session
        assert isinstance(session, ba.FreeForAllSession)
        title = Text(ba.Lstr(resource='firstToSeriesText',
                             subs=[('${COUNT}',
                                    str(session.get_ffa_series_length()))]),
                     scale=1.05 * scale,
                     position=(ts_h_offs - 0.0 * scale,
                               y_base + (v_offs + 50.0) * scale),
                     h_align=Text.HAlign.CENTER,
                     color=(0.5, 0.5, 0.5, 0.5),
                     transition=Text.Transition.IN_LEFT,
                     transition_delay=tdelay).autoretain()

        v_offs -= 25
        v_offs_start = v_offs

        ba.timer(
            tdelay + delay3,
            ba.WeakCall(
                self._safe_animate, title.position_combine, 'input0', {
                    0.0: ts_h_offs - 0.0 * scale,
                    transtime2: ts_h_offs - (0.0 + slide_amt) * scale
                }))

        for i, player in enumerate(player_order_prev):
            v_offs_2 = v_offs_start - spacing * (player_order.index(player))
            ba.timer(tdelay + 0.3,
                     ba.Call(ba.playsound, self._score_display_sound_small))
            if order_change:
                ba.timer(tdelay + delay2 + 0.1,
                         ba.Call(ba.playsound, self._cymbal_sound))
            img = Image(player.get_icon(),
                        position=(ts_h_offs - 72.0 * scale,
                                  y_base + (v_offs + 15.0) * scale),
                        scale=(30.0 * scale, 30.0 * scale),
                        transition=Image.Transition.IN_LEFT,
                        transition_delay=tdelay).autoretain()
            ba.timer(
                tdelay + delay2,
                ba.WeakCall(
                    self._safe_animate, img.position_combine, 'input1', {
                        0: y_base + (v_offs + 15.0) * scale,
                        transtime: y_base + (v_offs_2 + 15.0) * scale
                    }))
            ba.timer(
                tdelay + delay3,
                ba.WeakCall(
                    self._safe_animate, img.position_combine, 'input0', {
                        0: ts_h_offs - 72.0 * scale,
                        transtime2: ts_h_offs - (72.0 + slide_amt) * scale
                    }))
            txt = Text(ba.Lstr(value=player.getname(full=True)),
                       maxwidth=130.0,
                       scale=0.75 * scale,
                       position=(ts_h_offs - 50.0 * scale,
                                 y_base + (v_offs + 15.0) * scale),
                       h_align=Text.HAlign.LEFT,
                       v_align=Text.VAlign.CENTER,
                       color=ba.safecolor(player.team.color + (1, )),
                       transition=Text.Transition.IN_LEFT,
                       transition_delay=tdelay).autoretain()
            ba.timer(
                tdelay + delay2,
                ba.WeakCall(
                    self._safe_animate, txt.position_combine, 'input1', {
                        0: y_base + (v_offs + 15.0) * scale,
                        transtime: y_base + (v_offs_2 + 15.0) * scale
                    }))
            ba.timer(
                tdelay + delay3,
                ba.WeakCall(
                    self._safe_animate, txt.position_combine, 'input0', {
                        0: ts_h_offs - 50.0 * scale,
                        transtime2: ts_h_offs - (50.0 + slide_amt) * scale
                    }))

            txt_num = Text('#' + str(i + 1),
                           scale=0.55 * scale,
                           position=(ts_h_offs - 95.0 * scale,
                                     y_base + (v_offs + 8.0) * scale),
                           h_align=Text.HAlign.RIGHT,
                           color=(0.6, 0.6, 0.6, 0.6),
                           transition=Text.Transition.IN_LEFT,
                           transition_delay=tdelay).autoretain()
            ba.timer(
                tdelay + delay3,
                ba.WeakCall(
                    self._safe_animate, txt_num.position_combine, 'input0', {
                        0: ts_h_offs - 95.0 * scale,
                        transtime2: ts_h_offs - (95.0 + slide_amt) * scale
                    }))

            s_txt = _scoretxt(
                str(player.team.sessionteam.customdata['previous_score']), 80,
                0, False, 0, 1.0)
            ba.timer(
                tdelay + delay2,
                ba.WeakCall(
                    self._safe_animate, s_txt.position_combine, 'input1', {
                        0: y_base + (v_offs + 2.0) * scale,
                        transtime: y_base + (v_offs_2 + 2.0) * scale
                    }))
            ba.timer(
                tdelay + delay3,
                ba.WeakCall(
                    self._safe_animate, s_txt.position_combine, 'input0', {
                        0: ts_h_offs + 80.0 * scale,
                        transtime2: ts_h_offs + (80.0 - slide_amt) * scale
                    }))

            score_change = (
                player.team.sessionteam.customdata['score'] -
                player.team.sessionteam.customdata['previous_score'])
            if score_change > 0:
                xval = 113
                yval = 3.0
                s_txt_2 = _scoretxt('+' + str(score_change),
                                    xval,
                                    yval,
                                    True,
                                    0,
                                    0.7,
                                    flash=True)
                ba.timer(
                    tdelay + delay2,
                    ba.WeakCall(
                        self._safe_animate, s_txt_2.position_combine, 'input1',
                        {
                            0: y_base + (v_offs + yval + 2.0) * scale,
                            transtime: y_base + (v_offs_2 + yval + 2.0) * scale
                        }))
                ba.timer(
                    tdelay + delay3,
                    ba.WeakCall(
                        self._safe_animate, s_txt_2.position_combine, 'input0',
                        {
                            0: ts_h_offs + xval * scale,
                            transtime2: ts_h_offs + (xval - slide_amt) * scale
                        }))

                def _safesetattr(node: Optional[ba.Node], attr: str,
                                 value: Any) -> None:
                    if node:
                        setattr(node, attr, value)

                ba.timer(
                    tdelay + delay1,
                    ba.Call(_safesetattr, s_txt.node, 'color', (1, 1, 1, 1)))
                for j in range(score_change):
                    ba.timer((tdelay + delay1 + 0.15 * j),
                             ba.Call(
                                 _safesetattr, s_txt.node, 'text',
                                 str(player.team.sessionteam.
                                     customdata['previous_score'] + j + 1)))
                    tfin = tdelay + delay1 + 0.15 * j
                    if tfin not in sound_times:
                        sound_times.add(tfin)
                        ba.timer(
                            tfin,
                            ba.Call(ba.playsound,
                                    self._score_display_sound_small))
            v_offs -= spacing

    def _safe_animate(self, node: Optional[ba.Node], attr: str,
                      keys: Dict[float, float]) -> None:
        """Run an animation on a node if the node still exists."""
        if node:
            ba.animate(node, attr, keys)
