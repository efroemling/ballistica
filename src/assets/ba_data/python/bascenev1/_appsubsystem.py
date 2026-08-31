# Released under the MIT License. See LICENSE for details.
#
"""Provides the scene_v1 app subsystem."""

from typing import override

import babase

import _bascenev1


class SceneV1AppSubsystem(babase.AppSubsystem):
    """Consolidated scene_v1 state for the app.

    Access the single shared instance of this class via the
    :attr:`~babase.App.scene_v1` attr on the :class:`~babase.App`
    instance.
    """

    @override
    def reset(self) -> None:
        # Wipe any app-mode-supplied scene asset set (see
        # bascenev1.set_scene_asset_set). We run at every app-mode
        # switch, so this is what guarantees an incoming mode can never
        # inherit the outgoing one's art; the incoming mode supplies
        # its own as it activates.
        _bascenev1.clear_scene_asset_set_native()
