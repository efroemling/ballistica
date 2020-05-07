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
from typing import TYPE_CHECKING

import _ba
from ba._dependency import DependencyComponent

if TYPE_CHECKING:
    from weakref import ReferenceType
    from typing import Optional, Type, Any, Dict, List
    import ba
    from bastd.actor.respawnicon import RespawnIcon


class Activity(DependencyComponent):
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

    # Annotating attr types at the class level lets us introspect them.
    settings_raw: Dict[str, Any]
    teams: List[ba.Team]
    players: List[ba.Player]

    def __init__(self, settings: Dict[str, Any]):
        """Creates an activity in the current ba.Session.

        The activity will not be actually run until ba.Session.set_activity()
        is called. 'settings' should be a dict of key/value pairs specific
        to the activity.

        Activities should preload as much of their media/etc as possible in
        their constructor, but none of it should actually be used until they
        are transitioned in.
        """
        super().__init__()

        # FIXME: Relocate this stuff.
        self.sharedobjs: Dict[str, Any] = {}
        self.paused_text: Optional[ba.Actor] = None
        self.spaz_respawn_icons_right: Dict[int, RespawnIcon]

        # Create our internal engine data.
        self._activity_data = _ba.register_activity(self)

        session = _ba.getsession()
        if session is None:
            raise Exception('No current session')
        self._session = weakref.ref(session)

        # Preloaded data for actors, maps, etc; indexed by type.
        self.preloads: Dict[Type, Any] = {}

        if not isinstance(settings, dict):
            raise Exception('expected dict for settings')
        if _ba.getactivity(doraise=False) is not self:
            raise Exception('invalid context state')

        # Should perhaps kill this; activities should validate/store whatever
        # settings they need at init time (in a more type-safe way).
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

        # Whether to print every time a player dies. This can be pertinent
        # in games such as Death-Match but can be annoying in games where it
        # doesn't matter.
        self.announce_player_deaths = False

        # Joining activities are for waiting for initial player joins.
        # They are treated slightly differently than regular activities,
        # mainly in that all players are passed to the activity at once
        # instead of as each joins.
        self.is_joining_activity = False

        # Whether game-time should still progress when in menus/etc.
        self.allow_pausing = False

        # Whether idle players can potentially be kicked (should not happen in
        # menus/etc).
        self.allow_kick_idle_players = True

        # In vr mode, this determines whether overlay nodes (text, images, etc)
        # are created at a fixed position in space or one that moves based on
        # the current map. Generally this should be on for games and off for
        # transitions/score-screens/etc. that persist between maps.
        self.use_fixed_vr_overlay = False

        # If True, runs in slow motion and turns down sound pitch.
        self.slow_motion = False

        # Set this to True to inherit slow motion setting from previous
        # activity (useful for transitions to avoid hitches).
        self.inherits_slow_motion = False

        # Set this to True to keep playing the music from the previous activity
        # (without even restarting it).
        self.inherits_music = False

        # Set this to true to inherit VR camera offsets from the previous
        # activity (useful for preventing sporadic camera movement
        # during transitions).
        self.inherits_camera_vr_offset = False

        # Set this to true to inherit (non-fixed) VR overlay positioning from
        # the previous activity (useful for prevent sporadic overlay jostling
        # during transitions).
        self.inherits_vr_overlay_center = False

        # Set this to true to inherit screen tint/vignette colors from the
        # previous activity (useful to prevent sudden color changes during
        # transitions).
        self.inherits_tint = False

        # If the activity fades or transitions in, it should set the length of
        # time here so that previous activities will be kept alive for that
        # long (avoiding 'holes' in the screen)
        # This value is given in real-time seconds.
        self.transition_time = 0.0

        # Is it ok to show an ad after this activity ends before showing
        # the next activity?
        self.can_show_ad_on_death = False

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
        self._last_dead_object_prune_time = _ba.time()

        # This stuff gets filled in just before on_begin() is called.
        self.teams = []
        self.players = []
        self._stats: Optional[ba.Stats] = None

        self.lobby = None
        self._prune_dead_objects_timer: Optional[ba.Timer] = None

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

    def is_expired(self) -> bool:
        """Return whether the activity is expired.

        An activity is set as expired when shutting down.
        At this point no new nodes, timers, etc should be made,
        run, etc, and the activity should be considered a 'zombie'.
        """
        return self._expired

    def __del__(self) -> None:

        from ba._apputils import garbage_collect, call_after_ad

        # If the activity has been run then we should have already cleaned
        # it up, but we still need to run expire calls for un-run activities.
        if not self._expired:
            with _ba.Context('empty'):
                self._expire()

        # Since we're mostly between activities at this point, lets run a cycle
        # of garbage collection; hopefully it won't cause hitches here.
        garbage_collect(session_end=False)

        # Now that our object is officially gonna be dead, tell the session it
        # can fire up the next activity.
        if self._transitioning_out:
            session = self._session()
            if session is not None:
                with _ba.Context(session):
                    if self.can_show_ad_on_death:
                        call_after_ad(session.begin_next_activity)
                    else:
                        _ba.pushcall(session.begin_next_activity)

    def set_has_ended(self, val: bool) -> None:
        """(internal)"""
        self._has_ended = val

    def set_immediate_end(self, results: ba.TeamGameResults, delay: float,
                          force: bool) -> None:
        """Set the activity to die immediately after beginning.

        (internal)
        """
        if self.has_begun():
            raise Exception('This should only be called for Activities'
                            'that have not yet begun.')
        if not self._should_end_immediately or force:
            self._should_end_immediately = True
            self._should_end_immediately_results = results
            self._should_end_immediately_delay = delay

    def _get_player_icon(self, player: ba.Player) -> Dict[str, Any]:

        # Do we want to cache these somehow?
        info = player.get_icon_info()
        return {
            'texture': _ba.gettexture(info['texture']),
            'tint_texture': _ba.gettexture(info['tint_texture']),
            'tint_color': info['tint_color'],
            'tint2_color': info['tint2_color']
        }

    def _destroy(self) -> None:
        from ba._general import Call
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
            raise Exception('_destroy() called multiple times')

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
            from ba import _error
            _error.print_exception('exception on _check_activity_death:')

    def _expire(self) -> None:
        from ba import _error
        self._expired = True

        # Do some default cleanup.
        try:
            try:
                self.on_expire()
            except Exception:
                _error.print_exception('Error in activity on_expire()', self)

            # Send finalize notices to all remaining actors.
            for actor_ref in self._actor_weak_refs:
                try:
                    actor = actor_ref()
                    if actor is not None:
                        actor.on_expire()
                except Exception:
                    _error.print_exception(
                        'Exception on ba.Activity._expire()'
                        ' in actor on_expire():', actor_ref())

            # Reset all players.
            # (releases any attached actors, clears game-data, etc)
            for player in self.players:
                if player:
                    try:
                        player.reset()
                        player.set_activity(None)
                    except Exception:
                        _error.print_exception(
                            'Exception on ba.Activity._expire()'
                            ' resetting player:', player)

            # Ditto with teams.
            for team in self.teams:
                try:
                    team.reset()
                except Exception:
                    _error.print_exception(
                        'Exception on ba.Activity._expire() resetting team:',
                        team)

        except Exception:
            _error.print_exception('Exception during ba.Activity._expire():')

        # Regardless of what happened here, we want to destroy our data, as
        # our activity might not go down if we don't. This will kill all
        # Timers, Nodes, etc, which should clear up any remaining refs to our
        # Actors and Activity and allow us to die peacefully.
        try:
            self._activity_data.destroy()
        except Exception:
            _error.print_exception(
                'Exception during ba.Activity._expire() destroying data:')

    def _prune_dead_objects(self) -> None:
        self._actor_refs = [a for a in self._actor_refs if a]
        self._actor_weak_refs = [a for a in self._actor_weak_refs if a()]
        self._last_dead_object_prune_time = _ba.time()

    def retain_actor(self, actor: ba.Actor) -> None:
        """Add a strong-reference to a ba.Actor to this Activity.

        The reference will be lazily released once ba.Actor.exists()
        returns False for the Actor. The ba.Actor.autoretain() method
        is a convenient way to access this same functionality.
        """
        from ba import _actor as bsactor
        from ba import _error
        if not isinstance(actor, bsactor.Actor):
            raise Exception('non-actor passed to _retain_actor')
        if (self.has_transitioned_in()
                and _ba.time() - self._last_dead_object_prune_time > 10.0):
            _error.print_error('it looks like nodes/actors are not'
                               ' being pruned in your activity;'
                               ' did you call Activity.on_transition_in()'
                               ' from your subclass?; ' + str(self) +
                               ' (loc. a)')
        self._actor_refs.append(actor)

    def add_actor_weak_ref(self, actor: ba.Actor) -> None:
        """Add a weak-reference to a ba.Actor to the ba.Activity.

        (called by the ba.Actor base class)
        """
        from ba import _actor as bsactor
        from ba import _error
        if not isinstance(actor, bsactor.Actor):
            raise Exception('non-actor passed to _add_actor_weak_ref')
        if (self.has_transitioned_in()
                and _ba.time() - self._last_dead_object_prune_time > 10.0):
            _error.print_error('it looks like nodes/actors are '
                               'not being pruned in your activity;'
                               ' did you call Activity.on_transition_in()'
                               ' from your subclass?; ' + str(self) +
                               ' (loc. b)')
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

    def on_player_join(self, player: ba.Player) -> None:
        """Called when a new ba.Player has joined the Activity.

        (including the initial set of Players)
        """

    def on_player_leave(self, player: ba.Player) -> None:
        """Called when a ba.Player is leaving the Activity."""

    def on_team_join(self, team: ba.Team) -> None:
        """Called when a new ba.Team joins the Activity.

        (including the initial set of Teams)
        """

    def on_team_leave(self, team: ba.Team) -> None:
        """Called when a ba.Team leaves the Activity."""

    def on_transition_in(self) -> None:
        """Called when the Activity is first becoming visible.

        Upon this call, the Activity should fade in backgrounds,
        start playing music, etc. It does not yet have access to ba.Players
        or ba.Teams, however. They remain owned by the previous Activity
        up until ba.Activity.on_begin() is called.
        """
        from ba._general import WeakCall

        self._called_activity_on_transition_in = True

        # Start pruning our transient actors periodically.
        self._prune_dead_objects_timer = _ba.Timer(
            5.17, WeakCall(self._prune_dead_objects), repeat=True)
        self._prune_dead_objects()

        # Also start our low-level scene-graph running.
        self._activity_data.start()

    def on_transition_out(self) -> None:
        """Called when your activity begins transitioning out.

        Note that this may happen at any time even if finish() has not been
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

    def start_transition_in(self) -> None:
        """Called by Session to kick of transition-in.

        (internal)
        """
        assert not self._has_transitioned_in
        self._has_transitioned_in = True
        self.on_transition_in()

    def create_player_node(self, player: ba.Player) -> ba.Node:
        """Create the 'player' node associated with the provided ba.Player."""
        from ba._nodeactor import NodeActor
        with _ba.Context(self):
            node = _ba.newnode('player', attrs={'playerID': player.get_id()})
            # FIXME: Should add a dedicated slot for this on ba.Player
            #  instead of cluttering up their gamedata dict.
            player.gamedata['_playernode'] = NodeActor(node)
            return node

    def begin(self, session: ba.Session) -> None:
        """Begin the activity. (should only be called by Session).

        (internal)"""

        # pylint: disable=too-many-branches
        from ba import _error

        if self._has_begun:
            _error.print_error("_begin called twice; this shouldn't happen")
            return

        self._stats = session.stats

        # Operate on the subset of session players who have passed team/char
        # selection.
        players = []
        chooser_players = []
        for player in session.players:
            assert player  # should we ever have invalid players?..
            if player:
                try:
                    team: Optional[ba.Team] = player.team
                except _error.TeamNotFoundError:
                    team = None

                if team is not None:
                    player.reset_input()
                    players.append(player)
                else:
                    # Simply ignore players sitting in the lobby.
                    # (though this technically shouldn't happen anymore since
                    # choosers now get cleared when starting new activities.)
                    print('unexpected: got no-team player in _begin')
                    chooser_players.append(player)
            else:
                _error.print_error(
                    'got nonexistent player in Activity._begin()')

        # Add teams in one by one and send team-joined messages for each.
        for team in session.teams:
            if team in self.teams:
                raise Exception('Duplicate Team Entry')
            self.teams.append(team)
            try:
                with _ba.Context(self):
                    self.on_team_join(team)
            except Exception:
                _error.print_exception('Error in on_team_join for', self)

        # Now add each player to the activity and to its team's list,
        # and send player-joined messages for each.
        for player in players:
            self.players.append(player)
            player.team.players.append(player)
            player.set_activity(self)
            pnode = self.create_player_node(player)
            player.set_node(pnode)
            try:
                with _ba.Context(self):
                    self.on_player_join(player)
            except Exception:
                _error.print_exception('Error in on_player_join for', self)

        with _ba.Context(self):
            # And finally tell the game to start.
            self._has_begun = True
            self.on_begin()

        # Make sure that ba.Activity.on_transition_in() got called
        # at some point.
        if not self._called_activity_on_transition_in:
            _error.print_error(
                'ba.Activity.on_transition_in() never got called for ' +
                str(self) + '; did you forget to call it'
                ' in your on_transition_in override?')

        # Make sure that ba.Activity.on_begin() got called at some point.
        if not self._called_activity_on_begin:
            _error.print_error(
                'ba.Activity.on_begin() never got called for ' + str(self) +
                '; did you forget to call it in your on_begin override?')

        # If the whole session wants to die and was waiting on us, can get
        # that going now.
        if session.wants_to_end:
            session.launch_end_session_activity()
        else:
            # Otherwise, if we've already been told to die, do so now.
            if self._should_end_immediately:
                self.end(self._should_end_immediately_results,
                         self._should_end_immediately_delay)
