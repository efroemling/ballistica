# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to master-server connectivity."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable, Any


class ConnectWindow(bui.Window):
    """Window for preparing to connect to a game.

    Shows progress while wrangling credentials, asks for password, or
    anything else necessary to prepare for a connection.
    """

    def __init__(
        self,
    ) -> None:
        self._width = 650
        self._height = 300
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
                parent=bui.get_special_widget('overlay_stack'),
            )
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.7),
            size=(0, 0),
            scale=1.2,
            h_align='center',
            v_align='center',
            text=bui.Lstr(resource='internal.connectingToPartyText'),
            maxwidth=self._width * 0.9,
        )

        self._spinner = bui.spinnerwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.54),
            style='bomb',
            size=48,
        )

        self._info_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.4),
            size=(0, 0),
            color=(0.6, 0.5, 0.6),
            flatness=1.0,
            shadow=0.0,
            scale=0.75,
            h_align='center',
            v_align='center',
            text='HELLO THERE',
            maxwidth=self._width * 0.9,
        )
        self._info_text_str = ''

        cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(50, 30),
            size=(150, 50),
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=self._cancel,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=cancel_button)
        self._update_timer = bui.AppTimer(
            0.113, bui.WeakCall(self._update), repeat=True
        )

    def _update(self) -> None:
        print('updating...')

    def _cancel(self) -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(
            edit=self._root_widget,
            transition=('out_scale'),
        )
