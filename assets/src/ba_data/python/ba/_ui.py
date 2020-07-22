# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""User interface functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._enums import UIScale

if TYPE_CHECKING:
    from typing import Optional, Dict, Any, Callable, List
    from ba.ui import UICleanupCheck
    import ba


class UI:
    """UI subsystem for the app."""

    def __init__(self) -> None:
        env = _ba.env()

        self.controller: Optional[ba.UIController] = None

        self._main_menu_window: Optional[ba.Widget] = None
        self._main_menu_location: Optional[str] = None

        self._uiscale: ba.UIScale

        interfacetype = env['interface_type']
        if interfacetype == 'large':
            self._uiscale = UIScale.LARGE
        elif interfacetype == 'medium':
            self._uiscale = UIScale.MEDIUM
        elif interfacetype == 'small':
            self._uiscale = UIScale.SMALL
        else:
            raise RuntimeError('Invalid UIScale value: {interfacetype}')

        self.window_states: Dict = {}  # FIXME: Kill this.
        self.main_menu_selection: Optional[str] = None  # FIXME: Kill this.
        self.have_party_queue_window = False
        self.quit_window: Any = None
        self.dismiss_wii_remotes_window_call: (Optional[Callable[[],
                                                                 Any]]) = None
        self.cleanupchecks: List[UICleanupCheck] = []
        self.upkeeptimer: Optional[ba.Timer] = None
        self.use_toolbars = env.get('toolbar_test', True)
        self.party_window: Any = None  # FIXME: Don't use Any.
        self.title_color = (0.72, 0.7, 0.75)
        self.heading_color = (0.72, 0.7, 0.75)
        self.infotextcolor = (0.7, 0.9, 0.7)

    @property
    def uiscale(self) -> ba.UIScale:
        """Current ui scale for the app."""
        return self._uiscale

    def on_app_launch(self) -> None:
        """Should be run on app launch."""
        from ba.ui import UIController, ui_upkeep
        from ba._enums import TimeType

        # IMPORTANT: If tweaking UI stuff, make sure it behaves for small,
        # medium, and large UI modes. (doesn't run off screen, etc).
        # The overrides below can be used to test with different sizes.
        # Generally small is used on phones, medium is used on tablets/tvs,
        # and large is on desktop computers or perhaps large tablets. When
        # possible, run in windowed mode and resize the window to assure
        # this holds true at all aspect ratios.

        # UPDATE: A better way to test this is now by setting the environment
        # variable BA_FORCE_UI_SCALE to "small", "medium", or "large".
        # This will affect system UIs not covered by the values below such
        # as screen-messages. The below values remain functional, however,
        # for cases such as Android where environment variables can't be set
        # easily.

        if bool(False):  # force-test ui scale
            self._uiscale = UIScale.SMALL
            with _ba.Context('ui'):
                _ba.pushcall(lambda: _ba.screenmessage(
                    f'FORCING UISCALE {self._uiscale.name} FOR TESTING',
                    color=(1, 0, 1),
                    log=True))

        self.controller = UIController()

        # Kick off our periodic UI upkeep.
        # FIXME: Can probably kill this if we do immediate UI death checks.
        self.upkeeptimer = _ba.Timer(2.6543,
                                     ui_upkeep,
                                     timetype=TimeType.REAL,
                                     repeat=True)

    def set_main_menu_window(self, window: ba.Widget) -> None:
        """Set the current 'main' window, replacing any existing."""
        existing = self._main_menu_window
        from ba._enums import TimeType
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
            from ba._error import print_exception
            print_exception('Error calcing line for set_main_menu_window')

        # With our legacy main-menu system, the caller is responsible for
        # clearing out the old main menu window when assigning the new.
        # However there are corner cases where that doesn't happen and we get
        # old windows stuck under the new main one. So let's guard against that
        # However, we can't simply delete the existing main window when
        # a new one is assigned because the user may transition the old out
        # *after* the assignment. Sigh. So as a happy medium let's check in
        # on the old after a short bit of time and kill it if its still alive.
        # That will be a bit ugly on screen but at least will un-break things.
        def _delay_kill() -> None:
            import time
            if existing:
                print(f'Killing old main_menu_window'
                      f' when called at: {frameline} t={time.time():.3f}')
                existing.delete()

        _ba.timer(1.0, _delay_kill, timetype=TimeType.REAL)
        self._main_menu_window = window

    def clear_main_menu_window(self, transition: str = None) -> None:
        """Clear any existing 'main' window with the provided transition."""
        if self._main_menu_window:
            if transition is not None:
                _ba.containerwidget(edit=self._main_menu_window,
                                    transition=transition)
            else:
                self._main_menu_window.delete()

    def has_main_menu_window(self) -> bool:
        """Return whether a main menu window is present."""
        return bool(self._main_menu_window)

    def set_main_menu_location(self, location: str) -> None:
        """Set the location represented by the current main menu window."""
        self._main_menu_location = location

    def get_main_menu_location(self) -> Optional[str]:
        """Return the current named main menu location, if any."""
        return self._main_menu_location
