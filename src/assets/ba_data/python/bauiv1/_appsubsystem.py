# Released under the MIT License. See LICENSE for details.
#
"""User interface related functionality."""

from __future__ import annotations

import logging
import inspect
import weakref
import warnings
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
        CHEST_SLOT_0 = 'chest_slot_0'
        CHEST_SLOT_1 = 'chest_slot_1'
        CHEST_SLOT_2 = 'chest_slot_2'
        CHEST_SLOT_3 = 'chest_slot_3'

    def __init__(self) -> None:
        from bauiv1._uitypes import MainWindow

        super().__init__()

        # We hold only a weak ref to the current main Window; we want it
        # to be able to disappear on its own. That being said, we do
        # expect MainWindows to keep themselves alive until replaced by
        # another MainWindow and we complain if they don't.
        self._main_window = empty_weakref(MainWindow)
        self._main_window_widget: bauiv1.Widget | None = None

        self.quit_window: bauiv1.Widget | None = None

        # For storing arbitrary class-level state data for Windows or
        # other UI related classes.
        self.window_states: dict[type, Any] = {}

        self._uiscale: babase.UIScale
        self._update_ui_scale()

        self.cleanupchecks: list[UICleanupCheck] = []
        self.upkeeptimer: babase.AppTimer | None = None

        self.title_color = (0.72, 0.7, 0.75)
        self.heading_color = (0.72, 0.7, 0.75)
        self.infotextcolor = (0.7, 0.9, 0.7)

        # Elements in our root UI will call anything here when
        # activated.
        self.root_ui_calls: dict[
            UIV1AppSubsystem.RootUIElement, Callable[[], None]
        ] = {}

    def _update_ui_scale(self) -> None:
        uiscalestr = babase.get_ui_scale()
        if uiscalestr == 'large':
            self._uiscale = babase.UIScale.LARGE
        elif uiscalestr == 'medium':
            self._uiscale = babase.UIScale.MEDIUM
        elif uiscalestr == 'small':
            self._uiscale = babase.UIScale.SMALL
        else:
            logging.error("Invalid UIScale '%s'.", uiscalestr)
            self._uiscale = babase.UIScale.MEDIUM

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

        # IMPORTANT: If tweaking UI stuff, make sure it behaves for
        # small, medium, and large UI modes. (doesn't run off screen,
        # etc). The overrides below can be used to test with different
        # sizes. Generally small is used on phones, medium is used on
        # tablets/tvs, and large is on desktop computers or perhaps
        # large tablets. When possible, run in windowed mode and resize
        # the window to assure this holds true at all aspect ratios.

        # UPDATE: A better way to test this is now by setting the
        # environment variable BA_UI_SCALE to "small", "medium", or
        # "large". This will affect system UIs not covered by the values
        # below such as screen-messages. The below values remain
        # functional, however, for cases such as Android where
        # environment variables can't be set easily.

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

        # FIXME: Can probably kill this if we do immediate UI death
        # checks.
        self.upkeeptimer = babase.AppTimer(2.6543, ui_upkeep, repeat=True)

    def get_main_window(self) -> bauiv1.MainWindow | None:
        """Return main window, if any."""
        return self._main_window()

    def set_main_window(
        self,
        window: bauiv1.MainWindow,
        *,
        from_window: bauiv1.MainWindow | None | bool = True,
        is_back: bool = False,
        is_top_level: bool = False,
        is_auxiliary: bool = False,
        back_state: MainWindowState | None = None,
        suppress_warning: bool = False,
    ) -> None:
        """Set the current 'main' window.

        Generally this should not be called directly; The high level
        MainWindow methods main_window_replace() and main_window_back()
        should be used whenever possible to implement navigation.

        The caller is responsible for cleaning up any previous main
        window.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        from bauiv1._uitypes import MainWindow

        # Encourage migration to the new higher level nav calls.
        if not suppress_warning:
            warnings.warn(
                'set_main_window() should usually not be called directly;'
                ' use the main_window_replace() or main_window_back()'
                ' methods on MainWindow objects for navigation instead.'
                ' If you truly need to use set_main_window(),'
                ' pass suppress_warning=True to silence this warning.',
                DeprecationWarning,
                stacklevel=2,
            )

        # We used to accept Widgets but now want MainWindows.
        if not isinstance(window, MainWindow):
            raise RuntimeError(
                f'set_main_window() now takes a MainWindow as its "window" arg.'
                f' You passed a {type(window)}.',
            )
        window_weakref = weakref.ref(window)
        window_widget = window.get_root_widget()

        if not isinstance(from_window, MainWindow):
            if from_window is not None and not isinstance(from_window, bool):
                raise RuntimeError(
                    f'set_main_window() now takes a MainWindow or bool or None'
                    f'as its "from_window" arg.'
                    f' You passed a {type(from_window)}.',
                )

        existing = self._main_window()

        # If they passed a back-state, make sure it is fully filled out.
        if back_state is not None:
            if (
                back_state.is_top_level is None
                or back_state.is_auxiliary is None
                or back_state.window_type is None
            ):
                raise RuntimeError(
                    'Provided back_state is incomplete.'
                    ' Make sure to only pass fully-filled-out MainWindowStates.'
                )

        # If a top-level main-window is being set, complain if there already
        # is a main-window.
        if is_top_level:
            if existing:
                logging.warning(
                    'set_main_window() called with top-level window %s'
                    ' but found existing main-window %s.',
                    window,
                    existing,
                )
        else:
            # In other cases, sanity-check that the window asking for
            # this switch is the one we're switching away from.
            try:
                if isinstance(from_window, bool):
                    # For default val True we warn that the arg wasn't
                    # passed. False can be explicitly passed to disable
                    # this check.
                    if from_window is True:
                        caller_frame = inspect.stack()[1]
                        caller_filename = caller_frame.filename
                        caller_line_number = caller_frame.lineno
                        logging.warning(
                            'set_main_window() should be passed a'
                            " 'from_window' value to help ensure proper"
                            ' UI behavior (%s line %i).',
                            caller_filename,
                            caller_line_number,
                        )
                else:
                    # For everything else, warn if what they passed
                    # wasn't the previous main menu widget.
                    if from_window is not existing:
                        caller_frame = inspect.stack()[1]
                        caller_filename = caller_frame.filename
                        caller_line_number = caller_frame.lineno
                        logging.warning(
                            "set_main_window() was passed 'from_window' %s"
                            ' but existing main-menu-window is %s.'
                            ' (%s line %i).',
                            from_window,
                            existing,
                            caller_filename,
                            caller_line_number,
                        )
            except Exception:
                # Prevent any bugs in these checks from causing problems.
                logging.exception('Error checking from_window')

        if is_back:
            # These values should only be passed for forward navigation.
            assert not is_top_level
            assert not is_auxiliary
            # Make sure back state is complete.
            assert back_state is not None
            assert back_state.is_top_level is not None
            assert back_state.is_auxiliary is not None
            assert back_state.window_type is type(window)
            window.main_window_back_state = back_state.parent
            window.main_window_is_top_level = back_state.is_top_level
            window.main_window_is_auxiliary = back_state.is_auxiliary
        else:
            # Store if the window is top-level so we won't complain later if
            # we go back from it and there's nowhere to go to.
            window.main_window_is_top_level = is_top_level

            window.main_window_is_auxiliary = is_auxiliary

            # When navigating forward, generate a back-window-state from
            # the outgoing window.
            if is_top_level:
                # Top level windows don't have or expect anywhere to
                # go back to.
                window.main_window_back_state = None
            elif back_state is not None:
                window.main_window_back_state = back_state
            else:
                oldwin = self._main_window()
                if oldwin is None:
                    # We currenty only hold weak refs to windows so that
                    # they are free to die on their own, but we expect
                    # the main menu window to keep itself alive as long
                    # as its the main one. Holler if that seems to not
                    # be happening.
                    logging.warning(
                        'set_main_window: No old MainWindow found'
                        ' and is_top_level is False;'
                        ' this should not happen.'
                    )
                    window.main_window_back_state = None
                else:
                    window.main_window_back_state = self.save_main_window_state(
                        oldwin
                    )

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

    def save_main_window_state(self, window: MainWindow) -> MainWindowState:
        """Fully initialize a window-state from a window.

        Use this to get a complete state for later restoration purposes.
        Calling the window's get_main_window_state() directly is
        insufficient.
        """
        winstate = window.get_main_window_state()

        # Store some common window stuff on its state.
        winstate.parent = window.main_window_back_state
        winstate.is_top_level = window.main_window_is_top_level
        winstate.is_auxiliary = window.main_window_is_auxiliary
        winstate.window_type = type(window)

        return winstate

    def restore_main_window_state(self, state: MainWindowState) -> None:
        """Restore UI to a saved state."""
        existing = self.get_main_window()
        if existing is not None:
            raise RuntimeError('There is already a MainWindow.')

        # Valid states should have a value here.
        assert state.is_top_level is not None
        assert state.is_auxiliary is not None
        assert state.window_type is not None

        win = state.create_window(transition=None)
        self.set_main_window(
            win,
            from_window=False,  # disable check
            is_top_level=state.is_top_level,
            is_auxiliary=state.is_auxiliary,
            back_state=state.parent,
            suppress_warning=True,
        )

    @override
    def on_screen_change(self) -> None:
        # Update our stored UIScale.
        self._update_ui_scale()

        # Update native bits (allow root widget to rebuild itself/etc.)
        _bauiv1.on_screen_change()

        # Lastly, if we have a main window, recreate it to pick up the
        # new UIScale/etc.
        mainwindow = self.get_main_window()
        if mainwindow is not None:
            winstate = self.save_main_window_state(mainwindow)
            self.clear_main_window(transition='instant')
            self.restore_main_window_state(winstate)
