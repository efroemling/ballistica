# Released under the MIT License. See LICENSE for details.
"""A minimal core dialog usable without any UI feature-set."""

import logging
from typing import TYPE_CHECKING

import _babase

from efro.util import strip_exception_tracebacks
from babase._language import Lstr

if TYPE_CHECKING:
    from typing import Callable

logger = logging.getLogger(__name__)


def _eval(val: str | Lstr | None) -> str:
    """Flatten a str / Lstr / None field to a plain string for the engine.

    ``Lstr`` values are evaluated in the current language; ``None`` becomes
    the empty string (which the native side reads as 'no button', etc.).
    """
    if val is None:
        return ''
    if isinstance(val, Lstr):
        return val.evaluate()
    return val


class _Unset:
    """Sentinel type for 'argument not provided' in partial updates."""


_UNSET = _Unset()

#: Live dialogs keyed by native id, so a native button-press can be routed
#: back to the right wrapper (see :func:`dispatch_button`). An entry exists
#: exactly while its dialog is alive (added on create, removed on dismiss).
_dialogs: dict[int, SimpleDialog] = {}


class SimpleDialog:
    """A minimal core dialog: title, optional progress bar, message, button.

    Drawn end-to-end by the engine using only builtin assets (à la the dev
    console), so it can display in any context — gui app-modes, server-mode,
    early boot before any real app-mode is up. That makes it suitable for
    things like asset-package resolve progress and dead-in-the-water errors.

    It is deliberately minimal: a title, an optional progress bar, a
    multi-line message area, and an optional single button. As soon as a real
    UI feature-set is available (with its multi-controller ownership model,
    etc.) prefer that instead.

    The button (when present) fires on a touch/click on it, or on an
    OK/confirm press from any keyboard, game controller, or remote. Pass
    ``on_button`` to be notified; the meaning of the button (Retry, OK, …) and
    what it does are entirely up to the caller.

    Must be created and driven on the logic thread. Call :meth:`dismiss` to
    remove it.
    """

    def __init__(
        self,
        title: str | Lstr = '',
        message: str | Lstr = '',
        *,
        progress: float | None = None,
        button_label: str | Lstr | None = None,
        on_button: Callable[[], None] | None = None,
    ) -> None:
        assert _babase.in_logic_thread()
        self._title = title
        self._message = message
        self._progress = progress
        self._button_label = button_label
        self._on_button = on_button
        self._dismissed = False
        self._id = _babase.simpledialog_create()
        _dialogs[self._id] = self
        self._push()

    def update(
        self,
        *,
        title: str | Lstr | _Unset = _UNSET,
        message: str | Lstr | _Unset = _UNSET,
        progress: float | None | _Unset = _UNSET,
        button_label: str | Lstr | None | _Unset = _UNSET,
        on_button: Callable[[], None] | None | _Unset = _UNSET,
    ) -> None:
        """Update one or more fields; unspecified fields are left as-is.

        Pass ``progress=None`` to hide the bar or ``button_label=None`` to
        hide the button (versus simply omitting them to leave them unchanged).
        """
        assert _babase.in_logic_thread()
        if self._dismissed:
            return
        if not isinstance(title, _Unset):
            self._title = title
        if not isinstance(message, _Unset):
            self._message = message
        if not isinstance(progress, _Unset):
            self._progress = progress
        if not isinstance(button_label, _Unset):
            self._button_label = button_label
        if not isinstance(on_button, _Unset):
            self._on_button = on_button
        self._push()

    def dismiss(self) -> None:
        """Remove the dialog. Idempotent."""
        assert _babase.in_logic_thread()
        if self._dismissed:
            return
        self._dismissed = True
        _dialogs.pop(self._id, None)
        _babase.simpledialog_dismiss(self._id)

    def _push(self) -> None:
        """Push our full current state to the native dialog.

        Any ``Lstr`` fields are evaluated to the current language here, so a
        re-push (e.g. each progress update) picks up the latest translation.
        """
        # Native takes a negative progress as 'no bar' and an empty
        # button-label as 'no button'.
        _babase.simpledialog_update(
            self._id,
            _eval(self._title),
            _eval(self._message),
            -1.0 if self._progress is None else self._progress,
            _eval(self._button_label),
        )


def dispatch_button(dialog_id: int) -> None:
    """Route a native button-press to the owning dialog's callback.

    Called from the engine (logic thread) when a dialog's button is
    activated. Looks the dialog up by id and invokes its ``on_button``.
    """
    dialog = _dialogs.get(dialog_id)
    if dialog is None:
        # Pressed during/after dismissal; nothing to do.
        return
    cb = dialog._on_button  # pylint: disable=protected-access
    if cb is None:
        return
    try:
        cb()
    except Exception as exc:
        logger.exception('Error in SimpleDialog button callback.')
        strip_exception_tracebacks(exc)
