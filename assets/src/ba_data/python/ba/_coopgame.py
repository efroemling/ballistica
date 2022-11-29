# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to co-op games."""
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import _ba
from ba import _internal
from ba._gameactivity import GameActivity
from ba._general import WeakCall

if TYPE_CHECKING:
    from typing import Sequence
    from bastd.actor.playerspaz import PlayerSpaz
    import ba

# pylint: disable=invalid-name
PlayerType = TypeVar('PlayerType', bound='ba.Player')
TeamType = TypeVar('TeamType', bound='ba.Team')
# pylint: enable=invalid-name


class CoopGameActivity(GameActivity[PlayerType, TeamType]):
    """Base class for cooperative-mode games.

    Category: **Gameplay Classes**
    """

    # We can assume our session is a CoopSession.
    session: ba.CoopSession

    @classmethod
    def supports_session_type(cls, sessiontype: type[ba.Session]) -> bool:
        from ba._coopsession import CoopSession

        return issubclass(sessiontype, CoopSession)

    def __init__(self, settings: dict):
        super().__init__(settings)

        # Cache these for efficiency.
        self._achievements_awarded: set[str] = set()

        self._life_warning_beep: ba.Actor | None = None
        self._life_warning_beep_timer: ba.Timer | None = None
        self._warn_beeps_sound = _ba.getsound('warnBeeps')

    def on_begin(self) -> None:
        super().on_begin()

        # Show achievements remaining.
        if not (_ba.app.demo_mode or _ba.app.arcade_mode):
            _ba.timer(3.8, WeakCall(self._show_remaining_achievements))

        # Preload achievement images in case we get some.
        _ba.timer(2.0, WeakCall(self._preload_achievements))

    # FIXME: this is now redundant with activityutils.getscoreconfig();
    #  need to kill this.
    def get_score_type(self) -> str:
        """
        Return the score unit this co-op game uses ('point', 'seconds', etc.)
        """
        return 'points'

    def _get_coop_level_name(self) -> str:
        assert self.session.campaign is not None
        return self.session.campaign.name + ':' + str(self.settings_raw['name'])

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
        achievements = _ba.app.ach.achievements_for_coop_level(
            self._get_coop_level_name()
        )
        for ach in achievements:
            ach.get_icon_texture(True)

    def _show_remaining_achievements(self) -> None:
        # pylint: disable=cyclic-import
        from ba._language import Lstr
        from bastd.actor.text import Text

        ts_h_offs = 30
        v_offs = -200
        achievements = [
            a
            for a in _ba.app.ach.achievements_for_coop_level(
                self._get_coop_level_name()
            )
            if not a.complete
        ]
        vrmode = _ba.app.vr_mode
        if achievements:
            Text(
                Lstr(resource='achievementsRemainingText'),
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
                transition_out_delay=1.3 if self.slow_motion else 4.0,
            ).autoretain()
            hval = 70
            vval = -50
            tdelay = 0.0
            for ach in achievements:
                tdelay += 0.05
                ach.create_display(
                    hval + 40,
                    vval + v_offs,
                    0 + tdelay,
                    outdelay=1.3 if self.slow_motion else 4.0,
                    style='in_game',
                )
                vval -= 55

    def spawn_player_spaz(
        self,
        player: PlayerType,
        position: Sequence[float] = (0.0, 0.0, 0.0),
        angle: float | None = None,
    ) -> PlayerSpaz:
        """Spawn and wire up a standard player spaz."""
        spaz = super().spawn_player_spaz(player, position, angle)

        # Deaths are noteworthy in co-op games.
        spaz.play_big_death_sound = True
        return spaz

    def _award_achievement(
        self, achievement_name: str, sound: bool = True
    ) -> None:
        """Award an achievement.

        Returns True if a banner will be shown;
        False otherwise
        """

        if achievement_name in self._achievements_awarded:
            return

        ach = _ba.app.ach.get_achievement(achievement_name)

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
            _internal.report_achievement(achievement_name)

            # ...and to our account.
            _internal.add_transaction(
                {'type': 'ACHIEVEMENT', 'name': achievement_name}
            )

            # Now bring up a celebration banner.
            ach.announce_completion(sound=sound)

    def fade_to_red(self) -> None:
        """Fade the screen to red; (such as when the good guys have lost)."""
        from ba import _gameutils

        c_existing = self.globalsnode.tint
        cnode = _ba.newnode(
            'combine',
            attrs={
                'input0': c_existing[0],
                'input1': c_existing[1],
                'input2': c_existing[2],
                'size': 3,
            },
        )
        _gameutils.animate(cnode, 'input1', {0: c_existing[1], 2.0: 0})
        _gameutils.animate(cnode, 'input2', {0: c_existing[2], 2.0: 0})
        cnode.connectattr('output', self.globalsnode, 'tint')

    def setup_low_life_warning_sound(self) -> None:
        """Set up a beeping noise to play when any players are near death."""
        self._life_warning_beep = None
        self._life_warning_beep_timer = _ba.Timer(
            1.0, WeakCall(self._update_life_warning), repeat=True
        )

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
                _ba.newnode(
                    'sound',
                    attrs={
                        'sound': self._warn_beeps_sound,
                        'positional': False,
                        'loop': True,
                    },
                )
            )
        if self._life_warning_beep is not None and not should_beep:
            self._life_warning_beep = None
