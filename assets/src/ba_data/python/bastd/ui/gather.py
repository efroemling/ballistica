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
"""Provides UI for inviting/joining friends."""
# pylint: disable=too-many-lines

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, cast

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Optional, Tuple, Dict, List, Union, Callable


class GatherWindow(ba.Window):
    """Window for joining/inviting friends."""

    def __del__(self) -> None:
        _ba.set_party_icon_always_visible(False)

    def __init__(self,
                 transition: Optional[str] = 'in_right',
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from bastd.ui import tabs
        ba.set_analytics_screen('Gather Window')
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
        ba.app.ui.set_main_menu_location('Gather')
        _ba.set_party_icon_always_visible(True)
        self._public_parties: Dict[str, Dict[str, Any]] = {}
        uiscale = ba.app.ui.uiscale
        self._width = 1240 if uiscale is ba.UIScale.SMALL else 1040
        x_offs = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (582 if uiscale is ba.UIScale.SMALL else
                        680 if uiscale is ba.UIScale.MEDIUM else 800)
        self._current_tab: Optional[str] = None
        extra_top = 20 if uiscale is ba.UIScale.SMALL else 0
        self._r = 'gatherWindow'
        self._tab_data: Any = None
        self._internet_local_address: Optional[str] = None
        self._internet_host_text: Optional[ba.Widget] = None
        self._internet_join_text: Optional[ba.Widget] = None
        self._doing_access_check: Optional[bool] = None
        self._access_check_count: Optional[int] = None
        self._public_party_list_selection: Optional[Tuple[str, str]] = None
        self._internet_tab: Optional[str] = None
        self._internet_join_last_refresh_time = -99999.0
        self._last_public_party_list_rebuild_time: Optional[float] = None
        self._first_public_party_list_rebuild_time: Optional[float] = None
        self._internet_join_party_name_label: Optional[ba.Widget] = None
        self._internet_join_party_language_label: Optional[ba.Widget] = None
        self._internet_join_party_size_label: Optional[ba.Widget] = None
        self._internet_join_party_ping_label: Optional[ba.Widget] = None
        self._internet_host_scrollwidget: Optional[ba.Widget] = None
        self._internet_host_columnwidget: Optional[ba.Widget] = None
        self._internet_join_status_text: Optional[ba.Widget] = None
        self._internet_host_name_label_text: Optional[ba.Widget] = None
        self._internet_host_name_text: Optional[ba.Widget] = None
        self._internet_host_max_party_size_label: Optional[ba.Widget] = None
        self._internet_host_max_party_size_value: Optional[ba.Widget] = None
        self._internet_host_max_party_size_minus_button: (
            Optional[ba.Widget]) = None
        self._internet_host_max_party_size_plus_button: (
            Optional[ba.Widget]) = None
        self._internet_host_toggle_button: Optional[ba.Widget] = None
        self._internet_host_status_text: Optional[ba.Widget] = None
        self._internet_host_dedicated_server_info_text: (
            Optional[ba.Widget]) = None
        self._internet_lock_icon: Optional[ba.Widget] = None
        self._next_public_party_entry_index = 0
        self._refreshing_public_party_list: Optional[bool] = None
        self._last_public_party_connect_attempt_time: Optional[float] = None
        self._t_addr: Optional[ba.Widget] = None
        self._t_accessible: Optional[ba.Widget] = None
        self._t_accessible_extra: Optional[ba.Widget] = None

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height + extra_top),
            transition=transition,
            toolbar_visibility='menu_minimal',
            scale_origin_stack_offset=scale_origin,
            scale=(1.3 if uiscale is ba.UIScale.SMALL else
                   0.97 if uiscale is ba.UIScale.MEDIUM else 0.8),
            stack_offset=(0, -11) if uiscale is ba.UIScale.SMALL else (
                0, 0) if uiscale is ba.UIScale.MEDIUM else (0, 0)))

        if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._back)
            self._back_button = None
        else:
            self._back_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                position=(70 + x_offs, self._height - 74),
                size=(140, 60),
                scale=1.1,
                autoselect=True,
                label=ba.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self._back)
            ba.containerwidget(edit=self._root_widget, cancel_button=btn)
            ba.buttonwidget(edit=btn,
                            button_type='backSmall',
                            position=(70 + x_offs, self._height - 78),
                            size=(60, 60),
                            label=ba.charstr(ba.SpecialChar.BACK))

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 42),
                      size=(0, 0),
                      color=ba.app.ui.title_color,
                      scale=1.5,
                      h_align='center',
                      v_align='center',
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      maxwidth=550)

        platform = ba.app.platform
        subplatform = ba.app.subplatform

        tabs_def: List[Tuple[str, ba.Lstr]] = [
            ('about', ba.Lstr(resource=self._r + '.aboutText'))
        ]
        if _ba.get_account_misc_read_val('enablePublicParties', True):
            tabs_def.append(
                ('internet', ba.Lstr(resource=self._r + '.internetText')))
        if platform == 'android' and subplatform == 'google':
            tabs_def.append(
                ('google_play', ba.Lstr(resource=self._r + '.googlePlayText')))
        tabs_def.append(
            ('local_network', ba.Lstr(resource=self._r + '.localNetworkText')))

        tabs_def.append(('manual', ba.Lstr(resource=self._r + '.manualText')))

        scroll_buffer_h = 130 + 2 * x_offs
        tab_buffer_h = 250 + 2 * x_offs

        self._tab_buttons = tabs.create_tab_buttons(
            self._root_widget,
            tabs_def,
            pos=(tab_buffer_h * 0.5, self._height - 130),
            size=(self._width - tab_buffer_h, 50),
            on_select_call=self._set_tab)

        if ba.app.ui.use_toolbars:
            ba.widget(edit=self._tab_buttons[tabs_def[-1][0]],
                      right_widget=_ba.get_special_widget('party_button'))
            if uiscale is ba.UIScale.SMALL:
                ba.widget(edit=self._tab_buttons[tabs_def[0][0]],
                          left_widget=_ba.get_special_widget('back_button'))

        self._scroll_width = self._width - scroll_buffer_h
        self._scroll_height = self._height - 180.0

        # Not actually using a scroll widget anymore; just an image.
        scroll_left = (self._width - self._scroll_width) * 0.5
        scroll_bottom = self._height - self._scroll_height - 79 - 48
        buffer_h = 10
        buffer_v = 4
        ba.imagewidget(parent=self._root_widget,
                       position=(scroll_left - buffer_h,
                                 scroll_bottom - buffer_v),
                       size=(self._scroll_width + 2 * buffer_h,
                             self._scroll_height + 2 * buffer_v),
                       texture=ba.gettexture('scrollWidget'),
                       model_transparent=ba.getmodel('softEdgeOutside'))
        self._tab_container: Optional[ba.Widget] = None
        self._restore_state()

    def get_r(self) -> str:
        """(internal)"""
        return self._r

    def _on_google_play_show_invites_press(self) -> None:
        from bastd.ui import account
        if (_ba.get_account_state() != 'signed_in'
                or _ba.get_account_type() != 'Google Play'):
            account.show_sign_in_prompt('Google Play')
        else:
            _ba.show_invites_ui()

    def _on_google_play_invite_press(self) -> None:
        from bastd.ui import confirm
        from bastd.ui import account
        if (_ba.get_account_state() != 'signed_in'
                or _ba.get_account_type() != 'Google Play'):
            account.show_sign_in_prompt('Google Play')
        else:
            # If there's google play people connected to us, inform the user
            # that they will get disconnected. Otherwise just go ahead.
            google_player_count = (_ba.get_google_play_party_client_count())
            if google_player_count > 0:
                confirm.ConfirmWindow(
                    ba.Lstr(resource=self._r + '.googlePlayReInviteText',
                            subs=[('${COUNT}', str(google_player_count))]),
                    lambda: ba.timer(
                        0.2, _ba.invite_players, timetype=ba.TimeType.REAL),
                    width=500,
                    height=150,
                    ok_text=ba.Lstr(resource=self._r +
                                    '.googlePlayInviteText'))
            else:
                ba.timer(0.1, _ba.invite_players, timetype=ba.TimeType.REAL)

    def _invite_to_try_press(self) -> None:
        from bastd.ui import account
        from bastd.ui import appinvite
        if _ba.get_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return
        appinvite.handle_app_invites_press()

    def _set_tab(self, tab: str) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from bastd.ui import tabs
        if self._current_tab == tab:
            return
        self._current_tab = tab

        # We wanna preserve our current tab between runs.
        cfg = ba.app.config
        cfg['Gather Tab'] = tab
        cfg.commit()

        # Update tab colors based on which is selected.
        tabs.update_tab_button_colors(self._tab_buttons, tab)

        # (Re)create scroll widget.
        if self._tab_container:
            self._tab_container.delete()
        scroll_left = (self._width - self._scroll_width) * 0.5
        scroll_bottom = self._height - self._scroll_height - 79 - 48

        # A place where tabs can store data to get cleared when switching to
        # a different tab.
        self._tab_data = {}

        # So we can still select root level widgets with direction buttons.
        def _simple_message(tab2: str,
                            message: ba.Lstr,
                            string_height: float,
                            include_invite: bool = False) -> None:
            msc_scale = 1.1
            c_width_2 = self._scroll_width
            c_height_2 = min(self._scroll_height,
                             string_height * msc_scale + 100)
            try_tickets = _ba.get_account_misc_read_val(
                'friendTryTickets', None)
            if try_tickets is None:
                include_invite = False
            self._tab_container = cnt2 = ba.containerwidget(
                parent=self._root_widget,
                position=(scroll_left, scroll_bottom +
                          (self._scroll_height - c_height_2) * 0.5),
                size=(c_width_2, c_height_2),
                background=False,
                selectable=include_invite)
            ba.widget(edit=cnt2, up_widget=self._tab_buttons[tab2])

            ba.textwidget(
                parent=cnt2,
                position=(c_width_2 * 0.5,
                          c_height_2 * (0.58 if include_invite else 0.5)),
                color=(0.6, 1.0, 0.6),
                scale=msc_scale,
                size=(0, 0),
                maxwidth=c_width_2 * 0.9,
                max_height=c_height_2 * (0.7 if include_invite else 0.9),
                h_align='center',
                v_align='center',
                text=message)
            if include_invite:
                ba.textwidget(parent=cnt2,
                              position=(c_width_2 * 0.57, 35),
                              color=(0, 1, 0),
                              scale=0.6,
                              size=(0, 0),
                              maxwidth=c_width_2 * 0.5,
                              h_align='right',
                              v_align='center',
                              flatness=1.0,
                              text=ba.Lstr(
                                  resource=self._r + '.inviteAFriendText',
                                  subs=[('${COUNT}', str(try_tickets))]))
                ba.buttonwidget(
                    parent=cnt2,
                    position=(c_width_2 * 0.59, 10),
                    size=(230, 50),
                    color=(0.54, 0.42, 0.56),
                    textcolor=(0, 1, 0),
                    label=ba.Lstr(resource='gatherWindow.inviteFriendsText',
                                  fallback_resource=(
                                      'gatherWindow.getFriendInviteCodeText')),
                    autoselect=True,
                    on_activate_call=ba.WeakCall(self._invite_to_try_press),
                    up_widget=self._tab_buttons[tab2])

        if tab == 'about':
            msg = ba.Lstr(resource=self._r + '.aboutDescriptionText',
                          subs=[('${PARTY}',
                                 ba.charstr(ba.SpecialChar.PARTY_ICON)),
                                ('${BUTTON}',
                                 ba.charstr(ba.SpecialChar.TOP_BUTTON))])

            # Let's not talk about sharing in vr-mode; its tricky to fit more
            # than one head in a VR-headset ;-)
            if not ba.app.vr_mode:
                msg = ba.Lstr(
                    value='${A}\n\n${B}',
                    subs=[
                        ('${A}', msg),
                        ('${B}',
                         ba.Lstr(resource=self._r +
                                 '.aboutDescriptionLocalMultiplayerExtraText'))
                    ])

            _simple_message(tab, msg, 400, include_invite=True)

        elif tab == 'google_play':
            c_width = self._scroll_width
            c_height = 380.0
            self._tab_container = cnt = ba.containerwidget(
                parent=self._root_widget,
                position=(scroll_left, scroll_bottom +
                          (self._scroll_height - c_height) * 0.5),
                size=(c_width, c_height),
                background=False,
                selection_loops_to_parent=True)
            v = c_height - 30.0
            ba.textwidget(
                parent=cnt,
                position=(c_width * 0.5, v - 140.0),
                color=(0.6, 1.0, 0.6),
                scale=1.3,
                size=(0.0, 0.0),
                maxwidth=c_width * 0.9,
                h_align='center',
                v_align='center',
                text=ba.Lstr(resource='googleMultiplayerDiscontinuedText'))

        elif tab == 'internet':
            c_width = self._scroll_width
            c_height = self._scroll_height - 20
            self._tab_container = cnt = ba.containerwidget(
                parent=self._root_widget,
                position=(scroll_left, scroll_bottom +
                          (self._scroll_height - c_height) * 0.5),
                size=(c_width, c_height),
                background=False,
                selection_loops_to_parent=True)
            v = c_height - 30
            self._internet_join_text = txt = ba.textwidget(
                parent=cnt,
                position=(c_width * 0.5 - 245, v - 13),
                color=(0.6, 1.0, 0.6),
                scale=1.3,
                size=(200, 30),
                maxwidth=250,
                h_align='left',
                v_align='center',
                click_activate=True,
                selectable=True,
                autoselect=True,
                on_activate_call=lambda: self._set_internet_tab(
                    'join', playsound=True),
                text=ba.Lstr(resource=self._r +
                             '.joinPublicPartyDescriptionText'))
            ba.widget(edit=txt, up_widget=self._tab_buttons[tab])
            self._internet_host_text = txt = ba.textwidget(
                parent=cnt,
                position=(c_width * 0.5 + 45, v - 13),
                color=(0.6, 1.0, 0.6),
                scale=1.3,
                size=(200, 30),
                maxwidth=250,
                h_align='left',
                v_align='center',
                click_activate=True,
                selectable=True,
                autoselect=True,
                on_activate_call=lambda: self._set_internet_tab(
                    'host', playsound=True),
                text=ba.Lstr(resource=self._r +
                             '.hostPublicPartyDescriptionText'))
            ba.widget(edit=txt,
                      left_widget=self._internet_join_text,
                      up_widget=self._tab_buttons[tab])
            ba.widget(edit=self._internet_join_text, right_widget=txt)

            # Attempt to fetch our local address so we have it for
            # error messages.
            self._internet_local_address = None

            class AddrFetchThread(threading.Thread):
                """Thread for fetching an address in the bg."""

                def __init__(self, call: Callable[[Any], Any]):
                    super().__init__()
                    self._call = call

                def run(self) -> None:
                    try:
                        # FIXME: Update this to work with IPv6 at some point.
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.connect(('8.8.8.8', 80))
                        val = sock.getsockname()[0]
                        sock.close()
                        ba.pushcall(ba.Call(self._call, val),
                                    from_other_thread=True)
                    except Exception as exc:
                        # Ignore expected network errors; log others.
                        import errno
                        if (isinstance(exc, OSError)
                                and exc.errno == errno.ENETUNREACH):
                            pass
                        else:
                            ba.print_exception()

            AddrFetchThread(ba.WeakCall(
                self._internet_fetch_local_addr_cb)).start()

            assert self._internet_tab is not None
            self._set_internet_tab(self._internet_tab)
            self._tab_data = {
                'update_timer':
                    ba.Timer(0.2,
                             ba.WeakCall(self._update_internet_tab),
                             repeat=True,
                             timetype=ba.TimeType.REAL)
            }

            # Also update it immediately so we don't have to wait for the
            # initial query.
            self._update_internet_tab()

        elif tab == 'local_network':
            c_width = self._scroll_width
            c_height = self._scroll_height - 20
            sub_scroll_height = c_height - 85
            sub_scroll_width = 650

            class NetScanner:
                """Class for scanning for games on the lan."""

                def __init__(self, scrollwidget: ba.Widget,
                             tab_button: ba.Widget, width: float):
                    self._scrollwidget = scrollwidget
                    self._tab_button = tab_button
                    self._columnwidget = ba.columnwidget(
                        parent=self._scrollwidget,
                        border=2,
                        margin=0,
                        left_border=10)
                    ba.widget(edit=self._columnwidget, up_widget=tab_button)
                    self._width = width
                    self._last_selected_host: Optional[Dict[str, Any]] = None

                    self._update_timer = ba.Timer(1.0,
                                                  ba.WeakCall(self.update),
                                                  timetype=ba.TimeType.REAL,
                                                  repeat=True)
                    # Go ahead and run a few *almost* immediately so we don't
                    # have to wait a second.
                    self.update()
                    ba.timer(0.25,
                             ba.WeakCall(self.update),
                             timetype=ba.TimeType.REAL)

                def __del__(self) -> None:
                    _ba.end_host_scanning()

                def _on_select(self, host: Dict[str, Any]) -> None:
                    self._last_selected_host = host

                def _on_activate(self, host: Dict[str, Any]) -> None:
                    _ba.connect_to_party(host['address'])

                def update(self) -> None:
                    """(internal)"""
                    t_scale = 1.6
                    for child in self._columnwidget.get_children():
                        child.delete()

                    # Grab this now this since adding widgets will change it.
                    last_selected_host = self._last_selected_host
                    hosts = _ba.host_scan_cycle()
                    for i, host in enumerate(hosts):
                        txt3 = ba.textwidget(
                            parent=self._columnwidget,
                            size=(self._width / t_scale, 30),
                            selectable=True,
                            color=(1, 1, 1),
                            on_select_call=ba.Call(self._on_select, host),
                            on_activate_call=ba.Call(self._on_activate, host),
                            click_activate=True,
                            text=host['display_string'],
                            h_align='left',
                            v_align='center',
                            corner_scale=t_scale,
                            maxwidth=(self._width / t_scale) * 0.93)
                        if host == last_selected_host:
                            ba.containerwidget(edit=self._columnwidget,
                                               selected_child=txt3,
                                               visible_child=txt3)
                        if i == 0:
                            ba.widget(edit=txt3, up_widget=self._tab_button)

            self._tab_container = cnt = ba.containerwidget(
                parent=self._root_widget,
                position=(scroll_left, scroll_bottom +
                          (self._scroll_height - c_height) * 0.5),
                size=(c_width, c_height),
                background=False,
                selection_loops_to_parent=True)
            v = c_height - 30
            ba.textwidget(parent=cnt,
                          position=(c_width * 0.5, v - 3),
                          color=(0.6, 1.0, 0.6),
                          scale=1.3,
                          size=(0, 0),
                          maxwidth=c_width * 0.9,
                          h_align='center',
                          v_align='center',
                          text=ba.Lstr(resource=self._r +
                                       '.localNetworkDescriptionText'))
            v -= 15
            v -= sub_scroll_height + 23
            scrollw = ba.scrollwidget(
                parent=cnt,
                position=((self._scroll_width - sub_scroll_width) * 0.5, v),
                size=(sub_scroll_width, sub_scroll_height))

            self._tab_data = NetScanner(scrollw,
                                        self._tab_buttons[tab],
                                        width=sub_scroll_width)

            ba.widget(edit=scrollw,
                      autoselect=True,
                      up_widget=self._tab_buttons[tab])

        elif tab == 'bluetooth':
            c_width = self._scroll_width
            c_height = 380
            sub_scroll_width = 650

            self._tab_container = cnt = ba.containerwidget(
                parent=self._root_widget,
                position=(scroll_left, scroll_bottom +
                          (self._scroll_height - c_height) * 0.5),
                size=(c_width, c_height),
                background=False,
                selection_loops_to_parent=True)
            v = c_height - 30
            ba.textwidget(parent=cnt,
                          position=(c_width * 0.5, v),
                          color=(0.6, 1.0, 0.6),
                          scale=1.3,
                          size=(0, 0),
                          maxwidth=c_width * 0.9,
                          h_align='center',
                          v_align='center',
                          text=ba.Lstr(resource=self._r +
                                       '.bluetoothDescriptionText'))
            v -= 35
            ba.textwidget(parent=cnt,
                          position=(c_width * 0.5, v),
                          color=(0.6, 1.0, 0.6),
                          scale=0.7,
                          size=(0, 0),
                          maxwidth=c_width * 0.9,
                          h_align='center',
                          v_align='center',
                          text=ba.Lstr(resource=self._r +
                                       '.bluetoothAndroidSupportText'))

            v -= 55
            btn = ba.buttonwidget(
                parent=cnt,
                position=(c_width * 0.5 - sub_scroll_width * 0.5 + 10, v - 75),
                size=(300, 70),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.bluetoothHostText'))
            ba.widget(edit=btn, up_widget=self._tab_buttons[tab])
            btn = ba.buttonwidget(
                parent=cnt,
                position=(c_width * 0.5 - sub_scroll_width * 0.5 + 330,
                          v - 75),
                size=(300, 70),
                autoselect=True,
                on_activate_call=ba.Call(ba.screenmessage,
                                         'FIXME: Not wired up yet.'),
                label=ba.Lstr(resource=self._r + '.bluetoothJoinText'))
            ba.widget(edit=btn, up_widget=self._tab_buttons[tab])
            ba.widget(edit=self._tab_buttons[tab], down_widget=btn)

        elif tab == 'wifi_direct':
            c_width = self._scroll_width
            c_height = self._scroll_height - 20
            self._tab_container = cnt = ba.containerwidget(
                parent=self._root_widget,
                position=(scroll_left, scroll_bottom +
                          (self._scroll_height - c_height) * 0.5),
                size=(c_width, c_height),
                background=False,
                selection_loops_to_parent=True)
            v = c_height - 80

            ba.textwidget(parent=cnt,
                          position=(c_width * 0.5, v),
                          color=(0.6, 1.0, 0.6),
                          scale=1.0,
                          size=(0, 0),
                          maxwidth=c_width * 0.95,
                          max_height=140,
                          h_align='center',
                          v_align='center',
                          text=ba.Lstr(resource=self._r +
                                       '.wifiDirectDescriptionTopText'))
            v -= 140
            btn = ba.buttonwidget(
                parent=cnt,
                position=(c_width * 0.5 - 175, v),
                size=(350, 65),
                label=ba.Lstr(resource=self._r +
                              '.wifiDirectOpenWiFiSettingsText'),
                autoselect=True,
                on_activate_call=_ba.android_show_wifi_settings)
            v -= 82

            ba.widget(edit=btn, up_widget=self._tab_buttons[tab])

            ba.textwidget(parent=cnt,
                          position=(c_width * 0.5, v),
                          color=(0.6, 1.0, 0.6),
                          scale=0.9,
                          size=(0, 0),
                          maxwidth=c_width * 0.95,
                          max_height=150,
                          h_align='center',
                          v_align='center',
                          text=ba.Lstr(resource=self._r +
                                       '.wifiDirectDescriptionBottomText',
                                       subs=[('${APP_NAME}',
                                              ba.Lstr(resource='titleText'))]))

        elif tab == 'manual':
            c_width = self._scroll_width
            c_height = 380
            last_addr = ba.app.config.get('Last Manual Party Connect Address',
                                          '')

            self._tab_container = cnt = ba.containerwidget(
                parent=self._root_widget,
                position=(scroll_left, scroll_bottom +
                          (self._scroll_height - c_height) * 0.5),
                size=(c_width, c_height),
                background=False,
                selection_loops_to_parent=True)
            v = c_height - 30
            ba.textwidget(parent=cnt,
                          position=(c_width * 0.5, v),
                          color=(0.6, 1.0, 0.6),
                          scale=1.3,
                          size=(0, 0),
                          maxwidth=c_width * 0.9,
                          h_align='center',
                          v_align='center',
                          text=ba.Lstr(resource=self._r +
                                       '.manualDescriptionText'))
            v -= 30
            v -= 70
            ba.textwidget(parent=cnt,
                          position=(c_width * 0.5 - 260 - 50, v),
                          color=(0.6, 1.0, 0.6),
                          scale=1.0,
                          size=(0, 0),
                          maxwidth=130,
                          h_align='right',
                          v_align='center',
                          text=ba.Lstr(resource=self._r +
                                       '.manualAddressText'))
            txt = ba.textwidget(parent=cnt,
                                editable=True,
                                description=ba.Lstr(resource=self._r +
                                                    '.manualAddressText'),
                                position=(c_width * 0.5 - 240 - 50, v - 30),
                                text=last_addr,
                                autoselect=True,
                                v_align='center',
                                scale=1.0,
                                size=(420, 60))
            ba.textwidget(parent=cnt,
                          position=(c_width * 0.5 - 260 + 490, v),
                          color=(0.6, 1.0, 0.6),
                          scale=1.0,
                          size=(0, 0),
                          maxwidth=80,
                          h_align='right',
                          v_align='center',
                          text=ba.Lstr(resource=self._r + '.portText'))
            txt2 = ba.textwidget(parent=cnt,
                                 editable=True,
                                 description=ba.Lstr(resource=self._r +
                                                     '.portText'),
                                 text='43210',
                                 autoselect=True,
                                 max_chars=5,
                                 position=(c_width * 0.5 - 240 + 490, v - 30),
                                 v_align='center',
                                 scale=1.0,
                                 size=(170, 60))

            v -= 110

            def _connect(textwidget: ba.Widget,
                         port_textwidget: ba.Widget) -> None:
                addr = cast(str, ba.textwidget(query=textwidget))
                if addr == '':
                    ba.screenmessage(
                        ba.Lstr(resource='internal.invalidAddressErrorText'),
                        color=(1, 0, 0))
                    ba.playsound(ba.getsound('error'))
                    return
                try:
                    port = int(cast(str, ba.textwidget(query=port_textwidget)))
                except ValueError:
                    port = -1
                if port > 65535 or port < 0:
                    ba.screenmessage(
                        ba.Lstr(resource='internal.invalidPortErrorText'),
                        color=(1, 0, 0))
                    ba.playsound(ba.getsound('error'))
                    return

                class HostAddrFetchThread(threading.Thread):
                    """Thread to fetch an addr."""

                    def __init__(self, name: str,
                                 call: Callable[[Optional[str]], Any]):
                        super().__init__()
                        self._name = name
                        self._call = call

                    def run(self) -> None:
                        result: Optional[str]
                        try:
                            import socket
                            result = socket.gethostbyname(self._name)
                        except Exception:
                            result = None
                        ba.pushcall(ba.Call(self._call, result),
                                    from_other_thread=True)

                def do_it_2(addr2: Optional[str]) -> None:
                    if addr2 is None:
                        ba.screenmessage(ba.Lstr(
                            resource='internal.unableToResolveHostText'),
                                         color=(1, 0, 0))
                        ba.playsound(ba.getsound('error'))
                    else:
                        # Store for later.
                        cfg2 = ba.app.config
                        cfg2['Last Manual Party Connect Address'] = addr2
                        cfg2.commit()
                        _ba.connect_to_party(addr2, port=port)

                HostAddrFetchThread(addr, do_it_2).start()

            btn = ba.buttonwidget(
                parent=cnt,
                size=(300, 70),
                label=ba.Lstr(resource=self._r + '.manualConnectText'),
                position=(c_width * 0.5 - 150, v),
                autoselect=True,
                on_activate_call=ba.Call(_connect, txt, txt2))
            ba.widget(edit=txt, up_widget=self._tab_buttons[tab])
            ba.textwidget(edit=txt, on_return_press_call=btn.activate)
            ba.textwidget(edit=txt2, on_return_press_call=btn.activate)
            v -= 45

            tscl = 0.85
            tspc = 25

            def _safe_set_text(txt3: ba.Widget,
                               val: Union[str, ba.Lstr],
                               success: bool = True) -> None:
                if txt3:
                    ba.textwidget(edit=txt3,
                                  text=val,
                                  color=(0, 1, 0) if success else (1, 1, 0))

            # This currently doesn't work from china since we go through a
            # reverse proxy there.
            # UPDATE: it should work now; our proxy server forwards along
            # original IPs.
            do_internet_check = True

            def do_it(v2: float, cnt2: Optional[ba.Widget]) -> None:
                if not cnt2:
                    return

                ba.playsound(ba.getsound('swish'))
                ba.textwidget(parent=cnt2,
                              position=(c_width * 0.5 - 10, v2),
                              color=(0.6, 1.0, 0.6),
                              scale=tscl,
                              size=(0, 0),
                              maxwidth=c_width * 0.45,
                              flatness=1.0,
                              h_align='right',
                              v_align='center',
                              text=ba.Lstr(resource=self._r +
                                           '.manualYourLocalAddressText'))
                txt3 = ba.textwidget(parent=cnt2,
                                     position=(c_width * 0.5, v2),
                                     color=(0.5, 0.5, 0.5),
                                     scale=tscl,
                                     size=(0, 0),
                                     maxwidth=c_width * 0.45,
                                     flatness=1.0,
                                     h_align='left',
                                     v_align='center',
                                     text=ba.Lstr(resource=self._r +
                                                  '.checkingText'))

                class AddrFetchThread2(threading.Thread):
                    """Thread for fetching an addr."""

                    def __init__(self, window: GatherWindow,
                                 textwidget: ba.Widget):
                        super().__init__()
                        self._window = window
                        self._textwidget = textwidget

                    def run(self) -> None:
                        try:
                            # FIXME: Update this to work with IPv6.
                            import socket
                            sock = socket.socket(socket.AF_INET,
                                                 socket.SOCK_DGRAM)
                            sock.connect(('8.8.8.8', 80))
                            val = sock.getsockname()[0]
                            sock.close()
                            # val = ([(s.connect(('8.8.8.8', 80)),
                            #          s.getsockname()[0], s.close())
                            # for s in [
                            #              socket.socket(
                            # socket.AF_INET, socket.
                            #                            SOCK_DGRAM)
                            #          ]][0][1])
                            ba.pushcall(ba.Call(_safe_set_text,
                                                self._textwidget, val),
                                        from_other_thread=True)
                        except Exception as exc:
                            err_str = str(exc)

                            # FIXME: Should look at exception types here,
                            #  not strings.
                            if 'Network is unreachable' in err_str:
                                ba.pushcall(ba.Call(
                                    _safe_set_text, self._textwidget,
                                    ba.Lstr(resource=self._window.get_r() +
                                            '.noConnectionText'), False),
                                            from_other_thread=True)
                            else:
                                ba.pushcall(ba.Call(
                                    _safe_set_text, self._textwidget,
                                    ba.Lstr(resource=self._window.get_r() +
                                            '.addressFetchErrorText'), False),
                                            from_other_thread=True)
                                ba.pushcall(ba.Call(
                                    ba.print_error,
                                    'error in AddrFetchThread: ' + str(exc)),
                                            from_other_thread=True)

                AddrFetchThread2(self, txt3).start()

                v2 -= tspc
                ba.textwidget(
                    parent=cnt2,
                    position=(c_width * 0.5 - 10, v2),
                    color=(0.6, 1.0, 0.6),
                    scale=tscl,
                    size=(0, 0),
                    maxwidth=c_width * 0.45,
                    flatness=1.0,
                    h_align='right',
                    v_align='center',
                    text=ba.Lstr(resource=self._r +
                                 '.manualYourAddressFromInternetText'))

                t_addr = ba.textwidget(parent=cnt2,
                                       position=(c_width * 0.5, v2),
                                       color=(0.5, 0.5, 0.5),
                                       scale=tscl,
                                       size=(0, 0),
                                       maxwidth=c_width * 0.45,
                                       h_align='left',
                                       v_align='center',
                                       flatness=1.0,
                                       text=ba.Lstr(resource=self._r +
                                                    '.checkingText'))
                v2 -= tspc
                ba.textwidget(parent=cnt2,
                              position=(c_width * 0.5 - 10, v2),
                              color=(0.6, 1.0, 0.6),
                              scale=tscl,
                              size=(0, 0),
                              maxwidth=c_width * 0.45,
                              flatness=1.0,
                              h_align='right',
                              v_align='center',
                              text=ba.Lstr(resource=self._r +
                                           '.manualJoinableFromInternetText'))

                t_accessible = ba.textwidget(parent=cnt2,
                                             position=(c_width * 0.5, v2),
                                             color=(0.5, 0.5, 0.5),
                                             scale=tscl,
                                             size=(0, 0),
                                             maxwidth=c_width * 0.45,
                                             flatness=1.0,
                                             h_align='left',
                                             v_align='center',
                                             text=ba.Lstr(resource=self._r +
                                                          '.checkingText'))
                v2 -= 28
                t_accessible_extra = ba.textwidget(parent=cnt2,
                                                   position=(c_width * 0.5,
                                                             v2),
                                                   color=(1, 0.5, 0.2),
                                                   scale=0.7,
                                                   size=(0, 0),
                                                   maxwidth=c_width * 0.9,
                                                   flatness=1.0,
                                                   h_align='center',
                                                   v_align='center',
                                                   text='')

                self._doing_access_check = False
                self._access_check_count = 0  # Cap our refreshes eventually.
                self._tab_data['access_check_timer'] = ba.Timer(
                    10.0,
                    ba.WeakCall(self._access_check_update, t_addr,
                                t_accessible, t_accessible_extra),
                    repeat=True,
                    timetype=ba.TimeType.REAL)

                # Kick initial off.
                self._access_check_update(t_addr, t_accessible,
                                          t_accessible_extra)
                if check_button:
                    check_button.delete()

            if do_internet_check:
                check_button = ba.textwidget(
                    parent=cnt,
                    size=(250, 60),
                    text=ba.Lstr(resource=self._r + '.showMyAddressText'),
                    v_align='center',
                    h_align='center',
                    click_activate=True,
                    position=(c_width * 0.5 - 125, v - 30),
                    autoselect=True,
                    color=(0.5, 0.9, 0.5),
                    scale=0.8,
                    selectable=True,
                    on_activate_call=ba.Call(do_it, v, cnt))

    def _internet_fetch_local_addr_cb(self, val: str) -> None:
        self._internet_local_address = str(val)

    def _set_internet_tab(self, value: str, playsound: bool = False) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        if playsound:
            ba.playsound(ba.getsound('click01'))

        # If we're switching in from elsewhere, reset our selection.
        # (prevents selecting something way down the list if we switched away
        # and came back)
        if self._internet_tab != value:
            self._public_party_list_selection = None

        self._internet_tab = value
        active_color = (0.6, 1.0, 0.6)
        inactive_color = (0.5, 0.4, 0.5)
        ba.textwidget(
            edit=self._internet_join_text,
            color=active_color if value == 'join' else inactive_color)
        ba.textwidget(
            edit=self._internet_host_text,
            color=active_color if value == 'host' else inactive_color)

        # Clear anything in existence.
        for widget in [
                self._internet_host_scrollwidget,
                self._internet_host_name_text,
                self._internet_host_toggle_button,
                self._internet_host_name_label_text,
                self._internet_host_status_text,
                self._internet_join_party_size_label,
                self._internet_join_party_name_label,
                self._internet_join_party_language_label,
                self._internet_join_party_ping_label,
                self._internet_host_max_party_size_label,
                self._internet_host_max_party_size_value,
                self._internet_host_max_party_size_minus_button,
                self._internet_host_max_party_size_plus_button,
                self._internet_join_status_text,
                self._internet_host_dedicated_server_info_text
        ]:
            if widget is not None:
                widget.delete()

        c_width = self._scroll_width
        c_height = self._scroll_height - 20
        sub_scroll_height = c_height - 90
        sub_scroll_width = 830
        v = c_height - 35
        v -= 25
        is_public_enabled = _ba.get_public_party_enabled()
        if value == 'join':
            # Reset this so we do an immediate refresh query.
            self._internet_join_last_refresh_time = -99999.0

            # Reset our list of public parties.
            self._public_parties = {}
            self._last_public_party_list_rebuild_time = 0
            self._first_public_party_list_rebuild_time = None
            self._internet_join_party_name_label = ba.textwidget(
                text=ba.Lstr(resource='nameText'),
                parent=self._tab_container,
                size=(0, 0),
                position=(90, v - 8),
                maxwidth=60,
                scale=0.6,
                color=(0.5, 0.5, 0.5),
                flatness=1.0,
                shadow=0.0,
                h_align='center',
                v_align='center')
            if bool(False):
                self._internet_join_party_language_label = ba.textwidget(
                    text=ba.Lstr(
                        resource='settingsWindowAdvanced.languageText'),
                    parent=self._tab_container,
                    size=(0, 0),
                    position=(662, v - 8),
                    maxwidth=100,
                    scale=0.6,
                    color=(0.5, 0.5, 0.5),
                    flatness=1.0,
                    shadow=0.0,
                    h_align='center',
                    v_align='center')
            self._internet_join_party_size_label = ba.textwidget(
                text=ba.Lstr(resource=self._r + '.partySizeText'),
                parent=self._tab_container,
                size=(0, 0),
                position=(755, v - 8),
                maxwidth=60,
                scale=0.6,
                color=(0.5, 0.5, 0.5),
                flatness=1.0,
                shadow=0.0,
                h_align='center',
                v_align='center')
            self._internet_join_party_ping_label = ba.textwidget(
                text=ba.Lstr(resource=self._r + '.pingText'),
                parent=self._tab_container,
                size=(0, 0),
                position=(825, v - 8),
                maxwidth=60,
                scale=0.6,
                color=(0.5, 0.5, 0.5),
                flatness=1.0,
                shadow=0.0,
                h_align='center',
                v_align='center')
            v -= sub_scroll_height + 23

            self._internet_host_scrollwidget = scrollw = ba.scrollwidget(
                parent=self._tab_container,
                simple_culling_v=10,
                position=((self._scroll_width - sub_scroll_width) * 0.5, v),
                size=(sub_scroll_width, sub_scroll_height))
            ba.widget(edit=scrollw, autoselect=True)
            colw = self._internet_host_columnwidget = ba.containerwidget(
                parent=scrollw, background=False, size=(400, 400))
            ba.containerwidget(edit=scrollw, claims_left_right=True)
            ba.containerwidget(edit=colw, claims_left_right=True)

            self._internet_join_status_text = ba.textwidget(
                parent=self._tab_container,
                text=ba.Lstr(value='${A}...',
                             subs=[('${A}',
                                    ba.Lstr(resource='store.loadingText'))]),
                size=(0, 0),
                scale=0.9,
                flatness=1.0,
                shadow=0.0,
                h_align='center',
                v_align='top',
                maxwidth=c_width,
                color=(0.6, 0.6, 0.6),
                position=(c_width * 0.5, c_height * 0.5))

        if value == 'host':
            v -= 30
            party_name_text = ba.Lstr(
                resource='gatherWindow.partyNameText',
                fallback_resource='editGameListWindow.nameText')
            self._internet_host_name_label_text = ba.textwidget(
                parent=self._tab_container,
                size=(0, 0),
                h_align='right',
                v_align='center',
                maxwidth=200,
                scale=0.8,
                color=ba.app.ui.infotextcolor,
                position=(210, v - 9),
                text=party_name_text)
            self._internet_host_name_text = ba.textwidget(
                parent=self._tab_container,
                editable=True,
                size=(535, 40),
                position=(230, v - 30),
                text=ba.app.config.get('Public Party Name', ''),
                maxwidth=494,
                shadow=0.3,
                flatness=1.0,
                description=party_name_text,
                autoselect=True,
                v_align='center',
                corner_scale=1.0)

            v -= 60
            self._internet_host_max_party_size_label = ba.textwidget(
                parent=self._tab_container,
                size=(0, 0),
                h_align='right',
                v_align='center',
                maxwidth=200,
                scale=0.8,
                color=ba.app.ui.infotextcolor,
                position=(210, v - 9),
                text=ba.Lstr(resource='maxPartySizeText',
                             fallback_resource='maxConnectionsText'))
            self._internet_host_max_party_size_value = ba.textwidget(
                parent=self._tab_container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=1.2,
                color=(1, 1, 1),
                position=(240, v - 9),
                text=str(_ba.get_public_party_max_size()))
            btn1 = self._internet_host_max_party_size_minus_button = (
                ba.buttonwidget(
                    parent=self._tab_container,
                    size=(40, 40),
                    on_activate_call=ba.WeakCall(
                        self._on_max_public_party_size_minus_press),
                    position=(280, v - 26),
                    label='-',
                    autoselect=True))
            btn2 = self._internet_host_max_party_size_plus_button = (
                ba.buttonwidget(parent=self._tab_container,
                                size=(40, 40),
                                on_activate_call=ba.WeakCall(
                                    self._on_max_public_party_size_plus_press),
                                position=(350, v - 26),
                                label='+',
                                autoselect=True))
            v -= 50
            v -= 70
            if is_public_enabled:
                label = ba.Lstr(
                    resource='gatherWindow.makePartyPrivateText',
                    fallback_resource='gatherWindow.stopAdvertisingText')
            else:
                label = ba.Lstr(
                    resource='gatherWindow.makePartyPublicText',
                    fallback_resource='gatherWindow.startAdvertisingText')
            self._internet_host_toggle_button = ba.buttonwidget(
                parent=self._tab_container,
                label=label,
                size=(400, 80),
                on_activate_call=self._on_stop_internet_advertising_press
                if is_public_enabled else
                self._on_start_internet_advertizing_press,
                position=(c_width * 0.5 - 200, v),
                autoselect=True,
                up_widget=btn2)
            ba.widget(edit=self._internet_host_name_text, down_widget=btn2)
            ba.widget(edit=btn2, up_widget=self._internet_host_name_text)
            ba.widget(edit=btn1, up_widget=self._internet_host_name_text)
            ba.widget(edit=self._internet_join_text,
                      down_widget=self._internet_host_name_text)
            v -= 10
            self._internet_host_status_text = ba.textwidget(
                parent=self._tab_container,
                text=ba.Lstr(resource=self._r + '.partyStatusNotPublicText'),
                size=(0, 0),
                scale=0.7,
                flatness=1.0,
                shadow=0.0,
                h_align='center',
                v_align='top',
                maxwidth=c_width,
                color=(0.6, 0.6, 0.6),
                position=(c_width * 0.5, v))
            v -= 90
            self._internet_host_dedicated_server_info_text = ba.textwidget(
                parent=self._tab_container,
                text=ba.Lstr(resource=self._r + '.dedicatedServerInfoText'),
                size=(0, 0),
                scale=0.7,
                flatness=1.0,
                shadow=0.0,
                h_align='center',
                v_align='center',
                maxwidth=c_width * 0.9,
                color=ba.app.ui.infotextcolor,
                position=(c_width * 0.5, v))

            # If public sharing is already on,
            # launch a status-check immediately.
            if _ba.get_public_party_enabled():
                self._do_internet_status_check()

        # Now add a lock icon overlay for if we don't have pro.
        icon = self._internet_lock_icon
        if icon and self._internet_lock_icon:
            self._internet_lock_icon.delete()  # Kill any existing.
        self._internet_lock_icon = ba.imagewidget(
            parent=self._tab_container,
            position=(c_width * 0.5 - 60, c_height * 0.5 - 50),
            size=(120, 120),
            opacity=0.0 if not self._is_internet_locked() else 0.5,
            texture=ba.gettexture('lock'))

    def _is_internet_locked(self) -> bool:
        from ba.internal import have_pro
        if _ba.get_account_misc_read_val('ilck', False):
            return not have_pro()
        return False

    def _on_max_public_party_size_minus_press(self) -> None:
        val = _ba.get_public_party_max_size()
        val -= 1
        if val < 1:
            val = 1
        _ba.set_public_party_max_size(val)
        ba.textwidget(edit=self._internet_host_max_party_size_value,
                      text=str(val))

    def _on_max_public_party_size_plus_press(self) -> None:
        val = _ba.get_public_party_max_size()
        val += 1
        _ba.set_public_party_max_size(val)
        ba.textwidget(edit=self._internet_host_max_party_size_value,
                      text=str(val))

    def _on_public_party_query_result(
            self, result: Optional[Dict[str, Any]]) -> None:
        with ba.Context('ui'):
            # Any time we get any result at all, kill our loading status.
            status_text = self._internet_join_status_text
            if status_text:
                # Don't show results if not signed in
                # (probably didn't get any anyway).
                if _ba.get_account_state() != 'signed_in':
                    ba.textwidget(edit=status_text,
                                  text=ba.Lstr(resource='notSignedInText'))
                else:
                    if result is None:
                        ba.textwidget(edit=status_text,
                                      text=ba.Lstr(resource='errorText'))
                    else:
                        ba.textwidget(edit=status_text, text='')

            if result is not None:
                parties_in = result['l']
            else:
                parties_in = []

            for partyval in list(self._public_parties.values()):
                partyval['claimed'] = False

            for party_in in parties_in:
                # Party is indexed by (ADDR)_(PORT)
                party_key = party_in['a'] + '_' + str(party_in['p'])
                party = self._public_parties.get(party_key)
                if party is None:
                    # If this party is new to us, init it.
                    index = self._next_public_party_entry_index
                    self._next_public_party_entry_index = index + 1
                    party = self._public_parties[party_key] = {
                        'address':
                            party_in.get('a'),
                        'next_ping_time':
                            ba.time(ba.TimeType.REAL) + 0.001 * party_in['pd'],
                        'ping':
                            None,
                        'index':
                            index,
                    }

                # Now, new or not, update its values.
                party['queue'] = party_in.get('q')
                party['port'] = party_in.get('p')
                party['name'] = party_in['n']
                party['size'] = party_in['s']
                party['language'] = party_in['l']
                party['size_max'] = party_in['sm']
                party['claimed'] = True
                # (server provides this in milliseconds; we use seconds)
                party['ping_interval'] = 0.001 * party_in['pi']
                party['stats_addr'] = party_in['sa']

            # Prune unclaimed party entries.
            self._public_parties = {
                key: val
                for key, val in list(self._public_parties.items())
                if val['claimed']
            }

            self._rebuild_public_party_list()

    def _rebuild_public_party_list(self) -> None:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        cur_time = ba.time(ba.TimeType.REAL)
        if self._first_public_party_list_rebuild_time is None:
            self._first_public_party_list_rebuild_time = cur_time

        # Update faster for the first few seconds;
        # then ease off to keep the list from jumping around.
        since_first = cur_time - self._first_public_party_list_rebuild_time
        wait_time = (1.0 if since_first < 2.0 else
                     2.5 if since_first < 10.0 else 5.0)
        assert self._last_public_party_list_rebuild_time is not None
        if cur_time - self._last_public_party_list_rebuild_time < wait_time:
            return
        self._last_public_party_list_rebuild_time = cur_time

        # First off, check for the existence of our column widget;
        # if we don't have this, we're done.
        columnwidget = self._internet_host_columnwidget
        if not columnwidget:
            return

        with ba.Context('ui'):

            # Now kill and recreate all widgets.
            for widget in columnwidget.get_children():
                widget.delete()

            # Sort - show queue-enabled ones first and sort by lowest ping.
            ordered_parties = sorted(
                list(self._public_parties.values()),
                key=lambda p: (
                    p['queue'] is None,  # Show non-queued last.
                    p['ping'] if p['ping'] is not None else 999999,
                    p['index']))
            existing_selection = self._public_party_list_selection
            first = True

            sub_scroll_width = 830
            lineheight = 42
            sub_scroll_height = lineheight * len(ordered_parties) + 50
            ba.containerwidget(edit=columnwidget,
                               size=(sub_scroll_width, sub_scroll_height))

            # Ew; this rebuilding generates deferred selection callbacks
            # so we need to generated deferred ignore notices for ourself.
            def refresh_on() -> None:
                self._refreshing_public_party_list = True

            ba.pushcall(refresh_on)

            # Janky - allow escaping if there's nothing in us.
            ba.containerwidget(edit=self._internet_host_scrollwidget,
                               claims_up_down=(len(ordered_parties) > 0))

            for i, party in enumerate(ordered_parties):
                hpos = 20
                vpos = sub_scroll_height - lineheight * i - 50
                party['name_widget'] = ba.textwidget(
                    text=ba.Lstr(value=party['name']),
                    parent=columnwidget,
                    size=(sub_scroll_width * 0.63, 20),
                    position=(0 + hpos, 4 + vpos),
                    selectable=True,
                    on_select_call=ba.WeakCall(
                        self._set_public_party_selection,
                        (party['address'], 'name')),
                    on_activate_call=ba.WeakCall(
                        self._on_public_party_activate, party),
                    click_activate=True,
                    maxwidth=sub_scroll_width * 0.45,
                    corner_scale=1.4,
                    autoselect=True,
                    color=(1, 1, 1, 0.3 if party['ping'] is None else 1.0),
                    h_align='left',
                    v_align='center')
                ba.widget(edit=party['name_widget'],
                          left_widget=self._internet_join_text,
                          show_buffer_top=64.0,
                          show_buffer_bottom=64.0)
                if existing_selection == (party['address'], 'name'):
                    ba.containerwidget(edit=columnwidget,
                                       selected_child=party['name_widget'])
                if bool(False):
                    party['language_widget'] = ba.textwidget(
                        text=ba.Lstr(translate=('languages',
                                                party['language'])),
                        parent=columnwidget,
                        size=(0, 0),
                        position=(sub_scroll_width * 0.73 + hpos, 20 + vpos),
                        maxwidth=sub_scroll_width * 0.13,
                        scale=0.7,
                        color=(0.8, 0.8, 0.8),
                        h_align='center',
                        v_align='center')
                if party['stats_addr'] != '':
                    url = party['stats_addr'].replace(
                        '${ACCOUNT}',
                        _ba.get_account_misc_read_val_2(
                            'resolvedAccountID', 'UNKNOWN'))
                    party['stats_button'] = ba.buttonwidget(
                        color=(0.3, 0.6, 0.94),
                        textcolor=(1.0, 1.0, 1.0),
                        label=ba.Lstr(resource='statsText'),
                        parent=columnwidget,
                        autoselect=True,
                        on_activate_call=ba.Call(ba.open_url, url),
                        on_select_call=ba.WeakCall(
                            self._set_public_party_selection,
                            (party['address'], 'stats_button')),
                        size=(120, 40),
                        position=(sub_scroll_width * 0.66 + hpos, 1 + vpos),
                        scale=0.9)
                    if existing_selection == (party['address'],
                                              'stats_button'):
                        ba.containerwidget(
                            edit=columnwidget,
                            selected_child=party['stats_button'])
                else:
                    if 'stats_button' in party:
                        del party['stats_button']

                if first:
                    if 'stats_button' in party:
                        ba.widget(edit=party['stats_button'],
                                  up_widget=self._internet_join_text)
                    if 'name_widget' in party:
                        ba.widget(edit=party['name_widget'],
                                  up_widget=self._internet_join_text)
                    first = False

                party['size_widget'] = ba.textwidget(
                    text=str(party['size']) + '/' + str(party['size_max']),
                    parent=columnwidget,
                    size=(0, 0),
                    position=(sub_scroll_width * 0.86 + hpos, 20 + vpos),
                    scale=0.7,
                    color=(0.8, 0.8, 0.8),
                    h_align='right',
                    v_align='center')
                party['ping_widget'] = ba.textwidget(
                    parent=columnwidget,
                    size=(0, 0),
                    position=(sub_scroll_width * 0.94 + hpos, 20 + vpos),
                    scale=0.7,
                    h_align='right',
                    v_align='center')
                if party['ping'] is None:
                    ba.textwidget(edit=party['ping_widget'],
                                  text='-',
                                  color=(0.5, 0.5, 0.5))
                else:
                    ping_good = _ba.get_account_misc_read_val('pingGood', 100)
                    ping_med = _ba.get_account_misc_read_val('pingMed', 500)
                    ba.textwidget(edit=party['ping_widget'],
                                  text=str(party['ping']),
                                  color=(0, 1,
                                         0) if party['ping'] <= ping_good else
                                  (1, 1, 0) if party['ping'] <= ping_med else
                                  (1, 0, 0))

            # So our selection callbacks can start firing..
            def refresh_on2() -> None:
                self._refreshing_public_party_list = False

            ba.pushcall(refresh_on2)

    def _on_public_party_activate(self, party: Dict[str, Any]) -> None:
        from bastd.ui import purchase
        from bastd.ui import account
        if party['queue'] is not None:
            from bastd.ui import partyqueue
            ba.playsound(ba.getsound('swish'))
            partyqueue.PartyQueueWindow(party['queue'], party['address'],
                                        party['port'])
        else:
            address = party['address']
            port = party['port']
            if self._is_internet_locked():
                if _ba.get_account_state() != 'signed_in':
                    account.show_sign_in_prompt()
                else:
                    purchase.PurchaseWindow(items=['pro'])
                return
            # rate limit this a bit
            now = time.time()
            last_connect_time = self._last_public_party_connect_attempt_time
            if last_connect_time is None or now - last_connect_time > 2.0:
                _ba.connect_to_party(address, port=port)
                self._last_public_party_connect_attempt_time = now

    def _set_public_party_selection(self, sel: Tuple[str, str]) -> None:
        if self._refreshing_public_party_list:
            return
        self._public_party_list_selection = sel

    def _update_internet_tab(self) -> None:
        # pylint: disable=too-many-statements

        # Special case: if a party-queue window is up, don't do any of this
        # (keeps things smoother).
        if ba.app.ui.have_party_queue_window:
            return

        # If we've got a party-name text widget, keep its value plugged
        # into our public host name.
        text = self._internet_host_name_text
        if text:
            name = cast(str,
                        ba.textwidget(query=self._internet_host_name_text))
            _ba.set_public_party_name(name)

        # Show/hide the lock icon depending on if we've got pro.
        icon = self._internet_lock_icon
        if icon:
            if self._is_internet_locked():
                ba.imagewidget(edit=icon, opacity=0.5)
            else:
                ba.imagewidget(edit=icon, opacity=0.0)

        if self._internet_tab == 'join':
            now = ba.time(ba.TimeType.REAL)
            if (now - self._internet_join_last_refresh_time > 0.001 *
                    _ba.get_account_misc_read_val('pubPartyRefreshMS', 10000)):
                self._internet_join_last_refresh_time = now
                app = ba.app
                _ba.add_transaction(
                    {
                        'type': 'PUBLIC_PARTY_QUERY',
                        'proto': app.protocol_version,
                        'lang': app.language
                    },
                    callback=ba.WeakCall(self._on_public_party_query_result))
                _ba.run_transactions()

            # Go through our existing public party entries firing off pings
            # for any that have timed out.
            for party in list(self._public_parties.values()):
                if (party['next_ping_time'] <= now
                        and ba.app.ping_thread_count < 15):

                    # Make sure to fully catch up and not to multi-ping if
                    # we're way behind somehow.
                    while party['next_ping_time'] <= now:
                        # Crank the interval up for high-latency parties to
                        # save us some work.
                        mult = 1
                        if party['ping'] is not None:
                            mult = (10 if party['ping'] > 300 else
                                    5 if party['ping'] > 150 else 2)
                        party[
                            'next_ping_time'] += party['ping_interval'] * mult

                    class PingThread(threading.Thread):
                        """Thread for sending out pings."""

                        def __init__(self, address: str, port: int,
                                     call: Callable[[str, int, Optional[int]],
                                                    Optional[int]]):
                            super().__init__()
                            self._address = address
                            self._port = port
                            self._call = call

                        def run(self) -> None:
                            # pylint: disable=too-many-branches
                            ba.app.ping_thread_count += 1
                            try:
                                import socket
                                from ba.internal import get_ip_address_type
                                socket_type = get_ip_address_type(
                                    self._address)
                                sock = socket.socket(socket_type,
                                                     socket.SOCK_DGRAM)
                                sock.connect((self._address, self._port))

                                accessible = False
                                starttime = time.time()

                                # Send a few pings and wait a second for
                                # a response.
                                sock.settimeout(1)
                                for _i in range(3):
                                    sock.send(b'\x0b')
                                    result: Optional[bytes]
                                    try:
                                        # 11: BA_PACKET_SIMPLE_PING
                                        result = sock.recv(10)
                                    except Exception:
                                        result = None
                                    if result == b'\x0c':
                                        # 12: BA_PACKET_SIMPLE_PONG
                                        accessible = True
                                        break
                                    time.sleep(1)
                                sock.close()
                                ping = int((time.time() - starttime) * 1000.0)
                                ba.pushcall(ba.Call(
                                    self._call, self._address, self._port,
                                    ping if accessible else None),
                                            from_other_thread=True)
                            except ConnectionRefusedError:
                                # Fine, server; sorry we pinged you. Hmph.
                                pass
                            except OSError as exc:
                                import errno

                                # Ignore harmless errors.
                                if exc.errno in {
                                        errno.EHOSTUNREACH, errno.ENETUNREACH,
                                        errno.EINVAL, errno.EPERM
                                }:
                                    pass
                                elif exc.errno == 10022:
                                    # Windows 'invalid argument' error.
                                    pass
                                elif exc.errno == 10051:
                                    # Windows 'a socket operation was attempted
                                    # to an unreachable network' error.
                                    pass
                                elif exc.errno == errno.EADDRNOTAVAIL:
                                    if self._port == 0:
                                        # This has happened. Ignore.
                                        pass
                                    elif ba.do_once():
                                        print(
                                            f'Got EADDRNOTAVAIL on gather ping'
                                            f' for addr {self._address}'
                                            f' port {self._port}.')
                                else:
                                    ba.print_exception(
                                        f'Error on gather ping '
                                        f'(errno={exc.errno})',
                                        once=True)
                            except Exception:
                                ba.print_exception('Error on gather ping',
                                                   once=True)
                            ba.app.ping_thread_count -= 1

                    PingThread(party['address'], party['port'],
                               ba.WeakCall(self._ping_callback)).start()

    def _ping_callback(self, address: str, port: Optional[int],
                       result: Optional[int]) -> None:
        # Look for a widget corresponding to this target.
        # If we find one, update our list.
        party = self._public_parties.get(address + '_' + str(port))
        if party is not None:
            # We now smooth ping a bit to reduce jumping around in the list
            # (only where pings are relatively good).
            current_ping = party.get('ping')
            if (current_ping is not None and result is not None
                    and result < 150):
                smoothing = 0.7
                party['ping'] = int(smoothing * current_ping +
                                    (1.0 - smoothing) * result)
            else:
                party['ping'] = result

            # This can happen if we switch away and then back to the
            # client tab while pings are in flight.
            if 'ping_widget' not in party:
                pass
            elif party['ping_widget']:
                self._rebuild_public_party_list()

    def _do_internet_status_check(self) -> None:
        from ba.internal import master_server_get
        ba.textwidget(edit=self._internet_host_status_text,
                      color=(1, 1, 0),
                      text=ba.Lstr(resource=self._r +
                                   '.partyStatusCheckingText'))
        master_server_get('bsAccessCheck', {'b': ba.app.build_number},
                          callback=ba.WeakCall(
                              self._on_public_party_accessible_response))

    def _on_start_internet_advertizing_press(self) -> None:
        from bastd.ui import account
        from bastd.ui import purchase
        if _ba.get_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return

        # Requires sign-in and pro.
        if self._is_internet_locked():
            if _ba.get_account_state() != 'signed_in':
                account.show_sign_in_prompt()
            else:
                purchase.PurchaseWindow(items=['pro'])
            return

        name = cast(str, ba.textwidget(query=self._internet_host_name_text))
        if name == '':
            ba.screenmessage(ba.Lstr(resource='internal.invalidNameErrorText'),
                             color=(1, 0, 0))
            ba.playsound(ba.getsound('error'))
            return
        _ba.set_public_party_name(name)
        cfg = ba.app.config
        cfg['Public Party Name'] = name
        cfg.commit()
        ba.playsound(ba.getsound('shieldUp'))
        _ba.set_public_party_enabled(True)

        # In GUI builds we want to authenticate clients only when hosting
        # public parties.
        _ba.set_authenticate_clients(True)

        self._do_internet_status_check()
        ba.buttonwidget(
            edit=self._internet_host_toggle_button,
            label=ba.Lstr(
                resource='gatherWindow.makePartyPrivateText',
                fallback_resource='gatherWindow.stopAdvertisingText'),
            on_activate_call=self._on_stop_internet_advertising_press)

    def _on_public_party_accessible_response(
            self, data: Optional[Dict[str, Any]]) -> None:
        # If we've got status text widgets, update them.
        text = self._internet_host_status_text
        if text:
            if data is None:
                ba.textwidget(
                    edit=text,
                    text=ba.Lstr(resource=self._r +
                                 '.partyStatusNoConnectionText'),
                    color=(1, 0, 0),
                )
            else:
                if not data.get('accessible', False):
                    ex_line: Union[str, ba.Lstr]
                    if self._internet_local_address is not None:
                        ex_line = ba.Lstr(
                            value='\n${A} ${B}',
                            subs=[('${A}',
                                   ba.Lstr(resource=self._r +
                                           '.manualYourLocalAddressText')),
                                  ('${B}', self._internet_local_address)])
                    else:
                        ex_line = ''
                    ba.textwidget(
                        edit=text,
                        text=ba.Lstr(
                            value='${A}\n${B}${C}',
                            subs=[('${A}',
                                   ba.Lstr(resource=self._r +
                                           '.partyStatusNotJoinableText')),
                                  ('${B}',
                                   ba.Lstr(resource=self._r +
                                           '.manualRouterForwardingText',
                                           subs=[('${PORT}',
                                                  str(_ba.get_game_port()))])),
                                  ('${C}', ex_line)]),
                        color=(1, 0, 0))
                else:
                    ba.textwidget(edit=text,
                                  text=ba.Lstr(resource=self._r +
                                               '.partyStatusJoinableText'),
                                  color=(0, 1, 0))

    def _on_stop_internet_advertising_press(self) -> None:
        _ba.set_public_party_enabled(False)

        # In GUI builds we want to authenticate clients only when hosting
        # public parties.
        _ba.set_authenticate_clients(False)

        ba.playsound(ba.getsound('shieldDown'))
        text = self._internet_host_status_text
        if text:
            ba.textwidget(
                edit=text,
                text=ba.Lstr(resource=self._r + '.partyStatusNotPublicText'),
                color=(0.6, 0.6, 0.6),
            )

        ba.buttonwidget(
            edit=self._internet_host_toggle_button,
            label=ba.Lstr(
                resource='gatherWindow.makePartyPublicText',
                fallback_resource='gatherWindow.startAdvertisingText'),
            on_activate_call=self._on_start_internet_advertizing_press)

    def _access_check_update(self, t_addr: ba.Widget, t_accessible: ba.Widget,
                             t_accessible_extra: ba.Widget) -> None:
        from ba.internal import master_server_get

        # If we don't have an outstanding query, start one..
        assert self._doing_access_check is not None
        assert self._access_check_count is not None
        if not self._doing_access_check and self._access_check_count < 100:
            self._doing_access_check = True
            self._access_check_count += 1
            self._t_addr = t_addr
            self._t_accessible = t_accessible
            self._t_accessible_extra = t_accessible_extra
            master_server_get('bsAccessCheck', {'b': ba.app.build_number},
                              callback=ba.WeakCall(
                                  self._on_accessible_response))

    def _on_accessible_response(self, data: Optional[Dict[str, Any]]) -> None:
        t_addr = self._t_addr
        t_accessible = self._t_accessible
        t_accessible_extra = self._t_accessible_extra
        self._doing_access_check = False
        color_bad = (1, 1, 0)
        color_good = (0, 1, 0)
        if data is None or 'address' not in data or 'accessible' not in data:
            if t_addr:
                ba.textwidget(edit=t_addr,
                              text=ba.Lstr(resource=self._r +
                                           '.noConnectionText'),
                              color=color_bad)
            if t_accessible:
                ba.textwidget(edit=t_accessible,
                              text=ba.Lstr(resource=self._r +
                                           '.noConnectionText'),
                              color=color_bad)
            if t_accessible_extra:
                ba.textwidget(edit=t_accessible_extra,
                              text='',
                              color=color_bad)
            return
        if t_addr:
            ba.textwidget(edit=t_addr, text=data['address'], color=color_good)
        if t_accessible:
            if data['accessible']:
                ba.textwidget(edit=t_accessible,
                              text=ba.Lstr(resource=self._r +
                                           '.manualJoinableYesText'),
                              color=color_good)
                if t_accessible_extra:
                    ba.textwidget(edit=t_accessible_extra,
                                  text='',
                                  color=color_good)
            else:
                ba.textwidget(
                    edit=t_accessible,
                    text=ba.Lstr(resource=self._r +
                                 '.manualJoinableNoWithAsteriskText'),
                    color=color_bad)
                if t_accessible_extra:
                    ba.textwidget(edit=t_accessible_extra,
                                  text=ba.Lstr(resource=self._r +
                                               '.manualRouterForwardingText',
                                               subs=[('${PORT}',
                                                      str(_ba.get_game_port()))
                                                     ]),
                                  color=color_bad)

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._back_button:
                sel_name = 'Back'
            elif sel in list(self._tab_buttons.values()):
                sel_name = 'Tab:' + list(self._tab_buttons.keys())[list(
                    self._tab_buttons.values()).index(sel)]
            elif sel == self._tab_container:
                sel_name = 'TabContainer'
            else:
                raise ValueError(f'unrecognized selection: \'{sel}\'')
            ba.app.ui.window_states[self.__class__.__name__] = {
                'sel_name': sel_name,
                'tab': self._current_tab,
                'internet_tab': self._internet_tab
            }
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        try:
            winstate = ba.app.ui.window_states.get(self.__class__.__name__, {})
            sel_name = winstate.get('sel_name', None)
            self._internet_tab = winstate.get('internet_tab', 'join')
            current_tab = ba.app.config.get('Gather Tab', None)
            if current_tab is None or current_tab not in self._tab_buttons:
                current_tab = 'about'
            self._set_tab(current_tab)
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'TabContainer':
                sel = self._tab_container
            elif isinstance(sel_name, str) and sel_name.startswith('Tab:'):
                sel = self._tab_buttons[sel_name.split(':')[-1]]
            else:
                sel = self._tab_buttons[current_tab]
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')

    def _back(self) -> None:
        from bastd.ui.mainmenu import MainMenuWindow
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            MainMenuWindow(transition='in_left').get_root_widget())
