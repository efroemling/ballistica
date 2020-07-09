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
"""Functionality related to teams sessions."""
from __future__ import annotations

import copy
import random
from typing import TYPE_CHECKING

import _ba
from ba._session import Session
from ba._error import NotFoundError, print_error

if TYPE_CHECKING:
    from typing import Optional, Any, Dict, List, Type, Sequence
    import ba

DEFAULT_TEAM_COLORS = ((0.1, 0.25, 1.0), (1.0, 0.25, 0.2))
DEFAULT_TEAM_NAMES = ('Blue', 'Red')


class MultiTeamSession(Session):
    """Common base class for ba.DualTeamSession and ba.FreeForAllSession.

    Category: Gameplay Classes

    Free-for-all-mode is essentially just teams-mode with each ba.Player having
    their own ba.Team, so there is much overlap in functionality.
    """

    # These should be overridden.
    _playlist_selection_var = 'UNSET Playlist Selection'
    _playlist_randomize_var = 'UNSET Playlist Randomize'
    _playlists_var = 'UNSET Playlists'

    def __init__(self) -> None:
        """Set up playlists and launches a ba.Activity to accept joiners."""
        # pylint: disable=cyclic-import
        from ba import _playlist
        from bastd.activity.multiteamjoin import MultiTeamJoinActivity
        app = _ba.app
        cfg = app.config

        if self.use_teams:
            team_names = cfg.get('Custom Team Names', DEFAULT_TEAM_NAMES)
            team_colors = cfg.get('Custom Team Colors', DEFAULT_TEAM_COLORS)
        else:
            team_names = None
            team_colors = None

        # print('FIXME: TEAM BASE SESSION WOULD CALC DEPS.')
        depsets: Sequence[ba.DependencySet] = []

        super().__init__(depsets,
                         team_names=team_names,
                         team_colors=team_colors,
                         min_players=1,
                         max_players=self.get_max_players())

        self._series_length = app.teams_series_length
        self._ffa_series_length = app.ffa_series_length

        show_tutorial = cfg.get('Show Tutorial', True)

        self._tutorial_activity_instance: Optional[ba.Activity]
        if show_tutorial:
            from bastd.tutorial import TutorialActivity

            # Get this loading.
            self._tutorial_activity_instance = _ba.newactivity(
                TutorialActivity)
        else:
            self._tutorial_activity_instance = None

        self._playlist_name = cfg.get(self._playlist_selection_var,
                                      '__default__')
        self._playlist_randomize = cfg.get(self._playlist_randomize_var, False)

        # Which game activity we're on.
        self._game_number = 0

        playlists = cfg.get(self._playlists_var, {})

        if (self._playlist_name != '__default__'
                and self._playlist_name in playlists):

            # Make sure to copy this, as we muck with it in place once we've
            # got it and we don't want that to affect our config.
            playlist = copy.deepcopy(playlists[self._playlist_name])
        else:
            if self.use_teams:
                playlist = _playlist.get_default_teams_playlist()
            else:
                playlist = _playlist.get_default_free_for_all_playlist()

        # Resolve types and whatnot to get our final playlist.
        playlist_resolved = _playlist.filter_playlist(playlist,
                                                      sessiontype=type(self),
                                                      add_resolved_type=True)

        if not playlist_resolved:
            raise RuntimeError('Playlist contains no valid games.')

        self._playlist = ShuffleList(playlist_resolved,
                                     shuffle=self._playlist_randomize)

        # Get a game on deck ready to go.
        self._current_game_spec: Optional[Dict[str, Any]] = None
        self._next_game_spec: Dict[str, Any] = self._playlist.pull_next()
        self._next_game: Type[ba.GameActivity] = (
            self._next_game_spec['resolved_type'])

        # Go ahead and instantiate the next game we'll
        # use so it has lots of time to load.
        self._instantiate_next_game()

        # Start in our custom join screen.
        self.setactivity(_ba.newactivity(MultiTeamJoinActivity))

    def get_ffa_series_length(self) -> int:
        """Return free-for-all series length."""
        return self._ffa_series_length

    def get_series_length(self) -> int:
        """Return teams series length."""
        return self._series_length

    def get_next_game_description(self) -> ba.Lstr:
        """Returns a description of the next game on deck."""
        # pylint: disable=cyclic-import
        from ba._gameactivity import GameActivity
        gametype: Type[GameActivity] = self._next_game_spec['resolved_type']
        assert issubclass(gametype, GameActivity)
        return gametype.get_settings_display_string(self._next_game_spec)

    def get_game_number(self) -> int:
        """Returns which game in the series is currently being played."""
        return self._game_number

    def on_team_join(self, team: ba.SessionTeam) -> None:
        team.customdata['previous_score'] = team.customdata['score'] = 0

    def get_max_players(self) -> int:
        """Return max number of ba.Players allowed to join the game at once."""
        if self.use_teams:
            return _ba.app.config.get('Team Game Max Players', 8)
        return _ba.app.config.get('Free-for-All Max Players', 8)

    def _instantiate_next_game(self) -> None:
        self._next_game_instance = _ba.newactivity(
            self._next_game_spec['resolved_type'],
            self._next_game_spec['settings'])

    def on_activity_end(self, activity: ba.Activity, results: Any) -> None:
        # pylint: disable=cyclic-import
        from bastd.tutorial import TutorialActivity
        from bastd.activity.multiteamvictory import (
            TeamSeriesVictoryScoreScreenActivity)
        from ba._activitytypes import (TransitionActivity, JoinActivity,
                                       ScoreScreenActivity)

        # If we have a tutorial to show, that's the first thing we do no
        # matter what.
        if self._tutorial_activity_instance is not None:
            self.setactivity(self._tutorial_activity_instance)
            self._tutorial_activity_instance = None

        # If we're leaving the tutorial activity, pop a transition activity
        # to transition us into a round gracefully (otherwise we'd snap from
        # one terrain to another instantly).
        elif isinstance(activity, TutorialActivity):
            self.setactivity(_ba.newactivity(TransitionActivity))

        # If we're in a between-round activity or a restart-activity, hop
        # into a round.
        elif isinstance(
                activity,
            (JoinActivity, TransitionActivity, ScoreScreenActivity)):

            # If we're coming from a series-end activity, reset scores.
            if isinstance(activity, TeamSeriesVictoryScoreScreenActivity):
                self.stats.reset()
                self._game_number = 0
                for team in self.sessionteams:
                    team.customdata['score'] = 0

            # Otherwise just set accum (per-game) scores.
            else:
                self.stats.reset_accum()

            next_game = self._next_game_instance

            self._current_game_spec = self._next_game_spec
            self._next_game_spec = self._playlist.pull_next()
            self._game_number += 1

            # Instantiate the next now so they have plenty of time to load.
            self._instantiate_next_game()

            # (Re)register all players and wire stats to our next activity.
            for player in self.sessionplayers:
                # ..but only ones who have been placed on a team
                # (ie: no longer sitting in the lobby).
                try:
                    has_team = (player.sessionteam is not None)
                except NotFoundError:
                    has_team = False
                if has_team:
                    self.stats.register_sessionplayer(player)
            self.stats.setactivity(next_game)

            # Now flip the current activity.
            self.setactivity(next_game)

        # If we're leaving a round, go to the score screen.
        else:
            self._switch_to_score_screen(results)

    def _switch_to_score_screen(self, results: Any) -> None:
        """Switch to a score screen after leaving a round."""
        del results  # Unused arg.
        print_error('this should be overridden')

    def announce_game_results(self,
                              activity: ba.GameActivity,
                              results: ba.GameResults,
                              delay: float,
                              announce_winning_team: bool = True) -> None:
        """Show basic game result at the end of a game.

        (before transitioning to a score screen).
        This will include a zoom-text of 'BLUE WINS'
        or whatnot, along with a possible audio
        announcement of the same.
        """
        # pylint: disable=cyclic-import
        # pylint: disable=too-many-locals
        from ba._math import normalized_color
        from ba._general import Call
        from ba._gameutils import cameraflash
        from ba._lang import Lstr
        from ba._freeforallsession import FreeForAllSession
        from ba._messages import CelebrateMessage
        _ba.timer(delay, Call(_ba.playsound, _ba.getsound('boxingBell')))

        if announce_winning_team:
            winning_sessionteam = results.winning_sessionteam
            if winning_sessionteam is not None:
                # Have all players celebrate.
                celebrate_msg = CelebrateMessage(duration=10.0)
                assert winning_sessionteam.activityteam is not None
                for player in winning_sessionteam.activityteam.players:
                    if player.actor:
                        player.actor.handlemessage(celebrate_msg)
                cameraflash()

                # Some languages say "FOO WINS" different for teams vs players.
                if isinstance(self, FreeForAllSession):
                    wins_resource = 'winsPlayerText'
                else:
                    wins_resource = 'winsTeamText'
                wins_text = Lstr(resource=wins_resource,
                                 subs=[('${NAME}', winning_sessionteam.name)])
                activity.show_zoom_message(
                    wins_text,
                    scale=0.85,
                    color=normalized_color(winning_sessionteam.color),
                )


class ShuffleList:
    """Smart shuffler for game playlists.

    (avoids repeats in maps or game types)
    """

    def __init__(self, items: List[Dict[str, Any]], shuffle: bool = True):
        self.source_list = items
        self.shuffle = shuffle
        self.shuffle_list: List[Dict[str, Any]] = []
        self.last_gotten: Optional[Dict[str, Any]] = None

    def pull_next(self) -> Dict[str, Any]:
        """Pull and return the next item on the shuffle-list."""

        # Refill our list if its empty.
        if not self.shuffle_list:
            self.shuffle_list = list(self.source_list)

        # Ok now find an index we should pull.
        index = 0

        if self.shuffle:
            for _i in range(4):
                index = random.randrange(0, len(self.shuffle_list))
                test_obj = self.shuffle_list[index]

                # If the new one is the same map or game-type as the previous,
                # lets try to keep looking.
                if len(self.shuffle_list) > 1 and self.last_gotten is not None:
                    if (test_obj['settings']['map'] ==
                            self.last_gotten['settings']['map']):
                        continue
                    if test_obj['type'] == self.last_gotten['type']:
                        continue

                # Sufficiently different; lets go with it.
                break

        obj = self.shuffle_list.pop(index)
        self.last_gotten = obj
        return obj
