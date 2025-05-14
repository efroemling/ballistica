# Released under the MIT License. See LICENSE for details.
#
"""Functionality for editing config values and applying them to the game."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class ConfigCheckBox:
    """A checkbox wired up to control a config value.

    It will automatically save and apply the config when its
    value changes.
    """

    widget: bui.Widget
    """The underlying bui.Widget instance."""

    def __init__(
        self,
        parent: bui.Widget,
        configkey: str,
        position: tuple[float, float],
        size: tuple[float, float],
        *,
        displayname: str | bui.Lstr | None = None,
        scale: float | None = None,
        maxwidth: float | None = None,
        autoselect: bool = True,
        value_change_call: Callable[[Any], Any] | None = None,
    ):
        if displayname is None:
            displayname = configkey
        self._value_change_call = value_change_call
        self._configkey = configkey
        self.widget = bui.checkboxwidget(
            parent=parent,
            autoselect=autoselect,
            position=position,
            size=size,
            text=displayname,
            textcolor=(0.8, 0.8, 0.8),
            value=bui.app.config.resolve(configkey),
            on_value_change_call=self._value_changed,
            scale=scale,
            maxwidth=maxwidth,
        )
        # complain if we outlive our checkbox
        bui.uicleanupcheck(self, self.widget)

    def _value_changed(self, val: bool) -> None:
        cfg = bui.app.config
        cfg[self._configkey] = val
        if self._value_change_call is not None:
            self._value_change_call(val)
        cfg.apply_and_commit()


class ConfigNumberEdit:
    """A set of controls for editing a numeric config value.

    It will automatically save and apply the config when its
    value changes.
    """

    nametext: bui.Widget
    """The text widget displaying the name."""

    valuetext: bui.Widget
    """The text widget displaying the current value."""

    minusbutton: bui.Widget
    """The button widget used to reduce the value."""

    plusbutton: bui.Widget
    """The button widget used to increase the value."""

    def __init__(
        self,
        parent: bui.Widget,
        configkey: str,
        position: tuple[float, float],
        *,
        minval: float = 0.0,
        maxval: float = 100.0,
        increment: float = 1.0,
        callback: Callable[[float], Any] | None = None,
        xoffset: float = 0.0,
        displayname: str | bui.Lstr | None = None,
        changesound: bool = True,
        textscale: float = 1.0,
        as_percent: bool = False,
        fallback_value: float = 0.0,
        f: int = 1,
    ):
        if displayname is None:
            displayname = configkey

        self._configkey = configkey
        self._minval = minval
        self._maxval = maxval
        self._increment = increment
        self._callback = callback
        try:
            self._value = bui.app.config.resolve(configkey)
        except KeyError:
            self._value = bui.app.config.get(configkey, fallback_value)
        self._value = (
            self._minval
            if self._minval > self._value
            else self._maxval if self._maxval < self._value else self._value
        )
        self._as_percent = as_percent
        self._f = f

        self.nametext = bui.textwidget(
            parent=parent,
            position=(position[0], position[1] + 12.0),
            size=(0, 0),
            text=displayname,
            maxwidth=150 + xoffset,
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='left',
            v_align='center',
            scale=textscale,
        )
        self.valuetext = bui.textwidget(
            parent=parent,
            position=(position[0] + 216 + xoffset, position[1] + 12.0),
            size=(0, 0),
            editable=False,
            color=(0.3, 1.0, 0.3, 1.0),
            h_align='right',
            v_align='center',
            text=str(self._value),
            padding=2,
        )
        self.minusbutton = bui.buttonwidget(
            parent=parent,
            position=(position[0] + 230 + xoffset, position[1]),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=bui.Call(self._down),
            repeat=True,
            enable_sound=changesound,
        )
        self.plusbutton = bui.buttonwidget(
            parent=parent,
            position=(position[0] + 280 + xoffset, position[1]),
            size=(28, 28),
            label='+',
            autoselect=True,
            on_activate_call=bui.Call(self._up),
            repeat=True,
            enable_sound=changesound,
        )
        # Complain if we outlive our widgets.
        bui.uicleanupcheck(self, self.nametext)
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
        bui.app.config[self._configkey] = self._value
        bui.app.config.apply_and_commit()

    def _update_display(self) -> None:
        if self._as_percent:
            val = f'{round(self._value*100.0)}%'
        else:
            val = f'{self._value:.{self._f}f}'
        bui.textwidget(edit=self.valuetext, text=val)
