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
"""DeathMatch game and support classes."""

# ba_meta require api 6
# (see https://github.com/efroemling/ballistica/wiki/Meta-Tags)
from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor import playerspaz
from bastd.actor import spaz as stdspaz

if TYPE_CHECKING:
    from typing import Any, Type, List, Dict, Tuple, Union, Sequence


# ba_meta export game
class DeathMatchGame(ba.TeamGameActivity):
    """A game type based on acquiring kills."""

    @classmethod
    def get_name(cls) -> str:
        return 'Death Match'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Kill a set number of enemies to win.'

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return (issubclass(sessiontype, ba.DualTeamSession)
                or issubclass(sessiontype, ba.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('melee')

    @classmethod
    def get_settings(
            cls,
            sessiontype: Type[ba.Session]) -> List[Tuple[str, Dict[str, Any]]]:
        settings: List[Tuple[str, Dict[str, Any]]] = [
            ('Kills to Win Per Player', {
                'min_value': 1,
                'default': 5,
                'increment': 1
            }),
            ('Time Limit', {
                 'choices':
                 [('None', 0),
                  ('1 Minute', 60), ('2 Minutes', 120),
                  ('5 Minutes', 300), ('10 Minutes', 600),
                  ('20 Minutes', 1200)],
                 'default': 0
            }),
            ('Respawn Times', {
                 'choices':
                 [('Shorter', 0.25), ('Short', 0.5),
                  ('Normal', 1.0), ('Long', 2.0),
                  ('Longer', 4.0)],
                 'default': 1.0
            }),
            ('Epic Mode', {
                'default': False
            })
        ]  # yapf: disable

        # In teams mode, a suicide gives a point to the other team, but in
        # free-for-all it subtracts from your own score. By default we clamp
        # this at zero to benefit new players, but pro players might like to
        # be able to go negative. (to avoid a strategy of just
        # suiciding until you get a good drop)
        if issubclass(sessiontype, ba.FreeForAllSession):
            settings.append(('Allow Negative Scores', {'default': False}))

        return settings

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        if self.settings['Epic Mode']:
            self.slow_motion = True

        # Print messages when players die since it matters here.
        self.announce_player_deaths = True

        self._scoreboard = Scoreboard()
        self._score_to_win = None
        self._dingsound = ba.getsound('dingSmall')

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Crush ${ARG1} of your enemies.', self._score_to_win

    def get_instance_scoreboard_description(self) -> Union[str, Sequence]:
        return 'kill ${ARG1} enemies', self._score_to_win

    def on_transition_in(self) -> None:
        self.default_music = (ba.MusicType.EPIC if self.settings['Epic Mode']
                              else ba.MusicType.TO_THE_DEATH)
        super().on_transition_in()

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['score'] = 0
        if self.has_begun():
            self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self.settings['Time Limit'])
        self.setup_standard_powerup_drops()
        if self.teams:
            self._score_to_win = (
                self.settings['Kills to Win Per Player'] *
                max(1, max(len(t.players) for t in self.teams)))
        else:
            self._score_to_win = self.settings['Kills to Win Per Player']
        self._update_scoreboard()

    def handlemessage(self, msg: Any) -> Any:
        # pylint: disable=too-many-branches

        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):

            # Augment standard behavior.
            super().handlemessage(msg)

            player = msg.spaz.player
            self.respawn_player(player)

            killer = msg.killerplayer
            if killer is None:
                return

            # Handle team-kills.
            if killer.team is player.team:

                # In free-for-all, killing yourself loses you a point.
                if isinstance(self.session, ba.FreeForAllSession):
                    new_score = player.team.gamedata['score'] - 1
                    if not self.settings['Allow Negative Scores']:
                        new_score = max(0, new_score)
                    player.team.gamedata['score'] = new_score

                # In teams-mode it gives a point to the other team.
                else:
                    ba.playsound(self._dingsound)
                    for team in self.teams:
                        if team is not killer.team:
                            team.gamedata['score'] += 1

            # Killing someone on another team nets a kill.
            else:
                killer.team.gamedata['score'] += 1
                ba.playsound(self._dingsound)

                # In FFA show scores since its hard to find on the scoreboard.
                try:
                    if isinstance(killer.actor, stdspaz.Spaz):
                        killer.actor.set_score_text(
                            str(killer.team.gamedata['score']) + '/' +
                            str(self._score_to_win),
                            color=killer.team.color,
                            flash=True)
                except Exception:
                    pass

            self._update_scoreboard()

            # If someone has won, set a timer to end shortly.
            # (allows the dust to clear and draws to occur if deaths are
            # close enough)
            if any(team.gamedata['score'] >= self._score_to_win
                   for team in self.teams):
                ba.timer(0.5, self.end_game)

        else:
            super().handlemessage(msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.gamedata['score'],
                                            self._score_to_win)

    def end_game(self) -> None:
        results = ba.TeamGameResults()
        for team in self.teams:
            results.set_team_score(team, team.gamedata['score'])
        self.end(results=results)
