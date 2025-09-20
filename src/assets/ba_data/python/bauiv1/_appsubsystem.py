# Released under the MIT License. See LICENSE for details.
#
"""User interface related functionality."""

from __future__ import annotations

import os
import time
import logging
import inspect
import weakref
import warnings
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from efro.util import empty_weakref
import babase

import _bauiv1

if TYPE_CHECKING:
    from typing import Any, Callable

    from bauiv1._window import Window, MainWindow, MainWindowState
    import bauiv1

# Set environment variable BA_DEBUG_UI_CLEANUP_CHECKS to 1
# to print detailed info about what is getting cleaned up when.
DEBUG_UI_CLEANUP_CHECKS = os.environ.get('BA_DEBUG_UI_CLEANUP_CHECKS') == '1'


class UIV1AppSubsystem(babase.AppSubsystem):
    """Consolidated UI functionality for the app.

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
        from bauiv1._window import MainWindow

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

        self.title_color = (0.72, 0.7, 0.75)
        self.heading_color = (0.72, 0.7, 0.75)
        self.infotextcolor = (0.7, 0.9, 0.7)

        self.window_auto_recreate_suppress_count = 0

        self._uiscale: babase.UIScale
        self._update_ui_scale()
        self._upkeeptimer: babase.AppTimer | None = None
        self._cleanupchecks: list[_UICleanupCheck] = []
        self._last_win_recreate_screen_size: tuple[float, float] | None = None
        self._last_win_recreate_uiscale: bauiv1.UIScale | None = None
        self._last_win_recreate_time: float | None = None
        self._win_recreate_timer: babase.AppTimer | None = None

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
        from bauiv1._window import MainWindow

        self.root_ui_calls.clear()
        self._main_window = empty_weakref(MainWindow)
        self._main_window_widget = None

    @property
    def uiscale(self) -> babase.UIScale:
        """Current ui scale for the app."""
        return self._uiscale

    @override
    def on_app_loading(self) -> None:

        # Kick off our periodic UI upkeep.
        self._upkeeptimer = babase.AppTimer(2.6543, self._upkeep, repeat=True)

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
        from bauiv1._window import MainWindow

        # If we haven't grabbed initial uiscale or screen size for
        # recreate comparision purposes, this is a good time to do so.
        if self._last_win_recreate_screen_size is None:
            self._last_win_recreate_screen_size = (
                babase.get_virtual_screen_size()
            )
        if self._last_win_recreate_uiscale is None:
            self._last_win_recreate_uiscale = babase.app.ui_v1.uiscale

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

        # If a top-level main-window is being set, complain if there
        # already is a main-window.
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
            # Store if the window is top-level so we won't complain
            # later if we go back from it and there's nowhere to go to.
            window.main_window_is_top_level = is_top_level

            window.main_window_is_auxiliary = is_auxiliary

            # When navigating forward, generate a back-window-state from
            # the outgoing window.
            if is_top_level:
                # Top level windows don't have or expect anywhere to go
                # back to.
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
        from bauiv1._window import MainWindow

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

    def should_suppress_window_recreates(self) -> bool:
        """Should we avoid auto-recreating windows at the current time?"""

        # This is slightly hack-ish and ideally we can get to the point
        # where we never need this and can remove it.

        # Currently string-edits grab a weak-ref to the exact text
        # widget they're targeting. So we need to suppress recreates
        # while edits are in progress. Ideally we should change that to
        # use ids or something that would survive a recreate.
        if babase.app.stringedit.active_adapter() is not None:
            return True

        # Suppress if anything else is requesting suppression (such as
        # generic Windows that don't handle being recreated).
        return babase.app.ui_v1.window_auto_recreate_suppress_count > 0

    @override
    def on_ui_scale_change(self) -> None:
        # Update our stored UIScale.
        self._update_ui_scale()

        # Update native bits (allow root widget to rebuild itself/etc.)
        _bauiv1.on_ui_scale_change()

        self._schedule_main_win_recreate()

    @override
    def on_screen_size_change(self) -> None:

        self._schedule_main_win_recreate()

    def add_ui_cleanup_check(self, obj: Any, widget: bauiv1.Widget) -> None:
        """Checks to ensure a widget-owning object gets cleaned up properly.

        This adds a check which will print an error message if the provided
        object still exists ~5 seconds after the provided bauiv1.Widget
        dies.

        This is a good sanity check for any sort of object that wraps or
        controls a bauiv1.Widget. For instance, a 'Window' class instance
        has no reason to still exist once its root container bauiv1.Widget
        has fully transitioned out and been destroyed. Circular references
        or careless strong referencing can lead to such objects never
        getting destroyed, however, and this helps detect such cases to
        avoid memory leaks.
        """
        if DEBUG_UI_CLEANUP_CHECKS:
            print(f'adding uicleanup to {obj}')
        if not isinstance(widget, _bauiv1.Widget):
            raise TypeError('widget arg is not a bauiv1.Widget')

        if bool(False):

            def foobar() -> None:
                """Just testing."""
                if DEBUG_UI_CLEANUP_CHECKS:
                    print('uicleanupcheck widget dying...')

            widget.add_delete_callback(foobar)

        self._cleanupchecks.append(
            _UICleanupCheck(
                obj=weakref.ref(obj), widget=widget, widget_death_time=None
            )
        )

    def auxiliary_window_activate(
        self,
        win_type: type[bauiv1.MainWindow],
        win_create_call: Callable[[], bauiv1.MainWindow],
    ) -> None:
        """Navigate to or away from an Auxiliary window.

        Auxiliary windows can be thought of as 'side quests' in the
        window hierarchy; places such as settings windows or league
        ranking windows that the user might want to visit without losing
        their place in the regular hierarchy.

        Calling this method with a MainWindow of the provided type
        already in the stack will back out past it (effectively toggling
        the 'side quest' back off).

        Calling this method with a *different* auxiliary window in the
        stack will back out past that and replace it with this
        (effectively ending the old side-quest and starting a new one).
        """
        # pylint: disable=unidiomatic-typecheck

        current_main_window = self.get_main_window()

        # Scan our ancestors for auxiliary states matching our type as
        # well as auxiliary states in general.
        aux_matching_state: bauiv1.MainWindowState | None = None
        aux_state: bauiv1.MainWindowState | None = None

        if current_main_window is None:
            raise RuntimeError(
                'Not currently handling no-top-level-window case.'
            )

        state = current_main_window.main_window_back_state
        while state is not None:
            assert state.window_type is not None
            if state.is_auxiliary:
                if state.window_type is win_type:
                    aux_matching_state = state
                else:
                    aux_state = state

            state = state.parent

        # If there's an ancestor auxiliary window-state matching our
        # type, back out past it (example: poking settings, navigating
        # down a level or two, and then poking settings again should
        # back out of settings).
        if aux_matching_state is not None:
            current_main_window.main_window_back_state = (
                aux_matching_state.parent
            )
            current_main_window.main_window_back()
            return

        # If there's an ancestory auxiliary state *not* matching our
        # type, crop the state and swap in our new auxiliary UI
        # (example: poking settings, then poking account, then poking
        # back should end up where things were before the settings
        # poke).
        if aux_state is not None:
            # Blow away the window stack and build a fresh one.
            self.clear_main_window()
            self.set_main_window(
                win_create_call(),
                from_window=False,  # Disable from-check.
                back_state=aux_state.parent,
                suppress_warning=True,
                is_auxiliary=True,
            )
            return

        # Ok, no auxiliary states found. Now if current window is
        # auxiliary and the type matches, simply do a back.
        if (
            current_main_window.main_window_is_auxiliary
            and type(current_main_window) is win_type
        ):
            current_main_window.main_window_back()
            return

        # If current window is auxiliary but type doesn't match,
        # swap it out for our new auxiliary UI.
        if current_main_window.main_window_is_auxiliary:
            self.clear_main_window()
            self.set_main_window(
                win_create_call(),
                from_window=False,  # Disable from-check.
                back_state=current_main_window.main_window_back_state,
                suppress_warning=True,
                is_auxiliary=True,
            )
            return

        # Ok, no existing auxiliary stuff was found period. Just
        # navigate forward to this UI.
        current_main_window.main_window_replace(
            win_create_call(), is_auxiliary=True
        )

    def _schedule_main_win_recreate(self) -> None:

        # If there is a timer set already, do nothing.
        if self._win_recreate_timer is not None:
            return

        # Recreating a MainWindow is a kinda heavy thing and it doesn't
        # seem like we should be doing it at 120hz during a live window
        # resize, so let's limit the max rate we do it. We also use the
        # same mechanism to defer window recreates while anything is
        # suppressing them.
        now = time.monotonic()

        # Up to 4 refreshes per second seems reasonable.
        interval = 0.25

        # Ok; there's no timer. Schedule one.
        till_update = (
            interval
            if self.should_suppress_window_recreates()
            else (
                0.0
                if self._last_win_recreate_time is None
                else max(0.0, self._last_win_recreate_time + interval - now)
            )
        )
        self._win_recreate_timer = babase.AppTimer(
            till_update, self._do_main_win_recreate
        )

    def _do_main_win_recreate(self) -> None:
        self._last_win_recreate_time = time.monotonic()
        self._win_recreate_timer = None

        # If win-recreates are currently suppressed, just kick off
        # another timer. We'll do our actual thing once suppression
        # finally ends.
        if self.should_suppress_window_recreates():
            self._schedule_main_win_recreate()
            return

        mainwindow = self.get_main_window()

        # Can't recreate what doesn't exist.
        if mainwindow is None:
            return

        virtual_screen_size = babase.get_virtual_screen_size()
        uiscale = babase.app.ui_v1.uiscale

        # These should always get actual values when a main-window is
        # assigned so should never still be None here.
        assert self._last_win_recreate_uiscale is not None
        assert self._last_win_recreate_screen_size is not None

        # If uiscale hasn't changed and our screen-size hasn't either
        # (or it has but we don't care) then we're done.
        if uiscale is self._last_win_recreate_uiscale and (
            virtual_screen_size == self._last_win_recreate_screen_size
            or not mainwindow.refreshes_on_screen_size_changes
        ):
            return

        # Do the recreate.
        winstate = self.save_main_window_state(mainwindow)
        self.clear_main_window(transition='instant')
        self.restore_main_window_state(winstate)

        # Store the size we created this for to avoid redundant
        # future recreates.
        self._last_win_recreate_uiscale = uiscale
        self._last_win_recreate_screen_size = virtual_screen_size

    def _upkeep(self) -> None:
        """Run UI cleanup checks, etc. should be called periodically."""

        assert babase.app.classic is not None
        remainingchecks = []
        now = babase.apptime()
        for check in self._cleanupchecks:
            obj = check.obj()

            # If the object has died, ignore and don't re-add.
            if obj is None:
                if DEBUG_UI_CLEANUP_CHECKS:
                    print('uicleanupcheck object is dead; hooray!')
                continue

            # If the widget hadn't died yet, note if it has.
            if check.widget_death_time is None:
                remainingchecks.append(check)
                if not check.widget:
                    check.widget_death_time = now
            else:
                # Widget was already dead; complain if its been too long.
                if now - check.widget_death_time > 5.0:
                    print(
                        'WARNING:',
                        obj,
                        'is still alive 5 second after its Widget died;'
                        ' you might have a memory leak. Look for circular'
                        ' references or outside things referencing your Window'
                        ' class instance. See efro.debug module'
                        ' for tools that can help debug this sort of thing.',
                    )
                else:
                    remainingchecks.append(check)
        self._cleanupchecks = remainingchecks


@dataclass
class _UICleanupCheck:
    """Holds info about a uicleanupcheck target."""

    obj: weakref.ref
    widget: bauiv1.Widget
    widget_death_time: float | None
