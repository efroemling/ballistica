"""Defines a keep-away game type."""

# bs_meta require api 6
# (see bombsquadgame.com/apichanges)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor import flag as stdflag
from bastd.actor import playerspaz

if TYPE_CHECKING:
    from typing import (Any, Type, List, Tuple, Dict, Optional, Sequence,
                        Union)


# bs_meta export game
class KeepAwayGame(ba.TeamGameActivity):
    """Game where you try to keep the flag away from your enemies."""

    FLAG_NEW = 0
    FLAG_UNCONTESTED = 1
    FLAG_CONTESTED = 2
    FLAG_HELD = 3

    @classmethod
    def get_name(cls) -> str:
        return 'Keep Away'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Carry the flag for a set length of time.'

    @classmethod
    def get_score_info(cls) -> Dict[str, Any]:
        return {'score_name': 'Time Held'}

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        return (issubclass(sessiontype, ba.TeamsSession)
                or issubclass(sessiontype, ba.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        return ba.getmaps('keep_away')

    @classmethod
    def get_settings(cls, sessiontype: Type[ba.Session]
                     ) -> List[Tuple[str, Dict[str, Any]]]:
        return [
            ("Hold Time", {
                'min_value': 10,
                'default': 30,
                'increment': 10
            }),
            ("Time Limit", {
                'choices': [('None', 0), ('1 Minute', 60), ('2 Minutes', 120),
                            ('5 Minutes', 300), ('10 Minutes', 600),
                            ('20 Minutes', 1200)],
                'default': 0
            }),
            ("Respawn Times", {
                'choices': [('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0),
                            ('Long', 2.0), ('Longer', 4.0)],
                'default': 1.0
            })
        ]  # yapf: disable

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._swipsound = ba.getsound("swip")
        self._tick_sound = ba.getsound('tick')
        self._countdownsounds = {
            10: ba.getsound('announceTen'),
            9: ba.getsound('announceNine'),
            8: ba.getsound('announceEight'),
            7: ba.getsound('announceSeven'),
            6: ba.getsound('announceSix'),
            5: ba.getsound('announceFive'),
            4: ba.getsound('announceFour'),
            3: ba.getsound('announceThree'),
            2: ba.getsound('announceTwo'),
            1: ba.getsound('announceOne')
        }
        self._flag_spawn_pos: Optional[Sequence[float]] = None
        self._update_timer: Optional[ba.Timer] = None
        self._holding_players: List[ba.Player] = []
        self._flag_state: Optional[int] = None
        self._flag_light: Optional[ba.Node] = None
        self._scoring_team: Optional[ba.Team] = None
        self._flag: Optional[stdflag.Flag] = None

    def get_instance_description(self) -> Union[str, Sequence]:
        return ('Carry the flag for ${ARG1} seconds.',
                self.settings['Hold Time'])

    def get_instance_scoreboard_description(self) -> Union[str, Sequence]:
        return ('carry the flag for ${ARG1} seconds',
                self.settings['Hold Time'])

    # noinspection PyMethodOverriding
    def on_transition_in(self) -> None:  # type: ignore
        # FIXME: Unify these args.
        # pylint: disable=arguments-differ
        ba.TeamGameActivity.on_transition_in(self, music='Keep Away')

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['time_remaining'] = self.settings["Hold Time"]
        self._update_scoreboard()

    def on_begin(self) -> None:
        ba.TeamGameActivity.on_begin(self)
        self.setup_standard_time_limit(self.settings['Time Limit'])
        self.setup_standard_powerup_drops()
        self._flag_spawn_pos = self.map.get_flag_position(None)
        self._spawn_flag()
        self._update_timer = ba.Timer(1.0, call=self._tick, repeat=True)
        self._update_flag_state()
        self.project_flag_stand(self._flag_spawn_pos)

    def _tick(self) -> None:
        self._update_flag_state()

        # Award points to all living players holding the flag.
        for player in self._holding_players:
            if player:
                assert self.stats
                self.stats.player_scored(player,
                                         3,
                                         screenmessage=False,
                                         display=False)

        scoring_team = self._scoring_team

        if scoring_team is not None:

            if scoring_team.gamedata['time_remaining'] > 0:
                ba.playsound(self._tick_sound)

            scoring_team.gamedata['time_remaining'] = max(
                0, scoring_team.gamedata['time_remaining'] - 1)
            self._update_scoreboard()
            if scoring_team.gamedata['time_remaining'] > 0:
                assert self._flag is not None
                self._flag.set_score_text(
                    str(scoring_team.gamedata['time_remaining']))

            # Announce numbers we have sounds for.
            try:
                ba.playsound(self._countdownsounds[
                    scoring_team.gamedata['time_remaining']])
            except Exception:
                pass

            # Winner.
            if scoring_team.gamedata['time_remaining'] <= 0:
                self.end_game()

    def end_game(self) -> None:
        results = ba.TeamGameResults()
        for team in self.teams:
            results.set_team_score(
                team,
                self.settings['Hold Time'] - team.gamedata['time_remaining'])
        self.end(results=results, announce_delay=0)

    def _update_flag_state(self) -> None:
        for team in self.teams:
            team.gamedata['holding_flag'] = False
        self._holding_players = []
        for player in self.players:
            holding_flag = False
            try:
                assert player.actor is not None
                if (player.actor.is_alive() and player.actor.node
                        and player.actor.node.hold_node):
                    holding_flag = (
                        player.actor.node.hold_node.getnodetype() == 'flag')
            except Exception:
                ba.print_exception("exception checking hold flag")
            if holding_flag:
                self._holding_players.append(player)
                player.team.gamedata['holding_flag'] = True

        holding_teams = set(t for t in self.teams
                            if t.gamedata['holding_flag'])
        prev_state = self._flag_state
        assert self._flag is not None
        assert self._flag_light
        assert self._flag.node
        if len(holding_teams) > 1:
            self._flag_state = self.FLAG_CONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.6, 0.6, 0.1)
            self._flag.node.color = (1.0, 1.0, 0.4)
        elif len(holding_teams) == 1:
            holding_team = list(holding_teams)[0]
            self._flag_state = self.FLAG_HELD
            self._scoring_team = holding_team
            self._flag_light.color = ba.normalized_color(holding_team.color)
            self._flag.node.color = holding_team.color
        else:
            self._flag_state = self.FLAG_UNCONTESTED
            self._scoring_team = None
            self._flag_light.color = (0.2, 0.2, 0.2)
            self._flag.node.color = (1, 1, 1)

        if self._flag_state != prev_state:
            ba.playsound(self._swipsound)

    def _spawn_flag(self) -> None:
        ba.playsound(self._swipsound)
        self._flash_flag_spawn()
        assert self._flag_spawn_pos is not None
        self._flag = stdflag.Flag(dropped_timeout=20,
                                  position=self._flag_spawn_pos)
        self._flag_state = self.FLAG_NEW
        self._flag_light = ba.newnode('light',
                                      owner=self._flag.node,
                                      attrs={
                                          'intensity': 0.2,
                                          'radius': 0.3,
                                          'color': (0.2, 0.2, 0.2)
                                      })
        assert self._flag.node
        self._flag.node.connectattr('position', self._flag_light, 'position')
        self._update_flag_state()

    def _flash_flag_spawn(self) -> None:
        light = ba.newnode('light',
                           attrs={
                               'position': self._flag_spawn_pos,
                               'color': (1, 1, 1),
                               'radius': 0.3,
                               'height_attenuated': False
                           })
        ba.animate(light, 'intensity', {0.0: 0, 0.25: 0.5, 0.5: 0}, loop=True)
        ba.timer(1.0, light.delete)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team,
                                            team.gamedata['time_remaining'],
                                            self.settings['Hold Time'],
                                            countdown=True)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            self.respawn_player(msg.spaz.player)
        elif isinstance(msg, stdflag.FlagDeathMessage):
            self._spawn_flag()
        elif isinstance(
                msg,
            (stdflag.FlagDroppedMessage, stdflag.FlagPickedUpMessage)):
            self._update_flag_state()
        else:
            super().handlemessage(msg)
