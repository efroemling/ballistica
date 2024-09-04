# Released under the MIT License. See LICENSE for details.
#
"""User interface related functionality."""

from __future__ import annotations

import logging
import inspect
import weakref
from enum import Enum
from typing import TYPE_CHECKING, override

from efro.util import empty_weakref
import babase

import _bauiv1

if TYPE_CHECKING:
    from typing import Any, Callable

    from bauiv1._uitypes import (
        UICleanupCheck,
        Window,
        MainWindow,
        MainWindowState,
    )
    import bauiv1


class UIV1AppSubsystem(babase.AppSubsystem):
    """Consolidated UI functionality for the app.

    Category: **App Classes**

    To use this class, access the single instance of it at 'ba.app.ui'.
    """

    class RootUIElement(Enum):
        """Stuff provided by the root ui."""

        MENU_BUTTON = 'menu_button'
        SQUAD_BUTTON = 'squad_button'
        ACCOUNT_BUTTON = 'account_button'
        SETTINGS_BUTTON = 'settings_button'
        INBOX_BUTTON = 'inbox_button'
        STORE_BUTTON = 'store_button'
        INVENTORY_BUTTON = 'inventory_button'
        ACHIEVEMENTS_BUTTON = 'achievements_button'
        GET_TOKENS_BUTTON = 'get_tokens_button'
        TICKETS_METER = 'tickets_meter'
        TOKENS_METER = 'tokens_meter'
        TROPHY_METER = 'trophy_meter'
        LEVEL_METER = 'level_meter'
        CHEST_SLOT_1 = 'chest_slot_1'
        CHEST_SLOT_2 = 'chest_slot_2'
        CHEST_SLOT_3 = 'chest_slot_3'
        CHEST_SLOT_4 = 'chest_slot_4'

    def __init__(self) -> None:
        from bauiv1._uitypes import MainWindow

        super().__init__()
        env = babase.env()

        # We hold only a weak ref to the current main Window; we want it
        # to be able to disappear on its own. That being said, we do
        # expect MainWindows to keep themselves alive until replaced by
        # another MainWindow and we complain if they don't.
        self._main_window = empty_weakref(MainWindow)
        self._main_window_widget: bauiv1.Widget | None = None

        self.quit_window: bauiv1.Widget | None = None

        # The following should probably go away or move to classic.
        # self._main_menu_location: str | None = None

        # For storing arbitrary class-level state data for Windows or
        # other UI related classes.
        self.window_states: dict[type, Any] = {}

        uiscalestr = babase.app.config.get('UI Scale', env['ui_scale'])
        if uiscalestr == 'auto':
            uiscalestr = env['ui_scale']

        self._uiscale: babase.UIScale
        if uiscalestr == 'large':
            self._uiscale = babase.UIScale.LARGE
        elif uiscalestr == 'medium':
            self._uiscale = babase.UIScale.MEDIUM
        elif uiscalestr == 'small':
            self._uiscale = babase.UIScale.SMALL
        else:
            logging.error("Invalid UIScale '%s'.", uiscalestr)
            self._uiscale = babase.UIScale.MEDIUM

        self.cleanupchecks: list[UICleanupCheck] = []
        self.upkeeptimer: babase.AppTimer | None = None

        self.title_color = (0.72, 0.7, 0.75)
        self.heading_color = (0.72, 0.7, 0.75)
        self.infotextcolor = (0.7, 0.9, 0.7)

        # Elements in our root UI will call anything here when activated.
        self.root_ui_calls: dict[
            UIV1AppSubsystem.RootUIElement, Callable[[], None]
        ] = {}

    @property
    def available(self) -> bool:
        """Can uiv1 currently be used?

        Code that may run in headless mode, before the UI has been spun up,
        while other ui systems are active, etc. can check this to avoid
        likely erroring.
        """
        return _bauiv1.is_available()

    @override
    def reset(self) -> None:
        from bauiv1._uitypes import MainWindow

        self.root_ui_calls.clear()
        self._main_window = empty_weakref(MainWindow)
        self._main_window_widget = None

    @property
    def uiscale(self) -> babase.UIScale:
        """Current ui scale for the app."""
        return self._uiscale

    @override
    def on_app_loading(self) -> None:
        from bauiv1._uitypes import ui_upkeep

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

        # Kick off our periodic UI upkeep.
        # FIXME: Can probably kill this if we do immediate UI death checks.
        self.upkeeptimer = babase.AppTimer(2.6543, ui_upkeep, repeat=True)

    def do_main_window_back(self, from_window: MainWindow) -> None:
        """Sets the main menu window automatically from a parent WindowState."""

        main_window = self._main_window()
        back_state = (
            None if main_window is None else main_window.main_window_back_state
        )
        if back_state is None:
            raise RuntimeError(
                f'Main window {main_window} provides no back-state;'
                f' cannot use auto-back.'
            )
        backwin = back_state.create_window(transition='in_left')
        backwin.main_window_back_state = back_state.parent
        self.set_main_window(backwin, from_window=from_window, is_back=True)

    def get_main_window(self) -> bauiv1.MainWindow | None:
        """Return main window, if any."""
        return self._main_window()

    def set_main_window(
        self,
        window: bauiv1.MainWindow,
        from_window: bauiv1.MainWindow | None | bool = True,
        is_back: bool = False,
        is_top_level: bool = False,
        back_state: MainWindowState | None = None,
    ) -> None:
        """Set the current 'main' window, replacing any existing.

        Generally this should not be called directly; The high level
        MainWindow methods main_window_replace() and main_window_back()
        should be used when possible for navigation.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        from bauiv1._uitypes import MainWindow

        from_window_widget: bauiv1.Widget | None

        # We used to accept Widgets but now want MainWindows.
        if not isinstance(window, MainWindow):
            raise RuntimeError(
                f'set_main_window() now takes a MainWindow as its "window" arg.'
                f' You passed a {type(window)}.',
            )
        window_weakref = weakref.ref(window)
        window_widget = window.get_root_widget()

        if isinstance(from_window, MainWindow):
            from_window_widget = from_window.get_root_widget()
        else:
            if from_window is not None and not isinstance(from_window, bool):
                raise RuntimeError(
                    f'set_main_window() now takes a MainWindow or bool or None'
                    f'as its "from_window" arg.'
                    f' You passed a {type(from_window)}.',
                )

            from_window_widget = None

        existing = self._main_window_widget

        try:
            if isinstance(from_window, bool):
                # For default val True we warn that the arg wasn't
                # passed. False can be explicitly passed to disable this
                # check.
                if from_window is True:
                    caller_frame = inspect.stack()[1]
                    caller_filename = caller_frame.filename
                    caller_line_number = caller_frame.lineno
                    logging.warning(
                        'set_main_window() should be passed a'
                        " 'from_window' value to help ensure proper UI behavior"
                        ' (%s line %i).',
                        caller_filename,
                        caller_line_number,
                    )
            else:
                # For everything else, warn if what they passed wasn't
                # the previous main menu widget.
                if from_window_widget is not existing:
                    caller_frame = inspect.stack()[1]
                    caller_filename = caller_frame.filename
                    caller_line_number = caller_frame.lineno
                    logging.warning(
                        "set_main_window() was passed 'from_window' %s"
                        ' but existing main-menu-window is %s. (%s line %i).',
                        from_window_widget,
                        existing,
                        caller_filename,
                        caller_line_number,
                    )
        except Exception:
            # Prevent any bugs in these checks from causing problems.
            logging.exception('Error checking from_window')

        # Once the above code leads to us fixing all leftover window
        # bugs at the source, we can kill the code below.

        # Let's grab the location where we were called from to report if
        # we have to force-kill the existing window (which normally
        # should not happen).
        frameline = None
        try:
            frame = inspect.currentframe()
            if frame is not None:
                frame = frame.f_back
            if frame is not None:
                frameinfo = inspect.getframeinfo(frame)
                frameline = f'{frameinfo.filename} {frameinfo.lineno}'
        except Exception:
            logging.exception('Error calcing line for set_main_window')

        # NOTE: disabling this for now since hopefully our new system
        # will be bulletproof enough to avoid this. Can turn it back on
        # if that's not the case.

        # With our legacy main-menu system, the caller is responsible
        # for clearing out the old main menu window when assigning the
        # new. However there are corner cases where that doesn't happen
        # and we get old windows stuck under the new main one. So let's
        # guard against that. However, we can't simply delete the
        # existing main window when a new one is assigned because the
        # user may transition the old out *after* the assignment. Sigh.
        # So, as a happy medium, let's check in on the old after a short
        # bit of time and kill it if its still alive. That will be a bit
        # ugly on screen but at least should un-break things.
        def _delay_kill() -> None:
            import time

            if existing:
                print(
                    f'Killing old main_menu_window'
                    f' when called at: {frameline} t={time.time():.3f}'
                )
                existing.delete()

        if bool(False):
            babase.apptimer(1.0, _delay_kill)

        if is_back:
            pass
        else:
            # When navigating forward, generate a back-window-state from
            # the outgoing window.
            if is_top_level:
                # Top level windows don't have or expect anywhere to
                # go back to.
                #
                # self._main_window_back_state = None
                window.main_window_back_state = None
            elif back_state is not None:
                window.main_window_back_state = back_state
            else:
                oldwin = self._main_window()
                if oldwin is None:
                    # We currenty only hold weak refs to windows so
                    # that they are free to die on their own, but we
                    # expect the main menu window to keep itself
                    # alive as long as its the main one. Holler if
                    # that seems to not be happening.
                    logging.warning(
                        'set_main_window: No old MainWindow found'
                        ' and is_top_level is False;'
                        ' this should not happen.'
                    )
                    window.main_window_back_state = None
                else:
                    oldwinstate = oldwin.get_main_window_state()

                    # Store our previous back state on this new one.
                    oldwinstate.parent = oldwin.main_window_back_state
                    window.main_window_back_state = oldwinstate

        self._main_window = window_weakref
        self._main_window_widget = window_widget

    def has_main_window(self) -> bool:
        """Return whether a main menu window is present."""
        return bool(self._main_window_widget)

    def clear_main_window(self, transition: str | None = None) -> None:
        """Clear any existing main window."""
        from bauiv1._uitypes import MainWindow

        main_window = self._main_window()
        if main_window:
            main_window.main_window_close(transition=transition)
        else:
            # Fallback; if we have a widget but no window, nuke the widget.
            if self._main_window_widget:
                logging.error(
                    'Have _main_window_widget but no main_window'
                    ' on clear_main_window; unexpected.'
                )
                self._main_window_widget.delete()

        self._main_window = empty_weakref(MainWindow)
        self._main_window_widget = None
