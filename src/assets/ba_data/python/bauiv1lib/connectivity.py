# Released under the MIT License. See LICENSE for details.
#
"""UI functionality related to master-server connectivity."""

from __future__ import annotations

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
    # We do, however, push this call instead of calling it immediately
    # so as to be consistent with the waiting path.
    if plus.cloud.connected:
        bui.pushcall(on_connected)
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
            text='',
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

        plus = bui.app.plus
        assert plus is not None

        if plus.cloud.connected:
            self._connected()
            return

        # Show what connectivity is up to if we don't have any published
        # zone-pings yet (or if we do but there's no transport state to
        # show yet).
        if not bui.app.net.zone_pings or not bui.app.net.transport_state:
            infotext = bui.app.net.connectivity_state
        else:
            infotext = bui.app.net.transport_state
        if infotext != self._info_text_str:
            self._info_text_str = infotext
            bui.textwidget(edit=self._info_text, text=infotext)

    def _connected(self) -> None:
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        # Show 'connected.' and kill the spinner for the brief moment
        # we're visible on our way out.
        bui.textwidget(
            edit=self._info_text, text=bui.Lstr(resource='remote_app.connected')
        )
        if self._spinner:
            self._spinner.delete()

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
