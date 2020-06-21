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
"""Functionality for editing config values and applying them to the game."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Tuple, Union, Callable


class ConfigCheckBox:
    """A checkbox wired up to control a config value.

    It will automatically save and apply the config when its
    value changes.

    Attributes:

        widget
            The underlying ba.Widget instance.
    """

    def __init__(self,
                 parent: ba.Widget,
                 configkey: str,
                 position: Tuple[float, float],
                 size: Tuple[float, float],
                 displayname: Union[str, ba.Lstr] = None,
                 scale: float = None,
                 maxwidth: float = None,
                 autoselect: bool = True,
                 value_change_call: Callable[[Any], Any] = None):
        if displayname is None:
            displayname = configkey
        self._value_change_call = value_change_call
        self._configkey = configkey
        self.widget = ba.checkboxwidget(
            parent=parent,
            autoselect=autoselect,
            position=position,
            size=size,
            text=displayname,
            textcolor=(0.8, 0.8, 0.8),
            value=ba.app.config.resolve(configkey),
            on_value_change_call=self._value_changed,
            scale=scale,
            maxwidth=maxwidth)
        # complain if we outlive our checkbox
        ba.uicleanupcheck(self, self.widget)

    def _value_changed(self, val: bool) -> None:
        cfg = ba.app.config
        cfg[self._configkey] = val
        if self._value_change_call is not None:
            self._value_change_call(val)
        cfg.apply_and_commit()


class ConfigNumberEdit:
    """A set of controls for editing a numeric config value.

    It will automatically save and apply the config when its
    value changes.

    Attributes:

        nametext
            The text widget displaying the name.

        valuetext
            The text widget displaying the current value.

        minusbutton
            The button widget used to reduce the value.

        plusbutton
            The button widget used to increase the value.
    """

    def __init__(self,
                 parent: ba.Widget,
                 configkey: str,
                 position: Tuple[float, float],
                 minval: float = 0.0,
                 maxval: float = 100.0,
                 increment: float = 1.0,
                 callback: Callable[[float], Any] = None,
                 xoffset: float = 0.0,
                 displayname: Union[str, ba.Lstr] = None,
                 changesound: bool = True,
                 textscale: float = 1.0):
        if displayname is None:
            displayname = configkey

        self._configkey = configkey
        self._minval = minval
        self._maxval = maxval
        self._increment = increment
        self._callback = callback
        self._value = ba.app.config.resolve(configkey)

        self.nametext = ba.textwidget(parent=parent,
                                      position=position,
                                      size=(100, 30),
                                      text=displayname,
                                      maxwidth=160 + xoffset,
                                      color=(0.8, 0.8, 0.8, 1.0),
                                      h_align='left',
                                      v_align='center',
                                      scale=textscale)
        self.valuetext = ba.textwidget(parent=parent,
                                       position=(246 + xoffset, position[1]),
                                       size=(60, 28),
                                       editable=False,
                                       color=(0.3, 1.0, 0.3, 1.0),
                                       h_align='right',
                                       v_align='center',
                                       text=str(self._value),
                                       padding=2)
        self.minusbutton = ba.buttonwidget(
            parent=parent,
            position=(330 + xoffset, position[1]),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=ba.Call(self._down),
            repeat=True,
            enable_sound=changesound)
        self.plusbutton = ba.buttonwidget(parent=parent,
                                          position=(380 + xoffset,
                                                    position[1]),
                                          size=(28, 28),
                                          label='+',
                                          autoselect=True,
                                          on_activate_call=ba.Call(self._up),
                                          repeat=True,
                                          enable_sound=changesound)
        # Complain if we outlive our widgets.
        ba.uicleanupcheck(self, self.nametext)
        self._update_display()

    def _up(self) -> None:
        self._value = min(self._maxval, self._value + self._increment)
        self._changed()

    def _down(self) -> None:
        self._value = max(self._minval, self._value - self._increment)
        self._changed()

    def _changed(self) -> None:
        self._update_display()
        if self._callback:
            self._callback(self._value)
        ba.app.config[self._configkey] = self._value
        ba.app.config.apply_and_commit()

    def _update_display(self) -> None:
        ba.textwidget(edit=self.valuetext, text=f'{self._value:.1f}')
