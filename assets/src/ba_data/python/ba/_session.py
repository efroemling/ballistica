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
"""Defines base session class."""
from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import _ba
from ba._error import print_error, print_exception
from ba._lang import Lstr
from ba._player import Player

if TYPE_CHECKING:
    from typing import Sequence, List, Dict, Any, Optional, Set
    import ba


class Session:
    """Defines a high level series of activities with a common purpose.

    category: Gameplay Classes

    Examples of sessions are ba.FreeForAllSession, ba.DualTeamSession, and
    ba.CoopSession.

    A Session is responsible for wrangling and transitioning between various
    ba.Activity instances such as mini-games and score-screens, and for
    maintaining state between them (players, teams, score tallies, etc).

    Attributes:

        teams
            All the ba.Teams in the Session. Most things should use the team
            list in ba.Activity; not this.

        players
            All ba.Players in the Session. Most things should use the player
            list in ba.Activity; not this. Some players, such as those who have
            not yet selected a character, will only appear on this list.

        min_players
            The minimum number of Players who must be present for the Session
            to proceed past the initial joining screen.

        max_players
            The maximum number of Players allowed in the Session.

        lobby
            The ba.Lobby instance where new ba.Players go to select a
            Profile/Team/etc. before being added to games.
            Be aware this value may be None if a Session does not allow
            any such selection.

        campaign
            The ba.Campaign instance this Session represents, or None if
            there is no associated Campaign.

    """
    use_teams = False
    use_team_colors = True
    allow_mid_activity_joins = True

    # Note: even though these are instance vars, we annotate them at the
    # class level so that docs generation can access their types.
    campaign: Optional[ba.Campaign]
    lobby: ba.Lobby
    max_players: int
    min_players: int
    players: List[ba.SessionPlayer]
    teams: List[ba.SessionTeam]

    def __init__(self,
                 depsets: Sequence[ba.DependencySet],
                 team_names: Sequence[str] = None,
                 team_colors: Sequence[Sequence[float]] = None,
                 min_players: int = 1,
                 max_players: int = 8):
        """Instantiate a session.

        depsets should be a sequence of successfully resolved ba.DependencySet
        instances; one for each ba.Activity the session may potentially run.
        """
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from ba._lobby import Lobby
        from ba._stats import Stats
        from ba._gameutils import sharedobj
        from ba._gameactivity import GameActivity
        from ba._activity import Activity
        from ba._team import SessionTeam
        from ba._error import DependencyError
        from ba._dependency import Dependency, AssetPackage
        from efro.util import empty_weakref

        # First off, resolve all dependency-sets we were passed.
        # If things are missing, we'll try to gather them into a single
        # missing-deps exception if possible to give the caller a clean
        # path to download missing stuff and try again.
        missing_asset_packages: Set[str] = set()
        for depset in depsets:
            try:
                depset.resolve()
            except DependencyError as exc:
                # Gather/report missing assets only; barf on anything else.
                if all(issubclass(d.cls, AssetPackage) for d in exc.deps):
                    for dep in exc.deps:
                        assert isinstance(dep.config, str)
                        missing_asset_packages.add(dep.config)
                else:
                    missing_info = [(d.cls, d.config) for d in exc.deps]
                    raise RuntimeError(
                        f'Missing non-asset dependencies: {missing_info}')

        # Throw a combined exception if we found anything missing.
        if missing_asset_packages:
            raise DependencyError([
                Dependency(AssetPackage, set_id)
                for set_id in missing_asset_packages
            ])

        # Ok; looks like our dependencies check out.
        # Now give the engine a list of asset-set-ids to pass along to clients.
        required_asset_packages: Set[str] = set()
        for depset in depsets:
            required_asset_packages.update(depset.get_asset_package_ids())

        # print('Would set host-session asset-reqs to:',
        # required_asset_packages)

        # Stuff in this section should be removed from this class if possible.
        self._sessiondata = _ba.register_session(self)
        self.tournament_id: Optional[str] = None
        self.sharedobjs: Dict[str, Any] = {}
        self.have_shown_controls_help_overlay = False
        self.campaign = None
        self.campaign_state: Dict[str, str] = {}

        self.teams = []
        self.players = []
        self._in_set_activity = False
        self._next_team_id = 0
        self._activity_retained: Optional[ba.Activity] = None
        self._launch_end_session_activity_time: Optional[float] = None
        self._activity_end_timer: Optional[ba.Timer] = None
        self._activity_weak = empty_weakref(Activity)
        if self._activity_weak() is not None:
            raise Exception('Error creating empty activity weak ref.')

        self._next_activity: Optional[ba.Activity] = None
        self.wants_to_end = False
        self._ending = False
        self.min_players = min_players
        self.max_players = max_players

        # Create static teams if we're using them.
        if self.use_teams:
            assert team_names is not None
            assert team_colors is not None
            for i, color in enumerate(team_colors):
                team = SessionTeam(team_id=self._next_team_id,
                                   name=GameActivity.get_team_display_string(
                                       team_names[i]),
                                   color=color)
                self.teams.append(team)
                self._next_team_id += 1

                try:
                    with _ba.Context(self):
                        self.on_team_join(team)
                except Exception:
                    print_exception(f'Error in on_team_join for {self}.')

        self.lobby = Lobby()
        self.stats = Stats()

        # Instantiate our session globals node which will apply its settings.
        sharedobj('globals')

    def on_player_request(self, player: ba.SessionPlayer) -> bool:
        """Called when a new ba.Player wants to join the Session.

        This should return True or False to accept/reject.
        """

        # Limit player counts *unless* we're in a stress test.
        if _ba.app.stress_test_reset_timer is None:

            if len(self.players) >= self.max_players:

                # Print a rejection message *only* to the client trying to
                # join (prevents spamming everyone else in the game).
                _ba.playsound(_ba.getsound('error'))
                _ba.screenmessage(
                    Lstr(resource='playerLimitReachedText',
                         subs=[('${COUNT}', str(self.max_players))]),
                    color=(0.8, 0.0, 0.0),
                    clients=[player.get_input_device().client_id],
                    transient=True)
                return False

        _ba.playsound(_ba.getsound('dripity'))
        return True

    def on_player_leave(self, sessionplayer: ba.SessionPlayer) -> None:
        """Called when a previously-accepted ba.SessionPlayer leaves."""
        # pylint: disable=too-many-branches

        if sessionplayer not in self.players:
            print('ERROR: Session.on_player_leave called'
                  ' for player not in our list.')
            return

        _ba.playsound(_ba.getsound('playerLeft'))

        activity = self._activity_weak()

        if not sessionplayer.in_game:
            # Ok, the player's still in the lobby. Simply remove them from it.
            with _ba.Context(self):
                try:
                    self.lobby.remove_chooser(sessionplayer)
                except Exception:
                    print_exception('Error in Lobby.remove_chooser().')
        else:
            # Ok, they've already entered the game. Remove them from
            # teams/activities/etc.
            sessionteam = sessionplayer.team
            assert sessionteam is not None
            assert sessionplayer in sessionteam.players

            _ba.screenmessage(
                Lstr(resource='playerLeftText',
                     subs=[('${PLAYER}', sessionplayer.get_name(full=True))]))

            # Remove them from their SessionTeam.
            if sessionplayer in sessionteam.players:
                sessionteam.players.remove(sessionplayer)
            else:
                print('SessionPlayer not found in SessionTeam'
                      ' in on_player_leave.')

            # Grab their activity-specific player instance.
            player = sessionplayer.gameplayer
            assert isinstance(player, (Player, type(None)))

            # Remove them from any current Activity.
            if activity is not None:
                if player in activity.players:
                    activity.remove_player(sessionplayer)
                else:
                    print('Player not found in Activity in on_player_leave.')

            # If we're a non-team session, remove their team too.
            if not self.use_teams:

                # They should have been the only one on their team.
                assert not sessionteam.players

                # Remove their Team from the Activity.
                if activity is not None:
                    if sessionteam.gameteam in activity.teams:
                        activity.remove_team(sessionteam)
                    else:
                        print('Team not found in Activity in on_player_leave.')

                # And then from the Session.
                with _ba.Context(self):
                    if sessionteam in self.teams:
                        try:
                            self.teams.remove(sessionteam)
                            self.on_team_leave(sessionteam)
                        except Exception:
                            print_exception(
                                f'Error in on_team_leave for Session {self}.')
                    else:
                        print('Team no in Session teams in on_player_leave.')
                    try:
                        sessionteam.reset_sessiondata()
                    except Exception:
                        print_exception(
                            f'Error clearing sessiondata'
                            f' for team {sessionteam} in session {self}.')

        # Now remove them from the session list.
        self.players.remove(sessionplayer)

    def end(self) -> None:
        """Initiates an end to the session and a return to the main menu.

        Note that this happens asynchronously, allowing the
        session and its activities to shut down gracefully.
        """
        self.wants_to_end = True
        if self._next_activity is None:
            self.launch_end_session_activity()

    def launch_end_session_activity(self) -> None:
        """(internal)"""
        from ba._activitytypes import EndSessionActivity
        from ba._enums import TimeType
        with _ba.Context(self):
            curtime = _ba.time(TimeType.REAL)
            if self._ending:
                # Ignore repeats unless its been a while.
                assert self._launch_end_session_activity_time is not None
                since_last = (curtime - self._launch_end_session_activity_time)
                if since_last < 30.0:
                    return
                print_error(
                    'launch_end_session_activity called twice (since_last=' +
                    str(since_last) + ')')
            self._launch_end_session_activity_time = curtime
            self.set_activity(_ba.new_activity(EndSessionActivity))
            self.wants_to_end = False
            self._ending = True  # Prevent further actions.

    def on_team_join(self, team: ba.SessionTeam) -> None:
        """Called when a new ba.Team joins the session."""

    def on_team_leave(self, team: ba.SessionTeam) -> None:
        """Called when a ba.Team is leaving the session."""

    def _complete_end_activity(self, activity: ba.Activity,
                               results: Any) -> None:
        # Run the subclass callback in the session context.
        try:
            with _ba.Context(self):
                self.on_activity_end(activity, results)
        except Exception:
            print_exception('exception in on_activity_end() for session', self,
                            'activity', activity, 'with results', results)

    def end_activity(self, activity: ba.Activity, results: Any, delay: float,
                     force: bool) -> None:
        """Commence shutdown of a ba.Activity (if not already occurring).

        'delay' is the time delay before the Activity actually ends
        (in seconds). Further calls to end() will be ignored up until
        this time, unless 'force' is True, in which case the new results
        will replace the old.
        """
        from ba._general import Call
        from ba._enums import TimeType

        # Only pay attention if this is coming from our current activity.
        if activity is not self._activity_retained:
            return

        # If this activity hasn't begun yet, just set it up to end immediately
        # once it does.
        if not activity.has_begun():
            activity.set_immediate_end(results, delay, force)

        # The activity has already begun; get ready to end it.
        else:
            if (not activity.has_ended()) or force:
                activity.set_has_ended(True)

                # Set a timer to set in motion this activity's demise.
                self._activity_end_timer = _ba.Timer(
                    delay,
                    Call(self._complete_end_activity, activity, results),
                    timetype=TimeType.BASE)

    def handlemessage(self, msg: Any) -> Any:
        """General message handling; can be passed any message object."""
        from ba._lobby import PlayerReadyMessage
        from ba._messages import PlayerProfilesChangedMessage, UNHANDLED
        if isinstance(msg, PlayerReadyMessage):
            self._on_player_ready(msg.chooser)
            return None

        if isinstance(msg, PlayerProfilesChangedMessage):
            # If we have a current activity with a lobby, ask it to reload
            # profiles.
            with _ba.Context(self):
                self.lobby.reload_profiles()
            return None

        return UNHANDLED

    def set_activity(self, activity: ba.Activity) -> None:
        """Assign a new current ba.Activity for the session.

        Note that this will not change the current context to the new
        Activity's. Code must be run in the new activity's methods
        (on_transition_in, etc) to get it. (so you can't do
        session.set_activity(foo) and then ba.newnode() to add a node to foo)
        """
        from ba._gameutils import sharedobj
        from ba._enums import TimeType

        # Sanity test: make sure this doesn't get called recursively.
        if self._in_set_activity:
            raise RuntimeError(
                'Session.set_activity() cannot be called recursively.')
        self._in_set_activity = True

        if activity.session is not _ba.getsession():
            raise RuntimeError("Provided Activity's Session is not current.")

        # Quietly ignore this if the whole session is going down.
        if self._ending:
            return

        if activity is self._activity_retained:
            print_error('activity set to already-current activity')
            return

        if self._next_activity is not None:
            raise RuntimeError('Activity switch already in progress (to ' +
                               str(self._next_activity) + ')')

        prev_activity = self._activity_retained
        if prev_activity is not None:
            with _ba.Context(prev_activity):
                prev_globals = sharedobj('globals')
        else:
            prev_globals = None

        # Let the activity do its thing.
        activity.transition_in(prev_globals)

        self._next_activity = activity

        # If we have a current activity, tell it it's transitioning out;
        # the next one will become current once this one dies.
        if prev_activity is not None:
            prev_activity.transition_out()

            # Setting this to None should free up the old activity to die,
            # which will call begin_next_activity.
            # We can still access our old activity through
            # self._activity_weak() to keep it up to date on player
            # joins/departures/etc until it dies.
            self._activity_retained = None

        # There's no existing activity; lets just go ahead with the begin call.
        else:
            self.begin_next_activity()

        # We want to call destroy() for the previous activity once it should
        # tear itself down, clear out any self-refs, etc. After this call
        # the activity should have no refs left to it and should die (which
        # will trigger the next activity to run).
        if prev_activity is not None:
            with _ba.Context('ui'):
                _ba.timer(max(0.0, activity.transition_time),
                          prev_activity.destroy,
                          timetype=TimeType.REAL)
        self._in_set_activity = False

    def getactivity(self) -> Optional[ba.Activity]:
        """Return the current foreground activity for this session."""
        return self._activity_weak()

    def get_custom_menu_entries(self) -> List[Dict[str, Any]]:
        """Subclasses can override this to provide custom menu entries.

        The returned value should be a list of dicts, each containing
        a 'label' and 'call' entry, with 'label' being the text for
        the entry and 'call' being the callable to trigger if the entry
        is pressed.
        """
        return []

    def _request_player(self, sessionplayer: ba.SessionPlayer) -> bool:
        """Called by the C++ layer when players want to join."""

        # If we're ending, allow no new players.
        if self._ending:
            return False

        # Ask the session subclass to approve/deny this request.
        try:
            with _ba.Context(self):
                result = self.on_player_request(sessionplayer)
        except Exception:
            print_exception('error in on_player_request call for', self)
            result = False

        # If the user said yes, add the player to the session list.
        if result:
            self.players.append(sessionplayer)
            with _ba.Context(self):
                try:
                    self.lobby.add_chooser(sessionplayer)
                except Exception:
                    print_exception('exception in lobby.add_chooser()')

        return result

    def on_activity_end(self, activity: ba.Activity, results: Any) -> None:
        """Called when the current ba.Activity has ended.

        The ba.Session should look at the results and start
        another ba.Activity.
        """

    def begin_next_activity(self) -> None:
        """Called once the previous activity has been totally torn down.

        This means we're ready to begin the next one
        """
        if self._next_activity is not None:

            # We store both a weak and a strong ref to the new activity;
            # the strong is to keep it alive and the weak is so we can access
            # it even after we've released the strong-ref to allow it to die.
            self._activity_retained = self._next_activity
            self._activity_weak = weakref.ref(self._next_activity)
            self._next_activity = None

            # Kick out anyone loitering in the lobby.
            self.lobby.remove_all_choosers_and_kick_players()
            self._activity_retained.begin(self)

    def _on_player_ready(self, chooser: ba.Chooser) -> None:
        """Called when a ba.Player has checked themself ready."""
        lobby = chooser.lobby
        activity = self._activity_weak()

        # In joining activities, we wait till all choosers are ready
        # and then create all players at once.
        if activity is not None and activity.is_joining_activity:
            if lobby.check_all_ready():
                choosers = lobby.get_choosers()
                min_players = self.min_players
                if len(choosers) >= min_players:
                    for lch in lobby.get_choosers():
                        self._add_chosen_player(lch)
                    lobby.remove_all_choosers()

                    # Get our next activity going.
                    self._complete_end_activity(activity, {})
                else:
                    _ba.screenmessage(
                        Lstr(resource='notEnoughPlayersText',
                             subs=[('${COUNT}', str(min_players))]),
                        color=(1, 1, 0),
                    )
                    _ba.playsound(_ba.getsound('error'))
            else:
                return

        # Otherwise just add players on the fly.
        else:
            self._add_chosen_player(chooser)
            lobby.remove_chooser(chooser.getplayer())

    def _add_chosen_player(self, chooser: ba.Chooser) -> ba.SessionPlayer:
        from ba._team import SessionTeam
        sessionplayer = chooser.getplayer()
        assert sessionplayer in self.players, (
            'SessionPlayer not found in session '
            'player-list after chooser selection.')

        activity = self._activity_weak()
        assert activity is not None

        # Reset the player's input here, as it is probably
        # referencing the chooser which could inadvertently keep it alive.
        sessionplayer.reset_input()

        # Pass it to the current activity if it has already begun
        # (otherwise it'll get passed once begin is called).
        pass_to_activity = (activity.has_begun()
                            and not activity.is_joining_activity)

        # If we're not allowing mid-game joins, don't pass; just announce
        # the arrival and say they'll partake next round.
        if pass_to_activity:
            if not self.allow_mid_activity_joins:
                pass_to_activity = False
                with _ba.Context(self):
                    _ba.screenmessage(
                        Lstr(resource='playerDelayedJoinText',
                             subs=[('${PLAYER}',
                                    sessionplayer.get_name(full=True))]),
                        color=(0, 1, 0),
                    )

        # If we're a non-team session, each player gets their own team.
        # (keeps mini-game coding simpler if we can always deal with teams).
        if self.use_teams:
            sessionteam = chooser.get_team()
        else:
            our_team_id = self._next_team_id
            self._next_team_id += 1
            sessionteam = SessionTeam(
                team_id=our_team_id,
                color=chooser.get_color(),
                name=chooser.getplayer().get_name(full=True, icon=False),
            )

            # Add player's team to the Session.
            self.teams.append(sessionteam)
            try:
                with _ba.Context(self):
                    self.on_team_join(sessionteam)
            except Exception:
                print_exception(f'exception in on_team_join for {self}')

            # Add player's team to the Activity.
            if pass_to_activity:
                activity.add_team(sessionteam)

        assert sessionplayer not in sessionteam.players
        sessionteam.players.append(sessionplayer)
        sessionplayer.set_data(team=sessionteam,
                               character=chooser.get_character_name(),
                               color=chooser.get_color(),
                               highlight=chooser.get_highlight())

        self.stats.register_player(sessionplayer)
        if pass_to_activity:
            activity.add_player(sessionplayer)
        return sessionplayer
