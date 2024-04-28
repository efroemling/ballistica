# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the draw screen."""

from __future__ import annotations

from typing import override

import bascenev1 as bs

from bascenev1lib.activity.multiteamscore import MultiTeamScoreScreenActivity
from bascenev1lib.actor.zoomtext import ZoomText


class DrawScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Score screen shown after a draw."""

    default_music = None  # Awkward silence...

    @override
    def on_begin(self) -> None:
        bs.set_analytics_screen('Draw Score Screen')
        super().on_begin()
        ZoomText(
            bs.Lstr(resource='drawText'),
            position=(0, 0),
            maxwidth=400,
            shiftposition=(-220, 0),
            shiftdelay=2.0,
            flash=False,
            trail=False,
            jitter=1.0,
        ).autoretain()
        bs.timer(0.35, self._score_display_sound.play)
        self.show_player_scores(results=self.settings_raw.get('results', None))
