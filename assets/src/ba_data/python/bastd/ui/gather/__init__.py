# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for inviting/joining friends."""

from __future__ import annotations

import weakref
from enum import Enum
from typing import TYPE_CHECKING

import ba
import ba.internal
from bastd.ui.tabs import TabRow

if TYPE_CHECKING:
    pass


class GatherTab:
    """Defines a tab for use in the gather UI."""

    def __init__(self, window: GatherWindow) -> None:
        self._window = weakref.ref(window)

    @property
    def window(self) -> GatherWindow:
        """The GatherWindow that this tab belongs to."""
        window = self._window()
        if window is None:
            raise ba.NotFoundError("GatherTab's window no longer exists.")
        return window

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> ba.Widget:
        """Called when the tab becomes the active one.

        The tab should create and return a container widget covering the
        specified region.
        """
        raise RuntimeError('Should not get here.')

    def on_deactivate(self) -> None:
        """Called when the tab will no longer be the active one."""

    def save_state(self) -> None:
        """Called when the parent window is saving state."""

    def restore_state(self) -> None:
        """Called when the parent window is restoring state."""


class GatherWindow(ba.Window):
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
        origin_widget: ba.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bastd.ui.gather.abouttab import AboutGatherTab
        from bastd.ui.gather.manualtab import ManualGatherTab
        from bastd.ui.gather.privatetab import PrivateGatherTab
        from bastd.ui.gather.publictab import PublicGatherTab
        from bastd.ui.gather.nearbytab import NearbyGatherTab

        ba.set_analytics_screen('Gather Window')
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
        ba.app.ui.set_main_menu_location('Gather')
        ba.internal.set_party_icon_always_visible(True)
        uiscale = ba.app.ui.uiscale
        self._width = 1240 if uiscale is ba.UIScale.SMALL else 1040
        x_offs = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (
            582
            if uiscale is ba.UIScale.SMALL
            else 680
            if uiscale is ba.UIScale.MEDIUM
            else 800
        )
        self._current_tab: GatherWindow.TabID | None = None
        extra_top = 20 if uiscale is ba.UIScale.SMALL else 0
        self._r = 'gatherWindow'

        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height + extra_top),
                transition=transition,
                toolbar_visibility='menu_minimal',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    1.3
                    if uiscale is ba.UIScale.SMALL
                    else 0.97
                    if uiscale is ba.UIScale.MEDIUM
                    else 0.8
                ),
                stack_offset=(0, -11)
                if uiscale is ba.UIScale.SMALL
                else (0, 0)
                if uiscale is ba.UIScale.MEDIUM
                else (0, 0),
            )
        )

        if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
            ba.containerwidget(
                edit=self._root_widget, on_cancel_call=self._back
            )
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
                on_activate_call=self._back,
            )
            ba.containerwidget(edit=self._root_widget, cancel_button=btn)
            ba.buttonwidget(
                edit=btn,
                button_type='backSmall',
                position=(70 + x_offs, self._height - 78),
                size=(60, 60),
                label=ba.charstr(ba.SpecialChar.BACK),
            )

        condensed = uiscale is not ba.UIScale.LARGE
        t_offs_y = (
            0 if not condensed else 25 if uiscale is ba.UIScale.MEDIUM else 17
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 42 + t_offs_y),
            size=(0, 0),
            color=ba.app.ui.title_color,
            scale=(
                1.5
                if not condensed
                else 1.0
                if uiscale is ba.UIScale.MEDIUM
                else 0.6
            ),
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource=self._r + '.titleText'),
            maxwidth=550,
        )

        scroll_buffer_h = 130 + 2 * x_offs
        tab_buffer_h = (320 if condensed else 250) + 2 * x_offs

        # Build up the set of tabs we want.
        tabdefs: list[tuple[GatherWindow.TabID, ba.Lstr]] = [
            (self.TabID.ABOUT, ba.Lstr(resource=self._r + '.aboutText'))
        ]
        if ba.internal.get_v1_account_misc_read_val(
            'enablePublicParties', True
        ):
            tabdefs.append(
                (self.TabID.INTERNET, ba.Lstr(resource=self._r + '.publicText'))
            )
        tabdefs.append(
            (self.TabID.PRIVATE, ba.Lstr(resource=self._r + '.privateText'))
        )
        tabdefs.append(
            (self.TabID.NEARBY, ba.Lstr(resource=self._r + '.nearbyText'))
        )
        tabdefs.append(
            (self.TabID.MANUAL, ba.Lstr(resource=self._r + '.manualText'))
        )

        # On small UI, push our tabs up closer to the top of the screen to
        # save a bit of space.
        tabs_top_extra = 42 if condensed else 0
        self._tab_row = TabRow(
            self._root_widget,
            tabdefs,
            pos=(tab_buffer_h * 0.5, self._height - 130 + tabs_top_extra),
            size=(self._width - tab_buffer_h, 50),
            on_select_call=ba.WeakCall(self._set_tab),
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

        if ba.app.ui.use_toolbars:
            ba.widget(
                edit=self._tab_row.tabs[tabdefs[-1][0]].button,
                right_widget=ba.internal.get_special_widget('party_button'),
            )
            if uiscale is ba.UIScale.SMALL:
                ba.widget(
                    edit=self._tab_row.tabs[tabdefs[0][0]].button,
                    left_widget=ba.internal.get_special_widget('back_button'),
                )

        self._scroll_width = self._width - scroll_buffer_h
        self._scroll_height = self._height - 180.0 + tabs_top_extra

        self._scroll_left = (self._width - self._scroll_width) * 0.5
        self._scroll_bottom = (
            self._height - self._scroll_height - 79 - 48 + tabs_top_extra
        )
        buffer_h = 10
        buffer_v = 4

        # Not actually using a scroll widget anymore; just an image.
        ba.imagewidget(
            parent=self._root_widget,
            position=(
                self._scroll_left - buffer_h,
                self._scroll_bottom - buffer_v,
            ),
            size=(
                self._scroll_width + 2 * buffer_h,
                self._scroll_height + 2 * buffer_v,
            ),
            texture=ba.gettexture('scrollWidget'),
            model_transparent=ba.getmodel('softEdgeOutside'),
        )
        self._tab_container: ba.Widget | None = None

        self._restore_state()

    def __del__(self) -> None:
        ba.internal.set_party_icon_always_visible(False)

    def playlist_select(self, origin_widget: ba.Widget) -> None:
        """Called by the private-hosting tab to select a playlist."""
        from bastd.ui.play import PlayWindow

        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.selecting_private_party_playlist = True
        ba.app.ui.set_main_menu_window(
            PlayWindow(origin_widget=origin_widget).get_root_widget()
        )

    def _set_tab(self, tab_id: TabID) -> None:
        if self._current_tab is tab_id:
            return
        prev_tab_id = self._current_tab
        self._current_tab = tab_id

        # We wanna preserve our current tab between runs.
        cfg = ba.app.config
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
            ba.app.ui.window_states[type(self)] = {
                'sel_name': sel_name,
            }
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        from efro.util import enum_by_value

        try:
            for tab in self._tabs.values():
                tab.restore_state()

            sel: ba.Widget | None
            winstate = ba.app.ui.window_states.get(type(self), {})
            sel_name = winstate.get('sel_name', None)
            assert isinstance(sel_name, (str, type(None)))
            current_tab = self.TabID.ABOUT
            gather_tab_val = ba.app.config.get('Gather Tab')
            try:
                stored_tab = enum_by_value(self.TabID, gather_tab_val)
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
                    sel_tab_id = enum_by_value(
                        self.TabID, sel_name.split(':')[-1]
                    )
                except ValueError:
                    sel_tab_id = self.TabID.ABOUT
                sel = self._tab_row.tabs[sel_tab_id].button
            else:
                sel = self._tab_row.tabs[current_tab].button
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception('Error restoring gather-win state.')

    def _back(self) -> None:
        from bastd.ui.mainmenu import MainMenuWindow

        self._save_state()
        ba.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        ba.app.ui.set_main_menu_window(
            MainMenuWindow(transition='in_left').get_root_widget()
        )
