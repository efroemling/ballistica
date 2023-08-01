# Released under the MIT License. See LICENSE for details.
#
"""Defines Activity class."""
from __future__ import annotations

import weakref
import logging
from typing import TYPE_CHECKING, Generic, TypeVar

import babase
import _bascenev1
from bascenev1._dependency import DependencyComponent
from bascenev1._team import Team
from bascenev1._messages import UNHANDLED
from bascenev1._player import Player

if TYPE_CHECKING:
    from typing import Any
    import bascenev1

PlayerT = TypeVar('PlayerT', bound=Player)
TeamT = TypeVar('TeamT', bound=Team)


class Activity(DependencyComponent, Generic[PlayerT, TeamT]):
    """Units of execution wrangled by a bascenev1.Session.

    Category: Gameplay Classes

    Examples of Activities include games, score-screens, cutscenes, etc.
    A bascenev1.Session has one 'current' Activity at any time, though
    their existence can overlap during transitions.
    """

    # pylint: disable=too-many-public-methods

    settings_raw: dict[str, Any]
    """The settings dict passed in when the activity was made.
       This attribute is deprecated and should be avoided when possible;
       activities should pull all values they need from the 'settings' arg
       passed to the Activity __init__ call."""

    teams: list[TeamT]
    """The list of bascenev1.Team-s in the Activity. This gets populated just
       before on_begin() is called and is updated automatically as players
       join or leave the game. (at least in free-for-all mode where every
       player gets their own team; in teams mode there are always 2 teams
       regardless of the player count)."""

    players: list[PlayerT]
    """The list of bascenev1.Player-s in the Activity. This gets populated
       just before on_begin() is called and is updated automatically as
       players join or leave the game."""

    announce_player_deaths = False
    """Whether to print every time a player dies. This can be pertinent
       in games such as Death-Match but can be annoying in games where it
       doesn't matter."""

    is_joining_activity = False
    """Joining activities are for waiting for initial player joins.
       They are treated slightly differently than regular activities,
       mainly in that all players are passed to the activity at once
       instead of as each joins."""

    allow_pausing = False
    """Whether game-time should still progress when in menus/etc."""

    allow_kick_idle_players = True
    """Whether idle players can potentially be kicked (should not happen in
       menus/etc)."""

    use_fixed_vr_overlay = False
    """In vr mode, this determines whether overlay nodes (text, images, etc)
       are created at a fixed position in space or one that moves based on
       the current map. Generally this should be on for games and off for
       transitions/score-screens/etc. that persist between maps."""

    slow_motion = False
    """If True, runs in slow motion and turns down sound pitch."""

    inherits_slow_motion = False
    """Set this to True to inherit slow motion setting from previous
       activity (useful for transitions to avoid hitches)."""

    inherits_music = False
    """Set this to True to keep playing the music from the previous activity
       (without even restarting it)."""

    inherits_vr_camera_offset = False
    """Set this to true to inherit VR camera offsets from the previous
       activity (useful for preventing sporadic camera movement
       during transitions)."""

    inherits_vr_overlay_center = False
    """Set this to true to inherit (non-fixed) VR overlay positioning from
       the previous activity (useful for prevent sporadic overlay jostling
       during transitions)."""

    inherits_tint = False
    """Set this to true to inherit screen tint/vignette colors from the
       previous activity (useful to prevent sudden color changes during
       transitions)."""

    allow_mid_activity_joins: bool = True
    """Whether players should be allowed to join in the middle of this
       activity. Note that Sessions may not allow mid-activity-joins even
       if the activity says its ok."""

    transition_time = 0.0
    """If the activity fades or transitions in, it should set the length of
       time here so that previous activities will be kept alive for that
       long (avoiding 'holes' in the screen)
       This value is given in real-time seconds."""

    can_show_ad_on_death = False
    """Is it ok to show an ad after this activity ends before showing
       the next activity?"""

    def __init__(self, settings: dict):
        """Creates an Activity in the current bascenev1.Session.

        The activity will not be actually run until
        bascenev1.Session.setactivity is called. 'settings' should be a
        dict of key/value pairs specific to the activity.

        Activities should preload as much of their media/etc as possible in
        their constructor, but none of it should actually be used until they
        are transitioned in.
        """
        super().__init__()

        # Create our internal engine data.
        self._activity_data = _bascenev1.register_activity(self)

        assert isinstance(settings, dict)
        assert _bascenev1.getactivity() is self

        self._globalsnode: bascenev1.Node | None = None

        # Player/Team types should have been specified as type args;
        # grab those.
        self._playertype: type[PlayerT]
        self._teamtype: type[TeamT]
        self._setup_player_and_team_types()

        # FIXME: Relocate or remove the need for this stuff.
        self.paused_text: bascenev1.Actor | None = None

        self._session = weakref.ref(_bascenev1.getsession())

        # Preloaded data for actors, maps, etc; indexed by type.
        self.preloads: dict[type, Any] = {}

        # Hopefully can eventually kill this; activities should
        # validate/store whatever settings they need at init time
        # (in a more type-safe way).
        self.settings_raw = settings

        self._has_transitioned_in = False
        self._has_begun = False
        self._has_ended = False
        self._activity_death_check_timer: bascenev1.AppTimer | None = None
        self._expired = False
        self._delay_delete_players: list[PlayerT] = []
        self._delay_delete_teams: list[TeamT] = []
        self._players_that_left: list[weakref.ref[PlayerT]] = []
        self._teams_that_left: list[weakref.ref[TeamT]] = []
        self._transitioning_out = False

        # A handy place to put most actors; this list is pruned of dead
        # actors regularly and these actors are insta-killed as the activity
        # is dying.
        self._actor_refs: list[bascenev1.Actor] = []
        self._actor_weak_refs: list[weakref.ref[bascenev1.Actor]] = []
        self._last_prune_dead_actors_time = babase.apptime()
        self._prune_dead_actors_timer: bascenev1.Timer | None = None

        self.teams = []
        self.players = []

        self.lobby = None
        self._stats: bascenev1.Stats | None = None
        self._customdata: dict | None = {}

    def __del__(self) -> None:
        # If the activity has been run then we should have already cleaned
        # it up, but we still need to run expire calls for un-run activities.
        if not self._expired:
            with babase.ContextRef.empty():
                self._expire()

        # Inform our owner that we officially kicked the bucket.
        if self._transitioning_out:
            session = self._session()
            if session is not None:
                babase.pushcall(
                    babase.Call(
                        session.transitioning_out_activity_was_freed,
                        self.can_show_ad_on_death,
                    )
                )

    @property
    def context(self) -> bascenev1.ContextRef:
        """A context-ref pointing at this activity."""
        return self._activity_data.context()

    @property
    def globalsnode(self) -> bascenev1.Node:
        """The 'globals' bascenev1.Node for the activity. This contains various
        global controls and values.
        """
        node = self._globalsnode
        if not node:
            raise babase.NodeNotFoundError()
        return node

    @property
    def stats(self) -> bascenev1.Stats:
        """The stats instance accessible while the activity is running.

        If access is attempted before or after, raises a
        bascenev1.NotFoundError.
        """
        if self._stats is None:
            raise babase.NotFoundError()
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
    def playertype(self) -> type[PlayerT]:
        """The type of bascenev1.Player this Activity is using."""
        return self._playertype

    @property
    def teamtype(self) -> type[TeamT]:
        """The type of bascenev1.Team this Activity is using."""
        return self._teamtype

    def set_has_ended(self, val: bool) -> None:
        """(internal)"""
        self._has_ended = val

    def expire(self) -> None:
        """Begin the process of tearing down the activity.

        (internal)
        """

        # Create an app-timer that watches a weak-ref of this activity
        # and reports any lingering references keeping it alive.
        # We store the timer on the activity so as soon as the activity dies
        # it gets cleaned up.
        with babase.ContextRef.empty():
            ref = weakref.ref(self)
            self._activity_death_check_timer = babase.AppTimer(
                5.0,
                babase.Call(self._check_activity_death, ref, [0]),
                repeat=True,
            )

        # Run _expire in an empty context; nothing should be happening in
        # there except deleting things which requires no context.
        # (plus, _expire() runs in the destructor for un-run activities
        # and we can't properly provide context in that situation anyway; might
        # as well be consistent).
        if not self._expired:
            with babase.ContextRef.empty():
                self._expire()
        else:
            raise RuntimeError(
                f'destroy() called when already expired for {self}.'
            )

    def retain_actor(self, actor: bascenev1.Actor) -> None:
        """Add a strong-reference to a bascenev1.Actor to this Activity.

        The reference will be lazily released once bascenev1.Actor.exists()
        returns False for the Actor. The bascenev1.Actor.autoretain() method
        is a convenient way to access this same functionality.
        """
        if __debug__:
            from bascenev1._actor import Actor

            assert isinstance(actor, Actor)
        self._actor_refs.append(actor)

    def add_actor_weak_ref(self, actor: bascenev1.Actor) -> None:
        """Add a weak-reference to a bascenev1.Actor to the bascenev1.Activity.

        (called by the bascenev1.Actor base class)
        """
        if __debug__:
            from bascenev1._actor import Actor

            assert isinstance(actor, Actor)
        self._actor_weak_refs.append(weakref.ref(actor))

    @property
    def session(self) -> bascenev1.Session:
        """The bascenev1.Session this bascenev1.Activity belongs to.

        Raises a babase.SessionNotFoundError if the Session no longer exists.
        """
        session = self._session()
        if session is None:
            raise babase.SessionNotFoundError()
        return session

    def on_player_join(self, player: PlayerT) -> None:
        """Called when a new bascenev1.Player has joined the Activity.

        (including the initial set of Players)
        """

    def on_player_leave(self, player: PlayerT) -> None:
        """Called when a bascenev1.Player is leaving the Activity."""

    def on_team_join(self, team: TeamT) -> None:
        """Called when a new bascenev1.Team joins the Activity.

        (including the initial set of Teams)
        """

    def on_team_leave(self, team: TeamT) -> None:
        """Called when a bascenev1.Team leaves the Activity."""

    def on_transition_in(self) -> None:
        """Called when the Activity is first becoming visible.

        Upon this call, the Activity should fade in backgrounds,
        start playing music, etc. It does not yet have access to players
        or teams, however. They remain owned by the previous Activity
        up until bascenev1.Activity.on_begin() is called.
        """

    def on_transition_out(self) -> None:
        """Called when your activity begins transitioning out.

        Note that this may happen at any time even if bascenev1.Activity.end()
        has not been called.
        """

    def on_begin(self) -> None:
        """Called once the previous Activity has finished transitioning out.

        At this point the activity's initial players and teams are filled in
        and it should begin its actual game logic.
        """

    def handlemessage(self, msg: Any) -> Any:
        """General message handling; can be passed any message object."""
        del msg  # Unused arg.
        return UNHANDLED

    def has_transitioned_in(self) -> bool:
        """Return whether bascenev1.Activity.on_transition_in() has run."""
        return self._has_transitioned_in

    def has_begun(self) -> bool:
        """Return whether bascenev1.Activity.on_begin() has run."""
        return self._has_begun

    def has_ended(self) -> bool:
        """Return whether the activity has commenced ending."""
        return self._has_ended

    def is_transitioning_out(self) -> bool:
        """Return whether bascenev1.Activity.on_transition_out() has run."""
        return self._transitioning_out

    def transition_in(self, prev_globals: bascenev1.Node | None) -> None:
        """Called by Session to kick off transition-in.

        (internal)
        """
        assert not self._has_transitioned_in
        self._has_transitioned_in = True

        # Set up the globals node based on our settings.
        with self.context:
            glb = self._globalsnode = _bascenev1.newnode('globals')

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
                    prev_globals.vr_overlay_center_enabled
                )

            # If they want to inherit tint from the previous self.
            if self.inherits_tint and prev_globals is not None:
                glb.tint = prev_globals.tint
                glb.vignette_outer = prev_globals.vignette_outer
                glb.vignette_inner = prev_globals.vignette_inner

            # Start pruning our various things periodically.
            self._prune_dead_actors()
            self._prune_dead_actors_timer = _bascenev1.Timer(
                5.17, self._prune_dead_actors, repeat=True
            )

            _bascenev1.timer(13.3, self._prune_delay_deletes, repeat=True)

            # Also start our low-level scene running.
            self._activity_data.start()

            try:
                self.on_transition_in()
            except Exception:
                logging.exception('Error in on_transition_in for %s.', self)

        # Tell the C++ layer that this activity is the main one, so it uses
        # settings from our globals, directs various events to us, etc.
        self._activity_data.make_foreground()

    def transition_out(self) -> None:
        """Called by the Session to start us transitioning out."""
        assert not self._transitioning_out
        self._transitioning_out = True
        with self.context:
            try:
                self.on_transition_out()
            except Exception:
                logging.exception('Error in on_transition_out for %s.', self)

    def begin(self, session: bascenev1.Session) -> None:
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
        with self.context:
            # Note: do we want to catch errors here?
            # Currently I believe we wind up canceling the
            # activity launch; just wanna be sure that is intentional.
            self.on_begin()

    def end(
        self, results: Any = None, delay: float = 0.0, force: bool = False
    ) -> None:
        """Commences Activity shutdown and delivers results to the Session.

        'delay' is the time delay before the Activity actually ends
        (in seconds). Further calls to end() will be ignored up until
        this time, unless 'force' is True, in which case the new results
        will replace the old.
        """

        # Ask the session to end us.
        self.session.end_activity(self, results, delay, force)

    def create_player(self, sessionplayer: bascenev1.SessionPlayer) -> PlayerT:
        """Create the Player instance for this Activity.

        Subclasses can override this if the activity's player class
        requires a custom constructor; otherwise it will be called with
        no args. Note that the player object should not be used at this
        point as it is not yet fully wired up; wait for
        bascenev1.Activity.on_player_join() for that.
        """
        del sessionplayer  # Unused.
        player = self._playertype()
        return player

    def create_team(self, sessionteam: bascenev1.SessionTeam) -> TeamT:
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

    def add_player(self, sessionplayer: bascenev1.SessionPlayer) -> None:
        """(internal)"""
        assert sessionplayer.sessionteam is not None
        sessionplayer.resetinput()
        sessionteam = sessionplayer.sessionteam
        assert sessionplayer in sessionteam.players
        team = sessionteam.activityteam
        assert team is not None
        sessionplayer.setactivity(self)
        with self.context:
            sessionplayer.activityplayer = player = self.create_player(
                sessionplayer
            )
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
                logging.exception('Error in on_player_join for %s.', self)

    def remove_player(self, sessionplayer: bascenev1.SessionPlayer) -> None:
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

        # This should allow our bascenev1.Player instance to die.
        # Complain if that doesn't happen.
        # verify_object_death(player)

        with self.context:
            try:
                self.on_player_leave(player)
            except Exception:
                logging.exception('Error in on_player_leave for %s.', self)
            try:
                player.leave()
            except Exception:
                logging.exception('Error on leave for %s in %s.', player, self)

            self._reset_session_player_for_no_activity(sessionplayer)

        # Add the player to a list to keep it around for a while. This is
        # to discourage logic from firing on player object death, which
        # may not happen until activity end if something is holding refs
        # to it.
        self._delay_delete_players.append(player)
        self._players_that_left.append(weakref.ref(player))

    def add_team(self, sessionteam: bascenev1.SessionTeam) -> None:
        """Add a team to the Activity

        (internal)
        """
        assert not self.expired

        with self.context:
            sessionteam.activityteam = team = self.create_team(sessionteam)
            team.postinit(sessionteam)
            self.teams.append(team)
            try:
                self.on_team_join(team)
            except Exception:
                logging.exception('Error in on_team_join for %s.', self)

    def remove_team(self, sessionteam: bascenev1.SessionTeam) -> None:
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

        with self.context:
            # Make a decent attempt to persevere if user code breaks.
            try:
                self.on_team_leave(team)
            except Exception:
                logging.exception('Error in on_team_leave for %s.', self)
            try:
                team.leave()
            except Exception:
                logging.exception('Error on leave for %s in %s.', team, self)

            sessionteam.activityteam = None

        # Add the team to a list to keep it around for a while. This is
        # to discourage logic from firing on team object death, which
        # may not happen until activity end if something is holding refs
        # to it.
        self._delay_delete_teams.append(team)
        self._teams_that_left.append(weakref.ref(team))

    def _reset_session_player_for_no_activity(
        self, sessionplayer: bascenev1.SessionPlayer
    ) -> None:
        # Let's be extra-defensive here: killing a node/input-call/etc
        # could trigger user-code resulting in errors, but we would still
        # like to complete the reset if possible.
        try:
            sessionplayer.setnode(None)
        except Exception:
            logging.exception(
                'Error resetting SessionPlayer node on %s for %s.',
                sessionplayer,
                self,
            )
        try:
            sessionplayer.resetinput()
        except Exception:
            logging.exception(
                'Error resetting SessionPlayer input on %s for %s.',
                sessionplayer,
                self,
            )

        # These should never fail I think...
        sessionplayer.setactivity(None)
        sessionplayer.activityplayer = None

    # noinspection PyUnresolvedReferences
    def _setup_player_and_team_types(self) -> None:
        """Pull player and team types from our typing.Generic params."""

        # TODO: There are proper calls for pulling these in Python 3.8;
        # should update this code when we adopt that.
        # NOTE: If we get Any as PlayerT or TeamT (generally due
        # to no generic params being passed) we automatically use the
        # base class types, but also warn the user since this will mean
        # less type safety for that class. (its better to pass the base
        # player/team types explicitly vs. having them be Any)
        if not TYPE_CHECKING:
            self._playertype = type(self).__orig_bases__[-1].__args__[0]
            if not isinstance(self._playertype, type):
                self._playertype = Player
                print(
                    f'ERROR: {type(self)} was not passed a Player'
                    f' type argument; please explicitly pass bascenev1.Player'
                    f' if you do not want to override it.'
                )
            self._teamtype = type(self).__orig_bases__[-1].__args__[1]
            if not isinstance(self._teamtype, type):
                self._teamtype = Team
                print(
                    f'ERROR: {type(self)} was not passed a Team'
                    f' type argument; please explicitly pass bascenev1.Team'
                    f' if you do not want to override it.'
                )
        assert issubclass(self._playertype, Player)
        assert issubclass(self._teamtype, Team)

    @classmethod
    def _check_activity_death(
        cls, activity_ref: weakref.ref[Activity], counter: list[int]
    ) -> None:
        """Sanity check to make sure an Activity was destroyed properly.

        Receives a weakref to a bascenev1.Activity which should have torn
        itself down due to no longer being referenced anywhere. Will complain
        and/or print debugging info if the Activity still exists.
        """
        try:
            activity = activity_ref()
            print(
                'ERROR: Activity is not dying when expected:',
                activity,
                '(warning ' + str(counter[0] + 1) + ')',
            )
            print(
                'This means something is still strong-referencing it.\n'
                'Check out methods such as efro.debug.printrefs() to'
                ' help debug this sort of thing.'
            )
            # Note: no longer calling gc.get_referrers() here because it's
            # usage can bork stuff. (see notes at top of efro.debug)
            counter[0] += 1
            if counter[0] == 4:
                print('Killing app due to stuck activity... :-(')
                babase.quit()

        except Exception:
            logging.exception('Error on _check_activity_death.')

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
            logging.exception('Error in Activity on_expire() for %s.', self)

        try:
            self._customdata = None
        except Exception:
            logging.exception('Error clearing customdata for %s.', self)

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
            logging.exception('Error expiring _activity_data for %s.', self)

    def _expire_actors(self) -> None:
        # Expire all Actors.
        for actor_ref in self._actor_weak_refs:
            actor = actor_ref()
            if actor is not None:
                babase.verify_object_death(actor)
                try:
                    actor.on_expire()
                except Exception:
                    logging.exception(
                        'Error in Actor.on_expire() for %s.', actor_ref()
                    )

    def _expire_players(self) -> None:
        # Issue warnings for any players that left the game but don't
        # get freed soon.
        for ex_player in (p() for p in self._players_that_left):
            if ex_player is not None:
                babase.verify_object_death(ex_player)

        for player in self.players:
            # This should allow our bascenev1.Player instance to be freed.
            # Complain if that doesn't happen.
            babase.verify_object_death(player)

            try:
                player.expire()
            except Exception:
                logging.exception('Error expiring %s.', player)

            # Reset the SessionPlayer to a not-in-an-activity state.
            try:
                sessionplayer = player.sessionplayer
                self._reset_session_player_for_no_activity(sessionplayer)
            except babase.SessionPlayerNotFoundError:
                # Conceivably, someone could have held on to a Player object
                # until now whos underlying SessionPlayer left long ago...
                pass
            except Exception:
                logging.exception('Error expiring %s.', player)

    def _expire_teams(self) -> None:
        # Issue warnings for any teams that left the game but don't
        # get freed soon.
        for ex_team in (p() for p in self._teams_that_left):
            if ex_team is not None:
                babase.verify_object_death(ex_team)

        for team in self.teams:
            # This should allow our bascenev1.Team instance to die.
            # Complain if that doesn't happen.
            babase.verify_object_death(team)

            try:
                team.expire()
            except Exception:
                logging.exception('Error expiring %s.', team)

            try:
                sessionteam = team.sessionteam
                sessionteam.activityteam = None
            except babase.SessionTeamNotFoundError:
                # It is expected that Team objects may last longer than
                # the SessionTeam they came from (game objects may hold
                # team references past the point at which the underlying
                # player/team has left the game)
                pass
            except Exception:
                logging.exception('Error expiring Team %s.', team)

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
        self._last_prune_dead_actors_time = babase.apptime()

        # Prune our strong refs when the Actor's exists() call gives False
        self._actor_refs = [a for a in self._actor_refs if a.exists()]

        # Prune our weak refs once the Actor object has been freed.
        self._actor_weak_refs = [
            a for a in self._actor_weak_refs if a() is not None
        ]
