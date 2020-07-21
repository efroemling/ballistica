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
"""Popup window/menu related functionality."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Tuple, Any, Sequence, Callable, Optional, List, Union


class PopupWindow:
    """A transient window that positions and scales itself for visibility."""

    def __init__(self,
                 position: Tuple[float, float],
                 size: Tuple[float, float],
                 scale: float = 1.0,
                 offset: Tuple[float, float] = (0, 0),
                 bg_color: Tuple[float, float, float] = (0.35, 0.55, 0.15),
                 focus_position: Tuple[float, float] = (0, 0),
                 focus_size: Tuple[float, float] = None,
                 toolbar_visibility: str = 'menu_minimal_no_back'):
        # pylint: disable=too-many-locals
        if focus_size is None:
            focus_size = size

        # In vr mode we can't have windows going outside the screen.
        if ba.app.vr_mode:
            focus_size = size
            focus_position = (0, 0)

        width = focus_size[0]
        height = focus_size[1]

        # Ok, we've been given a desired width, height, and scale;
        # we now need to ensure that we're all onscreen by scaling down if
        # need be and clamping it to the UI bounds.
        bounds = ba.app.ui_bounds
        edge_buffer = 15
        bounds_width = (bounds[1] - bounds[0] - edge_buffer * 2)
        bounds_height = (bounds[3] - bounds[2] - edge_buffer * 2)

        fin_width = width * scale
        fin_height = height * scale
        if fin_width > bounds_width:
            scale /= (fin_width / bounds_width)
            fin_width = width * scale
            fin_height = height * scale
        if fin_height > bounds_height:
            scale /= (fin_height / bounds_height)
            fin_width = width * scale
            fin_height = height * scale

        x_min = bounds[0] + edge_buffer + fin_width * 0.5
        y_min = bounds[2] + edge_buffer + fin_height * 0.5
        x_max = bounds[1] - edge_buffer - fin_width * 0.5
        y_max = bounds[3] - edge_buffer - fin_height * 0.5

        x_fin = min(max(x_min, position[0] + offset[0]), x_max)
        y_fin = min(max(y_min, position[1] + offset[1]), y_max)

        # ok, we've calced a valid x/y position and a scale based on or
        # focus area. ..now calc the difference between the center of our
        # focus area and the center of our window to come up with the
        # offset we'll need to plug in to the window
        x_offs = ((focus_position[0] + focus_size[0] * 0.5) -
                  (size[0] * 0.5)) * scale
        y_offs = ((focus_position[1] + focus_size[1] * 0.5) -
                  (size[1] * 0.5)) * scale

        self.root_widget = ba.containerwidget(
            transition='in_scale',
            scale=scale,
            toolbar_visibility=toolbar_visibility,
            size=size,
            parent=_ba.get_special_widget('overlay_stack'),
            stack_offset=(x_fin - x_offs, y_fin - y_offs),
            scale_origin_stack_offset=(position[0], position[1]),
            on_outside_click_call=self.on_popup_cancel,
            claim_outside_clicks=True,
            color=bg_color,
            on_cancel_call=self.on_popup_cancel)
        # complain if we outlive our root widget
        ba.uicleanupcheck(self, self.root_widget)

    def on_popup_cancel(self) -> None:
        """Called when the popup is canceled.

        Cancels can occur due to clicking outside the window,
        hitting escape, etc.
        """


class PopupMenuWindow(PopupWindow):
    """A menu built using popup-window functionality."""

    def __init__(self,
                 position: Tuple[float, float],
                 choices: Sequence[str],
                 current_choice: str,
                 delegate: Any = None,
                 width: float = 230.0,
                 maxwidth: float = None,
                 scale: float = 1.0,
                 choices_disabled: Sequence[str] = None,
                 choices_display: Sequence[ba.Lstr] = None):
        # FIXME: Clean up a bit.
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        if choices_disabled is None:
            choices_disabled = []
        if choices_display is None:
            choices_display = []

        # FIXME: For the moment we base our width on these strings so
        #  we need to flatten them.
        choices_display_fin: List[str] = []
        for choice_display in choices_display:
            choices_display_fin.append(choice_display.evaluate())

        if maxwidth is None:
            maxwidth = width * 1.5

        self._transitioning_out = False
        self._choices = list(choices)
        self._choices_display = list(choices_display_fin)
        self._current_choice = current_choice
        self._choices_disabled = list(choices_disabled)
        self._done_building = False
        if not choices:
            raise TypeError('Must pass at least one choice')
        self._width = width
        self._scale = scale
        if len(choices) > 8:
            self._height = 280
            self._use_scroll = True
        else:
            self._height = 20 + len(choices) * 33
            self._use_scroll = False
        self._delegate = None  # don't want this stuff called just yet..

        # extend width to fit our longest string (or our max-width)
        for index, choice in enumerate(choices):
            if len(choices_display_fin) == len(choices):
                choice_display_name = choices_display_fin[index]
            else:
                choice_display_name = choice
            if self._use_scroll:
                self._width = max(
                    self._width,
                    min(
                        maxwidth,
                        _ba.get_string_width(choice_display_name,
                                             suppress_warning=True)) + 75)
            else:
                self._width = max(
                    self._width,
                    min(
                        maxwidth,
                        _ba.get_string_width(choice_display_name,
                                             suppress_warning=True)) + 60)

        # init parent class - this will rescale and reposition things as
        # needed and create our root widget
        PopupWindow.__init__(self,
                             position,
                             size=(self._width, self._height),
                             scale=self._scale)

        if self._use_scroll:
            self._scrollwidget = ba.scrollwidget(parent=self.root_widget,
                                                 position=(20, 20),
                                                 highlight=False,
                                                 color=(0.35, 0.55, 0.15),
                                                 size=(self._width - 40,
                                                       self._height - 40))
            self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
                                                 border=2,
                                                 margin=0)
        else:
            self._offset_widget = ba.containerwidget(parent=self.root_widget,
                                                     position=(30, 15),
                                                     size=(self._width - 40,
                                                           self._height),
                                                     background=False)
            self._columnwidget = ba.columnwidget(parent=self._offset_widget,
                                                 border=2,
                                                 margin=0)
        for index, choice in enumerate(choices):
            if len(choices_display_fin) == len(choices):
                choice_display_name = choices_display_fin[index]
            else:
                choice_display_name = choice
            inactive = (choice in self._choices_disabled)
            wdg = ba.textwidget(parent=self._columnwidget,
                                size=(self._width - 40, 28),
                                on_select_call=ba.Call(self._select, index),
                                click_activate=True,
                                color=(0.5, 0.5, 0.5, 0.5) if inactive else
                                ((0.5, 1, 0.5,
                                  1) if choice == self._current_choice else
                                 (0.8, 0.8, 0.8, 1.0)),
                                padding=0,
                                maxwidth=maxwidth,
                                text=choice_display_name,
                                on_activate_call=self._activate,
                                v_align='center',
                                selectable=(not inactive))
            if choice == self._current_choice:
                ba.containerwidget(edit=self._columnwidget,
                                   selected_child=wdg,
                                   visible_child=wdg)

        # ok from now on our delegate can be called
        self._delegate = weakref.ref(delegate)
        self._done_building = True

    def _select(self, index: int) -> None:
        if self._done_building:
            self._current_choice = self._choices[index]

    def _activate(self) -> None:
        ba.playsound(ba.getsound('swish'))
        ba.timer(0.05, self._transition_out, timetype=ba.TimeType.REAL)
        delegate = self._getdelegate()
        if delegate is not None:
            # Call this in a timer so it doesn't interfere with us killing
            # our widgets and whatnot.
            call = ba.Call(delegate.popup_menu_selected_choice, self,
                           self._current_choice)
            ba.timer(0, call, timetype=ba.TimeType.REAL)

    def _getdelegate(self) -> Any:
        return None if self._delegate is None else self._delegate()

    def _transition_out(self) -> None:
        if not self.root_widget:
            return
        if not self._transitioning_out:
            self._transitioning_out = True
            delegate = self._getdelegate()
            if delegate is not None:
                delegate.popup_menu_closing(self)
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        if not self._transitioning_out:
            ba.playsound(ba.getsound('swish'))
        self._transition_out()


class PopupMenu:
    """A complete popup-menu control.

    This creates a button and wrangles its pop-up menu.
    """

    def __init__(self,
                 parent: ba.Widget,
                 position: Tuple[float, float],
                 choices: Sequence[str],
                 current_choice: str = None,
                 on_value_change_call: Callable[[str], Any] = None,
                 opening_call: Callable[[], Any] = None,
                 closing_call: Callable[[], Any] = None,
                 width: float = 230.0,
                 maxwidth: float = None,
                 scale: float = None,
                 choices_disabled: Sequence[str] = None,
                 choices_display: Sequence[ba.Lstr] = None,
                 button_size: Tuple[float, float] = (160.0, 50.0),
                 autoselect: bool = True):
        # pylint: disable=too-many-locals
        if choices_disabled is None:
            choices_disabled = []
        if choices_display is None:
            choices_display = []
        uiscale = ba.app.ui.uiscale
        if scale is None:
            scale = (2.3 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)
        if current_choice not in choices:
            current_choice = None
        self._choices = list(choices)
        if not choices:
            raise TypeError('no choices given')
        self._choices_display = list(choices_display)
        self._choices_disabled = list(choices_disabled)
        self._width = width
        self._maxwidth = maxwidth
        self._scale = scale
        self._current_choice = (current_choice if current_choice is not None
                                else self._choices[0])
        self._position = position
        self._parent = parent
        if not choices:
            raise TypeError('Must pass at least one choice')
        self._parent = parent
        self._button_size = button_size

        self._button = ba.buttonwidget(
            parent=self._parent,
            position=(self._position[0], self._position[1]),
            autoselect=autoselect,
            size=self._button_size,
            scale=1.0,
            label='',
            on_activate_call=lambda: ba.timer(
                0, self._make_popup, timetype=ba.TimeType.REAL))
        self._on_value_change_call = None  # Don't wanna call for initial set.
        self._opening_call = opening_call
        self._autoselect = autoselect
        self._closing_call = closing_call
        self.set_choice(self._current_choice)
        self._on_value_change_call = on_value_change_call
        self._window_widget: Optional[ba.Widget] = None

        # Complain if we outlive our button.
        ba.uicleanupcheck(self, self._button)

    def _make_popup(self) -> None:
        if not self._button:
            return
        if self._opening_call:
            self._opening_call()
        self._window_widget = PopupMenuWindow(
            position=self._button.get_screen_space_center(),
            delegate=self,
            width=self._width,
            maxwidth=self._maxwidth,
            scale=self._scale,
            choices=self._choices,
            current_choice=self._current_choice,
            choices_disabled=self._choices_disabled,
            choices_display=self._choices_display).root_widget

    def get_button(self) -> ba.Widget:
        """Return the menu's button widget."""
        return self._button

    def get_window_widget(self) -> Optional[ba.Widget]:
        """Return the menu's window widget (or None if nonexistent)."""
        return self._window_widget

    def popup_menu_selected_choice(self, popup_window: PopupWindow,
                                   choice: str) -> None:
        """Called when a choice is selected."""
        del popup_window  # Unused here.
        self.set_choice(choice)
        if self._on_value_change_call:
            self._on_value_change_call(choice)

    def popup_menu_closing(self, popup_window: PopupWindow) -> None:
        """Called when the menu is closing."""
        del popup_window  # Unused here.
        if self._button:
            ba.containerwidget(edit=self._parent, selected_child=self._button)
        self._window_widget = None
        if self._closing_call:
            self._closing_call()

    def set_choice(self, choice: str) -> None:
        """Set the selected choice."""
        self._current_choice = choice
        displayname: Union[str, ba.Lstr]
        if len(self._choices_display) == len(self._choices):
            displayname = self._choices_display[self._choices.index(choice)]
        else:
            displayname = choice
        if self._button:
            ba.buttonwidget(edit=self._button, label=displayname)
