# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup window to view achievements."""

from __future__ import annotations

from typing import override

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui


class InboxWindow(PopupWindow):
    """Popup window to show account messages."""

    def __init__(
        self, position: tuple[float, float], scale: float | None = None
    ):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            )
        self._transitioning_out = False
        self._width = 450
        self._height = (
            300
            if uiscale is bui.UIScale.SMALL
            else 370 if uiscale is bui.UIScale.MEDIUM else 450
        )
        bg_color = (0.5, 0.4, 0.6)

        # creates our _root_widget
        super().__init__(
            position=position,
            size=(self._width, self._height),
            scale=scale,
            bg_color=bg_color,
            edge_buffer_scale=4.0,  # Try to keep button unobscured.
        )

        self._cancel_button = bui.buttonwidget(
            parent=self.root_widget,
            position=(50, self._height - 30),
            size=(50, 50),
            scale=0.5,
            label='',
            color=bg_color,
            on_activate_call=self._on_cancel_press,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        self._title_text = bui.textwidget(
            parent=self.root_widget,
            position=(self._width * 0.5, self._height - 20),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text='INBOX (UNDER CONSTRUCTION)',
            maxwidth=200,
            color=bui.app.ui_v1.title_color,
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self.root_widget,
            size=(self._width - 60, self._height - 70),
            position=(30, 30),
            capture_arrows=True,
            simple_culling_v=10,
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)

        bui.containerwidget(
            edit=self.root_widget, cancel_button=self._cancel_button
        )

        entries: list[str] = []
        incr = 20
        sub_width = self._width - 90
        sub_height = 40 + len(entries) * incr

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(sub_width, sub_height),
            background=False,
        )

        for i, entry in enumerate(entries):
            bui.textwidget(
                parent=self._subcontainer,
                position=(sub_width * 0.08 - 5, sub_height - 20 - incr * i),
                maxwidth=20,
                scale=0.5,
                flatness=1.0,
                shadow=0.0,
                text=entry,
                size=(0, 0),
                h_align='right',
                v_align='center',
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
