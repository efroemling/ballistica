# Released under the MIT License. See LICENSE for details.
#
"""Defines the public tab in the gather UI."""

from __future__ import annotations

import time
import threading
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import _ba
import ba
from bastd.ui.gather.bases import GatherTab

if TYPE_CHECKING:
    from typing import Callable, Any, Optional, Dict, Union, Tuple
    from bastd.ui.gather import GatherWindow


class SubTabType(Enum):
    """Available sub-tabs."""
    JOIN = 'join'
    HOST = 'host'


@dataclass
class TabState:
    """State saved/restored only while the app is running."""
    sub_tab: SubTabType = SubTabType.JOIN


@dataclass
class PartyEntry:
    """Info about a party."""
    address: str
    next_ping_time: float
    ping: Optional[int]
    index: int
    queue: Optional[str] = None
    port: int = -1
    name: str = ''
    size: int = -1
    size_max: int = -1
    claimed: bool = False
    ping_interval: float = -1.0
    stats_addr: Optional[str] = None
    name_widget: Optional[ba.Widget] = None
    ping_widget: Optional[ba.Widget] = None
    stats_button: Optional[ba.Widget] = None
    size_widget: Optional[ba.Widget] = None


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
            ba.pushcall(ba.Call(self._call, val), from_other_thread=True)
        except Exception as exc:
            # Ignore expected network errors; log others.
            import errno
            if isinstance(exc, OSError) and exc.errno == errno.ENETUNREACH:
                pass
            else:
                ba.print_exception()


