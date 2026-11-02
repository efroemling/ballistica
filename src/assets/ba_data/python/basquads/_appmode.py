# Released under the MIT License. See LICENSE for details.
#
"""Provides the Squads app-mode."""

from typing import TYPE_CHECKING, override

import _basquads
from babase import AppMode, AppIntentDefault

if TYPE_CHECKING:
    from babase import AppIntent, AppModeConfig


# ba_meta export babase.AppMode
class SquadsAppMode(AppMode):
    """The app-mode for squads (in development for 1.9).

    Currently a scaffold. It is not in the project's default app-modes,
    so the app never selects it on its own; it can be switched to
    manually via the dev-console's AppModes tab.
    """

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
        _basquads.squads_app_mode_activate()

    @override
    def on_deactivate(self) -> None:
        _basquads.squads_app_mode_deactivate()
