"""Functionality related to the draw screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.activity.teamsscorescreen import TeamsScoreScreenActivity

if TYPE_CHECKING:
    from typing import Any, Dict


class DrawScoreScreenActivity(TeamsScoreScreenActivity):
    """Score screen shown after a draw."""

    def __init__(self, settings: Dict[str, Any]):
        super().__init__(settings=settings)

    # noinspection PyMethodOverriding
    def on_transition_in(self) -> None:  # type: ignore
        # FIXME FIXME: unify args
        # pylint: disable=arguments-differ
        super().on_transition_in(music=None)

    # noinspection PyMethodOverriding
    def on_begin(self) -> None:  # type: ignore
        # FIXME FIXME: unify args
        # pylint: disable=arguments-differ
        from bastd.actor.zoomtext import ZoomText
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
        self.show_player_scores(results=self.settings.get('results', None))
