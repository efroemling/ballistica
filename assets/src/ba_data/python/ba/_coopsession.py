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
"""Functionality related to coop-mode sessions."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._session import Session

if TYPE_CHECKING:
    from typing import Any, List, Dict, Optional, Callable, Sequence
    import ba

TEAM_COLORS = [(0.2, 0.4, 1.6)]
TEAM_NAMES = ['Good Guys']


class CoopSession(Session):
    """A ba.Session which runs cooperative-mode games.

    Category: Gameplay Classes

    These generally consist of 1-4 players against
    the computer and include functionality such as
    high score lists.

    Attrs:

        campaign
            The ba.Campaign instance this Session represents, or None if
            there is no associated Campaign.
    """
    use_teams = True
    use_team_colors = False
    allow_mid_activity_joins = False

    # Note: even though these are instance vars, we annotate them at the
    # class level so that docs generation can access their types.
    campaign: Optional[ba.Campaign]

    def __init__(self) -> None:
        """Instantiate a co-op mode session."""
        # pylint: disable=cyclic-import
        from ba._campaign import getcampaign
        from bastd.activity.coopjoin import CoopJoinActivity

        _ba.increment_analytics_count('Co-op session start')
        app = _ba.app

        # If they passed in explicit min/max, honor that.
        # Otherwise defer to user overrides or defaults.
        if 'min_players' in app.coop_session_args:
            min_players = app.coop_session_args['min_players']
        else:
            min_players = 1
        if 'max_players' in app.coop_session_args:
            max_players = app.coop_session_args['max_players']
        else:
            max_players = app.config.get('Coop Game Max Players', 4)

        # print('FIXME: COOP SESSION WOULD CALC DEPS.')
        depsets: Sequence[ba.DependencySet] = []

        super().__init__(depsets,
                         team_names=TEAM_NAMES,
                         team_colors=TEAM_COLORS,
                         min_players=min_players,
                         max_players=max_players)

        # Tournament-ID if we correspond to a co-op tournament (otherwise None)
        self.tournament_id: Optional[str] = (
            app.coop_session_args.get('tournament_id'))

        self.campaign = getcampaign(app.coop_session_args['campaign'])
        self.campaign_level_name: str = app.coop_session_args['level']

        self._ran_tutorial_activity = False
        self._tutorial_activity: Optional[ba.Activity] = None
        self._custom_menu_ui: List[Dict[str, Any]] = []

        # Start our joining screen.
        self.setactivity(_ba.newactivity(CoopJoinActivity))

        self._next_game_instance: Optional[ba.GameActivity] = None
        self._next_game_level_name: Optional[str] = None
        self._update_on_deck_game_instances()

    def get_current_game_instance(self) -> ba.GameActivity:
        """Get the game instance currently being played."""
        return self._current_game_instance

    def _update_on_deck_game_instances(self) -> None:
        # pylint: disable=cyclic-import
        from ba._gameactivity import GameActivity

        # Instantiate levels we may be running soon to let them load in the bg.

        # Build an instance for the current level.
        assert self.campaign is not None
        level = self.campaign.getlevel(self.campaign_level_name)
        gametype = level.gametype
        settings = level.get_settings()

        # Make sure all settings the game expects are present.
        neededsettings = gametype.get_available_settings(type(self))
        for setting in neededsettings:
            if setting.name not in settings:
                settings[setting.name] = setting.default

        newactivity = _ba.newactivity(gametype, settings)
        assert isinstance(newactivity, GameActivity)
        self._current_game_instance: GameActivity = newactivity

        # Find the next level and build an instance for it too.
        levels = self.campaign.levels
        level = self.campaign.getlevel(self.campaign_level_name)

        nextlevel: Optional[ba.Level]
        if level.index < len(levels) - 1:
            nextlevel = levels[level.index + 1]
        else:
            nextlevel = None
        if nextlevel:
            gametype = nextlevel.gametype
            settings = nextlevel.get_settings()

            # Make sure all settings the game expects are present.
            neededsettings = gametype.get_available_settings(type(self))
            for setting in neededsettings:
                if setting.name not in settings:
                    settings[setting.name] = setting.default

            # We wanna be in the activity's context while taking it down.
            newactivity = _ba.newactivity(gametype, settings)
            assert isinstance(newactivity, GameActivity)
            self._next_game_instance = newactivity
            self._next_game_level_name = nextlevel.name
        else:
            self._next_game_instance = None
            self._next_game_level_name = None

        # Special case:
        # If our current level is 'onslaught training', instantiate
        # our tutorial so its ready to go. (if we haven't run it yet).
        if (self.campaign_level_name == 'Onslaught Training'
                and self._tutorial_activity is None
                and not self._ran_tutorial_activity):
            from bastd.tutorial import TutorialActivity
            self._tutorial_activity = _ba.newactivity(TutorialActivity)

    def get_custom_menu_entries(self) -> List[Dict[str, Any]]:
        return self._custom_menu_ui

    def on_player_leave(self, sessionplayer: ba.SessionPlayer) -> None:
        from ba._general import WeakCall
        super().on_player_leave(sessionplayer)

        # If all our players leave we wanna quit out of the session.
        _ba.timer(2.0, WeakCall(self._end_session_if_empty))

    def _end_session_if_empty(self) -> None:
        activity = self.getactivity()
        if activity is None:
            return  # Hmm what should we do in this case?

        # If there's still players in the current activity, we're good.
        if activity.players:
            return

        # If there's *no* players left in the current activity but there *is*
        # in the session, restart the activity to pull them into the game
        # (or quit if they're just in the lobby).
        if not activity.players and self.sessionplayers:

            # Special exception for tourney games; don't auto-restart these.
            if self.tournament_id is not None:
                self.end()
            else:
                # Don't restart joining activities; this probably means there's
                # someone with a chooser up in that case.
                if not activity.is_joining_activity:
                    self.restart()

        # Hmm; no players anywhere. lets just end the session.
        else:
            self.end()

    def _on_tournament_restart_menu_press(
            self, resume_callback: Callable[[], Any]) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.tournamententry import TournamentEntryWindow
        from ba._gameactivity import GameActivity
        activity = self.getactivity()
        if activity is not None and not activity.expired:
            assert self.tournament_id is not None
            assert isinstance(activity, GameActivity)
            TournamentEntryWindow(tournament_id=self.tournament_id,
                                  tournament_activity=activity,
                                  on_close_call=resume_callback)

    def restart(self) -> None:
        """Restart the current game activity."""

        # Tell the current activity to end with a 'restart' outcome.
        # We use 'force' so that we apply even if end has already been called
        # (but is in its delay period).

        # Make an exception if there's no players left. Otherwise this
        # can override the default session end that occurs in that case.
        if not self.sessionplayers:
            return

        # This method may get called from the UI context so make sure we
        # explicitly run in the activity's context.
        activity = self.getactivity()
        if activity is not None and not activity.expired:
            activity.can_show_ad_on_death = True
            with _ba.Context(activity):
                activity.end(results={'outcome': 'restart'}, force=True)

    def on_activity_end(self, activity: ba.Activity, results: Any) -> None:
        """Method override for co-op sessions.

        Jumps between co-op games and score screens.
        """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        from ba._activitytypes import JoinActivity, TransitionActivity
        from ba._lang import Lstr
        from ba._general import WeakCall
        from ba._coopgame import CoopGameActivity
        from ba._gameresults import GameResults
        from ba._score import ScoreType
        from ba._player import PlayerInfo
        from bastd.tutorial import TutorialActivity
        from bastd.activity.coopscore import CoopScoreScreen

        app = _ba.app

        # If we're running a TeamGameActivity we'll have a GameResults
        # as results. Otherwise its an old CoopGameActivity so its giving
        # us a dict of random stuff.
        if isinstance(results, GameResults):
            outcome = 'defeat'  # This can't be 'beaten'.
        else:
            outcome = '' if results is None else results.get('outcome', '')

        # If at any point we have no in-game players, quit out of the session
        # (this can happen if someone leaves in the tutorial for instance).
        active_players = [p for p in self.sessionplayers if p.in_game]
        if not active_players:
            self.end()
            return

        # If we're in a between-round activity or a restart-activity,
        # hop into a round.
        if (isinstance(activity,
                       (JoinActivity, CoopScoreScreen, TransitionActivity))):

            if outcome == 'next_level':
                if self._next_game_instance is None:
                    raise RuntimeError()
                assert self._next_game_level_name is not None
                self.campaign_level_name = self._next_game_level_name
                next_game = self._next_game_instance
            else:
                next_game = self._current_game_instance

            # Special case: if we're coming from a joining-activity
            # and will be going into onslaught-training, show the
            # tutorial first.
            if (isinstance(activity, JoinActivity)
                    and self.campaign_level_name == 'Onslaught Training'
                    and not app.kiosk_mode):
                if self._tutorial_activity is None:
                    raise RuntimeError('Tutorial not preloaded properly.')
                self.setactivity(self._tutorial_activity)
                self._tutorial_activity = None
                self._ran_tutorial_activity = True
                self._custom_menu_ui = []

            # Normal case; launch the next round.
            else:

                # Reset stats for the new activity.
                self.stats.reset()
                for player in self.sessionplayers:

                    # Skip players that are still choosing a team.
                    if player.in_game:
                        self.stats.register_sessionplayer(player)
                self.stats.setactivity(next_game)

                # Now flip the current activity..
                self.setactivity(next_game)

                if not app.kiosk_mode:
                    if self.tournament_id is not None:
                        self._custom_menu_ui = [{
                            'label':
                                Lstr(resource='restartText'),
                            'resume_on_call':
                                False,
                            'call':
                                WeakCall(self._on_tournament_restart_menu_press
                                         )
                        }]
                    else:
                        self._custom_menu_ui = [{
                            'label': Lstr(resource='restartText'),
                            'call': WeakCall(self.restart)
                        }]

        # If we were in a tutorial, just pop a transition to get to the
        # actual round.
        elif isinstance(activity, TutorialActivity):
            self.setactivity(_ba.newactivity(TransitionActivity))
        else:

            playerinfos: List[ba.PlayerInfo]

            # Generic team games.
            if isinstance(results, GameResults):
                playerinfos = results.playerinfos
                score = results.get_sessionteam_score(results.sessionteams[0])
                fail_message = None
                score_order = ('decreasing'
                               if results.lower_is_better else 'increasing')
                if results.scoretype in (ScoreType.SECONDS,
                                         ScoreType.MILLISECONDS):
                    scoretype = 'time'

                    # ScoreScreen wants hundredths of a second.
                    if score is not None:
                        if results.scoretype is ScoreType.SECONDS:
                            score *= 100
                        elif results.scoretype is ScoreType.MILLISECONDS:
                            score //= 10
                        else:
                            raise RuntimeError('FIXME')
                else:
                    if results.scoretype is not ScoreType.POINTS:
                        print(f'Unknown ScoreType:' f' "{results.scoretype}"')
                    scoretype = 'points'

            # Old coop-game-specific results; should migrate away from these.
            else:
                playerinfos = results.get('playerinfos')
                score = results['score'] if 'score' in results else None
                fail_message = (results['fail_message']
                                if 'fail_message' in results else None)
                score_order = (results['score_order']
                               if 'score_order' in results else 'increasing')
                activity_score_type = (activity.get_score_type() if isinstance(
                    activity, CoopGameActivity) else None)
                assert activity_score_type is not None
                scoretype = activity_score_type

            # Validate types.
            if playerinfos is not None:
                assert isinstance(playerinfos, list)
                assert (isinstance(i, PlayerInfo) for i in playerinfos)

            # Looks like we were in a round - check the outcome and
            # go from there.
            if outcome == 'restart':

                # This will pop up back in the same round.
                self.setactivity(_ba.newactivity(TransitionActivity))
            else:
                self.setactivity(
                    _ba.newactivity(
                        CoopScoreScreen, {
                            'playerinfos': playerinfos,
                            'score': score,
                            'fail_message': fail_message,
                            'score_order': score_order,
                            'score_type': scoretype,
                            'outcome': outcome,
                            'campaign': self.campaign,
                            'level': self.campaign_level_name
                        }))

        # No matter what, get the next 2 levels ready to go.
        self._update_on_deck_game_instances()
