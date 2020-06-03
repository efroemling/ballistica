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
"""Functionality related to co-op games."""
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import _ba
from ba._gameactivity import GameActivity
from ba._general import WeakCall

if TYPE_CHECKING:
    from typing import Type, Dict, Any, Set, List, Sequence, Optional
    from bastd.actor.playerspaz import PlayerSpaz
    import ba

PlayerType = TypeVar('PlayerType', bound='ba.Player')
TeamType = TypeVar('TeamType', bound='ba.Team')


class CoopGameActivity(GameActivity[PlayerType, TeamType]):
    """Base class for cooperative-mode games.

    Category: Gameplay Classes
    """

    # We can assume our session is a CoopSession.
    session: ba.CoopSession

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        from ba._coopsession import CoopSession
        return issubclass(sessiontype, CoopSession)

    def __init__(self, settings: dict):
        super().__init__(settings)

        # Cache these for efficiency.
        self._achievements_awarded: Set[str] = set()

        self._life_warning_beep: Optional[ba.Actor] = None
        self._life_warning_beep_timer: Optional[ba.Timer] = None
        self._warn_beeps_sound = _ba.getsound('warnBeeps')

    def on_begin(self) -> None:
        super().on_begin()

        # Show achievements remaining.
        if not _ba.app.kiosk_mode:
            _ba.timer(3.8, WeakCall(self._show_remaining_achievements))

        # Preload achievement images in case we get some.
        _ba.timer(2.0, WeakCall(self._preload_achievements))

        # Let's ask the server for a 'time-to-beat' value.
        levelname = self._get_coop_level_name()
        campaign = self.session.campaign
        assert campaign is not None
        config_str = (str(len(self.players)) + 'p' + campaign.getlevel(
            self.settings_raw['name']).get_score_version_string().replace(
                ' ', '_'))
        _ba.get_scores_to_beat(levelname, config_str,
                               WeakCall(self._on_got_scores_to_beat))

    def _on_got_scores_to_beat(self, scores: List[Dict[str, Any]]) -> None:
        pass

    def _show_standard_scores_to_beat_ui(self,
                                         scores: List[Dict[str, Any]]) -> None:
        from ba._gameutils import timestring, animate
        from ba._nodeactor import NodeActor
        from ba._enums import TimeFormat
        display_type = self.get_score_type()
        if scores is not None:

            # Sort by originating date so that the most recent is first.
            scores.sort(reverse=True, key=lambda s: s['time'])

            # Now make a display for the most recent challenge.
            for score in scores:
                if score['type'] == 'score_challenge':
                    tval = (score['player'] + ':  ' + timestring(
                        int(score['value']) * 10,
                        timeformat=TimeFormat.MILLISECONDS).evaluate()
                            if display_type == 'time' else str(score['value']))
                    hattach = 'center' if display_type == 'time' else 'left'
                    halign = 'center' if display_type == 'time' else 'left'
                    pos = (20, -70) if display_type == 'time' else (20, -130)
                    txt = NodeActor(
                        _ba.newnode('text',
                                    attrs={
                                        'v_attach': 'top',
                                        'h_attach': hattach,
                                        'h_align': halign,
                                        'color': (0.7, 0.4, 1, 1),
                                        'shadow': 0.5,
                                        'flatness': 1.0,
                                        'position': pos,
                                        'scale': 0.6,
                                        'text': tval
                                    })).autoretain()
                    assert txt.node is not None
                    animate(txt.node, 'scale', {1.0: 0.0, 1.1: 0.7, 1.2: 0.6})
                    break

    # FIXME: this is now redundant with activityutils.getscoreconfig();
    #  need to kill this.
    def get_score_type(self) -> str:
        """
        Return the score unit this co-op game uses ('point', 'seconds', etc.)
        """
        return 'points'

    def _get_coop_level_name(self) -> str:
        assert self.session.campaign is not None
        return self.session.campaign.name + ':' + str(
            self.settings_raw['name'])

    def celebrate(self, duration: float) -> None:
        """Tells all existing player-controlled characters to celebrate.

        Can be useful in co-op games when the good guys score or complete
        a wave.
        duration is given in seconds.
        """
        from ba._messages import CelebrateMessage
        for player in self.players:
            if player.actor:
                player.actor.handlemessage(CelebrateMessage(duration))

    def _preload_achievements(self) -> None:
        from ba import _achievement
        achievements = _achievement.get_achievements_for_coop_level(
            self._get_coop_level_name())
        for ach in achievements:
            ach.get_icon_texture(True)

    def _show_remaining_achievements(self) -> None:
        # pylint: disable=cyclic-import
        from ba._achievement import get_achievements_for_coop_level
        from ba._lang import Lstr
        from bastd.actor.text import Text
        ts_h_offs = 30
        v_offs = -200
        achievements = [
            a for a in get_achievements_for_coop_level(
                self._get_coop_level_name()) if not a.complete
        ]
        vrmode = _ba.app.vr_mode
        if achievements:
            Text(Lstr(resource='achievementsRemainingText'),
                 host_only=True,
                 position=(ts_h_offs - 10 + 40, v_offs - 10),
                 transition=Text.Transition.FADE_IN,
                 scale=1.1,
                 h_attach=Text.HAttach.LEFT,
                 v_attach=Text.VAttach.TOP,
                 color=(1, 1, 1.2, 1) if vrmode else (0.8, 0.8, 1.0, 1.0),
                 flatness=1.0 if vrmode else 0.6,
                 shadow=1.0 if vrmode else 0.5,
                 transition_delay=0.0,
                 transition_out_delay=1.3
                 if self.slow_motion else 4.0).autoretain()
            hval = 70
            vval = -50
            tdelay = 0.0
            for ach in achievements:
                tdelay += 0.05
                ach.create_display(hval + 40,
                                   vval + v_offs,
                                   0 + tdelay,
                                   outdelay=1.3 if self.slow_motion else 4.0,
                                   style='in_game')
                vval -= 55

    def spawn_player_spaz(self,
                          player: PlayerType,
                          position: Sequence[float] = (0.0, 0.0, 0.0),
                          angle: float = None) -> PlayerSpaz:
        """Spawn and wire up a standard player spaz."""
        spaz = super().spawn_player_spaz(player, position, angle)

        # Deaths are noteworthy in co-op games.
        spaz.play_big_death_sound = True
        return spaz

    def _award_achievement(self,
                           achievement_name: str,
                           sound: bool = True) -> None:
        """Award an achievement.

        Returns True if a banner will be shown;
        False otherwise
        """
        from ba._achievement import get_achievement

        if achievement_name in self._achievements_awarded:
            return

        ach = get_achievement(achievement_name)

        # If we're in the easy campaign and this achievement is hard-mode-only,
        # ignore it.
        try:
            campaign = self.session.campaign
            assert campaign is not None
            if ach.hard_mode_only and campaign.name == 'Easy':
                return
        except Exception:
            from ba._error import print_exception
            print_exception()

        # If we haven't awarded this one, check to see if we've got it.
        # If not, set it through the game service *and* add a transaction
        # for it.
        if not ach.complete:
            self._achievements_awarded.add(achievement_name)

            # Report new achievements to the game-service.
            _ba.report_achievement(achievement_name)

            # ...and to our account.
            _ba.add_transaction({
                'type': 'ACHIEVEMENT',
                'name': achievement_name
            })

            # Now bring up a celebration banner.
            ach.announce_completion(sound=sound)

    def fade_to_red(self) -> None:
        """Fade the screen to red; (such as when the good guys have lost)."""
        from ba import _gameutils
        c_existing = self.globalsnode.tint
        cnode = _ba.newnode('combine',
                            attrs={
                                'input0': c_existing[0],
                                'input1': c_existing[1],
                                'input2': c_existing[2],
                                'size': 3
                            })
        _gameutils.animate(cnode, 'input1', {0: c_existing[1], 2.0: 0})
        _gameutils.animate(cnode, 'input2', {0: c_existing[2], 2.0: 0})
        cnode.connectattr('output', self.globalsnode, 'tint')

    def setup_low_life_warning_sound(self) -> None:
        """Set up a beeping noise to play when any players are near death."""
        self._life_warning_beep = None
        self._life_warning_beep_timer = _ba.Timer(
            1.0, WeakCall(self._update_life_warning), repeat=True)

    def _update_life_warning(self) -> None:
        # Beep continuously if anyone is close to death.
        should_beep = False
        for player in self.players:
            if player.is_alive():
                # FIXME: Should abstract this instead of
                #  reading hitpoints directly.
                if getattr(player.actor, 'hitpoints', 999) < 200:
                    should_beep = True
                    break
        if should_beep and self._life_warning_beep is None:
            from ba._nodeactor import NodeActor
            self._life_warning_beep = NodeActor(
                _ba.newnode('sound',
                            attrs={
                                'sound': self._warn_beeps_sound,
                                'positional': False,
                                'loop': True
                            }))
        if self._life_warning_beep is not None and not should_beep:
            self._life_warning_beep = None
