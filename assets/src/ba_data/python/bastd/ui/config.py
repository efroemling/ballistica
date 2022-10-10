# Released under the MIT License. See LICENSE for details.
#
"""Functionality for editing config values and applying them to the game."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Callable


class ConfigCheckBox:
    """A checkbox wired up to control a config value.

    It will automatically save and apply the config when its
    value changes.
    """

    widget: ba.Widget
    """The underlying ba.Widget instance."""

    def __init__(
        self,
        parent: ba.Widget,
        configkey: str,
        position: tuple[float, float],
        size: tuple[float, float],
        displayname: str | ba.Lstr | None = None,
        scale: float | None = None,
        maxwidth: float | None = None,
        autoselect: bool = True,
        value_change_call: Callable[[Any], Any] | None = None,
    ):
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
            maxwidth=maxwidth,
        )
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
    """

    nametext: ba.Widget
    """The text widget displaying the name."""

    valuetext: ba.Widget
    """The text widget displaying the current value."""

    minusbutton: ba.Widget
    """The button widget used to reduce the value."""

    plusbutton: ba.Widget
    """The button widget used to increase the value."""

    def __init__(
        self,
        parent: ba.Widget,
        configkey: str,
        position: tuple[float, float],
        minval: float = 0.0,
        maxval: float = 100.0,
        increment: float = 1.0,
        callback: Callable[[float], Any] | None = None,
        xoffset: float = 0.0,
        displayname: str | ba.Lstr | None = None,
        changesound: bool = True,
        textscale: float = 1.0,
    ):
        if displayname is None:
            displayname = configkey

        self._configkey = configkey
        self._minval = minval
        self._maxval = maxval
        self._increment = increment
        self._callback = callback
        self._value = ba.app.config.resolve(configkey)

        self.nametext = ba.textwidget(
            parent=parent,
            position=position,
            size=(100, 30),
            text=displayname,
            maxwidth=160 + xoffset,
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='left',
            v_align='center',
            scale=textscale,
        )
        self.valuetext = ba.textwidget(
            parent=parent,
            position=(246 + xoffset, position[1]),
            size=(60, 28),
            editable=False,
            color=(0.3, 1.0, 0.3, 1.0),
            h_align='right',
            v_align='center',
            text=str(self._value),
            padding=2,
        )
        self.minusbutton = ba.buttonwidget(
            parent=parent,
            position=(330 + xoffset, position[1]),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=ba.Call(self._down),
            repeat=True,
            enable_sound=changesound,
        )
        self.plusbutton = ba.buttonwidget(
            parent=parent,
            position=(380 + xoffset, position[1]),
            size=(28, 28),
            label='+',
            autoselect=True,
            on_activate_call=ba.Call(self._up),
            repeat=True,
            enable_sound=changesound,
        )
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
