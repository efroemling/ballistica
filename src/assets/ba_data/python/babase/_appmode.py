# Released under the MIT License. See LICENSE for details.
#
"""Provides AppMode functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babase._appintent import AppIntent


class AppMode:
    """A high level mode for the app.

    Category: **App Classes**

    """

    @classmethod
    def supports_intent(cls, intent: AppIntent) -> bool:
        """Return whether our mode can handle the provided intent."""
        del intent

        # Say no to everything by default. Let's make mode explicitly
        # lay out everything they *do* support.
        return False

    def handle_intent(self, intent: AppIntent) -> None:
        """Handle an intent."""

    def on_activate(self) -> None:
        """Called when the mode is being activated."""

    def on_deactivate(self) -> None:
        """Called when the mode is being deactivated."""
