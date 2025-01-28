# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bacommon.app import AppExperience
    from babase._appintent import AppIntent


class AppMode:
    """A high level mode for the app.

    Category: **App Classes**

    """

    @classmethod
    def get_app_experience(cls) -> AppExperience:
        """Return the overall experience provided by this mode."""
        raise NotImplementedError('AppMode subclasses must override this.')

    @classmethod
    def can_handle_intent(cls, intent: AppIntent) -> bool:
        """Return whether this mode can handle the provided intent.

        For this to return True, the AppMode must claim to support the
        provided intent (via its _can_handle_intent() method) AND the
        AppExperience associated with the AppMode must be supported by
        the current app and runtime environment.
        """
        # TODO: check AppExperience against current environment.
        return cls._can_handle_intent(intent)

    @classmethod
    def _can_handle_intent(cls, intent: AppIntent) -> bool:
        """Return whether our mode can handle the provided intent.

        AppModes should override this to communicate what they can
        handle. Note that AppExperience does not have to be considered
        here; that is handled automatically by the can_handle_intent()
        call.
        """
        raise NotImplementedError('AppMode subclasses must override this.')

    def handle_intent(self, intent: AppIntent) -> None:
        """Handle an intent."""
        raise NotImplementedError('AppMode subclasses must override this.')

    def on_activate(self) -> None:
        """Called when the mode is being activated."""

    def on_deactivate(self) -> None:
        """Called when the mode is being deactivated."""

    def on_app_active_changed(self) -> None:
        """Called when ba*.app.active changes while this mode is active.

        The app-mode may want to take action such as pausing a running
        game in such cases.
        """
