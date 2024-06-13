# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to master-server connectivity."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable, Any


def wait_for_connectivity(
    on_connected: Callable[[], Any],
    on_cancel: Callable[[], Any] | None = None,
) -> None:
    """Wait for the engine to establish a master-server connection.

    If need be, shows a window to keep the user informed of connectivity
    state and allows the user to cancel the operation. Note that canceling
    does not prevent the engine from continuing its attempt to establish
    connectivity; it simply cancels the operation that depends on it.
    """
    plus = bui.app.plus
    assert plus is not None

    # Quick-out: if we're already connected, don't bother with the UI.
    if plus.cloud.connected:
        on_connected()
        return

    WaitForConnectivityWindow(on_connected=on_connected, on_cancel=on_cancel)


class WaitForConnectivityWindow(bui.Window):
    """Window informing the user that the game is establishing connectivity."""

    def __init__(
        self,
        on_connected: Callable[[], Any],
        on_cancel: Callable[[], Any] | None,
    ) -> None:
        self._on_connected = on_connected
        self._on_cancel = on_cancel
        self._width = 650
        self._height = 300
        self._infos: list[str | bui.Lstr] = [
            'This can take a few moments, especially on first launch.',
            'Make sure your internet connection is working.',
        ]
        self._last_info_switch_time = time.monotonic()
        self._info_index = 0
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
                parent=bui.get_special_widget('overlay_stack'),
            )
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.65),
            size=(0, 0),
            scale=1.2,
            h_align='center',
            v_align='center',
            text='Locating nearest regional servers...',
            maxwidth=self._width * 0.9,
        )
        self._info_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.45),
            size=(0, 0),
            color=(0.7, 0.6, 0.7),
            flatness=1.0,
            scale=0.8,
            h_align='center',
            v_align='center',
            text=self._infos[0],
            maxwidth=self._width * 0.9,
        )
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
        now = time.monotonic()

        plus = bui.app.plus
        assert plus is not None

        if plus.cloud.connected:
            self._connected()
            return

        if now - self._last_info_switch_time > 5.0:
            self._info_index = (self._info_index + 1) % len(self._infos)
            bui.textwidget(
                edit=self._info_text, text=self._infos[self._info_index]
            )
            self._last_info_switch_time = now

    def _connected(self) -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(
            edit=self._root_widget,
            transition=('out_scale'),
        )
        bui.pushcall(self._on_connected)

    def _cancel(self) -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(
            edit=self._root_widget,
            transition=('out_scale'),
        )
        if self._on_cancel is not None:
            bui.pushcall(self._on_cancel)
