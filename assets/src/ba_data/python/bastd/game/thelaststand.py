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
from dataclasses import dataclass
from typing import TYPE_CHECKING

import ba
from bastd.actor.playerspaz import PlayerSpaz
from bastd.actor.bomb import TNTSpawner
from bastd.actor.scoreboard import Scoreboard
from bastd.actor.powerupbox import PowerupBoxFactory, PowerupBox
from bastd.actor.spazbot import (SpazBotSet, SpazBotDiedMessage, BomberBot,
                                 BomberBotPro, BomberBotProShielded,
                                 BrawlerBot, BrawlerBotPro,
                                 BrawlerBotProShielded, TriggerBot,
                                 TriggerBotPro, TriggerBotProShielded,
                                 ChargerBot, StickyBot, ExplodeyBot)

if TYPE_CHECKING:
    from typing import Any, Dict, Type, List, Optional, Sequence
    from bastd.actor.spazbot import SpazBot


@dataclass
class SpawnInfo:
    """Spawning info for a particular bot type."""
    spawnrate: float
    increase: float
    dincrease: float


class Player(ba.Player['Team']):
    """Our player type for this game."""


class Team(ba.Team[Player]):
    """Our team type for this game."""


class TheLastStandGame(ba.CoopGameActivity[Player, Team]):
    """Slow motion how-long-can-you-last game."""

    name = 'The Last Stand'
    description = 'Final glorious epic slow motion battle to the death.'
    tips = [
        'This level never ends, but a high score here\n'
        'will earn you eternal respect throughout the world.'
    ]

    # Show messages when players die since it matters here.
    announce_player_deaths = True

    # And of course the most important part.
    slow_motion = True

    default_music = ba.MusicType.EPIC

    def __init__(self, settings: dict):
        settings['map'] = 'Rampage'
        super().__init__(settings)
        self._new_wave_sound = ba.getsound('scoreHit01')
        self._winsound = ba.getsound('score')
        self._cashregistersound = ba.getsound('cashRegister')
        self._spawn_center = (0, 5.5, -4.14)
        self._tntspawnpos = (0, 5.5, -6)
        self._powerup_center = (0, 7, -4.14)
        self._powerup_spread = (7, 2)
        self._preset = str(settings.get('preset', 'default'))
        self._excludepowerups: List[str] = []
        self._scoreboard: Optional[Scoreboard] = None
        self._score = 0
        self._bots = SpazBotSet()
        self._dingsound = ba.getsound('dingSmall')
        self._dingsoundhigh = ba.getsound('dingSmallHigh')
        self._tntspawner: Optional[TNTSpawner] = None
        self._bot_update_interval: Optional[float] = None
        self._bot_update_timer: Optional[ba.Timer] = None
        self._powerup_drop_timer = None

        # For each bot type: [spawnrate, increase, d_increase]
        self._bot_spawn_types = {
            BomberBot:              SpawnInfo(1.00, 0.00, 0.000),
            BomberBotPro:           SpawnInfo(0.00, 0.05, 0.001),
            BomberBotProShielded:   SpawnInfo(0.00, 0.02, 0.002),
            BrawlerBot:             SpawnInfo(1.00, 0.00, 0.000),
            BrawlerBotPro:          SpawnInfo(0.00, 0.05, 0.001),
            BrawlerBotProShielded:  SpawnInfo(0.00, 0.02, 0.002),
            TriggerBot:             SpawnInfo(0.30, 0.00, 0.000),
            TriggerBotPro:          SpawnInfo(0.00, 0.05, 0.001),
            TriggerBotProShielded:  SpawnInfo(0.00, 0.02, 0.002),
            ChargerBot:             SpawnInfo(0.30, 0.05, 0.000),
            StickyBot:              SpawnInfo(0.10, 0.03, 0.001),
            ExplodeyBot:            SpawnInfo(0.05, 0.02, 0.002)
        } # yapf: disable


    def on_transition_in(self) -> None:
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
        self._tntspawner = TNTSpawner(position=self._tntspawnpos,
                                      respawn_time=10.0)

    def spawn_player(self, player: Player) -> ba.Actor:
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
        if poweruptype is None:
            poweruptype = (PowerupBoxFactory.get().get_random_powerup_type(
                excludetypes=self._excludepowerups))
        PowerupBox(position=self.map.powerup_spawn_points[index],
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
                poweruptype=PowerupBoxFactory.get().get_random_powerup_type(
                    excludetypes=self._excludepowerups)).autoretain()

    def do_end(self, outcome: str) -> None:
        """End the game."""
        if outcome == 'defeat':
            self.fade_to_red()
        self.end(delay=2.0,
                 results={
                     'outcome': outcome,
                     'score': self._score,
                     'playerinfos': self.initialplayerinfos
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
                    assert isinstance(player.actor, PlayerSpaz)
                    assert player.actor.node
                    playerpts.append(player.actor.node.position)
            except Exception:
                ba.print_exception('Error updating bots.')
        for i in range(3):
            for playerpt in playerpts:
                dists[i] += abs(playerpt[0] - botspawnpts[i][0])
            dists[i] += random.random() * 5.0  # Minor random variation.
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
        for spawninfo in self._bot_spawn_types.values():
            total += spawninfo.spawnrate
        randval = random.random() * total

        # Now go back through and see where this value falls.
        total = 0
        bottype: Optional[Type[SpazBot]] = None
        for spawntype, spawninfo in self._bot_spawn_types.items():
            total += spawninfo.spawnrate
            if randval <= total:
                bottype = spawntype
                break
        spawn_time = 1.0
        assert bottype is not None
        self._bots.spawn_bot(bottype, pos=spawnpt, spawn_time=spawn_time)

        # After every spawn we adjust our ratios slightly to get more
        # difficult.
        for spawninfo in self._bot_spawn_types.values():
            spawninfo.spawnrate += spawninfo.increase
            spawninfo.increase += spawninfo.dincrease

    def _update_scores(self) -> None:
        score = self._score

        # Achievements apply to the default preset only.
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
        if isinstance(msg, ba.PlayerDiedMessage):
            player = msg.getplayer(Player)
            self.stats.player_was_killed(player)
            ba.timer(0.1, self._checkroundover)

        elif isinstance(msg, ba.PlayerScoredMessage):
            self._score += msg.score
            self._update_scores()

        elif isinstance(msg, SpazBotDiedMessage):
            pts, importance = msg.spazbot.get_death_points(msg.how)
            target: Optional[Sequence[float]]
            if msg.killerplayer:
                assert msg.spazbot.node
                target = msg.spazbot.node.position
                self.stats.player_scored(msg.killerplayer,
                                         pts,
                                         target=target,
                                         kill=True,
                                         screenmessage=False,
                                         importance=importance)
                ba.playsound(self._dingsound
                             if importance == 1 else self._dingsoundhigh,
                             volume=0.6)

            # Normally we pull scores from the score-set, but if there's no
            # player lets be explicit.
            else:
                self._score += pts
            self._update_scores()
        else:
            super().handlemessage(msg)

    def _on_got_scores_to_beat(self, scores: List[Dict[str, Any]]) -> None:
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
