# Released under the MIT License. See LICENSE for details.
#
"""Provide top level UI related functionality."""

from __future__ import annotations

import os
import weakref
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import babase

import _bauiv1

if TYPE_CHECKING:
    from typing import Any, Type, Literal, Callable

    import bauiv1

# Set environment variable BA_DEBUG_UI_CLEANUP_CHECKS to 1
# to print detailed info about what is getting cleaned up when.
DEBUG_UI_CLEANUP_CHECKS = os.environ.get('BA_DEBUG_UI_CLEANUP_CHECKS') == '1'


class Window:
    """A basic window.

    Essentially wraps a ContainerWidget with some higher level
    functionality.
    """

    def __init__(
        self,
        root_widget: bauiv1.Widget,
        cleanupcheck: bool = True,
        prevent_main_window_auto_recreate: bool = True,
    ):
        self._root_widget = root_widget

        # By default, the presence of any generic windows prevents the
        # app from running its fancy main-window-auto-recreate mechanism
        # on screen-resizes and whatnot. This avoids things like
        # temporary popup windows getting stuck under auto-re-created
        # main-windows.
        self._window_main_window_auto_recreate_suppress = (
            MainWindowAutoRecreateSuppress()
            if prevent_main_window_auto_recreate
            else None
        )

        # Generally we complain if we outlive our root widget.
        if cleanupcheck:
            uicleanupcheck(self, root_widget)

    def get_root_widget(self) -> bauiv1.Widget:
        """Return the root widget."""
        return self._root_widget


