# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for account functionality."""
# pylint: disable=too-many-lines

from __future__ import annotations

import time
import logging
from typing import override

from bacommon.cloud import WebLocation
from bacommon.login import LoginType
import bacommon.cloud
import bauiv1 as bui

from bauiv1lib.connectivity import wait_for_connectivity

# These days we're directing people to the web based account settings
# for V2 account linking and trying to get them to disconnect remaining
# V1 links, but leaving this escape hatch here in case needed.
FORCE_ENABLE_V1_LINKING = False


class AccountSettingsWindow(bui.MainWindow):
    """Window for account related functionality."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        close_once_signed_in: bool = False,
    ):
        # pylint: disable=too-many-statements

        plus = bui.app.plus
        assert plus is not None

        self._sign_in_v2_proxy_button: bui.Widget | None = None
        self._sign_in_device_button: bui.Widget | None = None

        self._show_legacy_unlink_button = False

        self._signing_in_adapter: bui.LoginAdapter | None = None
        self._close_once_signed_in = close_once_signed_in
        bui.set_analytics_screen('Account Window')

        self._explicitly_signed_out_of_gpgs = False

        self._r = 'accountSettingsWindow'
        self._needs_refresh = False
        self._v1_signed_in = plus.get_v1_account_state() == 'signed_in'
        self._v1_account_state_num = plus.get_v1_account_state_num()
        self._check_sign_in_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )

        self._can_reset_achievements = False

        app = bui.app
        assert app.classic is not None
        uiscale = app.ui_v1.uiscale

        self._width = 980 if uiscale is bui.UIScale.SMALL else 660
        x_offs = 70 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            430
            if uiscale is bui.UIScale.SMALL
            else 430 if uiscale is bui.UIScale.MEDIUM else 490
        )

        self._sign_in_button = None
        self._sign_in_text = None

        self._scroll_width = self._width - (100 + x_offs * 2)
        self._scroll_height = self._height - 120
        self._sub_width = self._scroll_width - 20

        # Determine which sign-in/sign-out buttons we should show.
        self._show_sign_in_buttons: list[str] = []

        if LoginType.GPGS in plus.accounts.login_adapters:
            self._show_sign_in_buttons.append('Google Play')

        if LoginType.GAME_CENTER in plus.accounts.login_adapters:
            self._show_sign_in_buttons.append('Game Center')

        # Always want to show our web-based v2 login option.
        self._show_sign_in_buttons.append('V2Proxy')

        # Legacy v1 device accounts available only if the user has
        # explicitly enabled deprecated login types.
        if bui.app.config.resolve('Show Deprecated Login Types'):
            self._show_sign_in_buttons.append('Device')

        top_extra = 26 if uiscale is bui.UIScale.SMALL else 0
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    1.72
                    if uiscale is bui.UIScale.SMALL
                    else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 8) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(51 + x_offs, self._height - 62),
                size=(120, 60),
                scale=0.8,
                text_scale=1.2,
                autoselect=True,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
            bui.buttonwidget(
                edit=btn,
                button_type='backSmall',
                size=(60, 56),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        titleyoffs = -9 if uiscale is bui.UIScale.SMALL else 0
        titlescale = 0.7 if uiscale is bui.UIScale.SMALL else 1.0
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 41 + titleyoffs),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=app.ui_v1.title_color,
            scale=titlescale,
            maxwidth=self._width - 340,
            h_align='center',
            v_align='center',
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=(
                (self._width - self._scroll_width) * 0.5,
                self._height - 65 - self._scroll_height,
            ),
            size=(self._scroll_width, self._scroll_height),
            claims_left_right=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )
        self._subcontainer: bui.Widget | None = None
        self._refresh()
        self._restore_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _update(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        # If they want us to close once we're signed in, do so.
        if self._close_once_signed_in and self._v1_signed_in:
            self.main_window_back()
            return

        # Hmm should update this to use get_account_state_num.
        # Theoretically if we switch from one signed-in account to
        # another in the background this would break.
        v1_account_state_num = plus.get_v1_account_state_num()
        v1_account_state = plus.get_v1_account_state()
        show_legacy_unlink_button = self._should_show_legacy_unlink_button()

        if (
            v1_account_state_num != self._v1_account_state_num
            or show_legacy_unlink_button != self._show_legacy_unlink_button
            or self._needs_refresh
        ):
            self._v1_account_state_num = v1_account_state_num
            self._v1_signed_in = v1_account_state == 'signed_in'
            self._show_legacy_unlink_button = show_legacy_unlink_button
            self._refresh()

        # Go ahead and refresh some individual things that may change
        # under us.
        self._update_linked_accounts_text()
        self._update_unlink_accounts_button()
        self._refresh_campaign_progress_text()
        self._refresh_achievements()
        self._refresh_tickets_text()
        self._refresh_account_name_text()

    def _refresh(self) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import

        plus = bui.app.plus
        assert plus is not None

        via_lines: list[str] = []

        primary_v2_account = plus.accounts.primary

        v1_state = plus.get_v1_account_state()
        v1_account_type = (
            plus.get_v1_account_type() if v1_state == 'signed_in' else 'unknown'
        )

        # We expose GPGS-specific functionality only if it is 'active'
        # (meaning the current GPGS player matches one of our account's
        # logins).
        adapter = plus.accounts.login_adapters.get(LoginType.GPGS)
        gpgs_active = adapter is not None and adapter.is_back_end_active()

        # Ditto for Game Center.
        adapter = plus.accounts.login_adapters.get(LoginType.GAME_CENTER)
        game_center_active = (
            adapter is not None and adapter.is_back_end_active()
        )

        show_signed_in_as = self._v1_signed_in
        signed_in_as_space = 95.0

        # To reduce confusion about the whole V2 account situation for
        # people used to seeing their Google Play Games or Game Center
        # account name and icon and whatnot, let's show those underneath
        # the V2 tag to help communicate that they are in fact logged in
        # through that account.
        via_space = 25.0
        if show_signed_in_as and bui.app.plus is not None:
            accounts = bui.app.plus.accounts
            if accounts.primary is not None:
                # For these login types, we show 'via' IF there is a
                # login of that type attached to our account AND it is
                # currently active (We don't want to show 'via Game
                # Center' if we're signed out of Game Center or
                # currently running on Steam, even if there is a Game
                # Center login attached to our account).
                for ltype, lchar in [
                    (LoginType.GPGS, bui.SpecialChar.GOOGLE_PLAY_GAMES_LOGO),
                    (LoginType.GAME_CENTER, bui.SpecialChar.GAME_CENTER_LOGO),
                ]:
                    linfo = accounts.primary.logins.get(ltype)
                    ladapter = accounts.login_adapters.get(ltype)
                    if (
                        linfo is not None
                        and ladapter is not None
                        and ladapter.is_back_end_active()
                    ):
                        via_lines.append(f'{bui.charstr(lchar)}{linfo.name}')

                # TEMP TESTING
                if bool(False):
                    icontxt = bui.charstr(bui.SpecialChar.GAME_CENTER_LOGO)
                    via_lines.append(f'{icontxt}FloofDibble')
                    icontxt = bui.charstr(
                        bui.SpecialChar.GOOGLE_PLAY_GAMES_LOGO
                    )
                    via_lines.append(f'{icontxt}StinkBobble')

        show_sign_in_benefits = not self._v1_signed_in
        sign_in_benefits_space = 80.0

        show_signing_in_text = (
            v1_state == 'signing_in' or self._signing_in_adapter is not None
        )
        signing_in_text_space = 80.0

        show_google_play_sign_in_button = (
            v1_state == 'signed_out'
            and self._signing_in_adapter is None
            and 'Google Play' in self._show_sign_in_buttons
        )
        show_game_center_sign_in_button = (
            v1_state == 'signed_out'
            and self._signing_in_adapter is None
            and 'Game Center' in self._show_sign_in_buttons
        )
        show_v2_proxy_sign_in_button = (
            v1_state == 'signed_out'
            and self._signing_in_adapter is None
            and 'V2Proxy' in self._show_sign_in_buttons
        )
        show_device_sign_in_button = (
            v1_state == 'signed_out'
            and self._signing_in_adapter is None
            and 'Device' in self._show_sign_in_buttons
        )
        sign_in_button_space = 70.0
        deprecated_space = 60

        # Game Center currently has a single UI for everything.
        show_game_service_button = game_center_active
        game_service_button_space = 60.0

        # Phasing this out (for V2 accounts at least).
        show_linked_accounts_text = (
            self._v1_signed_in and v1_account_type != 'V2'
        )
        linked_accounts_text_space = 60.0

        # Update: No longer showing this since its visible on main
        # toolbar.
        show_achievements_text = False
        achievements_text_space = 27.0

        show_leaderboards_button = self._v1_signed_in and gpgs_active
        leaderboards_button_space = 60.0

        # Update: No longer showing this; trying to get progress type
        # stuff out of the account panel.
        # show_campaign_progress = self._v1_signed_in
        show_campaign_progress = False
        campaign_progress_space = 27.0

        # show_tickets = self._v1_signed_in
        show_tickets = False
        tickets_space = 27.0

        show_manage_account_button = primary_v2_account is not None
        manage_account_button_space = 70.0

        show_create_account_button = show_v2_proxy_sign_in_button
        create_account_button_space = 70.0

        # Apple asks us to make a delete-account button directly
        # available in the UI. Currently disabling this elsewhere
        # however as I feel that poking 'Manage Account' and scrolling
        # down to 'Delete Account' is not hard to find.
        show_delete_account_button = primary_v2_account is not None and (
            bui.app.classic is not None
            and bui.app.classic.platform == 'mac'
            and bui.app.classic.subplatform == 'appstore'
        )
        delete_account_button_space = 70.0

        show_link_accounts_button = self._v1_signed_in and (
            primary_v2_account is None or FORCE_ENABLE_V1_LINKING
        )
        link_accounts_button_space = 70.0

        show_v1_obsolete_note = self._v1_signed_in and (
            primary_v2_account is None
        )
        v1_obsolete_note_space = 80.0

        show_unlink_accounts_button = show_link_accounts_button
        unlink_accounts_button_space = 90.0

        # Phasing this out.
        show_v2_link_info = False
        v2_link_info_space = 70.0

        legacy_unlink_button_space = 120.0

        show_sign_out_button = primary_v2_account is not None or (
            self._v1_signed_in and v1_account_type == 'Local'
        )
        sign_out_button_space = 70.0

        # We can show cancel if we're either waiting on an adapter to
        # provide us with v2 credentials or waiting for those
        # credentials to be verified.
        show_cancel_sign_in_button = self._signing_in_adapter is not None or (
            plus.accounts.have_primary_credentials()
            and primary_v2_account is None
        )
        cancel_sign_in_button_space = 70.0

        if self._subcontainer is not None:
            self._subcontainer.delete()
        self._sub_height = 60.0
        if show_signed_in_as:
            self._sub_height += signed_in_as_space
        self._sub_height += via_space * len(via_lines)
        if show_signing_in_text:
            self._sub_height += signing_in_text_space
        if show_google_play_sign_in_button:
            self._sub_height += sign_in_button_space
        if show_game_center_sign_in_button:
            self._sub_height += sign_in_button_space
        if show_v2_proxy_sign_in_button:
            self._sub_height += sign_in_button_space
        if show_device_sign_in_button:
            self._sub_height += sign_in_button_space + deprecated_space
        if show_game_service_button:
            self._sub_height += game_service_button_space
        if show_linked_accounts_text:
            self._sub_height += linked_accounts_text_space
        if show_achievements_text:
            self._sub_height += achievements_text_space
        if show_leaderboards_button:
            self._sub_height += leaderboards_button_space
        if show_campaign_progress:
            self._sub_height += campaign_progress_space
        if show_tickets:
            self._sub_height += tickets_space
        if show_sign_in_benefits:
            self._sub_height += sign_in_benefits_space
        if show_manage_account_button:
            self._sub_height += manage_account_button_space
        if show_create_account_button:
            self._sub_height += create_account_button_space
        if show_link_accounts_button:
            self._sub_height += link_accounts_button_space
        if show_v1_obsolete_note:
            self._sub_height += v1_obsolete_note_space
        if show_unlink_accounts_button:
            self._sub_height += unlink_accounts_button_space
        if show_v2_link_info:
            self._sub_height += v2_link_info_space
        if self._show_legacy_unlink_button:
            self._sub_height += legacy_unlink_button_space
        if show_sign_out_button:
            self._sub_height += sign_out_button_space
        if show_delete_account_button:
            self._sub_height += delete_account_button_space
        if show_cancel_sign_in_button:
            self._sub_height += cancel_sign_in_button_space
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )

        first_selectable = None
        v = self._sub_height - 10.0

        assert bui.app.classic is not None
        self._account_name_text: bui.Widget | None
        if show_signed_in_as:
            v -= signed_in_as_space * 0.2
            txt = bui.Lstr(
                resource='accountSettingsWindow.youAreSignedInAsText',
                fallback_resource='accountSettingsWindow.youAreLoggedInAsText',
            )
            bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                text=txt,
                scale=0.9,
                color=bui.app.ui_v1.title_color,
                maxwidth=self._sub_width * 0.9,
                h_align='center',
                v_align='center',
            )
            v -= signed_in_as_space * 0.5
            self._account_name_text = bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=1.5,
                maxwidth=self._sub_width * 0.9,
                res_scale=1.5,
                color=(1, 1, 1, 1),
                h_align='center',
                v_align='center',
            )

            self._refresh_account_name_text()

            v -= signed_in_as_space * 0.4

            for via in via_lines:
                v -= via_space * 0.1
                sscale = 0.7
                swidth = (
                    bui.get_string_width(via, suppress_warning=True) * sscale
                )
                bui.textwidget(
                    parent=self._subcontainer,
                    position=(self._sub_width * 0.5, v),
                    size=(0, 0),
                    text=via,
                    scale=sscale,
                    color=(0.6, 0.6, 0.6),
                    flatness=1.0,
                    shadow=0.0,
                    h_align='center',
                    v_align='center',
                )
                bui.textwidget(
                    parent=self._subcontainer,
                    position=(self._sub_width * 0.5 - swidth * 0.5 - 5, v),
                    size=(0, 0),
                    text=bui.Lstr(
                        value='(${VIA}',
                        subs=[('${VIA}', bui.Lstr(resource='viaText'))],
                    ),
                    scale=0.5,
                    color=(0.4, 0.6, 0.4, 0.5),
                    flatness=1.0,
                    shadow=0.0,
                    h_align='right',
                    v_align='center',
                )
                bui.textwidget(
                    parent=self._subcontainer,
                    position=(self._sub_width * 0.5 + swidth * 0.5 + 10, v),
                    size=(0, 0),
                    text=')',
                    scale=0.5,
                    color=(0.4, 0.6, 0.4, 0.5),
                    flatness=1.0,
                    shadow=0.0,
                    h_align='right',
                    v_align='center',
                )

                v -= via_space * 0.9

        else:
            self._account_name_text = None

        if self._back_button is None:
            bbtn = bui.get_special_widget('back_button')
        else:
            bbtn = self._back_button

        if show_sign_in_benefits:
            v -= sign_in_benefits_space
            bui.textwidget(
                parent=self._subcontainer,
                position=(
                    self._sub_width * 0.5,
                    v + sign_in_benefits_space * 0.4,
                ),
                size=(0, 0),
                text=bui.Lstr(resource=f'{self._r}.signInInfoText'),
                max_height=sign_in_benefits_space * 0.9,
                scale=0.9,
                color=(0.75, 0.7, 0.8),
                maxwidth=self._sub_width * 0.8,
                h_align='center',
                v_align='center',
            )

        if show_signing_in_text:
            v -= signing_in_text_space

            bui.textwidget(
                parent=self._subcontainer,
                position=(
                    self._sub_width * 0.5,
                    v + signing_in_text_space * 0.5,
                ),
                size=(0, 0),
                text=bui.Lstr(resource='accountSettingsWindow.signingInText'),
                scale=0.9,
                color=(0, 1, 0),
                maxwidth=self._sub_width * 0.8,
                h_align='center',
                v_align='center',
            )

        if show_google_play_sign_in_button:
            button_width = 350
            v -= sign_in_button_space
            self._sign_in_google_play_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                label=bui.Lstr(
                    value='${A} ${B}',
                    subs=[
                        (
                            '${A}',
                            bui.charstr(bui.SpecialChar.GOOGLE_PLAY_GAMES_LOGO),
                        ),
                        (
                            '${B}',
                            bui.Lstr(
                                resource=f'{self._r}.signInWithText',
                                subs=[
                                    (
                                        '${SERVICE}',
                                        bui.Lstr(resource='googlePlayText'),
                                    )
                                ],
                            ),
                        ),
                    ],
                ),
                on_activate_call=lambda: self._sign_in_press(LoginType.GPGS),
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn)
            bui.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        if show_game_center_sign_in_button:
            button_width = 350
            v -= sign_in_button_space
            self._sign_in_google_play_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                # Note: Apparently Game Center is just called 'Game Center'
                # in all languages. Can revisit if not true.
                # https://developer.apple.com/forums/thread/725779
                label=bui.Lstr(
                    value='${A} ${B}',
                    subs=[
                        (
                            '${A}',
                            bui.charstr(bui.SpecialChar.GAME_CENTER_LOGO),
                        ),
                        (
                            '${B}',
                            bui.Lstr(
                                resource=f'{self._r}.signInWithText',
                                subs=[('${SERVICE}', 'Game Center')],
                            ),
                        ),
                    ],
                ),
                on_activate_call=lambda: self._sign_in_press(
                    LoginType.GAME_CENTER
                ),
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn)
            bui.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        if show_v2_proxy_sign_in_button:
            button_width = 350
            v -= sign_in_button_space
            self._sign_in_v2_proxy_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                label='',
                on_activate_call=self._v2_proxy_sign_in_press,
            )

            v2labeltext: bui.Lstr | str = (
                bui.Lstr(resource=f'{self._r}.signInWithAnEmailAddressText')
                if show_game_center_sign_in_button
                or show_google_play_sign_in_button
                or show_device_sign_in_button
                else bui.Lstr(resource=f'{self._r}.signInText')
            )
            v2infotext: bui.Lstr | str | None = None

            bui.textwidget(
                parent=self._subcontainer,
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(
                    self._sub_width * 0.5,
                    v + (17 if v2infotext is not None else 10),
                ),
                text=bui.Lstr(
                    value='${A} ${B}',
                    subs=[
                        ('${A}', bui.charstr(bui.SpecialChar.V2_LOGO)),
                        (
                            '${B}',
                            v2labeltext,
                        ),
                    ],
                ),
                maxwidth=button_width * 0.8,
                color=(0.75, 1.0, 0.7),
            )
            if v2infotext is not None:
                bui.textwidget(
                    parent=self._subcontainer,
                    draw_controller=btn,
                    h_align='center',
                    v_align='center',
                    size=(0, 0),
                    position=(self._sub_width * 0.5, v - 4),
                    text=v2infotext,
                    flatness=1.0,
                    scale=0.57,
                    maxwidth=button_width * 0.9,
                    color=(0.55, 0.8, 0.5),
                )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn)
            bui.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        if show_device_sign_in_button:
            button_width = 350
            v -= sign_in_button_space + deprecated_space
            self._sign_in_device_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 20),
                autoselect=True,
                size=(button_width, 60),
                label='',
                on_activate_call=lambda: self._sign_in_press('Local'),
            )
            bui.textwidget(
                parent=self._subcontainer,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v + 60),
                text=bui.Lstr(resource='deprecatedText'),
                scale=0.8,
                maxwidth=300,
                color=(0.6, 0.55, 0.45),
            )

            bui.textwidget(
                parent=self._subcontainer,
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v + 17),
                text=bui.Lstr(
                    value='${A} ${B}',
                    subs=[
                        ('${A}', bui.charstr(bui.SpecialChar.LOCAL_ACCOUNT)),
                        (
                            '${B}',
                            bui.Lstr(
                                resource=f'{self._r}.signInWithDeviceText'
                            ),
                        ),
                    ],
                ),
                maxwidth=button_width * 0.8,
                color=(0.75, 1.0, 0.7),
            )
            bui.textwidget(
                parent=self._subcontainer,
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v - 4),
                text=bui.Lstr(resource=f'{self._r}.signInWithDeviceInfoText'),
                flatness=1.0,
                scale=0.57,
                maxwidth=button_width * 0.9,
                color=(0.55, 0.8, 0.5),
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn)
            bui.widget(edit=btn, show_buffer_bottom=40, show_buffer_top=100)
            self._sign_in_text = None

        if show_v1_obsolete_note:
            v -= v1_obsolete_note_space
            bui.textwidget(
                parent=self._subcontainer,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v + 35.0),
                text=(
                    'YOU ARE SIGNED IN WITH A V1 ACCOUNT.\n'
                    'THESE ARE NO LONGER SUPPORTED AND MANY\n'
                    'FEATURES WILL NOT WORK. PLEASE SWITCH TO\n'
                    'A V2 ACCOUNT OR UPGRADE THIS ONE.'
                ),
                maxwidth=self._sub_width * 0.8,
                color=(1, 0, 0),
                shadow=1.0,
                flatness=1.0,
            )

        if show_manage_account_button:
            button_width = 300
            v -= manage_account_button_space
            self._manage_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                autoselect=True,
                size=(button_width, 60),
                label=bui.Lstr(resource=f'{self._r}.manageAccountText'),
                color=(0.55, 0.5, 0.6),
                icon=bui.gettexture('settingsIcon'),
                textcolor=(0.75, 0.7, 0.8),
                on_activate_call=bui.WeakCall(self._on_manage_account_press),
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn)

        if show_create_account_button:
            button_width = 300
            v -= create_account_button_space
            self._create_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v - 30),
                autoselect=True,
                size=(button_width, 60),
                # label=bui.Lstr(resource=f'{self._r}.createAccountText'),
                label='Create an Account',
                color=(0.55, 0.5, 0.6),
                # icon=bui.gettexture('settingsIcon'),
                textcolor=(0.75, 0.7, 0.8),
                on_activate_call=bui.WeakCall(self._on_create_account_press),
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn)

        # the button to go to OS-Specific leaderboards/high-score-lists/etc.
        if show_game_service_button:
            button_width = 300
            v -= game_service_button_space * 0.6
            if game_center_active:
                # Note: Apparently Game Center is just called 'Game Center'
                # in all languages. Can revisit if not true.
                # https://developer.apple.com/forums/thread/725779
                game_service_button_label = bui.Lstr(
                    value=bui.charstr(bui.SpecialChar.GAME_CENTER_LOGO)
                    + 'Game Center'
                )
            else:
                raise ValueError(
                    "unknown account type: '" + str(v1_account_type) + "'"
                )
            self._game_service_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                on_activate_call=self._on_game_service_button_press,
                size=(button_width, 50),
                label=game_service_button_label,
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn)
            v -= game_service_button_space * 0.4
        else:
            self.game_service_button = None

        self._achievements_text: bui.Widget | None
        if show_achievements_text:
            v -= achievements_text_space * 0.5
            self._achievements_text = bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=0.9,
                color=(0.75, 0.7, 0.8),
                maxwidth=self._sub_width * 0.8,
                h_align='center',
                v_align='center',
            )
            v -= achievements_text_space * 0.5
        else:
            self._achievements_text = None

        if show_achievements_text:
            self._refresh_achievements()

        self._leaderboards_button: bui.Widget | None
        if show_leaderboards_button:
            button_width = 300
            v -= leaderboards_button_space * 0.85
            self._leaderboards_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                icon=bui.gettexture('googlePlayLeaderboardsIcon'),
                icon_color=(0.8, 0.95, 0.7),
                on_activate_call=self._on_leaderboards_press,
                size=(button_width, 50),
                label=bui.Lstr(resource='leaderboardsText'),
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn)
            v -= leaderboards_button_space * 0.15
        else:
            self._leaderboards_button = None

        self._campaign_progress_text: bui.Widget | None
        if show_campaign_progress:
            v -= campaign_progress_space * 0.5
            self._campaign_progress_text = bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=0.9,
                color=(0.75, 0.7, 0.8),
                maxwidth=self._sub_width * 0.8,
                h_align='center',
                v_align='center',
            )
            v -= campaign_progress_space * 0.5
            self._refresh_campaign_progress_text()
        else:
            self._campaign_progress_text = None

        self._tickets_text: bui.Widget | None
        if show_tickets:
            v -= tickets_space * 0.5
            self._tickets_text = bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=0.9,
                color=(0.75, 0.7, 0.8),
                maxwidth=self._sub_width * 0.8,
                flatness=1.0,
                h_align='center',
                v_align='center',
            )
            v -= tickets_space * 0.5
            self._refresh_tickets_text()

        else:
            self._tickets_text = None

        # bit of spacing before the reset/sign-out section
        # v -= 5

        button_width = 300

        self._linked_accounts_text: bui.Widget | None
        if show_linked_accounts_text:
            v -= linked_accounts_text_space * 0.8
            self._linked_accounts_text = bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5, v),
                size=(0, 0),
                scale=0.9,
                color=(0.75, 0.7, 0.8),
                maxwidth=self._sub_width * 0.95,
                text=bui.Lstr(resource=f'{self._r}.linkedAccountsText'),
                h_align='center',
                v_align='center',
            )
            v -= linked_accounts_text_space * 0.2
            self._update_linked_accounts_text()
        else:
            self._linked_accounts_text = None

        # Show link/unlink buttons only for V1 accounts.

        if show_link_accounts_button:
            v -= link_accounts_button_space
            self._link_accounts_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                autoselect=True,
                size=(button_width, 60),
                label='',
                color=(0.55, 0.5, 0.6),
                on_activate_call=self._link_accounts_press,
            )
            bui.textwidget(
                parent=self._subcontainer,
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v + 17 + 20),
                text=bui.Lstr(resource=f'{self._r}.linkAccountsText'),
                maxwidth=button_width * 0.8,
                color=(0.75, 0.7, 0.8),
            )
            bui.textwidget(
                parent=self._subcontainer,
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v - 4 + 20),
                text=bui.Lstr(resource=f'{self._r}.linkAccountsInfoText'),
                flatness=1.0,
                scale=0.5,
                maxwidth=button_width * 0.8,
                color=(0.75, 0.7, 0.8),
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=50)

        self._unlink_accounts_button: bui.Widget | None
        if show_unlink_accounts_button:
            v -= unlink_accounts_button_space
            self._unlink_accounts_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v + 25),
                autoselect=True,
                size=(button_width, 60),
                label='',
                color=(0.55, 0.5, 0.6),
                on_activate_call=self._unlink_accounts_press,
            )
            self._unlink_accounts_button_label = bui.textwidget(
                parent=self._subcontainer,
                draw_controller=btn,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v + 55),
                text=bui.Lstr(resource=f'{self._r}.unlinkAccountsText'),
                maxwidth=button_width * 0.8,
                color=(0.75, 0.7, 0.8),
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=50)
            self._update_unlink_accounts_button()
        else:
            self._unlink_accounts_button = None

        if show_v2_link_info:
            v -= v2_link_info_space
            bui.textwidget(
                parent=self._subcontainer,
                h_align='center',
                v_align='center',
                size=(0, 0),
                position=(self._sub_width * 0.5, v + v2_link_info_space - 20),
                text=bui.Lstr(resource='v2AccountLinkingInfoText'),
                flatness=1.0,
                scale=0.8,
                maxwidth=450,
                color=(0.5, 0.45, 0.55),
            )

        if self._show_legacy_unlink_button:
            v -= legacy_unlink_button_space
            button_width_w = button_width * 1.5
            bui.textwidget(
                parent=self._subcontainer,
                position=(self._sub_width * 0.5 - 150.0, v + 75),
                size=(300.0, 60),
                text=bui.Lstr(resource='whatIsThisText'),
                scale=0.8,
                color=(0.3, 0.7, 0.05),
                maxwidth=200.0,
                h_align='center',
                v_align='center',
                autoselect=True,
                selectable=True,
                on_activate_call=show_what_is_legacy_unlinking_page,
                click_activate=True,
            )
            btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width_w) * 0.5, v + 25),
                autoselect=True,
                size=(button_width_w, 60),
                label=bui.Lstr(
                    resource=f'{self._r}.unlinkLegacyV1AccountsText'
                ),
                textcolor=(0.8, 0.4, 0),
                color=(0.55, 0.5, 0.6),
                on_activate_call=self._unlink_accounts_press,
            )

        if show_sign_out_button:
            v -= sign_out_button_space
            self._sign_out_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                size=(button_width, 60),
                label=bui.Lstr(resource=f'{self._r}.signOutText'),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                on_activate_call=self._sign_out_press,
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=15)

        if show_cancel_sign_in_button:
            v -= cancel_sign_in_button_space
            self._cancel_sign_in_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                size=(button_width, 60),
                label=bui.Lstr(resource='cancelText'),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                autoselect=True,
                on_activate_call=self._cancel_sign_in_press,
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=15)

        if show_delete_account_button:
            v -= delete_account_button_space
            self._delete_account_button = btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=((self._sub_width - button_width) * 0.5, v),
                size=(button_width, 60),
                label=bui.Lstr(resource=f'{self._r}.deleteAccountText'),
                color=(0.85, 0.5, 0.6),
                textcolor=(0.9, 0.7, 0.8),
                autoselect=True,
                on_activate_call=self._on_delete_account_press,
            )
            if first_selectable is None:
                first_selectable = btn
            bui.widget(
                edit=btn, right_widget=bui.get_special_widget('squad_button')
            )
            bui.widget(edit=btn, left_widget=bbtn, show_buffer_bottom=15)

        # Whatever the topmost selectable thing is, we want it to scroll all
        # the way up when we select it.
        if first_selectable is not None:
            bui.widget(
                edit=first_selectable, up_widget=bbtn, show_buffer_top=400
            )
            # (this should re-scroll us to the top..)
            bui.containerwidget(
                edit=self._subcontainer, visible_child=first_selectable
            )
        self._needs_refresh = False

    def _on_game_service_button_press(self) -> None:
        if bui.app.plus is not None:
            bui.app.plus.show_game_service_ui()
        else:
            logging.warning(
                'game-service-ui not available without plus feature-set.'
            )

    def _on_custom_achievements_press(self) -> None:
        if bui.app.plus is not None:
            bui.apptimer(
                0.15,
                bui.Call(bui.app.plus.show_game_service_ui, 'achievements'),
            )
        else:
            logging.warning('show_game_service_ui requires plus feature-set.')

    def _on_manage_account_press(self) -> None:
        self._do_manage_account_press(WebLocation.ACCOUNT_EDITOR)

    def _on_create_account_press(self) -> None:
        bui.open_url('https://ballistica.net/createaccount')

    def _on_delete_account_press(self) -> None:
        self._do_manage_account_press(WebLocation.ACCOUNT_DELETE_SECTION)

    def _do_manage_account_press(self, weblocation: WebLocation) -> None:
        # If we're still waiting for our master-server connection,
        # keep the user informed of this instead of rushing in and
        # failing immediately.
        wait_for_connectivity(
            on_connected=lambda: self._do_manage_account(weblocation)
        )

    def _do_manage_account(self, weblocation: WebLocation) -> None:
        plus = bui.app.plus
        assert plus is not None

        bui.screenmessage(bui.Lstr(resource='oneMomentText'))

        # We expect to have a v2 account signed in if we get here.
        if plus.accounts.primary is None:
            logging.exception(
                'got manage-account press without v2 account present'
            )
            return

        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.cloud.ManageAccountMessage(weblocation=weblocation),
                on_response=bui.WeakCall(self._on_manage_account_response),
            )

    def _on_manage_account_response(
        self, response: bacommon.cloud.ManageAccountResponse | Exception
    ) -> None:
        if isinstance(response, Exception) or response.url is None:
            logging.warning(
                'Got error in manage-account-response: %s.', response
            )
            bui.screenmessage(bui.Lstr(resource='errorText'), color=(1, 0, 0))
            bui.getsound('error').play()
            return

        bui.open_url(response.url)

    def _on_leaderboards_press(self) -> None:
        if bui.app.plus is not None:
            bui.apptimer(
                0.15,
                bui.Call(bui.app.plus.show_game_service_ui, 'leaderboards'),
            )
        else:
            logging.warning('show_game_service_ui requires classic')

    def _have_unlinkable_v1_accounts(self) -> bool:
        plus = bui.app.plus
        assert plus is not None

        # If this is not present, we haven't had contact from the server
        # so let's not proceed.
        if plus.get_v1_account_public_login_id() is None:
            return False
        accounts = plus.get_v1_account_misc_read_val_2('linkedAccounts', [])
        return len(accounts) > 1

    def _update_unlink_accounts_button(self) -> None:
        if self._unlink_accounts_button is None:
            return
        if self._have_unlinkable_v1_accounts():
            clr = (0.75, 0.7, 0.8, 1.0)
        else:
            clr = (1.0, 1.0, 1.0, 0.25)
        bui.textwidget(edit=self._unlink_accounts_button_label, color=clr)

    def _should_show_legacy_unlink_button(self) -> bool:
        plus = bui.app.plus
        if plus is None:
            return False

        # Only show this when fully signed in to a v2 account.
        if not self._v1_signed_in or plus.accounts.primary is None:
            return False

        out = self._have_unlinkable_v1_accounts()
        return out

    def _update_linked_accounts_text(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        if self._linked_accounts_text is None:
            return

        # Disable this by default when signed in to a V2 account
        # (since this shows V1 links which we should no longer care about).
        if plus.accounts.primary is not None and not FORCE_ENABLE_V1_LINKING:
            return

        # if this is not present, we haven't had contact from the server so
        # let's not proceed..
        if plus.get_v1_account_public_login_id() is None:
            num = int(time.time()) % 4
            accounts_str = num * '.' + (4 - num) * ' '
        else:
            accounts = plus.get_v1_account_misc_read_val_2('linkedAccounts', [])
            # UPDATE - we now just print the number here; not the actual
            # accounts (they can see that in the unlink section if they're
            # curious)
            accounts_str = str(max(0, len(accounts) - 1))
        bui.textwidget(
            edit=self._linked_accounts_text,
            text=bui.Lstr(
                value='${L} ${A}',
                subs=[
                    (
                        '${L}',
                        bui.Lstr(resource=f'{self._r}.linkedAccountsText'),
                    ),
                    ('${A}', accounts_str),
                ],
            ),
        )

    def _refresh_campaign_progress_text(self) -> None:
        if self._campaign_progress_text is None:
            return
        p_str: str | bui.Lstr
        try:
            assert bui.app.classic is not None
            campaign = bui.app.classic.getcampaign('Default')
            levels = campaign.levels
            levels_complete = sum((1 if l.complete else 0) for l in levels)

            # Last level cant be completed; hence the -1;
            progress = min(1.0, float(levels_complete) / (len(levels) - 1))
            p_str = bui.Lstr(
                resource=f'{self._r}.campaignProgressText',
                subs=[('${PROGRESS}', str(int(progress * 100.0)) + '%')],
            )
        except Exception:
            p_str = '?'
            logging.exception('Error calculating co-op campaign progress.')
        bui.textwidget(edit=self._campaign_progress_text, text=p_str)

    def _refresh_tickets_text(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        if self._tickets_text is None:
            return
        try:
            tc_str = str(plus.get_v1_account_ticket_count())
        except Exception:
            logging.exception('error refreshing tickets text')
            tc_str = '-'
        bui.textwidget(
            edit=self._tickets_text,
            text=bui.Lstr(
                resource=f'{self._r}.ticketsText', subs=[('${COUNT}', tc_str)]
            ),
        )

    def _refresh_account_name_text(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        if self._account_name_text is None:
            return
        try:
            name_str = plus.get_v1_account_display_string()
        except Exception:
            logging.exception('error refreshing tickets text')
            name_str = '??'

        bui.textwidget(edit=self._account_name_text, text=name_str)

    def _refresh_achievements(self) -> None:
        assert bui.app.classic is not None
        if self._achievements_text is None:
            return
        complete = sum(
            1 if a.complete else 0 for a in bui.app.classic.ach.achievements
        )
        total = len(bui.app.classic.ach.achievements)
        txt_final = bui.Lstr(
            resource=f'{self._r}.achievementProgressText',
            subs=[('${COUNT}', str(complete)), ('${TOTAL}', str(total))],
        )

        if self._achievements_text is not None:
            bui.textwidget(edit=self._achievements_text, text=txt_final)

    def _link_accounts_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.account.link import AccountLinkWindow

        AccountLinkWindow(origin_widget=self._link_accounts_button)

    def _unlink_accounts_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.account.unlink import AccountUnlinkWindow

        if not self._have_unlinkable_v1_accounts():
            bui.getsound('error').play()
            return

        AccountUnlinkWindow(origin_widget=self._unlink_accounts_button)

    def _cancel_sign_in_press(self) -> None:
        # If we're waiting on an adapter to give us credentials, abort.
        self._signing_in_adapter = None

        plus = bui.app.plus
        assert plus is not None

        # Say we don't wanna be signed in anymore if we are.
        plus.accounts.set_primary_credentials(None)

        self._needs_refresh = True

        # Speed UI updates along.
        bui.apptimer(0.1, bui.WeakCall(self._update))

    def _sign_out_press(self) -> None:
        plus = bui.app.plus
        assert plus is not None

        if plus.accounts.have_primary_credentials():
            if (
                plus.accounts.primary is not None
                and LoginType.GPGS in plus.accounts.primary.logins
            ):
                self._explicitly_signed_out_of_gpgs = True
            plus.accounts.set_primary_credentials(None)
        else:
            plus.sign_out_v1()

        cfg = bui.app.config

        # Also take note that its our *explicit* intention to not be
        # signed in at this point (affects v1 accounts).
        cfg['Auto Account State'] = 'signed_out'
        cfg.commit()
        bui.buttonwidget(
            edit=self._sign_out_button,
            label=bui.Lstr(resource=f'{self._r}.signingOutText'),
        )

        # Speed UI updates along.
        bui.apptimer(0.1, bui.WeakCall(self._update))

    def _sign_in_press(self, login_type: str | LoginType) -> None:
        # If we're still waiting for our master-server connection,
        # keep the user informed of this instead of rushing in and
        # failing immediately.
        wait_for_connectivity(on_connected=lambda: self._sign_in(login_type))

    def _sign_in(self, login_type: str | LoginType) -> None:
        plus = bui.app.plus
        assert plus is not None

        # V1 login types are strings.
        if isinstance(login_type, str):
            plus.sign_in_v1(login_type)

            # Make note of the type account we're *wanting*
            # to be signed in with.
            cfg = bui.app.config
            cfg['Auto Account State'] = login_type
            cfg.commit()
            self._needs_refresh = True
            bui.apptimer(0.1, bui.WeakCall(self._update))
            return

        # V2 login sign-in buttons generally go through adapters.
        adapter = plus.accounts.login_adapters.get(login_type)
        if adapter is not None:
            self._signing_in_adapter = adapter
            adapter.sign_in(
                result_cb=bui.WeakCall(self._on_adapter_sign_in_result),
                description='account settings button',
            )
            # Will get 'Signing in...' to show.
            self._needs_refresh = True
            bui.apptimer(0.1, bui.WeakCall(self._update))
        else:
            bui.screenmessage(f'Unsupported login_type: {login_type.name}')

    def _on_adapter_sign_in_result(
        self,
        adapter: bui.LoginAdapter,
        result: bui.LoginAdapter.SignInResult | Exception,
    ) -> None:
        is_us = self._signing_in_adapter is adapter

        # If this isn't our current one we don't care.
        if not is_us:
            return

        # If it is us, note that we're done.
        self._signing_in_adapter = None

        if isinstance(result, Exception):
            # For now just make a bit of noise if anything went wrong;
            # can get more specific as needed later.
            logging.warning('Got error in v2 sign-in result: %s', result)
            bui.screenmessage(
                bui.Lstr(resource='internal.signInNoConnectionText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
        else:
            # Success! Plug in these credentials which will begin
            # verifying them and set our primary account-handle when
            # finished.
            plus = bui.app.plus
            assert plus is not None
            plus.accounts.set_primary_credentials(result.credentials)

            # Special case - if the user has explicitly signed out and
            # signed in again with GPGS via this button, warn them that
            # they need to use the app if they want to switch to a
            # different GPGS account.
            if (
                self._explicitly_signed_out_of_gpgs
                and adapter.login_type is LoginType.GPGS
            ):
                # Delay this slightly so it hopefully pops up after
                # credentials go through and the account name shows up.
                bui.apptimer(
                    1.5,
                    bui.Call(
                        bui.screenmessage,
                        bui.Lstr(
                            resource=self._r
                            + '.googlePlayGamesAccountSwitchText'
                        ),
                    ),
                )

        # Speed any UI updates along.
        self._needs_refresh = True
        bui.apptimer(0.1, bui.WeakCall(self._update))

    def _v2_proxy_sign_in_press(self) -> None:
        # If we're still waiting for our master-server connection, keep
        # the user informed of this instead of rushing in and failing
        # immediately.
        wait_for_connectivity(on_connected=self._v2_proxy_sign_in)

    def _v2_proxy_sign_in(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.account.v2proxy import V2ProxySignInWindow

        assert self._sign_in_v2_proxy_button is not None
        V2ProxySignInWindow(origin_widget=self._sign_in_v2_proxy_button)

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._back_button:
                sel_name = 'Back'
            elif sel == self._scrollwidget:
                sel_name = 'Scroll'
            else:
                raise ValueError('unrecognized selection')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = sel_name
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self))
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'Scroll':
                sel = self._scrollwidget
            else:
                sel = self._back_button
            bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)


def show_what_is_legacy_unlinking_page() -> None:
    """Show the webpage describing legacy unlinking."""
    plus = bui.app.plus
    assert plus is not None

    bamasteraddr = plus.get_master_server_address(version=2)
    bui.open_url(f'{bamasteraddr}/whatarev1links')
