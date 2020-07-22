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
"""Provides UI for account functionality."""
# pylint: disable=too-many-lines

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Optional, Tuple, List, Union


class AccountSettingsWindow(ba.Window):
    """Window for account related functionality."""

    def __init__(self,
                 transition: str = 'in_right',
                 modal: bool = False,
                 origin_widget: ba.Widget = None,
                 close_once_signed_in: bool = False):
        # pylint: disable=too-many-statements

        self._close_once_signed_in = close_once_signed_in
        ba.set_analytics_screen('Account Window')

        # If they provided an origin-widget, scale up from that.
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._r = 'accountSettingsWindow'
        self._modal = modal
        self._needs_refresh = False
        self._signed_in = (_ba.get_account_state() == 'signed_in')
        self._account_state_num = _ba.get_account_state_num()
        self._show_linked = (self._signed_in and _ba.get_account_misc_read_val(
            'allowAccountLinking2', False))
        self._check_sign_in_timer = ba.Timer(1.0,
                                             ba.WeakCall(self._update),
                                             timetype=ba.TimeType.REAL,
                                             repeat=True)

        # Currently we can only reset achievements on game-center.
        account_type: Optional[str]
        if self._signed_in:
            account_type = _ba.get_account_type()
        else:
            account_type = None
        self._can_reset_achievements = (account_type == 'Game Center')

        app = ba.app
        uiscale = app.ui.uiscale

        self._width = 760 if uiscale is ba.UIScale.SMALL else 660
        x_offs = 50 if uiscale is ba.UIScale.SMALL else 0
        self._height = (390 if uiscale is ba.UIScale.SMALL else
                        430 if uiscale is ba.UIScale.MEDIUM else 490)

        self._sign_in_button = None
        self._sign_in_text = None

        self._scroll_width = self._width - (100 + x_offs * 2)
        self._scroll_height = self._height - 120
        self._sub_width = self._scroll_width - 20

        # Determine which sign-in/sign-out buttons we should show.
        self._show_sign_in_buttons: List[str] = []

        if app.platform == 'android' and app.subplatform == 'google':
            self._show_sign_in_buttons.append('Google Play')

        elif app.platform == 'android' and app.subplatform == 'amazon':
            self._show_sign_in_buttons.append('Game Circle')

        # Local accounts are generally always available with a few key
        # exceptions.
        self._show_sign_in_buttons.append('Local')

        top_extra = 15 if uiscale is ba.UIScale.SMALL else 0
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + top_extra),
            transition=transition,
            toolbar_visibility='menu_minimal',
            scale_origin_stack_offset=scale_origin,
            scale=(2.09 if uiscale is ba.UIScale.SMALL else
                   1.4 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -19) if uiscale is ba.UIScale.SMALL else (0, 0)))
        if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
            self._back_button = None
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._back)
        else:
            self._back_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=(51 + x_offs, self._height - 62),
                size=(120, 60),
                scale=0.8,
                text_scale=1.2,
                autoselect=True,
                label=ba.Lstr(
                    resource='doneText' if self._modal else 'backText'),
                button_type='regular' if self._modal else 'back',
                on_activate_call=self._back)
            ba.containerwidget(edit=self._root_widget, cancel_button=btn)
            if not self._modal:
                ba.buttonwidget(edit=btn,
                                button_type='backSmall',
                                size=(60, 56),
                                label=ba.charstr(ba.SpecialChar.BACK))

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 41),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      color=ba.app.ui.title_color,
                      maxwidth=self._width - 340,
                      h_align='center',
                      v_align='center')

        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=((self._width - self._scroll_width) * 0.5,
                      self._height - 65 - self._scroll_height),
            size=(self._scroll_width, self._scroll_height),
            claims_left_right=True,
            claims_tab=True,
            selection_loops_to_parent=True)
        self._subcontainer: Optional[ba.Widget] = None
        self._refresh()
        self._restore_state()

    def _update(self) -> None:

        # If they want us to close once we're signed in, do so.
        if self._close_once_signed_in and self._signed_in:
            self._back()
            return

        # Hmm should update this to use get_account_state_num.
        # Theoretically if we switch from one signed-in account to another
        # in the background this would break.
        account_state_num = _ba.get_account_state_num()
        account_state = _ba.get_account_state()

        show_linked = (self._signed_in and _ba.get_account_misc_read_val(
            'allowAccountLinking2', False))

        if (account_state_num != self._account_state_num
                or self._show_linked != show_linked or self._needs_refresh):
            self._show_linked = show_linked
            self._account_state_num = account_state_num
            self._signed_in = (account_state == 'signed_in')
            self._refresh()

        # Go ahead and refresh some individual things
        # that may change under us.
        self._update_linked_accounts_text()
        self._update_unlink_accounts_button()
        self._refresh_campaign_progress_text()
        self._refresh_achievements()
        self._refresh_tickets_text()
        self._refresh_account_name_text()

    def _get_sign_in_text(self) -> ba.Lstr:
        return ba.Lstr(resource=self._r + '.signInText')

    def _refresh(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bastd.ui import confirm

        account_state = _ba.get_account_state()
        account_type = (_ba.get_account_type()
                        if account_state == 'signed_in' else 'unknown')

        is_google = account_type == 'Google Play'

        show_local_signed_in_as = False
        local_signed_in_as_space = 50.0

        show_signed_in_as = self._signed_in
        signed_in_as_space = 95.0

        show_sign_in_benefits = not self._signed_in
        sign_in_benefits_space = 80.0

        show_signing_in_text = account_state == 'signing_in'
        signing_in_text_space = 80.0

        show_google_play_sign_in_button = (account_state == 'signed_out'
                                           and 'Google Play'
                                           in self._show_sign_in_buttons)
        show_game_circle_sign_in_button = (account_state == 'signed_out'
                                           and 'Game Circle'
                                           in self._show_sign_in_buttons)
        show_ali_sign_in_button = (account_state == 'signed_out'
                                   and 'Ali' in self._show_sign_in_buttons)
        show_test_sign_in_button = (account_state == 'signed_out'
                                    and 'Test' in self._show_sign_in_buttons)
        show_device_sign_in_button = (account_state == 'signed_out' and 'Local'
                                      in self._show_sign_in_buttons)
        sign_in_button_space = 70.0

        show_game_service_button = (self._signed_in and account_type
                                    in ['Game Center', 'Game Circle'])
        game_service_button_space = 60.0

        show_linked_accounts_text = (self._signed_in
                                     and _ba.get_account_misc_read_val(
                                         'allowAccountLinking2', False))
        linked_accounts_text_space = 60.0

        show_achievements_button = (self._signed_in and account_type
                                    in ('Google Play', 'Alibaba', 'Local',
                                        'OUYA', 'Test'))
        achievements_button_space = 60.0

        show_achievements_text = (self._signed_in
                                  and not show_achievements_button)
        achievements_text_space = 27.0

        show_leaderboards_button = (self._signed_in and is_google)
        leaderboards_button_space = 60.0

        show_campaign_progress = self._signed_in
        campaign_progress_space = 27.0

        show_tickets = self._signed_in
        tickets_space = 27.0

        show_reset_progress_button = False
        reset_progress_button_space = 70.0

        show_player_profiles_button = self._signed_in
        player_profiles_button_space = 100.0

        show_link_accounts_button = (self._signed_in
                                     and _ba.get_account_misc_read_val(
                                         'allowAccountLinking2', False))
        link_accounts_button_space = 70.0

        show_unlink_accounts_button = show_link_accounts_button
        unlink_accounts_button_space = 90.0

        show_sign_out_button = (self._signed_in and account_type
                                in ['Test', 'Local', 'Google Play'])
        sign_out_button_space = 70.0

        if self._subcontainer is not None:
            self._subcontainer.delete()
        self._sub_height = 60.0
        if show_local_signed_in_as:
            self._sub_height += local_signed_in_as_space
        if show_signed_in_as:
            self._sub_height += signed_in_as_space
        if show_signing_in_text:
            self._sub_height += signing_in_text_space
        if show_google_play_sign_in_button:
            self._sub_height += sign_in_button_space
        if show_game_circle_sign_in_button:
            self._sub_height += sign_in_button_space
        if show_ali_sign_in_button:
            self._sub_height += sign_in_button_space
        if show_test_sign_in_button:
            self._sub_height += sign_in_button_space
        if show_device_sign_in_button:
            self._sub_height += sign_in_button_space
        if show_game_service_button:
            self._sub_height += game_service_button_space
        if show_linked_accounts_text:
            self._sub_height += linked_accounts_text_space
        if show_achievements_text:
            self._sub_height += achievements_text_space
        if show_achievements_button:
            self._sub_height += achievements_button_space
        if show_leaderboards_button:
            self._sub_height += leaderboards_button_space
        if show_campaign_progress:
            self._sub_height += campaign_progress_space
        if show_tickets:
            self._sub_height += tickets_space
        if show_sign_in_benefits:
            self._sub_height += sign_in_benefits_space
        if show_reset_progress_button:
            self._sub_height += reset_progress_button_space
        if show_player_profiles_button:
            self._sub_height += player_profiles_button_space
        if show_link_accounts_button:
            self._sub_height += link_accounts_button_space
        if show_unlink_accounts_button:
            self._sub_height += unlink_accounts_button_space
        if show_sign_out_button:
            self._sub_height += sign_out_button_space
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False,
                                                claims_left_right=True,
                                                claims_tab=True,
                                                selection_loops_to_parent=True)

        first_selectable = None
        v = self._sub_height - 10.0

        if show_local_signed_in_as:
            v -= local_signed_in_as_space * 0.6
            ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                text=ba.Lstr(
                    resource='accountSettingsWindow.deviceSpecificAccountText',
                    subs=[('${NAME}', _ba.get_account_display_string())]),
                scale=0.7,
                color=(0.5, 0.5, 0.6),
                maxwidth=self._sub_width * 0.9,
                flatness=1.0,
                h_align='center',
                v_align='center')
            v -= local_signed_in_as_space * 0.4

        self._account_name_text: Optional[ba.Widget]
        if show_signed_in_as:
            v -= signed_in_as_space * 0.2
            txt = ba.Lstr(
                resource='accountSettingsWindow.youAreSignedInAsText',
                fallback_resource='accountSettingsWindow.youAreLoggedInAsText')
            ba.textwidget(parent=self._subcontainer,
                          position=(self._sub_width * 0.5, v),
                          size=(0, 0),
                          text=txt,
                          scale=0.9,
                          color=ba.app.ui.title_color,
                          maxwidth=self._sub_width * 0.9,
                          h_align='center',
                          v_align='center')
            v -= signed_in_as_space * 0.4
            self._account_name_text = ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=1.5,
                maxwidth=self._sub_width * 0.9,
                res_scale=1.5,
                color=(1, 1, 1, 1),
                h_align='center',
                v_align='center')
            self._refresh_account_name_text()
            v -= signed_in_as_space * 0.4
        else:
            self._account_name_text = None

        if self._back_button is None:
            bbtn = _ba.get_special_widget('back_button')
        else:
            bbtn = self._back_button

        if show_sign_in_benefits:
            v -= sign_in_benefits_space
            app = ba.app
            extra: Optional[Union[str, ba.Lstr]]
            if (app.platform in ['mac', 'ios']
                    and app.subplatform == 'appstore'):
                extra = ba.Lstr(
                    value='\n${S}',
                    subs=[('${S}',
                           ba.Lstr(resource='signInWithGameCenterText'))])
            else:
                extra = ''

            ba.textwidget(parent=self._subcontainer,
                          position=(self._sub_width * 0.5,
                                    v + sign_in_benefits_space * 0.4),
                          size=(0, 0),
                          text=ba.Lstr(value='${A}${B}',
                                       subs=[('${A}',
                                              ba.Lstr(resource=self._r +
                                                      '.signInInfoText')),
                                             ('${B}', extra)]),
                          max_height=sign_in_benefits_space * 0.9,
                          scale=0.9,
                          color=(0.75, 0.7, 0.8),
                          maxwidth=self._sub_width * 0.8,
                          h_align='center',
                          v_align='center')

        if show_signing_in_text:
            v -= signing_in_text_space

            ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5,
                          v + signing_in_text_space * 0.5),
                size=(0, 0),
                text=ba.Lstr(resource='accountSettingsWindow.signingInText'),
                scale=0.9,
                color=(0, 1, 0),
                maxwidth=self._sub_width * 0.8,
                h_align='center',
                v_align='center')

        if show_google_play_sign_in_button:
            button_width = 350
            v -= sign_in_button_space
            self._sign_in_google_play_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                label=ba.Lstr(
                    value='${A}${B}',
                    subs=[('${A}',
                           ba.charstr(ba.SpecialChar.GOOGLE_PLAY_GAMES_LOGO)),
                          ('${B}',
                           ba.Lstr(resource=self._r +
                                   '.signInWithGooglePlayText'))]),
                on_activate_call=lambda: self._sign_in_press('Google Play'))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)
            ba.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        if show_game_circle_sign_in_button:
            button_width = 350
            v -= sign_in_button_space
            self._sign_in_game_circle_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                label=ba.Lstr(value='${A}${B}',
                              subs=[('${A}',
                                     ba.charstr(
                                         ba.SpecialChar.GAME_CIRCLE_LOGO)),
                                    ('${B}',
                                     ba.Lstr(resource=self._r +
                                             '.signInWithGameCircleText'))]),
                on_activate_call=lambda: self._sign_in_press('Game Circle'))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)
            ba.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        if show_ali_sign_in_button:
            button_width = 350
            v -= sign_in_button_space
            self._sign_in_ali_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                label=ba.Lstr(value='${A}${B}',
                              subs=[('${A}',
                                     ba.charstr(ba.SpecialChar.ALIBABA_LOGO)),
                                    ('${B}',
                                     ba.Lstr(resource=self._r + '.signInText'))
                                    ]),
                on_activate_call=lambda: self._sign_in_press('Ali'))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)
            ba.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        if show_device_sign_in_button:
            button_width = 350
            v -= sign_in_button_space
            self._sign_in_device_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                label='',
                on_activate_call=lambda: self._sign_in_press('Local'))
            ba.textwidget(parent=self._subcontainer,
                          draw_controller=btn,
                          h_align='center',
                          v_align='center',
                          size=(0, 0),
                          position=(self._sub_width * 0.5, v + 17),
                          text=ba.Lstr(
                              value='${A}${B}',
                              subs=[('${A}',
                                     ba.charstr(ba.SpecialChar.LOCAL_ACCOUNT)),
                                    ('${B}',
                                     ba.Lstr(resource=self._r +
                                             '.signInWithDeviceText'))]),
                          maxwidth=button_width * 0.8,
                          color=(0.75, 1.0, 0.7))
            ba.textwidget(parent=self._subcontainer,
                          draw_controller=btn,
                          h_align='center',
                          v_align='center',
                          size=(0, 0),
                          position=(self._sub_width * 0.5, v - 4),
                          text=ba.Lstr(resource=self._r +
                                       '.signInWithDeviceInfoText'),
                          flatness=1.0,
                          scale=0.57,
                          maxwidth=button_width * 0.9,
                          color=(0.55, 0.8, 0.5))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)
            ba.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        # Old test-account option.
        if show_test_sign_in_button:
            button_width = 350
            v -= sign_in_button_space
            self._sign_in_test_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                label='',
                on_activate_call=lambda: self._sign_in_press('Test'))
            ba.textwidget(parent=self._subcontainer,
                          draw_controller=btn,
                          h_align='center',
                          v_align='center',
                          size=(0, 0),
                          position=(self._sub_width * 0.5, v + 17),
                          text=ba.Lstr(
                              value='${A}${B}',
                              subs=[('${A}',
                                     ba.charstr(ba.SpecialChar.TEST_ACCOUNT)),
                                    ('${B}',
                                     ba.Lstr(resource=self._r +
                                             '.signInWithTestAccountText'))]),
                          maxwidth=button_width * 0.8,
                          color=(0.75, 1.0, 0.7))
            ba.textwidget(parent=self._subcontainer,
                          draw_controller=btn,
                          h_align='center',
                          v_align='center',
                          size=(0, 0),
                          position=(self._sub_width * 0.5, v - 4),
                          text=ba.Lstr(resource=self._r +
                                       '.signInWithTestAccountInfoText'),
                          flatness=1.0,
                          scale=0.57,
                          maxwidth=button_width * 0.9,
                          color=(0.55, 0.8, 0.5))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)
            ba.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        if show_player_profiles_button:
            button_width = 300
            v -= player_profiles_button_space
            self._player_profiles_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v + 30),
                autoselect=True,
                size=(button_width, 60),
                label=ba.Lstr(resource='playerProfilesWindow.titleText'),
                color=(0.55, 0.5, 0.6),
                icon=ba.gettexture('cuteSpaz'),
                textcolor=(0.75, 0.7, 0.8),
                on_activate_call=self._player_profiles_press)
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=0)

        # the button to go to OS-Specific leaderboards/high-score-lists/etc.
        if show_game_service_button:
            button_width = 300
            v -= game_service_button_space * 0.85
            account_type = _ba.get_account_type()
            if account_type == 'Game Center':
                account_type_name = ba.Lstr(resource='gameCenterText')
            elif account_type == 'Game Circle':
                account_type_name = ba.Lstr(resource='gameCircleText')
            else:
                raise ValueError("unknown account type: '" +
                                 str(account_type) + "'")
            self._game_service_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                on_activate_call=_ba.show_online_score_ui,
                size=(button_width, 50),
                label=account_type_name)
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)
            v -= game_service_button_space * 0.15
        else:
            self.game_service_button = None

        self._achievements_text: Optional[ba.Widget]
        if show_achievements_text:
            v -= achievements_text_space * 0.5
            self._achievements_text = ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=0.9,
                color=(0.75, 0.7, 0.8),
                maxwidth=self._sub_width * 0.8,
                h_align='center',
                v_align='center')
            v -= achievements_text_space * 0.5
        else:
            self._achievements_text = None

        self._achievements_button: Optional[ba.Widget]
        if show_achievements_button:
            button_width = 300
            v -= achievements_button_space * 0.85
            self._achievements_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                icon=ba.gettexture('googlePlayAchievementsIcon'
                                   if is_google else 'achievementsIcon'),
                icon_color=(0.8, 0.95, 0.7) if is_google else (0.85, 0.8, 0.9),
                on_activate_call=self._on_achievements_press,
                size=(button_width, 50),
                label='')
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)
            v -= achievements_button_space * 0.15
        else:
            self._achievements_button = None

        if show_achievements_text or show_achievements_button:
            self._refresh_achievements()

        self._leaderboards_button: Optional[ba.Widget]
        if show_leaderboards_button:
            button_width = 300
            v -= leaderboards_button_space * 0.85
            self._leaderboards_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                icon=ba.gettexture('googlePlayLeaderboardsIcon'),
                icon_color=(0.8, 0.95, 0.7),
                on_activate_call=self._on_leaderboards_press,
                size=(button_width, 50),
                label=ba.Lstr(resource='leaderboardsText'))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)
            v -= leaderboards_button_space * 0.15
        else:
            self._leaderboards_button = None

        self._campaign_progress_text: Optional[ba.Widget]
        if show_campaign_progress:
            v -= campaign_progress_space * 0.5
            self._campaign_progress_text = ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=0.9,
                color=(0.75, 0.7, 0.8),
                maxwidth=self._sub_width * 0.8,
                h_align='center',
                v_align='center')
            v -= campaign_progress_space * 0.5
            self._refresh_campaign_progress_text()
        else:
            self._campaign_progress_text = None

        self._tickets_text: Optional[ba.Widget]
        if show_tickets:
            v -= tickets_space * 0.5
            self._tickets_text = ba.textwidget(parent=self._subcontainer,
                                               position=(self._sub_width * 0.5,
                                                         v),
                                               size=(0, 0),
                                               scale=0.9,
                                               color=(0.75, 0.7, 0.8),
                                               maxwidth=self._sub_width * 0.8,
                                               flatness=1.0,
                                               h_align='center',
                                               v_align='center')
            v -= tickets_space * 0.5
            self._refresh_tickets_text()

        else:
            self._tickets_text = None

        # bit of spacing before the reset/sign-out section
        v -= 5

        button_width = 250
        if show_reset_progress_button:
            confirm_text = (ba.Lstr(resource=self._r +
                                    '.resetProgressConfirmText')
                            if self._can_reset_achievements else ba.Lstr(
                                resource=self._r +
                                '.resetProgressConfirmNoAchievementsText'))
            v -= reset_progress_button_space
            self._reset_progress_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                size=(button_width, 60),
                label=ba.Lstr(resource=self._r + '.resetProgressText'),
                on_activate_call=lambda: confirm.ConfirmWindow(
                    text=confirm_text,
                    width=500,
                    height=200,
                    action=self._reset_progress))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn)

        self._linked_accounts_text: Optional[ba.Widget]
        if show_linked_accounts_text:
            v -= linked_accounts_text_space * 0.8
            self._linked_accounts_text = ba.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=0.9,
                color=(0.75, 0.7, 0.8),
                maxwidth=self._sub_width * 0.95,
                h_align='center',
                v_align='center')
            v -= linked_accounts_text_space * 0.2
            self._update_linked_accounts_text()
        else:
            self._linked_accounts_text = None

        if show_link_accounts_button:
            v -= link_accounts_button_space
            self._link_accounts_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                autoselect=True,
                size=(button_width, 60),
                label='',
                color=(0.55, 0.5, 0.6),
                on_activate_call=self._link_accounts_press)
            ba.textwidget(parent=self._subcontainer,
                          draw_controller=btn,
                          h_align='center',
                          v_align='center',
                          size=(0, 0),
                          position=(self._sub_width * 0.5, v + 17 + 20),
                          text=ba.Lstr(resource=self._r + '.linkAccountsText'),
                          maxwidth=button_width * 0.8,
                          color=(0.75, 0.7, 0.8))
            ba.textwidget(parent=self._subcontainer,
                          draw_controller=btn,
                          h_align='center',
                          v_align='center',
                          size=(0, 0),
                          position=(self._sub_width * 0.5, v - 4 + 20),
                          text=ba.Lstr(resource=self._r +
                                       '.linkAccountsInfoText'),
                          flatness=1.0,
                          scale=0.5,
                          maxwidth=button_width * 0.8,
                          color=(0.75, 0.7, 0.8))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=50)

        self._unlink_accounts_button: Optional[ba.Widget]
        if show_unlink_accounts_button:
            v -= unlink_accounts_button_space
            self._unlink_accounts_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v + 25),
                autoselect=True,
                size=(button_width, 60),
                label='',
                color=(0.55, 0.5, 0.6),
                on_activate_call=self._unlink_accounts_press)
            self._unlink_accounts_button_label = ba.textwidget(
                parent=self._subcontainer,
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v + 55),
                text=ba.Lstr(resource=self._r + '.unlinkAccountsText'),
                maxwidth=button_width * 0.8,
                color=(0.75, 0.7, 0.8))
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=50)
            self._update_unlink_accounts_button()
        else:
            self._unlink_accounts_button = None

        if show_sign_out_button:
            v -= sign_out_button_space
            self._sign_out_button = btn = ba.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                size=(button_width, 60),
                label=ba.Lstr(resource=self._r + '.signOutText'),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                on_activate_call=self._sign_out_press)
            if first_selectable is None:
                first_selectable = btn
            if ba.app.ui.use_toolbars:
                ba.widget(edit=btn,
                          right_widget=_ba.get_special_widget('party_button'))
            ba.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=15)

        # Whatever the topmost selectable thing is, we want it to scroll all
        # the way up when we select it.
        if first_selectable is not None:
            ba.widget(edit=first_selectable,
                      up_widget=bbtn,
                      show_buffer_top=400)
            # (this should re-scroll us to the top..)
            ba.containerwidget(edit=self._subcontainer,
                               visible_child=first_selectable)
        self._needs_refresh = False

    def _on_achievements_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui import achievements
        account_state = _ba.get_account_state()
        account_type = (_ba.get_account_type()
                        if account_state == 'signed_in' else 'unknown')
        # for google play we use the built-in UI; otherwise pop up our own
        if account_type == 'Google Play':
            ba.timer(0.15,
                     ba.Call(_ba.show_online_score_ui, 'achievements'),
                     timetype=ba.TimeType.REAL)
        elif account_type != 'unknown':
            assert self._achievements_button is not None
            achievements.AchievementsWindow(
                position=self._achievements_button.get_screen_space_center())
        else:
            print('ERROR: unknown account type in on_achievements_press:',
                  account_type)

    def _on_leaderboards_press(self) -> None:
        ba.timer(0.15,
                 ba.Call(_ba.show_online_score_ui, 'leaderboards'),
                 timetype=ba.TimeType.REAL)

    def _have_unlinkable_accounts(self) -> bool:
        # if this is not present, we haven't had contact from the server so
        # let's not proceed..
        if _ba.get_public_login_id() is None:
            return False
        accounts = _ba.get_account_misc_read_val_2('linkedAccounts', [])
        return len(accounts) > 1

    def _update_unlink_accounts_button(self) -> None:
        if self._unlink_accounts_button is None:
            return
        if self._have_unlinkable_accounts():
            clr = (0.75, 0.7, 0.8, 1.0)
        else:
            clr = (1.0, 1.0, 1.0, 0.25)
        ba.textwidget(edit=self._unlink_accounts_button_label, color=clr)

    def _update_linked_accounts_text(self) -> None:
        if self._linked_accounts_text is None:
            return

        # if this is not present, we haven't had contact from the server so
        # let's not proceed..
        if _ba.get_public_login_id() is None:
            num = int(time.time()) % 4
            accounts_str = num * '.' + (4 - num) * ' '
        else:
            accounts = _ba.get_account_misc_read_val_2('linkedAccounts', [])
            # our_account = _bs.get_account_display_string()
            # accounts = [a for a in accounts if a != our_account]
            # accounts_str = u', '.join(accounts) if accounts else
            # ba.Lstr(translate=('settingNames', 'None'))
            # UPDATE - we now just print the number here; not the actual
            # accounts
            # (they can see that in the unlink section if they're curious)
            accounts_str = str(max(0, len(accounts) - 1))
        ba.textwidget(edit=self._linked_accounts_text,
                      text=ba.Lstr(value='${L} ${A}',
                                   subs=[('${L}',
                                          ba.Lstr(resource=self._r +
                                                  '.linkedAccountsText')),
                                         ('${A}', accounts_str)]))

    def _refresh_campaign_progress_text(self) -> None:
        from ba.internal import getcampaign
        if self._campaign_progress_text is None:
            return
        p_str: Union[str, ba.Lstr]
        try:
            campaign = getcampaign('Default')
            levels = campaign.levels
            levels_complete = sum((1 if l.complete else 0) for l in levels)

            # Last level cant be completed; hence the -1;
            progress = min(1.0, float(levels_complete) / (len(levels) - 1))
            p_str = ba.Lstr(resource=self._r + '.campaignProgressText',
                            subs=[('${PROGRESS}',
                                   str(int(progress * 100.0)) + '%')])
        except Exception:
            p_str = '?'
            ba.print_exception('Error calculating co-op campaign progress.')
        ba.textwidget(edit=self._campaign_progress_text, text=p_str)

    def _refresh_tickets_text(self) -> None:
        if self._tickets_text is None:
            return
        try:
            tc_str = str(_ba.get_account_ticket_count())
        except Exception:
            ba.print_exception()
            tc_str = '-'
        ba.textwidget(edit=self._tickets_text,
                      text=ba.Lstr(resource=self._r + '.ticketsText',
                                   subs=[('${COUNT}', tc_str)]))

    def _refresh_account_name_text(self) -> None:
        if self._account_name_text is None:
            return
        try:
            name_str = _ba.get_account_display_string()
        except Exception:
            ba.print_exception()
            name_str = '??'
        ba.textwidget(edit=self._account_name_text, text=name_str)

    def _refresh_achievements(self) -> None:
        if (self._achievements_text is None
                and self._achievements_button is None):
            return
        complete = sum(1 if a.complete else 0 for a in ba.app.achievements)
        total = len(ba.app.achievements)
        txt_final = ba.Lstr(resource=self._r + '.achievementProgressText',
                            subs=[('${COUNT}', str(complete)),
                                  ('${TOTAL}', str(total))])

        if self._achievements_text is not None:
            ba.textwidget(edit=self._achievements_text, text=txt_final)
        if self._achievements_button is not None:
            ba.buttonwidget(edit=self._achievements_button, label=txt_final)

    def _link_accounts_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account import link
        link.AccountLinkWindow(origin_widget=self._link_accounts_button)

    def _unlink_accounts_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.account import unlink
        if not self._have_unlinkable_accounts():
            ba.playsound(ba.getsound('error'))
            return
        unlink.AccountUnlinkWindow(origin_widget=self._unlink_accounts_button)

    def _player_profiles_press(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.profile import browser as pbrowser
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        pbrowser.ProfileBrowserWindow(
            origin_widget=self._player_profiles_button)

    def _sign_out_press(self) -> None:
        _ba.sign_out()
        cfg = ba.app.config

        # Take note that its our *explicit* intention to not be signed in at
        # this point.
        cfg['Auto Account State'] = 'signed_out'
        cfg.commit()
        ba.buttonwidget(edit=self._sign_out_button,
                        label=ba.Lstr(resource=self._r + '.signingOutText'))

    def _sign_in_press(self,
                       account_type: str,
                       show_test_warning: bool = True) -> None:
        del show_test_warning  # unused
        _ba.sign_in(account_type)

        # Make note of the type account we're *wanting* to be signed in with.
        cfg = ba.app.config
        cfg['Auto Account State'] = account_type
        cfg.commit()
        self._needs_refresh = True
        ba.timer(0.1, ba.WeakCall(self._update), timetype=ba.TimeType.REAL)

    def _reset_progress(self) -> None:
        try:
            from ba.internal import getcampaign
            # FIXME: This would need to happen server-side these days.
            if self._can_reset_achievements:
                ba.app.config['Achievements'] = {}
                _ba.reset_achievements()
            campaign = getcampaign('Default')
            campaign.reset()  # also writes the config..
            campaign = getcampaign('Challenges')
            campaign.reset()  # also writes the config..
        except Exception:
            ba.print_exception('Error resetting co-op campaign progress.')

        ba.playsound(ba.getsound('shieldDown'))
        self._refresh()

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.mainmenu import MainMenuWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)

        if not self._modal:
            ba.app.ui.set_main_menu_window(
                MainMenuWindow(transition='in_left').get_root_widget())

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._back_button:
                sel_name = 'Back'
            elif sel == self._scrollwidget:
                sel_name = 'Scroll'
            else:
                raise ValueError('unrecognized selection')
            ba.app.ui.window_states[self.__class__.__name__] = sel_name
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(self.__class__.__name__)
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'Scroll':
                sel = self._scrollwidget
            else:
                sel = self._back_button
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')
