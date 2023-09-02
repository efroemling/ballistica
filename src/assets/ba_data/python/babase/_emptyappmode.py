# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

from bacommon.app import AppExperience

import _babase
from babase._appmode import AppMode
from babase._appintent import AppIntentExec, AppIntentDefault

if TYPE_CHECKING:
    from babase import AppIntent


class EmptyAppMode(AppMode):
    """An empty app mode that can be used as a fallback/etc."""

    @classmethod
    def get_app_experience(cls) -> AppExperience:
        return AppExperience.EMPTY

    @classmethod
    def _supports_intent(cls, intent: AppIntent) -> bool:
        # We support default and exec intents currently.
        return isinstance(intent, AppIntentExec | AppIntentDefault)

    def handle_intent(self, intent: AppIntent) -> None:
        if isinstance(intent, AppIntentExec):
            _babase.empty_app_mode_handle_intent_exec(intent.code)
            return
        assert isinstance(intent, AppIntentDefault)
        _babase.empty_app_mode_handle_intent_default()

    def on_activate(self) -> None:
        # Let the native layer do its thing.
        _babase.on_empty_app_mode_activate()

    def on_deactivate(self) -> None:
        # Let the native layer do its thing.
        _babase.on_empty_app_mode_deactivate()
