# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

from babase import AppMode, AppIntentExec, AppIntentDefault
import _bascenev1

if TYPE_CHECKING:
    from babase import AppIntent


class SceneV1AppMode(AppMode):
    """Our app-mode."""

    @classmethod
    def supports_intent(cls, intent: AppIntent) -> bool:
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
        _bascenev1.app_mode_activate()

    def on_deactivate(self) -> None:
        # Let the native layer do its thing.
        _bascenev1.app_mode_deactivate()
