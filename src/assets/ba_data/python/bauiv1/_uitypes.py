# Released under the MIT License. See LICENSE for details.
#
"""Misc UI related types."""

import os
import time
import inspect
import warnings
from typing import TYPE_CHECKING, override

import babase

import _bauiv1

if TYPE_CHECKING:
    from typing import Any, Type, Literal, Callable

    import bauiv1


def snap_slider_value(
    value: float, *, min_value: float, max_value: float, increment: float
) -> float:
    """A :func:`bauiv1.sliderwidget` value, cleaned up for storing.

    The widget works in single precision and snaps to its increment
    grid in that arithmetic, so it reports things like
    ``0.800000011920929`` for the ``0.8`` a user picked. This returns
    the value at the same grid point in the decimal form the user
    would write, clamped to the range -- what config files and page
    state should hold. Every consumer of slider values goes through
    here so they agree on it.

    An ``increment`` of zero or less means no grid; the value is
    only clamped.
    """
    if increment <= 0.0:
        snapped = value
    else:
        steps = round((value - min_value) / increment)
        # (Nine decimals: past single precision's own noise but well
        # short of double's, so the grid value comes out exact.)
        snapped = round(min_value + steps * increment, 9)
    return float(min(max_value, max(min_value, snapped)))


# REMOVE WHEN API 9 SUPPORT ENDS
def uicleanupcheck(obj: Any, widget: bauiv1.Widget) -> None:
    """
    .. deprecated:: 1.7.51
       Use :meth:`UIV1AppSubsystem.add_ui_cleanup_check()`.
       Will be removed when api 9 support ends.
    """
    warnings.warn(
        'bauiv1.uicleanupcheck() will be removed when api 9 support ends;'
        ' use ba*.app.ui_v1.add_ui_cleanup_check() instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    babase.app.ui_v1.add_ui_cleanup_check(obj, widget)


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
        is_password: Any = _bauiv1.textwidget(query_password=text_widget)
        assert isinstance(is_password, bool)
        kind_val: Any = _bauiv1.textwidget(query_string_edit_kind=text_widget)
        assert isinstance(kind_val, str)

        screen_space_center = text_widget.get_screen_space_center()

        super().__init__(
            description,
            initial_text,
            max_length,
            screen_space_center,
            is_password=is_password,
            kind=babase.StringEditKind(kind_val),
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

    @override
    def _do_submit(self) -> None:
        if self.widget:
            _bauiv1.textwidget(edit=self.widget, invoke_submit=True)


class RootUIUpdatePause:
    """Pauses updates to the root-ui while in existence.

    Instances are expected to be short-lived (covering an animation or
    a server round-trip). Long holds get logged as warnings naming the
    creation site; a common cause is an instance caught in a reference
    cycle, where its release waits on the next explicit gc pass instead
    of happening immediately (see :class:`~babase.GarbageCollectionSubsystem`).
    """

    #: Holds at or beyond this many seconds log a warning at release.
    LONG_HOLD_WARN_THRESHOLD = 10.0

    def __init__(self) -> None:
        # Note where we were created, for long-hold warnings. We pull
        # simple strings out of the calling frame and immediately drop
        # it; storing the frame itself would create exactly the sort of
        # reference cycle that makes these holds go long.
        frame = inspect.currentframe()
        caller = frame.f_back if frame is not None else None
        if caller is not None:
            self._created_at = (
                f'{caller.f_code.co_qualname}'
                f' ({os.path.basename(caller.f_code.co_filename)}'
                f':{caller.f_lineno})'
            )
        else:
            self._created_at = '<unknown>'
        del caller
        del frame
        self._created_time = time.monotonic()
        _bauiv1.root_ui_pause_updates()

    def __del__(self) -> None:
        _bauiv1.root_ui_resume_updates()
        held = time.monotonic() - self._created_time
        if held >= self.LONG_HOLD_WARN_THRESHOLD:
            babase.uilog.warning(
                'RootUIUpdatePause created by %s was held %.1f seconds;'
                ' expected to be brief. A hold ending only when gc runs'
                ' implies the instance was stuck in a reference cycle.',
                self._created_at,
                held,
            )


class UIOpenState:
    """Keeps ui informed that something is open.

    Generally instances of this are assigned as a class member of some
    UI class, which will then keep the UI informed upon its death.

    It is valid to have multiple states for one tag; the UI will keep a
    tally.
    """

    __slots__ = ['stateid', '_dormant']

    def __init__(self, stateid: str) -> None:
        self.stateid = stateid
        self._dormant = False
        _bauiv1.ui_open_state_change(self.stateid, 1)

    @property
    def dormant(self) -> bool:
        """Whether this state is currently not counting as open."""
        return self._dormant

    def set_dormant(self, dormant: bool) -> None:
        """Stop (or resume) counting as open while staying alive.

        For states held somewhere that isn't actually showing anything,
        such as a saved UI state waiting to be restored after a game.
        """
        if dormant == self._dormant:
            return
        self._dormant = dormant
        _bauiv1.ui_open_state_change(self.stateid, -1 if dormant else 1)

    def __del__(self) -> None:
        if not self._dormant:
            _bauiv1.ui_open_state_change(self.stateid, -1)
