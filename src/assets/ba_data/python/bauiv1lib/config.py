# Released under the MIT License. See LICENSE for details.
#
"""Functionality for editing config values and applying them to the game."""

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
        displayname: str | bui.Lstr | bui.LangStr | None = None,
        scale: float | None = None,
        maxwidth: float | None = None,
        autoselect: bool = True,
        value_change_call: Callable[[Any], Any] | None = None,
        check_box_id: str | None = None,
    ):
        if displayname is None:
            displayname = configkey
        self._value_change_call = value_change_call
        self._configkey = configkey
        self.widget = bui.checkboxwidget(
            parent=parent,
            id=check_box_id,
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
        # Complain if we outlive our checkbox.
        bui.app.ui_v1.add_ui_cleanup_check(self, self.widget)

    def _value_changed(self, val: bool) -> None:
        cfg = bui.app.config
        cfg[self._configkey] = val
        if self._value_change_call is not None:
            self._value_change_call(val)
        cfg.apply_and_commit()


#: Where a control's editing widgets begin, measured from the row's
#: position. Shared so a row keeps its layout when its control is swapped
#: for a different kind.
CONTROL_X_OFFSET = 230.0

#: Height of a row's editing widgets.
CONTROL_HEIGHT = 28.0

#: Default for how often a drag in progress applies its value to the
#: running app. Paced for what accompanies an apply -- a sound, a music
#: level shifting -- rather than for the cost of the apply itself; those
#: read as busy well before they become expensive. Note this throttles
#: only the apply: whatever a control refreshes cheaply per drag step
#: (its value text, say) is not on this clock. A row wanting a different
#: pace passes its own ``drag_apply_interval`` -- slower where an apply
#: is audible, faster where it drives something visible on screen.
DRAG_APPLY_INTERVAL = 0.25


class _NumericConfigControl:
    """Shared plumbing for the numeric-config controls below.

    Owns the config round-trip (read at construction, write on change),
    the value formatting, and the name/value labels every such row has;
    subclasses add whatever widgets actually do the editing.

    This lives apart from either control on purpose. The two differ in
    how they are driven and laid out but not at all in what they do to
    the config, so sharing that here is what lets ConfigSlider exist
    without ConfigNumberEdit growing a mode flag and a set of arguments
    that are inert half the time.
    """

    nametext: bui.Widget
    """The text widget displaying the name."""

    valuetext: bui.Widget
    """The text widget displaying the current value."""

    def __init__(
        self,
        parent: bui.Widget,
        configkey: str,
        position: tuple[float, float],
        *,
        minval: float,
        maxval: float,
        increment: float,
        callback: Callable[[float], Any] | None,
        xoffset: float,
        displayname: str | bui.Lstr | bui.LangStr | None,
        textscale: float,
        as_percent: bool,
        fallback_value: float,
        f: int,
    ) -> None:
        if displayname is None:
            displayname = configkey

        self._configkey = configkey
        self._minval = minval
        self._maxval = maxval
        self._increment = increment
        self._callback = callback
        self._as_percent = as_percent
        self._f = f

        try:
            value = bui.app.config.resolve(configkey)
        except KeyError:
            value = bui.app.config.get(configkey, fallback_value)
        self._value = min(maxval, max(minval, value))

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
        # Complain if we outlive our widgets.
        bui.app.ui_v1.add_ui_cleanup_check(self, self.nametext)

    def _update_display(self) -> None:
        if self._as_percent:
            val = f'{round(self._value*100.0)}%'
        else:
            val = f'{self._value:.{self._f}f}'
        bui.textwidget(edit=self.valuetext, text=val)

    def _store_value(
        self, *, commit: bool = True, run_callback: bool = True
    ) -> None:
        """Apply our value to the running app, optionally saving it too.

        Pass ``commit=False`` while a value is still being settled on --
        the app hears the change, but nothing is scheduled for disk until
        the user is done.

        Any ``callback`` runs afterwards, once per applied value. For a
        control being dragged that is the throttled cadence rather than
        every step, and it is guaranteed for the value finally settled
        on -- so it is the place to hang whatever should accompany a
        value landing.
        """
        bui.app.config[self._configkey] = self._value
        if commit:
            bui.app.config.apply_and_commit()
        else:
            bui.app.config.apply()
        if run_callback:
            self._run_callback()

    def _run_callback(self) -> None:
        if self._callback is not None:
            self._callback(self._value)


class ConfigNumberEdit(_NumericConfigControl):
    """A set of controls for editing a numeric config value.

    It will automatically save and apply the config when its
    value changes.
    """

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
        displayname: str | bui.Lstr | bui.LangStr | None = None,
        changesound: bool = True,
        textscale: float = 1.0,
        as_percent: bool = False,
        fallback_value: float = 0.0,
        f: int = 1,
        idprefix: str | None = None,
    ):
        super().__init__(
            parent,
            configkey,
            position,
            minval=minval,
            maxval=maxval,
            increment=increment,
            callback=callback,
            xoffset=xoffset,
            displayname=displayname,
            textscale=textscale,
            as_percent=as_percent,
            fallback_value=fallback_value,
            f=f,
        )
        self.minusbutton = bui.buttonwidget(
            parent=parent,
            id=None if idprefix is None else f'{idprefix}|minus',
            position=(position[0] + CONTROL_X_OFFSET + xoffset, position[1]),
            size=(CONTROL_HEIGHT, CONTROL_HEIGHT),
            label='-',
            autoselect=True,
            on_activate_call=bui.CallStrict(self._down),
            repeat=True,
            enable_sound=changesound,
        )
        self.plusbutton = bui.buttonwidget(
            parent=parent,
            id=None if idprefix is None else f'{idprefix}|plus',
            position=(position[0] + 280 + xoffset, position[1]),
            size=(CONTROL_HEIGHT, CONTROL_HEIGHT),
            label='+',
            autoselect=True,
            on_activate_call=bui.CallStrict(self._up),
            repeat=True,
            enable_sound=changesound,
        )
        self._update_display()

    def _up(self) -> None:
        self._value = min(self._maxval, self._value + self._increment)
        self._changed()

    def _down(self) -> None:
        self._value = max(self._minval, self._value - self._increment)
        self._changed()

    def _changed(self) -> None:
        self._update_display()
        self._store_value()


