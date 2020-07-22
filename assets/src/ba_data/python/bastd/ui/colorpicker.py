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
"""Provides popup windows for choosing colors."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
from bastd.ui.popup import PopupWindow

if TYPE_CHECKING:
    from typing import Any, Tuple, Sequence, List, Optional


class ColorPicker(PopupWindow):
    """A popup UI to select from a set of colors.

    Passes the color to the delegate's color_picker_selected_color() method.
    """

    def __init__(self,
                 parent: ba.Widget,
                 position: Tuple[float, float],
                 initial_color: Sequence[float] = (1.0, 1.0, 1.0),
                 delegate: Any = None,
                 scale: float = None,
                 offset: Tuple[float, float] = (0.0, 0.0),
                 tag: Any = ''):
        # pylint: disable=too-many-locals
        from ba.internal import have_pro, get_player_colors

        c_raw = get_player_colors()
        assert len(c_raw) == 16
        self.colors = [c_raw[0:4], c_raw[4:8], c_raw[8:12], c_raw[12:16]]

        uiscale = ba.app.ui.uiscale
        if scale is None:
            scale = (2.3 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)
        self._parent = parent
        self._position = position
        self._scale = scale
        self._offset = offset
        self._delegate = delegate
        self._transitioning_out = False
        self._tag = tag
        self._initial_color = initial_color

        # Create our _root_widget.
        PopupWindow.__init__(self,
                             position=position,
                             size=(210, 240),
                             scale=scale,
                             focus_position=(10, 10),
                             focus_size=(190, 220),
                             bg_color=(0.5, 0.5, 0.5),
                             offset=offset)
        rows: List[List[ba.Widget]] = []
        closest_dist = 9999.0
        closest = (0, 0)
        for y in range(4):
            row: List[ba.Widget] = []
            rows.append(row)
            for x in range(4):
                color = self.colors[y][x]
                dist = (abs(color[0] - initial_color[0]) +
                        abs(color[1] - initial_color[1]) +
                        abs(color[2] - initial_color[2]))
                if dist < closest_dist:
                    closest = (x, y)
                    closest_dist = dist
                btn = ba.buttonwidget(parent=self.root_widget,
                                      position=(22 + 45 * x, 185 - 45 * y),
                                      size=(35, 40),
                                      label='',
                                      button_type='square',
                                      on_activate_call=ba.WeakCall(
                                          self._select, x, y),
                                      autoselect=True,
                                      color=color,
                                      extra_touch_border_scale=0.0)
                row.append(btn)
        other_button = ba.buttonwidget(
            parent=self.root_widget,
            position=(105 - 60, 13),
            color=(0.7, 0.7, 0.7),
            text_scale=0.5,
            textcolor=(0.8, 0.8, 0.8),
            size=(120, 30),
            label=ba.Lstr(resource='otherText',
                          fallback_resource='coopSelectWindow.customText'),
            autoselect=True,
            on_activate_call=ba.WeakCall(self._select_other))

        # Custom colors are limited to pro currently.
        if not have_pro():
            ba.imagewidget(parent=self.root_widget,
                           position=(50, 12),
                           size=(30, 30),
                           texture=ba.gettexture('lock'),
                           draw_controller=other_button)

        # If their color is close to one of our swatches, select it.
        # Otherwise select 'other'.
        if closest_dist < 0.03:
            ba.containerwidget(edit=self.root_widget,
                               selected_child=rows[closest[1]][closest[0]])
        else:
            ba.containerwidget(edit=self.root_widget,
                               selected_child=other_button)

    def get_tag(self) -> Any:
        """Return this popup's tag."""
        return self._tag

    def _select_other(self) -> None:
        from bastd.ui import purchase
        from ba.internal import have_pro

        # Requires pro.
        if not have_pro():
            purchase.PurchaseWindow(items=['pro'])
            self._transition_out()
            return
        ColorPickerExact(parent=self._parent,
                         position=self._position,
                         initial_color=self._initial_color,
                         delegate=self._delegate,
                         scale=self._scale,
                         offset=self._offset,
                         tag=self._tag)

        # New picker now 'owns' the delegate; we shouldn't send it any
        # more messages.
        self._delegate = None
        self._transition_out()

    def _select(self, x: int, y: int) -> None:
        if self._delegate:
            self._delegate.color_picker_selected_color(self, self.colors[y][x])
        ba.timer(0.05, self._transition_out, timetype=ba.TimeType.REAL)

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            if self._delegate is not None:
                self._delegate.color_picker_closing(self)
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        if not self._transitioning_out:
            ba.playsound(ba.getsound('swish'))
        self._transition_out()


