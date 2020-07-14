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
"""Provide top level UI related functionality."""

from __future__ import annotations

import os
import weakref
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, Type

import _ba
from ba._enums import TimeType

if TYPE_CHECKING:
    from typing import Optional, List, Any
    from weakref import ReferenceType

    import ba

# Set environment variable BA_DEBUG_UI_CLEANUP_CHECKS to 1
# to print detailed info about what is getting cleaned up when.
DEBUG_UI_CLEANUP_CHECKS = os.environ.get('BA_DEBUG_UI_CLEANUP_CHECKS') == '1'


class Window:
    """A basic window.

    Category: User Interface Classes
    """

    def __init__(self, root_widget: ba.Widget):
        self._root_widget = root_widget

    def get_root_widget(self) -> ba.Widget:
        """Return the root widget."""
        return self._root_widget


@dataclass
class UICleanupCheck:
    """Holds info about a uicleanupcheck target."""
    obj: ReferenceType
    widget: ba.Widget
    widget_death_time: Optional[float]


class UILocation:
    """Defines a specific 'place' in the UI the user can navigate to.

    Category: User Interface Classes
    """

    def __init__(self) -> None:
        pass

    def save_state(self) -> None:
        """Serialize this instance's state to a dict."""

    def restore_state(self) -> None:
        """Restore this instance's state from a dict."""

    def push_location(self, location: str) -> None:
        """Push a new location to the stack and transition to it."""


class UILocationWindow(UILocation):
    """A UILocation consisting of a single root window widget.

    Category: User Interface Classes
    """

    def __init__(self) -> None:
        super().__init__()
        self._root_widget: Optional[ba.Widget] = None

    def get_root_widget(self) -> ba.Widget:
        """Return the root widget for this window."""
        assert self._root_widget is not None
        return self._root_widget


class UIEntry:
    """State for a UILocation on the stack."""

    def __init__(self, name: str, controller: UIController):
        self._name = name
        self._state = None
        self._args = None
        self._instance: Optional[UILocation] = None
        self._controller = weakref.ref(controller)

    def create(self) -> None:
        """Create an instance of our UI."""
        cls = self._get_class()
        self._instance = cls()

    def destroy(self) -> None:
        """Transition out our UI if it exists."""
        if self._instance is None:
            return
        print('WOULD TRANSITION OUT', self._name)

    def _get_class(self) -> Type[UILocation]:
        """Returns the UI class our name points to."""
        # pylint: disable=cyclic-import

        # TEMP HARD CODED - WILL REPLACE THIS WITH BA_META LOOKUPS.
        if self._name == 'mainmenu':
            from bastd.ui import mainmenu
            return cast(Type[UILocation], mainmenu.MainMenuWindow)
        raise ValueError('unknown ui class ' + str(self._name))


class UIController:
    """Wrangles UILocations.

    Category: User Interface Classes
    """

    def __init__(self) -> None:

        # FIXME: document why we have separate stacks for game and menu...
        self._main_stack_game: List[UIEntry] = []
        self._main_stack_menu: List[UIEntry] = []

        # This points at either the game or menu stack.
        self._main_stack: Optional[List[UIEntry]] = None

        # There's only one of these since we don't need to preserve its state
        # between sessions.
        self._dialog_stack: List[UIEntry] = []

    def show_main_menu(self, in_game: bool = True) -> None:
        """Show the main menu, clearing other UIs from location stacks."""
        self._main_stack = []
        self._dialog_stack = []
        self._main_stack = (self._main_stack_game
                            if in_game else self._main_stack_menu)
        self._main_stack.append(UIEntry('mainmenu', self))
        self._update_ui()

    def _update_ui(self) -> None:
        """Instantiate the topmost ui in our stacks."""

        # First tell any existing UIs to get outta here.
        for stack in (self._dialog_stack, self._main_stack):
            assert stack is not None
            for entry in stack:
                entry.destroy()

        # Now create the topmost one if there is one.
        entrynew = (self._dialog_stack[-1] if self._dialog_stack else
                    self._main_stack[-1] if self._main_stack else None)
        if entrynew is not None:
            entrynew.create()


def uicleanupcheck(obj: Any, widget: ba.Widget) -> None:
    """Add a check to ensure a widget-owning object gets cleaned up properly.

    Category: User Interface Functions

    This adds a check which will print an error message if the provided
    object still exists ~5 seconds after the provided ba.Widget dies.

    This is a good sanity check for any sort of object that wraps or
    controls a ba.Widget. For instance, a 'Window' class instance has
    no reason to still exist once its root container ba.Widget has fully
    transitioned out and been destroyed. Circular references or careless
    strong referencing can lead to such objects never getting destroyed,
    however, and this helps detect such cases to avoid memory leaks.
    """
    if DEBUG_UI_CLEANUP_CHECKS:
        print(f'adding uicleanup to {obj}')
    if not isinstance(widget, _ba.Widget):
        raise TypeError('widget arg is not a ba.Widget')

    if bool(False):

        def foobar() -> None:
            """Just testing."""
            if DEBUG_UI_CLEANUP_CHECKS:
                print('uicleanupcheck widget dying...')

        widget.add_delete_callback(foobar)

    _ba.app.ui.cleanupchecks.append(
        UICleanupCheck(obj=weakref.ref(obj),
                       widget=widget,
                       widget_death_time=None))


def ui_upkeep() -> None:
    """Run UI cleanup checks, etc. should be called periodically."""
    ui = _ba.app.ui
    remainingchecks = []
    now = _ba.time(TimeType.REAL)
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
                    'WARNING:', obj,
                    'is still alive 5 second after its widget died;'
                    ' you probably have a memory leak.')
            else:
                remainingchecks.append(check)
    ui.cleanupchecks = remainingchecks