class PublicGatherTab(GatherTab):
    """The public tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._container: Optional[ba.Widget] = None
        self._join_text: Optional[ba.Widget] = None
        self._host_text: Optional[ba.Widget] = None
        self._local_address: Optional[str] = None
        self._last_public_party_connect_attempt_time: Optional[float] = None
        self._sub_tab: SubTabType = SubTabType.JOIN
        self._public_party_list_selection: Optional[Tuple[str, str]] = None
        self._refreshing_public_party_list: Optional[bool] = None
        self._update_timer: Optional[ba.Timer] = None
        self._host_scrollwidget: Optional[ba.Widget] = None
        self._host_name_text: Optional[ba.Widget] = None
        self._host_toggle_button: Optional[ba.Widget] = None
        self._join_last_refresh_time = -99999.0
        self._host_columnwidget: Optional[ba.Widget] = None
        self._join_status_text: Optional[ba.Widget] = None
        self._host_max_party_size_value: Optional[ba.Widget] = None
        self._host_max_party_size_minus_button: (Optional[ba.Widget]) = None
        self._host_max_party_size_plus_button: (Optional[ba.Widget]) = None
        self._host_status_text: Optional[ba.Widget] = None
        self._public_parties: Dict[str, PartyEntry] = {}
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
        self._join_text = ba.textwidget(
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
            on_activate_call=lambda: self._set_sub_tab(SubTabType.JOIN,
                                                       region_width,
                                                       region_height,
                                                       region_left,
                                                       region_bottom,
                                                       playsound=True),
            text=ba.Lstr(resource='gatherWindow.'
                         'joinPublicPartyDescriptionText'))
        self._host_text = ba.textwidget(
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
            on_activate_call=lambda: self._set_sub_tab(SubTabType.HOST,
                                                       region_width,
                                                       region_height,
                                                       region_left,
                                                       region_bottom,
                                                       playsound=True),
            text=ba.Lstr(resource='gatherWindow.'
                         'hostPublicPartyDescriptionText'))
        ba.widget(edit=self._join_text, up_widget=tab_button)
        ba.widget(edit=self._host_text,
                  left_widget=self._join_text,
                  up_widget=tab_button)
        ba.widget(edit=self._join_text, right_widget=self._host_text)

        # Attempt to fetch our local address so we have it for
        # error messages.
        self._local_address = None

        AddrFetchThread(ba.WeakCall(self._fetch_local_addr_cb)).start()

        assert self._sub_tab is not None
        self._set_sub_tab(self._sub_tab, region_width, region_height,
                          region_left, region_bottom)
        self._update_timer = ba.Timer(0.2,
                                      ba.WeakCall(self._update_sub_tab),
                                      repeat=True,
                                      timetype=ba.TimeType.REAL)

        # Also update it immediately so we don't have to wait for the
        # initial query.
        self._update_sub_tab()
        return self._container

    def on_deactivate(self) -> None:
        self._update_timer = None

    def save_state(self) -> None:
        ba.app.ui.window_states[self.__class__.__name__] = TabState(
            sub_tab=self._sub_tab)

    def restore_state(self) -> None:
        state = ba.app.ui.window_states.get(self.__class__.__name__)
        if state is None:
            state = TabState()
        assert isinstance(state, TabState)
        self._sub_tab = state.sub_tab

    def _set_sub_tab(self,
                     value: SubTabType,
                     region_width: float,
                     region_height: float,
                     region_left: float,
                     region_bottom: float,
                     playsound: bool = False) -> None:
        assert self._container
        del region_left, region_bottom  # Unused
        if playsound:
            ba.playsound(ba.getsound('click01'))

        # If we're switching in from elsewhere, reset our selection.
        # (prevents selecting something way down the list if we switched away
        # and came back)
        if self._sub_tab != value:
            self._public_party_list_selection = None

        self._sub_tab = value
        active_color = (0.6, 1.0, 0.6)
        inactive_color = (0.5, 0.4, 0.5)
        ba.textwidget(
            edit=self._join_text,
            color=active_color if value is SubTabType.JOIN else inactive_color)
        ba.textwidget(
            edit=self._host_text,
            color=active_color if value is SubTabType.HOST else inactive_color)

        # Clear anything in existence in our sub-tabs.
        for widget in self._container.get_children():
            if widget and widget not in {self._host_text, self._join_text}:
                widget.delete()

        c_width = region_width
        c_height = region_height - 20
        sub_scroll_height = c_height - 90
        sub_scroll_width = 830
        v = c_height - 35
        v -= 25
        if value is SubTabType.JOIN:
            self._build_join_tab(v, sub_scroll_width, sub_scroll_height,
                                 c_width, c_height)

        if value is SubTabType.HOST:
            self._build_host_tab(v, sub_scroll_width, sub_scroll_height,
                                 c_width, c_height)

    def _build_join_tab(self, v: float, sub_scroll_width: float,
                        sub_scroll_height: float, c_width: float,
                        c_height: float) -> None:
        # Reset this so we do an immediate refresh query.
        self._join_last_refresh_time = -99999.0

        # Reset our list of public parties.
        self._public_parties = {}
        self._last_public_party_list_rebuild_time = 0
        self._first_public_party_list_rebuild_time = None
        ba.textwidget(text=ba.Lstr(resource='nameText'),
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
        ba.textwidget(text=ba.Lstr(resource='gatherWindow.'
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
        ba.textwidget(text=ba.Lstr(resource='gatherWindow.'
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

        self._host_scrollwidget = scrollw = ba.scrollwidget(
            parent=self._container,
            simple_culling_v=10,
            position=((c_width - sub_scroll_width) * 0.5, v),
            size=(sub_scroll_width, sub_scroll_height))
        ba.widget(edit=scrollw, autoselect=True)
        colw = self._host_columnwidget = ba.containerwidget(parent=scrollw,
                                                            background=False,
                                                            size=(400, 400))
        ba.containerwidget(edit=scrollw, claims_left_right=True)
        ba.containerwidget(edit=colw, claims_left_right=True)

        self._join_status_text = ba.textwidget(
            parent=self._container,
            text=ba.Lstr(
                value='${A}...',
                subs=[('${A}', ba.Lstr(resource='store.loadingText'))],
            ),
            size=(0, 0),
            scale=0.9,
            flatness=1.0,
            shadow=0.0,
            h_align='center',
            v_align='top',
            maxwidth=c_width,
            color=(0.6, 0.6, 0.6),
            position=(c_width * 0.5, c_height * 0.5))

    def _build_host_tab(self, v: float, sub_scroll_width: float,
                        sub_scroll_height: float, c_width: float,
                        c_height: float) -> None:
        del sub_scroll_width, sub_scroll_height, c_height  # Unused.
        is_public_enabled = _ba.get_public_party_enabled()
        v -= 30
        party_name_text = ba.Lstr(
            resource='gatherWindow.partyNameText',
            fallback_resource='editGameListWindow.nameText')
        ba.textwidget(parent=self._container,
                      size=(0, 0),
                      h_align='right',
                      v_align='center',
                      maxwidth=200,
                      scale=0.8,
                      color=ba.app.ui.infotextcolor,
                      position=(210, v - 9),
                      text=party_name_text)
        self._host_name_text = ba.textwidget(parent=self._container,
                                             editable=True,
                                             size=(535, 40),
                                             position=(230, v - 30),
                                             text=ba.app.config.get(
                                                 'Public Party Name', ''),
                                             maxwidth=494,
                                             shadow=0.3,
                                             flatness=1.0,
                                             description=party_name_text,
                                             autoselect=True,
                                             v_align='center',
                                             corner_scale=1.0)

        v -= 60
        ba.textwidget(parent=self._container,
                      size=(0, 0),
                      h_align='right',
                      v_align='center',
                      maxwidth=200,
                      scale=0.8,
                      color=ba.app.ui.infotextcolor,
                      position=(210, v - 9),
                      text=ba.Lstr(resource='maxPartySizeText',
                                   fallback_resource='maxConnectionsText'))
        self._host_max_party_size_value = ba.textwidget(
            parent=self._container,
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=1.2,
            color=(1, 1, 1),
            position=(240, v - 9),
            text=str(_ba.get_public_party_max_size()))
        btn1 = self._host_max_party_size_minus_button = (ba.buttonwidget(
            parent=self._container,
            size=(40, 40),
            on_activate_call=ba.WeakCall(
                self._on_max_public_party_size_minus_press),
            position=(280, v - 26),
            label='-',
            autoselect=True))
        btn2 = self._host_max_party_size_plus_button = (ba.buttonwidget(
            parent=self._container,
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
        self._host_toggle_button = ba.buttonwidget(
            parent=self._container,
            label=label,
            size=(400, 80),
            on_activate_call=self._on_stop_advertising_press
            if is_public_enabled else self._on_start_advertizing_press,
            position=(c_width * 0.5 - 200, v),
            autoselect=True,
            up_widget=btn2)
        ba.widget(edit=self._host_name_text, down_widget=btn2)
        ba.widget(edit=btn2, up_widget=self._host_name_text)
        ba.widget(edit=btn1, up_widget=self._host_name_text)
        ba.widget(edit=self._join_text, down_widget=self._host_name_text)
        v -= 10
        self._host_status_text = ba.textwidget(
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
        ba.textwidget(parent=self._container,
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
            self._do_status_check()

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
        columnwidget = self._host_columnwidget
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
                    p.queue is None,  # Show non-queued last.
                    p.ping if p.ping is not None else 999999,
                    p.index))
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
            ba.containerwidget(edit=self._host_scrollwidget,
                               claims_up_down=(len(ordered_parties) > 0))

            for i, party in enumerate(ordered_parties):
                hpos = 20
                vpos = sub_scroll_height - lineheight * i - 50
                party.name_widget = ba.textwidget(
                    text=ba.Lstr(value=party.name),
                    parent=columnwidget,
                    size=(sub_scroll_width * 0.63, 20),
                    position=(0 + hpos, 4 + vpos),
                    selectable=True,
                    on_select_call=ba.WeakCall(
                        self._set_public_party_selection,
                        (party.address, 'name')),
                    on_activate_call=ba.WeakCall(
                        self._on_public_party_activate, party),
                    click_activate=True,
                    maxwidth=sub_scroll_width * 0.45,
                    corner_scale=1.4,
                    autoselect=True,
                    color=(1, 1, 1, 0.3 if party.ping is None else 1.0),
                    h_align='left',
                    v_align='center')
                ba.widget(edit=party.name_widget,
                          left_widget=self._join_text,
                          show_buffer_top=64.0,
                          show_buffer_bottom=64.0)
                if existing_selection == (party.address, 'name'):
                    ba.containerwidget(edit=columnwidget,
                                       selected_child=party.name_widget)
                if party.stats_addr:
                    url = party.stats_addr.replace(
                        '${ACCOUNT}',
                        _ba.get_account_misc_read_val_2(
                            'resolvedAccountID', 'UNKNOWN'))
                    party.stats_button = ba.buttonwidget(
                        color=(0.3, 0.6, 0.94),
                        textcolor=(1.0, 1.0, 1.0),
                        label=ba.Lstr(resource='statsText'),
                        parent=columnwidget,
                        autoselect=True,
                        on_activate_call=ba.Call(ba.open_url, url),
                        on_select_call=ba.WeakCall(
                            self._set_public_party_selection,
                            (party.address, 'stats_button')),
                        size=(120, 40),
                        position=(sub_scroll_width * 0.66 + hpos, 1 + vpos),
                        scale=0.9)
                    if existing_selection == (party.address, 'stats_button'):
                        ba.containerwidget(edit=columnwidget,
                                           selected_child=party.stats_button)
                else:
                    if party.stats_button:
                        party.stats_button.delete()
                        party.stats_button = None

                if first:
                    if party.stats_button:
                        ba.widget(edit=party.stats_button,
                                  up_widget=self._join_text)
                    if party.name_widget:
                        ba.widget(edit=party.name_widget,
                                  up_widget=self._join_text)
                    first = False

                party.size_widget = ba.textwidget(
                    text=str(party.size) + '/' + str(party.size_max),
                    parent=columnwidget,
                    size=(0, 0),
                    position=(sub_scroll_width * 0.86 + hpos, 20 + vpos),
                    scale=0.7,
                    color=(0.8, 0.8, 0.8),
                    h_align='right',
                    v_align='center')
                party.ping_widget = ba.textwidget(
                    parent=columnwidget,
                    size=(0, 0),
                    position=(sub_scroll_width * 0.94 + hpos, 20 + vpos),
                    scale=0.7,
                    h_align='right',
                    v_align='center')
                if party.ping is None:
                    ba.textwidget(edit=party.ping_widget,
                                  text='-',
                                  color=(0.5, 0.5, 0.5))
                else:
                    ping_good = _ba.get_account_misc_read_val('pingGood', 100)
                    ping_med = _ba.get_account_misc_read_val('pingMed', 500)
                    ba.textwidget(edit=party.ping_widget,
                                  text=str(party.ping),
                                  color=(0, 1,
                                         0) if party.ping <= ping_good else
                                  (1, 1, 0) if party.ping <= ping_med else
                                  (1, 0, 0))

            # So our selection callbacks can start firing..
            def refresh_off() -> None:
                self._refreshing_public_party_list = False

            ba.pushcall(refresh_off)

    def _on_public_party_query_result(
            self, result: Optional[Dict[str, Any]]) -> None:
        with ba.Context('ui'):
            # Any time we get any result at all, kill our loading status.
            status_text = self._join_status_text
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
                partyval.claimed = False

            for party_in in parties_in:
                # Party is indexed by (ADDR)_(PORT)
                party_key = party_in['a'] + '_' + str(party_in['p'])
                party = self._public_parties.get(party_key)
                if party is None:
                    # If this party is new to us, init it.
                    index = self._next_public_party_entry_index
                    self._next_public_party_entry_index = index + 1
                    party = self._public_parties[party_key] = PartyEntry(
                        address=party_in.get('a'),
                        next_ping_time=ba.time(ba.TimeType.REAL) +
                        0.001 * party_in['pd'],
                        ping=None,
                        index=index)
                    assert isinstance(party.address, str)
                    assert isinstance(party.next_ping_time, float)

                # Now, new or not, update its values.
                party.queue = party_in.get('q')
                assert isinstance(party.queue, (str, type(None)))
                party.port = party_in.get('p')
                assert isinstance(party.port, int)
                party.name = party_in['n']
                assert isinstance(party.name, str)
                party.size = party_in['s']
                assert isinstance(party.size, int)
                party.size_max = party_in['sm']
                assert isinstance(party.size_max, int)
                party.claimed = True
                # (server provides this in milliseconds; we use seconds)
                party.ping_interval = 0.001 * party_in['pi']
                assert isinstance(party.ping_interval, float)
                party.stats_addr = party_in['sa']
                assert isinstance(party.stats_addr, (str, type(None)))

            # Prune unclaimed party entries.
            self._public_parties = {
                key: val
                for key, val in list(self._public_parties.items())
                if val.claimed
            }

            self._rebuild_public_party_list()

    def _update_sub_tab(self) -> None:
        # pylint: disable=too-many-statements

        # Special case: if a party-queue window is up, don't do any of this
        # (keeps things smoother).
        if ba.app.ui.have_party_queue_window:
            return

        # If we've got a party-name text widget, keep its value plugged
        # into our public host name.
        text = self._host_name_text
        if text:
            name = cast(str, ba.textwidget(query=self._host_name_text))
            _ba.set_public_party_name(name)

        if self._sub_tab is SubTabType.JOIN:
            now = ba.time(ba.TimeType.REAL)
            if (now - self._join_last_refresh_time > 0.001 *
                    _ba.get_account_misc_read_val('pubPartyRefreshMS', 10000)):
                self._join_last_refresh_time = now
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
                if (party.next_ping_time <= now
                        and ba.app.ping_thread_count < 15):

                    # Make sure to fully catch up and not to multi-ping if
                    # we're way behind somehow.
                    while party.next_ping_time <= now:
                        # Crank the interval up for high-latency parties to
                        # save us some work.
                        mult = 1
                        if party.ping is not None:
                            mult = (10 if party.ping > 300 else
                                    5 if party.ping > 150 else 2)
                        party.next_ping_time += party.ping_interval * mult

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

                    PingThread(party.address, party.port,
                               ba.WeakCall(self._ping_callback)).start()

    def _ping_callback(self, address: str, port: Optional[int],
                       result: Optional[int]) -> None:
        # Look for a widget corresponding to this target.
        # If we find one, update our list.
        party = self._public_parties.get(address + '_' + str(port))
        if party is not None:
            # We now smooth ping a bit to reduce jumping around in the list
            # (only where pings are relatively good).
            current_ping = party.ping
            if (current_ping is not None and result is not None
                    and result < 150):
                smoothing = 0.7
                party.ping = int(smoothing * current_ping +
                                 (1.0 - smoothing) * result)
            else:
                party.ping = result

            # This can happen if we switch away and then back to the
            # client tab while pings are in flight.
            # if 'ping_widget' not in party:
            #     pass
            if party.ping_widget:
                self._rebuild_public_party_list()

    def _fetch_local_addr_cb(self, val: str) -> None:
        self._local_address = str(val)

    def _on_public_party_accessible_response(
            self, data: Optional[Dict[str, Any]]) -> None:

        # If we've got status text widgets, update them.
        text = self._host_status_text
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
                    if self._local_address is not None:
                        ex_line = ba.Lstr(
                            value='\n${A} ${B}',
                            subs=[('${A}',
                                   ba.Lstr(resource='gatherWindow.'
                                           'manualYourLocalAddressText')),
                                  ('${B}', self._local_address)])
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

    def _do_status_check(self) -> None:
        from ba.internal import master_server_get
        ba.textwidget(edit=self._host_status_text,
                      color=(1, 1, 0),
                      text=ba.Lstr(resource='gatherWindow.'
                                   'partyStatusCheckingText'))
        master_server_get('bsAccessCheck', {'b': ba.app.build_number},
                          callback=ba.WeakCall(
                              self._on_public_party_accessible_response))

    def _on_start_advertizing_press(self) -> None:
        from bastd.ui.account import show_sign_in_prompt
        if _ba.get_account_state() != 'signed_in':
            show_sign_in_prompt()
            return

        name = cast(str, ba.textwidget(query=self._host_name_text))
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

        self._do_status_check()
        ba.buttonwidget(
            edit=self._host_toggle_button,
            label=ba.Lstr(
                resource='gatherWindow.makePartyPrivateText',
                fallback_resource='gatherWindow.stopAdvertisingText'),
            on_activate_call=self._on_stop_advertising_press)

    def _on_stop_advertising_press(self) -> None:
        _ba.set_public_party_enabled(False)

        # In GUI builds we want to authenticate clients only when hosting
        # public parties.
        _ba.set_authenticate_clients(False)
        ba.playsound(ba.getsound('shieldDown'))
        text = self._host_status_text
        if text:
            ba.textwidget(
                edit=text,
                text=ba.Lstr(resource='gatherWindow.'
                             'partyStatusNotPublicText'),
                color=(0.6, 0.6, 0.6),
            )
        ba.buttonwidget(
            edit=self._host_toggle_button,
            label=ba.Lstr(
                resource='gatherWindow.makePartyPublicText',
                fallback_resource='gatherWindow.startAdvertisingText'),
            on_activate_call=self._on_start_advertizing_press)

    def _on_public_party_activate(self, party: PartyEntry) -> None:
        if party.queue is not None:
            from bastd.ui.partyqueue import PartyQueueWindow
            ba.playsound(ba.getsound('swish'))
            PartyQueueWindow(party.queue, party.address, party.port)
        else:
            address = party.address
            port = party.port

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
        ba.textwidget(edit=self._host_max_party_size_value, text=str(val))

    def _on_max_public_party_size_plus_press(self) -> None:
        val = _ba.get_public_party_max_size()
        val += 1
        _ba.set_public_party_max_size(val)
        ba.textwidget(edit=self._host_max_party_size_value, text=str(val))
