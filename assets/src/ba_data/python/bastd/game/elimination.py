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
"""Elimination mini-game."""

# ba_meta require api 6
# (see https://github.com/efroemling/ballistica/wiki/Meta-Tags)

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.actor import playerspaz
from bastd.actor import spaz

if TYPE_CHECKING:
    from typing import (Any, Tuple, Dict, Type, List, Sequence, Optional,
                        Union)


class Icon(ba.Actor):
    """Creates in in-game icon on screen."""

    def __init__(self,
                 player: ba.Player,
                 position: Tuple[float, float],
                 scale: float,
                 show_lives: bool = True,
                 show_death: bool = True,
                 name_scale: float = 1.0,
                 name_maxwidth: float = 115.0,
                 flatness: float = 1.0,
                 shadow: float = 1.0):
        super().__init__()

        self._player = player
        self._show_lives = show_lives
        self._show_death = show_death
        self._name_scale = name_scale
        self._outline_tex = ba.gettexture('characterIconMask')

        icon = player.get_icon()
        self.node = ba.newnode('image',
                               delegate=self,
                               attrs={
                                   'texture': icon['texture'],
                                   'tint_texture': icon['tint_texture'],
                                   'tint_color': icon['tint_color'],
                                   'vr_depth': 400,
                                   'tint2_color': icon['tint2_color'],
                                   'mask_texture': self._outline_tex,
                                   'opacity': 1.0,
                                   'absolute_scale': True,
                                   'attach': 'bottomCenter'
                               })
        self._name_text = ba.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': ba.Lstr(value=player.get_name()),
                'color': ba.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': name_maxwidth,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom'
            })
        if self._show_lives:
            self._lives_text = ba.newnode('text',
                                          owner=self.node,
                                          attrs={
                                              'text': 'x0',
                                              'color': (1, 1, 0.5),
                                              'h_align': 'left',
                                              'vr_depth': 430,
                                              'shadow': 1.0,
                                              'flatness': 1.0,
                                              'h_attach': 'center',
                                              'v_attach': 'bottom'
                                          })
        self.set_position_and_scale(position, scale)

    def set_position_and_scale(self, position: Tuple[float, float],
                               scale: float) -> None:
        """(Re)position the icon."""
        assert self.node
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._name_text.position = (position[0], position[1] + scale * 52.0)
        self._name_text.scale = 1.0 * scale * self._name_scale
        if self._show_lives:
            self._lives_text.position = (position[0] + scale * 10.0,
                                         position[1] - scale * 43.0)
            self._lives_text.scale = 1.0 * scale

    def update_for_lives(self) -> None:
        """Update for the target player's current lives."""
        if self._player:
            lives = self._player.gamedata['lives']
        else:
            lives = 0
        if self._show_lives:
            if lives > 0:
                self._lives_text.text = 'x' + str(lives - 1)
            else:
                self._lives_text.text = ''
        if lives == 0:
            self._name_text.opacity = 0.2
            assert self.node
            self.node.color = (0.7, 0.3, 0.3)
            self.node.opacity = 0.2

    def handle_player_spawned(self) -> None:
        """Our player spawned; hooray!"""
        if not self.node:
            return
        self.node.opacity = 1.0
        self.update_for_lives()

    def handle_player_died(self) -> None:
        """Well poo; our player died."""
        if not self.node:
            return
        if self._show_death:
            ba.animate(
                self.node, 'opacity', {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 1.0,
                    0.55: 0.2
                })
            lives = self._player.gamedata['lives']
            if lives == 0:
                ba.timer(0.6, self.update_for_lives)


