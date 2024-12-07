# Released under the MIT License. See LICENSE for details.
#
"""Provides the AppSubsystem base class."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from babase import UIScale


class AppSubsystem:
    """Base class for an app subsystem.

    Category: **App Classes**

    An app 'subsystem' is a bit of a vague term, as pieces of the app
    can technically be any class and are not required to use this, but
    building one out of this base class provides conveniences such as
    predefined callbacks during app state changes.

    Subsystems must be registered with the app before it completes its
    transition to the 'running' state.
    """

    def __init__(self) -> None:
        _babase.app.register_subsystem(self)

    def on_app_loading(self) -> None:
        """Called when the app reaches the loading state.

        Note that subsystems created after the app switches to the
        loading state will not receive this callback. Subsystems created
        by plugins are an example of this.
        """

    def on_app_running(self) -> None:
        """Called when the app reaches the running state."""

    def on_app_suspend(self) -> None:
        """Called when the app enters the suspended state."""

    def on_app_unsuspend(self) -> None:
        """Called when the app exits the suspended state."""

    def on_app_shutdown(self) -> None:
        """Called when the app begins shutting down."""

    def on_app_shutdown_complete(self) -> None:
        """Called when the app completes shutting down."""

    def do_apply_app_config(self) -> None:
        """Called when the app config should be applied."""

    def on_screen_change(self) -> None:
        """Called when screen dimensions or ui-scale changes."""

    def reset(self) -> None:
        """Reset the subsystem to a default state.

        This is called when switching app modes, but may be called
        at other times too.
        """
