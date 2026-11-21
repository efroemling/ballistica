# Released under the MIT License. See LICENSE for details.
#
"""Provides the Remote app-mode."""

from typing import TYPE_CHECKING, override

import _baremote
import babase
from babase import AppMode, AppIntentDefault

# The touch controls' art comes from the classic package for now (see
# _make_base_asset_set).
from bauiv1 import _classicassets

from baremote._client import RemoteClient

if TYPE_CHECKING:
    from babase import AppIntent, AppModeConfig


# ba_meta export babase.AppMode
class RemoteAppMode(AppMode):
    """The app-mode for using a device as a game controller.

    This turns a phone or tablet into a controller for a game on the
    same network; it is the future home of the BombSquad Remote app (in
    development for 1.9).

    Currently a placeholder with no ui of its own: it connects to the
    first game it finds, and while connected the device's touchscreen
    controls (or a keyboard or gamepad) drive a player in that game.
    Progress is reported as screen-messages and ``ba.net`` log lines. It
    is not in the project's default app-modes, so the app never selects
    it on its own; it can be switched to manually via the dev-console's
    AppModes tab.
    """

    #: Testing hook -- if set, the client queries only these (address,
    #: port) pairs instead of broadcasting, so a test run can't latch
    #: onto some other game on the network. Takes effect on the next
    #: activation.
    test_scan_targets: list[tuple[str, int]] | None = None

    #: Testing hook -- send random presses instead of real input (for
    #: headless runs, which have no input devices). Takes effect on the
    #: next activation.
    test_random_input: bool = False

    def __init__(self) -> None:
        super().__init__()
        self._client: RemoteClient | None = None

    @override
    @classmethod
    def can_handle_intent(cls, intent: AppIntent) -> bool:
        return isinstance(intent, AppIntentDefault)

    @override
    def handle_intent(self, intent: AppIntent) -> None:
        assert isinstance(intent, AppIntentDefault)

    @override
    def on_activate(self, config: AppModeConfig) -> None:
        del config  # Unused.
        babase.set_base_asset_set(_make_base_asset_set())
        _baremote.remote_app_mode_activate()
        assert self._client is None
        self._client = RemoteClient(
            scan_targets=self.test_scan_targets,
            random_input=self.test_random_input,
        )
        self._client.start()

    @override
    def on_deactivate(self) -> None:
        if self._client is not None:
            self._client.stop()
            self._client = None
        _baremote.remote_app_mode_deactivate()


def _make_base_asset_set() -> babase.BaseAssetSet:
    """Build the art we supply for base's draws: the touch controls.

    Everything else stays at its engine placeholder (we draw no scenes).
    This borrows classic's touch-control art; a lean remote app would
    want it in a small package of its own.
    """
    tex = _classicassets.textures
    msh = _classicassets.meshes
    assets = babase.BaseAssetSet()
    assets.action_buttons = tex.action_buttons
    assets.touch_arrows = tex.touch_arrows
    assets.touch_arrows_actions = tex.touch_arrows_actions
    assets.arrow = tex.arrow
    assets.action_button_bottom = msh.action_button_bottom
    assets.action_button_left = msh.action_button_left
    assets.action_button_right = msh.action_button_right
    assets.action_button_top = msh.action_button_top
    assets.arrow_back = msh.arrow_back
    assets.arrow_front = msh.arrow_front
    return assets
