# Released under the MIT License. See LICENSE for details.
#
"""Defines the nearby tab in the gather UI."""

import weakref
from typing import TYPE_CHECKING, override, assert_never

from bacommon.analytics import ClassicAnalyticsEvent
import bauiv1 as bui
from bauiv1 import _classicassets
import bascenev1 as bs

from bauiv1lib.gather import GatherTab

if TYPE_CHECKING:
    from bauiv1lib.gather import GatherWindow
    from bauiv1lib.localnetwork import LocalNetworkPermissionWarning


class NetScanner:
    """Class for scanning for nearby games (lan, bluetooth, etc)."""

    def __init__(
        self,
        *,
        tab: GatherTab,
        scrollwidget: bui.Widget,
        tab_button: bui.Widget,
        width: float,
        idprefix: str,
    ):
        self._idprefix = idprefix
        self._tab = weakref.ref(tab)
        self._scrollwidget = scrollwidget
        self._tab_button = tab_button
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            id=f'{self._idprefix}|col',
            border=2,
            margin=0,
            left_border=10,
        )
        bui.widget(edit=self._columnwidget, up_widget=tab_button)
        self._width = width
        self._last_selected_key: str | None = None
        self._last_rows: list[tuple[str, str]] | None = None

        # Results arrive as hosts are found (or lost); discovery runs
        # while this scan does.
        self._scan: bs.NearbyScan | None = bs.app.nearby.scan(
            {bs.NearbyService.GAME},
            on_change=bui.WeakCallStrict(self._update),
        )
        self._update()

    def stop(self) -> None:
        """Stop scanning."""
        if self._scan is not None:
            self._scan.stop()
            self._scan = None

    def __del__(self) -> None:
        self.stop()

    def _on_select(self, key: str) -> None:
        self._last_selected_key = key

    def _on_activate(self, key: str) -> None:
        if self._scan is None:
            return
        host = next((h for h in self._scan.hosts if h.key == key), None)
        if host is None:
            return
        # Offer every plain-address route on the best one's port, best
        # first; the join races them and uses whichever answers first
        # (so a route that just went stale can't sink the join).
        port = host.route.port
        addresses: list[str] = []
        for route in host.routes:
            match route.type:
                case bs.NearbyRouteType.UDP:
                    if route.port == port:
                        addresses.append(route.address)
                case _:
                    assert_never(route.type)
        if not addresses:
            return

        # Repeat taps while a join to this host is underway are ignored
        # there; only count/act on actual attempts.
        if not bs.connect_to_party(addresses, port=port):
            return

        bui.app.analytics.submit_event(
            ClassicAnalyticsEvent(
                ClassicAnalyticsEvent.EventType.JOIN_NEARBY_PARTY
            )
        )

        # Store UI location to return to when done. (The connect itself
        # happens asynchronously, after this.)
        if bs.app.classic is not None:
            bs.app.classic.save_ui_state()

    def _update(self) -> None:
        """(internal)"""

        # In case our UI was killed from under us.
        if not self._columnwidget:
            bui.uilog.error(
                'nearbytab NetScanner running without UI at time %s.',
                bui.apptime(),
            )
            return

        if self._scan is None:
            return

        # What we show for each host: its party name when it advertises
        # one (newer hosts), otherwise its player name.
        rows: list[tuple[str, str]] = []
        for host in self._scan.hosts:
            assert host.game is not None
            rows.append(
                (
                    host.key,
                    host.game.party_name
                    or bs.player_spec_display_string(host.game.player_spec),
                )
            )

        # If nothing we show has changed, do nothing (round-trip times
        # move constantly). Redundant rebuilds are likely to lose some
        # clicks by rebuilding after a click starts but before it ends.
        if rows == self._last_rows:
            return

        self._last_rows = rows

        t_scale = 1.6
        for child in self._columnwidget.get_children():
            child.delete()

        # Grab this now this since adding widgets will change it.
        last_selected_key = self._last_selected_key
        for i, (key, text) in enumerate(rows):
            txt3 = bui.textwidget(
                parent=self._columnwidget,
                size=(self._width / t_scale, 30),
                selectable=True,
                color=(1, 1, 1),
                on_select_call=bui.CallStrict(self._on_select, key),
                on_activate_call=bui.CallStrict(self._on_activate, key),
                click_activate=True,
                text=text,
                literal=True,
                h_align='left',
                v_align='center',
                corner_scale=t_scale,
                maxwidth=(self._width / t_scale) * 0.93,
            )
            # We don't give these ids since they pop in and out and it
            # doesn't make sense to save/restore selections for them.
            # But we need to suppress the warning from that.
            bui.widget(edit=txt3, allow_preserve_selection=False)

            if key == last_selected_key:
                bui.containerwidget(
                    edit=self._columnwidget,
                    selected_child=txt3,
                    visible_child=txt3,
                )
            if i == 0:
                bui.widget(edit=txt3, up_widget=self._tab_button)


class NearbyGatherTab(GatherTab):
    """The nearby tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._idprefix = f'{window.main_window_id_prefix}|nearby'
        self._net_scanner: NetScanner | None = None
        self._container: bui.Widget | None = None
        self._permission_warning: LocalNetworkPermissionWarning | None = None

    @override
    def on_activate(
        self,
        parent_widget: bui.Widget,
        tab_button: bui.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> bui.Widget:
        # pylint: disable=too-many-positional-arguments
        from bauiv1lib.localnetwork import (
            WARNING_HEIGHT,
            LocalNetworkPermissionWarning,
            local_network_permission_missing,
        )

        c_width = region_width
        c_height = region_height - 20
        sub_scroll_height = c_height - 85
        sub_scroll_width = 650

        # Lacking local-network permission (Android 17+)? Shorten the
        # list to make room for a warning below it. (Once granted, it
        # stays shortened until the tab is rebuilt; harmless.)
        show_permission_warning = local_network_permission_missing()
        if show_permission_warning:
            sub_scroll_height -= WARNING_HEIGHT
        self._container = bui.containerwidget(
            parent=parent_widget,
            position=(
                region_left,
                region_bottom + (region_height - c_height) * 0.5,
            ),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True,
        )
        v = c_height - 30
        bui.textwidget(
            parent=self._container,
            position=(c_width * 0.5, v - 3),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(0, 0),
            maxwidth=c_width * 0.9,
            h_align='center',
            v_align='center',
            text=_classicassets.strings.gather.local_network_description,
        )
        v -= 15
        v -= sub_scroll_height + 23
        scrollw = bui.scrollwidget(
            parent=self._container,
            position=((region_width - sub_scroll_width) * 0.5, v),
            size=(sub_scroll_width, sub_scroll_height),
        )

        self._net_scanner = NetScanner(
            idprefix=self._idprefix,
            tab=self,
            scrollwidget=scrollw,
            tab_button=tab_button,
            width=sub_scroll_width,
        )

        bui.widget(edit=scrollw, autoselect=True, up_widget=tab_button)

        if show_permission_warning:
            self._permission_warning = LocalNetworkPermissionWarning(
                parent=self._container,
                position=(c_width * 0.5, v - WARNING_HEIGHT * 0.5),
                width=sub_scroll_width,
                idprefix=self._idprefix,
            )
        return self._container

    @override
    def on_deactivate(self) -> None:
        if self._net_scanner is not None:
            self._net_scanner.stop()
        self._net_scanner = None
        self._permission_warning = None
