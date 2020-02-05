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
"""Functionality related to the join screen for multi-team sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from ba.internal import JoiningActivity
from bastd.actor import text as textactor

if TYPE_CHECKING:
    from typing import Any, Dict, Optional


class TeamJoiningActivity(JoiningActivity):
    """Join screen for teams sessions."""

    def __init__(self, settings: Dict[str, Any]):
        super().__init__(settings)
        self._next_up_text: Optional[textactor.Text] = None

    def on_transition_in(self) -> None:
        from bastd.actor.controlsguide import ControlsGuide
        from ba import TeamsSession
        super().on_transition_in()
        ControlsGuide(delay=1.0).autoretain()

        session = self.session
        assert isinstance(session, ba.TeamBaseSession)

        # Show info about the next up game.
        self._next_up_text = textactor.Text(ba.Lstr(
            value='${1} ${2}',
            subs=[('${1}', ba.Lstr(resource='upFirstText')),
                  ('${2}', session.get_next_game_description())]),
                                            h_attach='center',
                                            scale=0.7,
                                            v_attach='top',
                                            h_align='center',
                                            position=(0, -70),
                                            flash=False,
                                            color=(0.5, 0.5, 0.5, 1.0),
                                            transition='fade_in',
                                            transition_delay=5.0)

        # In teams mode, show our two team names.
        # FIXME: Lobby should handle this.
        if isinstance(ba.getsession(), TeamsSession):
            team_names = [team.name for team in ba.getsession().teams]
            team_colors = [
                tuple(team.color) + (0.5, ) for team in ba.getsession().teams
            ]
            if len(team_names) == 2:
                for i in range(2):
                    textactor.Text(team_names[i],
                                   scale=0.7,
                                   h_attach='center',
                                   v_attach='top',
                                   h_align='center',
                                   position=(-200 + 350 * i, -100),
                                   color=team_colors[i],
                                   transition='fade_in').autoretain()

        textactor.Text(ba.Lstr(resource='mustInviteFriendsText',
                               subs=[
                                   ('${GATHER}',
                                    ba.Lstr(resource='gatherWindow.titleText'))
                               ]),
                       h_attach='center',
                       scale=0.8,
                       host_only=True,
                       v_attach='center',
                       h_align='center',
                       position=(0, 0),
                       flash=False,
                       color=(0, 1, 0, 1.0),
                       transition='fade_in',
                       transition_delay=2.0,
                       transition_out_delay=7.0).autoretain()
