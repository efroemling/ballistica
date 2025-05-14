# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the join screen for multi-team sessions."""

from __future__ import annotations

from typing import override

import bascenev1 as bs

from bascenev1lib.actor.text import Text


class MultiTeamJoinActivity(bs.JoinActivity):
    """Join screen for teams sessions."""

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._next_up_text: Text | None = None

    @override
    def on_transition_in(self) -> None:
        from bascenev1lib.actor.controlsguide import ControlsGuide

        super().on_transition_in()
        ControlsGuide(delay=1.0).autoretain()

        session = self.session
        assert isinstance(session, bs.MultiTeamSession)

        # Show info about the next up game.
        self._next_up_text = Text(
            bs.Lstr(
                value='${1} ${2}',
                subs=[
                    ('${1}', bs.Lstr(resource='upFirstText')),
                    ('${2}', session.get_next_game_description()),
                ],
            ),
            h_attach=Text.HAttach.CENTER,
            scale=0.7,
            v_attach=Text.VAttach.TOP,
            h_align=Text.HAlign.CENTER,
            position=(0, -70),
            flash=False,
            color=(0.5, 0.5, 0.5, 1.0),
            transition=Text.Transition.FADE_IN,
            transition_delay=5.0,
        )

        # In teams mode, show our two team names.
        # FIXME: Lobby should handle this.
        if isinstance(bs.getsession(), bs.DualTeamSession):
            team_names = [team.name for team in bs.getsession().sessionteams]
            team_colors = [
                tuple(team.color) + (0.5,)
                for team in bs.getsession().sessionteams
            ]
            if len(team_names) == 2:
                for i in range(2):
                    Text(
                        team_names[i],
                        scale=0.7,
                        h_attach=Text.HAttach.CENTER,
                        v_attach=Text.VAttach.TOP,
                        h_align=Text.HAlign.CENTER,
                        position=(-200 + 350 * i, -100),
                        color=team_colors[i],
                        transition=Text.Transition.FADE_IN,
                    ).autoretain()

        Text(
            bs.Lstr(
                resource='mustInviteFriendsText',
                subs=[
                    (
                        '${GATHER}',
                        bs.Lstr(resource='gatherWindow.titleText'),
                    )
                ],
            ),
            h_attach=Text.HAttach.CENTER,
            scale=0.8,
            host_only=True,
            v_attach=Text.VAttach.CENTER,
            h_align=Text.HAlign.CENTER,
            position=(0, 0),
            flash=False,
            color=(0, 1, 0, 1.0),
            transition=Text.Transition.FADE_IN,
            transition_delay=2.0,
            transition_out_delay=7.0,
        ).autoretain()
