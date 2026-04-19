# Released under the MIT License. See LICENSE for details.
"""In-game automation helpers for use over the dev-build FIFO channel.

This module is the Python-side companion to
``src/ballistica/base/automation/`` — together they form a
dev-build-only control channel that lets external tools (Claude Code,
test scripts, etc.) drive the running game by writing Python lines
to ``<silo>/cmd.fifo``. Each line is exec'd on the logic thread.

The helpers below standardize how automation results are reported back
out of the game: each helper takes an optional ``tag`` and emits a
``[automation] <tag> <status> <payload>`` line via the ``ba.app``
logger so external watchers can ``grep`` for results without parsing
free-form output. The ``[automation]`` prefix is the stable grep
marker; the choice of logger is incidental (we reuse ``ba.app`` to
avoid the cross-repo plumbing that adding a dedicated logger entry
would require).

Only the UI-agnostic helpers live here — anything that reaches into
the widget tree (press/scroll by id or label, wait_for_widget, inspect,
dump_widgets) lives in :mod:`bauiv1.automation` so that base-only
spinoffs don't pull in a ``bauiv1`` dependency.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from typing import Any

automationlog = logging.getLogger('ba.app')

# Dev-build-only native hooks (automation_*) live on _babase but are
# compiled out of non-dev builds, so the standard dummy stubs don't
# include them. Route dev-hook calls through this Any-typed alias so
# mypy stays happy in both variants without per-call type: ignores.
_badev: Any = _babase


def _emit(tag: str, status: str, payload: str = '') -> None:
    """Print the standard ``[automation] <tag> <status> <payload>`` line.

    Always logs at INFO so external watchers don't need to opt in to a
    specific log level. Use ``status`` values like ``ok``, ``fail``,
    ``not_implemented``; ``payload`` is a free-form trailing string
    callers can include identifiers, timings, error messages, etc. in.
    """
    if payload:
        automationlog.info('[automation] %s %s %s', tag, status, payload)
    else:
        automationlog.info('[automation] %s %s', tag, status)


def ping(tag: str = 'ping') -> None:
    """Round-trip sanity check: emits ``[automation] <tag> ok pong``.

    Useful as a "is the channel alive?" probe at the start of a test
    script; if you see the matching line in the log within a tick of
    sending it, the FIFO + reader thread + dispatcher are all healthy.
    """
    _emit(tag, 'ok', 'pong')


def shutdown(tag: str = 'shutdown') -> None:
    """Cleanly quit the running game.

    Wraps ``_babase.quit()`` so external scripts have a single
    consistent way to end an automated session. Emits the marker
    *before* triggering shutdown so the watcher can still see it.
    """
    _emit(tag, 'ok')
    _babase.quit()


def screenshot(path: str, tag: str = 'screenshot') -> None:
    """Save the next-rendered framebuffer as a PNG.

    Fire-and-forget — the actual capture happens on the graphics
    thread between frames; a ``[automation] <tag> ok|fail <details>``
    line lands in the log (``ba.app``) when it completes.

    Path resolution:

    * **Absolute path** (``/tmp/x.png``, ``/Users/.../shot.png``) —
      used as-is. Note: writing outside the project tree will trigger
      sandbox permission prompts.
    * **Relative path or bare filename** (``home.png``,
      ``menus/main.png``) — resolved under the per-instance silo's
      screenshots dir (``<silo>/screenshots/``). That dir is sandbox-
      writable and gets cleaned up automatically when the silo is
      removed via ``rm -rf build/test_run/<n>``.
      Subdirs are created as needed.

    Default-case usage is therefore prompt-free:

    >>> auto.screenshot('main_menu.png')
    # Writes to build/test_run/<instance>/screenshots/main_menu.png

    Native-resolution capture: on retina displays the image will be
    at physical pixel dimensions (e.g. 2880x1800), not logical
    window size. Resize externally if you need a specific dpi.
    """
    import os

    if os.path.isabs(path):
        abs_path = path
    else:
        screenshots_dir = _automation_screenshots_dir()
        os.makedirs(screenshots_dir, exist_ok=True)
        abs_path = os.path.join(screenshots_dir, path)
        # Ensure subdirs in the relative path exist too
        # (e.g. screenshot('menus/main.png')).
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    _badev.automation_capture_screenshot(path=abs_path, tag=tag)


def _automation_screenshots_dir() -> str:
    """Resolve the per-silo screenshots dir from BA_AUTOMATION_FIFO.

    The game is launched with ``BA_AUTOMATION_FIFO=<silo>/cmd.fifo``;
    derive the silo dir from that and append ``screenshots/``. If the
    env var isn't set (shouldn't happen — automation can't be active
    without it) we fall back to the cwd.
    """
    import os

    fifo_path = os.environ.get('BA_AUTOMATION_FIFO')
    if fifo_path:
        silo_dir = os.path.dirname(fifo_path)
        return os.path.join(silo_dir, 'screenshots')
    return os.path.join(os.getcwd(), 'screenshots')


def _evaluate_lstr_json(raw: str) -> str:
    """Evaluate a JSON-encoded :class:`babase.Lstr` blob to its display text.

    Exposed so :mod:`bauiv1.automation` can flatten localized labels
    without reaching into the private ``_babase`` module directly.
    """
    return str(_babase.evaluate_lstr(raw))


def scroll_at(
    x: float,
    y: float,
    dx: float = 0.0,
    dy: float = 0.0,
    *,
    tag: str = 'scroll',
) -> None:
    """Synthesize a mouse-wheel scroll at virtual-screen coords.

    ``dy`` is vertical wheel units — positive scrolls the *content* down
    (wheel up), negative scrolls content up (wheel down) — the sign
    convention mirrors real mouse-wheel events. Same story for ``dx``
    on the horizontal axis.

    Cursor is moved to ``(x, y)`` first since wheel events dispatch to
    whatever widget is under the cursor, so place the coords over the
    scrollable area you actually want to scroll (a character row, the
    outer store container, etc.) rather than off in empty space.

    Typical magnitudes: one physical "notch" of a mouse wheel delivers
    roughly 1.0 unit. Ballistica's scrollwidgets multiply that
    internally, so 1.0–3.0 is a reasonable step; 10+ is a big jump.
    """
    _badev.automation_scroll_at_virtual(x=x, y=y, dx=dx, dy=dy)
    _emit(tag, 'ok', f'@ {x:.0f},{y:.0f} d=({dx:+.2f},{dy:+.2f})')
