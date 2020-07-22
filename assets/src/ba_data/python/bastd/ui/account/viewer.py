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
"""Provides a popup for displaying info about any account."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba
from bastd.ui import popup

if TYPE_CHECKING:
    from typing import Any, Tuple, Dict, Optional


class AccountViewerWindow(popup.PopupWindow):
    """Popup window that displays info for an account."""

    def __init__(self,
                 account_id: str,
                 profile_id: str = None,
                 position: Tuple[float, float] = (0.0, 0.0),
                 scale: float = None,
                 offset: Tuple[float, float] = (0.0, 0.0)):
        from ba.internal import is_browser_likely_available, master_server_get

        self._account_id = account_id
        self._profile_id = profile_id

        uiscale = ba.app.ui.uiscale
        if scale is None:
            scale = (2.6 if uiscale is ba.UIScale.SMALL else
                     1.8 if uiscale is ba.UIScale.MEDIUM else 1.4)
        self._transitioning_out = False

        self._width = 400
        self._height = (300 if uiscale is ba.UIScale.SMALL else
                        400 if uiscale is ba.UIScale.MEDIUM else 450)
        self._subcontainer: Optional[ba.Widget] = None

        bg_color = (0.5, 0.4, 0.6)

        # Creates our _root_widget.
        popup.PopupWindow.__init__(self,
                                   position=position,
                                   size=(self._width, self._height),
                                   scale=scale,
                                   bg_color=bg_color,
                                   offset=offset)

        self._cancel_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=ba.gettexture('crossOut'),
            iconscale=1.2)

        self._title_text = ba.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 20),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text=ba.Lstr(resource='playerInfoText'),
            maxwidth=200,
            color=(0.7, 0.7, 0.7, 0.7))

        self._scrollwidget = ba.scrollwidget(parent=self.root_widget,
                                             size=(self._width - 60,
                                                   self._height - 70),
                                             position=(30, 30),
                                             capture_arrows=True,
                                             simple_culling_v=10)
        ba.widget(edit=self._scrollwidget, autoselect=True)

        self._loading_text = ba.textwidget(
            parent=self._scrollwidget,
            scale=0.5,
            text=ba.Lstr(value='${A}...',
                         subs=[('${A}', ba.Lstr(resource='loadingText'))]),
            size=(self._width - 60, 100),
            h_align='center',
            v_align='center')

        # In cases where the user most likely has a browser/email, lets
        # offer a 'report this user' button.
        if (is_browser_likely_available() and _ba.get_account_misc_read_val(
                'showAccountExtrasMenu', False)):

            self._extras_menu_button = ba.buttonwidget(
                parent=self.root_widget,
                size=(20, 20),
                position=(self._width - 60, self._height - 30),
                autoselect=True,
                label='...',
                button_type='square',
                color=(0.64, 0.52, 0.69),
                textcolor=(0.57, 0.47, 0.57),
                on_activate_call=self._on_extras_menu_press)

        ba.containerwidget(edit=self.root_widget,
                           cancel_button=self._cancel_button)

        master_server_get('bsAccountInfo', {
            'buildNumber': ba.app.build_number,
            'accountID': self._account_id,
            'profileID': self._profile_id
        },
                          callback=ba.WeakCall(self._on_query_response))

    def popup_menu_selected_choice(self, window: popup.PopupMenu,
                                   choice: str) -> None:
        """Called when a menu entry is selected."""
        del window  # Unused arg.
        if choice == 'more':
            self._on_more_press()
        elif choice == 'report':
            self._on_report_press()
        elif choice == 'ban':
            self._on_ban_press()
        else:
            print('ERROR: unknown account info extras menu item:', choice)

    def popup_menu_closing(self, window: popup.PopupMenu) -> None:
        """Called when the popup menu is closing."""

    def _on_extras_menu_press(self) -> None:
        choices = ['more', 'report']
        choices_display = [
            ba.Lstr(resource='coopSelectWindow.seeMoreText'),
            ba.Lstr(resource='reportThisPlayerText')
        ]
        is_admin = False
        if is_admin:
            ba.screenmessage('TEMP FORCING ADMIN ON')
            choices.append('ban')
            choices_display.append(ba.Lstr(resource='banThisPlayerText'))

        uiscale = ba.app.ui.uiscale
        popup.PopupMenuWindow(
            position=self._extras_menu_button.get_screen_space_center(),
            scale=(2.3 if uiscale is ba.UIScale.SMALL else
                   1.65 if uiscale is ba.UIScale.MEDIUM else 1.23),
            choices=choices,
            choices_display=choices_display,
            current_choice='more',
            delegate=self)

    def _on_ban_press(self) -> None:
        _ba.add_transaction({
            'type': 'BAN_ACCOUNT',
            'account': self._account_id
        })
        _ba.run_transactions()

    def _on_report_press(self) -> None:
        from bastd.ui import report
        report.ReportPlayerWindow(self._account_id,
                                  origin_widget=self._extras_menu_button)

    def _on_more_press(self) -> None:
        ba.open_url(_ba.get_master_server_address() + '/highscores?profile=' +
                    self._account_id)

    def _on_query_response(self, data: Optional[Dict[str, Any]]) -> None:
        # FIXME: Tidy this up.
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-nested-blocks
        if data is None:
            ba.textwidget(
                edit=self._loading_text,
                text=ba.Lstr(resource='internal.unavailableNoConnectionText'))
        else:
            try:
                self._loading_text.delete()
                trophystr = ''
                try:
                    trophystr = data['trophies']
                    num = 10
                    chunks = [
                        trophystr[i:i + num]
                        for i in range(0, len(trophystr), num)
                    ]
                    trophystr = ('\n\n'.join(chunks))
                    if trophystr == '':
                        trophystr = '-'
                except Exception:
                    ba.print_exception('Error displaying trophies.')
                account_name_spacing = 15
                tscale = 0.65
                ts_height = _ba.get_string_height(trophystr,
                                                  suppress_warning=True)
                sub_width = self._width - 80
                sub_height = 200 + ts_height * tscale + \
                    account_name_spacing * len(data['accountDisplayStrings'])
                self._subcontainer = ba.containerwidget(
                    parent=self._scrollwidget,
                    size=(sub_width, sub_height),
                    background=False)
                v = sub_height - 20

                title_scale = 0.37
                center = 0.3
                maxwidth_scale = 0.45
                showing_character = False
                if data['profileDisplayString'] is not None:
                    tint_color = (1, 1, 1)
                    try:
                        if data['profile'] is not None:
                            profile = data['profile']
                            character = ba.app.spaz_appearances.get(
                                profile['character'], None)
                            if character is not None:
                                tint_color = (profile['color'] if 'color'
                                              in profile else (1, 1, 1))
                                tint2_color = (profile['highlight']
                                               if 'highlight' in profile else
                                               (1, 1, 1))
                                icon_tex = character.icon_texture
                                tint_tex = character.icon_mask_texture
                                mask_texture = ba.gettexture(
                                    'characterIconMask')
                                ba.imagewidget(
                                    parent=self._subcontainer,
                                    position=(sub_width * center - 40, v - 80),
                                    size=(80, 80),
                                    color=(1, 1, 1),
                                    mask_texture=mask_texture,
                                    texture=ba.gettexture(icon_tex),
                                    tint_texture=ba.gettexture(tint_tex),
                                    tint_color=tint_color,
                                    tint2_color=tint2_color)
                                v -= 95
                    except Exception:
                        ba.print_exception('Error displaying character.')
                    ba.textwidget(
                        parent=self._subcontainer,
                        size=(0, 0),
                        position=(sub_width * center, v),
                        h_align='center',
                        v_align='center',
                        scale=0.9,
                        color=ba.safecolor(tint_color, 0.7),
                        shadow=1.0,
                        text=ba.Lstr(value=data['profileDisplayString']),
                        maxwidth=sub_width * maxwidth_scale * 0.75)
                    showing_character = True
                    v -= 33

                center = 0.75 if showing_character else 0.5
                maxwidth_scale = 0.45 if showing_character else 0.9

                v = sub_height - 20
                if len(data['accountDisplayStrings']) <= 1:
                    account_title = ba.Lstr(
                        resource='settingsWindow.accountText')
                else:
                    account_title = ba.Lstr(
                        resource='accountSettingsWindow.accountsText',
                        fallback_resource='settingsWindow.accountText')
                ba.textwidget(parent=self._subcontainer,
                              size=(0, 0),
                              position=(sub_width * center, v),
                              flatness=1.0,
                              h_align='center',
                              v_align='center',
                              scale=title_scale,
                              color=ba.app.ui.infotextcolor,
                              text=account_title,
                              maxwidth=sub_width * maxwidth_scale)
                draw_small = (showing_character
                              or len(data['accountDisplayStrings']) > 1)
                v -= 14 if draw_small else 20
                for account_string in data['accountDisplayStrings']:
                    ba.textwidget(parent=self._subcontainer,
                                  size=(0, 0),
                                  position=(sub_width * center, v),
                                  h_align='center',
                                  v_align='center',
                                  scale=0.55 if draw_small else 0.8,
                                  text=account_string,
                                  maxwidth=sub_width * maxwidth_scale)
                    v -= account_name_spacing

                v += account_name_spacing
                v -= 25 if showing_character else 29

                ba.textwidget(parent=self._subcontainer,
                              size=(0, 0),
                              position=(sub_width * center, v),
                              flatness=1.0,
                              h_align='center',
                              v_align='center',
                              scale=title_scale,
                              color=ba.app.ui.infotextcolor,
                              text=ba.Lstr(resource='rankText'),
                              maxwidth=sub_width * maxwidth_scale)
                v -= 14
                if data['rank'] is None:
                    rank_str = '-'
                    suffix_offset = None
                else:
                    str_raw = ba.Lstr(
                        resource='league.rankInLeagueText').evaluate()
                    # FIXME: Would be nice to not have to eval this.
                    rank_str = ba.Lstr(
                        resource='league.rankInLeagueText',
                        subs=[('${RANK}', str(data['rank'][2])),
                              ('${NAME}',
                               ba.Lstr(translate=('leagueNames',
                                                  data['rank'][0]))),
                              ('${SUFFIX}', '')]).evaluate()
                    rank_str_width = min(
                        sub_width * maxwidth_scale,
                        _ba.get_string_width(rank_str, suppress_warning=True) *
                        0.55)

                    # Only tack our suffix on if its at the end and only for
                    # non-diamond leagues.
                    if (str_raw.endswith('${SUFFIX}')
                            and data['rank'][0] != 'Diamond'):
                        suffix_offset = rank_str_width * 0.5 + 2
                    else:
                        suffix_offset = None

                ba.textwidget(parent=self._subcontainer,
                              size=(0, 0),
                              position=(sub_width * center, v),
                              h_align='center',
                              v_align='center',
                              scale=0.55,
                              text=rank_str,
                              maxwidth=sub_width * maxwidth_scale)
                if suffix_offset is not None:
                    assert data['rank'] is not None
                    ba.textwidget(parent=self._subcontainer,
                                  size=(0, 0),
                                  position=(sub_width * center + suffix_offset,
                                            v + 3),
                                  h_align='left',
                                  v_align='center',
                                  scale=0.29,
                                  flatness=1.0,
                                  text='[' + str(data['rank'][1]) + ']')
                v -= 14

                str_raw = ba.Lstr(
                    resource='league.rankInLeagueText').evaluate()
                old_offs = -50
                prev_ranks_shown = 0
                for prev_rank in data['prevRanks']:
                    rank_str = ba.Lstr(
                        value='${S}:    ${I}',
                        subs=[
                            ('${S}',
                             ba.Lstr(resource='league.seasonText',
                                     subs=[('${NUMBER}', str(prev_rank[0]))])),
                            ('${I}',
                             ba.Lstr(resource='league.rankInLeagueText',
                                     subs=[('${RANK}', str(prev_rank[3])),
                                           ('${NAME}',
                                            ba.Lstr(translate=('leagueNames',
                                                               prev_rank[1]))),
                                           ('${SUFFIX}', '')]))
                        ]).evaluate()
                    rank_str_width = min(
                        sub_width * maxwidth_scale,
                        _ba.get_string_width(rank_str, suppress_warning=True) *
                        0.3)

                    # Only tack our suffix on if its at the end and only for
                    # non-diamond leagues.
                    if (str_raw.endswith('${SUFFIX}')
                            and prev_rank[1] != 'Diamond'):
                        suffix_offset = rank_str_width + 2
                    else:
                        suffix_offset = None
                    ba.textwidget(parent=self._subcontainer,
                                  size=(0, 0),
                                  position=(sub_width * center + old_offs, v),
                                  h_align='left',
                                  v_align='center',
                                  scale=0.3,
                                  text=rank_str,
                                  flatness=1.0,
                                  maxwidth=sub_width * maxwidth_scale)
                    if suffix_offset is not None:
                        ba.textwidget(parent=self._subcontainer,
                                      size=(0, 0),
                                      position=(sub_width * center + old_offs +
                                                suffix_offset, v + 1),
                                      h_align='left',
                                      v_align='center',
                                      scale=0.20,
                                      flatness=1.0,
                                      text='[' + str(prev_rank[2]) + ']')
                    prev_ranks_shown += 1
                    v -= 10

                v -= 13

                ba.textwidget(parent=self._subcontainer,
                              size=(0, 0),
                              position=(sub_width * center, v),
                              flatness=1.0,
                              h_align='center',
                              v_align='center',
                              scale=title_scale,
                              color=ba.app.ui.infotextcolor,
                              text=ba.Lstr(resource='achievementsText'),
                              maxwidth=sub_width * maxwidth_scale)
                v -= 14
                ba.textwidget(parent=self._subcontainer,
                              size=(0, 0),
                              position=(sub_width * center, v),
                              h_align='center',
                              v_align='center',
                              scale=0.55,
                              text=str(data['achievementsCompleted']) + ' / ' +
                              str(len(ba.app.achievements)),
                              maxwidth=sub_width * maxwidth_scale)
                v -= 25

                if prev_ranks_shown == 0 and showing_character:
                    v -= 20
                elif prev_ranks_shown == 1 and showing_character:
                    v -= 10

                center = 0.5
                maxwidth_scale = 0.9

                ba.textwidget(parent=self._subcontainer,
                              size=(0, 0),
                              position=(sub_width * center, v),
                              h_align='center',
                              v_align='center',
                              scale=title_scale,
                              color=ba.app.ui.infotextcolor,
                              flatness=1.0,
                              text=ba.Lstr(resource='trophiesThisSeasonText',
                                           fallback_resource='trophiesText'),
                              maxwidth=sub_width * maxwidth_scale)
                v -= 19
                ba.textwidget(parent=self._subcontainer,
                              size=(0, ts_height),
                              position=(sub_width * 0.5,
                                        v - ts_height * tscale),
                              h_align='center',
                              v_align='top',
                              corner_scale=tscale,
                              text=trophystr)

            except Exception:
                ba.print_exception('Error displaying account info.')

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._transition_out()