class ConfigSlider(_NumericConfigControl):
    """A slider for editing a numeric config value.

    Same config behavior as :class:`ConfigNumberEdit` -- it reads the
    value at construction and saves and applies it on change -- but
    driven by a draggable slider rather than a +/- pair. It begins where
    that pair does, so swapping one for the other leaves the rest of a
    settings row where it was.
    """

    slider: bui.Widget
    """The underlying slider bui.Widget instance."""

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
        width: float = 200.0,
        displayname: str | bui.Lstr | bui.LangStr | None = None,
        textscale: float = 1.0,
        as_percent: bool = False,
        fallback_value: float = 0.0,
        f: int = 1,
        idprefix: str | None = None,
        drag_apply_interval: float = DRAG_APPLY_INTERVAL,
    ):
        super().__init__(
            parent,
            configkey,
            position,
            minval=minval,
            maxval=maxval,
            increment=increment,
            callback=callback,
            xoffset=xoffset,
            displayname=displayname,
            textscale=textscale,
            as_percent=as_percent,
            fallback_value=fallback_value,
            f=f,
        )
        self._drag_apply_interval = drag_apply_interval
        self._apply_timer: bui.AppTimer | None = None
        self._next_apply_time = 0.0
        self._pending: str | None = None

        self.slider = bui.sliderwidget(
            parent=parent,
            id=None if idprefix is None else f'{idprefix}|slider',
            position=(position[0] + CONTROL_X_OFFSET + xoffset, position[1]),
            size=(width, CONTROL_HEIGHT),
            min_value=minval,
            max_value=maxval,
            increment=increment,
            value=self._value,
            # As with ConfigNumberEdit's buttons -- without this,
            # directional navigation falls back to legacy list-order
            # looping and cannot reach the toolbars.
            autoselect=True,
            on_drag_call=self._slider_dragged,
            on_change_call=self._slider_changed,
        )
        self._update_display()

    def _slider_dragged(self, value: float) -> None:
        self._value = value

        # Updating the text is cheap, so keep it exact at every step.
        self._update_display()
        self._schedule('drag')

    def _slider_changed(self, value: float) -> None:
        self._value = value
        self._update_display()

        # A settled value is saved right now, never behind a timer --
        # correctness should not depend on one still being alive. Only
        # what *accompanies* the value keeps its spacing, which is what
        # scheduling below is for.
        self._store_value(commit=True, run_callback=False)
        self._schedule('settled')

    def _schedule(self, action: str) -> None:
        """Run an action now, or when the interval next comes round.

        Both the drag and settled paths go through here so they share one
        clock: letting go right after a drag update no longer lands a
        second callback on top of the first.

        Note the *trailing* edge -- rather than dropping actions that
        arrive too soon we arm a timer for when the next one is due. That
        is what guarantees the value we settle on is applied even if it
        arrived mid-interval.
        """
        # A later action supersedes a pending earlier one; 'settled' has
        # already stored, so a pending 'drag' store would be redundant.
        self._pending = action
        now = bui.apptime()
        if now >= self._next_apply_time:
            self._run_pending()
        elif self._apply_timer is None:
            self._apply_timer = bui.AppTimer(
                self._next_apply_time - now, bui.WeakCall(self._run_pending)
            )

    def _run_pending(self) -> None:
        self._apply_timer = None
        self._next_apply_time = bui.apptime() + self._drag_apply_interval
        action, self._pending = self._pending, None

        # Deliberately acts on our *current* value rather than one
        # captured when the timer was armed. A later drag update then
        # supersedes an earlier pending one with no bookkeeping -- and a
        # cancelled drag, which reaches us as an ordinary drag call
        # carrying the restored value, is handled like any other. That is
        # why nothing here needs to know a cancel happened.
        if action == 'drag':
            self._store_value(commit=False)
        elif action == 'settled':
            self._run_callback()
