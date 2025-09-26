# Released under the MIT License. See LICENSE for details.
#
"""Window related UI bits."""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, override

import babase

import _bauiv1

if TYPE_CHECKING:
    from typing import Any, Type, Literal, Callable

    import bauiv1


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
            babase.app.ui_v1.add_ui_cleanup_check(self, root_widget)

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

        This is called internally by methods such as
        :meth:`main_window_replace()` and :meth:`main_window_back()` so
        generally you do not need to call it directly when using those.
        However you may still opt to check this if doing other actions
        besides main-window navigation (such as displaying pop-ups).
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

            # When leaving an auxiliary window, scale the destination
            # window in instead of sliding to convey that its more of a
            # 'swapping out' than a 'back' action.
            backwin = back_state.create_window(
                transition=(
                    'in_scale' if self.main_window_is_auxiliary else 'in_left'
                )
            )

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
        new_window: MainWindow | Callable[[], MainWindow],
        back_state: MainWindowState | None = None,
        is_auxiliary: bool = False,
    ) -> MainWindow | None:
        """Replace ourself with a new MainWindow.

        Returns the new MainWindow. Will no-op and return None if
        we are not allowed to replace the MainWindow.
        """

        ui = babase.app.ui_v1

        # If they didn't provide an explicit back-state, calc one.
        if back_state is None:
            back_state = ui.save_current_main_window_state()

        if not isinstance(new_window, MainWindow):
            # If we're not in control, we're not allowed to change things.
            if not self.main_window_has_control():
                babase.uilog.debug(
                    'main_window_replace:'
                    ' no-op due to main_window_has_control() returning False.',
                    stack_info=True,
                )
                return None

            new_window = new_window()
        else:
            # We originally were passed MainWindows directly, but want
            # to phase this out, as it prevents our automatic selection
            # save/restore from working (we need to save the old
            # selection *before* the replacement window is created since
            # the creation itself will change the selection).
            warnings.warn(
                'Passing MainWindow objects to main_window_replace() is'
                ' deprecated and will be removed when api 9 support ends.'
                ' You should instead pass calls to generate MainWindow objects.'
                ' So `main_window_replace(MyWin(some_arg))` would become'
                ' `main_win_replace(lambda: MyWin(some_arg))`.',
                DeprecationWarning,
                stacklevel=2,
            )

            # In this old path, users should always check
            # main_window_has_control() *before* creating new
            # MainWindows and passing them in here. Kill the passed
            # window and Error if it seems they did not.
            if not self.main_window_has_control():
                new_window.get_root_widget().delete()
                raise RuntimeError(
                    f'main_window_replace() called on a not-in-control window'
                    f' ({self}); always check main_window_has_control() before'
                    f' calling main_window_replace().'
                )

        # For auxiliary windows, use scale to give a feel that we're
        # switching over to a totally separate 'side quest' ui. For
        # regular back/forward relationships, shove the old out the left
        # to give the feel that we're adding to a nav stack.
        if is_auxiliary:
            transition = 'out_scale'
        else:
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
        return new_window

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
    """A basic MainWindowState.

    Holds some call to recreate a window and optionally a selection to
    restore.
    """

    def __init__(
        self,
        create_call: Callable[
            [
                Literal['in_right', 'in_left', 'in_scale'] | None,
                bauiv1.Widget | None,
            ],
            bauiv1.MainWindow,
        ],
        restore_selection: bool = False,
    ) -> None:
        super().__init__()
        self.create_call = create_call
        self.selection: str | None = None

        if restore_selection:
            sel = _bauiv1.get_selected_widget()
            if sel is not None:
                self.selection = sel.id
                if self.selection is not None:
                    babase.uilog.debug(
                        "Saving ui selection: '%s'.", self.selection
                    )
                else:
                    babase.uilog.warning(
                        'restore_selection=True was passed to'
                        ' BasicMainWindowState but the currently selected'
                        ' widget has no id. All selectable widgets must have'
                        ' ids for selection restore to work properly.'
                        ' Current selection=%s.',
                        sel,
                    )

    @override
    def create_window(
        self,
        transition: Literal['in_right', 'in_left', 'in_scale'] | None = None,
        origin_widget: bauiv1.Widget | None = None,
    ) -> bauiv1.MainWindow:
        win = self.create_call(transition, origin_widget)
        if self.selection is not None:
            widget = _bauiv1.widget_by_id(self.selection)
            if widget is not None:
                widget.global_select()
            else:
                # We expect this to happen sometimes (windows may come
                # up with different UIs visible/etc.). Let's note it but
                # subtly.
                babase.uilog.debug(
                    "Unable to restore selection '%s'; widget not found.",
                    self.selection,
                )

        return win


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
