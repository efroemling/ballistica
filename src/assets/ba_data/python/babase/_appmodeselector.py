# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babase._appintent import AppIntent
    from babase._appmode import AppMode


class AppModeSelector:
    """Defines which AppModes to use to handle given AppIntents.

    Category: **App Classes**

    The app calls an instance of this class when passed an AppIntent to
    determine which AppMode to use to handle the intent. Plugins or
    spinoff projects can modify high level app behavior by replacing or
    modifying this.
    """

    def app_mode_for_intent(self, intent: AppIntent) -> type[AppMode]:
        """Given an AppIntent, return the AppMode that should handle it.

        If None is returned, the AppIntent will be ignored.

        This is called in a background thread, so avoid any calls
        limited to logic thread use/etc.
        """
        raise RuntimeError('app_mode_for_intent() should be overridden.')
