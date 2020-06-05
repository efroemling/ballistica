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
"""Functionality related to teams mode score screen."""
from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from ba.internal import ScoreScreenActivity
from bastd.actor.text import Text
from bastd.actor.image import Image

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Union


class MultiTeamScoreScreenActivity(ScoreScreenActivity):
    """Base class for score screens."""

    def __init__(self, settings: dict):
        super().__init__(settings=settings)
        self._score_display_sound = ba.getsound('scoreHit01')
        self._score_display_sound_small = ba.getsound('scoreHit02')

        self._show_up_next: bool = True

    def on_begin(self) -> None:
        super().on_begin()
        session = self.session
        if self._show_up_next and isinstance(session, ba.MultiTeamSession):
            txt = ba.Lstr(value='${A}   ${B}',
                          subs=[
                              ('${A}',
                               ba.Lstr(resource='upNextText',
                                       subs=[
                                           ('${COUNT}',
                                            str(session.get_game_number() + 1))
                                       ])),
                              ('${B}', session.get_next_game_description())
                          ])
            Text(txt,
                 maxwidth=900,
                 h_attach=Text.HAttach.CENTER,
                 v_attach=Text.VAttach.BOTTOM,
                 h_align=Text.HAlign.CENTER,
                 v_align=Text.VAlign.CENTER,
                 position=(0, 53),
                 flash=False,
                 color=(0.3, 0.3, 0.35, 1.0),
                 transition=Text.Transition.FADE_IN,
                 transition_delay=2.0).autoretain()

    def show_player_scores(self,
                           delay: float = 2.5,
                           results: Optional[ba.GameResults] = None,
                           scale: float = 1.0,
                           x_offset: float = 0.0,
                           y_offset: float = 0.0) -> None:
        """Show scores for individual players."""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        ts_v_offset = 150.0 + y_offset
        ts_h_offs = 80.0 + x_offset
        tdelay = delay
        spacing = 40

        is_free_for_all = isinstance(self.session, ba.FreeForAllSession)

        def _get_prec_score(p_rec: ba.PlayerRecord) -> Optional[int]:
            if is_free_for_all and results is not None:
                assert isinstance(results, ba.GameResults)
                assert p_rec.team.activityteam is not None
                val = results.get_sessionteam_score(p_rec.team)
                return val
            return p_rec.accumscore

        def _get_prec_score_str(p_rec: ba.PlayerRecord) -> Union[str, ba.Lstr]:
            if is_free_for_all and results is not None:
                assert isinstance(results, ba.GameResults)
                assert p_rec.team.activityteam is not None
                val = results.get_sessionteam_score_str(p_rec.team)
                assert val is not None
                return val
            return str(p_rec.accumscore)

        # stats.get_records() can return players that are no longer in
        # the game.. if we're using results we have to filter those out
        # (since they're not in results and that's where we pull their
        # scores from)
        if results is not None:
            assert isinstance(results, ba.GameResults)
            player_records = []
            assert self.stats
            valid_players = list(self.stats.get_records().items())

            def _get_player_score_set_entry(
                    player: ba.SessionPlayer) -> Optional[ba.PlayerRecord]:
                for p_rec in valid_players:
                    if p_rec[1].player is player:
                        return p_rec[1]
                return None

            # Results is already sorted; just convert it into a list of
            # score-set-entries.
            for winnergroup in results.winnergroups:
                for team in winnergroup.teams:
                    if len(team.players) == 1:
                        player_entry = _get_player_score_set_entry(
                            team.players[0])
                        if player_entry is not None:
                            player_records.append(player_entry)
        else:
            player_records = []
            player_records_scores = [
                (_get_prec_score(p), name, p)
                for name, p in list(self.stats.get_records().items())
            ]
            player_records_scores.sort(reverse=True)

            # Just want living player entries.
            player_records = [p[2] for p in player_records_scores if p[2]]

        voffs = -140.0 + spacing * len(player_records) * 0.5

        def _txt(xoffs: float,
                 yoffs: float,
                 text: ba.Lstr,
                 h_align: Text.HAlign = Text.HAlign.RIGHT,
                 extrascale: float = 1.0,
                 maxwidth: Optional[float] = 120.0) -> None:
            Text(text,
                 color=(0.5, 0.5, 0.6, 0.5),
                 position=(ts_h_offs + xoffs * scale,
                           ts_v_offset + (voffs + yoffs + 4.0) * scale),
                 h_align=h_align,
                 v_align=Text.VAlign.CENTER,
                 scale=0.8 * scale * extrascale,
                 maxwidth=maxwidth,
                 transition=Text.Transition.IN_LEFT,
                 transition_delay=tdelay).autoretain()

        session = self.session
        assert isinstance(session, ba.MultiTeamSession)
        tval = ba.Lstr(resource='gameLeadersText',
                       subs=[('${COUNT}', str(session.get_game_number()))])
        _txt(180,
             43,
             tval,
             h_align=Text.HAlign.CENTER,
             extrascale=1.4,
             maxwidth=None)
        _txt(-15, 4, ba.Lstr(resource='playerText'), h_align=Text.HAlign.LEFT)
        _txt(180, 4, ba.Lstr(resource='killsText'))
        _txt(280, 4, ba.Lstr(resource='deathsText'), maxwidth=100)

        score_label = 'Score' if results is None else results.score_label
        translated = ba.Lstr(translate=('scoreNames', score_label))

        _txt(390, 0, translated)

        topkillcount = 0
        topkilledcount = 99999
        top_score = 0 if not player_records else _get_prec_score(
            player_records[0])

        for prec in player_records:
            topkillcount = max(topkillcount, prec.accum_kill_count)
            topkilledcount = min(topkilledcount, prec.accum_killed_count)

        def _scoretxt(text: Union[str, ba.Lstr],
                      x_offs: float,
                      highlight: bool,
                      delay2: float,
                      maxwidth: float = 70.0) -> None:
            Text(text,
                 position=(ts_h_offs + x_offs * scale,
                           ts_v_offset + (voffs + 15) * scale),
                 scale=scale,
                 color=(1.0, 0.9, 0.5, 1.0) if highlight else
                 (0.5, 0.5, 0.6, 0.5),
                 h_align=Text.HAlign.RIGHT,
                 v_align=Text.VAlign.CENTER,
                 maxwidth=maxwidth,
                 transition=Text.Transition.IN_LEFT,
                 transition_delay=tdelay + delay2).autoretain()

        for playerrec in player_records:
            tdelay += 0.05
            voffs -= spacing
            Image(playerrec.get_icon(),
                  position=(ts_h_offs - 12 * scale,
                            ts_v_offset + (voffs + 15.0) * scale),
                  scale=(30.0 * scale, 30.0 * scale),
                  transition=Image.Transition.IN_LEFT,
                  transition_delay=tdelay).autoretain()
            Text(ba.Lstr(value=playerrec.getname(full=True)),
                 maxwidth=160,
                 scale=0.75 * scale,
                 position=(ts_h_offs + 10.0 * scale,
                           ts_v_offset + (voffs + 15) * scale),
                 h_align=Text.HAlign.LEFT,
                 v_align=Text.VAlign.CENTER,
                 color=ba.safecolor(playerrec.team.color + (1, )),
                 transition=Text.Transition.IN_LEFT,
                 transition_delay=tdelay).autoretain()
            _scoretxt(str(playerrec.accum_kill_count), 180,
                      playerrec.accum_kill_count == topkillcount, 0.1)
            _scoretxt(str(playerrec.accum_killed_count), 280,
                      playerrec.accum_killed_count == topkilledcount, 0.1)
            _scoretxt(_get_prec_score_str(playerrec), 390,
                      _get_prec_score(playerrec) == top_score, 0.2)
