# Released under the MIT License. See LICENSE for details.
#
"""Defines base session class."""
from __future__ import annotations

import math
import weakref
import logging
from typing import TYPE_CHECKING

import babase

import _bascenev1
from bascenev1._player import Player

if TYPE_CHECKING:
    from typing import Sequence, Any

    import bascenev1

# How many seconds someone who left the session (but not the party) must
# wait to rejoin the session again. Intended to prevent game exploits
# such as skipping respawn waits.
_g_player_rejoin_cooldown: float = 0.0

# overrides the session's decision of max_players
_max_players_override: int | None = None


def set_player_rejoin_cooldown(cooldown: float) -> None:
    """Set the cooldown for individual players rejoining after leaving."""
    global _g_player_rejoin_cooldown  # pylint: disable=global-statement
    _g_player_rejoin_cooldown = max(0.0, cooldown)


def set_max_players_override(max_players: int | None) -> None:
    """Set the override for how many players can join a session"""
    global _max_players_override  # pylint: disable=global-statement
    _max_players_override = max_players


class Session:
    """Wrangles a series of :class:`~bascenev1.Activity` instances.

    Examples of sessions are :class:`bascenev1.FreeForAllSession`,
    :class:`bascenev1.DualTeamSession`, and
    :class:`bascenev1.CoopSession`.

    A session is responsible for wrangling and transitioning between
    various activity instances such as mini-games and score-screens, and
    for maintaining state between them (players, teams, score tallies,
    etc).
    """

    #: Whether this session groups players into an explicit set of teams.
    #: If this is off, a unique team is generated for each player that
    #: joins.
    use_teams: bool = False

    #: Whether players on a team should all adopt the colors of that team
    #: instead of their own profile colors. This only applies if
    #: :attr:`use_teams` is enabled.
    use_team_colors: bool = True

    # Note: even though these are instance vars, we annotate and
    # document them at the class level so that looks better and nobody
    # get lost while reading large __init__

    #: The lobby instance where new players go to select a
    #: profile/team/etc. before being added to games. Be aware this value
    #: may be None if a session does not allow any such selection.
    lobby: bascenev1.Lobby

    #: The maximum number of players allowed in the Session.
    max_players: int

    #: The minimum number of players who must be present for the Session
    #: to proceed past the initial joining screen
    min_players: int

    #: All players in the session. Note that most things should use the
    #: list of :class:`~bascenev1.Player` instances found in the
    #: :class:`~bascenev1.Activity`; not this. Some players, such as
    #: those who have not yet selected a character, will only be found on
    #: this list.
    sessionplayers: list[bascenev1.SessionPlayer]

    #: A shared dictionary for objects to use as storage on this session.
    #: Ensure that keys here are unique to avoid collisions.
    customdata: dict

    #: All the teams in the session. Most things will operate on the list
    #: of :class:`~bascenev1.Team` instances found in an
    #: :class:`~bascenev1.Activity`; not this.
    sessionteams: list[bascenev1.SessionTeam]

    def __init__(
        self,
        depsets: Sequence[bascenev1.DependencySet],
        *,
        team_names: Sequence[str] | None = None,
        team_colors: Sequence[Sequence[float]] | None = None,
        min_players: int = 1,
        max_players: int = 8,
        submit_score: bool = True,
    ):
        """Instantiate a session.

        depsets should be a sequence of successfully resolved
        bascenev1.DependencySet instances; one for each bascenev1.Activity
        the session may potentially run.
        """
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        # pylint: disable=too-many-branches
        from efro.util import empty_weakref
        from bascenev1._dependency import (
            Dependency,
            AssetPackage,
            DependencyError,
        )
        from bascenev1._lobby import Lobby
        from bascenev1._stats import Stats
        from bascenev1._gameactivity import GameActivity
        from bascenev1._activity import Activity
        from bascenev1._team import SessionTeam

        # First off, resolve all dependency-sets we were passed.
        # If things are missing, we'll try to gather them into a single
        # missing-deps exception if possible to give the caller a clean
        # path to download missing stuff and try again.
        missing_asset_packages: set[str] = set()
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
                        f'Missing non-asset dependencies: {missing_info}'
                    ) from exc

        # Throw a combined exception if we found anything missing.
        if missing_asset_packages:
            raise DependencyError(
                [
                    Dependency(AssetPackage, set_id)
                    for set_id in missing_asset_packages
                ]
            )

        # Ok; looks like our dependencies check out.
        # Now give the engine a list of asset-set-ids to pass along to clients.
        required_asset_packages: set[str] = set()
        for depset in depsets:
            required_asset_packages.update(depset.get_asset_package_ids())

        # print('Would set host-session asset-reqs to:',
        # required_asset_packages)

        # Init our C++ layer data.
        self._sessiondata = _bascenev1.register_session(self)

        # Should remove this if possible.
        self.tournament_id: str | None = None

        self.sessionteams = []
        self.sessionplayers = []
        self.min_players = min_players
        self.max_players = (
            max_players
            if _max_players_override is None
            else _max_players_override
        )
        self.submit_score = submit_score

        self.customdata = {}
        self._in_set_activity = False
        self._next_team_id = 0
        self._activity_retained: bascenev1.Activity | None = None
        self._launch_end_session_activity_time: float | None = None
        self._activity_end_timer: bascenev1.BaseTimer | None = None
        self._activity_weak = empty_weakref(Activity)
        self._next_activity: bascenev1.Activity | None = None
        self._wants_to_end = False
        self._ending = False
        self._activity_should_end_immediately = False
        self._activity_should_end_immediately_results: (
            bascenev1.GameResults | None
        ) = None
        self._activity_should_end_immediately_delay = 0.0

        # Create static teams if we're using them.
        if self.use_teams:
            if team_names is None:
                raise RuntimeError(
                    'use_teams is True but team_names not provided.'
                )
            if team_colors is None:
                raise RuntimeError(
                    'use_teams is True but team_colors not provided.'
                )
            if len(team_colors) != len(team_names):
                raise RuntimeError(
                    f'Got {len(team_names)} team_names'
                    f' and {len(team_colors)} team_colors;'
                    f' these numbers must match.'
                )
            for i, color in enumerate(team_colors):
                team = SessionTeam(
                    team_id=self._next_team_id,
                    name=GameActivity.get_team_display_string(team_names[i]),
                    color=color,
                )
                self.sessionteams.append(team)
                self._next_team_id += 1
                try:
                    with self.context:
                        self.on_team_join(team)
                except Exception:
                    logging.exception('Error in on_team_join for %s.', self)

        self.lobby = Lobby()
        self.stats = Stats()

        # Instantiate our session globals node which will apply its settings.
        self._sessionglobalsnode = _bascenev1.newnode('sessionglobals')

        # Rejoin cooldown stuff.
        self._players_on_wait: dict = {}
        self._player_requested_identifiers: dict = {}
        self._waitlist_timers: dict = {}

    @property
    def context(self) -> bascenev1.ContextRef:
        """A context-ref pointing at this activity."""
        return self._sessiondata.context()

    @property
    def sessionglobalsnode(self) -> bascenev1.Node:
        """The sessionglobals node for the session."""
        node = self._sessionglobalsnode
        if not node:
            raise babase.NodeNotFoundError()
        return node

    def should_allow_mid_activity_joins(
        self, activity: bascenev1.Activity
    ) -> bool:
        """Ask ourself if we should allow joins during an Activity.

        Note that for a join to be allowed, both the session and
        activity have to be ok with it (via this function and the
        :attr:`bascenev1.Activity.allow_mid_activity_joins` property.
        """
        del activity  # Unused.
        return True

    def on_player_request(self, player: bascenev1.SessionPlayer) -> bool:
        """Called when a new player wants to join the session.

        This should return True or False to accept/reject.
        """
        # Limit player counts *unless* we're in a stress test.
        if (
            babase.app.classic is not None
            and babase.app.classic.stress_test_update_timer is None
        ):
            if len(self.sessionplayers) >= self.max_players >= 0:
                # Print a rejection message *only* to the client trying to
                # join (prevents spamming everyone else in the game).
                _bascenev1.getsound('error').play()
                _bascenev1.broadcastmessage(
                    babase.Lstr(
                        resource='playerLimitReachedText',
                        subs=[('${COUNT}', str(self.max_players))],
                    ),
                    color=(0.8, 0.0, 0.0),
                    clients=[player.inputdevice.client_id],
                    transient=True,
                )
                return False

        # Rejoin cooldown.
        identifier = player.get_v1_account_id()
        if identifier:
            leave_time = self._players_on_wait.get(identifier)
            if leave_time:
                diff = str(
                    math.ceil(
                        _g_player_rejoin_cooldown
                        - babase.apptime()
                        + leave_time
                    )
                )
                _bascenev1.broadcastmessage(
                    babase.Lstr(
                        translate=(
                            'serverResponses',
                            'You can join in ${COUNT} seconds.',
                        ),
                        subs=[('${COUNT}', diff)],
                    ),
                    color=(1, 1, 0),
                    clients=[player.inputdevice.client_id],
                    transient=True,
                )
                return False
            self._player_requested_identifiers[player.id] = identifier

        _bascenev1.getsound('dripity').play()
        return True

    def on_player_leave(self, sessionplayer: bascenev1.SessionPlayer) -> None:
        """Called when a previously-accepted bascenev1.SessionPlayer leaves."""

        if sessionplayer not in self.sessionplayers:
            print(
                'ERROR: Session.on_player_leave called'
                ' for player not in our list.'
            )
            return

        _bascenev1.getsound('playerLeft').play()

        activity = self._activity_weak()

        # Rejoin cooldown.
        identifier = self._player_requested_identifiers.get(sessionplayer.id)
        if identifier:
            self._players_on_wait[identifier] = babase.apptime()
            with babase.ContextRef.empty():
                self._waitlist_timers[identifier] = babase.AppTimer(
                    _g_player_rejoin_cooldown,
                    babase.Call(self._remove_player_from_waitlist, identifier),
                )

        if not sessionplayer.in_game:
            # Ok, the player is still in the lobby; simply remove them.
            with self.context:
                try:
                    self.lobby.remove_chooser(sessionplayer)
                except Exception:
                    logging.exception('Error in Lobby.remove_chooser().')
        else:
            # Ok, they've already entered the game. Remove them from
            # teams/activities/etc.
            sessionteam = sessionplayer.sessionteam
            assert sessionteam is not None

            _bascenev1.broadcastmessage(
                babase.Lstr(
                    resource='playerLeftText',
                    subs=[('${PLAYER}', sessionplayer.getname(full=True))],
                )
            )

            # Remove them from their SessionTeam.
            if sessionplayer in sessionteam.players:
                sessionteam.players.remove(sessionplayer)
            else:
                print(
                    'SessionPlayer not found in SessionTeam'
                    ' in on_player_leave.'
                )

            # Grab their activity-specific player instance.
            player = sessionplayer.activityplayer
            assert isinstance(player, (Player, type(None)))

            # Remove them from any current Activity.
            if player is not None and activity is not None:
                if player in activity.players:
                    activity.remove_player(sessionplayer)
                else:
                    print('Player not found in Activity in on_player_leave.')

            # If we're a non-team session, remove their team too.
            if not self.use_teams:
                self._remove_player_team(sessionteam, activity)

        # Now remove them from the session list.
        self.sessionplayers.remove(sessionplayer)

    def _remove_player_team(
        self,
        sessionteam: bascenev1.SessionTeam,
        activity: bascenev1.Activity | None,
    ) -> None:
        """Remove the player-specific team in non-teams mode."""

        # They should have been the only one on their team.
        assert not sessionteam.players

        # Remove their Team from the Activity.
        if activity is not None:
            if sessionteam.activityteam in activity.teams:
                activity.remove_team(sessionteam)
            else:
                print('Team not found in Activity in on_player_leave.')

        # And then from the Session.
        with self.context:
            if sessionteam in self.sessionteams:
                try:
                    self.sessionteams.remove(sessionteam)
                    self.on_team_leave(sessionteam)
                except Exception:
                    logging.exception(
                        'Error in on_team_leave for Session %s.', self
                    )
            else:
                print('Team no in Session teams in on_player_leave.')
            try:
                sessionteam.leave()
            except Exception:
                logging.exception(
                    'Error clearing sessiondata for team %s in session %s.',
                    sessionteam,
                    self,
                )

    def end(self) -> None:
        """Initiate an end to the session and a return to the main menu.

        Note that this happens asynchronously, allowing the session and
        its activities to shut down gracefully.
        """
        self._wants_to_end = True
        if self._next_activity is None:
            self._launch_end_session_activity()

    def _launch_end_session_activity(self) -> None:
        """(internal)"""
        from bascenev1._activitytypes import EndSessionActivity

        with self.context:
            curtime = babase.apptime()
            if self._ending:
                # Ignore repeats unless its been a while.
                assert self._launch_end_session_activity_time is not None
                since_last = curtime - self._launch_end_session_activity_time
                if since_last < 30.0:
                    return
                logging.error(
                    '_launch_end_session_activity called twice (since_last=%s)',
                    since_last,
                )
            self._launch_end_session_activity_time = curtime
            self.setactivity(_bascenev1.newactivity(EndSessionActivity))
            self._wants_to_end = False
            self._ending = True  # Prevent further actions.

    def on_team_join(self, team: bascenev1.SessionTeam) -> None:
        """Called when a new team joins the session."""

    def on_team_leave(self, team: bascenev1.SessionTeam) -> None:
        """Called when a team is leaving the session."""

    def end_activity(
        self,
        activity: bascenev1.Activity,
        results: Any,
        delay: float,
        force: bool,
    ) -> None:
        """Commence shutdown of an activity (if not already occurring).

        'delay' is the time delay before the activity actually ends (in
        seconds). Further calls to end the activity will be ignored up
        until this time, unless 'force' is True, in which case the new
        results will replace the old.
        """
        # Only pay attention if this is coming from our current activity.
        if activity is not self._activity_retained:
            return

        # If this activity hasn't begun yet, just set it up to end immediately
        # once it does.
        if not activity.has_begun():
            # activity.set_immediate_end(results, delay, force)
            if not self._activity_should_end_immediately or force:
                self._activity_should_end_immediately = True
                self._activity_should_end_immediately_results = results
                self._activity_should_end_immediately_delay = delay

        # The activity has already begun; get ready to end it.
        else:
            if (not activity.has_ended()) or force:
                activity.set_has_ended(True)

                # Set a timer to set in motion this activity's demise.
                self._activity_end_timer = _bascenev1.BaseTimer(
                    delay,
                    babase.Call(self._complete_end_activity, activity, results),
                )

    def handlemessage(self, msg: Any) -> Any:
        """General message handling; can be passed any message object."""
        from bascenev1._lobby import PlayerReadyMessage
        from bascenev1._messages import PlayerProfilesChangedMessage, UNHANDLED

        if isinstance(msg, PlayerReadyMessage):
            self._on_player_ready(msg.chooser)

        elif isinstance(msg, PlayerProfilesChangedMessage):
            # If we have a current activity with a lobby, ask it to reload
            # profiles.
            with self.context:
                self.lobby.reload_profiles()
            return None

        else:
            return UNHANDLED
        return None

    class _SetActivityScopedLock:
        def __init__(self, session: Session) -> None:
            self._session = session
            if session._in_set_activity:
                raise RuntimeError('Session.setactivity() called recursively.')
            self._session._in_set_activity = True

        def __del__(self) -> None:
            self._session._in_set_activity = False

    def setactivity(self, activity: bascenev1.Activity) -> None:
        """Assign a new current activity for the session.

        Note that this will not change the current context to the new
        activity's. Code must be run in the new activity's methods
        (:meth:`~bascenev1.Activity.on_transition_in()`, etc) to get it.
        (so you can't do ``session.setactivity(foo)`` and then
        ``bascenev1.newnode()`` to add a node to foo).
        """

        # Make sure we don't get called recursively.
        _rlock = self._SetActivityScopedLock(self)

        if activity.session is not _bascenev1.getsession():
            raise RuntimeError("Provided Activity's Session is not current.")

        # Quietly ignore this if the whole session is going down.
        if self._ending:
            return

        if activity is self._activity_retained:
            logging.error('Activity set to already-current activity.')
            return

        if self._next_activity is not None:
            raise RuntimeError(
                'Activity switch already in progress (to '
                + str(self._next_activity)
                + ')'
            )

        prev_activity = self._activity_retained
        prev_globals = (
            prev_activity.globalsnode if prev_activity is not None else None
        )

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
            with babase.ContextRef.empty():
                babase.apptimer(
                    max(0.0, activity.transition_time), prev_activity.expire
                )
        self._in_set_activity = False

    def getactivity(self) -> bascenev1.Activity | None:
        """Return the current foreground activity for this session."""
        return self._activity_weak()

    def get_custom_menu_entries(self) -> list[dict[str, Any]]:
        """Subclasses can override this to provide custom menu entries.

        The returned value should be a list of dicts, each containing
        a 'label' and 'call' entry, with 'label' being the text for
        the entry and 'call' being the callable to trigger if the entry
        is pressed.
        """
        return []

    def _complete_end_activity(
        self, activity: bascenev1.Activity, results: Any
    ) -> None:
        # Run the subclass callback in the session context.
        try:
            with self.context:
                self.on_activity_end(activity, results)
        except Exception:
            logging.error(
                'Error in on_activity_end() for session %s'
                ' activity %s with results %s',
                self,
                activity,
                results,
            )

    def _request_player(self, sessionplayer: bascenev1.SessionPlayer) -> bool:
        """Called by the native layer when a player wants to join."""

        # If we're ending, allow no new players.
        if self._ending:
            return False

        # Ask the bascenev1.Session subclass to approve/deny this request.
        try:
            with self.context:
                result = self.on_player_request(sessionplayer)
        except Exception:
            logging.exception('Error in on_player_request for %s.', self)
            result = False

        # If they said yes, add the player to the lobby.
        if result:
            self.sessionplayers.append(sessionplayer)
            with self.context:
                try:
                    self.lobby.add_chooser(sessionplayer)
                except Exception:
                    logging.exception('Error in lobby.add_chooser().')

        return result

    def on_activity_end(
        self, activity: bascenev1.Activity, results: Any
    ) -> None:
        """Called when the current activity has ended.

        The session should look at the results and start another
        activity.
        """

    def begin_next_activity(self) -> None:
        """Called once the previous activity has been totally torn down.

        This means we're ready to begin the next one.
        """
        if self._next_activity is None:
            # Should this ever happen?
            logging.error('begin_next_activity() called with no _next_activity')
            return

        # We store both a weak and a strong ref to the new activity;
        # the strong is to keep it alive and the weak is so we can access
        # it even after we've released the strong-ref to allow it to die.
        self._activity_retained = self._next_activity
        self._activity_weak = weakref.ref(self._next_activity)
        self._next_activity = None
        self._activity_should_end_immediately = False

        # Kick out anyone loitering in the lobby.
        self.lobby.remove_all_choosers_and_kick_players()

        # Kick off the activity.
        self._activity_retained.begin(self)

        # If we want to completely end the session, we can now kick that off.
        if self._wants_to_end:
            self._launch_end_session_activity()
        else:
            # Otherwise, if the activity has already been told to end,
            # do so now.
            if self._activity_should_end_immediately:
                self._activity_retained.end(
                    self._activity_should_end_immediately_results,
                    self._activity_should_end_immediately_delay,
                )

    def _on_player_ready(self, chooser: bascenev1.Chooser) -> None:
        """Called when a bascenev1.Player has checked themself ready."""
        lobby = chooser.lobby
        activity = self._activity_weak()

        # This happens sometimes. That seems like it shouldn't be happening;
        # when would we have a session and a chooser with players but no
        # active activity?
        if activity is None:
            print('_on_player_ready called with no activity.')
            return

        # In joining-activities, we wait till all choosers are ready
        # and then create all players at once.
        if activity.is_joining_activity:
            if not lobby.check_all_ready():
                return
            choosers = lobby.get_choosers()
            min_players = self.min_players
            if len(choosers) >= min_players:
                for lch in lobby.get_choosers():
                    self._add_chosen_player(lch)
                lobby.remove_all_choosers()

                # Get our next activity going.
                self._complete_end_activity(activity, {})
            else:
                _bascenev1.broadcastmessage(
                    babase.Lstr(
                        resource='notEnoughPlayersText',
                        subs=[('${COUNT}', str(min_players))],
                    ),
                    color=(1, 1, 0),
                )
                _bascenev1.getsound('error').play()

        # Otherwise just add players on the fly.
        else:
            self._add_chosen_player(chooser)
            lobby.remove_chooser(chooser.getplayer())

    def transitioning_out_activity_was_freed(
        self, can_show_ad_on_death: bool
    ) -> None:
        """(internal)

        :meta private:
        """
        # pylint: disable=cyclic-import

        # Since things should be generally still right now, it's a good time
        # to run garbage collection to clear out any circular dependency
        # loops. We keep this disabled normally to avoid non-deterministic
        # hitches.
        babase.app.gc.collect()

        classic = babase.app.classic
        plus = babase.app.plus
        assert classic is not None
        assert plus is not None

        with self.context:
            if can_show_ad_on_death and classic.can_show_interstitial():
                plus.ads.call_after_ad(self.begin_next_activity)
            else:
                babase.pushcall(self.begin_next_activity)

    def _add_chosen_player(
        self, chooser: bascenev1.Chooser
    ) -> bascenev1.SessionPlayer:
        from bascenev1._team import SessionTeam

        sessionplayer = chooser.getplayer()
        assert sessionplayer in self.sessionplayers, (
            'SessionPlayer not found in session '
            'player-list after chooser selection.'
        )

        activity = self._activity_weak()
        assert activity is not None

        # Reset the player's input here, as it is probably
        # referencing the chooser which could inadvertently keep it alive.
        sessionplayer.resetinput()

        # We can pass it to the current activity if it has already begun
        # (otherwise it'll get passed once begin is called).
        pass_to_activity = (
            activity.has_begun() and not activity.is_joining_activity
        )

        # However, if we're not allowing mid-game joins, don't actually pass;
        # just announce the arrival and say they'll partake next round.
        if pass_to_activity:
            if not (
                activity.allow_mid_activity_joins
                and self.should_allow_mid_activity_joins(activity)
            ):
                pass_to_activity = False
                with self.context:
                    _bascenev1.broadcastmessage(
                        babase.Lstr(
                            resource='playerDelayedJoinText',
                            subs=[
                                ('${PLAYER}', sessionplayer.getname(full=True))
                            ],
                        ),
                        color=(0, 1, 0),
                    )

        # If we're a non-team session, each player gets their own team.
        # (keeps mini-game coding simpler if we can always deal with teams).
        if self.use_teams:
            sessionteam = chooser.sessionteam
        else:
            our_team_id = self._next_team_id
            self._next_team_id += 1
            sessionteam = SessionTeam(
                team_id=our_team_id,
                color=chooser.get_color(),
                name=chooser.getplayer().getname(full=True, icon=False),
            )

            # Add player's team to the Session.
            self.sessionteams.append(sessionteam)

            with self.context:
                try:
                    self.on_team_join(sessionteam)
                except Exception:
                    logging.exception('Error in on_team_join for %s.', self)

            # Add player's team to the Activity.
            if pass_to_activity:
                activity.add_team(sessionteam)

        assert sessionplayer not in sessionteam.players
        sessionteam.players.append(sessionplayer)
        sessionplayer.setdata(
            team=sessionteam,
            character=chooser.get_character_name(),
            color=chooser.get_color(),
            highlight=chooser.get_highlight(),
        )

        self.stats.register_sessionplayer(sessionplayer)
        if pass_to_activity:
            activity.add_player(sessionplayer)
        return sessionplayer

    def _remove_player_from_waitlist(self, identifier: str) -> None:
        try:
            self._players_on_wait.pop(identifier)
        except KeyError:
            pass
