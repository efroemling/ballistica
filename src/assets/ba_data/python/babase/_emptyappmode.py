# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

# from bacommon.app import AppExperience

import _babase
from babase._appmode import AppMode
from babase._appintent import AppIntentExec, AppIntentDefault

if TYPE_CHECKING:
    from babase import AppIntent


# ba_meta export babase.AppMode
class EmptyAppMode(AppMode):
    """An AppMode that does not do much at all.

    :meta private:
    """

    @override
    @classmethod
    def can_handle_intent(cls, intent: AppIntent) -> bool:
        # We support default and exec intents currently.
        return isinstance(intent, AppIntentExec | AppIntentDefault)

    @override
    def handle_intent(self, intent: AppIntent) -> None:
        if isinstance(intent, AppIntentExec):
            _babase.empty_app_mode_handle_app_intent_exec(intent.code)
            return
        assert isinstance(intent, AppIntentDefault)
        _babase.empty_app_mode_handle_app_intent_default()

    @override
    def on_activate(self) -> None:
        # Let the native layer do its thing.
        _babase.empty_app_mode_activate()

    @override
    def on_deactivate(self) -> None:
        # Let the native layer do its thing.
        _babase.empty_app_mode_deactivate()
