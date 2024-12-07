# Released under the MIT License. See LICENSE for details.
#
"""Provides a window which shows info about resource types."""

from __future__ import annotations

from typing import override, TYPE_CHECKING, assert_never

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Literal


class ResourceTypeInfoWindow(PopupWindow):
    """Popup window providing info about resource types."""

    def __init__(
        self,
        resource_type: Literal['tickets', 'tokens', 'trophies', 'xp'],
        origin_widget: bui.Widget,
    ):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        self._transitioning_out = False
        self._width = 570
        self._height = 350
        bg_color = (0.5, 0.4, 0.6)
        super().__init__(
            size=(self._width, self._height),
            toolbar_visibility='inherit',
            scale=scale,
            bg_color=bg_color,
            position=origin_widget.get_screen_space_center(),
            edge_buffer_scale=4.0,
        )
        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(40, self._height - 40),
            size=(50, 50),
            scale=0.7,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        if resource_type == 'tickets':
            rdesc = 'Will describe tickets.'
        elif resource_type == 'tokens':
            rdesc = 'Will describe tokens.'
        elif resource_type == 'trophies':
            rdesc = 'Will show trophies & league rankings.'
        elif resource_type == 'xp':
            rdesc = 'Will describe xp/levels.'
        else:
            assert_never(resource_type)

        bui.textwidget(
            parent=self.root_widget,
            h_align='center',
            v_align='center',
            size=(0, 0),
            position=(self._width * 0.5, self._height * 0.5),
            text=(f'UNDER CONSTRUCTION.\n({rdesc})'),
        )

    def _on_cancel_press(self) -> None:
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()
