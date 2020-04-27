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
"""Defines the last stand minigame."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import ba
from bastd.actor import playerspaz
from bastd.actor import spazbot
from bastd.actor.bomb import TNTSpawner

if TYPE_CHECKING:
    from typing import Any, Dict, Type, List, Optional, Sequence
    from bastd.actor.scoreboard import Scoreboard


class TheLastStandGame(ba.CoopGameActivity):
    """Slow motion how-long-can-you-last game."""

    tips = [
        'This level never ends, but a high score here\n'
        'will earn you eternal respect throughout the world.'
    ]

    @classmethod
    def get_name(cls) -> str:
        return 'The Last Stand'

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Final glorious epic slow motion battle to the death.'

    def __init__(self, settings: Dict[str, Any]):
        settings['map'] = 'Rampage'
        super().__init__(settings)

        # Show messages when players die since it matters here.
        self.announce_player_deaths = True

        # And of course the most important part.
        self.slow_motion = True

        self._new_wave_sound = ba.getsound('scoreHit01')
        self._winsound = ba.getsound('score')
        self._cashregistersound = ba.getsound('cashRegister')
        self._spawn_center = (0, 5.5, -4.14)
        self._tntspawnpos = (0, 5.5, -6)
        self._powerup_center = (0, 7, -4.14)
        self._powerup_spread = (7, 2)
        self._preset = self.settings.get('preset', 'default')
        self._excludepowerups: List[str] = []
        self._scoreboard: Optional[Scoreboard] = None
        self._score = 0
        self._bots = spazbot.BotSet()
        self._dingsound = ba.getsound('dingSmall')
        self._dingsoundhigh = ba.getsound('dingSmallHigh')
        self._tntspawner: Optional[TNTSpawner] = None
        self._bot_update_interval: Optional[float] = None
        self._bot_update_timer: Optional[ba.Timer] = None
        self._powerup_drop_timer = None

        # For each bot type: [spawn-rate, increase, d_increase]
        self._bot_spawn_types = {
            spazbot.BomberBot:              [1.00, 0.00, 0.000],
            spazbot.BomberBotPro:           [0.00, 0.05, 0.001],
            spazbot.BomberBotProShielded:   [0.00, 0.02, 0.002],
            spazbot.BrawlerBot:             [1.00, 0.00, 0.000],
            spazbot.BrawlerBotPro:          [0.00, 0.05, 0.001],
            spazbot.BrawlerBotProShielded:  [0.00, 0.02, 0.002],
            spazbot.TriggerBot:             [0.30, 0.00, 0.000],
            spazbot.TriggerBotPro:          [0.00, 0.05, 0.001],
            spazbot.TriggerBotProShielded:  [0.00, 0.02, 0.002],
            spazbot.ChargerBot:             [0.30, 0.05, 0.000],
            spazbot.StickyBot:              [0.10, 0.03, 0.001],
            spazbot.ExplodeyBot:            [0.05, 0.02, 0.002]
        }  # yapf: disable

    def on_transition_in(self) -> None:
        from bastd.actor.scoreboard import Scoreboard
        self.default_music = ba.MusicType.EPIC
        super().on_transition_in()
        ba.timer(1.3, ba.Call(ba.playsound, self._new_wave_sound))
        self._scoreboard = Scoreboard(label=ba.Lstr(resource='scoreText'),
                                      score_split=0.5)

    def on_begin(self) -> None:
        super().on_begin()

        # Spit out a few powerups and start dropping more shortly.
        self._drop_powerups(standard_points=True)
        ba.timer(2.0, ba.WeakCall(self._start_powerup_drops))
        ba.timer(0.001, ba.WeakCall(self._start_bot_updates))
        self.setup_low_life_warning_sound()
        self._update_scores()

        # Our TNT spawner (if applicable).
        self._tntspawner = TNTSpawner(position=self._tntspawnpos,
                                      respawn_time=10.0)

    def spawn_player(self, player: ba.Player) -> ba.Actor:
        pos = (self._spawn_center[0] + random.uniform(-1.5, 1.5),
               self._spawn_center[1],
               self._spawn_center[2] + random.uniform(-1.5, 1.5))
        return self.spawn_player_spaz(player, position=pos)

    def _start_bot_updates(self) -> None:
        self._bot_update_interval = 3.3 - 0.3 * (len(self.players))
        self._update_bots()
        self._update_bots()
        if len(self.players) > 2:
            self._update_bots()
        if len(self.players) > 3:
            self._update_bots()
        self._bot_update_timer = ba.Timer(self._bot_update_interval,
                                          ba.WeakCall(self._update_bots))

    def _drop_powerup(self, index: int, poweruptype: str = None) -> None:
        from bastd.actor import powerupbox
        if poweruptype is None:
            poweruptype = (powerupbox.get_factory().get_random_powerup_type(
                excludetypes=self._excludepowerups))
        powerupbox.PowerupBox(position=self.map.powerup_spawn_points[index],
                              poweruptype=poweruptype).autoretain()

    def _start_powerup_drops(self) -> None:
        self._powerup_drop_timer = ba.Timer(3.0,
                                            ba.WeakCall(self._drop_powerups),
                                            repeat=True)

    def _drop_powerups(self,
                       standard_points: bool = False,
                       force_first: str = None) -> None:
        """Generic powerup drop."""
        from bastd.actor import powerupbox
        if standard_points:
            pts = self.map.powerup_spawn_points
            for i in range(len(pts)):
                ba.timer(
                    1.0 + i * 0.5,
                    ba.WeakCall(self._drop_powerup, i,
                                force_first if i == 0 else None))
        else:
            drop_pt = (self._powerup_center[0] + random.uniform(
                -1.0 * self._powerup_spread[0], 1.0 * self._powerup_spread[0]),
                       self._powerup_center[1],
                       self._powerup_center[2] + random.uniform(
                           -self._powerup_spread[1], self._powerup_spread[1]))

            # Drop one random one somewhere.
            powerupbox.PowerupBox(
                position=drop_pt,
                poweruptype=powerupbox.get_factory().get_random_powerup_type(
                    excludetypes=self._excludepowerups)).autoretain()

    def do_end(self, outcome: str) -> None:
        """End the game."""
        if outcome == 'defeat':
            self.fade_to_red()
        self.end(delay=2.0,
                 results={
                     'outcome': outcome,
                     'score': self._score,
                     'player_info': self.initial_player_info
                 })

    def _update_bots(self) -> None:
        assert self._bot_update_interval is not None
        self._bot_update_interval = max(0.5, self._bot_update_interval * 0.98)
        self._bot_update_timer = ba.Timer(self._bot_update_interval,
                                          ba.WeakCall(self._update_bots))
        botspawnpts: List[Sequence[float]] = [[-5.0, 5.5, -4.14],
                                              [0.0, 5.5, -4.14],
                                              [5.0, 5.5, -4.14]]
        dists = [0.0, 0.0, 0.0]
        playerpts: List[Sequence[float]] = []
        for player in self.players:
            try:
                if player.is_alive():
                    assert isinstance(player.actor, playerspaz.PlayerSpaz)
                    assert player.actor.node
                    playerpts.append(player.actor.node.position)
            except Exception as exc:
                print('ERROR in _update_bots', exc)
        for i in range(3):
            for playerpt in playerpts:
                dists[i] += abs(playerpt[0] - botspawnpts[i][0])

            # Little random variation.
            dists[i] += random.random() * 5.0
        if dists[0] > dists[1] and dists[0] > dists[2]:
            spawnpt = botspawnpts[0]
        elif dists[1] > dists[2]:
            spawnpt = botspawnpts[1]
        else:
            spawnpt = botspawnpts[2]

        spawnpt = (spawnpt[0] + 3.0 * (random.random() - 0.5), spawnpt[1],
                   2.0 * (random.random() - 0.5) + spawnpt[2])

        # Normalize our bot type total and find a random number within that.
        total = 0.0
        for spawntype in self._bot_spawn_types.items():
            total += spawntype[1][0]
        randval = random.random() * total

        # Now go back through and see where this value falls.
        total = 0
        bottype: Optional[Type[spazbot.SpazBot]] = None
        for spawntype in self._bot_spawn_types.items():
            total += spawntype[1][0]
            if randval <= total:
                bottype = spawntype[0]
                break
        spawn_time = 1.0
        assert bottype is not None
        self._bots.spawn_bot(bottype, pos=spawnpt, spawn_time=spawn_time)

        # After every spawn we adjust our ratios slightly to get more
        # difficult.
        for spawntype in self._bot_spawn_types.items():
            spawntype[1][0] += spawntype[1][1]  # incr spawn rate
            spawntype[1][1] += spawntype[1][2]  # incr spawn rate incr rate

    def _update_scores(self) -> None:
        # Achievements in default preset only.
        score = self._score
        if self._preset == 'default':
            if score >= 250:
                self._award_achievement('Last Stand Master')
            if score >= 500:
                self._award_achievement('Last Stand Wizard')
            if score >= 1000:
                self._award_achievement('Last Stand God')
        assert self._scoreboard is not None
        self._scoreboard.set_team_value(self.teams[0], score, max_score=None)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):
            player = msg.spaz.getplayer()
            if player is None:
                ba.print_error('FIXME: getplayer() should no longer '
                               'ever be returning None.')
                return
            if not player:
                return
            self.stats.player_was_killed(player)
            ba.timer(0.1, self._checkroundover)

        elif isinstance(msg, ba.PlayerScoredMessage):
            self._score += msg.score
            self._update_scores()

        elif isinstance(msg, spazbot.SpazBotDeathMessage):
            pts, importance = msg.badguy.get_death_points(msg.how)
            target: Optional[Sequence[float]]
            if msg.killerplayer:
                try:
                    assert msg.badguy.node
                    target = msg.badguy.node.position
                except Exception:
                    ba.print_exception()
                    target = None
                try:
                    self.stats.player_scored(msg.killerplayer,
                                             pts,
                                             target=target,
                                             kill=True,
                                             screenmessage=False,
                                             importance=importance)
                    ba.playsound(self._dingsound
                                 if importance == 1 else self._dingsoundhigh,
                                 volume=0.6)
                except Exception as exc:
                    print('EXC on last-stand SpazBotDeathMessage', exc)

            # Normally we pull scores from the score-set, but if there's no
            # player lets be explicit.
            else:
                self._score += pts
            self._update_scores()
        else:
            super().handlemessage(msg)

    def _on_got_scores_to_beat(self, scores: List[Dict[str, Any]]) -> None:
        # FIXME: Unify args.
        self._show_standard_scores_to_beat_ui(scores)

    def end_game(self) -> None:
        # Tell our bots to celebrate just to rub it in.
        self._bots.final_celebrate()
        ba.setmusic(None)
        ba.pushcall(ba.WeakCall(self.do_end, 'defeat'))

    def _checkroundover(self) -> None:
        """End the round if conditions are met."""
        if not any(player.is_alive() for player in self.teams[0].players):
            self.end_game()