class MainWindow(Window):
    """A special type of window that can be set as 'main'.

    The UI system has at most one main window at any given time.
    MainWindows support high level functionality such as saving and
    restoring states, allowing them to be automatically recreated when
    navigating back from other locations or when something like ui-scale
    changes.
    """

    def __init__(
        self,
        root_widget: bauiv1.Widget,
        *,
        transition: str | None,
        origin_widget: bauiv1.Widget | None,
        cleanupcheck: bool = True,
        refresh_on_screen_size_changes: bool = False,
    ):
        """Create a MainWindow given a root widget and transition info.

        Automatically handles in and out transitions on the provided
        widget, so there is no need to set transitions when creating it.
        """
        # A back-state supplied by the ui system.
        self.main_window_back_state: MainWindowState | None = None

        self.main_window_is_top_level: bool = False

        # Windows that size tailor themselves to exact screen dimensions
        # can pass True for this. Generally this only applies to small
        # ui scale and at larger scales windows simply fit in the
        # virtual safe area.
        self.refreshes_on_screen_size_changes = refresh_on_screen_size_changes

        # Windows can be flagged as auxiliary when not related to the
        # main UI task at hand. UI code may choose to handle auxiliary
        # windows in special ways, such as by implicitly replacing
        # existing auxiliary windows with new ones instead of keeping
        # old ones as back targets.
        self.main_window_is_auxiliary: bool = False

        self._main_window_transition = transition
        self._main_window_origin_widget = origin_widget
        super().__init__(
            root_widget,
            cleanupcheck=cleanupcheck,
            prevent_main_window_auto_recreate=False,
        )

        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._main_window_transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._main_window_transition_out = 'out_right'
            scale_origin = None
        _bauiv1.containerwidget(
            edit=root_widget,
            transition=transition,
            scale_origin_stack_offset=scale_origin,
        )

    def main_window_close(self, transition: str | None = None) -> None:
        """Get window transitioning out if still alive."""

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        # Transition ourself out.
        try:
            self.on_main_window_close()
        except Exception:
            logging.exception('Error in on_main_window_close() for %s.', self)

        # Note: normally transition of None means instant, but we use
        # that to mean 'do the default' so we support a special
        # 'instant' string.
        if transition == 'instant':
            self._root_widget.delete()
        else:
            _bauiv1.containerwidget(
                edit=self._root_widget,
                transition=(
                    self._main_window_transition_out
                    if transition is None
                    else transition
                ),
            )

    def main_window_has_control(self) -> bool:
        """Is this MainWindow allowed to change the global main window?

        It is a good idea to make sure this is True before calling
        main_window_replace(). This prevents fluke UI breakage such as
        multiple simultaneous events causing a MainWindow to spawn
        multiple replacements for itself.
        """
        # We are allowed to change main windows if we are the current one
        # AND our underlying widget is still alive and not transitioning out.
        return (
            babase.app.ui_v1.get_main_window() is self
            and bool(self._root_widget)
            and not self._root_widget.transitioning_out
        )

    def main_window_back(self) -> None:
        """Move back in the main window stack.

        Is a no-op if the main window does not have control;
        no need to check main_window_has_control() first.
        """

        # Users should always check main_window_has_control() before
        # calling us. Error if it seems they did not.
        if not self.main_window_has_control():
            return

        uiv1 = babase.app.ui_v1

        # Get the 'back' window coming in.
        if not self.main_window_is_top_level:

            back_state = self.main_window_back_state
            if back_state is None:
                raise RuntimeError(
                    f'Main window {self} provides no back-state.'
                )

            # Valid states should have values here.
            assert back_state.is_top_level is not None
            assert back_state.is_auxiliary is not None
            assert back_state.window_type is not None

            backwin = back_state.create_window(transition='in_left')

            uiv1.set_main_window(
                backwin,
                from_window=self,
                is_back=True,
                back_state=back_state,
                suppress_warning=True,
            )

        # Transition ourself out.
        self.main_window_close()

    def main_window_replace(
        self,
        new_window: MainWindow,
        back_state: MainWindowState | None = None,
        is_auxiliary: bool = False,
    ) -> None:
        """Replace ourself with a new MainWindow."""

        # Users should always check main_window_has_control() *before*
        # creating new MainWindows and passing them in here. Kill the
        # passed window and Error if it seems they did not.
        if not self.main_window_has_control():
            new_window.get_root_widget().delete()
            raise RuntimeError(
                f'main_window_replace() called on a not-in-control window'
                f' ({self}); always check main_window_has_control() before'
                f' calling main_window_replace().'
            )

        # Just shove the old out the left to give the feel that we're
        # adding to the nav stack.
        transition = 'out_left'

        # Transition ourself out.
        try:
            self.on_main_window_close()
        except Exception:
            logging.exception('Error in on_main_window_close() for %s.', self)

        _bauiv1.containerwidget(edit=self._root_widget, transition=transition)
        babase.app.ui_v1.set_main_window(
            new_window,
            from_window=self,
            back_state=back_state,
            is_auxiliary=is_auxiliary,
            suppress_warning=True,
        )

    def on_main_window_close(self) -> None:
        """Called before transitioning out a main window.

        A good opportunity to save window state/etc.
        """

    def get_main_window_state(self) -> MainWindowState:
        """Return a WindowState to recreate this window, if supported."""
        raise NotImplementedError()


class MainWindowState:
    """Persistent state for a specific MainWindow.

    This allows MainWindows to be automatically recreated for back-button
    purposes, when switching app-modes, etc.
    """

    def __init__(self) -> None:
        # The window that back/cancel navigation should take us to.
        self.parent: MainWindowState | None = None
        self.is_top_level: bool | None = None
        self.is_auxiliary: bool | None = None
        self.window_type: type[MainWindow] | None = None
        self.selection: str | None = None

    def create_window(
        self,
        transition: Literal['in_right', 'in_left', 'in_scale'] | None = None,
        origin_widget: bauiv1.Widget | None = None,
    ) -> MainWindow:
        """Create a window based on this state.

        WindowState child classes should override this to recreate their
        particular type of window.
        """
        raise NotImplementedError()


