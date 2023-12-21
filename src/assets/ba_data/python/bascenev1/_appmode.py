# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

from bacommon.app import AppExperience
from babase import (
    app,
    AppMode,
    AppIntentExec,
    AppIntentDefault,
    invoke_main_menu,
)

import _bascenev1

if TYPE_CHECKING:
    from babase import AppIntent


class SceneV1AppMode(AppMode):
    """Our app-mode."""

    @classmethod
    def get_app_experience(cls) -> AppExperience:
        return AppExperience.MELEE

    @classmethod
    def _supports_intent(cls, intent: AppIntent) -> bool:
        # We support default and exec intents currently.
        return isinstance(intent, AppIntentExec | AppIntentDefault)

    def handle_intent(self, intent: AppIntent) -> None:
        if isinstance(intent, AppIntentExec):
            _bascenev1.handle_app_intent_exec(intent.code)
            return
        assert isinstance(intent, AppIntentDefault)
        _bascenev1.handle_app_intent_default()

    def on_activate(self) -> None:
        # Let the native layer do its thing.
        _bascenev1.on_app_mode_activate()

    def on_deactivate(self) -> None:
        # Let the native layer do its thing.
        _bascenev1.on_app_mode_deactivate()

    def on_app_active_changed(self) -> None:
        # If we've gone inactive, bring up the main menu, which has the
        # side effect of pausing the action (when possible).
        if not app.active:
            invoke_main_menu()
