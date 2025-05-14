# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the final screen in multi-teams sessions."""

from __future__ import annotations

from typing import override, TYPE_CHECKING

import bascenev1 as bs

from bascenev1lib.activity.multiteamscore import MultiTeamScoreScreenActivity

if TYPE_CHECKING:
    from typing import Any


class TeamSeriesVictoryScoreScreenActivity(MultiTeamScoreScreenActivity):
    """Final score screen for a team series."""

    # Dont' play music by default; (we do manually after a delay).
    default_music = None

    def __init__(self, settings: dict):
        super().__init__(settings=settings)
        self._min_view_time = 15.0
        self._is_ffa = isinstance(self.session, bs.FreeForAllSession)
        self._allow_server_transition = True
        self._tips_text = None
        self._default_show_tips = False
        self._ffa_top_player_info: list[Any] | None = None
        self._ffa_top_player_rec: bs.PlayerRecord | None = None

    @override
    def on_begin(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bascenev1lib.actor.text import Text
        from bascenev1lib.actor.image import Image

        bs.set_analytics_screen(
            'FreeForAll Series Victory Screen'
            if self._is_ffa
            else 'Teams Series Victory Screen'
        )
        assert bs.app.classic is not None
        if bs.app.ui_v1.uiscale is bs.UIScale.LARGE:
            sval = bs.Lstr(resource='pressAnyKeyButtonPlayAgainText')
        else:
            sval = bs.Lstr(resource='pressAnyButtonPlayAgainText')
        self._show_up_next = False
        self._custom_continue_message = sval
        super().on_begin()
        winning_sessionteam = self.settings_raw['winner']

        # Pause a moment before playing victory music.
        bs.timer(0.6, bs.WeakCall(self._play_victory_music))
        bs.timer(
            4.4, bs.WeakCall(self._show_winner, self.settings_raw['winner'])
        )
        bs.timer(4.6, self._score_display_sound.play)

        # Score / Name / Player-record.
        player_entries: list[tuple[int, str, bs.PlayerRecord]] = []

        # Note: for ffa, exclude players who haven't entered the game yet.
        if self._is_ffa:
            for _pkey, prec in self.stats.get_records().items():
                if prec.player.in_game:
                    player_entries.append(
                        (
                            prec.player.sessionteam.customdata['score'],
                            prec.getname(full=True),
                            prec,
                        )
                    )
            player_entries.sort(reverse=True, key=lambda x: x[0])
            if len(player_entries) > 0:
                # Store some info for the top ffa player so we can
                # show winner info even if they leave.
                self._ffa_top_player_info = list(player_entries[0])
                self._ffa_top_player_info[1] = self._ffa_top_player_info[
                    2
                ].getname()
                self._ffa_top_player_info[2] = self._ffa_top_player_info[
                    2
                ].get_icon()
        else:
            for _pkey, prec in self.stats.get_records().items():
                player_entries.append((prec.score, prec.name_full, prec))
            player_entries.sort(reverse=True, key=lambda x: x[0])

        ts_height = 300.0
        ts_h_offs = -390.0
        tval = 6.4
        t_incr = 0.12

        always_use_first_to = bs.app.lang.get_resource(
            'bestOfUseFirstToInstead'
        )

        session = self.session
        if self._is_ffa:
            assert isinstance(session, bs.FreeForAllSession)
            txt = bs.Lstr(
                value='${A}:',
                subs=[
                    (
                        '${A}',
                        bs.Lstr(
                            resource='firstToFinalText',
                            subs=[
                                (
                                    '${COUNT}',
                                    str(session.get_ffa_series_length()),
                                )
                            ],
                        ),
                    )
                ],
            )
        else:
            assert isinstance(session, bs.MultiTeamSession)

            # Some languages may prefer to always show 'first to X' instead of
            # 'best of X'.
            # FIXME: This will affect all clients connected to us even if
            #  they're not using this language. Should try to come up
            #  with a wording that works everywhere.
            if always_use_first_to:
                txt = bs.Lstr(
                    value='${A}:',
                    subs=[
                        (
                            '${A}',
                            bs.Lstr(
                                resource='firstToFinalText',
                                subs=[
                                    (
                                        '${COUNT}',
                                        str(
                                            session.get_series_length() / 2 + 1
                                        ),
                                    )
                                ],
                            ),
                        )
                    ],
                )
            else:
                txt = bs.Lstr(
                    value='${A}:',
                    subs=[
                        (
                            '${A}',
                            bs.Lstr(
                                resource='bestOfFinalText',
                                subs=[
                                    (
                                        '${COUNT}',
                                        str(session.get_series_length()),
                                    )
                                ],
                            ),
                        )
                    ],
                )

        Text(
            txt,
            v_align=Text.VAlign.CENTER,
            maxwidth=300,
            color=(0.5, 0.5, 0.5, 1.0),
            position=(0, 220),
            scale=1.2,
            transition=Text.Transition.IN_TOP_SLOW,
            h_align=Text.HAlign.CENTER,
            transition_delay=t_incr * 4,
        ).autoretain()

        win_score = (session.get_series_length() - 1) // 2 + 1
        lose_score = 0
        for team in self.teams:
            if team.sessionteam.customdata['score'] != win_score:
                lose_score = team.sessionteam.customdata['score']

        if not self._is_ffa:
            Text(
                bs.Lstr(
                    resource='gamesToText',
                    subs=[
                        ('${WINCOUNT}', str(win_score)),
                        ('${LOSECOUNT}', str(lose_score)),
                    ],
                ),
                color=(0.5, 0.5, 0.5, 1.0),
                maxwidth=160,
                v_align=Text.VAlign.CENTER,
                position=(0, -215),
                scale=1.8,
                transition=Text.Transition.IN_LEFT,
                h_align=Text.HAlign.CENTER,
                transition_delay=4.8 + t_incr * 4,
            ).autoretain()

        if self._is_ffa:
            v_extra = 120
        else:
            v_extra = 0

        mvp: bs.PlayerRecord | None = None
        mvp_name: str | None = None

        # Show game MVP.
        if not self._is_ffa:
            mvp, mvp_name = None, None
            for entry in player_entries:
                if entry[2].team == winning_sessionteam:
                    mvp = entry[2]
                    mvp_name = entry[1]
                    break
            if mvp is not None:
                Text(
                    bs.Lstr(resource='mostValuablePlayerText'),
                    color=(0.5, 0.5, 0.5, 1.0),
                    v_align=Text.VAlign.CENTER,
                    maxwidth=300,
                    position=(180, ts_height / 2 + 15),
                    transition=Text.Transition.IN_LEFT,
                    h_align=Text.HAlign.LEFT,
                    transition_delay=tval,
                ).autoretain()
                tval += 4 * t_incr

                Image(
                    mvp.get_icon(),
                    position=(230, ts_height / 2 - 55 + 14 - 5),
                    scale=(70, 70),
                    transition=Image.Transition.IN_LEFT,
                    transition_delay=tval,
                ).autoretain()
                assert mvp_name is not None
                Text(
                    bs.Lstr(value=mvp_name),
                    position=(280, ts_height / 2 - 55 + 15 - 5),
                    h_align=Text.HAlign.LEFT,
                    v_align=Text.VAlign.CENTER,
                    maxwidth=170,
                    scale=1.3,
                    color=bs.safecolor(mvp.team.color + (1,)),
                    transition=Text.Transition.IN_LEFT,
                    transition_delay=tval,
                ).autoretain()
                tval += 4 * t_incr

        # Most violent.
        most_kills = 0
        for entry in player_entries:
            if entry[2].kill_count >= most_kills:
                mvp = entry[2]
                mvp_name = entry[1]
                most_kills = entry[2].kill_count
        if mvp is not None:
            Text(
                bs.Lstr(resource='mostViolentPlayerText'),
                color=(0.5, 0.5, 0.5, 1.0),
                v_align=Text.VAlign.CENTER,
                maxwidth=300,
                position=(180, ts_height / 2 - 150 + v_extra + 15),
                transition=Text.Transition.IN_LEFT,
                h_align=Text.HAlign.LEFT,
                transition_delay=tval,
            ).autoretain()
            Text(
                bs.Lstr(
                    value='(${A})',
                    subs=[
                        (
                            '${A}',
                            bs.Lstr(
                                resource='killsTallyText',
                                subs=[('${COUNT}', str(most_kills))],
                            ),
                        )
                    ],
                ),
                position=(260, ts_height / 2 - 150 - 15 + v_extra),
                color=(0.3, 0.3, 0.3, 1.0),
                scale=0.6,
                h_align=Text.HAlign.LEFT,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            tval += 4 * t_incr

            Image(
                mvp.get_icon(),
                position=(233, ts_height / 2 - 150 - 30 - 46 + 25 + v_extra),
                scale=(50, 50),
                transition=Image.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            assert mvp_name is not None
            Text(
                bs.Lstr(value=mvp_name),
                position=(270, ts_height / 2 - 150 - 30 - 36 + v_extra + 15),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                maxwidth=180,
                color=bs.safecolor(mvp.team.color + (1,)),
                transition=Text.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
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
            Text(
                bs.Lstr(resource='mostDestroyedPlayerText'),
                color=(0.5, 0.5, 0.5, 1.0),
                v_align=Text.VAlign.CENTER,
                maxwidth=300,
                position=(180, ts_height / 2 - 300 + v_extra + 15),
                transition=Text.Transition.IN_LEFT,
                h_align=Text.HAlign.LEFT,
                transition_delay=tval,
            ).autoretain()
            Text(
                bs.Lstr(
                    value='(${A})',
                    subs=[
                        (
                            '${A}',
                            bs.Lstr(
                                resource='deathsTallyText',
                                subs=[('${COUNT}', str(most_killed))],
                            ),
                        )
                    ],
                ),
                position=(260, ts_height / 2 - 300 - 15 + v_extra),
                h_align=Text.HAlign.LEFT,
                scale=0.6,
                color=(0.3, 0.3, 0.3, 1.0),
                transition=Text.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            tval += 4 * t_incr
            Image(
                mkp.get_icon(),
                position=(233, ts_height / 2 - 300 - 30 - 46 + 25 + v_extra),
                scale=(50, 50),
                transition=Image.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            assert mkp_name is not None
            Text(
                bs.Lstr(value=mkp_name),
                position=(270, ts_height / 2 - 300 - 30 - 36 + v_extra + 15),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                color=bs.safecolor(mkp.team.color + (1,)),
                maxwidth=180,
                transition=Text.Transition.IN_LEFT,
                transition_delay=tval,
            ).autoretain()
            tval += 4 * t_incr

        # Now show individual scores.
        tdelay = tval
        Text(
            bs.Lstr(resource='finalScoresText'),
            color=(0.5, 0.5, 0.5, 1.0),
            position=(ts_h_offs, ts_height / 2),
            transition=Text.Transition.IN_RIGHT,
            transition_delay=tdelay,
        ).autoretain()
        tdelay += 4 * t_incr

        v_offs = 0.0
        tdelay += len(player_entries) * 8 * t_incr
        for _score, name, prec in player_entries:
            tdelay -= 4 * t_incr
            v_offs -= 40
            Text(
                (
                    str(prec.team.customdata['score'])
                    if self._is_ffa
                    else str(prec.score)
                ),
                color=(0.5, 0.5, 0.5, 1.0),
                position=(ts_h_offs + 230, ts_height / 2 + v_offs),
                h_align=Text.HAlign.RIGHT,
                transition=Text.Transition.IN_RIGHT,
                transition_delay=tdelay,
            ).autoretain()
            tdelay -= 4 * t_incr

            Image(
                prec.get_icon(),
                position=(ts_h_offs - 72, ts_height / 2 + v_offs + 15),
                scale=(30, 30),
                transition=Image.Transition.IN_LEFT,
                transition_delay=tdelay,
            ).autoretain()
            Text(
                bs.Lstr(value=name),
                position=(ts_h_offs - 50, ts_height / 2 + v_offs + 15),
                h_align=Text.HAlign.LEFT,
                v_align=Text.VAlign.CENTER,
                maxwidth=180,
                color=bs.safecolor(prec.team.color + (1,)),
                transition=Text.Transition.IN_RIGHT,
                transition_delay=tdelay,
            ).autoretain()

        bs.timer(15.0, bs.WeakCall(self._show_tips))

    def _show_tips(self) -> None:
        from bascenev1lib.actor.tipstext import TipsText

        self._tips_text = TipsText(offs_y=70)

    def _play_victory_music(self) -> None:
        # Make sure we don't stomp on the next activity's music choice.
        if not self.is_transitioning_out():
            bs.setmusic(bs.MusicType.VICTORY)

    def _show_winner(self, team: bs.SessionTeam) -> None:
        from bascenev1lib.actor.image import Image
        from bascenev1lib.actor.zoomtext import ZoomText

        if not self._is_ffa:
            offs_v = 0.0
            ZoomText(
                team.name,
                position=(0, 97),
                color=team.color,
                scale=1.15,
                jitter=1.0,
                maxwidth=250,
            ).autoretain()
        else:
            offs_v = -80
            assert isinstance(self.session, bs.MultiTeamSession)
            series_length = self.session.get_ffa_series_length()
            icon: dict | None
            # Pull live player info if they're still around.
            if len(team.players) == 1:
                icon = team.players[0].get_icon()
                player_name = team.players[0].getname(full=True, icon=False)
            # Otherwise use the special info we stored when we came in.
            elif (
                self._ffa_top_player_info is not None
                and self._ffa_top_player_info[0] >= series_length
            ):
                icon = self._ffa_top_player_info[2]
                player_name = self._ffa_top_player_info[1]
            else:
                icon = None
                player_name = 'Player Not Found'

            if icon is not None:
                i = Image(
                    icon,
                    position=(0, 143),
                    scale=(100, 100),
                ).autoretain()
                assert i.node
                bs.animate(i.node, 'opacity', {0.0: 0.0, 0.25: 1.0})

            ZoomText(
                bs.Lstr(value=player_name),
                position=(0, 97 + offs_v + (0 if icon is not None else 60)),
                color=team.color,
                scale=1.15,
                jitter=1.0,
                maxwidth=250,
            ).autoretain()

        s_extra = 1.0 if self._is_ffa else 1.0

        # Some languages say "FOO WINS" differently for teams vs players.
        if isinstance(self.session, bs.FreeForAllSession):
            wins_resource = 'seriesWinLine1PlayerText'
        else:
            wins_resource = 'seriesWinLine1TeamText'
        wins_text = bs.Lstr(resource=wins_resource)

        # Temp - if these come up as the english default, fall-back to the
        # unified old form which is more likely to be translated.
        ZoomText(
            wins_text,
            position=(0, -10 + offs_v),
            color=team.color,
            scale=0.65 * s_extra,
            jitter=1.0,
            maxwidth=250,
        ).autoretain()
        ZoomText(
            bs.Lstr(resource='seriesWinLine2Text'),
            position=(0, -110 + offs_v),
            scale=1.0 * s_extra,
            color=team.color,
            jitter=1.0,
            maxwidth=250,
        ).autoretain()
