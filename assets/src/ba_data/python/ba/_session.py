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

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import Sequence, List, Dict, Any, Optional, Set

    import ba


class Session:
    """Defines a high level series of activities with a common purpose.

    category: Gameplay Classes

    Examples of sessions are ba.FreeForAllSession, ba.TeamsSession, and
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

    # Annotate our attrs at class level so they're available for introspection.
    teams: List[ba.Team]
    campaign: Optional[ba.Campaign]
    lobby: ba.Lobby
    min_players: int
    max_players: int
    players: List[ba.Player]

    def __init__(self,
                 depsets: Sequence[ba.DependencySet],
                 team_names: Sequence[str] = None,
                 team_colors: Sequence[Sequence[float]] = None,
                 use_team_colors: bool = True,
                 min_players: int = 1,
                 max_players: int = 8,
                 allow_mid_activity_joins: bool = True):
        """Instantiate a session.

        depsets should be a sequence of successfully resolved ba.DependencySet
        instances; one for each ba.Activity the session may potentially run.
        """
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from ba._lobby import Lobby
        from ba._stats import Stats
        from ba._gameutils import sharedobj
        from ba._gameactivity import GameActivity
        from ba._team import Team
        from ba._error import DependencyError
        from ba._dependency import Dependency, AssetPackage

        # print(' WOULD LOOK AT DEP SETS', depsets)

        # first off, resolve all dep-sets we were passed.
        # if things are missing, we'll try to gather them into
        # a single missing-deps exception if possible
        # to give the caller a clean path to download missing
        # stuff and try again.
        missing_asset_packages: Set[str] = set()
        for depset in depsets:
            try:
                depset.resolve()
            except DependencyError as exc:
                # we gather/report missing assets only; barf on anything else
                if all(issubclass(d.cls, AssetPackage) for d in exc.deps):
                    for dep in exc.deps:
                        assert isinstance(dep.config, str)
                        missing_asset_packages.add(dep.config)
                else:
                    missing_info = [(d.cls, d.config) for d in exc.deps]
                    raise Exception(
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

        if team_names is None:
            team_names = ['Good Guys']
        if team_colors is None:
            team_colors = [(0.6, 0.2, 1.0)]

        # First thing, wire up our internal engine data.
        self._sessiondata = _ba.register_session(self)

        self.tournament_id: Optional[str] = None

        # FIXME: This stuff shouldn't be here.
        self.sharedobjs: Dict[str, Any] = {}

        # TeamGameActivity uses this to display a help overlay on
        # the first activity only.
        self.have_shown_controls_help_overlay = False

        self.campaign = None

        # FIXME: Should be able to kill this I think.
        self.campaign_state: Dict[str, str] = {}

        self._use_teams = (team_names is not None)
        self._use_team_colors = use_team_colors
        self._in_set_activity = False
        self._allow_mid_activity_joins = allow_mid_activity_joins

        self.teams = []
        self.players = []
        self._next_team_id = 0
        self._activity_retained: Optional[ba.Activity] = None
        self.launch_end_session_activity_time: Optional[float] = None
        self._activity_end_timer: Optional[ba.Timer] = None

        # Hacky way to create empty weak ref; must be a better way.
        class _EmptyObj:
            pass

        self._activity_weak: ReferenceType[ba.Activity]
        self._activity_weak = weakref.ref(_EmptyObj())  # type: ignore

        if self._activity_weak() is not None:
            raise Exception("error creating empty weak ref")

        self._next_activity: Optional[ba.Activity] = None
        self.wants_to_end = False
        self._ending = False
        self.min_players = min_players
        self.max_players = max_players

        if self._use_teams:
            for i, color in enumerate(team_colors):
                team = Team(team_id=self._next_team_id,
                            name=GameActivity.get_team_display_string(
                                team_names[i]),
                            color=color)
                self.teams.append(team)
                self._next_team_id += 1

                try:
                    with _ba.Context(self):
                        self.on_team_join(team)
                except Exception:
                    from ba import _error
                    _error.print_exception('exception in on_team_join for',
                                           self)

        self.lobby = Lobby()
        self.stats = Stats()

        # Instantiate our session globals node
        # (so it can apply default settings).
        sharedobj('globals')

    @property
    def use_teams(self) -> bool:
        """(internal)"""
        return self._use_teams

    @property
    def use_team_colors(self) -> bool:
        """(internal)"""
        return self._use_team_colors

    def on_player_request(self, player: ba.Player) -> bool:
        """Called when a new ba.Player wants to join the Session.

        This should return True or False to accept/reject.
        """
        from ba._lang import Lstr

        # Limit player counts *unless* we're in a stress test.
        if _ba.app.stress_test_reset_timer is None:

            if len(self.players) >= self.max_players:

                # Print a rejection message *only* to the client trying to join
                # (prevents spamming everyone else in the game).
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

    def on_player_leave(self, player: ba.Player) -> None:
        """Called when a previously-accepted ba.Player leaves the session."""
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=cyclic-import
        from ba._freeforallsession import FreeForAllSession
        from ba._lang import Lstr
        from ba import _error

        # Remove them from the game rosters.
        if player in self.players:

            _ba.playsound(_ba.getsound('playerLeft'))

            team: Optional[ba.Team]

            # The player will have no team if they are still in the lobby.
            try:
                team = player.team
            except _error.TeamNotFoundError:
                team = None

            activity = self._activity_weak()

            # If he had no team, he's in the lobby.
            # If we have a current activity with a lobby, ask them to
            # remove him.
            if team is None:
                with _ba.Context(self):
                    try:
                        self.lobby.remove_chooser(player)
                    except Exception:
                        _error.print_exception(
                            'Error in Lobby.remove_chooser()')

            # *if* he was actually in the game, announce his departure
            if team is not None:
                _ba.screenmessage(
                    Lstr(resource='playerLeftText',
                         subs=[('${PLAYER}', player.get_name(full=True))]))

            # Remove him from his team and session lists.
            # (he may not be on the team list since player are re-added to
            # team lists every activity)
            if team is not None and player in team.players:

                # Testing.. can remove this eventually.
                if isinstance(self, FreeForAllSession):
                    if len(team.players) != 1:
                        _error.print_error("expected 1 player in FFA team")
                team.players.remove(player)

            # Remove player from any current activity.
            if activity is not None and player in activity.players:
                activity.players.remove(player)

                # Run the activity callback unless its been expired.
                if not activity.is_expired():
                    try:
                        with _ba.Context(activity):
                            activity.on_player_leave(player)
                    except Exception:
                        _error.print_exception(
                            'exception in on_player_leave for activity',
                            activity)
                else:
                    _error.print_error("expired activity in on_player_leave;"
                                       " shouldn't happen")

                player.set_activity(None)
                player.set_node(None)

                # reset the player - this will remove its actor-ref and clear
                # its calls/etc
                try:
                    with _ba.Context(activity):
                        player.reset()
                except Exception:
                    _error.print_exception(
                        'exception in player.reset in'
                        ' on_player_leave for player', player)

            # If we're a non-team session, remove the player's team completely.
            if not self._use_teams and team is not None:

                # If the team's in an activity, call its on_team_leave
                # callback.
                if activity is not None and team in activity.teams:
                    activity.teams.remove(team)

                    if not activity.is_expired():
                        try:
                            with _ba.Context(activity):
                                activity.on_team_leave(team)
                        except Exception:
                            _error.print_exception(
                                'exception in on_team_leave for activity',
                                activity)
                    else:
                        _error.print_error(
                            "expired activity in on_player_leave p2"
                            "; shouldn't happen")

                    # Clear the team's game-data (so dying stuff will
                    # have proper context).
                    try:
                        with _ba.Context(activity):
                            team.reset_gamedata()
                    except Exception:
                        _error.print_exception(
                            'exception clearing gamedata for team:', team,
                            'for player:', player, 'in activity:', activity)

                # Remove the team from the session.
                self.teams.remove(team)
                try:
                    with _ba.Context(self):
                        self.on_team_leave(team)
                except Exception:
                    _error.print_exception(
                        'exception in on_team_leave for session', self)
                # Clear the team's session-data (so dying stuff will
                # have proper context).
                try:
                    with _ba.Context(self):
                        team.reset_sessiondata()
                except Exception:
                    _error.print_exception(
                        'exception clearing sessiondata for team:', team,
                        'in session:', self)

            # Now remove them from the session list.
            self.players.remove(player)

        else:
            print('ERROR: Session.on_player_leave called'
                  ' for player not in our list.')

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
        from ba import _error
        from ba._activitytypes import EndSessionActivity
        from ba._enums import TimeType
        with _ba.Context(self):
            curtime = _ba.time(TimeType.REAL)
            if self._ending:
                # Ignore repeats unless its been a while.
                assert self.launch_end_session_activity_time is not None
                since_last = (curtime - self.launch_end_session_activity_time)
                if since_last < 30.0:
                    return
                _error.print_error(
                    "launch_end_session_activity called twice (since_last=" +
                    str(since_last) + ")")
            self.launch_end_session_activity_time = curtime
            self.set_activity(_ba.new_activity(EndSessionActivity))
            self.wants_to_end = False
            self._ending = True  # Prevent further activity-mucking.

    def on_team_join(self, team: ba.Team) -> None:
        """Called when a new ba.Team joins the session."""

    def on_team_leave(self, team: ba.Team) -> None:
        """Called when a ba.Team is leaving the session."""

    def _complete_end_activity(self, activity: ba.Activity,
                               results: Any) -> None:
        # Run the subclass callback in the session context.
        try:
            with _ba.Context(self):
                self.on_activity_end(activity, results)
        except Exception:
            from ba import _error
            _error.print_exception(
                'exception in on_activity_end() for session', self, 'activity',
                activity, 'with results', results)

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
        # only pay attention if this is coming from our current activity..
        if activity is not self._activity_retained:
            return

        # if this activity hasn't begun yet, just set it up to end immediately
        # once it does
        if not activity.has_begun():
            activity.set_immediate_end(results, delay, force)

        # the activity has already begun; get ready to end it..
        else:
            if (not activity.has_ended()) or force:
                activity.set_has_ended(True)
                # set a timer to set in motion this activity's demise
                self._activity_end_timer = _ba.Timer(
                    delay,
                    Call(self._complete_end_activity, activity, results),
                    timetype=TimeType.BASE)

    def handlemessage(self, msg: Any) -> Any:
        """General message handling; can be passed any message object."""
        from ba._lobby import PlayerReadyMessage
        from ba._error import UNHANDLED
        from ba._messages import PlayerProfilesChangedMessage
        if isinstance(msg, PlayerReadyMessage):
            self._on_player_ready(msg.chooser)
            return None

        if isinstance(msg, PlayerProfilesChangedMessage):
            # if we have a current activity with a lobby, ask it to
            # reload profiles
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
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        from ba import _error
        from ba._gameutils import sharedobj
        from ba._enums import TimeType

        # Sanity test: make sure this doesn't get called recursively.
        if self._in_set_activity:
            raise Exception(
                "Session.set_activity() cannot be called recursively.")

        if activity.session is not _ba.getsession():
            raise Exception("provided activity's session is not current")

        # Quietly ignore this if the whole session is going down.
        if self._ending:
            return

        if activity is self._activity_retained:
            _error.print_error("activity set to already-current activity")
            return

        if self._next_activity is not None:
            raise Exception("Activity switch already in progress (to " +
                            str(self._next_activity) + ")")

        self._in_set_activity = True

        prev_activity = self._activity_retained

        if prev_activity is not None:
            with _ba.Context(prev_activity):
                gprev = sharedobj('globals')
        else:
            gprev = None

        with _ba.Context(activity):

            # Now that it's going to be front and center,
            # set some global values based on what the activity wants.
            glb = sharedobj('globals')
            glb.use_fixed_vr_overlay = activity.use_fixed_vr_overlay
            glb.allow_kick_idle_players = activity.allow_kick_idle_players
            if activity.inherits_slow_motion and gprev is not None:
                glb.slow_motion = gprev.slow_motion
            else:
                glb.slow_motion = activity.slow_motion
            if activity.inherits_music and gprev is not None:
                glb.music_continuous = True  # Prevent restarting same music.
                glb.music = gprev.music
                glb.music_count += 1
            if activity.inherits_camera_vr_offset and gprev is not None:
                glb.vr_camera_offset = gprev.vr_camera_offset
            if activity.inherits_vr_overlay_center and gprev is not None:
                glb.vr_overlay_center = gprev.vr_overlay_center
                glb.vr_overlay_center_enabled = gprev.vr_overlay_center_enabled

            # If they want to inherit tint from the previous activity.
            if activity.inherits_tint and gprev is not None:
                glb.tint = gprev.tint
                glb.vignette_outer = gprev.vignette_outer
                glb.vignette_inner = gprev.vignette_inner

            # Let the activity do its thing.
            activity.start_transition_in()

        self._next_activity = activity

        # If we have a current activity, tell it it's transitioning out;
        # the next one will become current once this one dies.
        if prev_activity is not None:
            # pylint: disable=protected-access
            prev_activity._transitioning_out = True
            # pylint: enable=protected-access

            # activity will be None until the next one begins.
            with _ba.Context(prev_activity):
                prev_activity.on_transition_out()

            # Setting this to None should free up the old activity to die,
            # which will call begin_next_activity.
            # We can still access our old activity through
            # self._activity_weak() to keep it up to date on player
            # joins/departures/etc until it dies.
            self._activity_retained = None

        # There's no existing activity; lets just go ahead with the begin call.
        else:
            self.begin_next_activity()

        # Tell the C layer that this new activity is now 'foregrounded'.
        # This means that its globals node controls global stuff and stuff
        # like console operations, keyboard shortcuts, etc will run in it.
        # pylint: disable=protected-access
        # noinspection PyProtectedMember
        activity._activity_data.make_foreground()
        # pylint: enable=protected-access

        # We want to call _destroy() for the previous activity once it should
        # tear itself down, clear out any self-refs, etc.  If the new activity
        # has a transition-time, set it up to be called after that passes;
        # otherwise call it immediately. After this call the activity should
        # have no refs left to it and should die (which will trigger the next
        # activity to run).
        if prev_activity is not None:
            if activity.transition_time > 0.0:
                # FIXME: We should tweak the activity to not allow
                #  node-creation/etc when we call _destroy (or after).
                with _ba.Context('ui'):
                    # pylint: disable=protected-access
                    # noinspection PyProtectedMember
                    _ba.timer(activity.transition_time,
                              prev_activity._destroy,
                              timetype=TimeType.REAL)
            # Just run immediately.
            else:
                # noinspection PyProtectedMember
                prev_activity._destroy()  # pylint: disable=protected-access
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

    def _request_player(self, player: ba.Player) -> bool:

        # If we're ending, allow no new players.
        if self._ending:
            return False

        # Ask the user.
        try:
            with _ba.Context(self):
                result = self.on_player_request(player)
        except Exception:
            from ba import _error
            _error.print_exception('error in on_player_request call for', self)
            result = False

        # If the user said yes, add the player to the session list.
        if result:
            self.players.append(player)

            # If we have a current activity with a lobby,
            # ask it to bring up a chooser for this player.
            # otherwise they'll have to wait around for the next activity.
            with _ba.Context(self):
                try:
                    self.lobby.add_chooser(player)
                except Exception:
                    from ba import _error
                    _error.print_exception('exception in lobby.add_chooser()')

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

            # Lets kick out any players sitting in the lobby since
            # new activities such as score screens could cover them up;
            # better to have them rejoin.
            self.lobby.remove_all_choosers_and_kick_players()
            activity = self._activity_weak()
            assert activity is not None
            activity.begin(self)

    def _on_player_ready(self, chooser: ba.Chooser) -> None:
        """Called when a ba.Player has checked themself ready."""
        from ba._lang import Lstr
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
                    _ba.screenmessage(Lstr(resource='notEnoughPlayersText',
                                           subs=[('${COUNT}', str(min_players))
                                                 ]),
                                      color=(1, 1, 0))
                    _ba.playsound(_ba.getsound('error'))
            else:
                return
        # Otherwise just add players on the fly.
        else:
            self._add_chosen_player(chooser)
            lobby.remove_chooser(chooser.getplayer())

    def _add_chosen_player(self, chooser: ba.Chooser) -> ba.Player:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        from ba import _error
        from ba._lang import Lstr
        from ba._team import Team
        from ba import _freeforallsession
        player = chooser.getplayer()
        if player not in self.players:
            _error.print_error('player not found in session '
                               'player-list after chooser selection')

        activity = self._activity_weak()
        assert activity is not None

        # We need to reset the player's input here, as it is currently
        # referencing the chooser which could inadvertently keep it alive.
        player.reset_input()

        # Pass it to the current activity if it has already begun
        # (otherwise it'll get passed once begin is called).
        pass_to_activity = (activity is not None and activity.has_begun()
                            and not activity.is_joining_activity)

        # If we're not allowing mid-game joins, don't pass; just announce
        # the arrival.
        if pass_to_activity:
            if not self._allow_mid_activity_joins:
                pass_to_activity = False
                with _ba.Context(self):
                    _ba.screenmessage(Lstr(resource='playerDelayedJoinText',
                                           subs=[('${PLAYER}',
                                                  player.get_name(full=True))
                                                 ]),
                                      color=(0, 1, 0))

        # If we're a non-team game, each player gets their own team
        # (keeps mini-game coding simpler if we can always deal with teams).
        if self._use_teams:
            team = chooser.get_team()
        else:
            our_team_id = self._next_team_id
            team = Team(team_id=our_team_id,
                        name=chooser.getplayer().get_name(full=True,
                                                          icon=False),
                        color=chooser.get_color())
            self.teams.append(team)
            self._next_team_id += 1
            try:
                with _ba.Context(self):
                    self.on_team_join(team)
            except Exception:
                _error.print_exception(f'exception in on_team_join for {self}')

            if pass_to_activity:
                if team in activity.teams:
                    _error.print_error(
                        "Duplicate team ID in ba.Session._add_chosen_player")
                activity.teams.append(team)
                try:
                    with _ba.Context(activity):
                        activity.on_team_join(team)
                except Exception:
                    _error.print_exception(
                        f'ERROR: exception in on_team_join for {activity}')

        player.set_data(team=team,
                        character=chooser.get_character_name(),
                        color=chooser.get_color(),
                        highlight=chooser.get_highlight())

        self.stats.register_player(player)
        if pass_to_activity:
            if isinstance(self, _freeforallsession.FreeForAllSession):
                if player.team.players:
                    _error.print_error("expected 0 players in FFA team")

            # Don't actually add the player to their team list if we're not
            # in an activity. (players get (re)added to their team lists
            # when the activity begins).
            player.team.players.append(player)
            if player in activity.players:
                _error.print_exception(
                    f'Dup player in ba.Session._add_chosen_player: {player}')
            else:
                activity.players.append(player)
                player.set_activity(activity)
                pnode = activity.create_player_node(player)
                player.set_node(pnode)
                try:
                    with _ba.Context(activity):
                        activity.on_player_join(player)
                except Exception:
                    _error.print_exception(
                        f'Error on on_player_join for {activity}')
        return player
