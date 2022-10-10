# Released under the MIT License. See LICENSE for details.
#
"""Defines the nearby tab in the gather UI."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import ba
import ba.internal
from bastd.ui.gather import GatherTab

if TYPE_CHECKING:
    from typing import Any
    from bastd.ui.gather import GatherWindow


class NetScanner:
    """Class for scanning for games on the lan."""

    def __init__(
        self,
        tab: GatherTab,
        scrollwidget: ba.Widget,
        tab_button: ba.Widget,
        width: float,
    ):
        self._tab = weakref.ref(tab)
        self._scrollwidget = scrollwidget
        self._tab_button = tab_button
        self._columnwidget = ba.columnwidget(
            parent=self._scrollwidget, border=2, margin=0, left_border=10
        )
        ba.widget(edit=self._columnwidget, up_widget=tab_button)
        self._width = width
        self._last_selected_host: dict[str, Any] | None = None

        self._update_timer = ba.Timer(
            1.0,
            ba.WeakCall(self.update),
            timetype=ba.TimeType.REAL,
            repeat=True,
        )
        # Go ahead and run a few *almost* immediately so we don't
        # have to wait a second.
        self.update()
        ba.timer(0.25, ba.WeakCall(self.update), timetype=ba.TimeType.REAL)

    def __del__(self) -> None:
        ba.internal.end_host_scanning()

    def _on_select(self, host: dict[str, Any]) -> None:
        self._last_selected_host = host

    def _on_activate(self, host: dict[str, Any]) -> None:
        ba.internal.connect_to_party(host['address'])

    def update(self) -> None:
        """(internal)"""

        # In case our UI was killed from under us.
        if not self._columnwidget:
            print(
                f'ERROR: NetScanner running without UI at time'
                f' {ba.time(timetype=ba.TimeType.REAL)}.'
            )
            return

        t_scale = 1.6
        for child in self._columnwidget.get_children():
            child.delete()

        # Grab this now this since adding widgets will change it.
        last_selected_host = self._last_selected_host
        hosts = ba.internal.host_scan_cycle()
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
                maxwidth=(self._width / t_scale) * 0.93,
            )
            if host == last_selected_host:
                ba.containerwidget(
                    edit=self._columnwidget,
                    selected_child=txt3,
                    visible_child=txt3,
                )
            if i == 0:
                ba.widget(edit=txt3, up_widget=self._tab_button)


class NearbyGatherTab(GatherTab):
    """The nearby tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._net_scanner: NetScanner | None = None
        self._container: ba.Widget | None = None

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
        sub_scroll_height = c_height - 85
        sub_scroll_width = 650
        self._container = ba.containerwidget(
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
        ba.textwidget(
            parent=self._container,
            position=(c_width * 0.5, v - 3),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(0, 0),
            maxwidth=c_width * 0.9,
            h_align='center',
            v_align='center',
            text=ba.Lstr(
                resource='gatherWindow.' 'localNetworkDescriptionText'
            ),
        )
        v -= 15
        v -= sub_scroll_height + 23
        scrollw = ba.scrollwidget(
            parent=self._container,
            position=((region_width - sub_scroll_width) * 0.5, v),
            size=(sub_scroll_width, sub_scroll_height),
        )

        self._net_scanner = NetScanner(
            self, scrollw, tab_button, width=sub_scroll_width
        )

        ba.widget(edit=scrollw, autoselect=True, up_widget=tab_button)
        return self._container

    def on_deactivate(self) -> None:
        self._net_scanner = None
