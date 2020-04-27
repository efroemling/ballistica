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
"""Functionality related to team games."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._freeforallsession import FreeForAllSession
from ba._gameactivity import GameActivity
from ba._gameresults import TeamGameResults
from ba._dualteamsession import DualTeamSession

if TYPE_CHECKING:
    from typing import Any, Dict, Type, Sequence
    from bastd.actor.playerspaz import PlayerSpaz
    import ba


class TeamGameActivity(GameActivity):
    """Base class for teams and free-for-all mode games.

    Category: Gameplay Classes

    (Free-for-all is essentially just a special case where every
    ba.Player has their own ba.Team)
    """

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        """
        Class method override;
        returns True for ba.DualTeamSessions and ba.FreeForAllSessions;
        False otherwise.
        """
        return (issubclass(sessiontype, DualTeamSession)
                or issubclass(sessiontype, FreeForAllSession))

    def __init__(self, settings: Dict[str, Any]):
        super().__init__(settings)

        # By default we don't show kill-points in free-for-all.
        # (there's usually some activity-specific score and we don't
        # wanna confuse things)
        if isinstance(_ba.getsession(), FreeForAllSession):
            self._show_kill_points = False

    def on_transition_in(self) -> None:
        # pylint: disable=cyclic-import
        from ba._coopsession import CoopSession
        from bastd.actor.controlsguide import ControlsGuide
        super().on_transition_in()

        # On the first game, show the controls UI momentarily.
        # (unless we're being run in co-op mode, in which case we leave
        # it up to them)
        if not isinstance(self.session, CoopSession):
            # FIXME: Need an elegant way to store on session.
            if not self.session.have_shown_controls_help_overlay:
                delay = 4.0
                lifespan = 10.0
                if self.slow_motion:
                    lifespan *= 0.3
                ControlsGuide(delay=delay,
                              lifespan=lifespan,
                              scale=0.8,
                              position=(380, 200),
                              bright=True).autoretain()
                self.session.have_shown_controls_help_overlay = True

    def on_begin(self) -> None:
        super().on_begin()
        try:
            # Award a few achievements.
            if isinstance(self.session, FreeForAllSession):
                if len(self.players) >= 2:
                    from ba import _achievement
                    _achievement.award_local_achievement('Free Loader')
            elif isinstance(self.session, DualTeamSession):
                if len(self.players) >= 4:
                    from ba import _achievement
                    _achievement.award_local_achievement('Team Player')
        except Exception:
            from ba import _error
            _error.print_exception()

    def spawn_player_spaz(self,
                          player: ba.Player,
                          position: Sequence[float] = None,
                          angle: float = None) -> PlayerSpaz:
        """
        Method override; spawns and wires up a standard ba.PlayerSpaz for
        a ba.Player.

        If position or angle is not supplied, a default will be chosen based
        on the ba.Player and their ba.Team.
        """
        if position is None:
            # In teams-mode get our team-start-location.
            if isinstance(self.session, DualTeamSession):
                position = (self.map.get_start_position(player.team.get_id()))
            else:
                # Otherwise do free-for-all spawn locations.
                position = self.map.get_ffa_start_position(self.players)

        return super().spawn_player_spaz(player, position, angle)

    def end(  # type: ignore
            self,
            results: Any = None,
            announce_winning_team: bool = True,
            announce_delay: float = 0.1,
            force: bool = False) -> None:
        """
        End the game and announce the single winning team
        unless 'announce_winning_team' is False.
        (for results without a single most-important winner).
        """
        # pylint: disable=arguments-differ
        from ba._coopsession import CoopSession
        from ba._multiteamsession import MultiTeamSession
        from ba._general import Call

        # Announce win (but only for the first finish() call)
        # (also don't announce in co-op sessions; we leave that up to them).
        session = self.session
        if not isinstance(session, CoopSession):
            do_announce = not self.has_ended()
            super().end(results, delay=2.0 + announce_delay, force=force)
            # Need to do this *after* end end call so that results is valid.
            assert isinstance(results, TeamGameResults)
            if do_announce and isinstance(session, MultiTeamSession):
                session.announce_game_results(
                    self,
                    results,
                    delay=announce_delay,
                    announce_winning_team=announce_winning_team)

        # For co-op we just pass this up the chain with a delay added
        # (in most cases). Team games expect a delay for the announce
        # portion in teams/ffa mode so this keeps it consistent.
        else:
            # don't want delay on restarts..
            if (isinstance(results, dict) and 'outcome' in results
                    and results['outcome'] == 'restart'):
                delay = 0.0
            else:
                delay = 2.0
                _ba.timer(0.1, Call(_ba.playsound, _ba.getsound('boxingBell')))
            super().end(results, delay=delay, force=force)
