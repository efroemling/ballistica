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
"""Functionality related to the final screen in multi-teams sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.activity.multiteamscore import MultiTeamScoreScreenActivity

if TYPE_CHECKING:
    from typing import Any, Dict, List, Tuple, Optional


class TeamSeriesVictoryScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Final score screen for a team series."""

    # Dont' play music by default; (we do manually after a delay).
    default_music = None

    def __init__(self, settings: dict):
        super().__init__(settings=settings)
        self._min_view_time = 15.0
        self._is_ffa = isinstance(self.session, ba.FreeForAllSession)
        self._allow_server_transition = True
        self._tips_text = None
        self._default_show_tips = False

    def on_begin(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bastd.actor.text import Text
        from bastd.actor.image import Image
        from ba.deprecated import get_resource
        ba.set_analytics_screen('FreeForAll Series Victory Screen' if self.
                                _is_ffa else 'Teams Series Victory Screen')
        if ba.app.ui.uiscale is ba.UIScale.LARGE:
            sval = ba.Lstr(resource='pressAnyKeyButtonPlayAgainText')
        else:
            sval = ba.Lstr(resource='pressAnyButtonPlayAgainText')
        self._show_up_next = False
        self._custom_continue_message = sval
        super().on_begin()
        winning_sessionteam = self.settings_raw['winner']

        # Pause a moment before playing victory music.
        ba.timer(0.6, ba.WeakCall(self._play_victory_music))
        ba.timer(4.4,
                 ba.WeakCall(self._show_winner, self.settings_raw['winner']))
        ba.timer(4.6, ba.Call(ba.playsound, self._score_display_sound))

        # Score / Name / Player-record.
        player_entries: List[Tuple[int, str, ba.PlayerRecord]] = []

        # Note: for ffa, exclude players who haven't entered the game yet.
        if self._is_ffa:
            for _pkey, prec in self.stats.get_records().items():
                if prec.player.in_game:
                    player_entries.append(
                        (prec.player.sessionteam.customdata['score'],
                         prec.getname(full=True), prec))
            player_entries.sort(reverse=True, key=lambda x: x[0])
        else:
            for _pkey, prec in self.stats.get_records().items():
                player_entries.append((prec.score, prec.name_full, prec))
            player_entries.sort(reverse=True, key=lambda x: x[0])

        ts_height = 300.0
        ts_h_offs = -390.0
        tval = 6.4
        t_incr = 0.12

        always_use_first_to = get_resource('bestOfUseFirstToInstead')

        session = self.session
        if self._is_ffa:
            assert isinstance(session, ba.FreeForAllSession)
            txt = ba.Lstr(
                value='${A}:',
                subs=[('${A}',
                       ba.Lstr(resource='firstToFinalText',
                               subs=[('${COUNT}',
                                      str(session.get_ffa_series_length()))]))
                      ])
        else:
            assert isinstance(session, ba.MultiTeamSession)

            # Some languages may prefer to always show 'first to X' instead of
            # 'best of X'.
            # FIXME: This will affect all clients connected to us even if
            #  they're not using this language. Should try to come up
            #  with a wording that works everywhere.
            if always_use_first_to:
                txt = ba.Lstr(
                    value='${A}:',
                    subs=[
                        ('${A}',
                         ba.Lstr(resource='firstToFinalText',
                                 subs=[
                                     ('${COUNT}',
                                      str(session.get_series_length() / 2 + 1))
                                 ]))
                    ])
            else:
                txt = ba.Lstr(
                    value='${A}:',
                    subs=[('${A}',
                           ba.Lstr(resource='bestOfFinalText',
                                   subs=[('${COUNT}',
                                          str(session.get_series_length()))]))
                          ])

        Text(txt,
             v_align=Text.VAlign.CENTER,
             maxwidth=300,
             color=(0.5, 0.5, 0.5, 1.0),
             position=(0, 220),
             scale=1.2,
             transition=Text.Transition.IN_TOP_SLOW,
             h_align=Text.HAlign.CENTER,
             transition_delay=t_incr * 4).autoretain()

        win_score = (session.get_series_length() - 1) // 2 + 1
        lose_score = 0
        for team in self.teams:
            if team.sessionteam.customdata['score'] != win_score:
                lose_score = team.sessionteam.customdata['score']

        if not self._is_ffa:
            Text(ba.Lstr(resource='gamesToText',
                         subs=[('${WINCOUNT}', str(win_score)),
                               ('${LOSECOUNT}', str(lose_score))]),
                 color=(0.5, 0.5, 0.5, 1.0),
                 maxwidth=160,
                 v_align=Text.VAlign.CENTER,
                 position=(0, -215),
                 scale=1.8,
                 transition=Text.Transition.IN_LEFT,
                 h_align=Text.HAlign.CENTER,
                 transition_delay=4.8 + t_incr * 4).autoretain()

        if self._is_ffa:
            v_extra = 120
        else:
            v_extra = 0

        mvp: Optional[ba.PlayerRecord] = None
        mvp_name: Optional[str] = None

        # Show game MVP.
        if not self._is_ffa:
            mvp, mvp_name = None, None
            for entry in player_entries:
                if entry[2].team == winning_sessionteam:
                    mvp = entry[2]
                    mvp_name = entry[1]
                    break
            if mvp is not None:
                Text(ba.Lstr(resource='mostValuablePlayerText'),
                     color=(0.5, 0.5, 0.5, 1.0),
                     v_align=Text.VAlign.CENTER,
                     maxwidth=300,
                     position=(180, ts_height / 2 + 15),
                     transition=Text.Transition.IN_LEFT,
                     h_align=Text.HAlign.LEFT,
                     transition_delay=tval).autoretain()
                tval += 4 * t_incr

                Image(mvp.get_icon(),
                      position=(230, ts_height / 2 - 55 + 14 - 5),
                      scale=(70, 70),
                      transition=Image.Transition.IN_LEFT,
                      transition_delay=tval).autoretain()
                assert mvp_name is not None
                Text(ba.Lstr(value=mvp_name),
                     position=(280, ts_height / 2 - 55 + 15 - 5),
                     h_align=Text.HAlign.LEFT,
                     v_align=Text.VAlign.CENTER,
                     maxwidth=170,
                     scale=1.3,
                     color=ba.safecolor(mvp.team.color + (1, )),
                     transition=Text.Transition.IN_LEFT,
                     transition_delay=tval).autoretain()
                tval += 4 * t_incr

        # Most violent.
        most_kills = 0
        for entry in player_entries:
            if entry[2].kill_count >= most_kills:
                mvp = entry[2]
                mvp_name = entry[1]
                most_kills = entry[2].kill_count
        if mvp is not None:
            Text(ba.Lstr(resource='mostViolentPlayerText'),
                 color=(0.5, 0.5, 0.5, 1.0),
                 v_align=Text.VAlign.CENTER,
                 maxwidth=300,
                 position=(180, ts_height / 2 - 150 + v_extra + 15),
                 transition=Text.Transition.IN_LEFT,
                 h_align=Text.HAlign.LEFT,
                 transition_delay=tval).autoretain()
            Text(ba.Lstr(value='(${A})',
                         subs=[('${A}',
                                ba.Lstr(resource='killsTallyText',
                                        subs=[('${COUNT}', str(most_kills))]))
                               ]),
                 position=(260, ts_height / 2 - 150 - 15 + v_extra),
                 color=(0.3, 0.3, 0.3, 1.0),
                 scale=0.6,
                 h_align=Text.HAlign.LEFT,
                 transition=Text.Transition.IN_LEFT,
                 transition_delay=tval).autoretain()
            tval += 4 * t_incr

            Image(mvp.get_icon(),
                  position=(233, ts_height / 2 - 150 - 30 - 46 + 25 + v_extra),
                  scale=(50, 50),
                  transition=Image.Transition.IN_LEFT,
                  transition_delay=tval).autoretain()
            assert mvp_name is not None
            Text(ba.Lstr(value=mvp_name),
                 position=(270, ts_height / 2 - 150 - 30 - 36 + v_extra + 15),
                 h_align=Text.HAlign.LEFT,
                 v_align=Text.VAlign.CENTER,
                 maxwidth=180,
                 color=ba.safecolor(mvp.team.color + (1, )),
                 transition=Text.Transition.IN_LEFT,
                 transition_delay=tval).autoretain()
            tval += 4 * t_incr

        # Most killed.
        most_killed = 0
        mkp, mkp_name = None, None
        for entry in player_entries:
            if entry[2].killed_count >= most_killed:
                mkp = entry[2]
                mkp_name = entry[1]
                most_killed = entry[2].killed_count
        if mkp is not None:
            Text(ba.Lstr(resource='mostViolatedPlayerText'),
                 color=(0.5, 0.5, 0.5, 1.0),
                 v_align=Text.VAlign.CENTER,
                 maxwidth=300,
                 position=(180, ts_height / 2 - 300 + v_extra + 15),
                 transition=Text.Transition.IN_LEFT,
                 h_align=Text.HAlign.LEFT,
                 transition_delay=tval).autoretain()
            Text(ba.Lstr(value='(${A})',
                         subs=[('${A}',
                                ba.Lstr(resource='deathsTallyText',
                                        subs=[('${COUNT}', str(most_killed))]))
                               ]),
                 position=(260, ts_height / 2 - 300 - 15 + v_extra),
                 h_align=Text.HAlign.LEFT,
                 scale=0.6,
                 color=(0.3, 0.3, 0.3, 1.0),
                 transition=Text.Transition.IN_LEFT,
                 transition_delay=tval).autoretain()
            tval += 4 * t_incr
            Image(mkp.get_icon(),
                  position=(233, ts_height / 2 - 300 - 30 - 46 + 25 + v_extra),
                  scale=(50, 50),
                  transition=Image.Transition.IN_LEFT,
                  transition_delay=tval).autoretain()
            assert mkp_name is not None
            Text(ba.Lstr(value=mkp_name),
                 position=(270, ts_height / 2 - 300 - 30 - 36 + v_extra + 15),
                 h_align=Text.HAlign.LEFT,
                 v_align=Text.VAlign.CENTER,
                 color=ba.safecolor(mkp.team.color + (1, )),
                 maxwidth=180,
                 transition=Text.Transition.IN_LEFT,
                 transition_delay=tval).autoretain()
            tval += 4 * t_incr

        # Now show individual scores.
        tdelay = tval
        Text(ba.Lstr(resource='finalScoresText'),
             color=(0.5, 0.5, 0.5, 1.0),
             position=(ts_h_offs, ts_height / 2),
             transition=Text.Transition.IN_RIGHT,
             transition_delay=tdelay).autoretain()
        tdelay += 4 * t_incr

        v_offs = 0.0
        tdelay += len(player_entries) * 8 * t_incr
        for _score, name, prec in player_entries:
            tdelay -= 4 * t_incr
            v_offs -= 40
            Text(str(prec.team.customdata['score'])
                 if self._is_ffa else str(prec.score),
                 color=(0.5, 0.5, 0.5, 1.0),
                 position=(ts_h_offs + 230, ts_height / 2 + v_offs),
                 h_align=Text.HAlign.RIGHT,
                 transition=Text.Transition.IN_RIGHT,
                 transition_delay=tdelay).autoretain()
            tdelay -= 4 * t_incr

            Image(prec.get_icon(),
                  position=(ts_h_offs - 72, ts_height / 2 + v_offs + 15),
                  scale=(30, 30),
                  transition=Image.Transition.IN_LEFT,
                  transition_delay=tdelay).autoretain()
            Text(ba.Lstr(value=name),
                 position=(ts_h_offs - 50, ts_height / 2 + v_offs + 15),
                 h_align=Text.HAlign.LEFT,
                 v_align=Text.VAlign.CENTER,
                 maxwidth=180,
                 color=ba.safecolor(prec.team.color + (1, )),
                 transition=Text.Transition.IN_RIGHT,
                 transition_delay=tdelay).autoretain()

        ba.timer(15.0, ba.WeakCall(self._show_tips))

    def _show_tips(self) -> None:
        from bastd.actor.tipstext import TipsText
        self._tips_text = TipsText(offs_y=70)

    def _play_victory_music(self) -> None:

        # Make sure we don't stomp on the next activity's music choice.
        if not self.is_transitioning_out():
            ba.setmusic(ba.MusicType.VICTORY)

    def _show_winner(self, team: ba.SessionTeam) -> None:
        from bastd.actor.image import Image
        from bastd.actor.zoomtext import ZoomText
        if not self._is_ffa:
            offs_v = 0.0
            ZoomText(team.name,
                     position=(0, 97),
                     color=team.color,
                     scale=1.15,
                     jitter=1.0,
                     maxwidth=250).autoretain()
        else:
            offs_v = -80.0
            if len(team.players) == 1:
                i = Image(team.players[0].get_icon(),
                          position=(0, 143),
                          scale=(100, 100)).autoretain()
                assert i.node
                ba.animate(i.node, 'opacity', {0.0: 0.0, 0.25: 1.0})
                ZoomText(ba.Lstr(
                    value=team.players[0].getname(full=True, icon=False)),
                         position=(0, 97 + offs_v),
                         color=team.color,
                         scale=1.15,
                         jitter=1.0,
                         maxwidth=250).autoretain()

        s_extra = 1.0 if self._is_ffa else 1.0

        # Some languages say "FOO WINS" differently for teams vs players.
        if isinstance(self.session, ba.FreeForAllSession):
            wins_resource = 'seriesWinLine1PlayerText'
        else:
            wins_resource = 'seriesWinLine1TeamText'
        wins_text = ba.Lstr(resource=wins_resource)

        # Temp - if these come up as the english default, fall-back to the
        # unified old form which is more likely to be translated.
        ZoomText(wins_text,
                 position=(0, -10 + offs_v),
                 color=team.color,
                 scale=0.65 * s_extra,
                 jitter=1.0,
                 maxwidth=250).autoretain()
        ZoomText(ba.Lstr(resource='seriesWinLine2Text'),
                 position=(0, -110 + offs_v),
                 scale=1.0 * s_extra,
                 color=team.color,
                 jitter=1.0,
                 maxwidth=250).autoretain()
