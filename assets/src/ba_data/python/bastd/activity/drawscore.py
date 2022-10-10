# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the draw screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.activity.multiteamscore import MultiTeamScoreScreenActivity
from bastd.actor.zoomtext import ZoomText

if TYPE_CHECKING:
    pass


class DrawScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Score screen shown after a draw."""

    default_music = None  # Awkward silence...

    def on_begin(self) -> None:
        ba.set_analytics_screen('Draw Score Screen')
        super().on_begin()
        ZoomText(
            ba.Lstr(resource='drawText'),
            position=(0, 0),
            maxwidth=400,
            shiftposition=(-220, 0),
            shiftdelay=2.0,
            flash=False,
            trail=False,
            jitter=1.0,
        ).autoretain()
        ba.timer(0.35, ba.Call(ba.playsound, self._score_display_sound))
        self.show_player_scores(results=self.settings_raw.get('results', None))
