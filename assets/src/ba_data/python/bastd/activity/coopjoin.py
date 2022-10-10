# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the co-op join screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from ba.internal import JoinActivity

if TYPE_CHECKING:
    pass


class CoopJoinActivity(JoinActivity):
    """Join-screen for co-op mode."""

    # We can assume our session is a CoopSession.
    session: ba.CoopSession

    def __init__(self, settings: dict):
        super().__init__(settings)
        session = self.session
        assert isinstance(session, ba.CoopSession)

    def on_transition_in(self) -> None:
        from bastd.actor.controlsguide import ControlsGuide
        from bastd.actor.text import Text

        super().on_transition_in()
        assert isinstance(self.session, ba.CoopSession)
        assert self.session.campaign
        Text(
            self.session.campaign.getlevel(
                self.session.campaign_level_name
            ).displayname,
            scale=1.3,
            h_attach=Text.HAttach.CENTER,
            h_align=Text.HAlign.CENTER,
            v_attach=Text.VAttach.TOP,
            transition=Text.Transition.FADE_IN,
            transition_delay=4.0,
            color=(1, 1, 1, 0.6),
            position=(0, -95),
        ).autoretain()
        ControlsGuide(delay=1.0).autoretain()

        ba.pushcall(self._show_remaining_achievements)

    def _show_remaining_achievements(self) -> None:
        from bastd.actor.text import Text

        # We only show achievements and challenges for CoopGameActivities.
        session = self.session
        assert isinstance(session, ba.CoopSession)
        gameinstance = session.get_current_game_instance()
        if not isinstance(gameinstance, ba.CoopGameActivity):
            return

        delay = 1.0
        vpos = -140.0

        # Now list our remaining achievements for this level.
        assert self.session.campaign is not None
        assert isinstance(self.session, ba.CoopSession)
        levelname = (
            self.session.campaign.name + ':' + self.session.campaign_level_name
        )
        ts_h_offs = 60

        if not (ba.app.demo_mode or ba.app.arcade_mode):
            achievements = [
                a
                for a in ba.app.ach.achievements_for_coop_level(levelname)
                if not a.complete
            ]
            have_achievements = bool(achievements)
            achievements = [a for a in achievements if not a.complete]
            vrmode = ba.app.vr_mode
            if have_achievements:
                Text(
                    ba.Lstr(resource='achievementsRemainingText'),
                    host_only=True,
                    position=(ts_h_offs - 10, vpos),
                    transition=Text.Transition.FADE_IN,
                    scale=1.1 * 0.76,
                    h_attach=Text.HAttach.LEFT,
                    v_attach=Text.VAttach.TOP,
                    color=(1, 1, 1.2, 1) if vrmode else (0.8, 0.8, 1, 1),
                    shadow=1.0,
                    flatness=1.0 if vrmode else 0.6,
                    transition_delay=delay,
                ).autoretain()
                hval = ts_h_offs + 50
                vpos -= 35
                for ach in achievements:
                    delay += 0.05
                    ach.create_display(hval, vpos, delay, style='in_game')
                    vpos -= 55
                if not achievements:
                    Text(
                        ba.Lstr(resource='noAchievementsRemainingText'),
                        host_only=True,
                        position=(ts_h_offs + 15, vpos + 10),
                        transition=Text.Transition.FADE_IN,
                        scale=0.7,
                        h_attach=Text.HAttach.LEFT,
                        v_attach=Text.VAttach.TOP,
                        color=(1, 1, 1, 0.5),
                        transition_delay=delay + 0.5,
                    ).autoretain()
