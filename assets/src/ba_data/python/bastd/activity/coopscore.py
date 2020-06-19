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
"""Provides a score screen for coop games."""
# pylint: disable=too-many-lines

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _ba
import ba
from ba.internal import get_achievements_for_coop_level
from bastd.actor.text import Text
from bastd.actor.zoomtext import ZoomText

if TYPE_CHECKING:
    from typing import Optional, Tuple, List, Dict, Any, Sequence
    from bastd.ui.store.button import StoreButton
    from bastd.ui.league.rankbutton import LeagueRankButton


class CoopScoreScreen(ba.Activity[ba.Player, ba.Team]):
    """Score screen showing the results of a cooperative game."""

    def __init__(self, settings: dict):
        # pylint: disable=too-many-statements
        super().__init__(settings)

        # Keep prev activity alive while we fade in
        self.transition_time = 0.5
        self.inherits_tint = True
        self.inherits_vr_camera_offset = True
        self.inherits_music = True
        self.use_fixed_vr_overlay = True

        self._do_new_rating: bool = self.session.tournament_id is not None

        self._score_display_sound = ba.getsound('scoreHit01')
        self._score_display_sound_small = ba.getsound('scoreHit02')
        self.drum_roll_sound = ba.getsound('drumRoll')
        self.cymbal_sound = ba.getsound('cymbal')

        # These get used in UI bits so need to load them in the UI context.
        with ba.Context('ui'):
            self._replay_icon_texture = ba.gettexture('replayIcon')
            self._menu_icon_texture = ba.gettexture('menuIcon')
            self._next_level_icon_texture = ba.gettexture('nextLevelIcon')

        self._campaign: ba.Campaign = settings['campaign']

        self._have_achievements = bool(
            get_achievements_for_coop_level(self._campaign.name + ':' +
                                            settings['level']))

        self._account_type = (_ba.get_account_type() if
                              _ba.get_account_state() == 'signed_in' else None)

        self._game_service_icon_color: Optional[Sequence[float]]
        self._game_service_achievements_texture: Optional[ba.Texture]
        self._game_service_leaderboards_texture: Optional[ba.Texture]

        with ba.Context('ui'):
            if self._account_type == 'Game Center':
                self._game_service_icon_color = (1.0, 1.0, 1.0)
                icon = ba.gettexture('gameCenterIcon')
                self._game_service_achievements_texture = icon
                self._game_service_leaderboards_texture = icon
                self._account_has_achievements = True
            elif self._account_type == 'Game Circle':
                icon = ba.gettexture('gameCircleIcon')
                self._game_service_icon_color = (1, 1, 1)
                self._game_service_achievements_texture = icon
                self._game_service_leaderboards_texture = icon
                self._account_has_achievements = True
            elif self._account_type == 'Google Play':
                self._game_service_icon_color = (0.8, 1.0, 0.6)
                self._game_service_achievements_texture = (
                    ba.gettexture('googlePlayAchievementsIcon'))
                self._game_service_leaderboards_texture = (
                    ba.gettexture('googlePlayLeaderboardsIcon'))
                self._account_has_achievements = True
            else:
                self._game_service_icon_color = None
                self._game_service_achievements_texture = None
                self._game_service_leaderboards_texture = None
                self._account_has_achievements = False

        self._cashregistersound = ba.getsound('cashRegister')
        self._gun_cocking_sound = ba.getsound('gunCocking')
        self._dingsound = ba.getsound('ding')
        self._score_link: Optional[str] = None
        self._root_ui: Optional[ba.Widget] = None
        self._background: Optional[ba.Actor] = None
        self._old_best_rank = 0.0
        self._game_name_str: Optional[str] = None
        self._game_config_str: Optional[str] = None

        # Ui bits.
        self._corner_button_offs: Optional[Tuple[float, float]] = None
        self._league_rank_button: Optional[LeagueRankButton] = None
        self._store_button_instance: Optional[StoreButton] = None
        self._restart_button: Optional[ba.Widget] = None
        self._update_corner_button_positions_timer: Optional[ba.Timer] = None
        self._next_level_error: Optional[ba.Actor] = None

        # Score/gameplay bits.
        self._was_complete: Optional[bool] = None
        self._is_complete: Optional[bool] = None
        self._newly_complete: Optional[bool] = None
        self._is_more_levels: Optional[bool] = None
        self._next_level_name: Optional[str] = None
        self._show_friend_scores: Optional[bool] = None
        self._show_info: Optional[Dict[str, Any]] = None
        self._name_str: Optional[str] = None
        self._friends_loading_status: Optional[ba.Actor] = None
        self._score_loading_status: Optional[ba.Actor] = None
        self._tournament_time_remaining: Optional[float] = None
        self._tournament_time_remaining_text: Optional[Text] = None
        self._tournament_time_remaining_text_timer: Optional[ba.Timer] = None

        self._playerinfos: List[ba.PlayerInfo] = settings['playerinfos']
        assert isinstance(self._playerinfos, list)
        assert (isinstance(i, ba.PlayerInfo) for i in self._playerinfos)

        self._score: Optional[int] = settings['score']
        assert isinstance(self._score, (int, type(None)))

        self._fail_message: Optional[ba.Lstr] = settings['fail_message']
        assert isinstance(self._fail_message, (ba.Lstr, type(None)))

        self._begin_time: Optional[float] = None

        self._score_order: str
        if 'score_order' in settings:
            if not settings['score_order'] in ['increasing', 'decreasing']:
                raise ValueError('Invalid score order: ' +
                                 settings['score_order'])
            self._score_order = settings['score_order']
        else:
            self._score_order = 'increasing'
        assert isinstance(self._score_order, str)

        self._score_type: str
        if 'score_type' in settings:
            if not settings['score_type'] in ['points', 'time']:
                raise ValueError('Invalid score type: ' +
                                 settings['score_type'])
            self._score_type = settings['score_type']
        else:
            self._score_type = 'points'
        assert isinstance(self._score_type, str)

        self._level_name: str = settings['level']
        assert isinstance(self._level_name, str)

        self._game_name_str = self._campaign.name + ':' + self._level_name
        self._game_config_str = str(len(
            self._playerinfos)) + 'p' + self._campaign.getlevel(
                self._level_name).get_score_version_string().replace(' ', '_')

        # If game-center/etc scores are available we show our friends'
        # scores. Otherwise we show our local high scores.
        self._show_friend_scores = _ba.game_service_has_leaderboard(
            self._game_name_str, self._game_config_str)

        try:
            self._old_best_rank = self._campaign.getlevel(
                self._level_name).rating
        except Exception:
            self._old_best_rank = 0.0

        self._victory: bool = settings['outcome'] == 'victory'

    def __del__(self) -> None:
        super().__del__()

        # If our UI is still up, kill it.
        if self._root_ui:
            with ba.Context('ui'):
                ba.containerwidget(edit=self._root_ui, transition='out_left')

    def on_transition_in(self) -> None:
        from bastd.actor import background  # FIXME NO BSSTD
        ba.set_analytics_screen('Coop Score Screen')
        super().on_transition_in()
        self._background = background.Background(fade_time=0.45,
                                                 start_faded=False,
                                                 show_logo=True)

    def _ui_menu(self) -> None:
        from bastd.ui import specialoffer
        if specialoffer.show_offer():
            return
        ba.containerwidget(edit=self._root_ui, transition='out_left')
        with ba.Context(self):
            ba.timer(0.1, ba.Call(ba.WeakCall(self.session.end)))

    def _ui_restart(self) -> None:
        from bastd.ui.tournamententry import TournamentEntryWindow
        from bastd.ui import specialoffer
        if specialoffer.show_offer():
            return

        # If we're in a tournament and it looks like there's no time left,
        # disallow.
        if self.session.tournament_id is not None:
            if self._tournament_time_remaining is None:
                ba.screenmessage(
                    ba.Lstr(resource='tournamentCheckingStateText'),
                    color=(1, 0, 0))
                ba.playsound(ba.getsound('error'))
                return
            if self._tournament_time_remaining <= 0:
                ba.screenmessage(ba.Lstr(resource='tournamentEndedText'),
                                 color=(1, 0, 0))
                ba.playsound(ba.getsound('error'))
                return

        # If there are currently fewer players than our session min,
        # don't allow.
        if len(self.players) < self.session.min_players:
            ba.screenmessage(ba.Lstr(resource='notEnoughPlayersRemainingText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return

        self._campaign.set_selected_level(self._level_name)

        # If this is a tournament, go back to the tournament-entry UI
        # otherwise just hop back in.
        tournament_id = self.session.tournament_id
        if tournament_id is not None:
            assert self._restart_button is not None
            TournamentEntryWindow(
                tournament_id=tournament_id,
                tournament_activity=self,
                position=self._restart_button.get_screen_space_center())
        else:
            ba.containerwidget(edit=self._root_ui, transition='out_left')
            self.can_show_ad_on_death = True
            with ba.Context(self):
                self.end({'outcome': 'restart'})

    def _ui_next(self) -> None:
        from bastd.ui.specialoffer import show_offer
        if show_offer():
            return

        # If we didn't just complete this level but are choosing to play the
        # next one, set it as current (this won't happen otherwise).
        if (self._is_complete and self._is_more_levels
                and not self._newly_complete):
            assert self._next_level_name is not None
            self._campaign.set_selected_level(self._next_level_name)
        ba.containerwidget(edit=self._root_ui, transition='out_left')
        with ba.Context(self):
            self.end({'outcome': 'next_level'})

    def _ui_gc(self) -> None:
        _ba.show_online_score_ui('leaderboard',
                                 game=self._game_name_str,
                                 game_version=self._game_config_str)

    def _ui_show_achievements(self) -> None:
        _ba.show_online_score_ui('achievements')

    def _ui_worlds_best(self) -> None:
        if self._score_link is None:
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource='scoreListUnavailableText'),
                             color=(1, 0.5, 0))
        else:
            ba.open_url(self._score_link)

    def _ui_error(self) -> None:
        with ba.Context(self):
            self._next_level_error = Text(
                ba.Lstr(resource='completeThisLevelToProceedText'),
                flash=True,
                maxwidth=360,
                scale=0.54,
                h_align=Text.HAlign.CENTER,
                color=(0.5, 0.7, 0.5, 1),
                position=(300, -235))
            ba.playsound(ba.getsound('error'))
            ba.timer(
                2.0,
                ba.WeakCall(self._next_level_error.handlemessage,
                            ba.DieMessage()))

    def _should_show_worlds_best_button(self) -> bool:
        # Link is too complicated to display with no browser.
        return ba.is_browser_likely_available()

    def request_ui(self) -> None:
        """Set up a callback to show our UI at the next opportune time."""
        # We don't want to just show our UI in case the user already has the
        # main menu up, so instead we add a callback for when the menu
        # closes; if we're still alive, we'll come up then.
        # If there's no main menu this gets called immediately.
        ba.app.add_main_menu_close_callback(ba.WeakCall(self.show_ui))

    def show_ui(self) -> None:
        """Show the UI for restarting, playing the next Level, etc."""
        # pylint: disable=too-many-locals
        from bastd.ui.store.button import StoreButton
        from bastd.ui.league.rankbutton import LeagueRankButton

        delay = 0.7 if (self._score is not None) else 0.0

        # If there's no players left in the game, lets not show the UI
        # (that would allow restarting the game with zero players, etc).
        if not self.players:
            return

        rootc = self._root_ui = ba.containerwidget(size=(0, 0),
                                                   transition='in_right')

        h_offs = 7.0
        v_offs = -280.0

        # We wanna prevent controllers users from popping up browsers
        # or game-center widgets in cases where they can't easily get back
        # to the game (like on mac).
        can_select_extra_buttons = ba.app.platform == 'android'

        _ba.set_ui_input_device(None)  # Menu is up for grabs.

        if self._show_friend_scores:
            ba.buttonwidget(parent=rootc,
                            color=(0.45, 0.4, 0.5),
                            position=(h_offs - 520, v_offs + 480),
                            size=(300, 60),
                            label=ba.Lstr(resource='topFriendsText'),
                            on_activate_call=ba.WeakCall(self._ui_gc),
                            transition_delay=delay + 0.5,
                            icon=self._game_service_leaderboards_texture,
                            icon_color=self._game_service_icon_color,
                            autoselect=True,
                            selectable=can_select_extra_buttons)

        if self._have_achievements and self._account_has_achievements:
            ba.buttonwidget(parent=rootc,
                            color=(0.45, 0.4, 0.5),
                            position=(h_offs - 520, v_offs + 450 - 235 + 40),
                            size=(300, 60),
                            label=ba.Lstr(resource='achievementsText'),
                            on_activate_call=ba.WeakCall(
                                self._ui_show_achievements),
                            transition_delay=delay + 1.5,
                            icon=self._game_service_achievements_texture,
                            icon_color=self._game_service_icon_color,
                            autoselect=True,
                            selectable=can_select_extra_buttons)

        if self._should_show_worlds_best_button():
            ba.buttonwidget(
                parent=rootc,
                color=(0.45, 0.4, 0.5),
                position=(160, v_offs + 480),
                size=(350, 62),
                label=ba.Lstr(resource='tournamentStandingsText')
                if self.session.tournament_id is not None else ba.Lstr(
                    resource='worldsBestScoresText') if self._score_type
                == 'points' else ba.Lstr(resource='worldsBestTimesText'),
                autoselect=True,
                on_activate_call=ba.WeakCall(self._ui_worlds_best),
                transition_delay=delay + 1.9,
                selectable=can_select_extra_buttons)
        else:
            pass

        show_next_button = self._is_more_levels and not ba.app.kiosk_mode

        if not show_next_button:
            h_offs += 70

        menu_button = ba.buttonwidget(parent=rootc,
                                      autoselect=True,
                                      position=(h_offs - 130 - 60, v_offs),
                                      size=(110, 85),
                                      label='',
                                      on_activate_call=ba.WeakCall(
                                          self._ui_menu))
        ba.imagewidget(parent=rootc,
                       draw_controller=menu_button,
                       position=(h_offs - 130 - 60 + 22, v_offs + 14),
                       size=(60, 60),
                       texture=self._menu_icon_texture,
                       opacity=0.8)
        self._restart_button = restart_button = ba.buttonwidget(
            parent=rootc,
            autoselect=True,
            position=(h_offs - 60, v_offs),
            size=(110, 85),
            label='',
            on_activate_call=ba.WeakCall(self._ui_restart))
        ba.imagewidget(parent=rootc,
                       draw_controller=restart_button,
                       position=(h_offs - 60 + 19, v_offs + 7),
                       size=(70, 70),
                       texture=self._replay_icon_texture,
                       opacity=0.8)

        next_button: Optional[ba.Widget] = None

        # Our 'next' button is disabled if we haven't unlocked the next
        # level yet and invisible if there is none.
        if show_next_button:
            if self._is_complete:
                call = ba.WeakCall(self._ui_next)
                button_sound = True
                image_opacity = 0.8
                color = None
            else:
                call = ba.WeakCall(self._ui_error)
                button_sound = False
                image_opacity = 0.2
                color = (0.3, 0.3, 0.3)
            next_button = ba.buttonwidget(parent=rootc,
                                          autoselect=True,
                                          position=(h_offs + 130 - 60, v_offs),
                                          size=(110, 85),
                                          label='',
                                          on_activate_call=call,
                                          color=color,
                                          enable_sound=button_sound)
            ba.imagewidget(parent=rootc,
                           draw_controller=next_button,
                           position=(h_offs + 130 - 60 + 12, v_offs + 5),
                           size=(80, 80),
                           texture=self._next_level_icon_texture,
                           opacity=image_opacity)

        x_offs_extra = 0 if show_next_button else -100
        self._corner_button_offs = (h_offs + 300.0 + 100.0 + x_offs_extra,
                                    v_offs + 560.0)

        if ba.app.kiosk_mode:
            self._league_rank_button = None
            self._store_button_instance = None
        else:
            self._league_rank_button = LeagueRankButton(
                parent=rootc,
                position=(h_offs + 300 + 100 + x_offs_extra, v_offs + 560),
                size=(100, 60),
                scale=0.9,
                color=(0.4, 0.4, 0.9),
                textcolor=(0.9, 0.9, 2.0),
                transition_delay=0.0,
                smooth_update_delay=5.0)
            self._store_button_instance = StoreButton(
                parent=rootc,
                position=(h_offs + 400 + 100 + x_offs_extra, v_offs + 560),
                show_tickets=True,
                sale_scale=0.85,
                size=(100, 60),
                scale=0.9,
                button_type='square',
                color=(0.35, 0.25, 0.45),
                textcolor=(0.9, 0.7, 1.0),
                transition_delay=0.0)

        ba.containerwidget(edit=rootc,
                           selected_child=next_button if
                           (self._newly_complete and self._victory
                            and show_next_button) else restart_button,
                           on_cancel_call=menu_button.activate)

        self._update_corner_button_positions()
        self._update_corner_button_positions_timer = ba.Timer(
            1.0,
            ba.WeakCall(self._update_corner_button_positions),
            repeat=True,
            timetype=ba.TimeType.REAL)

    def _update_corner_button_positions(self) -> None:
        offs = -55 if _ba.is_party_icon_visible() else 0
        assert self._corner_button_offs is not None
        pos_x = self._corner_button_offs[0] + offs
        pos_y = self._corner_button_offs[1]
        if self._league_rank_button is not None:
            self._league_rank_button.set_position((pos_x, pos_y))
        if self._store_button_instance is not None:
            self._store_button_instance.set_position((pos_x + 100, pos_y))

    def on_begin(self) -> None:
        # FIXME: Clean this up.
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        super().on_begin()

        self._begin_time = ba.time()

        # Calc whether the level is complete and other stuff.
        levels = self._campaign.levels
        level = self._campaign.getlevel(self._level_name)
        self._was_complete = level.complete
        self._is_complete = (self._was_complete or self._victory)
        self._newly_complete = (self._is_complete and not self._was_complete)
        self._is_more_levels = ((level.index < len(levels) - 1)
                                and self._campaign.sequential)

        # Any time we complete a level, set the next one as unlocked.
        if self._is_complete and self._is_more_levels:
            _ba.add_transaction({
                'type': 'COMPLETE_LEVEL',
                'campaign': self._campaign.name,
                'level': self._level_name
            })
            self._next_level_name = levels[level.index + 1].name

            # If this is the first time we completed it, set the next one
            # as current.
            if self._newly_complete:
                cfg = ba.app.config
                cfg['Selected Coop Game'] = (self._campaign.name + ':' +
                                             self._next_level_name)
                cfg.commit()
                self._campaign.set_selected_level(self._next_level_name)

        ba.timer(1.0, ba.WeakCall(self.request_ui))

        if (self._is_complete and self._victory and self._is_more_levels
                and not ba.app.kiosk_mode):
            Text(ba.Lstr(value='${A}:\n',
                         subs=[('${A}', ba.Lstr(resource='levelUnlockedText'))
                               ]) if self._newly_complete else
                 ba.Lstr(value='${A}:\n',
                         subs=[('${A}', ba.Lstr(resource='nextLevelText'))]),
                 transition=Text.Transition.IN_RIGHT,
                 transition_delay=5.2,
                 flash=self._newly_complete,
                 scale=0.54,
                 h_align=Text.HAlign.CENTER,
                 maxwidth=270,
                 color=(0.5, 0.7, 0.5, 1),
                 position=(270, -235)).autoretain()
            assert self._next_level_name is not None
            Text(ba.Lstr(translate=('coopLevelNames', self._next_level_name)),
                 transition=Text.Transition.IN_RIGHT,
                 transition_delay=5.2,
                 flash=self._newly_complete,
                 scale=0.7,
                 h_align=Text.HAlign.CENTER,
                 maxwidth=205,
                 color=(0.5, 0.7, 0.5, 1),
                 position=(270, -255)).autoretain()
            if self._newly_complete:
                ba.timer(5.2, ba.Call(ba.playsound, self._cashregistersound))
                ba.timer(5.2, ba.Call(ba.playsound, self._dingsound))

        offs_x = -195
        if len(self._playerinfos) > 1:
            pstr = ba.Lstr(value='- ${A} -',
                           subs=[('${A}',
                                  ba.Lstr(resource='multiPlayerCountText',
                                          subs=[('${COUNT}',
                                                 str(len(self._playerinfos)))
                                                ]))])
        else:
            pstr = ba.Lstr(value='- ${A} -',
                           subs=[('${A}',
                                  ba.Lstr(resource='singlePlayerCountText'))])
        ZoomText(self._campaign.getlevel(self._level_name).displayname,
                 maxwidth=800,
                 flash=False,
                 trail=False,
                 color=(0.5, 1, 0.5, 1),
                 h_align='center',
                 scale=0.4,
                 position=(0, 292),
                 jitter=1.0).autoretain()
        Text(pstr,
             maxwidth=300,
             transition=Text.Transition.FADE_IN,
             scale=0.7,
             h_align=Text.HAlign.CENTER,
             v_align=Text.VAlign.CENTER,
             color=(0.5, 0.7, 0.5, 1),
             position=(0, 230)).autoretain()

        adisp = _ba.get_account_display_string()
        txt = Text(ba.Lstr(resource='waitingForHostText',
                           subs=[('${HOST}', adisp)]),
                   maxwidth=300,
                   transition=Text.Transition.FADE_IN,
                   transition_delay=8.0,
                   scale=0.85,
                   h_align=Text.HAlign.CENTER,
                   v_align=Text.VAlign.CENTER,
                   color=(1, 1, 0, 1),
                   position=(0, -230)).autoretain()
        assert txt.node
        txt.node.client_only = True

        if self._score is not None:
            ba.timer(0.35,
                     ba.Call(ba.playsound, self._score_display_sound_small))

        # Vestigial remain; this stuff should just be instance vars.
        self._show_info = {}

        if self._score is not None:
            ba.timer(0.8, ba.WeakCall(self._show_score_val, offs_x))
        else:
            ba.pushcall(ba.WeakCall(self._show_fail))

        self._name_str = name_str = ', '.join(
            [p.name for p in self._playerinfos])

        if self._show_friend_scores:
            self._friends_loading_status = Text(
                ba.Lstr(value='${A}...',
                        subs=[('${A}', ba.Lstr(resource='loadingText'))]),
                position=(-405, 150 + 30),
                color=(1, 1, 1, 0.4),
                transition=Text.Transition.FADE_IN,
                scale=0.7,
                transition_delay=2.0)
        self._score_loading_status = Text(ba.Lstr(
            value='${A}...', subs=[('${A}', ba.Lstr(resource='loadingText'))]),
                                          position=(280, 150 + 30),
                                          color=(1, 1, 1, 0.4),
                                          transition=Text.Transition.FADE_IN,
                                          scale=0.7,
                                          transition_delay=2.0)

        if self._score is not None:
            ba.timer(0.4, ba.WeakCall(self._play_drumroll))

        # Add us to high scores, filter, and store.
        our_high_scores_all = self._campaign.getlevel(
            self._level_name).get_high_scores()

        our_high_scores = our_high_scores_all.setdefault(
            str(len(self._playerinfos)) + ' Player', [])

        if self._score is not None:
            our_score: Optional[list] = [
                self._score, {
                    'players': [{
                        'name': p.name,
                        'character': p.character
                    } for p in self._playerinfos]
                }
            ]
            our_high_scores.append(our_score)
        else:
            our_score = None

        try:
            our_high_scores.sort(reverse=self._score_order == 'increasing',
                                 key=lambda x: x[0])
        except Exception:
            ba.print_exception('Error sorting scores.')
            print(f'our_high_scores: {our_high_scores}')

        del our_high_scores[10:]

        if self._score is not None:
            sver = (self._campaign.getlevel(
                self._level_name).get_score_version_string())
            _ba.add_transaction({
                'type': 'SET_LEVEL_LOCAL_HIGH_SCORES',
                'campaign': self._campaign.name,
                'level': self._level_name,
                'scoreVersion': sver,
                'scores': our_high_scores_all
            })
        if _ba.get_account_state() != 'signed_in':
            # We expect this only in kiosk mode; complain otherwise.
            if not ba.app.kiosk_mode:
                print('got not-signed-in at score-submit; unexpected')
            if self._show_friend_scores:
                ba.pushcall(ba.WeakCall(self._got_friend_score_results, None))
            ba.pushcall(ba.WeakCall(self._got_score_results, None))
        else:
            assert self._game_name_str is not None
            assert self._game_config_str is not None
            _ba.submit_score(self._game_name_str,
                             self._game_config_str,
                             name_str,
                             self._score,
                             ba.WeakCall(self._got_score_results),
                             ba.WeakCall(self._got_friend_score_results)
                             if self._show_friend_scores else None,
                             order=self._score_order,
                             tournament_id=self.session.tournament_id,
                             score_type=self._score_type,
                             campaign=self._campaign.name,
                             level=self._level_name)

        # Apply the transactions we've been adding locally.
        _ba.run_transactions()

        # If we're not doing the world's-best button, just show a title
        # instead.
        ts_height = 300
        ts_h_offs = 210
        v_offs = 40
        txt = Text(ba.Lstr(resource='tournamentStandingsText')
                   if self.session.tournament_id is not None else ba.Lstr(
                       resource='worldsBestScoresText') if self._score_type
                   == 'points' else ba.Lstr(resource='worldsBestTimesText'),
                   maxwidth=210,
                   position=(ts_h_offs - 10, ts_height / 2 + 25 + v_offs + 20),
                   transition=Text.Transition.IN_LEFT,
                   v_align=Text.VAlign.CENTER,
                   scale=1.2,
                   transition_delay=2.2).autoretain()

        # If we've got a button on the server, only show this on clients.
        if self._should_show_worlds_best_button():
            assert txt.node
            txt.node.client_only = True

        # If we have no friend scores, display local best scores.
        if self._show_friend_scores:

            # Host has a button, so we need client-only text.
            ts_height = 300
            ts_h_offs = -480
            v_offs = 40
            txt = Text(ba.Lstr(resource='topFriendsText'),
                       maxwidth=210,
                       position=(ts_h_offs - 10,
                                 ts_height / 2 + 25 + v_offs + 20),
                       transition=Text.Transition.IN_RIGHT,
                       v_align=Text.VAlign.CENTER,
                       scale=1.2,
                       transition_delay=1.8).autoretain()
            assert txt.node
            txt.node.client_only = True
        else:

            ts_height = 300
            ts_h_offs = -480
            v_offs = 40
            Text(ba.Lstr(resource='yourBestScoresText') if self._score_type
                 == 'points' else ba.Lstr(resource='yourBestTimesText'),
                 maxwidth=210,
                 position=(ts_h_offs - 10, ts_height / 2 + 25 + v_offs + 20),
                 transition=Text.Transition.IN_RIGHT,
                 v_align=Text.VAlign.CENTER,
                 scale=1.2,
                 transition_delay=1.8).autoretain()

            display_scores = list(our_high_scores)
            display_count = 5

            while len(display_scores) < display_count:
                display_scores.append((0, None))

            showed_ours = False
            h_offs_extra = 85 if self._score_type == 'points' else 130
            v_offs_extra = 20
            v_offs_names = 0
            scale = 1.0
            p_count = len(self._playerinfos)
            h_offs_extra -= 75
            if p_count > 1:
                h_offs_extra -= 20
            if p_count == 2:
                scale = 0.9
            elif p_count == 3:
                scale = 0.65
            elif p_count == 4:
                scale = 0.5
            times: List[Tuple[float, float]] = []
            for i in range(display_count):
                times.insert(random.randrange(0,
                                              len(times) + 1),
                             (1.9 + i * 0.05, 2.3 + i * 0.05))
            for i in range(display_count):
                try:
                    if display_scores[i][1] is None:
                        name_str = '-'
                    else:
                        name_str = ', '.join([
                            p['name'] for p in display_scores[i][1]['players']
                        ])
                except Exception:
                    ba.print_exception(
                        f'Error calcing name_str for {display_scores}')
                    name_str = '-'
                if display_scores[i] == our_score and not showed_ours:
                    flash = True
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.6, 0.6, 0.6, 1.0)
                    tdelay1 = 3.7
                    tdelay2 = 3.7
                    showed_ours = True
                else:
                    flash = False
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.6, 0.6, 0.6, 1.0)
                    tdelay1 = times[i][0]
                    tdelay2 = times[i][1]
                Text(str(display_scores[i][0]) if self._score_type == 'points'
                     else ba.timestring(display_scores[i][0] * 10,
                                        timeformat=ba.TimeFormat.MILLISECONDS,
                                        suppress_format_warning=True),
                     position=(ts_h_offs + 20 + h_offs_extra,
                               v_offs_extra + ts_height / 2 + -ts_height *
                               (i + 1) / 10 + v_offs + 11.0),
                     h_align=Text.HAlign.RIGHT,
                     v_align=Text.VAlign.CENTER,
                     color=color0,
                     flash=flash,
                     transition=Text.Transition.IN_RIGHT,
                     transition_delay=tdelay1).autoretain()

                Text(ba.Lstr(value=name_str),
                     position=(ts_h_offs + 35 + h_offs_extra,
                               v_offs_extra + ts_height / 2 + -ts_height *
                               (i + 1) / 10 + v_offs_names + v_offs + 11.0),
                     maxwidth=80.0 + 100.0 * len(self._playerinfos),
                     v_align=Text.VAlign.CENTER,
                     color=color1,
                     flash=flash,
                     scale=scale,
                     transition=Text.Transition.IN_RIGHT,
                     transition_delay=tdelay2).autoretain()

        # Show achievements for this level.
        ts_height = -150
        ts_h_offs = -480
        v_offs = 40

        # Only make this if we don't have the button
        # (never want clients to see it so no need for client-only
        # version, etc).
        if self._have_achievements:
            if not self._account_has_achievements:
                Text(ba.Lstr(resource='achievementsText'),
                     position=(ts_h_offs - 10,
                               ts_height / 2 + 25 + v_offs + 3),
                     maxwidth=210,
                     host_only=True,
                     transition=Text.Transition.IN_RIGHT,
                     v_align=Text.VAlign.CENTER,
                     scale=1.2,
                     transition_delay=2.8).autoretain()

            assert self._game_name_str is not None
            achievements = get_achievements_for_coop_level(self._game_name_str)
            hval = -455
            vval = -100
            tdelay = 0.0
            for ach in achievements:
                ach.create_display(hval, vval + v_offs, 3.0 + tdelay)
                vval -= 55
                tdelay += 0.250

        ba.timer(5.0, ba.WeakCall(self._show_tips))

    def _play_drumroll(self) -> None:
        ba.NodeActor(
            ba.newnode('sound',
                       attrs={
                           'sound': self.drum_roll_sound,
                           'positional': False,
                           'loop': False
                       })).autoretain()

    def _got_friend_score_results(self, results: Optional[List[Any]]) -> None:

        # FIXME: tidy this up
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # delay a bit if results come in too fast
        assert self._begin_time is not None
        base_delay = max(0, 1.9 - (ba.time() - self._begin_time))
        ts_height = 300
        ts_h_offs = -550
        v_offs = 30

        # Report in case of error.
        if results is None:
            self._friends_loading_status = Text(
                ba.Lstr(resource='friendScoresUnavailableText'),
                maxwidth=330,
                position=(-475, 150 + v_offs),
                color=(1, 1, 1, 0.4),
                transition=Text.Transition.FADE_IN,
                transition_delay=base_delay + 0.8,
                scale=0.7)
            return

        self._friends_loading_status = None

        # Ok, it looks like we aren't able to reliably get a just-submitted
        # result returned in the score list, so we need to look for our score
        # in this list and replace it if ours is better or add ours otherwise.
        if self._score is not None:
            our_score_entry = [self._score, 'Me', True]
            for score in results:
                if score[2]:
                    if self._score_order == 'increasing':
                        our_score_entry[0] = max(score[0], self._score)
                    else:
                        our_score_entry[0] = min(score[0], self._score)
                    results.remove(score)
                    break
            results.append(our_score_entry)
            results.sort(reverse=self._score_order == 'increasing',
                         key=lambda x: x[0])

        # If we're not submitting our own score, we still want to change the
        # name of our own score to 'Me'.
        else:
            for score in results:
                if score[2]:
                    score[1] = 'Me'
                    break
        h_offs_extra = 80 if self._score_type == 'points' else 130
        v_offs_extra = 20
        v_offs_names = 0
        scale = 1.0

        # Make sure there's at least 5.
        while len(results) < 5:
            results.append([0, '-', False])
        results = results[:5]
        times: List[Tuple[float, float]] = []
        for i in range(len(results)):
            times.insert(random.randrange(0,
                                          len(times) + 1),
                         (base_delay + i * 0.05, base_delay + 0.3 + i * 0.05))
        for i, tval in enumerate(results):
            score = int(tval[0])
            name_str = tval[1]
            is_me = tval[2]
            if is_me and score == self._score:
                flash = True
                color0 = (0.6, 0.4, 0.1, 1.0)
                color1 = (0.6, 0.6, 0.6, 1.0)
                tdelay1 = base_delay + 1.0
                tdelay2 = base_delay + 1.0
            else:
                flash = False
                if is_me:
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.9, 1.0, 0.9, 1.0)
                else:
                    color0 = (0.6, 0.4, 0.1, 1.0)
                    color1 = (0.6, 0.6, 0.6, 1.0)
                tdelay1 = times[i][0]
                tdelay2 = times[i][1]
            if name_str != '-':
                Text(str(score) if self._score_type == 'points' else
                     ba.timestring(score * 10,
                                   timeformat=ba.TimeFormat.MILLISECONDS),
                     position=(ts_h_offs + 20 + h_offs_extra,
                               v_offs_extra + ts_height / 2 + -ts_height *
                               (i + 1) / 10 + v_offs + 11.0),
                     h_align=Text.HAlign.RIGHT,
                     v_align=Text.VAlign.CENTER,
                     color=color0,
                     flash=flash,
                     transition=Text.Transition.IN_RIGHT,
                     transition_delay=tdelay1).autoretain()
            else:
                if is_me:
                    print('Error: got empty name_str on score result:', tval)

            Text(ba.Lstr(value=name_str),
                 position=(ts_h_offs + 35 + h_offs_extra,
                           v_offs_extra + ts_height / 2 + -ts_height *
                           (i + 1) / 10 + v_offs_names + v_offs + 11.0),
                 color=color1,
                 maxwidth=160.0,
                 v_align=Text.VAlign.CENTER,
                 flash=flash,
                 scale=scale,
                 transition=Text.Transition.IN_RIGHT,
                 transition_delay=tdelay2).autoretain()

    def _got_score_results(self, results: Optional[Dict[str, Any]]) -> None:

        # FIXME: tidy this up
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        # We need to manually run this in the context of our activity
        # and only if we aren't shutting down.
        # (really should make the submit_score call handle that stuff itself)
        if self.expired:
            return
        with ba.Context(self):
            # Delay a bit if results come in too fast.
            assert self._begin_time is not None
            base_delay = max(0, 2.7 - (ba.time() - self._begin_time))
            v_offs = 20
            if results is None:
                self._score_loading_status = Text(
                    ba.Lstr(resource='worldScoresUnavailableText'),
                    position=(230, 150 + v_offs),
                    color=(1, 1, 1, 0.4),
                    transition=Text.Transition.FADE_IN,
                    transition_delay=base_delay + 0.3,
                    scale=0.7)
            else:
                self._score_link = results['link']
                assert self._score_link is not None
                if not self._score_link.startswith('http://'):
                    self._score_link = (_ba.get_master_server_address() + '/' +
                                        self._score_link)
                self._score_loading_status = None
                if 'tournamentSecondsRemaining' in results:
                    secs_remaining = results['tournamentSecondsRemaining']
                    assert isinstance(secs_remaining, int)
                    self._tournament_time_remaining = secs_remaining
                    self._tournament_time_remaining_text_timer = ba.Timer(
                        1.0,
                        ba.WeakCall(
                            self._update_tournament_time_remaining_text),
                        repeat=True,
                        timetype=ba.TimeType.BASE)

            assert self._show_info is not None
            self._show_info['results'] = results
            if results is not None:
                if results['tops'] != '':
                    self._show_info['tops'] = results['tops']
                else:
                    self._show_info['tops'] = []
            offs_x = -195
            available = (self._show_info['results'] is not None)
            if self._score is not None:
                ba.timer((1.5 + base_delay),
                         ba.WeakCall(self._show_world_rank, offs_x),
                         timetype=ba.TimeType.BASE)
            ts_h_offs = 200
            ts_height = 300

            # Show world tops.
            if available:

                # Show the number of games represented by this
                # list (except for in tournaments).
                if self.session.tournament_id is None:
                    Text(ba.Lstr(resource='lastGamesText',
                                 subs=[
                                     ('${COUNT}',
                                      str(self._show_info['results']['total']))
                                 ]),
                         position=(ts_h_offs - 35 + 95,
                                   ts_height / 2 + 6 + v_offs),
                         color=(0.4, 0.4, 0.4, 1.0),
                         scale=0.7,
                         transition=Text.Transition.IN_RIGHT,
                         transition_delay=base_delay + 0.3).autoretain()
                else:
                    v_offs += 20

                h_offs_extra = 0
                v_offs_names = 0
                scale = 1.0
                p_count = len(self._playerinfos)
                if p_count > 1:
                    h_offs_extra -= 40
                if self._score_type != 'points':
                    h_offs_extra += 60
                if p_count == 2:
                    scale = 0.9
                elif p_count == 3:
                    scale = 0.65
                elif p_count == 4:
                    scale = 0.5

                # Make sure there's at least 10.
                while len(self._show_info['tops']) < 10:
                    self._show_info['tops'].append([0, '-'])

                times: List[Tuple[float, float]] = []
                for i in range(len(self._show_info['tops'])):
                    times.insert(
                        random.randrange(0,
                                         len(times) + 1),
                        (base_delay + i * 0.05, base_delay + 0.4 + i * 0.05))
                for i, tval in enumerate(self._show_info['tops']):
                    score = int(tval[0])
                    name_str = tval[1]
                    if self._name_str == name_str and self._score == score:
                        flash = True
                        color0 = (0.6, 0.4, 0.1, 1.0)
                        color1 = (0.6, 0.6, 0.6, 1.0)
                        tdelay1 = base_delay + 1.0
                        tdelay2 = base_delay + 1.0
                    else:
                        flash = False
                        if self._name_str == name_str:
                            color0 = (0.6, 0.4, 0.1, 1.0)
                            color1 = (0.9, 1.0, 0.9, 1.0)
                        else:
                            color0 = (0.6, 0.4, 0.1, 1.0)
                            color1 = (0.6, 0.6, 0.6, 1.0)
                        tdelay1 = times[i][0]
                        tdelay2 = times[i][1]

                    if name_str != '-':
                        Text(str(score) if self._score_type == 'points' else
                             ba.timestring(
                                 score * 10,
                                 timeformat=ba.TimeFormat.MILLISECONDS),
                             position=(ts_h_offs + 20 + h_offs_extra,
                                       ts_height / 2 + -ts_height *
                                       (i + 1) / 10 + v_offs + 11.0),
                             h_align=Text.HAlign.RIGHT,
                             v_align=Text.VAlign.CENTER,
                             color=color0,
                             flash=flash,
                             transition=Text.Transition.IN_LEFT,
                             transition_delay=tdelay1).autoretain()
                    Text(ba.Lstr(value=name_str),
                         position=(ts_h_offs + 35 + h_offs_extra,
                                   ts_height / 2 + -ts_height * (i + 1) / 10 +
                                   v_offs_names + v_offs + 11.0),
                         maxwidth=80.0 + 100.0 * len(self._playerinfos),
                         v_align=Text.VAlign.CENTER,
                         color=color1,
                         flash=flash,
                         scale=scale,
                         transition=Text.Transition.IN_LEFT,
                         transition_delay=tdelay2).autoretain()

    def _show_tips(self) -> None:
        from bastd.actor.tipstext import TipsText
        TipsText(offs_y=30).autoretain()

    def _update_tournament_time_remaining_text(self) -> None:
        if self._tournament_time_remaining is None:
            return
        self._tournament_time_remaining = max(
            0, self._tournament_time_remaining - 1)
        if self._tournament_time_remaining_text is not None:
            val = ba.timestring(self._tournament_time_remaining,
                                suppress_format_warning=True,
                                centi=False)
            self._tournament_time_remaining_text.node.text = val

    def _show_world_rank(self, offs_x: float) -> None:
        # FIXME: Tidy this up.
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        from ba.internal import get_tournament_prize_strings
        assert self._show_info is not None
        available = (self._show_info['results'] is not None)

        if available:
            error = (self._show_info['results']['error']
                     if 'error' in self._show_info['results'] else None)
            rank = self._show_info['results']['rank']
            total = self._show_info['results']['total']
            rating = (10.0 if total == 1 else 10.0 * (1.0 - (float(rank - 1) /
                                                             (total - 1))))
            player_rank = self._show_info['results']['playerRank']
            best_player_rank = self._show_info['results']['bestPlayerRank']
        else:
            error = False
            rating = None
            player_rank = None
            best_player_rank = None

        # If we've got tournament-seconds-remaining, show it.
        if self._tournament_time_remaining is not None:
            Text(ba.Lstr(resource='coopSelectWindow.timeRemainingText'),
                 position=(-360, -70 - 100),
                 color=(1, 1, 1, 0.7),
                 h_align=Text.HAlign.CENTER,
                 v_align=Text.VAlign.CENTER,
                 transition=Text.Transition.FADE_IN,
                 scale=0.8,
                 maxwidth=300,
                 transition_delay=2.0).autoretain()
            self._tournament_time_remaining_text = Text(
                '',
                position=(-360, -110 - 100),
                color=(1, 1, 1, 0.7),
                h_align=Text.HAlign.CENTER,
                v_align=Text.VAlign.CENTER,
                transition=Text.Transition.FADE_IN,
                scale=1.6,
                maxwidth=150,
                transition_delay=2.0)

        # If we're a tournament, show prizes.
        try:
            tournament_id = self.session.tournament_id
            if tournament_id is not None:
                if tournament_id in ba.app.tournament_info:
                    tourney_info = ba.app.tournament_info[tournament_id]
                    # pylint: disable=unbalanced-tuple-unpacking
                    pr1, pv1, pr2, pv2, pr3, pv3 = (
                        get_tournament_prize_strings(tourney_info))
                    # pylint: enable=unbalanced-tuple-unpacking
                    Text(ba.Lstr(resource='coopSelectWindow.prizesText'),
                         position=(-360, -70 + 77),
                         color=(1, 1, 1, 0.7),
                         h_align=Text.HAlign.CENTER,
                         v_align=Text.VAlign.CENTER,
                         transition=Text.Transition.FADE_IN,
                         scale=1.0,
                         maxwidth=300,
                         transition_delay=2.0).autoretain()
                    vval = -107 + 70
                    for rng, val in ((pr1, pv1), (pr2, pv2), (pr3, pv3)):
                        Text(rng,
                             position=(-410 + 10, vval),
                             color=(1, 1, 1, 0.7),
                             h_align=Text.HAlign.RIGHT,
                             v_align=Text.VAlign.CENTER,
                             transition=Text.Transition.FADE_IN,
                             scale=0.6,
                             maxwidth=300,
                             transition_delay=2.0).autoretain()
                        Text(val,
                             position=(-390 + 10, vval),
                             color=(0.7, 0.7, 0.7, 1.0),
                             h_align=Text.HAlign.LEFT,
                             v_align=Text.VAlign.CENTER,
                             transition=Text.Transition.FADE_IN,
                             scale=0.8,
                             maxwidth=300,
                             transition_delay=2.0).autoretain()
                        vval -= 35
        except Exception:
            ba.print_exception('Error showing prize ranges.')

        if self._do_new_rating:
            if error:
                ZoomText(ba.Lstr(resource='failText'),
                         flash=True,
                         trail=True,
                         scale=1.0 if available else 0.333,
                         tilt_translate=0.11,
                         h_align='center',
                         position=(190 + offs_x, -60),
                         maxwidth=200,
                         jitter=1.0).autoretain()
                Text(ba.Lstr(translate=('serverResponses', error)),
                     position=(0, -140),
                     color=(1, 1, 1, 0.7),
                     h_align=Text.HAlign.CENTER,
                     v_align=Text.VAlign.CENTER,
                     transition=Text.Transition.FADE_IN,
                     scale=0.9,
                     maxwidth=400,
                     transition_delay=1.0).autoretain()
            else:
                ZoomText((('#' + str(player_rank)) if player_rank is not None
                          else ba.Lstr(resource='unavailableText')),
                         flash=True,
                         trail=True,
                         scale=1.0 if available else 0.333,
                         tilt_translate=0.11,
                         h_align='center',
                         position=(190 + offs_x, -60),
                         maxwidth=200,
                         jitter=1.0).autoretain()

                Text(ba.Lstr(value='${A}:',
                             subs=[('${A}', ba.Lstr(resource='rankText'))]),
                     position=(0, 36),
                     maxwidth=300,
                     transition=Text.Transition.FADE_IN,
                     h_align=Text.HAlign.CENTER,
                     v_align=Text.VAlign.CENTER,
                     transition_delay=0).autoretain()
                if best_player_rank is not None:
                    Text(ba.Lstr(resource='currentStandingText',
                                 fallback_resource='bestRankText',
                                 subs=[('${RANK}', str(best_player_rank))]),
                         position=(0, -155),
                         color=(1, 1, 1, 0.7),
                         h_align=Text.HAlign.CENTER,
                         transition=Text.Transition.FADE_IN,
                         scale=0.7,
                         transition_delay=1.0).autoretain()
        else:
            ZoomText((f'{rating:.1f}' if available else ba.Lstr(
                resource='unavailableText')),
                     flash=True,
                     trail=True,
                     scale=0.6 if available else 0.333,
                     tilt_translate=0.11,
                     h_align='center',
                     position=(190 + offs_x, -94),
                     maxwidth=200,
                     jitter=1.0).autoretain()

            if available:
                if rating >= 9.5:
                    stars = 3
                elif rating >= 7.5:
                    stars = 2
                elif rating > 0.0:
                    stars = 1
                else:
                    stars = 0
                star_tex = ba.gettexture('star')
                star_x = 135 + offs_x
                for _i in range(stars):
                    img = ba.NodeActor(
                        ba.newnode('image',
                                   attrs={
                                       'texture': star_tex,
                                       'position': (star_x, -16),
                                       'scale': (62, 62),
                                       'opacity': 1.0,
                                       'color': (2.2, 1.2, 0.3),
                                       'absolute_scale': True
                                   })).autoretain()

                    assert img.node
                    ba.animate(img.node, 'opacity', {0.15: 0, 0.4: 1})
                    star_x += 60
                for _i in range(3 - stars):
                    img = ba.NodeActor(
                        ba.newnode('image',
                                   attrs={
                                       'texture': star_tex,
                                       'position': (star_x, -16),
                                       'scale': (62, 62),
                                       'opacity': 1.0,
                                       'color': (0.3, 0.3, 0.3),
                                       'absolute_scale': True
                                   })).autoretain()
                    assert img.node
                    ba.animate(img.node, 'opacity', {0.15: 0, 0.4: 1})
                    star_x += 60

                def dostar(count: int, xval: float, offs_y: float,
                           score: str) -> None:
                    Text(score + ' =',
                         position=(xval, -64 + offs_y),
                         color=(0.6, 0.6, 0.6, 0.6),
                         h_align=Text.HAlign.CENTER,
                         v_align=Text.VAlign.CENTER,
                         transition=Text.Transition.FADE_IN,
                         scale=0.4,
                         transition_delay=1.0).autoretain()
                    stx = xval + 20
                    for _i2 in range(count):
                        img2 = ba.NodeActor(
                            ba.newnode('image',
                                       attrs={
                                           'texture': star_tex,
                                           'position': (stx, -64 + offs_y),
                                           'scale': (12, 12),
                                           'opacity': 0.7,
                                           'color': (2.2, 1.2, 0.3),
                                           'absolute_scale': True
                                       })).autoretain()
                        assert img2.node
                        ba.animate(img2.node, 'opacity', {1.0: 0.0, 1.5: 0.5})
                        stx += 13.0

                dostar(1, -44 - 30, -112, '0.0')
                dostar(2, 10 - 30, -112, '7.5')
                dostar(3, 77 - 30, -112, '9.5')
            try:
                best_rank = self._campaign.getlevel(self._level_name).rating
            except Exception:
                best_rank = 0.0

            if available:
                Text(ba.Lstr(
                    resource='outOfText',
                    subs=[('${RANK}',
                           str(int(self._show_info['results']['rank']))),
                          ('${ALL}', str(self._show_info['results']['total']))
                          ]),
                     position=(0, -155 if self._newly_complete else -145),
                     color=(1, 1, 1, 0.7),
                     h_align=Text.HAlign.CENTER,
                     transition=Text.Transition.FADE_IN,
                     scale=0.55,
                     transition_delay=1.0).autoretain()

            new_best = (best_rank > self._old_best_rank and best_rank > 0.0)
            was_string = ba.Lstr(value=' ${A}',
                                 subs=[('${A}',
                                        ba.Lstr(resource='scoreWasText')),
                                       ('${COUNT}', str(self._old_best_rank))])
            if not self._newly_complete:
                Text(ba.Lstr(value='${A}${B}',
                             subs=[('${A}',
                                    ba.Lstr(resource='newPersonalBestText')),
                                   ('${B}', was_string)]) if new_best else
                     ba.Lstr(resource='bestRatingText',
                             subs=[('${RATING}', str(best_rank))]),
                     position=(0, -165),
                     color=(1, 1, 1, 0.7),
                     flash=new_best,
                     h_align=Text.HAlign.CENTER,
                     transition=(Text.Transition.IN_RIGHT
                                 if new_best else Text.Transition.FADE_IN),
                     scale=0.5,
                     transition_delay=1.0).autoretain()

            Text(ba.Lstr(value='${A}:',
                         subs=[('${A}', ba.Lstr(resource='ratingText'))]),
                 position=(0, 36),
                 maxwidth=300,
                 transition=Text.Transition.FADE_IN,
                 h_align=Text.HAlign.CENTER,
                 v_align=Text.VAlign.CENTER,
                 transition_delay=0).autoretain()

        ba.timer(0.35, ba.Call(ba.playsound, self._score_display_sound))
        if not error:
            ba.timer(0.35, ba.Call(ba.playsound, self.cymbal_sound))

    def _show_fail(self) -> None:
        ZoomText(ba.Lstr(resource='failText'),
                 maxwidth=300,
                 flash=False,
                 trail=True,
                 h_align='center',
                 tilt_translate=0.11,
                 position=(0, 40),
                 jitter=1.0).autoretain()
        if self._fail_message is not None:
            Text(self._fail_message,
                 h_align=Text.HAlign.CENTER,
                 position=(0, -130),
                 maxwidth=300,
                 color=(1, 1, 1, 0.5),
                 transition=Text.Transition.FADE_IN,
                 transition_delay=1.0).autoretain()
        ba.timer(0.35, ba.Call(ba.playsound, self._score_display_sound))

    def _show_score_val(self, offs_x: float) -> None:
        assert self._score_type is not None
        assert self._score is not None
        ZoomText((str(self._score) if self._score_type == 'points' else
                  ba.timestring(self._score * 10,
                                timeformat=ba.TimeFormat.MILLISECONDS)),
                 maxwidth=300,
                 flash=True,
                 trail=True,
                 scale=1.0 if self._score_type == 'points' else 0.6,
                 h_align='center',
                 tilt_translate=0.11,
                 position=(190 + offs_x, 115),
                 jitter=1.0).autoretain()
        Text(ba.Lstr(
            value='${A}:', subs=[('${A}', ba.Lstr(
                resource='finalScoreText'))]) if self._score_type == 'points'
             else ba.Lstr(value='${A}:',
                          subs=[('${A}', ba.Lstr(resource='finalTimeText'))]),
             maxwidth=300,
             position=(0, 200),
             transition=Text.Transition.FADE_IN,
             h_align=Text.HAlign.CENTER,
             v_align=Text.VAlign.CENTER,
             transition_delay=0).autoretain()
        ba.timer(0.35, ba.Call(ba.playsound, self._score_display_sound))
