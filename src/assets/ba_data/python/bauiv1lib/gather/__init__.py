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
        # pylint: disable=too-many-statements
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
        self._width = 1640 if uiscale is bui.UIScale.SMALL else 1040
        x_offs = 200 if uiscale is bui.UIScale.SMALL else 0
        y_offs = -65 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            650
            if uiscale is bui.UIScale.SMALL
            else 680 if uiscale is bui.UIScale.MEDIUM else 800
        )
        self._current_tab: GatherWindow.TabID | None = None
        extra_top = 20 if uiscale is bui.UIScale.SMALL else 0
        self._r = 'gatherWindow'

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + extra_top),
                toolbar_visibility=(
                    'menu_tokens'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    1.15
                    if uiscale is bui.UIScale.SMALL
                    else 0.95 if uiscale is bui.UIScale.MEDIUM else 0.7
                ),
                stack_offset=(
                    (0, 0)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 0) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(70 + x_offs, self._height - 74 + y_offs),
                size=(140, 60),
                scale=1.1,
                autoselect=True,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
            bui.buttonwidget(
                edit=btn,
                button_type='backSmall',
                position=(70 + x_offs, self._height - 78),
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        condensed = uiscale is not bui.UIScale.LARGE
        t_offs_y = (
            0 if not condensed else 25 if uiscale is bui.UIScale.MEDIUM else 33
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 42 + t_offs_y + y_offs),
            size=(0, 0),
            color=bui.app.ui_v1.title_color,
            scale=(
                1.5
                if not condensed
                else 1.0 if uiscale is bui.UIScale.MEDIUM else 1.0
            ),
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            maxwidth=320,
        )

        scroll_buffer_h = 130 + 2 * x_offs
        tab_buffer_h = (320 if condensed else 250) + 2 * x_offs

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

        # On small UI, push our tabs up closer to the top of the screen to
        # save a bit of space.
        tabs_top_extra = 42 if condensed else 0
        self._tab_row = TabRow(
            self._root_widget,
            tabdefs,
            pos=(
                tab_buffer_h * 0.5,
                self._height - 130 + tabs_top_extra + y_offs,
            ),
            size=(self._width - tab_buffer_h, 50),
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

        bui.widget(
            edit=self._tab_row.tabs[tabdefs[-1][0]].button,
            right_widget=bui.get_special_widget('squad_button'),
        )
        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=self._tab_row.tabs[tabdefs[0][0]].button,
                left_widget=bui.get_special_widget('back_button'),
            )

        self._scroll_width = self._width - scroll_buffer_h
        self._scroll_height = (
            self._height
            - (270.0 if uiscale is bui.UIScale.SMALL else 180.0)
            + tabs_top_extra
        )

        self._scroll_left = (self._width - self._scroll_width) * 0.5
        self._scroll_bottom = (
            self._height
            - self._scroll_height
            - 79
            - 48
            + tabs_top_extra
            + y_offs
        )
        buffer_h = 10
        buffer_v = 4

        # Not actually using a scroll widget anymore; just an image.
        bui.imagewidget(
            parent=self._root_widget,
            position=(
                self._scroll_left - buffer_h,
                self._scroll_bottom - buffer_v,
            ),
            size=(
                self._scroll_width + 2 * buffer_h,
                self._scroll_height + 2 * buffer_v,
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
