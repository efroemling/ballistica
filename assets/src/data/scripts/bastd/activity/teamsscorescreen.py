# Copyright (c) 2011-2019 Eric Froemling
"""Functionality related to teams mode score screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from ba.internal import ScoreScreenActivity

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Union
    from ba import PlayerRecord


class TeamsScoreScreenActivity(ScoreScreenActivity):
    """Base class for score screens."""

    def __init__(self, settings: Dict[str, Any]):
        super().__init__(settings=settings)
        self._score_display_sound = ba.getsound("scoreHit01")
        self._score_display_sound_small = ba.getsound("scoreHit02")

    def on_begin(  # type: ignore
            self,
            show_up_next: bool = True,
            custom_continue_message: ba.Lstr = None) -> None:
        # FIXME FIXME unify args
        # pylint: disable=arguments-differ
        from bastd.actor.text import Text
        super().on_begin(custom_continue_message=custom_continue_message)
        session = self.session
        if show_up_next and isinstance(session, ba.TeamBaseSession):
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
                 h_attach='center',
                 v_attach='bottom',
                 h_align='center',
                 v_align='center',
                 position=(0, 53),
                 flash=False,
                 color=(0.3, 0.3, 0.35, 1.0),
                 transition='fade_in',
                 transition_delay=2.0).autoretain()

    def show_player_scores(self,
                           delay: float = 2.5,
                           results: Any = None,
                           scale: float = 1.0,
                           x_offset: float = 0.0,
                           y_offset: float = 0.0) -> None:
        """Show scores for individual players."""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bastd.actor.text import Text
        from bastd.actor.image import Image
        from ba import FreeForAllSession

        ts_v_offset = 150.0 + y_offset
        ts_h_offs = 80.0 + x_offset
        tdelay = delay
        spacing = 40

        is_free_for_all = isinstance(self.session, FreeForAllSession)

        def _get_prec_score(p_rec: PlayerRecord) -> int:
            if is_free_for_all and results is not None:
                assert isinstance(results, ba.TeamGameResults)
                val = results.get_team_score(p_rec.team)
                assert val is not None
                return val
            return p_rec.accumscore

        def _get_prec_score_str(p_rec: PlayerRecord) -> Union[str, ba.Lstr]:
            if is_free_for_all and results is not None:
                assert isinstance(results, ba.TeamGameResults)
                val = results.get_team_score_str(p_rec.team)
                assert val is not None
                return val
            return str(p_rec.accumscore)

        # get_records() can return players that are no longer in
        # the game.. if we're using results we have to filter those out
        # (since they're not in results and that's where we pull their
        # scores from)
        if results is not None:
            assert isinstance(results, ba.TeamGameResults)
            player_records = []
            assert self.stats
            valid_players = list(self.stats.get_records().items())

            def _get_player_score_set_entry(player: ba.Player
                                            ) -> Optional[PlayerRecord]:
                for p_rec in valid_players:
                    # PyCharm incorrectly thinks valid_players is a List[str]
                    # noinspection PyUnresolvedReferences
                    if p_rec[1].player is player:
                        # noinspection PyTypeChecker
                        return p_rec[1]
                return None

            # Results is already sorted; just convert it into a list of
            # score-set-entries.
            for winner in results.get_winners():
                for team in winner.teams:
                    if len(team.players) == 1:
                        player_entry = _get_player_score_set_entry(
                            team.players[0])
                        if player_entry is not None:
                            player_records.append(player_entry)
        else:
            raise Exception('FIXME; CODE PATH NEEDS FIXING')
            # player_records = [[
            #     _get_prec_score(p), name, p
            # ] for name, p in list(self.stats.get_records().items())]
            # player_records.sort(
            #     reverse=(results is None
            #             or not results.get_lower_is_better()))
            # # just want living player entries
            # player_records = [p[2] for p in player_records if p[2]]

        v_offs = -140.0 + spacing * len(player_records) * 0.5

        def _txt(x_offs: float,
                 y_offs: float,
                 text: ba.Lstr,
                 h_align: str = 'right',
                 extrascale: float = 1.0,
                 maxwidth: Optional[float] = 120.0) -> None:
            Text(text,
                 color=(0.5, 0.5, 0.6, 0.5),
                 position=(ts_h_offs + x_offs * scale,
                           ts_v_offset + (v_offs + y_offs + 4.0) * scale),
                 h_align=h_align,
                 v_align='center',
                 scale=0.8 * scale * extrascale,
                 maxwidth=maxwidth,
                 transition='in_left',
                 transition_delay=tdelay).autoretain()

        session = self.session
        assert isinstance(session, ba.TeamBaseSession)
        tval = ba.Lstr(resource='gameLeadersText',
                       subs=[('${COUNT}', str(session.get_game_number()))])
        _txt(180, 43, tval, h_align='center', extrascale=1.4, maxwidth=None)
        _txt(-15, 4, ba.Lstr(resource='playerText'), h_align='left')
        _txt(180, 4, ba.Lstr(resource='killsText'))
        _txt(280, 4, ba.Lstr(resource='deathsText'), maxwidth=100)

        score_name = 'Score' if results is None else results.get_score_name()
        translated = ba.Lstr(translate=('scoreNames', score_name))

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
                           ts_v_offset + (v_offs + 15) * scale),
                 scale=scale,
                 color=(1.0, 0.9, 0.5, 1.0) if highlight else
                 (0.5, 0.5, 0.6, 0.5),
                 h_align='right',
                 v_align='center',
                 maxwidth=maxwidth,
                 transition='in_left',
                 transition_delay=tdelay + delay2).autoretain()

        for playerrec in player_records:
            tdelay += 0.05
            v_offs -= spacing
            Image(playerrec.get_icon(),
                  position=(ts_h_offs - 12 * scale,
                            ts_v_offset + (v_offs + 15.0) * scale),
                  scale=(30.0 * scale, 30.0 * scale),
                  transition='in_left',
                  transition_delay=tdelay).autoretain()
            Text(ba.Lstr(value=playerrec.get_name(full=True)),
                 maxwidth=160,
                 scale=0.75 * scale,
                 position=(ts_h_offs + 10.0 * scale,
                           ts_v_offset + (v_offs + 15) * scale),
                 h_align='left',
                 v_align='center',
                 color=ba.safecolor(playerrec.team.color + (1, )),
                 transition='in_left',
                 transition_delay=tdelay).autoretain()
            _scoretxt(str(playerrec.accum_kill_count), 180,
                      playerrec.accum_kill_count == topkillcount, 100)
            _scoretxt(str(playerrec.accum_killed_count), 280,
                      playerrec.accum_killed_count == topkilledcount, 100)
            _scoretxt(_get_prec_score_str(playerrec), 390,
                      _get_prec_score(playerrec) == top_score, 200)