class BasicMainWindowState(MainWindowState):
    """A basic MainWindowState holding a lambda to recreate a MainWindow."""

    def __init__(
        self,
        create_call: Callable[
            [
                Literal['in_right', 'in_left', 'in_scale'] | None,
                bauiv1.Widget | None,
            ],
            bauiv1.MainWindow,
        ],
    ) -> None:
        super().__init__()
        self.create_call = create_call

    @override
    def create_window(
        self,
        transition: Literal['in_right', 'in_left', 'in_scale'] | None = None,
        origin_widget: bauiv1.Widget | None = None,
    ) -> bauiv1.MainWindow:
        return self.create_call(transition, origin_widget)


class MainWindowAutoRecreateSuppress:
    """Suppresses main-window auto-recreate while in existence.

    Can be instantiated and held by windows or processes within windows
    for the purpose of preventing the main-window auto-recreate
    mechanism from firing. This mechanism normally fires when the screen
    is resized or the ui-scale is changed, allowing windows to be
    recreated to adapt to the new configuration.
    """

    def __init__(self) -> None:
        babase.app.ui_v1.window_auto_recreate_suppress_count += 1

    def __del__(self) -> None:
        babase.app.ui_v1.window_auto_recreate_suppress_count -= 1


@dataclass
class UICleanupCheck:
    """Holds info about a uicleanupcheck target."""

    obj: weakref.ref
    widget: bauiv1.Widget
    widget_death_time: float | None


def uicleanupcheck(obj: Any, widget: bauiv1.Widget) -> None:
    """Checks to ensure a widget-owning object gets cleaned up properly.

    This adds a check which will print an error message if the provided
    object still exists ~5 seconds after the provided bauiv1.Widget dies.

    This is a good sanity check for any sort of object that wraps or
    controls a bauiv1.Widget. For instance, a 'Window' class instance has
    no reason to still exist once its root container bauiv1.Widget has fully
    transitioned out and been destroyed. Circular references or careless
    strong referencing can lead to such objects never getting destroyed,
    however, and this helps detect such cases to avoid memory leaks.
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

    assert babase.app.classic is not None
    babase.app.ui_v1.cleanupchecks.append(
        UICleanupCheck(
            obj=weakref.ref(obj), widget=widget, widget_death_time=None
        )
    )


def ui_upkeep() -> None:
    """Run UI cleanup checks, etc. should be called periodically."""
    assert babase.app.classic is not None
    ui = babase.app.ui_v1
    remainingchecks = []
    now = babase.apptime()
    for check in ui.cleanupchecks:
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
    ui.cleanupchecks = remainingchecks


class TextWidgetStringEditAdapter(babase.StringEditAdapter):
    """A StringEditAdapter subclass for editing our text widgets."""

    def __init__(self, text_widget: bauiv1.Widget) -> None:
        self.widget = text_widget

        # Ugly hacks to pull values from widgets. Really need to clean
        # up that api.
        description: Any = _bauiv1.textwidget(query_description=text_widget)
        assert isinstance(description, str)
        initial_text: Any = _bauiv1.textwidget(query=text_widget)
        assert isinstance(initial_text, str)
        max_length: Any = _bauiv1.textwidget(query_max_chars=text_widget)
        assert isinstance(max_length, int)

        screen_space_center = text_widget.get_screen_space_center()

        super().__init__(
            description, initial_text, max_length, screen_space_center
        )

    @override
    def _do_apply(self, new_text: str) -> None:
        if self.widget:
            _bauiv1.textwidget(
                edit=self.widget, text=new_text, adapter_finished=True
            )

    @override
    def _do_cancel(self) -> None:
        if self.widget:
            _bauiv1.textwidget(edit=self.widget, adapter_finished=True)


class RootUIUpdatePause:
    """Pauses updates to the root-ui while in existence."""

    def __init__(self) -> None:
        _bauiv1.root_ui_pause_updates()

    def __del__(self) -> None:
        _bauiv1.root_ui_resume_updates()
