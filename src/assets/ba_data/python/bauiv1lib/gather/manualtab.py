# Released under the MIT License. See LICENSE for details.
#
"""Defines the manual tab in the gather UI."""
# pylint: disable=too-many-lines

from __future__ import annotations

import logging
from enum import Enum
from threading import Thread
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, override
from bauiv1lib.gather import GatherTab

import bauiv1 as bui
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Callable

    from bauiv1lib.gather import GatherWindow


def _safe_set_text(
    txt: bui.Widget | None, val: str | bui.Lstr, success: bool = True
) -> None:
    if txt:
        bui.textwidget(
            edit=txt, text=val, color=(0, 1, 0) if success else (1, 1, 0)
        )


class _HostLookupThread(Thread):
    """Thread to fetch an addr."""

    def __init__(
        self, name: str, port: int, call: Callable[[str | None, int], Any]
    ):
        super().__init__()
        self._name = name
        self._port = port
        self._call = call

    @override
    def run(self) -> None:
        result: str | None
        try:
            import socket

            result = [
                item[-1][0]
                for item in socket.getaddrinfo(self.name, self._port)
            ][0]
        except Exception:
            result = None
        bui.pushcall(
            lambda: self._call(result, self._port), from_other_thread=True
        )


class SubTabType(Enum):
    """Available sub-tabs."""

    JOIN_BY_ADDRESS = 'join_by_address'
    FAVORITES = 'favorites'


@dataclass
class State:
    """State saved/restored only while the app is running."""

    sub_tab: SubTabType = SubTabType.JOIN_BY_ADDRESS


