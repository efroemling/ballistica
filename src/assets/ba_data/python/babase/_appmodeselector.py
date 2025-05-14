# Released under the MIT License. See LICENSE for details.
#
"""Contains AppModeSelector base class."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babase import AppMode, AppIntent


class AppModeSelector:
    """Defines which app-modes should handle which app-intents.

    The app calls an instance of this class when passed an
    :class:`~babase.AppIntent` to determine which
    :class:`~babase.AppMode` to use to handle it. Plugins or spinoff
    projects can modify high level app behavior by replacing or
    modifying the app's :attr:`~babase.App.mode_selector` attr or by
    modifying settings used to construct the default one.
    """

    def app_mode_for_intent(self, intent: AppIntent) -> type[AppMode] | None:
        """Given an app-intent, return the app-mode that should handle it.

        If None is returned, the intent will be ignored.

        This may be called in a background thread, so avoid any calls
        limited to logic thread use/etc.
        """
        raise NotImplementedError()
