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
from ba._error import (print_exception, SessionTeamNotFoundError,
                       SessionPlayerNotFoundError, NodeNotFoundError)
from ba._dependency import DependencyComponent
from ba._general import Call, verify_object_death
from ba._messages import UNHANDLED
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
    inherits_vr_camera_offset = False

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

    def __init__(self, settings: dict):
        """Creates an Activity in the current ba.Session.

        The activity will not be actually run until ba.Session.setactivity()
        is called. 'settings' should be a dict of key/value pairs specific
        to the activity.

        Activities should preload as much of their media/etc as possible in
        their constructor, but none of it should actually be used until they
        are transitioned in.
        """
        super().__init__()

        # Create our internal engine data.
        self._activity_data = _ba.register_activity(self)

        assert isinstance(settings, dict)
        assert _ba.getactivity() is self

        self._globalsnode: Optional[ba.Node] = None

        # Player/Team types should have been specified as type args;
        # grab those.
        self._playertype: Type[PlayerType]
        self._teamtype: Type[TeamType]
        self._setup_player_and_team_types()

        # FIXME: Relocate or remove the need for this stuff.
        self.paused_text: Optional[ba.Actor] = None

        self._session = weakref.ref(_ba.getsession())

        # Preloaded data for actors, maps, etc; indexed by type.
        self.preloads: Dict[Type, Any] = {}

        # Hopefully can eventually kill this; activities should
        # validate/store whatever settings they need at init time
        # (in a more type-safe way).
        self.settings_raw = settings

        self._has_transitioned_in = False
        self._has_begun = False
        self._has_ended = False
        self._activity_death_check_timer: Optional[ba.Timer] = None
        self._expired = False
        self._delay_delete_players: List[PlayerType] = []
        self._delay_delete_teams: List[TeamType] = []
        self._players_that_left: List[ReferenceType[PlayerType]] = []
        self._teams_that_left: List[ReferenceType[TeamType]] = []
        self._transitioning_out = False

        # A handy place to put most actors; this list is pruned of dead
        # actors regularly and these actors are insta-killed as the activity
        # is dying.
        self._actor_refs: List[ba.Actor] = []
        self._actor_weak_refs: List[ReferenceType[ba.Actor]] = []
        self._last_prune_dead_actors_time = _ba.time()
        self._prune_dead_actors_timer: Optional[ba.Timer] = None

        self.teams = []
        self.players = []

        self.lobby = None
        self._stats: Optional[ba.Stats] = None
        self._customdata: Optional[dict] = {}

    def __del__(self) -> None:

        # If the activity has been run then we should have already cleaned
        # it up, but we still need to run expire calls for un-run activities.
        if not self._expired:
            with _ba.Context('empty'):
                self._expire()

        # Inform our owner that we officially kicked the bucket.
        if self._transitioning_out:
            session = self._session()
            if session is not None:
                _ba.pushcall(
                    Call(session.transitioning_out_activity_was_freed,
                         self.can_show_ad_on_death))

    @property
    def globalsnode(self) -> ba.Node:
        """The 'globals' ba.Node for the activity. This contains various
        global controls and values.
        """
        node = self._globalsnode
        if not node:
            raise NodeNotFoundError()
        return node

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
    def customdata(self) -> dict:
        """Entities needing to store simple data with an activity can put it
        here. This dict will be deleted when the activity expires, so contained
        objects generally do not need to worry about handling expired
        activities.
        """
        assert not self._expired
        assert isinstance(self._customdata, dict)
        return self._customdata

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

    def expire(self) -> None:
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
        if __debug__:
            from ba._actor import Actor
            assert isinstance(actor, Actor)
        self._actor_refs.append(actor)

    def add_actor_weak_ref(self, actor: ba.Actor) -> None:
        """Add a weak-reference to a ba.Actor to the ba.Activity.

        (called by the ba.Actor base class)
        """
        if __debug__:
            from ba._actor import Actor
            assert isinstance(actor, Actor)
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

    def handlemessage(self, msg: Any) -> Any:
        """General message handling; can be passed any message object."""
        del msg  # Unused arg.
        return UNHANDLED

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
        assert not self._has_transitioned_in
        self._has_transitioned_in = True

        # Set up the globals node based on our settings.
        with _ba.Context(self):
            glb = self._globalsnode = _ba.newnode('globals')

            # Now that it's going to be front and center,
            # set some global values based on what the activity wants.
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
            if self.inherits_vr_camera_offset and prev_globals is not None:
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

            # Start pruning our various things periodically.
            self._prune_dead_actors()
            self._prune_dead_actors_timer = _ba.Timer(5.17,
                                                      self._prune_dead_actors,
                                                      repeat=True)

            _ba.timer(13.3, self._prune_delay_deletes, repeat=True)

            # Also start our low-level scene running.
            self._activity_data.start()

            try:
                self.on_transition_in()
            except Exception:
                print_exception(f'Error in on_transition_in for {self}.')

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
                print_exception(f'Error in on_transition_out for {self}.')

    def begin(self, session: ba.Session) -> None:
        """Begin the activity.

        (internal)
        """

        assert not self._has_begun

        # Inherit stats from the session.
        self._stats = session.stats

        # Add session's teams in.
        for team in session.sessionteams:
            self.add_team(team)

        # Add session's players in.
        for player in session.sessionplayers:
            self.add_player(player)

        self._has_begun = True

        # Let the activity do its thing.
        with _ba.Context(self):
            # Note: do we want to catch errors here?
            # Currently I believe we wind up canceling the
            # activity launch; just wanna be sure that is intentional.
            self.on_begin()

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

    def create_player(self, sessionplayer: ba.SessionPlayer) -> PlayerType:
        """Create the Player instance for this Activity.

        Subclasses can override this if the activity's player class
        requires a custom constructor; otherwise it will be called with
        no args. Note that the player object should not be used at this
        point as it is not yet fully wired up; wait for on_player_join()
        for that.
        """
        del sessionplayer  # Unused.
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
        assert sessionplayer.sessionteam is not None
        sessionplayer.resetinput()
        sessionteam = sessionplayer.sessionteam
        assert sessionplayer in sessionteam.players
        team = sessionteam.activityteam
        assert team is not None
        sessionplayer.setactivity(self)
        with _ba.Context(self):
            sessionplayer.activityplayer = player = self.create_player(
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
                print_exception(f'Error in on_player_join for {self}.')

    def remove_player(self, sessionplayer: ba.SessionPlayer) -> None:
        """Remove a player from the Activity while it is running.

        (internal)
        """
        assert not self.expired

        player: Any = sessionplayer.activityplayer
        assert isinstance(player, self._playertype)
        team: Any = sessionplayer.sessionteam.activityteam
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
            try:
                self.on_player_leave(player)
            except Exception:
                print_exception(f'Error in on_player_leave for {self}.')
            try:
                player.leave()
            except Exception:
                print_exception(f'Error on leave for {player} in {self}.')

            self._reset_session_player_for_no_activity(sessionplayer)

        # Add the player to a list to keep it around for a while. This is
        # to discourage logic from firing on player object death, which
        # may not happen until activity end if something is holding refs
        # to it.
        self._delay_delete_players.append(player)
        self._players_that_left.append(weakref.ref(player))

    def add_team(self, sessionteam: ba.SessionTeam) -> None:
        """Add a team to the Activity

        (internal)
        """
        assert not self.expired

        with _ba.Context(self):
            sessionteam.activityteam = team = self.create_team(sessionteam)
            team.postinit(sessionteam)
            self.teams.append(team)
            try:
                self.on_team_join(team)
            except Exception:
                print_exception(f'Error in on_team_join for {self}.')

    def remove_team(self, sessionteam: ba.SessionTeam) -> None:
        """Remove a team from a Running Activity

        (internal)
        """
        assert not self.expired
        assert sessionteam.activityteam is not None

        team: Any = sessionteam.activityteam
        assert isinstance(team, self._teamtype)

        assert team in self.teams
        self.teams.remove(team)
        assert team not in self.teams

        with _ba.Context(self):
            # Make a decent attempt to persevere if user code breaks.
            try:
                self.on_team_leave(team)
            except Exception:
                print_exception(f'Error in on_team_leave for {self}.')
            try:
                team.leave()
            except Exception:
                print_exception(f'Error on leave for {team} in {self}.')

            sessionteam.activityteam = None

        # Add the team to a list to keep it around for a while. This is
        # to discourage logic from firing on team object death, which
        # may not happen until activity end if something is holding refs
        # to it.
        self._delay_delete_teams.append(team)
        self._teams_that_left.append(weakref.ref(team))

    def _reset_session_player_for_no_activity(
            self, sessionplayer: ba.SessionPlayer) -> None:

        # Let's be extra-defensive here: killing a node/input-call/etc
        # could trigger user-code resulting in errors, but we would still
        # like to complete the reset if possible.
        try:
            sessionplayer.setnode(None)
        except Exception:
            print_exception(
                f'Error resetting SessionPlayer node on {sessionplayer}'
                f' for {self}.')
        try:
            sessionplayer.resetinput()
        except Exception:
            print_exception(
                f'Error resetting SessionPlayer input on {sessionplayer}'
                f' for {self}.')

        # These should never fail I think...
        sessionplayer.setactivity(None)
        sessionplayer.activityplayer = None

    def _setup_player_and_team_types(self) -> None:
        """Pull player and team types from our typing.Generic params."""

        # TODO: There are proper calls for pulling these in Python 3.8;
        # should update this code when we adopt that.
        # NOTE: If we get Any as PlayerType or TeamType (generally due
        # to no generic params being passed) we automatically use the
        # base class types, but also warn the user since this will mean
        # less type safety for that class. (its better to pass the base
        # player/team types explicitly vs. having them be Any)
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
            print_exception('Error on _check_activity_death/')

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
            print_exception(f'Error in Activity on_expire() for {self}.')

        try:
            self._customdata = None
        except Exception:
            print_exception(f'Error clearing customdata for {self}.')

        # Don't want to be holding any delay-delete refs at this point.
        self._prune_delay_deletes()

        self._expire_actors()
        self._expire_players()
        self._expire_teams()

        # This will kill all low level stuff: Timers, Nodes, etc., which
        # should clear up any remaining refs to our Activity and allow us
        # to die peacefully.
        try:
            self._activity_data.expire()
        except Exception:
            print_exception(f'Error expiring _activity_data for {self}.')

    def _expire_actors(self) -> None:
        # Expire all Actors.
        for actor_ref in self._actor_weak_refs:
            actor = actor_ref()
            if actor is not None:
                verify_object_death(actor)
                try:
                    actor.on_expire()
                except Exception:
                    print_exception(f'Error in Actor.on_expire()'
                                    f' for {actor_ref()}.')

    def _expire_players(self) -> None:

        # Issue warnings for any players that left the game but don't
        # get freed soon.
        for ex_player in (p() for p in self._players_that_left):
            if ex_player is not None:
                verify_object_death(ex_player)

        for player in self.players:
            # This should allow our ba.Player instance to be freed.
            # Complain if that doesn't happen.
            verify_object_death(player)

            try:
                player.expire()
            except Exception:
                print_exception(f'Error expiring {player}')

            # Reset the SessionPlayer to a not-in-an-activity state.
            try:
                sessionplayer = player.sessionplayer
                self._reset_session_player_for_no_activity(sessionplayer)
            except SessionPlayerNotFoundError:
                # Conceivably, someone could have held on to a Player object
                # until now whos underlying SessionPlayer left long ago...
                pass
            except Exception:
                print_exception(f'Error expiring {player}.')

    def _expire_teams(self) -> None:

        # Issue warnings for any teams that left the game but don't
        # get freed soon.
        for ex_team in (p() for p in self._teams_that_left):
            if ex_team is not None:
                verify_object_death(ex_team)

        for team in self.teams:
            # This should allow our ba.Team instance to die.
            # Complain if that doesn't happen.
            verify_object_death(team)

            try:
                team.expire()
            except Exception:
                print_exception(f'Error expiring {team}')

            try:
                sessionteam = team.sessionteam
                sessionteam.activityteam = None
            except SessionTeamNotFoundError:
                # It is expected that Team objects may last longer than
                # the SessionTeam they came from (game objects may hold
                # team references past the point at which the underlying
                # player/team has left the game)
                pass
            except Exception:
                print_exception(f'Error expiring Team {team}.')

    def _prune_delay_deletes(self) -> None:
        self._delay_delete_players.clear()
        self._delay_delete_teams.clear()

        # Clear out any dead weak-refs.
        self._teams_that_left = [
            t for t in self._teams_that_left if t() is not None
        ]
        self._players_that_left = [
            p for p in self._players_that_left if p() is not None
        ]

    def _prune_dead_actors(self) -> None:
        self._last_prune_dead_actors_time = _ba.time()

        # Prune our strong refs when the Actor's exists() call gives False
        self._actor_refs = [a for a in self._actor_refs if a.exists()]

        # Prune our weak refs once the Actor object has been freed.
        self._actor_weak_refs = [
            a for a in self._actor_weak_refs if a() is not None
        ]
