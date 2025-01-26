# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for selecting maps in playlists."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable

    import bascenev1 as bs


class PlaylistMapSelectWindow(bui.MainWindow):
    """Window to select a map."""

    def __init__(
        self,
        gametype: type[bs.GameActivity],
        sessiontype: type[bs.Session],
        config: dict[str, Any],
        edit_info: dict[str, Any],
        completion_call: Callable[[dict[str, Any] | None, bui.MainWindow], Any],
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        select_get_more_maps_button: bool = False,
    ):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-positional-arguments

        from bascenev1 import get_filtered_map_name

        self._gametype = gametype
        self._sessiontype = sessiontype
        self._config = config
        self._completion_call = completion_call
        self._edit_info = edit_info
        self._maps: list[tuple[str, bui.Texture]] = []
        self._selected_get_more_maps = False
        try:
            self._previous_map = get_filtered_map_name(
                config['settings']['map']
            )
        except Exception:
            self._previous_map = ''

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 815 if uiscale is bui.UIScale.SMALL else 615
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        height = (
            420
            if uiscale is bui.UIScale.SMALL
            else 480 if uiscale is bui.UIScale.MEDIUM else 600
        )
        yoffs = -37 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                scale=(
                    2.3
                    if uiscale is bui.UIScale.SMALL
                    else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        self._cancel_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(38 + x_inset, height - 67 + yoffs),
            size=(140, 50),
            scale=0.9,
            text_scale=1.0,
            autoselect=True,
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=self.main_window_back,
        )

        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, height - 46 + yoffs),
            size=(0, 0),
            maxwidth=260,
            scale=1.1,
            text=bui.Lstr(
                resource='mapSelectTitleText',
                subs=[('${GAME}', self._gametype.get_display_string())],
            ),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )
        v = height - 70 + yoffs
        self._scroll_width = width - (80 + 2 * x_inset)
        self._scroll_height = height - (
            170 if uiscale is bui.UIScale.SMALL else 140
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(40 + x_inset, v - self._scroll_height),
            size=(self._scroll_width, self._scroll_height),
            border_opacity=0.4,
        )
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )
        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._subcontainer: bui.Widget | None = None
        self._refresh(select_get_more_maps_button=select_get_more_maps_button)

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull things out of self here; if we do it in the lambda we'll
        # keep ourself alive.
        gametype = self._gametype
        sessiontype = self._sessiontype
        config = self._config
        edit_info = self._edit_info
        completion_call = self._completion_call
        select_get_more_maps = self._selected_get_more_maps

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                gametype=gametype,
                sessiontype=sessiontype,
                config=config,
                edit_info=edit_info,
                completion_call=completion_call,
                select_get_more_maps_button=select_get_more_maps,
            )
        )

    def _refresh(self, select_get_more_maps_button: bool = False) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        from bascenev1 import (
            get_map_class,
            get_map_display_string,
        )

        assert bui.app.classic is not None
        store = bui.app.classic.store
        # Kill old.
        if self._subcontainer is not None:
            self._subcontainer.delete()

        mesh_opaque = bui.getmesh('level_select_button_opaque')
        mesh_transparent = bui.getmesh('level_select_button_transparent')

        self._maps = []
        map_list = self._gametype.get_supported_maps(self._sessiontype)
        map_list_sorted = list(map_list)
        map_list_sorted.sort()
        unowned_maps = store.get_unowned_maps()

        for mapname in map_list_sorted:
            # Disallow ones we don't own.
            if mapname in unowned_maps:
                continue
            map_tex_name = get_map_class(mapname).get_preview_texture_name()
            if map_tex_name is not None:
                try:
                    map_tex = bui.gettexture(map_tex_name)
                    self._maps.append((mapname, map_tex))
                except Exception:
                    print(f'Invalid map preview texture: "{map_tex_name}".')
            else:
                print('Error: no map preview texture for map:', mapname)

        count = len(self._maps)
        columns = 2
        rows = int(math.ceil(float(count) / columns))
        button_width = 220
        button_height = button_width * 0.5
        button_buffer_h = 16
        button_buffer_v = 19
        self._sub_width = self._scroll_width * 0.95
        self._sub_height = (
            5 + rows * (button_height + 2 * button_buffer_v) + 100
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
        )
        index = 0
        mask_texture = bui.gettexture('mapPreviewMask')
        h_offs = 130 if len(self._maps) == 1 else 0
        for y in range(rows):
            for x in range(columns):
                pos = (
                    x * (button_width + 2 * button_buffer_h)
                    + button_buffer_h
                    + h_offs,
                    self._sub_height
                    - (y + 1) * (button_height + 2 * button_buffer_v)
                    + 12,
                )
                btn = bui.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    size=(button_width, button_height),
                    autoselect=True,
                    texture=self._maps[index][1],
                    mask_texture=mask_texture,
                    mesh_opaque=mesh_opaque,
                    mesh_transparent=mesh_transparent,
                    label='',
                    color=(1, 1, 1),
                    on_activate_call=bui.Call(
                        self._select_with_delay, self._maps[index][0]
                    ),
                    position=pos,
                )
                if x == 0:
                    bui.widget(edit=btn, left_widget=self._cancel_button)
                if y == 0:
                    bui.widget(edit=btn, up_widget=self._cancel_button)
                if x == columns - 1:
                    bui.widget(
                        edit=btn,
                        right_widget=bui.get_special_widget('squad_button'),
                    )

                bui.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)
                if self._maps[index][0] == self._previous_map:
                    bui.containerwidget(
                        edit=self._subcontainer,
                        selected_child=btn,
                        visible_child=btn,
                    )
                name = get_map_display_string(self._maps[index][0])
                bui.textwidget(
                    parent=self._subcontainer,
                    text=name,
                    position=(pos[0] + button_width * 0.5, pos[1] - 12),
                    size=(0, 0),
                    scale=0.5,
                    maxwidth=button_width,
                    draw_controller=btn,
                    h_align='center',
                    v_align='center',
                    color=(0.8, 0.8, 0.8, 0.8),
                )
                index += 1

                if index >= count:
                    break
            if index >= count:
                break
        self._get_more_maps_button = btn = bui.buttonwidget(
            parent=self._subcontainer,
            size=(self._sub_width * 0.8, 60),
            position=(self._sub_width * 0.1, 30),
            label=bui.Lstr(resource='mapSelectGetMoreMapsText'),
            on_activate_call=self._on_store_press,
            color=(0.6, 0.53, 0.63),
            textcolor=(0.75, 0.7, 0.8),
            autoselect=True,
        )
        bui.widget(edit=btn, show_buffer_top=30, show_buffer_bottom=30)
        if select_get_more_maps_button:
            bui.containerwidget(
                edit=self._subcontainer, selected_child=btn, visible_child=btn
            )

    def _on_store_press(self) -> None:
        from bauiv1lib.account.signin import show_sign_in_prompt
        from bauiv1lib.store.browser import StoreBrowserWindow

        # No-op if we're not in control.
        if not self.main_window_has_control():
            return

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return

        self._selected_get_more_maps = True

        self.main_window_replace(
            StoreBrowserWindow(
                show_tab=StoreBrowserWindow.TabID.MAPS,
                origin_widget=self._get_more_maps_button,
                minimal_toolbars=True,
            )
        )

    def _select(self, map_name: str) -> None:

        # no-op if our underlying widget is dead or on its way out.
        if not self.main_window_has_control():
            return

        self._config['settings']['map'] = map_name
        self.main_window_back()

    def _select_with_delay(self, map_name: str) -> None:
        bui.lock_all_input()
        bui.apptimer(0.1, bui.unlock_all_input)
        bui.apptimer(0.1, bui.WeakCall(self._select, map_name))
