# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Defines the public tab in the gather UI."""

from __future__ import annotations

import time
import threading
from typing import TYPE_CHECKING, cast

import _ba
import ba
from bastd.ui.gather.bases import GatherTab

if TYPE_CHECKING:
    from typing import Callable, Any, Optional, Dict, Union, Tuple
    from bastd.ui.gather import GatherWindow


class PublicGatherTab(GatherTab):
    """The public tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._container: Optional[ba.Widget] = None
        self._internet_join_text: Optional[ba.Widget] = None
        self._internet_host_text: Optional[ba.Widget] = None
        self._internet_local_address: Optional[str] = None
        self._last_public_party_connect_attempt_time: Optional[float] = None
        self._internet_tab: Optional[str] = None
        self._public_party_list_selection: Optional[Tuple[str, str]] = None
        self._refreshing_public_party_list: Optional[bool] = None
        self._update_timer: Optional[ba.Timer] = None
        self._internet_host_scrollwidget: Optional[ba.Widget] = None
        self._internet_host_name_text: Optional[ba.Widget] = None
        self._internet_host_toggle_button: Optional[ba.Widget] = None
        self._internet_join_last_refresh_time = -99999.0
        self._internet_join_party_name_label: Optional[ba.Widget] = None
        self._internet_join_party_language_label: Optional[ba.Widget] = None
        self._internet_join_party_size_label: Optional[ba.Widget] = None
        self._internet_join_party_ping_label: Optional[ba.Widget] = None
        self._internet_host_columnwidget: Optional[ba.Widget] = None
        self._internet_join_status_text: Optional[ba.Widget] = None
        self._internet_host_name_label_text: Optional[ba.Widget] = None
        self._internet_host_max_party_size_label: Optional[ba.Widget] = None
        self._internet_host_max_party_size_value: Optional[ba.Widget] = None
        self._internet_host_max_party_size_minus_button: (
            Optional[ba.Widget]) = None
        self._internet_host_max_party_size_plus_button: (
            Optional[ba.Widget]) = None
        self._internet_host_status_text: Optional[ba.Widget] = None
        self._internet_host_dedicated_server_info_text: (
            Optional[ba.Widget]) = None
        self._internet_lock_icon: Optional[ba.Widget] = None
        self._public_parties: Dict[str, Dict[str, Any]] = {}
        self._last_public_party_list_rebuild_time: Optional[float] = None
        self._first_public_party_list_rebuild_time: Optional[float] = None
        self._next_public_party_entry_index = 0

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> ba.Widget:
        c_width = region_width
        c_height = region_height - 20
        self._container = ba.containerwidget(
            parent=parent_widget,
            position=(region_left,
                      region_bottom + (region_height - c_height) * 0.5),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True)
        v = c_height - 30
        self._internet_join_text = txt = ba.textwidget(
            parent=self._container,
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
            on_activate_call=lambda: self._set_internet_tab('join',
                                                            region_width,
                                                            region_height,
                                                            region_left,
                                                            region_bottom,
                                                            playsound=True),
            text=ba.Lstr(resource='gatherWindow.'
                         'joinPublicPartyDescriptionText'))
        ba.widget(edit=txt, up_widget=tab_button)
        self._internet_host_text = txt = ba.textwidget(
            parent=self._container,
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
            on_activate_call=lambda: self._set_internet_tab('host',
                                                            region_width,
                                                            region_height,
                                                            region_left,
                                                            region_bottom,
                                                            playsound=True),
            text=ba.Lstr(resource='gatherWindow.'
                         'hostPublicPartyDescriptionText'))
        ba.widget(edit=txt,
                  left_widget=self._internet_join_text,
                  up_widget=tab_button)
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
        self._set_internet_tab(self._internet_tab, region_width, region_height,
                               region_left, region_bottom)
        self._update_timer = ba.Timer(0.2,
                                      ba.WeakCall(self._update_internet_tab),
                                      repeat=True,
                                      timetype=ba.TimeType.REAL)

        # Also update it immediately so we don't have to wait for the
        # initial query.
        self._update_internet_tab()
        return self._container

    def on_deactivate(self) -> None:
        self._update_timer = None

    def save_state(self) -> None:
        ba.app.ui.window_states[self.__class__.__name__] = {
            'internet_tab': self._internet_tab
        }

    def restore_state(self) -> None:
        winstate = ba.app.ui.window_states.get(self.__class__.__name__, {})
        self._internet_tab = winstate.get('internet_tab', 'join')

    def _set_internet_tab(self,
                          value: str,
                          region_width: float,
                          region_height: float,
                          region_left: float,
                          region_bottom: float,
                          playsound: bool = False) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        assert self._container
        del region_left, region_bottom  # Unused
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

        c_width = region_width
        c_height = region_height - 20
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
                parent=self._container,
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
                    parent=self._container,
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
                text=ba.Lstr(resource='gatherWindow.'
                             'partySizeText'),
                parent=self._container,
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
                text=ba.Lstr(resource='gatherWindow.'
                             'pingText'),
                parent=self._container,
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
                parent=self._container,
                simple_culling_v=10,
                position=((region_width - sub_scroll_width) * 0.5, v),
                size=(sub_scroll_width, sub_scroll_height))
            ba.widget(edit=scrollw, autoselect=True)
            colw = self._internet_host_columnwidget = ba.containerwidget(
                parent=scrollw, background=False, size=(400, 400))
            ba.containerwidget(edit=scrollw, claims_left_right=True)
            ba.containerwidget(edit=colw, claims_left_right=True)

            self._internet_join_status_text = ba.textwidget(
                parent=self._container,
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
                parent=self._container,
                size=(0, 0),
                h_align='right',
                v_align='center',
                maxwidth=200,
                scale=0.8,
                color=ba.app.ui.infotextcolor,
                position=(210, v - 9),
                text=party_name_text)
            self._internet_host_name_text = ba.textwidget(
                parent=self._container,
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
                parent=self._container,
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
                parent=self._container,
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=1.2,
                color=(1, 1, 1),
                position=(240, v - 9),
                text=str(_ba.get_public_party_max_size()))
            btn1 = self._internet_host_max_party_size_minus_button = (
                ba.buttonwidget(
                    parent=self._container,
                    size=(40, 40),
                    on_activate_call=ba.WeakCall(
                        self._on_max_public_party_size_minus_press),
                    position=(280, v - 26),
                    label='-',
                    autoselect=True))
            btn2 = self._internet_host_max_party_size_plus_button = (
                ba.buttonwidget(parent=self._container,
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
                parent=self._container,
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
                parent=self._container,
                text=ba.Lstr(resource='gatherWindow.'
                             'partyStatusNotPublicText'),
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
                parent=self._container,
                text=ba.Lstr(resource='gatherWindow.'
                             'dedicatedServerInfoText'),
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
            parent=self._container,
            position=(c_width * 0.5 - 60, c_height * 0.5 - 50),
            size=(120, 120),
            opacity=0.0 if not self._is_internet_locked() else 0.5,
            texture=ba.gettexture('lock'))

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
                        'lang': app.lang.language
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
                                        errno.EINVAL, errno.EPERM, errno.EACCES
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

    def _internet_fetch_local_addr_cb(self, val: str) -> None:
        self._internet_local_address = str(val)

    def _on_public_party_accessible_response(
            self, data: Optional[Dict[str, Any]]) -> None:

        # If we've got status text widgets, update them.
        text = self._internet_host_status_text
        if text:
            if data is None:
                ba.textwidget(
                    edit=text,
                    text=ba.Lstr(resource='gatherWindow.'
                                 'partyStatusNoConnectionText'),
                    color=(1, 0, 0),
                )
            else:
                if not data.get('accessible', False):
                    ex_line: Union[str, ba.Lstr]
                    if self._internet_local_address is not None:
                        ex_line = ba.Lstr(
                            value='\n${A} ${B}',
                            subs=[('${A}',
                                   ba.Lstr(resource='gatherWindow.'
                                           'manualYourLocalAddressText')),
                                  ('${B}', self._internet_local_address)])
                    else:
                        ex_line = ''
                    ba.textwidget(
                        edit=text,
                        text=ba.Lstr(
                            value='${A}\n${B}${C}',
                            subs=[('${A}',
                                   ba.Lstr(resource='gatherWindow.'
                                           'partyStatusNotJoinableText')),
                                  ('${B}',
                                   ba.Lstr(resource='gatherWindow.'
                                           'manualRouterForwardingText',
                                           subs=[('${PORT}',
                                                  str(_ba.get_game_port()))])),
                                  ('${C}', ex_line)]),
                        color=(1, 0, 0))
                else:
                    ba.textwidget(edit=text,
                                  text=ba.Lstr(resource='gatherWindow.'
                                               'partyStatusJoinableText'),
                                  color=(0, 1, 0))

    def _do_internet_status_check(self) -> None:
        from ba.internal import master_server_get
        ba.textwidget(edit=self._internet_host_status_text,
                      color=(1, 1, 0),
                      text=ba.Lstr(resource='gatherWindow.'
                                   'partyStatusCheckingText'))
        master_server_get('bsAccessCheck', {'b': ba.app.build_number},
                          callback=ba.WeakCall(
                              self._on_public_party_accessible_response))

    def _on_start_internet_advertizing_press(self) -> None:
        from bastd.ui.account import show_sign_in_prompt
        from bastd.ui.purchase import PurchaseWindow
        if _ba.get_account_state() != 'signed_in':
            show_sign_in_prompt()
            return

        # Requires sign-in and pro.
        if self._is_internet_locked():
            if _ba.get_account_state() != 'signed_in':
                show_sign_in_prompt()
            else:
                PurchaseWindow(items=['pro'])
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
                text=ba.Lstr(resource='gatherWindow.'
                             'partyStatusNotPublicText'),
                color=(0.6, 0.6, 0.6),
            )
        ba.buttonwidget(
            edit=self._internet_host_toggle_button,
            label=ba.Lstr(
                resource='gatherWindow.makePartyPublicText',
                fallback_resource='gatherWindow.startAdvertisingText'),
            on_activate_call=self._on_start_internet_advertizing_press)

    def _is_internet_locked(self) -> bool:
        if _ba.get_account_misc_read_val('ilck', False):
            return not ba.app.accounts.have_pro()
        return False

    def _on_public_party_activate(self, party: Dict[str, Any]) -> None:
        from bastd.ui.purchase import PurchaseWindow
        from bastd.ui.account import show_sign_in_prompt
        if party['queue'] is not None:
            from bastd.ui.partyqueue import PartyQueueWindow
            ba.playsound(ba.getsound('swish'))
            PartyQueueWindow(party['queue'], party['address'], party['port'])
        else:
            address = party['address']
            port = party['port']
            if self._is_internet_locked():
                if _ba.get_account_state() != 'signed_in':
                    show_sign_in_prompt()
                else:
                    PurchaseWindow(items=['pro'])
                return

            # Rate limit this a bit.
            now = time.time()
            last_connect_time = self._last_public_party_connect_attempt_time
            if last_connect_time is None or now - last_connect_time > 2.0:
                _ba.connect_to_party(address, port=port)
                self._last_public_party_connect_attempt_time = now

    def _set_public_party_selection(self, sel: Tuple[str, str]) -> None:
        if self._refreshing_public_party_list:
            return
        self._public_party_list_selection = sel

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
