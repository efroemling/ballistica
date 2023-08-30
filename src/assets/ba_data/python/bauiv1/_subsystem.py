# Released under the MIT License. See LICENSE for details.
#
"""User interface related functionality."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import babase
import _bauiv1

if TYPE_CHECKING:
    from typing import Any, Callable

    from bauiv1._uitypes import UICleanupCheck, UIController
    import bauiv1


class UIV1Subsystem(babase.AppSubsystem):
    """Consolidated UI functionality for the app.

    Category: **App Classes**

    To use this class, access the single instance of it at 'ba.app.ui'.
    """

    def __init__(self) -> None:
        super().__init__()
        env = babase.env()

        self.controller: UIController | None = None

        self._main_menu_window: bauiv1.Widget | None = None
        self._main_menu_location: str | None = None
        self.quit_window: bauiv1.Widget | None = None

        # From classic.
        self.main_menu_resume_callbacks: list = []  # Can probably go away.

        self._uiscale: babase.UIScale

        interfacetype = env['ui_scale']
        if interfacetype == 'large':
            self._uiscale = babase.UIScale.LARGE
        elif interfacetype == 'medium':
            self._uiscale = babase.UIScale.MEDIUM
        elif interfacetype == 'small':
            self._uiscale = babase.UIScale.SMALL
        else:
            raise RuntimeError(f'Invalid UIScale value: {interfacetype}')

        self.window_states: dict[type, Any] = {}  # FIXME: Kill this.
        self.main_menu_selection: str | None = None  # FIXME: Kill this.
        self.have_party_queue_window = False
        self.cleanupchecks: list[UICleanupCheck] = []
        self.upkeeptimer: babase.AppTimer | None = None
        self.use_toolbars = _bauiv1.toolbar_test()
        # self.use_toolbars = env.get('toolbar_test', True)

        self.title_color = (0.72, 0.7, 0.75)
        self.heading_color = (0.72, 0.7, 0.75)
        self.infotextcolor = (0.7, 0.9, 0.7)

        # Switch our overall game selection UI flow between Play and
        # Private-party playlist selection modes; should do this in
        # a more elegant way once we revamp high level UI stuff a bit.
        self.selecting_private_party_playlist: bool = False

    @property
    def uiscale(self) -> babase.UIScale:
        """Current ui scale for the app."""
        return self._uiscale

    def on_app_loading(self) -> None:
        from bauiv1._uitypes import UIController, ui_upkeep

        # IMPORTANT: If tweaking UI stuff, make sure it behaves for small,
        # medium, and large UI modes. (doesn't run off screen, etc).
        # The overrides below can be used to test with different sizes.
        # Generally small is used on phones, medium is used on tablets/tvs,
        # and large is on desktop computers or perhaps large tablets. When
        # possible, run in windowed mode and resize the window to assure
        # this holds true at all aspect ratios.

        # UPDATE: A better way to test this is now by setting the environment
        # variable BA_UI_SCALE to "small", "medium", or "large".
        # This will affect system UIs not covered by the values below such
        # as screen-messages. The below values remain functional, however,
        # for cases such as Android where environment variables can't be set
        # easily.

        if bool(False):  # force-test ui scale
            self._uiscale = babase.UIScale.SMALL
            with babase.ContextRef.empty():
                babase.pushcall(
                    lambda: babase.screenmessage(
                        f'FORCING UISCALE {self._uiscale.name} FOR TESTING',
                        color=(1, 0, 1),
                        log=True,
                    )
                )

        self.controller = UIController()

        # Kick off our periodic UI upkeep.
        # FIXME: Can probably kill this if we do immediate UI death checks.
        self.upkeeptimer = babase.AppTimer(2.6543, ui_upkeep, repeat=True)

    def set_main_menu_window(self, window: bauiv1.Widget) -> None:
        """Set the current 'main' window, replacing any existing."""
        existing = self._main_menu_window
        from inspect import currentframe, getframeinfo

        # Let's grab the location where we were called from to report
        # if we have to force-kill the existing window (which normally
        # should not happen).
        frameline = None
        try:
            frame = currentframe()
            if frame is not None:
                frame = frame.f_back
            if frame is not None:
                frameinfo = getframeinfo(frame)
                frameline = f'{frameinfo.filename} {frameinfo.lineno}'
        except Exception:
            logging.exception('Error calcing line for set_main_menu_window')

        # With our legacy main-menu system, the caller is responsible for
        # clearing out the old main menu window when assigning the new.
        # However there are corner cases where that doesn't happen and we get
        # old windows stuck under the new main one. So let's guard against
        # that. However, we can't simply delete the existing main window when
        # a new one is assigned because the user may transition the old out
        # *after* the assignment. Sigh. So, as a happy medium, let's check in
        # on the old after a short bit of time and kill it if its still alive.
        # That will be a bit ugly on screen but at least should un-break
        # things.
        def _delay_kill() -> None:
            import time

            if existing:
                print(
                    f'Killing old main_menu_window'
                    f' when called at: {frameline} t={time.time():.3f}'
                )
                existing.delete()

        babase.apptimer(1.0, _delay_kill)
        self._main_menu_window = window

    def clear_main_menu_window(self, transition: str | None = None) -> None:
        """Clear any existing 'main' window with the provided transition."""
        if self._main_menu_window:
            if transition is not None:
                _bauiv1.containerwidget(
                    edit=self._main_menu_window, transition=transition
                )
            else:
                self._main_menu_window.delete()

    def add_main_menu_close_callback(self, call: Callable[[], Any]) -> None:
        """(internal)"""

        # If there's no main menu up, just call immediately.
        if not self.has_main_menu_window():
            with babase.ContextRef.empty():
                call()
        else:
            self.main_menu_resume_callbacks.append(call)

    def has_main_menu_window(self) -> bool:
        """Return whether a main menu window is present."""
        return bool(self._main_menu_window)

    def set_main_menu_location(self, location: str) -> None:
        """Set the location represented by the current main menu window."""
        self._main_menu_location = location

    def get_main_menu_location(self) -> str | None:
        """Return the current named main menu location, if any."""
        return self._main_menu_location
