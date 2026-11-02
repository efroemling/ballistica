# Released under the MIT License. See LICENSE for details.
#
"""UI for the local-network permission (Android 17+).

Android 17 requires a runtime permission for any local-network traffic
(LAN scanning, hosting, joining by address). Everywhere else the
permission always reads as granted, so none of this UI ever shows.
"""

from enum import Enum
from typing import TYPE_CHECKING, assert_never

import bauiv1 as bui
from bauiv1 import _classicassets, _commonassets

if TYPE_CHECKING:
    from typing import Callable

# How often UI showing permission state re-checks it. The check reads a
# cached native value (Android pushes changes to it), so it's cheap.
UPDATE_INTERVAL = 1.0

WARNING_COLOR = (1.0, 0.85, 0.2)

# Leads warning text. (Two spaces; the emoji's advance renders narrow,
# so one looks cramped.)
WARNING_PREFIX = '⚠️  '

# Vertical room UI should leave for a LocalNetworkPermissionWarning.
WARNING_HEIGHT = 70.0


def local_network_permission_missing() -> bool:
    """Whether we currently lack local-network permission."""
    return (
        get_local_network_permission_state()
        is not LocalNetworkPermissionState.GRANTED
    )


class LocalNetworkPermissionState(Enum):
    """Where we stand on the local-network permission."""

    GRANTED = 'granted'

    #: Not granted; requesting it will show a system prompt.
    REQUESTABLE = 'requestable'

    #: Denied for good; only system settings can grant it now.
    DENIED = 'denied'


def get_local_network_permission_state() -> LocalNetworkPermissionState:
    """Return our current local-network permission state."""
    if bui.have_permission(bui.Permission.LOCAL_NETWORK):
        return LocalNetworkPermissionState.GRANTED
    if bui.can_request_permission(bui.Permission.LOCAL_NETWORK):
        return LocalNetworkPermissionState.REQUESTABLE
    return LocalNetworkPermissionState.DENIED


def request_local_network_permission() -> None:
    """Ask the OS for the local-network permission."""
    bui.request_permission(bui.Permission.LOCAL_NETWORK)


def show_local_network_permission_dialog(
    *,
    origin_widget: bui.Widget | None,
    on_continue: Callable[[], None],
) -> None:
    """Explain that local network play needs permission.

    Offers to request it (then just closes; whatever UI is showing
    picks up the change) or to continue without it via
    ``on_continue``. If the permission can no longer be requested, it
    explains how to enable it in settings and then continues.
    """
    # pylint: disable=cyclic-import
    from bauiv1lib.confirm import ConfirmWindow

    state = get_local_network_permission_state()
    if state is LocalNetworkPermissionState.GRANTED:
        on_continue()
        return
    if state is LocalNetworkPermissionState.REQUESTABLE:
        ConfirmWindow(
            text=_classicassets.strings.gather.local_network_permission_prompt,
            # Request goes on the left (ConfirmWindow's cancel slot) and
            # starts selected; 'Not Now' on the right carries on.
            cancel_action=request_local_network_permission,
            action=on_continue,
            cancel_is_selected=True,
            cancel_text=(
                _classicassets.strings.gather.request_local_network_permission
            ),
            ok_text=_commonassets.strings.actions.not_now,
            width=500,
            height=150,
            origin_widget=origin_widget,
        )
        return
    if state is LocalNetworkPermissionState.DENIED:
        ConfirmWindow(
            text=_settings_instructions(),
            action=on_continue,
            cancel_button=False,
            width=500,
            height=150,
            origin_widget=origin_widget,
        )
        return
    assert_never(state)


def _settings_instructions() -> bui.LangStr:
    # (Wraps to two lines at display; set in the string's workspace.)
    return _classicassets.strings.gather.local_network_settings_instructions(
        app_name=bui.appnameupper()
    )


def _warning_text(
    text: bui.LangStr, *, lines: int | None = None
) -> bui.LangStr:
    """Prefix text with our warning icon.

    Joining doesn't carry the inner string's line-wrapping through to
    the result, so pass ``lines`` to re-wrap the whole thing to that
    many lines.
    """
    joined = bui.LangStr.join([bui.LangStr.from_text(WARNING_PREFIX), text])
    if lines is not None:
        return bui.LangStr(joined.to_json(), wrap=(lines, lines, None))
    return joined


class LocalNetworkPermissionWarning:
    """Warning text (plus a request button if possible) shown in UI
    that needs local network access while we don't have it.

    Re-checks the permission every ``UPDATE_INTERVAL`` seconds and
    updates (or clears) itself to match.
    """

    def __init__(
        self,
        *,
        parent: bui.Widget,
        position: tuple[float, float],
        width: float,
        idprefix: str,
    ):
        self._parent = parent
        self._position = position
        self._width = width
        self._idprefix = idprefix
        self._state: LocalNetworkPermissionState | None = None
        self._text: bui.Widget | None = None
        self._button: bui.Widget | None = None
        self._update_timer = bui.AppTimer(
            UPDATE_INTERVAL, bui.WeakCallStrict(self._update), repeat=True
        )
        self._update()

    def _clear(self) -> None:
        for widget in (self._text, self._button):
            if widget:
                widget.delete()
        self._text = self._button = None

    def _update(self) -> None:
        if not self._parent:
            return
        state = get_local_network_permission_state()
        if state is self._state:
            return
        self._state = state
        self._clear()
        x, y = self._position
        gstrs = _classicassets.strings.gather
        if state is LocalNetworkPermissionState.GRANTED:
            return
        if state is LocalNetworkPermissionState.REQUESTABLE:
            button_width = 240.0
            text_width = self._width - button_width - 20.0
            self._text = bui.textwidget(
                parent=self._parent,
                position=(x - self._width * 0.5 + text_width * 0.5, y),
                size=(0, 0),
                h_align='center',
                v_align='center',
                color=WARNING_COLOR,
                scale=0.9,
                maxwidth=text_width,
                text=_warning_text(gstrs.local_network_permission_needed),
            )
            self._button = bui.buttonwidget(
                parent=self._parent,
                id=f'{self._idprefix}|requestlocalnetwork',
                position=(
                    x + self._width * 0.5 - button_width,
                    y - 20.0,
                ),
                size=(button_width, 40.0),
                autoselect=True,
                color=(0.6, 0.53, 0.2),
                textcolor=(1.0, 1.0, 0.8),
                label=gstrs.request_local_network_permission,
                on_activate_call=request_local_network_permission,
            )
            return
        if state is LocalNetworkPermissionState.DENIED:
            self._text = bui.textwidget(
                parent=self._parent,
                position=(x, y),
                size=(0, 0),
                h_align='center',
                v_align='center',
                color=WARNING_COLOR,
                scale=0.8,
                maxwidth=self._width,
                text=_warning_text(_settings_instructions(), lines=2),
            )
            return
        assert_never(state)
