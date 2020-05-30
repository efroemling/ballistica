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
"""Functionality related to the draw screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.activity.multiteamscore import MultiTeamScoreScreenActivity
from bastd.actor.zoomtext import ZoomText

if TYPE_CHECKING:
    from typing import Any, Dict


class DrawScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Score screen shown after a draw."""

    default_music = None  # Awkward silence...

    def on_begin(self) -> None:
        ba.set_analytics_screen('Draw Score Screen')
        super().on_begin()
        ZoomText(ba.Lstr(resource='drawText'),
                 position=(0, 0),
                 maxwidth=400,
                 shiftposition=(-220, 0),
                 shiftdelay=2.0,
                 flash=False,
                 trail=False,
                 jitter=1.0).autoretain()
        ba.timer(0.35, ba.Call(ba.playsound, self._score_display_sound))
        self.show_player_scores(results=self.settings_raw.get('results', None))