# ba_meta export game
class EliminationGame(ba.TeamGameActivity[ba.Player, ba.Team]):
    """Game type where last player(s) left alive win."""

    @classmethod
    def get_name(cls) -> str:
        return 'Elimination'

    @classmethod
    def get_score_info(cls) -> ba.ScoreInfo:
        return ba.ScoreInfo(label='Survived',
                            scoretype=ba.ScoreType.SECONDS,
                            none_is_winner=True)

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        return 'Last remaining alive wins.'

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
            ('Lives Per Player', {
                'default': 1, 'min_value': 1,
                'max_value': 10, 'increment': 1
            }),
            ('Time Limit', {
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120), ('5 Minutes', 300),
                            ('10 Minutes', 600), ('20 Minutes', 1200)],
                'default': 0
            }),
            ('Respawn Times', {
                'choices': [('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0),
                            ('Long', 2.0), ('Longer', 4.0)],
                'default': 1.0
            }),
            ('Epic Mode', {'default': False})]  # yapf: disable

        if issubclass(sessiontype, ba.DualTeamSession):
            settings.append(('Solo Mode', {'default': False}))
            settings.append(('Balance Total Lives', {'default': False}))

        return settings

    def __init__(self, settings: Dict[str, Any]):
        from bastd.actor.scoreboard import Scoreboard
        super().__init__(settings)
        if self.settings_raw['Epic Mode']:
            self.slow_motion = True

        # Show messages when players die since it's meaningful here.
        self.announce_player_deaths = True

        self._solo_mode = settings.get('Solo Mode', False)
        self._scoreboard = Scoreboard()
        self._start_time: Optional[float] = None
        self._vs_text: Optional[ba.Actor] = None
        self._round_end_timer: Optional[ba.Timer] = None

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Last team standing wins.' if isinstance(
            self.session, ba.DualTeamSession) else 'Last one standing wins.'

    def get_instance_scoreboard_description(self) -> Union[str, Sequence]:
        return 'last team standing wins' if isinstance(
            self.session, ba.DualTeamSession) else 'last one standing wins'

    def on_transition_in(self) -> None:
        self.default_music = (ba.MusicType.EPIC
                              if self.settings_raw['Epic Mode'] else
                              ba.MusicType.SURVIVAL)
        super().on_transition_in()
        self._start_time = ba.time()

    def on_team_join(self, team: ba.Team) -> None:
        team.gamedata['survival_seconds'] = None
        team.gamedata['spawn_order'] = []

    def on_player_join(self, player: ba.Player) -> None:

        # No longer allowing mid-game joiners here; too easy to exploit.
        if self.has_begun():
            player.gamedata['lives'] = 0
            player.gamedata['icons'] = []

            # Make sure our team has survival seconds set if they're all dead
            # (otherwise blocked new ffa players would be considered 'still
            # alive' in score tallying).
            if self._get_total_team_lives(
                    player.team
            ) == 0 and player.team.gamedata['survival_seconds'] is None:
                player.team.gamedata['survival_seconds'] = 0
            ba.screenmessage(ba.Lstr(resource='playerDelayedJoinText',
                                     subs=[('${PLAYER}',
                                            player.get_name(full=True))]),
                             color=(0, 1, 0))
            return

        player.gamedata['lives'] = self.settings_raw['Lives Per Player']

        if self._solo_mode:
            player.gamedata['icons'] = []
            player.team.gamedata['spawn_order'].append(player)
            self._update_solo_mode()
        else:
            # Create our icon and spawn.
            player.gamedata['icons'] = [
                Icon(player, position=(0, 50), scale=0.8)
            ]
            if player.gamedata['lives'] > 0:
                self.spawn_player(player)

        # Don't waste time doing this until begin.
        if self.has_begun():
            self._update_icons()

    def _update_solo_mode(self) -> None:
        # For both teams, find the first player on the spawn order list with
        # lives remaining and spawn them if they're not alive.
        for team in self.teams:
            # Prune dead players from the spawn order.
            team.gamedata['spawn_order'] = [
                p for p in team.gamedata['spawn_order'] if p
            ]
            for player in team.gamedata['spawn_order']:
                if player.gamedata['lives'] > 0:
                    if not player.is_alive():
                        self.spawn_player(player)
                    break

    def _update_icons(self) -> None:
        # pylint: disable=too-many-branches

        # In free-for-all mode, everyone is just lined up along the bottom.
        if isinstance(self.session, ba.FreeForAllSession):
            count = len(self.teams)
            x_offs = 85
            xval = x_offs * (count - 1) * -0.5
            for team in self.teams:
                if len(team.players) == 1:
                    player = team.players[0]
                    for icon in player.gamedata['icons']:
                        icon.set_position_and_scale((xval, 30), 0.7)
                        icon.update_for_lives()
                    xval += x_offs

        # In teams mode we split up teams.
        else:
            if self._solo_mode:
                # First off, clear out all icons.
                for player in self.players:
                    player.gamedata['icons'] = []

                # Now for each team, cycle through our available players
                # adding icons.
                for team in self.teams:
                    if team.id == 0:
                        xval = -60
                        x_offs = -78
                    else:
                        xval = 60
                        x_offs = 78
                    is_first = True
                    test_lives = 1
                    while True:
                        players_with_lives = [
                            p for p in team.gamedata['spawn_order']
                            if p and p.gamedata['lives'] >= test_lives
                        ]
                        if not players_with_lives:
                            break
                        for player in players_with_lives:
                            player.gamedata['icons'].append(
                                Icon(player,
                                     position=(xval, (40 if is_first else 25)),
                                     scale=1.0 if is_first else 0.5,
                                     name_maxwidth=130 if is_first else 75,
                                     name_scale=0.8 if is_first else 1.0,
                                     flatness=0.0 if is_first else 1.0,
                                     shadow=0.5 if is_first else 1.0,
                                     show_death=is_first,
                                     show_lives=False))
                            xval += x_offs * (0.8 if is_first else 0.56)
                            is_first = False
                        test_lives += 1
            # Non-solo mode.
            else:
                for team in self.teams:
                    if team.id == 0:
                        xval = -50
                        x_offs = -85
                    else:
                        xval = 50
                        x_offs = 85
                    for player in team.players:
                        for icon in player.gamedata['icons']:
                            icon.set_position_and_scale((xval, 30), 0.7)
                            icon.update_for_lives()
                        xval += x_offs

    def _get_spawn_point(self, player: ba.Player) -> Optional[ba.Vec3]:
        del player  # Unused.

        # In solo-mode, if there's an existing live player on the map, spawn at
        # whichever spot is farthest from them (keeps the action spread out).
        if self._solo_mode:
            living_player = None
            living_player_pos = None
            for team in self.teams:
                for tplayer in team.players:
                    if tplayer.is_alive():
                        assert tplayer.node
                        ppos = tplayer.node.position
                        living_player = tplayer
                        living_player_pos = ppos
                        break
            if living_player:
                assert living_player_pos is not None
                player_pos = ba.Vec3(living_player_pos)
                points: List[Tuple[float, ba.Vec3]] = []
                for team in self.teams:
                    start_pos = ba.Vec3(self.map.get_start_position(team.id))
                    points.append(
                        ((start_pos - player_pos).length(), start_pos))
                # Hmm.. we need to sorting vectors too?
                points.sort(key=lambda x: x[0])
                return points[-1][1]
        return None

    def spawn_player(self, player: ba.Player) -> ba.Actor:
        actor = self.spawn_player_spaz(player, self._get_spawn_point(player))
        if not self._solo_mode:
            ba.timer(0.3, ba.Call(self._print_lives, player))

        # If we have any icons, update their state.
        for icon in player.gamedata['icons']:
            icon.handle_player_spawned()
        return actor

    def _print_lives(self, player: ba.Player) -> None:
        from bastd.actor import popuptext
        assert player  # Shouldn't be passing invalid refs around.
        if not player or not player.is_alive() or not player.node:
            return

        popuptext.PopupText('x' + str(player.gamedata['lives'] - 1),
                            color=(1, 1, 0, 1),
                            offset=(0, -0.8, 0),
                            random_offset=0.0,
                            scale=1.8,
                            position=player.node.position).autoretain()

    def on_player_leave(self, player: ba.Player) -> None:
        super().on_player_leave(player)
        player.gamedata['icons'] = None

        # Remove us from spawn-order.
        if self._solo_mode:
            if player in player.team.gamedata['spawn_order']:
                player.team.gamedata['spawn_order'].remove(player)

        # Update icons in a moment since our team will be gone from the
        # list then.
        ba.timer(0, self._update_icons)

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self.settings_raw['Time Limit'])
        self.setup_standard_powerup_drops()
        if self._solo_mode:
            self._vs_text = ba.NodeActor(
                ba.newnode('text',
                           attrs={
                               'position': (0, 105),
                               'h_attach': 'center',
                               'h_align': 'center',
                               'maxwidth': 200,
                               'shadow': 0.5,
                               'vr_depth': 390,
                               'scale': 0.6,
                               'v_attach': 'bottom',
                               'color': (0.8, 0.8, 0.3, 1.0),
                               'text': ba.Lstr(resource='vsText')
                           }))

        # If balance-team-lives is on, add lives to the smaller team until
        # total lives match.
        if (isinstance(self.session, ba.DualTeamSession)
                and self.settings_raw['Balance Total Lives']
                and self.teams[0].players and self.teams[1].players):
            if self._get_total_team_lives(
                    self.teams[0]) < self._get_total_team_lives(self.teams[1]):
                lesser_team = self.teams[0]
                greater_team = self.teams[1]
            else:
                lesser_team = self.teams[1]
                greater_team = self.teams[0]
            add_index = 0
            while self._get_total_team_lives(
                    lesser_team) < self._get_total_team_lives(greater_team):
                lesser_team.players[add_index].gamedata['lives'] += 1
                add_index = (add_index + 1) % len(lesser_team.players)

        self._update_icons()

        # We could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it.
        ba.timer(1.0, self._update, repeat=True)

    def _get_total_team_lives(self, team: ba.Team) -> int:
        return sum(player.gamedata['lives'] for player in team.players)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, playerspaz.PlayerSpazDeathMessage):

            # Augment standard behavior.
            super().handlemessage(msg)
            player = msg.playerspaz(self).player

            player.gamedata['lives'] -= 1
            if player.gamedata['lives'] < 0:
                ba.print_error(
                    "Got lives < 0 in Elim; this shouldn't happen. solo:" +
                    str(self._solo_mode))
                player.gamedata['lives'] = 0

            # If we have any icons, update their state.
            for icon in player.gamedata['icons']:
                icon.handle_player_died()

            # Play big death sound on our last death
            # or for every one in solo mode.
            if self._solo_mode or player.gamedata['lives'] == 0:
                ba.playsound(spaz.get_factory().single_player_death_sound)

            # If we hit zero lives, we're dead (and our team might be too).
            if player.gamedata['lives'] == 0:
                # If the whole team is now dead, mark their survival time.
                if self._get_total_team_lives(player.team) == 0:
                    assert self._start_time is not None
                    player.team.gamedata['survival_seconds'] = int(
                        ba.time() - self._start_time)
            else:
                # Otherwise, in regular mode, respawn.
                if not self._solo_mode:
                    self.respawn_player(player)

            # In solo, put ourself at the back of the spawn order.
            if self._solo_mode:
                player.team.gamedata['spawn_order'].remove(player)
                player.team.gamedata['spawn_order'].append(player)

    def _update(self) -> None:
        if self._solo_mode:
            # For both teams, find the first player on the spawn order
            # list with lives remaining and spawn them if they're not alive.
            for team in self.teams:
                # Prune dead players from the spawn order.
                team.gamedata['spawn_order'] = [
                    p for p in team.gamedata['spawn_order'] if p
                ]
                for player in team.gamedata['spawn_order']:
                    if player.gamedata['lives'] > 0:
                        if not player.is_alive():
                            self.spawn_player(player)
                            self._update_icons()
                        break

        # If we're down to 1 or fewer living teams, start a timer to end
        # the game (allows the dust to settle and draws to occur if deaths
        # are close enough).
        if len(self._get_living_teams()) < 2:
            self._round_end_timer = ba.Timer(0.5, self.end_game)

    def _get_living_teams(self) -> List[ba.Team]:
        return [
            team for team in self.teams
            if len(team.players) > 0 and any(player.gamedata['lives'] > 0
                                             for player in team.players)
        ]

    def end_game(self) -> None:
        if self.has_ended():
            return
        results = ba.TeamGameResults()
        self._vs_text = None  # Kill our 'vs' if its there.
        for team in self.teams:
            results.set_team_score(team, team.gamedata['survival_seconds'])
        self.end(results=results)
