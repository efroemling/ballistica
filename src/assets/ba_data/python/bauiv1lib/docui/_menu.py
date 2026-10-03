# Released under the MIT License. See LICENSE for details.
#
"""The menus doc-ui buttons can pop up."""

from dataclasses import replace
from typing import TYPE_CHECKING
import weakref

import bacommon.docui.v2 as dui2
import bauiv1 as bui
from bauiv1 import _builtinassets

from bauiv1lib.popup import PopupMenuWindow, popup_menu_default_scale

if TYPE_CHECKING:
    from bauiv1lib.popup import PopupWindow
    from bauiv1lib.docui.prep import MenuPrep
    from bauiv1lib.docui._window import DocUIWindow


class DocUIMenuWindow(PopupMenuWindow):
    """The menu popped up by a doc-ui button with a menu action.

    Picking an item runs its action as if the button itself had been
    pressed with it.
    """

    def __init__(
        self,
        window: DocUIWindow,
        widgetid: str,
        button: bui.Widget,
        menu: MenuPrep,
    ) -> None:
        # We live exactly as long as our widgets do (they hold our
        # callbacks), so hold nothing here that holds the window.
        self._window = weakref.ref(window)
        self._widgetid = widgetid
        self._button = button
        self._actions = menu.actions

        # Menus key their choices by string; ours are item indices.
        keys = [str(i) for i in range(len(menu.labels))]

        super().__init__(
            position=button.get_screen_space_center(),
            choices=keys,
            current_choice=None,
            # (Held weakly.)
            delegate=self,
            # A floor; the menu grows to fit its labels.
            width=100.0,
            scale=popup_menu_default_scale(),
            choices_disabled=[
                k for k, off in zip(keys, menu.disabled, strict=True) if off
            ],
            choices_display=menu.labels,
        )

    def popup_menu_selected_choice(
        self, popup_window: PopupWindow, choice: str
    ) -> None:
        """Called when an item is picked."""
        del popup_window  # Unused.

        window = self._window()

        # The page that offered us may have been replaced while we were
        # up (a timed action, a refresh). Its widget ids live on in the
        # new page but our actions are the old page's, so drop the pick.
        if window is None or not self._button:
            return

        action = self._actions[int(choice)]

        if isinstance(action, dui2.Menu):
            bui.uilog.warning(
                'Ignoring MENU action (disallowed in menu items).'
            )
            _builtinassets.audio.error.get().play()
            return

        # A pick already made the menu's sound.
        if isinstance(action, (dui2.Browse, dui2.Replace, dui2.Local)):
            action = replace(action, default_sound=False)

        # Take the global selection back before running anything: a
        # request saves the window's selection first, and we are still
        # onscreen holding it at this point. (See _ColorRowPicker.)
        self._button.global_select()

        window.controller.run_action(window, self._widgetid, action)

    def popup_menu_closing(self, popup_window: PopupWindow) -> None:
        """Called when the menu is closing."""
        # Nothing to do: our button is still its window's selection, so
        # that comes back on its own as we go away. (Selecting it here
        # would also fight whatever a picked action just opened.)
        del popup_window  # Unused.