class ManualGatherTab(GatherTab):
    """The manual tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._check_button: bui.Widget | None = None
        self._doing_access_check: bool | None = None
        self._access_check_count: int | None = None
        self._sub_tab: SubTabType = SubTabType.JOIN_BY_ADDRESS
        self._t_addr: bui.Widget | None = None
        self._t_accessible: bui.Widget | None = None
        self._t_accessible_extra: bui.Widget | None = None
        self._access_check_timer: bui.AppTimer | None = None
        self._checking_state_text: bui.Widget | None = None
        self._container: bui.Widget | None = None
        self._join_by_address_text: bui.Widget | None = None
        self._favorites_text: bui.Widget | None = None
        self._width: float | None = None
        self._height: float | None = None
        self._scroll_width: float | None = None
        self._scroll_height: float | None = None
        self._favorites_scroll_width: int | None = None
        self._favorites_connect_button: bui.Widget | None = None
        self._scrollwidget: bui.Widget | None = None
        self._columnwidget: bui.Widget | None = None
        self._favorite_selected: str | None = None
        self._favorite_edit_window: bui.Widget | None = None
        self._party_edit_name_text: bui.Widget | None = None
        self._party_edit_addr_text: bui.Widget | None = None
        self._party_edit_port_text: bui.Widget | None = None
        self._no_parties_added_text: bui.Widget | None = None

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
        c_width = region_width
        c_height = region_height - 20

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
        self._join_by_address_text = bui.textwidget(
            parent=self._container,
            position=(c_width * 0.5 - 245, v - 13),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(200, 30),
            maxwidth=250,
            h_align='center',
            v_align='center',
            click_activate=True,
            selectable=True,
            autoselect=True,
            on_activate_call=lambda: self._set_sub_tab(
                SubTabType.JOIN_BY_ADDRESS,
                region_width,
                region_height,
                playsound=True,
            ),
            text=bui.Lstr(resource='gatherWindow.manualJoinSectionText'),
            glow_type='uniform',
        )
        self._favorites_text = bui.textwidget(
            parent=self._container,
            position=(c_width * 0.5 + 45, v - 13),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(200, 30),
            maxwidth=250,
            h_align='center',
            v_align='center',
            click_activate=True,
            selectable=True,
            autoselect=True,
            on_activate_call=lambda: self._set_sub_tab(
                SubTabType.FAVORITES,
                region_width,
                region_height,
                playsound=True,
            ),
            text=bui.Lstr(resource='gatherWindow.favoritesText'),
            glow_type='uniform',
        )
        bui.widget(edit=self._join_by_address_text, up_widget=tab_button)
        bui.widget(
            edit=self._favorites_text,
            left_widget=self._join_by_address_text,
            up_widget=tab_button,
        )
        bui.widget(edit=tab_button, down_widget=self._favorites_text)
        bui.widget(
            edit=self._join_by_address_text, right_widget=self._favorites_text
        )
        self._set_sub_tab(self._sub_tab, region_width, region_height)

        return self._container

    @override
    def save_state(self) -> None:
        assert bui.app.classic is not None
        bui.app.ui_v1.window_states[type(self)] = State(sub_tab=self._sub_tab)

    @override
    def restore_state(self) -> None:
        assert bui.app.classic is not None
        state = bui.app.ui_v1.window_states.get(type(self))
        if state is None:
            state = State()
        assert isinstance(state, State)
        self._sub_tab = state.sub_tab

    def _set_sub_tab(
        self,
        value: SubTabType,
        region_width: float,
        region_height: float,
        playsound: bool = False,
    ) -> None:
        assert self._container
        if playsound:
            bui.getsound('click01').play()

        self._sub_tab = value
        active_color = (0.6, 1.0, 0.6)
        inactive_color = (0.5, 0.4, 0.5)
        bui.textwidget(
            edit=self._join_by_address_text,
            color=(
                active_color
                if value is SubTabType.JOIN_BY_ADDRESS
                else inactive_color
            ),
        )
        bui.textwidget(
            edit=self._favorites_text,
            color=(
                active_color
                if value is SubTabType.FAVORITES
                else inactive_color
            ),
        )

        # Clear anything existing in the old sub-tab.
        for widget in self._container.get_children():
            if widget and widget not in {
                self._favorites_text,
                self._join_by_address_text,
            }:
                widget.delete()

        if value is SubTabType.JOIN_BY_ADDRESS:
            self._build_join_by_address_tab(region_width, region_height)

        if value is SubTabType.FAVORITES:
            self._build_favorites_tab(region_width, region_height)

    # The old manual tab
    def _build_join_by_address_tab(
        self, region_width: float, region_height: float
    ) -> None:
        c_width = region_width
        c_height = region_height - 20
        last_addr = bui.app.config.get('Last Manual Party Connect Address', '')
        last_port = bui.app.config.get('Last Manual Party Connect Port', 43210)
        v = c_height - 70
        v -= 70
        bui.textwidget(
            parent=self._container,
            position=(c_width * 0.5 - 260 - 50, v),
            color=(0.6, 1.0, 0.6),
            scale=1.0,
            size=(0, 0),
            maxwidth=130,
            h_align='right',
            v_align='center',
            text=bui.Lstr(resource='gatherWindow.' 'manualAddressText'),
        )
        txt = bui.textwidget(
            parent=self._container,
            editable=True,
            description=bui.Lstr(resource='gatherWindow.' 'manualAddressText'),
            position=(c_width * 0.5 - 240 - 50, v - 30),
            text=last_addr,
            autoselect=True,
            v_align='center',
            scale=1.0,
            maxwidth=380,
            size=(420, 60),
        )
        assert self._join_by_address_text is not None
        bui.widget(edit=self._join_by_address_text, down_widget=txt)
        assert self._favorites_text is not None
        bui.widget(edit=self._favorites_text, down_widget=txt)
        bui.textwidget(
            parent=self._container,
            position=(c_width * 0.5 - 260 + 490, v),
            color=(0.6, 1.0, 0.6),
            scale=1.0,
            size=(0, 0),
            maxwidth=80,
            h_align='right',
            v_align='center',
            text=bui.Lstr(resource='gatherWindow.' 'portText'),
        )
        txt2 = bui.textwidget(
            parent=self._container,
            editable=True,
            description=bui.Lstr(resource='gatherWindow.' 'portText'),
            text=str(last_port),
            autoselect=True,
            max_chars=5,
            position=(c_width * 0.5 - 240 + 490, v - 30),
            v_align='center',
            scale=1.0,
            size=(170, 60),
        )

        v -= 110

        btn = bui.buttonwidget(
            parent=self._container,
            size=(300, 70),
            label=bui.Lstr(resource='gatherWindow.' 'manualConnectText'),
            position=(c_width * 0.5 - 300, v),
            autoselect=True,
            on_activate_call=bui.Call(self._connect, txt, txt2),
        )
        savebutton = bui.buttonwidget(
            parent=self._container,
            size=(300, 70),
            label=bui.Lstr(resource='gatherWindow.favoritesSaveText'),
            position=(c_width * 0.5 - 240 + 490 - 200, v),
            autoselect=True,
            on_activate_call=bui.Call(self._save_server, txt, txt2),
        )
        bui.widget(edit=btn, right_widget=savebutton)
        bui.widget(edit=savebutton, left_widget=btn, up_widget=txt2)
        bui.textwidget(edit=txt, on_return_press_call=btn.activate)
        bui.textwidget(edit=txt2, on_return_press_call=btn.activate)
        v -= 45

        self._check_button = bui.textwidget(
            parent=self._container,
            size=(250, 60),
            text=bui.Lstr(resource='gatherWindow.showMyAddressText'),
            v_align='center',
            h_align='center',
            click_activate=True,
            position=(c_width * 0.5 - 125, v - 30),
            autoselect=True,
            color=(0.5, 0.9, 0.5),
            scale=0.8,
            selectable=True,
            on_activate_call=bui.Call(
                self._on_show_my_address_button_press,
                v,
                self._container,
                c_width,
            ),
            glow_type='uniform',
        )
        bui.widget(edit=self._check_button, up_widget=btn)

    # Tab containing saved favorite addresses
    def _build_favorites_tab(
        self, region_width: float, region_height: float
    ) -> None:
        c_height = region_height - 20
        v = c_height - 35 - 25 - 30

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        # self._width = 1240 if uiscale is bui.UIScale.SMALL else 1040
        self._width = region_width
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            578
            if uiscale is bui.UIScale.SMALL
            else 670 if uiscale is bui.UIScale.MEDIUM else 800
        )

        self._scroll_width = self._width - 130 + 2 * x_inset
        self._scroll_height = self._height - 180
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0

        c_height = self._scroll_height - 20
        sub_scroll_height = c_height - 63
        self._favorites_scroll_width = sub_scroll_width = (
            680 if uiscale is bui.UIScale.SMALL else 640
        )

        v = c_height - 30

        b_width = 140 if uiscale is bui.UIScale.SMALL else 178
        b_height = (
            107
            if uiscale is bui.UIScale.SMALL
            else 142 if uiscale is bui.UIScale.MEDIUM else 190
        )
        b_space_extra = (
            0
            if uiscale is bui.UIScale.SMALL
            else -2 if uiscale is bui.UIScale.MEDIUM else -5
        )

        btnv = (
            c_height
            - (
                48
                if uiscale is bui.UIScale.SMALL
                else 45 if uiscale is bui.UIScale.MEDIUM else 40
            )
            - b_height
        )

        self._favorites_connect_button = btn1 = bui.buttonwidget(
            parent=self._container,
            size=(b_width, b_height),
            position=(140 if uiscale is bui.UIScale.SMALL else 40, btnv),
            button_type='square',
            color=(0.6, 0.53, 0.63),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self._on_favorites_connect_press,
            text_scale=1.0 if uiscale is bui.UIScale.SMALL else 1.2,
            label=bui.Lstr(resource='gatherWindow.manualConnectText'),
            autoselect=True,
        )
        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=btn1,
                left_widget=bui.get_special_widget('back_button'),
            )
        btnv -= b_height + b_space_extra
        bui.buttonwidget(
            parent=self._container,
            size=(b_width, b_height),
            position=(140 if uiscale is bui.UIScale.SMALL else 40, btnv),
            button_type='square',
            color=(0.6, 0.53, 0.63),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self._on_favorites_edit_press,
            text_scale=1.0 if uiscale is bui.UIScale.SMALL else 1.2,
            label=bui.Lstr(resource='editText'),
            autoselect=True,
        )
        btnv -= b_height + b_space_extra
        bui.buttonwidget(
            parent=self._container,
            size=(b_width, b_height),
            position=(140 if uiscale is bui.UIScale.SMALL else 40, btnv),
            button_type='square',
            color=(0.6, 0.53, 0.63),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self._on_favorite_delete_press,
            text_scale=1.0 if uiscale is bui.UIScale.SMALL else 1.2,
            label=bui.Lstr(resource='deleteText'),
            autoselect=True,
        )

        v -= sub_scroll_height + 23
        self._scrollwidget = scrlw = bui.scrollwidget(
            parent=self._container,
            position=(290 if uiscale is bui.UIScale.SMALL else 225, v),
            size=(sub_scroll_width, sub_scroll_height),
            claims_left_right=True,
        )
        bui.widget(
            edit=self._favorites_connect_button, right_widget=self._scrollwidget
        )
        self._columnwidget = bui.columnwidget(
            parent=scrlw,
            left_border=10,
            border=2,
            margin=0,
            claims_left_right=True,
        )

        self._no_parties_added_text = bui.textwidget(
            parent=self._container,
            size=(0, 0),
            h_align='center',
            v_align='center',
            text='',
            color=(0.6, 0.6, 0.6),
            scale=1.2,
            position=(
                (
                    (240 if uiscale is bui.UIScale.SMALL else 225)
                    + sub_scroll_width * 0.5
                ),
                v + sub_scroll_height * 0.5,
            ),
            glow_type='uniform',
        )

        self._favorite_selected = None
        self._refresh_favorites()

    def _no_favorite_selected_error(self) -> None:
        bui.screenmessage(
            bui.Lstr(resource='nothingIsSelectedErrorText'), color=(1, 0, 0)
        )
        bui.getsound('error').play()

    def _on_favorites_connect_press(self) -> None:
        if self._favorite_selected is None:
            self._no_favorite_selected_error()

        else:
            config = bui.app.config['Saved Servers'][self._favorite_selected]
            _HostLookupThread(
                name=config['addr'],
                port=config['port'],
                call=bui.WeakCall(self._host_lookup_result),
            ).start()

    def _on_favorites_edit_press(self) -> None:
        if self._favorite_selected is None:
            self._no_favorite_selected_error()
            return

        c_width = 600
        c_height = 310
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._favorite_edit_window = cnt = bui.containerwidget(
            scale=(
                1.8
                if uiscale is bui.UIScale.SMALL
                else 1.55 if uiscale is bui.UIScale.MEDIUM else 1.0
            ),
            size=(c_width, c_height),
            transition='in_scale',
        )

        bui.textwidget(
            parent=cnt,
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='editText'),
            color=(0.6, 1.0, 0.6),
            maxwidth=c_width * 0.8,
            position=(c_width * 0.5, c_height - 60),
        )

        bui.textwidget(
            parent=cnt,
            position=(c_width * 0.2 - 15, c_height - 120),
            color=(0.6, 1.0, 0.6),
            scale=1.0,
            size=(0, 0),
            maxwidth=60,
            h_align='right',
            v_align='center',
            text=bui.Lstr(resource='nameText'),
        )

        self._party_edit_name_text = bui.textwidget(
            parent=cnt,
            size=(c_width * 0.7, 40),
            h_align='left',
            v_align='center',
            text=bui.app.config['Saved Servers'][self._favorite_selected][
                'name'
            ],
            editable=True,
            description=bui.Lstr(resource='nameText'),
            position=(c_width * 0.2, c_height - 140),
            autoselect=True,
            maxwidth=c_width * 0.6,
            max_chars=200,
        )

        bui.textwidget(
            parent=cnt,
            position=(c_width * 0.2 - 15, c_height - 180),
            color=(0.6, 1.0, 0.6),
            scale=1.0,
            size=(0, 0),
            maxwidth=60,
            h_align='right',
            v_align='center',
            text=bui.Lstr(resource='gatherWindow.' 'manualAddressText'),
        )

        self._party_edit_addr_text = bui.textwidget(
            parent=cnt,
            size=(c_width * 0.4, 40),
            h_align='left',
            v_align='center',
            text=bui.app.config['Saved Servers'][self._favorite_selected][
                'addr'
            ],
            editable=True,
            description=bui.Lstr(resource='gatherWindow.manualAddressText'),
            position=(c_width * 0.2, c_height - 200),
            autoselect=True,
            maxwidth=c_width * 0.35,
            max_chars=200,
        )

        bui.textwidget(
            parent=cnt,
            position=(c_width * 0.7 - 10, c_height - 180),
            color=(0.6, 1.0, 0.6),
            scale=1.0,
            size=(0, 0),
            maxwidth=45,
            h_align='right',
            v_align='center',
            text=bui.Lstr(resource='gatherWindow.' 'portText'),
        )

        self._party_edit_port_text = bui.textwidget(
            parent=cnt,
            size=(c_width * 0.2, 40),
            h_align='left',
            v_align='center',
            text=str(
                bui.app.config['Saved Servers'][self._favorite_selected]['port']
            ),
            editable=True,
            description=bui.Lstr(resource='gatherWindow.portText'),
            position=(c_width * 0.7, c_height - 200),
            autoselect=True,
            maxwidth=c_width * 0.2,
            max_chars=6,
        )
        cbtn = bui.buttonwidget(
            parent=cnt,
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=bui.Call(
                lambda c: bui.containerwidget(edit=c, transition='out_scale'),
                cnt,
            ),
            size=(180, 60),
            position=(30, 30),
            autoselect=True,
        )
        okb = bui.buttonwidget(
            parent=cnt,
            label=bui.Lstr(resource='saveText'),
            size=(180, 60),
            position=(c_width - 230, 30),
            on_activate_call=bui.Call(self._edit_saved_party),
            autoselect=True,
        )
        bui.widget(edit=cbtn, right_widget=okb)
        bui.widget(edit=okb, left_widget=cbtn)
        bui.containerwidget(edit=cnt, cancel_button=cbtn, start_button=okb)

    def _edit_saved_party(self) -> None:
        server = self._favorite_selected
        if self._favorite_selected is None:
            self._no_favorite_selected_error()
            return
        if not self._party_edit_name_text or not self._party_edit_addr_text:
            return
        new_name_raw = cast(
            str, bui.textwidget(query=self._party_edit_name_text)
        )
        new_addr_raw = cast(
            str, bui.textwidget(query=self._party_edit_addr_text)
        )
        new_port_raw = cast(
            str, bui.textwidget(query=self._party_edit_port_text)
        )
        bui.app.config['Saved Servers'][server]['name'] = new_name_raw
        bui.app.config['Saved Servers'][server]['addr'] = new_addr_raw
        try:
            bui.app.config['Saved Servers'][server]['port'] = int(new_port_raw)
        except ValueError:
            # Notify about incorrect port? I'm lazy; simply leave old value.
            pass
        bui.app.config.commit()
        bui.getsound('gunCocking').play()
        self._refresh_favorites()

        bui.containerwidget(
            edit=self._favorite_edit_window, transition='out_scale'
        )

    def _on_favorite_delete_press(self) -> None:
        from bauiv1lib import confirm

        if self._favorite_selected is None:
            self._no_favorite_selected_error()
            return
        confirm.ConfirmWindow(
            bui.Lstr(
                resource='gameListWindow.deleteConfirmText',
                subs=[
                    (
                        '${LIST}',
                        bui.app.config['Saved Servers'][
                            self._favorite_selected
                        ]['name'],
                    )
                ],
            ),
            self._delete_saved_party,
            450,
            150,
        )

    def _delete_saved_party(self) -> None:
        if self._favorite_selected is None:
            self._no_favorite_selected_error()
            return
        config = bui.app.config['Saved Servers']
        del config[self._favorite_selected]
        self._favorite_selected = None
        bui.app.config.commit()
        bui.getsound('shieldDown').play()
        self._refresh_favorites()

    def _on_favorite_select(self, server: str) -> None:
        self._favorite_selected = server

    def _refresh_favorites(self) -> None:
        assert self._columnwidget is not None
        for child in self._columnwidget.get_children():
            child.delete()
        t_scale = 1.6

        config = bui.app.config
        if 'Saved Servers' in config:
            servers = config['Saved Servers']

        else:
            servers = []

        assert self._favorites_scroll_width is not None
        assert self._favorites_connect_button is not None

        bui.textwidget(
            edit=self._no_parties_added_text,
            text='',
        )
        num_of_fav = 0
        for i, server in enumerate(servers):
            txt = bui.textwidget(
                parent=self._columnwidget,
                size=(self._favorites_scroll_width / t_scale, 30),
                selectable=True,
                color=(1.0, 1, 0.4),
                always_highlight=True,
                on_select_call=bui.Call(self._on_favorite_select, server),
                on_activate_call=self._favorites_connect_button.activate,
                text=(
                    config['Saved Servers'][server]['name']
                    if config['Saved Servers'][server]['name'] != ''
                    else config['Saved Servers'][server]['addr']
                    + ' '
                    + str(config['Saved Servers'][server]['port'])
                ),
                h_align='left',
                v_align='center',
                corner_scale=t_scale,
                maxwidth=(self._favorites_scroll_width / t_scale) * 0.93,
            )
            if i == 0:
                bui.widget(edit=txt, up_widget=self._favorites_text)
                self._favorite_selected = server
            bui.widget(
                edit=txt,
                left_widget=self._favorites_connect_button,
                right_widget=txt,
            )
            num_of_fav = num_of_fav + 1

        # If there's no servers, allow selecting out of the scroll area
        bui.containerwidget(
            edit=self._scrollwidget,
            claims_left_right=bool(servers),
            claims_up_down=bool(servers),
        )
        assert self._scrollwidget is not None
        bui.widget(
            edit=self._scrollwidget,
            up_widget=self._favorites_text,
            left_widget=self._favorites_connect_button,
        )
        if num_of_fav == 0:
            bui.textwidget(
                edit=self._no_parties_added_text,
                text=bui.Lstr(resource='gatherWindow.noPartiesAddedText'),
            )

    @override
    def on_deactivate(self) -> None:
        self._access_check_timer = None

    def _connect(
        self, textwidget: bui.Widget, port_textwidget: bui.Widget
    ) -> None:
        addr = cast(str, bui.textwidget(query=textwidget))
        if addr == '':
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        try:
            port = int(cast(str, bui.textwidget(query=port_textwidget)))
        except ValueError:
            port = -1
        if port > 65535 or port < 0:
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidPortErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        _HostLookupThread(
            name=addr, port=port, call=bui.WeakCall(self._host_lookup_result)
        ).start()

    def _save_server(
        self, textwidget: bui.Widget, port_textwidget: bui.Widget
    ) -> None:
        addr = cast(str, bui.textwidget(query=textwidget))
        if addr == '':
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        try:
            port = int(cast(str, bui.textwidget(query=port_textwidget)))
        except ValueError:
            port = -1
        if port > 65535 or port < 0:
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidPortErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return
        config = bui.app.config

        if addr:
            if not isinstance(config.get('Saved Servers'), dict):
                config['Saved Servers'] = {}
            config['Saved Servers'][f'{addr}@{port}'] = {
                'addr': addr,
                'port': port,
                'name': addr,
            }
            config.commit()
            bui.getsound('gunCocking').play()
            bui.screenmessage(
                bui.Lstr(
                    resource='addedToFavoritesText', subs=[('${NAME}', addr)]
                ),
                color=(0, 1, 0),
            )
        else:
            bui.screenmessage(
                bui.Lstr(resource='internal.invalidAddressErrorText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()

    def _host_lookup_result(
        self, resolved_address: str | None, port: int
    ) -> None:
        if resolved_address is None:
            bui.screenmessage(
                bui.Lstr(resource='internal.unableToResolveHostText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
        else:
            # Store for later.
            config = bui.app.config
            config['Last Manual Party Connect Address'] = resolved_address
            config['Last Manual Party Connect Port'] = port
            config.commit()

            # Store UI location to return to when done.
            if bs.app.classic is not None:
                bs.app.classic.save_ui_state()

            bs.connect_to_party(resolved_address, port=port)

    def _run_addr_fetch(self) -> None:
        try:
            # FIXME: Update this to work with IPv6.
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(('8.8.8.8', 80))
            val = sock.getsockname()[0]
            sock.close()
            bui.pushcall(
                bui.Call(
                    _safe_set_text,
                    self._checking_state_text,
                    val,
                ),
                from_other_thread=True,
            )
        except Exception as exc:
            from efro.error import is_udp_communication_error

            if is_udp_communication_error(exc):
                bui.pushcall(
                    bui.Call(
                        _safe_set_text,
                        self._checking_state_text,
                        bui.Lstr(resource='gatherWindow.' 'noConnectionText'),
                        False,
                    ),
                    from_other_thread=True,
                )
            else:
                bui.pushcall(
                    bui.Call(
                        _safe_set_text,
                        self._checking_state_text,
                        bui.Lstr(
                            resource='gatherWindow.' 'addressFetchErrorText'
                        ),
                        False,
                    ),
                    from_other_thread=True,
                )
                logging.exception('Error in AddrFetchThread.')

    def _on_show_my_address_button_press(
        self, v2: float, container: bui.Widget | None, c_width: float
    ) -> None:
        if not container:
            return

        tscl = 0.85
        tspc = 25

        bui.getsound('swish').play()
        bui.textwidget(
            parent=container,
            position=(c_width * 0.5 - 10, v2),
            color=(0.6, 1.0, 0.6),
            scale=tscl,
            size=(0, 0),
            maxwidth=c_width * 0.45,
            flatness=1.0,
            h_align='right',
            v_align='center',
            text=bui.Lstr(
                resource='gatherWindow.' 'manualYourLocalAddressText'
            ),
        )
        self._checking_state_text = bui.textwidget(
            parent=container,
            position=(c_width * 0.5, v2),
            color=(0.5, 0.5, 0.5),
            scale=tscl,
            size=(0, 0),
            maxwidth=c_width * 0.45,
            flatness=1.0,
            h_align='left',
            v_align='center',
            text=bui.Lstr(resource='gatherWindow.' 'checkingText'),
        )

        Thread(target=self._run_addr_fetch).start()

        v2 -= tspc
        bui.textwidget(
            parent=container,
            position=(c_width * 0.5 - 10, v2),
            color=(0.6, 1.0, 0.6),
            scale=tscl,
            size=(0, 0),
            maxwidth=c_width * 0.45,
            flatness=1.0,
            h_align='right',
            v_align='center',
            text=bui.Lstr(
                resource='gatherWindow.' 'manualYourAddressFromInternetText'
            ),
        )

        t_addr = bui.textwidget(
            parent=container,
            position=(c_width * 0.5, v2),
            color=(0.5, 0.5, 0.5),
            scale=tscl,
            size=(0, 0),
            maxwidth=c_width * 0.45,
            h_align='left',
            v_align='center',
            flatness=1.0,
            text=bui.Lstr(resource='gatherWindow.' 'checkingText'),
        )
        v2 -= tspc
        bui.textwidget(
            parent=container,
            position=(c_width * 0.5 - 10, v2),
            color=(0.6, 1.0, 0.6),
            scale=tscl,
            size=(0, 0),
            maxwidth=c_width * 0.45,
            flatness=1.0,
            h_align='right',
            v_align='center',
            text=bui.Lstr(
                resource='gatherWindow.' 'manualJoinableFromInternetText'
            ),
        )

        t_accessible = bui.textwidget(
            parent=container,
            position=(c_width * 0.5, v2),
            color=(0.5, 0.5, 0.5),
            scale=tscl,
            size=(0, 0),
            maxwidth=c_width * 0.45,
            flatness=1.0,
            h_align='left',
            v_align='center',
            text=bui.Lstr(resource='gatherWindow.' 'checkingText'),
        )
        v2 -= 28
        t_accessible_extra = bui.textwidget(
            parent=container,
            position=(c_width * 0.5, v2),
            color=(1, 0.5, 0.2),
            scale=0.7,
            size=(0, 0),
            maxwidth=c_width * 0.9,
            flatness=1.0,
            h_align='center',
            v_align='center',
            text='',
        )

        self._doing_access_check = False
        self._access_check_count = 0  # Cap our refreshes eventually.
        self._access_check_timer = bui.AppTimer(
            10.0,
            bui.WeakCall(
                self._access_check_update,
                t_addr,
                t_accessible,
                t_accessible_extra,
            ),
            repeat=True,
        )

        # Kick initial off.
        self._access_check_update(t_addr, t_accessible, t_accessible_extra)
        if self._check_button:
            self._check_button.delete()

    def _access_check_update(
        self,
        t_addr: bui.Widget,
        t_accessible: bui.Widget,
        t_accessible_extra: bui.Widget,
    ) -> None:
        assert bui.app.classic is not None
        # If we don't have an outstanding query, start one..
        assert self._doing_access_check is not None
        assert self._access_check_count is not None
        if not self._doing_access_check and self._access_check_count < 100:
            self._doing_access_check = True
            self._access_check_count += 1
            self._t_addr = t_addr
            self._t_accessible = t_accessible
            self._t_accessible_extra = t_accessible_extra
            bui.app.classic.master_server_v1_get(
                'bsAccessCheck',
                {'b': bui.app.env.engine_build_number},
                callback=bui.WeakCall(self._on_accessible_response),
            )

    def _on_accessible_response(self, data: dict[str, Any] | None) -> None:
        t_addr = self._t_addr
        t_accessible = self._t_accessible
        t_accessible_extra = self._t_accessible_extra
        self._doing_access_check = False
        color_bad = (1, 1, 0)
        color_good = (0, 1, 0)
        if data is None or 'address' not in data or 'accessible' not in data:
            if t_addr:
                bui.textwidget(
                    edit=t_addr,
                    text=bui.Lstr(resource='gatherWindow.' 'noConnectionText'),
                    color=color_bad,
                )
            if t_accessible:
                bui.textwidget(
                    edit=t_accessible,
                    text=bui.Lstr(resource='gatherWindow.' 'noConnectionText'),
                    color=color_bad,
                )
            if t_accessible_extra:
                bui.textwidget(
                    edit=t_accessible_extra, text='', color=color_bad
                )
            return
        if t_addr:
            bui.textwidget(edit=t_addr, text=data['address'], color=color_good)
        if t_accessible:
            if data['accessible']:
                bui.textwidget(
                    edit=t_accessible,
                    text=bui.Lstr(
                        resource='gatherWindow.' 'manualJoinableYesText'
                    ),
                    color=color_good,
                )
                if t_accessible_extra:
                    bui.textwidget(
                        edit=t_accessible_extra, text='', color=color_good
                    )
            else:
                bui.textwidget(
                    edit=t_accessible,
                    text=bui.Lstr(
                        resource='gatherWindow.'
                        'manualJoinableNoWithAsteriskText'
                    ),
                    color=color_bad,
                )
                if t_accessible_extra:
                    bui.textwidget(
                        edit=t_accessible_extra,
                        text=bui.Lstr(
                            resource='gatherWindow.'
                            'manualRouterForwardingText',
                            subs=[
                                ('${PORT}', str(bs.get_game_port())),
                            ],
                        ),
                        color=color_bad,
                    )
