# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the final screen in free-for-all games."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.activity.multiteamscore import MultiTeamScoreScreenActivity

if TYPE_CHECKING:
    from typing import Any


class FreeForAllVictoryScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Score screen shown at after free-for-all rounds."""

    def __init__(self, settings: dict):
        super().__init__(settings=settings)

        # Keep prev activity alive while we fade in.
        self.transition_time = 0.5
        self._cymbal_sound = bs.getsound('cymbal')

    @override
    def on_begin(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bascenev1lib.actor.text import Text
        from bascenev1lib.actor.image import Image

        bs.set_analytics_screen('FreeForAll Score Screen')
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
            ),
        )
        player_order = list(self.players)
        player_order.sort(
            reverse=True,
            key=lambda p: (
                p.team.sessionteam.customdata['score'],
                p.team.sessionteam.customdata['score'],
                p.getname(full=True),
            ),
        )

        v_offs = -74.0 + spacing * len(player_order_prev) * 0.5
        delay1 = 1.3 + 0.1
        delay2 = 2.9 + 0.1
        delay3 = 2.9 + 0.1
        order_change = player_order != player_order_prev

        if order_change:
            delay3 += 1.5

        bs.timer(0.3, self._score_display_sound.play)
        results = self.settings_raw['results']
        assert isinstance(results, bs.GameResults)
        self.show_player_scores(
            delay=0.001, results=results, scale=1.2, x_offset=-110.0
        )

        sound_times: set[float] = set()

        def _scoretxt(
            text: str,
            x_offs: float,
            y_offs: float,
            highlight: bool,
            delay: float,
            extrascale: float,
            flash: bool = False,
        ) -> Text:
            # pylint: disable=too-many-positional-arguments
            return Text(
                text,
                position=(
                    ts_h_offs + x_offs * scale,
                    y_base + (y_offs + v_offs + 2.0) * scale,
                ),
                scale=scale * extrascale,
                color=(
                    (1.0, 0.7, 0.3, 1.0) if highlight else (0.7, 0.7, 0.7, 0.7)
                ),
                h_align=Text.HAlign.RIGHT,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tdelay + delay,
                flash=flash,
            ).autoretain()

        v_offs -= spacing
        slide_amt = 0.0
        transtime = 0.250
        transtime2 = 0.250

        session = self.session
        assert isinstance(session, bs.FreeForAllSession)
        title = Text(
            bs.Lstr(
                resource='firstToSeriesText',
                subs=[('${COUNT}', str(session.get_ffa_series_length()))],
            ),
            scale=1.05 * scale,
            position=(
                ts_h_offs - 0.0 * scale,
                y_base + (v_offs + 50.0) * scale,
            ),
            h_align=Text.HAlign.CENTER,
            color=(0.5, 0.5, 0.5, 0.5),
            transition=Text.Transition.IN_LEFT,
            transition_delay=tdelay,
        ).autoretain()

        v_offs -= 25
        v_offs_start = v_offs

        bs.timer(
            tdelay + delay3,
            bs.WeakCall(
                self._safe_animate,
                title.position_combine,
                'input0',
                {
                    0.0: ts_h_offs - 0.0 * scale,
                    transtime2: ts_h_offs - (0.0 + slide_amt) * scale,
                },
            ),
        )

        for i, player in enumerate(player_order_prev):
            v_offs_2 = v_offs_start - spacing * (player_order.index(player))
            bs.timer(tdelay + 0.3, self._score_display_sound_small.play)
            if order_change:
                bs.timer(tdelay + delay2 + 0.1, self._cymbal_sound.play)
            img = Image(
                player.get_icon(),
                position=(
                    ts_h_offs - 72.0 * scale,
                    y_base + (v_offs + 15.0) * scale,
                ),
                scale=(30.0 * scale, 30.0 * scale),
                transition=Image.Transition.IN_LEFT,
                transition_delay=tdelay,
            ).autoretain()
            bs.timer(
                tdelay + delay2,
                bs.WeakCall(
                    self._safe_animate,
                    img.position_combine,
                    'input1',
                    {
                        0: y_base + (v_offs + 15.0) * scale,
                        transtime: y_base + (v_offs_2 + 15.0) * scale,
                    },
                ),
            )
            bs.timer(
                tdelay + delay3,
                bs.WeakCall(
                    self._safe_animate,
                    img.position_combine,
                    'input0',
                    {
                        0: ts_h_offs - 72.0 * scale,
                        transtime2: ts_h_offs - (72.0 + slide_amt) * scale,
                    },
                ),
            )
            txt = Text(
                bs.Lstr(value=player.getname(full=True)),
                maxwidth=130.0,
                scale=0.75 * scale,
                position=(
                    ts_h_offs - 50.0 * scale,
                    y_base + (v_offs + 15.0) * scale,
                ),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                color=bs.safecolor(player.team.color + (1,)),
                transition=Text.Transition.IN_LEFT,
                transition_delay=tdelay,
            ).autoretain()
            bs.timer(
                tdelay + delay2,
                bs.WeakCall(
                    self._safe_animate,
                    txt.position_combine,
                    'input1',
                    {
                        0: y_base + (v_offs + 15.0) * scale,
                        transtime: y_base + (v_offs_2 + 15.0) * scale,
                    },
                ),
            )
            bs.timer(
                tdelay + delay3,
                bs.WeakCall(
                    self._safe_animate,
                    txt.position_combine,
                    'input0',
                    {
                        0: ts_h_offs - 50.0 * scale,
                        transtime2: ts_h_offs - (50.0 + slide_amt) * scale,
                    },
                ),
            )

            txt_num = Text(
                '#' + str(i + 1),
                scale=0.55 * scale,
                position=(
                    ts_h_offs - 95.0 * scale,
                    y_base + (v_offs + 8.0) * scale,
                ),
                h_align=Text.HAlign.RIGHT,
                color=(0.6, 0.6, 0.6, 0.6),
                transition=Text.Transition.IN_LEFT,
                transition_delay=tdelay,
            ).autoretain()
            bs.timer(
                tdelay + delay3,
                bs.WeakCall(
                    self._safe_animate,
                    txt_num.position_combine,
                    'input0',
                    {
                        0: ts_h_offs - 95.0 * scale,
                        transtime2: ts_h_offs - (95.0 + slide_amt) * scale,
                    },
                ),
            )

            s_txt = _scoretxt(
                str(player.team.sessionteam.customdata['previous_score']),
                80,
                0,
                False,
                0,
                1.0,
            )
            bs.timer(
                tdelay + delay2,
                bs.WeakCall(
                    self._safe_animate,
                    s_txt.position_combine,
                    'input1',
                    {
                        0: y_base + (v_offs + 2.0) * scale,
                        transtime: y_base + (v_offs_2 + 2.0) * scale,
                    },
                ),
            )
            bs.timer(
                tdelay + delay3,
                bs.WeakCall(
                    self._safe_animate,
                    s_txt.position_combine,
                    'input0',
                    {
                        0: ts_h_offs + 80.0 * scale,
                        transtime2: ts_h_offs + (80.0 - slide_amt) * scale,
                    },
                ),
            )

            score_change = (
                player.team.sessionteam.customdata['score']
                - player.team.sessionteam.customdata['previous_score']
            )
            if score_change > 0:
                xval = 113
                yval = 3.0
                s_txt_2 = _scoretxt(
                    '+' + str(score_change),
                    xval,
                    yval,
                    True,
                    0,
                    0.7,
                    flash=True,
                )
                bs.timer(
                    tdelay + delay2,
                    bs.WeakCall(
                        self._safe_animate,
                        s_txt_2.position_combine,
                        'input1',
                        {
                            0: y_base + (v_offs + yval + 2.0) * scale,
                            transtime: y_base + (v_offs_2 + yval + 2.0) * scale,
                        },
                    ),
                )
                bs.timer(
                    tdelay + delay3,
                    bs.WeakCall(
                        self._safe_animate,
                        s_txt_2.position_combine,
                        'input0',
                        {
                            0: ts_h_offs + xval * scale,
                            transtime2: ts_h_offs + (xval - slide_amt) * scale,
                        },
                    ),
                )

                def _safesetattr(
                    node: bs.Node | None, attr: str, value: Any
                ) -> None:
                    if node:
                        setattr(node, attr, value)

                bs.timer(
                    tdelay + delay1,
                    bs.Call(_safesetattr, s_txt.node, 'color', (1, 1, 1, 1)),
                )
                for j in range(score_change):
                    bs.timer(
                        (tdelay + delay1 + 0.15 * j),
                        bs.Call(
                            _safesetattr,
                            s_txt.node,
                            'text',
                            str(
                                player.team.sessionteam.customdata[
                                    'previous_score'
                                ]
                                + j
                                + 1
                            ),
                        ),
                    )
                    tfin = tdelay + delay1 + 0.15 * j
                    if tfin not in sound_times:
                        sound_times.add(tfin)
                        bs.timer(tfin, self._score_display_sound_small.play)
            v_offs -= spacing

    def _safe_animate(
        self, node: bs.Node | None, attr: str, keys: dict[float, float]
    ) -> None:
        """Run an animation on a node if the node still exists."""
        if node:
            bs.animate(node, attr, keys)