class ColorPickerExact(PopupWindow):
    """ pops up a ui to select from a set of colors.
    passes the color to the delegate's color_picker_selected_color() method """

    def __init__(self,
                 parent: ba.Widget,
                 position: Tuple[float, float],
                 initial_color: Sequence[float] = (1.0, 1.0, 1.0),
                 delegate: Any = None,
                 scale: float = None,
                 offset: Tuple[float, float] = (0.0, 0.0),
                 tag: Any = ''):
        # pylint: disable=too-many-locals
        del parent  # Unused var.
        from ba.internal import get_player_colors
        c_raw = get_player_colors()
        assert len(c_raw) == 16
        self.colors = [c_raw[0:4], c_raw[4:8], c_raw[8:12], c_raw[12:16]]

        uiscale = ba.app.ui.uiscale
        if scale is None:
            scale = (2.3 if uiscale is ba.UIScale.SMALL else
                     1.65 if uiscale is ba.UIScale.MEDIUM else 1.23)
        self._delegate = delegate
        self._transitioning_out = False
        self._tag = tag
        self._color = list(initial_color)
        self._last_press_time = ba.time(ba.TimeType.REAL,
                                        ba.TimeFormat.MILLISECONDS)
        self._last_press_color_name: Optional[str] = None
        self._last_press_increasing: Optional[bool] = None
        self._change_speed = 1.0
        width = 180.0
        height = 240.0

        # Creates our _root_widget.
        PopupWindow.__init__(self,
                             position=position,
                             size=(width, height),
                             scale=scale,
                             focus_position=(10, 10),
                             focus_size=(width - 20, height - 20),
                             bg_color=(0.5, 0.5, 0.5),
                             offset=offset)
        self._swatch = ba.imagewidget(parent=self.root_widget,
                                      position=(width * 0.5 - 50, height - 70),
                                      size=(100, 70),
                                      texture=ba.gettexture('buttonSquare'),
                                      color=(1, 0, 0))
        x = 50
        y = height - 90
        self._label_r: ba.Widget
        self._label_g: ba.Widget
        self._label_b: ba.Widget
        for color_name, color_val in [('r', (1, 0.15, 0.15)),
                                      ('g', (0.15, 1, 0.15)),
                                      ('b', (0.15, 0.15, 1))]:
            txt = ba.textwidget(parent=self.root_widget,
                                position=(x - 10, y),
                                size=(0, 0),
                                h_align='center',
                                color=color_val,
                                v_align='center',
                                text='0.12')
            setattr(self, '_label_' + color_name, txt)
            for b_label, bhval, binc in [('-', 30, False), ('+', 75, True)]:
                ba.buttonwidget(parent=self.root_widget,
                                position=(x + bhval, y - 15),
                                scale=0.8,
                                repeat=True,
                                text_scale=1.3,
                                size=(40, 40),
                                label=b_label,
                                autoselect=True,
                                enable_sound=False,
                                on_activate_call=ba.WeakCall(
                                    self._color_change_press, color_name,
                                    binc))
            y -= 42

        btn = ba.buttonwidget(parent=self.root_widget,
                              position=(width * 0.5 - 40, 10),
                              size=(80, 30),
                              text_scale=0.6,
                              color=(0.6, 0.6, 0.6),
                              textcolor=(0.7, 0.7, 0.7),
                              label=ba.Lstr(resource='doneText'),
                              on_activate_call=ba.WeakCall(
                                  self._transition_out),
                              autoselect=True)
        ba.containerwidget(edit=self.root_widget, start_button=btn)

        # Unlike the swatch picker, we stay open and constantly push our
        # color to the delegate, so start doing that.
        self._update_for_color()

    def _update_for_color(self) -> None:
        if not self.root_widget:
            return
        ba.imagewidget(edit=self._swatch, color=self._color)

        # We generate these procedurally, so pylint misses them.
        # FIXME: create static attrs instead.
        ba.textwidget(edit=self._label_r, text='%.2f' % self._color[0])
        ba.textwidget(edit=self._label_g, text='%.2f' % self._color[1])
        ba.textwidget(edit=self._label_b, text='%.2f' % self._color[2])
        if self._delegate is not None:
            self._delegate.color_picker_selected_color(self, self._color)

    def _color_change_press(self, color_name: str, increasing: bool) -> None:
        # If we get rapid-fire presses, eventually start moving faster.
        current_time = ba.time(ba.TimeType.REAL, ba.TimeFormat.MILLISECONDS)
        since_last = current_time - self._last_press_time
        if (since_last < 200 and self._last_press_color_name == color_name
                and self._last_press_increasing == increasing):
            self._change_speed += 0.25
        else:
            self._change_speed = 1.0
        self._last_press_time = current_time
        self._last_press_color_name = color_name
        self._last_press_increasing = increasing

        color_index = ('r', 'g', 'b').index(color_name)
        offs = int(self._change_speed) * (0.01 if increasing else -0.01)
        self._color[color_index] = max(
            0.0, min(1.0, self._color[color_index] + offs))
        self._update_for_color()

    def get_tag(self) -> Any:
        """Return this popup's tag value."""
        return self._tag

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            if self._delegate is not None:
                self._delegate.color_picker_closing(self)
            ba.containerwidget(edit=self.root_widget, transition='out_scale')

    def on_popup_cancel(self) -> None:
        if not self._transitioning_out:
            ba.playsound(ba.getsound('swish'))
        self._transition_out()
