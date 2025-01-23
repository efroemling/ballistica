# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for inviting/joining friends."""

from __future__ import annotations

import weakref
import logging
from enum import Enum
from typing import override, TYPE_CHECKING

from bauiv1lib.tabs import TabRow
import bauiv1 as bui

if TYPE_CHECKING:
    from bauiv1lib.play import PlaylistSelectContext


class GatherTab:
    """Defines a tab for use in the gather UI."""

    def __init__(self, window: GatherWindow) -> None:
        self._window = weakref.ref(window)

    @property
    def window(self) -> GatherWindow:
        """The GatherWindow that this tab belongs to."""
        window = self._window()
        if window is None:
            raise bui.NotFoundError("GatherTab's window no longer exists.")
        return window

    def on_activate(
        self,
        parent_widget: bui.Widget,
        tab_button: bui.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> bui.Widget:
        """Called when the tab becomes the active one.

        The tab should create and return a container widget covering the
        specified region.
        """
        # pylint: disable=too-many-positional-arguments
        raise RuntimeError('Should not get here.')

    def on_deactivate(self) -> None:
        """Called when the tab will no longer be the active one."""

    def save_state(self) -> None:
        """Called when the parent window is saving state."""

    def restore_state(self) -> None:
        """Called when the parent window is restoring state."""


class GatherWindow(bui.MainWindow):
    """Window for joining/inviting friends."""

    class TabID(Enum):
        """Our available tab types."""

        ABOUT = 'about'
        INTERNET = 'internet'
        PRIVATE = 'private'
        NEARBY = 'nearby'
        MANUAL = 'manual'

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bauiv1lib.gather.abouttab import AboutGatherTab
        from bauiv1lib.gather.manualtab import ManualGatherTab
        from bauiv1lib.gather.privatetab import PrivateGatherTab
        from bauiv1lib.gather.publictab import PublicGatherTab
        from bauiv1lib.gather.nearbytab import NearbyGatherTab

        plus = bui.app.plus
        assert plus is not None

        bui.set_analytics_screen('Gather Window')
        uiscale = bui.app.ui_v1.uiscale
        self._width = (
            1640
            if uiscale is bui.UIScale.SMALL
            else 1100 if uiscale is bui.UIScale.MEDIUM else 1200
        )
        self._height = (
            1000
            if uiscale is bui.UIScale.SMALL
            else 730 if uiscale is bui.UIScale.MEDIUM else 900
        )
        self._current_tab: GatherWindow.TabID | None = None
        self._r = 'gatherWindow'

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.4
            if uiscale is bui.UIScale.SMALL
            else 0.88 if uiscale is bui.UIScale.MEDIUM else 0.66
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 130, screensize[0] / scale)
        target_height = min(self._height - 130, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        self._scroll_width = target_width
        self._scroll_height = target_height - 65
        self._scroll_bottom = yoffs - 93 - self._scroll_height
        self._scroll_left = (self._width - self._scroll_width) * 0.5

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_tokens'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(70, yoffs - 43),
                size=(60, 60),
                scale=1.1,
                autoselect=True,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(
                (
                    self._width * 0.5
                    + (
                        (self._scroll_width * -0.5 + 170.0 - 70.0)
                        if uiscale is bui.UIScale.SMALL
                        else 0.0
                    )
                ),
                yoffs - (64 if uiscale is bui.UIScale.SMALL else 4),
            ),
            size=(0, 0),
            color=bui.app.ui_v1.title_color,
            scale=1.3 if uiscale is bui.UIScale.SMALL else 1.0,
            h_align='left' if uiscale is bui.UIScale.SMALL else 'center',
            v_align='center',
            text=(bui.Lstr(resource=f'{self._r}.titleText')),
            maxwidth=135 if uiscale is bui.UIScale.SMALL else 320,
        )

        # Build up the set of tabs we want.
        tabdefs: list[tuple[GatherWindow.TabID, bui.Lstr]] = [
            (self.TabID.ABOUT, bui.Lstr(resource=f'{self._r}.aboutText'))
        ]
        if plus.get_v1_account_misc_read_val('enablePublicParties', True):
            tabdefs.append(
                (
                    self.TabID.INTERNET,
                    bui.Lstr(resource=f'{self._r}.publicText'),
                )
            )
        tabdefs.append(
            (self.TabID.PRIVATE, bui.Lstr(resource=f'{self._r}.privateText'))
        )
        tabdefs.append(
            (self.TabID.NEARBY, bui.Lstr(resource=f'{self._r}.nearbyText'))
        )
        tabdefs.append(
            (self.TabID.MANUAL, bui.Lstr(resource=f'{self._r}.manualText'))
        )

        tab_inset = 250.0 if uiscale is bui.UIScale.SMALL else 100.0

        self._tab_row = TabRow(
            self._root_widget,
            tabdefs,
            size=(self._scroll_width - 2.0 * tab_inset, 50),
            pos=(
                self._scroll_left + tab_inset,
                self._scroll_bottom + self._scroll_height - 4.0,
            ),
            on_select_call=bui.WeakCall(self._set_tab),
        )

        # Now instantiate handlers for these tabs.
        tabtypes: dict[GatherWindow.TabID, type[GatherTab]] = {
            self.TabID.ABOUT: AboutGatherTab,
            self.TabID.MANUAL: ManualGatherTab,
            self.TabID.PRIVATE: PrivateGatherTab,
            self.TabID.INTERNET: PublicGatherTab,
            self.TabID.NEARBY: NearbyGatherTab,
        }
        self._tabs: dict[GatherWindow.TabID, GatherTab] = {}
        for tab_id in self._tab_row.tabs:
            tabtype = tabtypes.get(tab_id)
            if tabtype is not None:
                self._tabs[tab_id] = tabtype(self)

        # Eww; tokens meter may or may not be here; should be smarter
        # about this.
        bui.widget(
            edit=self._tab_row.tabs[tabdefs[-1][0]].button,
            right_widget=bui.get_special_widget('tokens_meter'),
        )
        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=self._tab_row.tabs[tabdefs[0][0]].button,
                left_widget=bui.get_special_widget('back_button'),
                up_widget=bui.get_special_widget('back_button'),
            )

        # Not actually using a scroll widget anymore; just an image.
        bui.imagewidget(
            parent=self._root_widget,
            size=(self._scroll_width, self._scroll_height),
            position=(
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
            ),
            texture=bui.gettexture('scrollWidget'),
            mesh_transparent=bui.getmesh('softEdgeOutside'),
            opacity=0.4,
        )
        self._tab_container: bui.Widget | None = None

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

    def playlist_select(
        self,
        origin_widget: bui.Widget,
        context: PlaylistSelectContext,
    ) -> None:
        """Called by the private-hosting tab to select a playlist."""
        from bauiv1lib.play import PlayWindow

        # Avoid redundant window spawns.
        if not self.main_window_has_control():
            return

        playwindow = PlayWindow(
            origin_widget=origin_widget, playlist_select_context=context
        )
        self.main_window_replace(playwindow)

        # Grab the newly-set main-window's back-state; that will lead us
        # back here once we're done going down our main-window
        # rabbit-hole for playlist selection.
        context.back_state = playwindow.main_window_back_state

    def _set_tab(self, tab_id: TabID) -> None:
        if self._current_tab is tab_id:
            return
        prev_tab_id = self._current_tab
        self._current_tab = tab_id

        # We wanna preserve our current tab between runs.
        cfg = bui.app.config
        cfg['Gather Tab'] = tab_id.value
        cfg.commit()

        # Update tab colors based on which is selected.
        self._tab_row.update_appearance(tab_id)

        if prev_tab_id is not None:
            prev_tab = self._tabs.get(prev_tab_id)
            if prev_tab is not None:
                prev_tab.on_deactivate()

        # Clear up prev container if it hasn't been done.
        if self._tab_container:
            self._tab_container.delete()

        tab = self._tabs.get(tab_id)
        if tab is not None:
            self._tab_container = tab.on_activate(
                self._root_widget,
                self._tab_row.tabs[tab_id].button,
                self._scroll_width,
                self._scroll_height,
                self._scroll_left,
                self._scroll_bottom,
            )
            return

    def _save_state(self) -> None:
        try:
            for tab in self._tabs.values():
                tab.save_state()

            sel = self._root_widget.get_selected_child()
            selected_tab_ids = [
                tab_id
                for tab_id, tab in self._tab_row.tabs.items()
                if sel == tab.button
            ]
            if sel == self._back_button:
                sel_name = 'Back'
            elif selected_tab_ids:
                assert len(selected_tab_ids) == 1
                sel_name = f'Tab:{selected_tab_ids[0].value}'
            elif sel == self._tab_container:
                sel_name = 'TabContainer'
            else:
                raise ValueError(f'unrecognized selection: \'{sel}\'')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = {
                'sel_name': sel_name,
            }
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            for tab in self._tabs.values():
                tab.restore_state()

            sel: bui.Widget | None
            assert bui.app.classic is not None
            winstate = bui.app.ui_v1.window_states.get(type(self), {})
            sel_name = winstate.get('sel_name', None)
            assert isinstance(sel_name, (str, type(None)))
            current_tab = self.TabID.ABOUT
            gather_tab_val = bui.app.config.get('Gather Tab')
            try:
                stored_tab = self.TabID(gather_tab_val)
                if stored_tab in self._tab_row.tabs:
                    current_tab = stored_tab
            except ValueError:
                pass
            self._set_tab(current_tab)
            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'TabContainer':
                sel = self._tab_container
            elif isinstance(sel_name, str) and sel_name.startswith('Tab:'):
                try:
                    sel_tab_id = self.TabID(sel_name.split(':')[-1])
                except ValueError:
                    sel_tab_id = self.TabID.ABOUT
                sel = self._tab_row.tabs[sel_tab_id].button
            else:
                sel = self._tab_row.tabs[current_tab].button
            bui.containerwidget(edit=self._root_widget, selected_child=sel)

        except Exception:
            logging.exception('Error restoring state for %s.', self)
