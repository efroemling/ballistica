# Released under the MIT License. See LICENSE for details.
#
"""Defines button for co-op games."""

from __future__ import annotations

from typing import TYPE_CHECKING
import copy

import ba
import ba.internal

if TYPE_CHECKING:
    from typing import Any, Callable


class TournamentButton:
    """Button showing a tournament in coop window."""

    def __init__(
        self,
        parent: ba.Widget,
        x: float,
        y: float,
        select: bool,
        on_pressed: Callable[[TournamentButton], None],
    ) -> None:
        self._r = 'coopSelectWindow'
        sclx = 300
        scly = 195.0
        self.on_pressed = on_pressed
        self.lsbt = ba.getmodel('level_select_button_transparent')
        self.lsbo = ba.getmodel('level_select_button_opaque')
        self.allow_ads = False
        self.tournament_id: str | None = None
        self.time_remaining: int = 0
        self.has_time_remaining: bool = False
        self.leader: Any = None
        self.required_league: str | None = None
        self.button = btn = ba.buttonwidget(
            parent=parent,
            position=(x + 23, y + 4),
            size=(sclx, scly),
            label='',
            button_type='square',
            autoselect=True,
            # on_activate_call=lambda: self.run(None, tournament_button=data)
            on_activate_call=ba.WeakCall(self._pressed),
        )
        ba.widget(
            edit=btn,
            show_buffer_bottom=50,
            show_buffer_top=50,
            show_buffer_left=400,
            show_buffer_right=200,
        )
        if select:
            ba.containerwidget(
                edit=parent, selected_child=btn, visible_child=btn
            )
        image_width = sclx * 0.85 * 0.75

        self.image = ba.imagewidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 21 + sclx * 0.5 - image_width * 0.5, y + scly - 150),
            size=(image_width, image_width * 0.5),
            model_transparent=self.lsbt,
            model_opaque=self.lsbo,
            texture=ba.gettexture('black'),
            opacity=0.2,
            mask_texture=ba.gettexture('mapPreviewMask'),
        )

        self.lock_image = ba.imagewidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 21 + sclx * 0.5 - image_width * 0.25, y + scly - 150),
            size=(image_width * 0.5, image_width * 0.5),
            texture=ba.gettexture('lock'),
            opacity=0.0,
        )

        self.button_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 20 + sclx * 0.5, y + scly - 35),
            size=(0, 0),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=sclx * 0.76,
            scale=0.85,
            color=(0.8, 1.0, 0.8, 1.0),
        )

        header_color = (0.43, 0.4, 0.5, 1)
        value_color = (0.6, 0.6, 0.6, 1)

        x_offs = 0
        ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 360, y + scly - 20),
            size=(0, 0),
            h_align='center',
            text=ba.Lstr(resource=self._r + '.entryFeeText'),
            v_align='center',
            maxwidth=100,
            scale=0.9,
            color=header_color,
            flatness=1.0,
        )

        self.entry_fee_text_top = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 360, y + scly - 60),
            size=(0, 0),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=60,
            scale=1.3,
            color=value_color,
            flatness=1.0,
        )
        self.entry_fee_text_or = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 360, y + scly - 90),
            size=(0, 0),
            h_align='center',
            text='',
            v_align='center',
            maxwidth=60,
            scale=0.5,
            color=value_color,
            flatness=1.0,
        )
        self.entry_fee_text_remaining = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 360, y + scly - 90),
            size=(0, 0),
            h_align='center',
            text='',
            v_align='center',
            maxwidth=60,
            scale=0.5,
            color=value_color,
            flatness=1.0,
        )

        self.entry_fee_ad_image = ba.imagewidget(
            parent=parent,
            size=(40, 40),
            draw_controller=btn,
            position=(x + 360 - 20, y + scly - 140),
            opacity=0.0,
            texture=ba.gettexture('tv'),
        )

        x_offs += 50

        ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 447 + x_offs, y + scly - 20),
            size=(0, 0),
            h_align='center',
            text=ba.Lstr(resource=self._r + '.prizesText'),
            v_align='center',
            maxwidth=130,
            scale=0.9,
            color=header_color,
            flatness=1.0,
        )

        self.button_x = x
        self.button_y = y
        self.button_scale_y = scly

        xo2 = 0
        prize_value_scale = 1.5

        self.prize_range_1_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 355 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='right',
            v_align='center',
            maxwidth=50,
            text='-',
            scale=0.8,
            color=header_color,
            flatness=1.0,
        )
        self.prize_value_1_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 380 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='left',
            text='-',
            v_align='center',
            maxwidth=100,
            scale=prize_value_scale,
            color=value_color,
            flatness=1.0,
        )

        self.prize_range_2_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 355 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='right',
            v_align='center',
            maxwidth=50,
            scale=0.8,
            color=header_color,
            flatness=1.0,
        )
        self.prize_value_2_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 380 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='left',
            text='',
            v_align='center',
            maxwidth=100,
            scale=prize_value_scale,
            color=value_color,
            flatness=1.0,
        )

        self.prize_range_3_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 355 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='right',
            v_align='center',
            maxwidth=50,
            scale=0.8,
            color=header_color,
            flatness=1.0,
        )
        self.prize_value_3_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 380 + xo2 + x_offs, y + scly - 93),
            size=(0, 0),
            h_align='left',
            text='',
            v_align='center',
            maxwidth=100,
            scale=prize_value_scale,
            color=value_color,
            flatness=1.0,
        )

        ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 620 + x_offs, y + scly - 20),
            size=(0, 0),
            h_align='center',
            text=ba.Lstr(resource=self._r + '.currentBestText'),
            v_align='center',
            maxwidth=180,
            scale=0.9,
            color=header_color,
            flatness=1.0,
        )
        self.current_leader_name_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(
                x + 620 + x_offs - (170 / 1.4) * 0.5,
                y + scly - 60 - 40 * 0.5,
            ),
            selectable=True,
            click_activate=True,
            autoselect=True,
            on_activate_call=ba.WeakCall(self._show_leader),
            size=(170 / 1.4, 40),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=170,
            scale=1.4,
            color=value_color,
            flatness=1.0,
        )
        self.current_leader_score_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 620 + x_offs, y + scly - 113 + 10),
            size=(0, 0),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=170,
            scale=1.8,
            color=value_color,
            flatness=1.0,
        )

        self.more_scores_button = ba.buttonwidget(
            parent=parent,
            position=(x + 620 + x_offs - 60, y + scly - 50 - 125),
            color=(0.5, 0.5, 0.6),
            textcolor=(0.7, 0.7, 0.8),
            label='-',
            size=(120, 40),
            autoselect=True,
            up_widget=self.current_leader_name_text,
            text_scale=0.6,
            on_activate_call=ba.WeakCall(self._show_scores),
        )
        ba.widget(
            edit=self.current_leader_name_text,
            down_widget=self.more_scores_button,
        )

        ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 820 + x_offs, y + scly - 20),
            size=(0, 0),
            h_align='center',
            text=ba.Lstr(resource=self._r + '.timeRemainingText'),
            v_align='center',
            maxwidth=180,
            scale=0.9,
            color=header_color,
            flatness=1.0,
        )
        self.time_remaining_value_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 820 + x_offs, y + scly - 68),
            size=(0, 0),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=180,
            scale=2.0,
            color=value_color,
            flatness=1.0,
        )
        self.time_remaining_out_of_text = ba.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 820 + x_offs, y + scly - 110),
            size=(0, 0),
            h_align='center',
            text='-',
            v_align='center',
            maxwidth=120,
            scale=0.72,
            color=(0.4, 0.4, 0.5),
            flatness=1.0,
        )

    def _pressed(self) -> None:
        self.on_pressed(self)

    def _show_leader(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account.viewer import AccountViewerWindow

        tournament_id = self.tournament_id

        # FIXME: This assumes a single player entry in leader; should expand
        #  this to work with multiple.
        if (
            tournament_id is None
            or self.leader is None
            or len(self.leader[2]) != 1
        ):
            ba.playsound(ba.getsound('error'))
            return
        ba.playsound(ba.getsound('swish'))
        AccountViewerWindow(
            account_id=self.leader[2][0].get('a', None),
            profile_id=self.leader[2][0].get('p', None),
            position=self.current_leader_name_text.get_screen_space_center(),
        )

    def _show_scores(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.tournamentscores import TournamentScoresWindow

        tournament_id = self.tournament_id
        if tournament_id is None:
            ba.playsound(ba.getsound('error'))
            return

        TournamentScoresWindow(
            tournament_id=tournament_id,
            position=self.more_scores_button.get_screen_space_center(),
        )

    def update_for_data(self, entry: dict[str, Any]) -> None:
        """Update for new incoming data."""
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        from ba.internal import getcampaign, get_tournament_prize_strings

        prize_y_offs = (
            34
            if 'prizeRange3' in entry
            else 20
            if 'prizeRange2' in entry
            else 12
        )
        x_offs = 90

        # This seems to be a false alarm.
        # pylint: disable=unbalanced-tuple-unpacking
        pr1, pv1, pr2, pv2, pr3, pv3 = get_tournament_prize_strings(entry)
        # pylint: enable=unbalanced-tuple-unpacking
        enabled = 'requiredLeague' not in entry
        ba.buttonwidget(
            edit=self.button,
            color=(0.5, 0.7, 0.2) if enabled else (0.5, 0.5, 0.5),
        )
        ba.imagewidget(edit=self.lock_image, opacity=0.0 if enabled else 1.0)
        ba.textwidget(
            edit=self.prize_range_1_text,
            text='-' if pr1 == '' else pr1,
            position=(
                self.button_x + 365 + x_offs,
                self.button_y + self.button_scale_y - 93 + prize_y_offs,
            ),
        )

        # We want to draw values containing tickets a bit smaller
        # (scratch that; we now draw medals a bit bigger).
        ticket_char = ba.charstr(ba.SpecialChar.TICKET_BACKING)
        prize_value_scale_large = 1.0
        prize_value_scale_small = 1.0

        ba.textwidget(
            edit=self.prize_value_1_text,
            text='-' if pv1 == '' else pv1,
            scale=prize_value_scale_large
            if ticket_char not in pv1
            else prize_value_scale_small,
            position=(
                self.button_x + 380 + x_offs,
                self.button_y + self.button_scale_y - 93 + prize_y_offs,
            ),
        )

        ba.textwidget(
            edit=self.prize_range_2_text,
            text=pr2,
            position=(
                self.button_x + 365 + x_offs,
                self.button_y + self.button_scale_y - 93 - 45 + prize_y_offs,
            ),
        )
        ba.textwidget(
            edit=self.prize_value_2_text,
            text=pv2,
            scale=prize_value_scale_large
            if ticket_char not in pv2
            else prize_value_scale_small,
            position=(
                self.button_x + 380 + x_offs,
                self.button_y + self.button_scale_y - 93 - 45 + prize_y_offs,
            ),
        )

        ba.textwidget(
            edit=self.prize_range_3_text,
            text=pr3,
            position=(
                self.button_x + 365 + x_offs,
                self.button_y + self.button_scale_y - 93 - 90 + prize_y_offs,
            ),
        )
        ba.textwidget(
            edit=self.prize_value_3_text,
            text=pv3,
            scale=prize_value_scale_large
            if ticket_char not in pv3
            else prize_value_scale_small,
            position=(
                self.button_x + 380 + x_offs,
                self.button_y + self.button_scale_y - 93 - 90 + prize_y_offs,
            ),
        )

        leader_name = '-'
        leader_score: str | ba.Lstr = '-'
        if entry['scores']:
            score = self.leader = copy.deepcopy(entry['scores'][0])
            leader_name = score[1]
            leader_score = (
                ba.timestring(
                    score[0] * 10,
                    centi=True,
                    timeformat=ba.TimeFormat.MILLISECONDS,
                    suppress_format_warning=True,
                )
                if entry['scoreType'] == 'time'
                else str(score[0])
            )
        else:
            self.leader = None

        ba.textwidget(
            edit=self.current_leader_name_text, text=ba.Lstr(value=leader_name)
        )
        ba.textwidget(edit=self.current_leader_score_text, text=leader_score)
        ba.buttonwidget(
            edit=self.more_scores_button,
            label=ba.Lstr(resource=self._r + '.seeMoreText'),
        )
        out_of_time_text: str | ba.Lstr = (
            '-'
            if 'totalTime' not in entry
            else ba.Lstr(
                resource=self._r + '.ofTotalTimeText',
                subs=[
                    (
                        '${TOTAL}',
                        ba.timestring(
                            entry['totalTime'],
                            centi=False,
                            suppress_format_warning=True,
                        ),
                    )
                ],
            )
        )
        ba.textwidget(
            edit=self.time_remaining_out_of_text, text=out_of_time_text
        )

        self.time_remaining = entry['timeRemaining']
        self.has_time_remaining = entry is not None
        self.tournament_id = entry['tournamentID']
        self.required_league = (
            None if 'requiredLeague' not in entry else entry['requiredLeague']
        )

        game = ba.app.accounts_v1.tournament_info[self.tournament_id]['game']

        if game is None:
            ba.textwidget(edit=self.button_text, text='-')
            ba.imagewidget(
                edit=self.image, texture=ba.gettexture('black'), opacity=0.2
            )
        else:
            campaignname, levelname = game.split(':')
            campaign = getcampaign(campaignname)
            max_players = ba.app.accounts_v1.tournament_info[
                self.tournament_id
            ]['maxPlayers']
            txt = ba.Lstr(
                value='${A} ${B}',
                subs=[
                    ('${A}', campaign.getlevel(levelname).displayname),
                    (
                        '${B}',
                        ba.Lstr(
                            resource='playerCountAbbreviatedText',
                            subs=[('${COUNT}', str(max_players))],
                        ),
                    ),
                ],
            )
            ba.textwidget(edit=self.button_text, text=txt)
            ba.imagewidget(
                edit=self.image,
                texture=campaign.getlevel(levelname).get_preview_texture(),
                opacity=1.0 if enabled else 0.5,
            )

        fee = entry['fee']

        if fee is None:
            fee_var = None
        elif fee == 4:
            fee_var = 'price.tournament_entry_4'
        elif fee == 3:
            fee_var = 'price.tournament_entry_3'
        elif fee == 2:
            fee_var = 'price.tournament_entry_2'
        elif fee == 1:
            fee_var = 'price.tournament_entry_1'
        else:
            if fee != 0:
                print('Unknown fee value:', fee)
            fee_var = 'price.tournament_entry_0'

        self.allow_ads = allow_ads = entry['allowAds']

        final_fee: int | None = (
            None
            if fee_var is None
            else ba.internal.get_v1_account_misc_read_val(fee_var, '?')
        )

        final_fee_str: str | ba.Lstr
        if fee_var is None:
            final_fee_str = ''
        else:
            if final_fee == 0:
                final_fee_str = ba.Lstr(resource='getTicketsWindow.freeText')
            else:
                final_fee_str = ba.charstr(ba.SpecialChar.TICKET_BACKING) + str(
                    final_fee
                )

        ad_tries_remaining = ba.app.accounts_v1.tournament_info[
            self.tournament_id
        ]['adTriesRemaining']
        free_tries_remaining = ba.app.accounts_v1.tournament_info[
            self.tournament_id
        ]['freeTriesRemaining']

        # Now, if this fee allows ads and we support video ads, show
        # the 'or ad' version.
        if allow_ads and ba.internal.has_video_ads():
            ads_enabled = ba.internal.have_incentivized_ad()
            ba.imagewidget(
                edit=self.entry_fee_ad_image,
                opacity=1.0 if ads_enabled else 0.25,
            )
            or_text = (
                ba.Lstr(resource='orText', subs=[('${A}', ''), ('${B}', '')])
                .evaluate()
                .strip()
            )
            ba.textwidget(edit=self.entry_fee_text_or, text=or_text)
            ba.textwidget(
                edit=self.entry_fee_text_top,
                position=(
                    self.button_x + 360,
                    self.button_y + self.button_scale_y - 60,
                ),
                scale=1.3,
                text=final_fee_str,
            )

            # Possibly show number of ad-plays remaining.
            ba.textwidget(
                edit=self.entry_fee_text_remaining,
                position=(
                    self.button_x + 360,
                    self.button_y + self.button_scale_y - 146,
                ),
                text=''
                if ad_tries_remaining in [None, 0]
                else ('' + str(ad_tries_remaining)),
                color=(0.6, 0.6, 0.6, 1 if ads_enabled else 0.2),
            )
        else:
            ba.imagewidget(edit=self.entry_fee_ad_image, opacity=0.0)
            ba.textwidget(edit=self.entry_fee_text_or, text='')
            ba.textwidget(
                edit=self.entry_fee_text_top,
                position=(
                    self.button_x + 360,
                    self.button_y + self.button_scale_y - 80,
                ),
                scale=1.3,
                text=final_fee_str,
            )

            # Possibly show number of free-plays remaining.
            ba.textwidget(
                edit=self.entry_fee_text_remaining,
                position=(
                    self.button_x + 360,
                    self.button_y + self.button_scale_y - 100,
                ),
                text=(
                    ''
                    if (free_tries_remaining in [None, 0] or final_fee != 0)
                    else ('' + str(free_tries_remaining))
                ),
                color=(0.6, 0.6, 0.6, 1),
            )
