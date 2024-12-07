# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the end screen in dual-team mode."""

from __future__ import annotations

from typing import override

import bascenev1 as bs

from bascenev1lib.activity.multiteamscore import MultiTeamScoreScreenActivity
from bascenev1lib.actor.zoomtext import ZoomText


class TeamVictoryScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Scorescreen between rounds of a dual-team session."""

    def __init__(self, settings: dict):
        super().__init__(settings=settings)
        self._winner: bs.SessionTeam = settings['winner']
        assert isinstance(self._winner, bs.SessionTeam)

    @override
    def on_begin(self) -> None:
        bs.set_analytics_screen('Teams Score Screen')
        super().on_begin()

        height = 130
        active_team_count = len(self.teams)
        vval = (height * active_team_count) / 2 - height / 2
        i = 0
        shift_time = 2.5

        # Usually we say 'Best of 7', but if the language prefers we can say
        # 'First to 4'.
        session = self.session
        assert isinstance(session, bs.MultiTeamSession)
        if bs.app.lang.get_resource('bestOfUseFirstToInstead'):
            best_txt = bs.Lstr(
                resource='firstToSeriesText',
                subs=[('${COUNT}', str(session.get_series_length() / 2 + 1))],
            )
        else:
            best_txt = bs.Lstr(
                resource='bestOfSeriesText',
                subs=[('${COUNT}', str(session.get_series_length()))],
            )

        ZoomText(
            best_txt,
            position=(0, 175),
            shiftposition=(-250, 175),
            shiftdelay=2.5,
            flash=False,
            trail=False,
            h_align='center',
            scale=0.25,
            color=(0.5, 0.5, 0.5, 1.0),
            jitter=3.0,
        ).autoretain()
        for team in self.session.sessionteams:
            bs.timer(
                i * 0.15 + 0.15,
                bs.WeakCall(
                    self._show_team_name,
                    vval - i * height,
                    team,
                    i * 0.2,
                    shift_time - (i * 0.150 + 0.150),
                ),
            )
            bs.timer(i * 0.150 + 0.5, self._score_display_sound_small.play)
            scored = team is self._winner
            delay = 0.2
            if scored:
                delay = 1.2
                bs.timer(
                    i * 0.150 + 0.2,
                    bs.WeakCall(
                        self._show_team_old_score,
                        vval - i * height,
                        team,
                        shift_time - (i * 0.15 + 0.2),
                    ),
                )
                bs.timer(i * 0.15 + 1.5, self._score_display_sound.play)

            bs.timer(
                i * 0.150 + delay,
                bs.WeakCall(
                    self._show_team_score,
                    vval - i * height,
                    team,
                    scored,
                    i * 0.2 + 0.1,
                    shift_time - (i * 0.15 + delay),
                ),
            )
            i += 1
        self.show_player_scores()

    def _show_team_name(
        self,
        pos_v: float,
        team: bs.SessionTeam,
        kill_delay: float,
        shiftdelay: float,
    ) -> None:
        del kill_delay  # Unused arg.
        ZoomText(
            bs.Lstr(value='${A}:', subs=[('${A}', team.name)]),
            position=(100, pos_v),
            shiftposition=(-150, pos_v),
            shiftdelay=shiftdelay,
            flash=False,
            trail=False,
            h_align='right',
            maxwidth=300,
            color=team.color,
            jitter=1.0,
        ).autoretain()

    def _show_team_old_score(
        self, pos_v: float, sessionteam: bs.SessionTeam, shiftdelay: float
    ) -> None:
        ZoomText(
            str(sessionteam.customdata['score'] - 1),
            position=(150, pos_v),
            maxwidth=100,
            color=(0.6, 0.6, 0.7),
            shiftposition=(-100, pos_v),
            shiftdelay=shiftdelay,
            flash=False,
            trail=False,
            lifespan=1.0,
            h_align='left',
            jitter=1.0,
        ).autoretain()

    def _show_team_score(
        self,
        pos_v: float,
        sessionteam: bs.SessionTeam,
        scored: bool,
        kill_delay: float,
        shiftdelay: float,
    ) -> None:
        # pylint: disable=too-many-positional-arguments
        del kill_delay  # Unused arg.
        ZoomText(
            str(sessionteam.customdata['score']),
            position=(150, pos_v),
            maxwidth=100,
            color=(1.0, 0.9, 0.5) if scored else (0.6, 0.6, 0.7),
            shiftposition=(-100, pos_v),
            shiftdelay=shiftdelay,
            flash=scored,
            trail=scored,
            h_align='left',
            jitter=1.0,
            trailcolor=(1, 0.8, 0.0, 0),
        ).autoretain()
