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
"""Provides GameActivity class."""
# pylint: disable=too-many-lines

from __future__ import annotations

import random
from typing import TYPE_CHECKING, TypeVar

from ba._activity import Activity
from ba._score import ScoreConfig
from ba._lang import Lstr
from ba._messages import PlayerDiedMessage, StandMessage
from ba._error import NotFoundError, print_error, print_exception
from ba._general import Call, WeakCall
from ba._player import PlayerInfo
from ba import _map
import _ba

if TYPE_CHECKING:
    from typing import (List, Optional, Dict, Type, Any, Callable, Sequence,
                        Tuple, Union)
    from bastd.actor.playerspaz import PlayerSpaz
    from bastd.actor.bomb import TNTSpawner
    import ba

PlayerType = TypeVar('PlayerType', bound='ba.Player')
TeamType = TypeVar('TeamType', bound='ba.Team')


class GameActivity(Activity[PlayerType, TeamType]):
    """Common base class for all game ba.Activities.

    category: Gameplay Classes
    """
    # pylint: disable=too-many-public-methods

    # Tips to be presented to the user at the start of the game.
    tips: List[Union[str, ba.GameTip]] = []

    # Default getname() will return this if not None.
    name: Optional[str] = None

    # Default get_description() will return this if not None.
    description: Optional[str] = None

    # Default get_available_settings() will return this if not None.
    available_settings: Optional[List[ba.Setting]] = None

    # Default getscoreconfig() will return this if not None.
    scoreconfig: Optional[ba.ScoreConfig] = None

    # Override some defaults.
    allow_pausing = True
    allow_kick_idle_players = True

    # Whether to show points for kills.
    show_kill_points = True

    # If not None, the music type that should play in on_transition_in()
    # (unless overridden by the map).
    default_music: Optional[ba.MusicType] = None

    @classmethod
    def create_settings_ui(
        cls,
        sessiontype: Type[ba.Session],
        settings: Optional[dict],
        completion_call: Callable[[Optional[dict]], None],
    ) -> None:
        """Launch an in-game UI to configure settings for a game type.

        'sessiontype' should be the ba.Session class the game will be used in.

        'settings' should be an existing settings dict (implies 'edit'
          ui mode) or None (implies 'add' ui mode).

        'completion_call' will be called with a filled-out settings dict on
          success or None on cancel.

        Generally subclasses don't need to override this; if they override
        ba.GameActivity.get_available_settings() and
        ba.GameActivity.get_supported_maps() they can just rely on
        the default implementation here which calls those methods.
        """
        delegate = _ba.app.delegate
        assert delegate is not None
        delegate.create_default_game_settings_ui(cls, sessiontype, settings,
                                                 completion_call)

    @classmethod
    def getscoreconfig(cls) -> ba.ScoreConfig:
        """Return info about game scoring setup; can be overridden by games."""
        return (cls.scoreconfig
                if cls.scoreconfig is not None else ScoreConfig())

    @classmethod
    def getname(cls) -> str:
        """Return a str name for this game type.

        This default implementation simply returns the 'name' class attr.
        """
        return cls.name if cls.name is not None else 'Untitled Game'

    @classmethod
    def get_display_string(cls, settings: Optional[Dict] = None) -> ba.Lstr:
        """Return a descriptive name for this game/settings combo.

        Subclasses should override getname(); not this.
        """
        name = Lstr(translate=('gameNames', cls.getname()))

        # A few substitutions for 'Epic', 'Solo' etc. modes.
        # FIXME: Should provide a way for game types to define filters of
        #  their own and should not rely on hard-coded settings names.
        if settings is not None:
            if 'Solo Mode' in settings and settings['Solo Mode']:
                name = Lstr(resource='soloNameFilterText',
                            subs=[('${NAME}', name)])
            if 'Epic Mode' in settings and settings['Epic Mode']:
                name = Lstr(resource='epicNameFilterText',
                            subs=[('${NAME}', name)])

        return name

    @classmethod
    def get_team_display_string(cls, name: str) -> ba.Lstr:
        """Given a team name, returns a localized version of it."""
        return Lstr(translate=('teamNames', name))

    @classmethod
    def get_description(cls, sessiontype: Type[ba.Session]) -> str:
        """Get a str description of this game type.

        The default implementation simply returns the 'description' class var.
        Classes which want to change their description depending on the session
        can override this method.
        """
        del sessiontype  # Unused arg.
        return cls.description if cls.description is not None else ''

    @classmethod
    def get_description_display_string(
            cls, sessiontype: Type[ba.Session]) -> ba.Lstr:
        """Return a translated version of get_description().

        Sub-classes should override get_description(); not this.
        """
        description = cls.get_description(sessiontype)
        return Lstr(translate=('gameDescriptions', description))

    @classmethod
    def get_available_settings(
            cls, sessiontype: Type[ba.Session]) -> List[ba.Setting]:
        """Return a list of settings relevant to this game type when
        running under the provided session type.
        """
        del sessiontype  # Unused arg.
        return [] if cls.available_settings is None else cls.available_settings

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[ba.Session]) -> List[str]:
        """
        Called by the default ba.GameActivity.create_settings_ui()
        implementation; should return a list of map names valid
        for this game-type for the given ba.Session type.
        """
        del sessiontype  # Unused arg.
        return _map.getmaps('melee')

    @classmethod
    def get_settings_display_string(cls, config: Dict[str, Any]) -> ba.Lstr:
        """Given a game config dict, return a short description for it.

        This is used when viewing game-lists or showing what game
        is up next in a series.
        """
        name = cls.get_display_string(config['settings'])

        # In newer configs, map is in settings; it used to be in the
        # config root.
        if 'map' in config['settings']:
            sval = Lstr(value='${NAME} @ ${MAP}',
                        subs=[('${NAME}', name),
                              ('${MAP}',
                               _map.get_map_display_string(
                                   _map.get_filtered_map_name(
                                       config['settings']['map'])))])
        elif 'map' in config:
            sval = Lstr(value='${NAME} @ ${MAP}',
                        subs=[('${NAME}', name),
                              ('${MAP}',
                               _map.get_map_display_string(
                                   _map.get_filtered_map_name(config['map'])))
                              ])
        else:
            print('invalid game config - expected map entry under settings')
            sval = Lstr(value='???')
        return sval

    @classmethod
    def supports_session_type(cls, sessiontype: Type[ba.Session]) -> bool:
        """Return whether this game supports the provided Session type."""
        from ba._multiteamsession import MultiTeamSession

        # By default, games support any versus mode
        return issubclass(sessiontype, MultiTeamSession)

    def __init__(self, settings: dict):
        """Instantiate the Activity."""
        super().__init__(settings)

        # Holds some flattened info about the player set at the point
        # when on_begin() is called.
        self.initialplayerinfos: Optional[List[ba.PlayerInfo]] = None

        # Go ahead and get our map loading.
        self._map_type = _map.get_map_class(self._calc_map_name(settings))

        self._spawn_sound = _ba.getsound('spawn')
        self._map_type.preload()
        self._map: Optional[ba.Map] = None
        self._powerup_drop_timer: Optional[ba.Timer] = None
        self._tnt_spawners: Optional[Dict[int, TNTSpawner]] = None
        self._tnt_drop_timer: Optional[ba.Timer] = None
        self._game_scoreboard_name_text: Optional[ba.Actor] = None
        self._game_scoreboard_description_text: Optional[ba.Actor] = None
        self._standard_time_limit_time: Optional[int] = None
        self._standard_time_limit_timer: Optional[ba.Timer] = None
        self._standard_time_limit_text: Optional[ba.NodeActor] = None
        self._standard_time_limit_text_input: Optional[ba.NodeActor] = None
        self._tournament_time_limit: Optional[int] = None
        self._tournament_time_limit_timer: Optional[ba.Timer] = None
        self._tournament_time_limit_title_text: Optional[ba.NodeActor] = None
        self._tournament_time_limit_text: Optional[ba.NodeActor] = None
        self._tournament_time_limit_text_input: Optional[ba.NodeActor] = None
        self._zoom_message_times: Dict[int, float] = {}
        self._is_waiting_for_continue = False

        self._continue_cost = _ba.get_account_misc_read_val(
            'continueStartCost', 25)
        self._continue_cost_mult = _ba.get_account_misc_read_val(
            'continuesMult', 2)
        self._continue_cost_offset = _ba.get_account_misc_read_val(
            'continuesOffset', 0)

    @property
    def map(self) -> ba.Map:
        """The map being used for this game.

        Raises a ba.NotFoundError if the map does not currently exist.
        """
        if self._map is None:
            raise NotFoundError
        return self._map

    def get_instance_display_string(self) -> ba.Lstr:
        """Return a name for this particular game instance."""
        return self.get_display_string(self.settings_raw)

    def get_instance_scoreboard_display_string(self) -> ba.Lstr:
        """Return a name for this particular game instance.

        This name is used above the game scoreboard in the corner
        of the screen, so it should be as concise as possible.
        """
        # If we're in a co-op session, use the level name.
        # FIXME: Should clean this up.
        try:
            from ba._coopsession import CoopSession
            if isinstance(self.session, CoopSession):
                campaign = self.session.campaign
                assert campaign is not None
                return campaign.getlevel(
                    self.session.campaign_level_name).displayname
        except Exception:
            print_error('error getting campaign level name')
        return self.get_instance_display_string()

    def get_instance_description(self) -> Union[str, Sequence]:
        """Return a description for this game instance, in English.

        This is shown in the center of the screen below the game name at the
        start of a game. It should start with a capital letter and end with a
        period, and can be a bit more verbose than the version returned by
        get_instance_description_short().

        Note that translation is applied by looking up the specific returned
        value as a key, so the number of returned variations should be limited;
        ideally just one or two. To include arbitrary values in the
        description, you can return a sequence of values in the following
        form instead of just a string:

        # This will give us something like 'Score 3 goals.' in English
        # and can properly translate to 'Anota 3 goles.' in Spanish.
        # If we just returned the string 'Score 3 Goals' here, there would
        # have to be a translation entry for each specific number. ew.
        return ['Score ${ARG1} goals.', self.settings_raw['Score to Win']]

        This way the first string can be consistently translated, with any arg
        values then substituted into the result. ${ARG1} will be replaced with
        the first value, ${ARG2} with the second, etc.
        """
        return self.get_description(type(self.session))

    def get_instance_description_short(self) -> Union[str, Sequence]:
        """Return a short description for this game instance in English.

        This description is used above the game scoreboard in the
        corner of the screen, so it should be as concise as possible.
        It should be lowercase and should not contain periods or other
        punctuation.

        Note that translation is applied by looking up the specific returned
        value as a key, so the number of returned variations should be limited;
        ideally just one or two. To include arbitrary values in the
        description, you can return a sequence of values in the following form
        instead of just a string:

        # This will give us something like 'score 3 goals' in English
        # and can properly translate to 'anota 3 goles' in Spanish.
        # If we just returned the string 'score 3 goals' here, there would
        # have to be a translation entry for each specific number. ew.
        return ['score ${ARG1} goals', self.settings_raw['Score to Win']]

        This way the first string can be consistently translated, with any arg
        values then substituted into the result. ${ARG1} will be replaced
        with the first value, ${ARG2} with the second, etc.

        """
        return ''

    def on_transition_in(self) -> None:
        super().on_transition_in()

        # Make our map.
        self._map = self._map_type()

        # Give our map a chance to override the music.
        # (for happy-thoughts and other such themed maps)
        map_music = self._map_type.get_music_type()
        music = map_music if map_music is not None else self.default_music

        if music is not None:
            from ba import _music
            _music.setmusic(music)

    def on_continue(self) -> None:
        """
        This is called if a game supports and offers a continue and the player
        accepts.  In this case the player should be given an extra life or
        whatever is relevant to keep the game going.
        """

    def _continue_choice(self, do_continue: bool) -> None:
        self._is_waiting_for_continue = False
        if self.has_ended():
            return
        with _ba.Context(self):
            if do_continue:
                _ba.playsound(_ba.getsound('shieldUp'))
                _ba.playsound(_ba.getsound('cashRegister'))
                _ba.add_transaction({
                    'type': 'CONTINUE',
                    'cost': self._continue_cost
                })
                _ba.run_transactions()
                self._continue_cost = (
                    self._continue_cost * self._continue_cost_mult +
                    self._continue_cost_offset)
                self.on_continue()
            else:
                self.end_game()

    def is_waiting_for_continue(self) -> bool:
        """Returns whether or not this activity is currently waiting for the
        player to continue (or timeout)"""
        return self._is_waiting_for_continue

    def continue_or_end_game(self) -> None:
        """If continues are allowed, prompts the player to purchase a continue
        and calls either end_game or continue_game depending on the result"""
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=cyclic-import
        from bastd.ui.continues import ContinuesWindow
        from ba._coopsession import CoopSession
        from ba._enums import TimeType

        try:
            if _ba.get_account_misc_read_val('enableContinues', False):
                session = self.session

                # We only support continuing in non-tournament games.
                tournament_id = session.tournament_id
                if tournament_id is None:

                    # We currently only support continuing in sequential
                    # co-op campaigns.
                    if isinstance(session, CoopSession):
                        assert session.campaign is not None
                        if session.campaign.sequential:
                            gnode = self.globalsnode

                            # Only attempt this if we're not currently paused
                            # and there appears to be no UI.
                            if (not gnode.paused
                                    and not _ba.app.ui.has_main_menu_window()):
                                self._is_waiting_for_continue = True
                                with _ba.Context('ui'):
                                    _ba.timer(
                                        0.5,
                                        lambda: ContinuesWindow(
                                            self,
                                            self._continue_cost,
                                            continue_call=WeakCall(
                                                self._continue_choice, True),
                                            cancel_call=WeakCall(
                                                self._continue_choice, False)),
                                        timetype=TimeType.REAL)
                                return

        except Exception:
            print_exception('Error handling continues.')

        self.end_game()

    def on_begin(self) -> None:
        from ba._analytics import game_begin_analytics
        super().on_begin()

        game_begin_analytics()

        # We don't do this in on_transition_in because it may depend on
        # players/teams which aren't available until now.
        _ba.timer(0.001, self._show_scoreboard_info)
        _ba.timer(1.0, self._show_info)
        _ba.timer(2.5, self._show_tip)

        # Store some basic info about players present at start time.
        self.initialplayerinfos = [
            PlayerInfo(name=p.getname(full=True), character=p.character)
            for p in self.players
        ]

        # Sort this by name so high score lists/etc will be consistent
        # regardless of player join order.
        self.initialplayerinfos.sort(key=lambda x: x.name)

        # If this is a tournament, query info about it such as how much
        # time is left.
        tournament_id = self.session.tournament_id
        if tournament_id is not None:
            _ba.tournament_query(
                args={
                    'tournamentIDs': [tournament_id],
                    'source': 'in-game time remaining query'
                },
                callback=WeakCall(self._on_tournament_query_response),
            )

    def _on_tournament_query_response(self, data: Optional[Dict[str,
                                                                Any]]) -> None:
        from ba._account import cache_tournament_info
        if data is not None:
            data_t = data['t']  # This used to be the whole payload.

            # Keep our cached tourney info up to date
            cache_tournament_info(data_t)
            self._setup_tournament_time_limit(
                max(5, data_t[0]['timeRemaining']))

    def on_player_join(self, player: PlayerType) -> None:
        super().on_player_join(player)

        # By default, just spawn a dude.
        self.spawn_player(player)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, PlayerDiedMessage):
            # pylint: disable=cyclic-import
            from bastd.actor.spaz import Spaz

            player = msg.getplayer(self.playertype)
            killer = msg.getkillerplayer(self.playertype)

            # Inform our stats of the demise.
            self.stats.player_was_killed(player,
                                         killed=msg.killed,
                                         killer=killer)

            # Award the killer points if he's on a different team.
            # FIXME: This should not be linked to Spaz actors.
            # (should move get_death_points to Actor or make it a message)
            if killer and killer.team is not player.team:
                assert isinstance(killer.actor, Spaz)
                pts, importance = killer.actor.get_death_points(msg.how)
                if not self.has_ended():
                    self.stats.player_scored(killer,
                                             pts,
                                             kill=True,
                                             victim_player=player,
                                             importance=importance,
                                             showpoints=self.show_kill_points)
        else:
            return super().handlemessage(msg)
        return None

    def _show_scoreboard_info(self) -> None:
        """Create the game info display.

        This is the thing in the top left corner showing the name
        and short description of the game.
        """
        # pylint: disable=too-many-locals
        from ba._freeforallsession import FreeForAllSession
        from ba._gameutils import animate
        from ba._nodeactor import NodeActor
        sb_name = self.get_instance_scoreboard_display_string()

        # The description can be either a string or a sequence with args
        # to swap in post-translation.
        sb_desc_in = self.get_instance_description_short()
        sb_desc_l: Sequence
        if isinstance(sb_desc_in, str):
            sb_desc_l = [sb_desc_in]  # handle simple string case
        else:
            sb_desc_l = sb_desc_in
        if not isinstance(sb_desc_l[0], str):
            raise TypeError('Invalid format for instance description.')

        is_empty = (sb_desc_l[0] == '')
        subs = []
        for i in range(len(sb_desc_l) - 1):
            subs.append(('${ARG' + str(i + 1) + '}', str(sb_desc_l[i + 1])))
        translation = Lstr(translate=('gameDescriptions', sb_desc_l[0]),
                           subs=subs)
        sb_desc = translation
        vrmode = _ba.app.vr_mode
        yval = -34 if is_empty else -20
        yval -= 16
        sbpos = ((15, yval) if isinstance(self.session, FreeForAllSession) else
                 (15, yval))
        self._game_scoreboard_name_text = NodeActor(
            _ba.newnode('text',
                        attrs={
                            'text': sb_name,
                            'maxwidth': 300,
                            'position': sbpos,
                            'h_attach': 'left',
                            'vr_depth': 10,
                            'v_attach': 'top',
                            'v_align': 'bottom',
                            'color': (1.0, 1.0, 1.0, 1.0),
                            'shadow': 1.0 if vrmode else 0.6,
                            'flatness': 1.0 if vrmode else 0.5,
                            'scale': 1.1
                        }))

        assert self._game_scoreboard_name_text.node
        animate(self._game_scoreboard_name_text.node, 'opacity', {
            0: 0.0,
            1.0: 1.0
        })

        descpos = (((17, -44 +
                     10) if isinstance(self.session, FreeForAllSession) else
                    (17, -44 + 10)))
        self._game_scoreboard_description_text = NodeActor(
            _ba.newnode(
                'text',
                attrs={
                    'text': sb_desc,
                    'maxwidth': 480,
                    'position': descpos,
                    'scale': 0.7,
                    'h_attach': 'left',
                    'v_attach': 'top',
                    'v_align': 'top',
                    'shadow': 1.0 if vrmode else 0.7,
                    'flatness': 1.0 if vrmode else 0.8,
                    'color': (1, 1, 1, 1) if vrmode else (0.9, 0.9, 0.9, 1.0)
                }))

        assert self._game_scoreboard_description_text.node
        animate(self._game_scoreboard_description_text.node, 'opacity', {
            0: 0.0,
            1.0: 1.0
        })

    def _show_info(self) -> None:
        """Show the game description."""
        from ba._gameutils import animate
        from bastd.actor.zoomtext import ZoomText
        name = self.get_instance_display_string()
        ZoomText(name,
                 maxwidth=800,
                 lifespan=2.5,
                 jitter=2.0,
                 position=(0, 180),
                 flash=False,
                 color=(0.93 * 1.25, 0.9 * 1.25, 1.0 * 1.25),
                 trailcolor=(0.15, 0.05, 1.0, 0.0)).autoretain()
        _ba.timer(0.2, Call(_ba.playsound, _ba.getsound('gong')))

        # The description can be either a string or a sequence with args
        # to swap in post-translation.
        desc_in = self.get_instance_description()
        desc_l: Sequence
        if isinstance(desc_in, str):
            desc_l = [desc_in]  # handle simple string case
        else:
            desc_l = desc_in
        if not isinstance(desc_l[0], str):
            raise TypeError('Invalid format for instance description')
        subs = []
        for i in range(len(desc_l) - 1):
            subs.append(('${ARG' + str(i + 1) + '}', str(desc_l[i + 1])))
        translation = Lstr(translate=('gameDescriptions', desc_l[0]),
                           subs=subs)

        # Do some standard filters (epic mode, etc).
        if self.settings_raw.get('Epic Mode', False):
            translation = Lstr(resource='epicDescriptionFilterText',
                               subs=[('${DESCRIPTION}', translation)])
        vrmode = _ba.app.vr_mode
        dnode = _ba.newnode('text',
                            attrs={
                                'v_attach': 'center',
                                'h_attach': 'center',
                                'h_align': 'center',
                                'color': (1, 1, 1, 1),
                                'shadow': 1.0 if vrmode else 0.5,
                                'flatness': 1.0 if vrmode else 0.5,
                                'vr_depth': -30,
                                'position': (0, 80),
                                'scale': 1.2,
                                'maxwidth': 700,
                                'text': translation
                            })
        cnode = _ba.newnode('combine',
                            owner=dnode,
                            attrs={
                                'input0': 1.0,
                                'input1': 1.0,
                                'input2': 1.0,
                                'size': 4
                            })
        cnode.connectattr('output', dnode, 'color')
        keys = {0.5: 0, 1.0: 1.0, 2.5: 1.0, 4.0: 0.0}
        animate(cnode, 'input3', keys)
        _ba.timer(4.0, dnode.delete)

    def _show_tip(self) -> None:
        # pylint: disable=too-many-locals
        from ba._gameutils import animate, GameTip
        from ba._enums import SpecialChar

        # If there's any tips left on the list, display one.
        if self.tips:
            tip = self.tips.pop(random.randrange(len(self.tips)))
            tip_title = Lstr(value='${A}:',
                             subs=[('${A}', Lstr(resource='tipText'))])
            icon: Optional[ba.Texture] = None
            sound: Optional[ba.Sound] = None
            if isinstance(tip, GameTip):
                icon = tip.icon
                sound = tip.sound
                tip = tip.text
                assert isinstance(tip, str)

            # Do a few substitutions.
            tip_lstr = Lstr(translate=('tips', tip),
                            subs=[('${PICKUP}',
                                   _ba.charstr(SpecialChar.TOP_BUTTON))])
            base_position = (75, 50)
            tip_scale = 0.8
            tip_title_scale = 1.2
            vrmode = _ba.app.vr_mode

            t_offs = -350.0
            tnode = _ba.newnode('text',
                                attrs={
                                    'text': tip_lstr,
                                    'scale': tip_scale,
                                    'maxwidth': 900,
                                    'position': (base_position[0] + t_offs,
                                                 base_position[1]),
                                    'h_align': 'left',
                                    'vr_depth': 300,
                                    'shadow': 1.0 if vrmode else 0.5,
                                    'flatness': 1.0 if vrmode else 0.5,
                                    'v_align': 'center',
                                    'v_attach': 'bottom'
                                })
            t2pos = (base_position[0] + t_offs - (20 if icon is None else 82),
                     base_position[1] + 2)
            t2node = _ba.newnode('text',
                                 owner=tnode,
                                 attrs={
                                     'text': tip_title,
                                     'scale': tip_title_scale,
                                     'position': t2pos,
                                     'h_align': 'right',
                                     'vr_depth': 300,
                                     'shadow': 1.0 if vrmode else 0.5,
                                     'flatness': 1.0 if vrmode else 0.5,
                                     'maxwidth': 140,
                                     'v_align': 'center',
                                     'v_attach': 'bottom'
                                 })
            if icon is not None:
                ipos = (base_position[0] + t_offs - 40, base_position[1] + 1)
                img = _ba.newnode('image',
                                  attrs={
                                      'texture': icon,
                                      'position': ipos,
                                      'scale': (50, 50),
                                      'opacity': 1.0,
                                      'vr_depth': 315,
                                      'color': (1, 1, 1),
                                      'absolute_scale': True,
                                      'attach': 'bottomCenter'
                                  })
                animate(img, 'opacity', {0: 0, 1.0: 1, 4.0: 1, 5.0: 0})
                _ba.timer(5.0, img.delete)
            if sound is not None:
                _ba.playsound(sound)

            combine = _ba.newnode('combine',
                                  owner=tnode,
                                  attrs={
                                      'input0': 1.0,
                                      'input1': 0.8,
                                      'input2': 1.0,
                                      'size': 4
                                  })
            combine.connectattr('output', tnode, 'color')
            combine.connectattr('output', t2node, 'color')
            animate(combine, 'input3', {0: 0, 1.0: 1, 4.0: 1, 5.0: 0})
            _ba.timer(5.0, tnode.delete)

    def end(self,
            results: Any = None,
            delay: float = 0.0,
            force: bool = False) -> None:
        from ba._gameresults import GameResults

        # If results is a standard team-game-results, associate it with us
        # so it can grab our score prefs.
        if isinstance(results, GameResults):
            results.set_game(self)

        # If we had a standard time-limit that had not expired, stop it so
        # it doesnt tick annoyingly.
        if (self._standard_time_limit_time is not None
                and self._standard_time_limit_time > 0):
            self._standard_time_limit_timer = None
            self._standard_time_limit_text = None

        # Ditto with tournament time limits.
        if (self._tournament_time_limit is not None
                and self._tournament_time_limit > 0):
            self._tournament_time_limit_timer = None
            self._tournament_time_limit_text = None
            self._tournament_time_limit_title_text = None

        super().end(results, delay, force)

    def end_game(self) -> None:
        """Tell the game to wrap up and call ba.Activity.end() immediately.

        This method should be overridden by subclasses. A game should always
        be prepared to end and deliver results, even if there is no 'winner'
        yet; this way things like the standard time-limit
        (ba.GameActivity.setup_standard_time_limit()) will work with the game.
        """
        print('WARNING: default end_game() implementation called;'
              ' your game should override this.')

    def respawn_player(self,
                       player: PlayerType,
                       respawn_time: Optional[float] = None) -> None:
        """
        Given a ba.Player, sets up a standard respawn timer,
        along with the standard counter display, etc.
        At the end of the respawn period spawn_player() will
        be called if the Player still exists.
        An explicit 'respawn_time' can optionally be provided
        (in seconds).
        """
        # pylint: disable=cyclic-import

        assert player
        if respawn_time is None:
            teamsize = len(player.team.players)
            if teamsize == 1:
                respawn_time = 3.0
            elif teamsize == 2:
                respawn_time = 5.0
            elif teamsize == 3:
                respawn_time = 6.0
            else:
                respawn_time = 7.0

        # If this standard setting is present, factor it in.
        if 'Respawn Times' in self.settings_raw:
            respawn_time *= self.settings_raw['Respawn Times']

        # We want whole seconds.
        assert respawn_time is not None
        respawn_time = round(max(1.0, respawn_time), 0)

        if player.actor and not self.has_ended():
            from bastd.actor.respawnicon import RespawnIcon
            player.customdata['respawn_timer'] = _ba.Timer(
                respawn_time, WeakCall(self.spawn_player_if_exists, player))
            player.customdata['respawn_icon'] = RespawnIcon(
                player, respawn_time)

    def spawn_player_if_exists(self, player: PlayerType) -> None:
        """
        A utility method which calls self.spawn_player() *only* if the
        ba.Player provided still exists; handy for use in timers and whatnot.

        There is no need to override this; just override spawn_player().
        """
        if player:
            self.spawn_player(player)

    def spawn_player(self, player: PlayerType) -> ba.Actor:
        """Spawn *something* for the provided ba.Player.

        The default implementation simply calls spawn_player_spaz().
        """
        assert player  # Dead references should never be passed as args.

        return self.spawn_player_spaz(player)

    def spawn_player_spaz(self,
                          player: PlayerType,
                          position: Sequence[float] = (0, 0, 0),
                          angle: float = None) -> PlayerSpaz:
        """Create and wire up a ba.PlayerSpaz for the provided ba.Player."""
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from ba import _math
        from ba._gameutils import animate
        from ba._coopsession import CoopSession
        from bastd.actor.playerspaz import PlayerSpaz
        name = player.getname()
        color = player.color
        highlight = player.highlight

        light_color = _math.normalized_color(color)
        display_color = _ba.safecolor(color, target_intensity=0.75)
        spaz = PlayerSpaz(color=color,
                          highlight=highlight,
                          character=player.character,
                          player=player)

        player.actor = spaz
        assert spaz.node

        # If this is co-op and we're on Courtyard or Runaround, add the
        # material that allows us to collide with the player-walls.
        # FIXME: Need to generalize this.
        if isinstance(self.session, CoopSession) and self.map.getname() in [
                'Courtyard', 'Tower D'
        ]:
            mat = self.map.preloaddata['collide_with_wall_material']
            assert isinstance(spaz.node.materials, tuple)
            assert isinstance(spaz.node.roller_materials, tuple)
            spaz.node.materials += (mat, )
            spaz.node.roller_materials += (mat, )

        spaz.node.name = name
        spaz.node.name_color = display_color
        spaz.connect_controls_to_player()

        # Move to the stand position and add a flash of light.
        spaz.handlemessage(
            StandMessage(
                position,
                angle if angle is not None else random.uniform(0, 360)))
        _ba.playsound(self._spawn_sound, 1, position=spaz.node.position)
        light = _ba.newnode('light', attrs={'color': light_color})
        spaz.node.connectattr('position', light, 'position')
        animate(light, 'intensity', {0: 0, 0.25: 1, 0.5: 0})
        _ba.timer(0.5, light.delete)
        return spaz

    def setup_standard_powerup_drops(self, enable_tnt: bool = True) -> None:
        """Create standard powerup drops for the current map."""
        # pylint: disable=cyclic-import
        from bastd.actor.powerupbox import DEFAULT_POWERUP_INTERVAL
        self._powerup_drop_timer = _ba.Timer(DEFAULT_POWERUP_INTERVAL,
                                             WeakCall(
                                                 self._standard_drop_powerups),
                                             repeat=True)
        self._standard_drop_powerups()
        if enable_tnt:
            self._tnt_spawners = {}
            self._setup_standard_tnt_drops()

    def _standard_drop_powerup(self, index: int, expire: bool = True) -> None:
        # pylint: disable=cyclic-import
        from bastd.actor.powerupbox import PowerupBox, PowerupBoxFactory
        PowerupBox(
            position=self.map.powerup_spawn_points[index],
            poweruptype=PowerupBoxFactory.get().get_random_powerup_type(),
            expire=expire).autoretain()

    def _standard_drop_powerups(self) -> None:
        """Standard powerup drop."""

        # Drop one powerup per point.
        points = self.map.powerup_spawn_points
        for i in range(len(points)):
            _ba.timer(i * 0.4, WeakCall(self._standard_drop_powerup, i))

    def _setup_standard_tnt_drops(self) -> None:
        """Standard tnt drop."""
        # pylint: disable=cyclic-import
        from bastd.actor.bomb import TNTSpawner
        for i, point in enumerate(self.map.tnt_points):
            assert self._tnt_spawners is not None
            if self._tnt_spawners.get(i) is None:
                self._tnt_spawners[i] = TNTSpawner(point)

    def setup_standard_time_limit(self, duration: float) -> None:
        """
        Create a standard game time-limit given the provided
        duration in seconds.
        This will be displayed at the top of the screen.
        If the time-limit expires, end_game() will be called.
        """
        from ba._nodeactor import NodeActor
        if duration <= 0.0:
            return
        self._standard_time_limit_time = int(duration)
        self._standard_time_limit_timer = _ba.Timer(
            1.0, WeakCall(self._standard_time_limit_tick), repeat=True)
        self._standard_time_limit_text = NodeActor(
            _ba.newnode('text',
                        attrs={
                            'v_attach': 'top',
                            'h_attach': 'center',
                            'h_align': 'left',
                            'color': (1.0, 1.0, 1.0, 0.5),
                            'position': (-25, -30),
                            'flatness': 1.0,
                            'scale': 0.9
                        }))
        self._standard_time_limit_text_input = NodeActor(
            _ba.newnode('timedisplay',
                        attrs={
                            'time2': duration * 1000,
                            'timemin': 0
                        }))
        self.globalsnode.connectattr('time',
                                     self._standard_time_limit_text_input.node,
                                     'time1')
        assert self._standard_time_limit_text_input.node
        assert self._standard_time_limit_text.node
        self._standard_time_limit_text_input.node.connectattr(
            'output', self._standard_time_limit_text.node, 'text')

    def _standard_time_limit_tick(self) -> None:
        from ba._gameutils import animate
        assert self._standard_time_limit_time is not None
        self._standard_time_limit_time -= 1
        if self._standard_time_limit_time <= 10:
            if self._standard_time_limit_time == 10:
                assert self._standard_time_limit_text is not None
                assert self._standard_time_limit_text.node
                self._standard_time_limit_text.node.scale = 1.3
                self._standard_time_limit_text.node.position = (-30, -45)
                cnode = _ba.newnode('combine',
                                    owner=self._standard_time_limit_text.node,
                                    attrs={'size': 4})
                cnode.connectattr('output',
                                  self._standard_time_limit_text.node, 'color')
                animate(cnode, 'input0', {0: 1, 0.15: 1}, loop=True)
                animate(cnode, 'input1', {0: 1, 0.15: 0.5}, loop=True)
                animate(cnode, 'input2', {0: 0.1, 0.15: 0.0}, loop=True)
                cnode.input3 = 1.0
            _ba.playsound(_ba.getsound('tick'))
        if self._standard_time_limit_time <= 0:
            self._standard_time_limit_timer = None
            self.end_game()
            node = _ba.newnode('text',
                               attrs={
                                   'v_attach': 'top',
                                   'h_attach': 'center',
                                   'h_align': 'center',
                                   'color': (1, 0.7, 0, 1),
                                   'position': (0, -90),
                                   'scale': 1.2,
                                   'text': Lstr(resource='timeExpiredText')
                               })
            _ba.playsound(_ba.getsound('refWhistle'))
            animate(node, 'scale', {0.0: 0.0, 0.1: 1.4, 0.15: 1.2})

    def _setup_tournament_time_limit(self, duration: float) -> None:
        """
        Create a tournament game time-limit given the provided
        duration in seconds.
        This will be displayed at the top of the screen.
        If the time-limit expires, end_game() will be called.
        """
        from ba._nodeactor import NodeActor
        from ba._enums import TimeType
        if duration <= 0.0:
            return
        self._tournament_time_limit = int(duration)

        # We want this timer to match the server's time as close as possible,
        # so lets go with base-time. Theoretically we should do real-time but
        # then we have to mess with contexts and whatnot since its currently
        # not available in activity contexts. :-/
        self._tournament_time_limit_timer = _ba.Timer(
            1.0,
            WeakCall(self._tournament_time_limit_tick),
            repeat=True,
            timetype=TimeType.BASE)
        self._tournament_time_limit_title_text = NodeActor(
            _ba.newnode('text',
                        attrs={
                            'v_attach': 'bottom',
                            'h_attach': 'left',
                            'h_align': 'center',
                            'v_align': 'center',
                            'vr_depth': 300,
                            'maxwidth': 100,
                            'color': (1.0, 1.0, 1.0, 0.5),
                            'position': (60, 50),
                            'flatness': 1.0,
                            'scale': 0.5,
                            'text': Lstr(resource='tournamentText')
                        }))
        self._tournament_time_limit_text = NodeActor(
            _ba.newnode('text',
                        attrs={
                            'v_attach': 'bottom',
                            'h_attach': 'left',
                            'h_align': 'center',
                            'v_align': 'center',
                            'vr_depth': 300,
                            'maxwidth': 100,
                            'color': (1.0, 1.0, 1.0, 0.5),
                            'position': (60, 30),
                            'flatness': 1.0,
                            'scale': 0.9
                        }))
        self._tournament_time_limit_text_input = NodeActor(
            _ba.newnode('timedisplay',
                        attrs={
                            'timemin': 0,
                            'time2': self._tournament_time_limit * 1000
                        }))
        assert self._tournament_time_limit_text.node
        assert self._tournament_time_limit_text_input.node
        self._tournament_time_limit_text_input.node.connectattr(
            'output', self._tournament_time_limit_text.node, 'text')

    def _tournament_time_limit_tick(self) -> None:
        from ba._gameutils import animate
        assert self._tournament_time_limit is not None
        self._tournament_time_limit -= 1
        if self._tournament_time_limit <= 10:
            if self._tournament_time_limit == 10:
                assert self._tournament_time_limit_title_text is not None
                assert self._tournament_time_limit_title_text.node
                assert self._tournament_time_limit_text is not None
                assert self._tournament_time_limit_text.node
                self._tournament_time_limit_title_text.node.scale = 1.0
                self._tournament_time_limit_text.node.scale = 1.3
                self._tournament_time_limit_title_text.node.position = (80, 85)
                self._tournament_time_limit_text.node.position = (80, 60)
                cnode = _ba.newnode(
                    'combine',
                    owner=self._tournament_time_limit_text.node,
                    attrs={'size': 4})
                cnode.connectattr('output',
                                  self._tournament_time_limit_title_text.node,
                                  'color')
                cnode.connectattr('output',
                                  self._tournament_time_limit_text.node,
                                  'color')
                animate(cnode, 'input0', {0: 1, 0.15: 1}, loop=True)
                animate(cnode, 'input1', {0: 1, 0.15: 0.5}, loop=True)
                animate(cnode, 'input2', {0: 0.1, 0.15: 0.0}, loop=True)
                cnode.input3 = 1.0
            _ba.playsound(_ba.getsound('tick'))
        if self._tournament_time_limit <= 0:
            self._tournament_time_limit_timer = None
            self.end_game()
            tval = Lstr(resource='tournamentTimeExpiredText',
                        fallback_resource='timeExpiredText')
            node = _ba.newnode('text',
                               attrs={
                                   'v_attach': 'top',
                                   'h_attach': 'center',
                                   'h_align': 'center',
                                   'color': (1, 0.7, 0, 1),
                                   'position': (0, -200),
                                   'scale': 1.6,
                                   'text': tval
                               })
            _ba.playsound(_ba.getsound('refWhistle'))
            animate(node, 'scale', {0: 0.0, 0.1: 1.4, 0.15: 1.2})

        # Normally we just connect this to time, but since this is a bit of a
        # funky setup we just update it manually once per second.
        assert self._tournament_time_limit_text_input is not None
        assert self._tournament_time_limit_text_input.node
        self._tournament_time_limit_text_input.node.time2 = (
            self._tournament_time_limit * 1000)

    def show_zoom_message(self,
                          message: ba.Lstr,
                          color: Sequence[float] = (0.9, 0.4, 0.0),
                          scale: float = 0.8,
                          duration: float = 2.0,
                          trail: bool = False) -> None:
        """Zooming text used to announce game names and winners."""
        # pylint: disable=cyclic-import
        from bastd.actor.zoomtext import ZoomText

        # Reserve a spot on the screen (in case we get multiple of these so
        # they don't overlap).
        i = 0
        cur_time = _ba.time()
        while True:
            if (i not in self._zoom_message_times
                    or self._zoom_message_times[i] < cur_time):
                self._zoom_message_times[i] = cur_time + duration
                break
            i += 1
        ZoomText(message,
                 lifespan=duration,
                 jitter=2.0,
                 position=(0, 200 - i * 100),
                 scale=scale,
                 maxwidth=800,
                 trail=trail,
                 color=color).autoretain()

    def _calc_map_name(self, settings: dict) -> str:
        map_name: str
        if 'map' in settings:
            map_name = settings['map']
        else:
            # If settings doesn't specify a map, pick a random one from the
            # list of supported ones.
            unowned_maps = _map.get_unowned_maps()
            valid_maps: List[str] = [
                m for m in self.get_supported_maps(type(self.session))
                if m not in unowned_maps
            ]
            if not valid_maps:
                _ba.screenmessage(Lstr(resource='noValidMapsErrorText'))
                raise Exception('No valid maps')
            map_name = valid_maps[random.randrange(len(valid_maps))]
        return map_name
