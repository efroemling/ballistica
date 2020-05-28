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
"""Defines Activity class."""
from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Generic, TypeVar

from ba._team import Team
from ba._player import Player
from ba._error import print_exception, print_error, SessionTeamNotFoundError
from ba._dependency import DependencyComponent
from ba._general import Call, verify_object_death
import _ba

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import Optional, Type, Any, Dict, List
    import ba
    from bastd.actor.respawnicon import RespawnIcon

PlayerType = TypeVar('PlayerType', bound=Player)
TeamType = TypeVar('TeamType', bound=Team)


class Activity(DependencyComponent, Generic[PlayerType, TeamType]):
    """Units of execution wrangled by a ba.Session.

    Category: Gameplay Classes

    Examples of Activities include games, score-screens, cutscenes, etc.
    A ba.Session has one 'current' Activity at any time, though their existence
    can overlap during transitions.

    Attributes:

       settings_raw
          The settings dict passed in when the activity was made.
          This attribute is deprecated and should be avoided when possible;
          activities should pull all values they need from the 'settings' arg
          passed to the Activity __init__ call.

       teams
          The list of ba.Teams in the Activity. This gets populated just before
          before on_begin() is called and is updated automatically as players
          join or leave the game. (at least in free-for-all mode where every
          player gets their own team; in teams mode there are always 2 teams
          regardless of the player count).

       players
          The list of ba.Players in the Activity. This gets populated just
          before on_begin() is called and is updated automatically as players
          join or leave the game.
    """

    # pylint: disable=too-many-public-methods

    # Annotating attr types at the class level lets us introspect at runtime.
    settings_raw: Dict[str, Any]
    teams: List[TeamType]
    players: List[PlayerType]

    # Whether to print every time a player dies. This can be pertinent
    # in games such as Death-Match but can be annoying in games where it
    # doesn't matter.
    announce_player_deaths = False

    # Joining activities are for waiting for initial player joins.
    # They are treated slightly differently than regular activities,
    # mainly in that all players are passed to the activity at once
    # instead of as each joins.
    is_joining_activity = False

    # Whether game-time should still progress when in menus/etc.
    allow_pausing = False

    # Whether idle players can potentially be kicked (should not happen in
    # menus/etc).
    allow_kick_idle_players = True

    # In vr mode, this determines whether overlay nodes (text, images, etc)
    # are created at a fixed position in space or one that moves based on
    # the current map. Generally this should be on for games and off for
    # transitions/score-screens/etc. that persist between maps.
    use_fixed_vr_overlay = False

    # If True, runs in slow motion and turns down sound pitch.
    slow_motion = False

    # Set this to True to inherit slow motion setting from previous
    # activity (useful for transitions to avoid hitches).
    inherits_slow_motion = False

    # Set this to True to keep playing the music from the previous activity
    # (without even restarting it).
    inherits_music = False

    # Set this to true to inherit VR camera offsets from the previous
    # activity (useful for preventing sporadic camera movement
    # during transitions).
    inherits_camera_vr_offset = False

    # Set this to true to inherit (non-fixed) VR overlay positioning from
    # the previous activity (useful for prevent sporadic overlay jostling
    # during transitions).
    inherits_vr_overlay_center = False

    # Set this to true to inherit screen tint/vignette colors from the
    # previous activity (useful to prevent sudden color changes during
    # transitions).
    inherits_tint = False

    # If the activity fades or transitions in, it should set the length of
    # time here so that previous activities will be kept alive for that
    # long (avoiding 'holes' in the screen)
    # This value is given in real-time seconds.
    transition_time = 0.0

    # Is it ok to show an ad after this activity ends before showing
    # the next activity?
    can_show_ad_on_death = False

    def __init__(self, settings: Dict[str, Any]):
        """Creates an Activity in the current ba.Session.

        The activity will not be actually run until ba.Session.set_activity()
        is called. 'settings' should be a dict of key/value pairs specific
        to the activity.

        Activities should preload as much of their media/etc as possible in
        their constructor, but none of it should actually be used until they
        are transitioned in.
        """
        super().__init__()

        # Create our internal engine data.
        self._activity_data = _ba.register_activity(self)

        # Player/Team types should have been specified as type args;
        # grab those.
        self._playertype: Type[PlayerType]
        self._teamtype: Type[TeamType]
        self._setup_player_and_team_types()

        # FIXME: Relocate or remove the need for this stuff.
        self.sharedobjs: Dict[str, Any] = {}
        self.paused_text: Optional[ba.Actor] = None
        self.spaz_respawn_icons_right: Dict[int, RespawnIcon]

        session = _ba.getsession()
        if session is None:
            raise RuntimeError('No current session')
        self._session = weakref.ref(session)

        # Preloaded data for actors, maps, etc; indexed by type.
        self.preloads: Dict[Type, Any] = {}

        if not isinstance(settings, dict):
            raise TypeError('expected dict for settings')
        if _ba.getactivity(doraise=False) is not self:
            raise Exception('invalid context state')

        # Hopefully can eventually kill this; activities should
        # validate/store whatever settings they need at init time
        # (in a more type-safe way).
        self.settings_raw = settings

        self._has_transitioned_in = False
        self._has_begun = False
        self._has_ended = False
        self._should_end_immediately = False
        self._should_end_immediately_results: (
            Optional[ba.TeamGameResults]) = None
        self._should_end_immediately_delay = 0.0
        self._called_activity_on_transition_in = False
        self._called_activity_on_begin = False

        self._activity_death_check_timer: Optional[ba.Timer] = None
        self._expired = False

        # This gets set once another activity has begun transitioning in but
        # before this one is killed. The on_transition_out() method is also
        # called at this time.  Make sure to not assign player inputs,
        # change music, or anything else with global implications once this
        # happens.
        self._transitioning_out = False

        # A handy place to put most actors; this list is pruned of dead
        # actors regularly and these actors are insta-killed as the activity
        # is dying.
        self._actor_refs: List[ba.Actor] = []
        self._actor_weak_refs: List[ReferenceType[ba.Actor]] = []
        self._last_prune_dead_actors_time = _ba.time()
        self._prune_dead_actors_timer: Optional[ba.Timer] = None

        # This stuff gets filled in just before on_begin() is called.
        self.teams = []
        self.players = []
        self.lobby = None
        self._stats: Optional[ba.Stats] = None

    def __del__(self) -> None:

        # If the activity has been run then we should have already cleaned
        # it up, but we still need to run expire calls for un-run activities.
        if not self._expired:
            with _ba.Context('empty'):
                self._expire()

        # Inform our owner that we're officially kicking the bucket.
        if self._transitioning_out:
            session = self._session()
            if session is not None:
                _ba.pushcall(
                    Call(session.transitioning_out_activity_was_freed,
                         self.can_show_ad_on_death))

    @property
    def stats(self) -> ba.Stats:
        """The stats instance accessible while the activity is running.

        If access is attempted before or after, raises a ba.NotFoundError.
        """
        if self._stats is None:
            from ba._error import NotFoundError
            raise NotFoundError()
        return self._stats

    def on_expire(self) -> None:
        """Called when your activity is being expired.

        If your activity has created anything explicitly that may be retaining
        a strong reference to the activity and preventing it from dying, you
        should clear that out here. From this point on your activity's sole
        purpose in life is to hit zero references and die so the next activity
        can begin.
        """

    @property
    def expired(self) -> bool:
        """Whether the activity is expired.

        An activity is set as expired when shutting down.
        At this point no new nodes, timers, etc should be made,
        run, etc, and the activity should be considered a 'zombie'.
        """
        return self._expired

    @property
    def playertype(self) -> Type[PlayerType]:
        """The type of ba.Player this Activity is using."""
        return self._playertype

    @property
    def teamtype(self) -> Type[TeamType]:
        """The type of ba.Team this Activity is using."""
        return self._teamtype

    def set_has_ended(self, val: bool) -> None:
        """(internal)"""
        self._has_ended = val

    def set_immediate_end(self, results: ba.TeamGameResults, delay: float,
                          force: bool) -> None:
        """Set the activity to die immediately after beginning.

        (internal)
        """
        if self.has_begun():
            raise RuntimeError('This should only be called for Activities'
                               'that have not yet begun.')
        if not self._should_end_immediately or force:
            self._should_end_immediately = True
            self._should_end_immediately_results = results
            self._should_end_immediately_delay = delay

    def destroy(self) -> None:
        """Begin the process of tearing down the activity.

        (internal)
        """
        from ba._enums import TimeType

        # Create a real-timer that watches a weak-ref of this activity
        # and reports any lingering references keeping it alive.
        # We store the timer on the activity so as soon as the activity dies
        # it gets cleaned up.
        with _ba.Context('ui'):
            ref = weakref.ref(self)
            self._activity_death_check_timer = _ba.Timer(
                5.0,
                Call(self._check_activity_death, ref, [0]),
                repeat=True,
                timetype=TimeType.REAL)

        # Run _expire in an empty context; nothing should be happening in
        # there except deleting things which requires no context.
        # (plus, _expire() runs in the destructor for un-run activities
        # and we can't properly provide context in that situation anyway; might
        # as well be consistent).
        if not self._expired:
            with _ba.Context('empty'):
                self._expire()
        else:
            raise RuntimeError(f'destroy() called when'
                               f' already expired for {self}')

    def retain_actor(self, actor: ba.Actor) -> None:
        """Add a strong-reference to a ba.Actor to this Activity.

        The reference will be lazily released once ba.Actor.exists()
        returns False for the Actor. The ba.Actor.autoretain() method
        is a convenient way to access this same functionality.
        """
        from ba import _actor as bsactor
        if not isinstance(actor, bsactor.Actor):
            raise TypeError('non-actor passed to retain_actor')
        if (self.has_transitioned_in()
                and _ba.time() - self._last_prune_dead_actors_time > 10.0):
            print_error('It looks like nodes/actors are not'
                        ' being pruned in your activity;'
                        ' did you call Activity.on_transition_in()'
                        ' from your subclass?; ' + str(self) + ' (loc. a)')
        self._actor_refs.append(actor)

    def add_actor_weak_ref(self, actor: ba.Actor) -> None:
        """Add a weak-reference to a ba.Actor to the ba.Activity.

        (called by the ba.Actor base class)
        """
        from ba import _actor as bsactor
        if not isinstance(actor, bsactor.Actor):
            raise TypeError('non-actor passed to add_actor_weak_ref')
        if (self.has_transitioned_in()
                and _ba.time() - self._last_prune_dead_actors_time > 10.0):
            print_error('It looks like nodes/actors are '
                        'not being pruned in your activity;'
                        ' did you call Activity.on_transition_in()'
                        ' from your subclass?; ' + str(self) + ' (loc. b)')
        self._actor_weak_refs.append(weakref.ref(actor))

    @property
    def session(self) -> ba.Session:
        """The ba.Session this ba.Activity belongs go.

        Raises a ba.SessionNotFoundError if the Session no longer exists.
        """
        session = self._session()
        if session is None:
            from ba._error import SessionNotFoundError
            raise SessionNotFoundError()
        return session

    def on_player_join(self, player: PlayerType) -> None:
        """Called when a new ba.Player has joined the Activity.

        (including the initial set of Players)
        """

    def on_player_leave(self, player: PlayerType) -> None:
        """Called when a ba.Player is leaving the Activity."""

    def on_team_join(self, team: TeamType) -> None:
        """Called when a new ba.Team joins the Activity.

        (including the initial set of Teams)
        """

    def on_team_leave(self, team: TeamType) -> None:
        """Called when a ba.Team leaves the Activity."""

    def on_transition_in(self) -> None:
        """Called when the Activity is first becoming visible.

        Upon this call, the Activity should fade in backgrounds,
        start playing music, etc. It does not yet have access to players
        or teams, however. They remain owned by the previous Activity
        up until ba.Activity.on_begin() is called.
        """
        self._called_activity_on_transition_in = True

    def on_transition_out(self) -> None:
        """Called when your activity begins transitioning out.

        Note that this may happen at any time even if end() has not been
        called.
        """

    def on_begin(self) -> None:
        """Called once the previous ba.Activity has finished transitioning out.

        At this point the activity's initial players and teams are filled in
        and it should begin its actual game logic.
        """
        self._called_activity_on_begin = True

    def handlemessage(self, msg: Any) -> Any:
        """General message handling; can be passed any message object."""

    def end(self,
            results: Any = None,
            delay: float = 0.0,
            force: bool = False) -> None:
        """Commences Activity shutdown and delivers results to the ba.Session.

        'delay' is the time delay before the Activity actually ends
        (in seconds). Further calls to end() will be ignored up until
        this time, unless 'force' is True, in which case the new results
        will replace the old.
        """

        # Ask the session to end us.
        self.session.end_activity(self, results, delay, force)

    def has_transitioned_in(self) -> bool:
        """Return whether on_transition_in() has been called."""
        return self._has_transitioned_in

    def has_begun(self) -> bool:
        """Return whether on_begin() has been called."""
        return self._has_begun

    def has_ended(self) -> bool:
        """Return whether the activity has commenced ending."""
        return self._has_ended

    def is_transitioning_out(self) -> bool:
        """Return whether on_transition_out() has been called."""
        return self._transitioning_out

    def transition_in(self, prev_globals: Optional[ba.Node]) -> None:
        """Called by Session to kick off transition-in.

        (internal)
        """
        from ba._general import WeakCall
        from ba._gameutils import sharedobj
        assert not self._has_transitioned_in
        self._has_transitioned_in = True

        # Set up the globals node based on our settings.
        with _ba.Context(self):
            # Now that it's going to be front and center,
            # set some global values based on what the activity wants.
            glb = sharedobj('globals')
            glb.use_fixed_vr_overlay = self.use_fixed_vr_overlay
            glb.allow_kick_idle_players = self.allow_kick_idle_players
            if self.inherits_slow_motion and prev_globals is not None:
                glb.slow_motion = prev_globals.slow_motion
            else:
                glb.slow_motion = self.slow_motion
            if self.inherits_music and prev_globals is not None:
                glb.music_continuous = True  # Prevent restarting same music.
                glb.music = prev_globals.music
                glb.music_count += 1
            if self.inherits_camera_vr_offset and prev_globals is not None:
                glb.vr_camera_offset = prev_globals.vr_camera_offset
            if self.inherits_vr_overlay_center and prev_globals is not None:
                glb.vr_overlay_center = prev_globals.vr_overlay_center
                glb.vr_overlay_center_enabled = (
                    prev_globals.vr_overlay_center_enabled)

            # If they want to inherit tint from the previous self.
            if self.inherits_tint and prev_globals is not None:
                glb.tint = prev_globals.tint
                glb.vignette_outer = prev_globals.vignette_outer
                glb.vignette_inner = prev_globals.vignette_inner

            # Start pruning our transient actors periodically.
            self._prune_dead_actors_timer = _ba.Timer(
                5.17, WeakCall(self._prune_dead_actors), repeat=True)
            self._prune_dead_actors()

            # Also start our low-level scene running.
            self._activity_data.start()

            try:
                self.on_transition_in()
            except Exception:
                print_exception('Error in on_transition_in for', self)

        # Tell the C++ layer that this activity is the main one, so it uses
        # settings from our globals, directs various events to us, etc.
        self._activity_data.make_foreground()

    def transition_out(self) -> None:
        """Called by the Session to start us transitioning out."""
        assert not self._transitioning_out
        self._transitioning_out = True
        with _ba.Context(self):
            try:
                self.on_transition_out()
            except Exception:
                print_exception('Error in on_transition_out for', self)

    def begin(self, session: ba.Session) -> None:
        """Begin the activity.

        (internal)
        """

        assert not self._has_begun

        # Inherit stats from the session.
        self._stats = session.stats

        # Add session's teams in.
        for team in session.teams:
            self.add_team(team)

        # Add session's players in.
        for player in session.players:
            self.add_player(player)

        # And finally tell the game to start.
        with _ba.Context(self):
            self._has_begun = True
            self.on_begin()

        self._sanity_check_begin_call()

        # If the whole session wants to die and was waiting on us,
        # can kick off that process now.
        if session.wants_to_end:
            session.launch_end_session_activity()
        else:
            # Otherwise, if we've already been told to die, do so now.
            if self._should_end_immediately:
                self.end(self._should_end_immediately_results,
                         self._should_end_immediately_delay)

    def create_player(self, sessionplayer: ba.SessionPlayer) -> PlayerType:
        """Create the Player instance for this Activity.

        Subclasses can override this if the activity's player class
        requires a custom constructor; otherwise it will be called with
        no args. Note that the player object should not be used at this
        point as it is not yet fully wired up; wait for on_player_join()
        for that.
        """
        del sessionplayer  # Unused
        player = self._playertype()
        return player

    def create_team(self, sessionteam: ba.SessionTeam) -> TeamType:
        """Create the Team instance for this Activity.

        Subclasses can override this if the activity's team class
        requires a custom constructor; otherwise it will be called with
        no args. Note that the team object should not be used at this
        point as it is not yet fully wired up; wait for on_team_join()
        for that.
        """
        del sessionteam  # Unused.
        team = self._teamtype()
        return team

    def add_player(self, sessionplayer: ba.SessionPlayer) -> None:
        """(internal)"""
        assert sessionplayer.team is not None
        sessionplayer.reset_input()
        sessionteam = sessionplayer.team
        assert sessionplayer in sessionteam.players
        team = sessionteam.gameteam
        assert team is not None
        sessionplayer.set_activity(self)
        with _ba.Context(self):
            sessionplayer.gameplayer = player = self.create_player(
                sessionplayer)
            player.postinit(sessionplayer)

            assert player not in team.players
            team.players.append(player)
            assert player in team.players

            assert player not in self.players
            self.players.append(player)
            assert player in self.players

            try:
                self.on_player_join(player)
            except Exception:
                print_exception('Error in on_player_join for', self)

    def remove_player(self, sessionplayer: ba.SessionPlayer) -> None:
        """(internal)"""

        # This should only be called on unexpired activities
        # the player has been added to.
        assert not self.expired

        player: Any = sessionplayer.gameplayer
        assert isinstance(player, self._playertype)
        team: Any = sessionplayer.team.gameteam
        assert isinstance(team, self._teamtype)

        assert player in team.players
        team.players.remove(player)
        assert player not in team.players

        assert player in self.players
        self.players.remove(player)
        assert player not in self.players

        # This should allow our ba.Player instance to die.
        # Complain if that doesn't happen.
        # verify_object_death(player)

        with _ba.Context(self):
            # Make a decent attempt to persevere if user code breaks.
            try:
                self.on_player_leave(player)
            except Exception:
                print_exception(f'Error in on_player_leave for {self}')
            try:
                sessionplayer.reset()
                sessionplayer.set_node(None)
                sessionplayer.set_activity(None)
            except Exception:
                print_exception(f'Error resetting player for {self}')

    def add_team(self, sessionteam: ba.SessionTeam) -> None:
        """(internal)"""
        assert not self.expired

        with _ba.Context(self):
            sessionteam.gameteam = team = self.create_team(sessionteam)
            team.postinit(sessionteam)
            self.teams.append(team)
            try:
                self.on_team_join(team)
            except Exception:
                print_exception(f'Error in on_team_join for {self}')

    def remove_team(self, sessionteam: ba.SessionTeam) -> None:
        """(internal)"""

        # This should only be called on unexpired activities the team has
        # been added to.
        assert not self.expired
        assert sessionteam.gameteam is not None
        assert sessionteam.gameteam in self.teams

        team = sessionteam.gameteam
        assert isinstance(team, self._teamtype)

        assert team in self.teams
        self.teams.remove(team)
        assert team not in self.teams

        # This should allow our ba.Team instance to die. Complain
        # if that doesn't happen.
        # verify_object_death(team)

        with _ba.Context(self):
            # Make a decent attempt to persevere if user code breaks.
            try:
                self.on_team_leave(team)
            except Exception:
                print_exception(f'Error in on_team_leave for {self}')
            try:
                sessionteam.reset_gamedata()
            except Exception:
                print_exception(f'Error in reset_gamedata for {self}')

            sessionteam.gameteam = None

    def _sanity_check_begin_call(self) -> None:
        # Make sure ba.Activity.on_transition_in() got called at some point.
        if not self._called_activity_on_transition_in:
            print_error(
                'ba.Activity.on_transition_in() never got called for ' +
                str(self) + '; did you forget to call it'
                ' in your on_transition_in override?')
        # Make sure that ba.Activity.on_begin() got called at some point.
        if not self._called_activity_on_begin:
            print_error(
                'ba.Activity.on_begin() never got called for ' + str(self) +
                '; did you forget to call it in your on_begin override?')

    def _setup_player_and_team_types(self) -> None:
        """Pull player and team types from our typing.Generic params."""

        # TODO: There are proper calls for pulling these in Python 3.8;
        # should update this code when we adopt that.
        # NOTE: If we get Any as PlayerType or TeamType (generally due
        # to no generic params being passed) we automatically use the
        # base class types, but also warn the user since this will mean
        # less type safety for that class. (its better to pass the base
        # types explicitly vs. having them be Any)
        if not TYPE_CHECKING:
            self._playertype = type(self).__orig_bases__[-1].__args__[0]
            if not isinstance(self._playertype, type):
                self._playertype = Player
                print(f'ERROR: {type(self)} was not passed a Player'
                      f' type argument; please explicitly pass ba.Player'
                      f' if you do not want to override it.')
            self._teamtype = type(self).__orig_bases__[-1].__args__[1]
            if not isinstance(self._teamtype, type):
                self._teamtype = Team
                print(f'ERROR: {type(self)} was not passed a Team'
                      f' type argument; please explicitly pass ba.Team'
                      f' if you do not want to override it.')
        assert issubclass(self._playertype, Player)
        assert issubclass(self._teamtype, Team)

    @classmethod
    def _check_activity_death(cls, activity_ref: ReferenceType[Activity],
                              counter: List[int]) -> None:
        """Sanity check to make sure an Activity was destroyed properly.

        Receives a weakref to a ba.Activity which should have torn itself
        down due to no longer being referenced anywhere. Will complain
        and/or print debugging info if the Activity still exists.
        """
        try:
            import gc
            import types
            activity = activity_ref()
            print('ERROR: Activity is not dying when expected:', activity,
                  '(warning ' + str(counter[0] + 1) + ')')
            print('This means something is still strong-referencing it.')
            counter[0] += 1

            # FIXME: Running the code below shows us references but winds up
            #  keeping the object alive; need to figure out why.
            #  For now we just print refs if the count gets to 3, and then we
            #  kill the app at 4 so it doesn't matter anyway.
            if counter[0] == 3:
                print('Activity references for', activity, ':')
                refs = list(gc.get_referrers(activity))
                i = 1
                for ref in refs:
                    if isinstance(ref, types.FrameType):
                        continue
                    print('  reference', i, ':', ref)
                    i += 1
            if counter[0] == 4:
                print('Killing app due to stuck activity... :-(')
                _ba.quit()

        except Exception:
            print_exception('exception on _check_activity_death:')

    def _expire(self) -> None:
        """Put the activity in a state where it can be garbage-collected.

        This involves clearing anything that might be holding a reference
        to it, etc.
        """
        assert not self._expired
        self._expired = True

        try:
            self.on_expire()
        except Exception:
            print_exception(f'Error in Activity on_expire() for {self}')

        # Send expire notices to all remaining actors.
        for actor_ref in self._actor_weak_refs:
            actor = actor_ref()
            if actor is not None:
                verify_object_death(actor)
                try:
                    actor.on_expire()
                except Exception:
                    print_exception(f'Error in Actor.on_expire()'
                                    f' for {actor_ref()}')

        # Reset all Players.
        # (releases any attached actors, clears game-data, etc)
        for player in self.players:
            try:
                # This should allow our ba.Player instance to die.
                # Complain if that doesn't happen.
                # verify_object_death(player)
                sessionplayer = player.sessionplayer
                player.reset()
                sessionplayer.set_node(None)
                sessionplayer.set_activity(None)

                sessionplayer.gameplayer = None
                sessionplayer.reset()
            except Exception:
                print_exception(f'Error resetting Player {player}')

        # Ditto with Teams.
        for team in self.teams:
            try:
                sessionteam = team.sessionteam

                # This should allow our ba.Team instance to die.
                # Complain if that doesn't happen.
                # verify_object_death(sessionteam.gameteam)
                sessionteam.gameteam = None
                sessionteam.reset_gamedata()
            except SessionTeamNotFoundError:
                # It is expected that Team objects may last longer than
                # the SessionTeam they came from (game objects may hold
                # team references past the point at which the underlying
                # player/team leaves)
                pass
            except Exception:
                print_exception(f'Error resetting Team {team}')

        # Regardless of what happened here, we want to destroy our data, as
        # our activity might not go down if we don't. This will kill all
        # Timers, Nodes, etc, which should clear up any remaining refs to our
        # Actors and Activity and allow us to die peacefully.
        try:
            self._activity_data.destroy()
        except Exception:
            print_exception(
                'Error during ba.Activity._expire() destroying data:')

    def _prune_dead_actors(self) -> None:
        self._last_prune_dead_actors_time = _ba.time()

        # Prune our strong refs when the Actor's exists() call gives False
        self._actor_refs = [a for a in self._actor_refs if a.exists()]

        # Prune our weak refs once the Actor object has been freed.
        self._actor_weak_refs = [
            a for a in self._actor_weak_refs if a() is not None
        ]
