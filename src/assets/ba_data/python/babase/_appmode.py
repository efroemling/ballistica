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
        """Called when the mode is becoming the active one fro the app."""

    def on_deactivate(self) -> None:
        """Called when the mode stops being the active one for the app.

        Note: On platforms where the app is explicitly exited (such as
        desktop PC) this will also be called at app shutdown.

        To best cover both mobile and desktop style platforms, actions
        such as saving state should generally happen in response to both
        on_deactivate() and on_app_active_changed() (when active is
        False).
        """

    def on_app_active_changed(self) -> None:
        """Called when ba*.app.active changes while in this app-mode.

        Active state becomes false when the app is hidden, minimized,
        backgrounded, etc. The app-mode may want to take action such as
        pausing a running game or saving state when this occurs.

        Note: On platforms such as mobile where apps get suspended and
        later silently terminated by the OS, this is likely to be the
        last reliable place to save state/etc.

        To best cover both mobile and desktop style platforms, actions
        such as saving state should generally happen in response to both
        on_deactivate() and on_app_active_changed() (when active is
        False).
        """
