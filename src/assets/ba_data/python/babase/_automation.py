# Released under the MIT License. See LICENSE for details.
"""In-game automation helpers for the opt-in FIFO control channel.

.. warning::

   **Unstable, unsupported API.** May change or be removed without
   notice. No backward-compatibility guarantees across versions.
   Use at your own risk.

The automation channel is an optional dev tool that lets external
tools (scripts, test harnesses, Claude Code, etc.) drive a running
game in-process by writing Python lines to ``<silo>/cmd.fifo``,
which a reader thread dispatches on the logic thread.

Two-stage opt-in:

* **Compile time** — the whole subsystem is gated on the
  ``BA_ENABLE_AUTOMATION`` build define (CMake:
  ``-DENABLE_AUTOMATION=ON``). When off, no FIFO is created, no
  native hooks are compiled in, and the helpers below emit a
  ``[automation] <tag> fail not_compiled_in`` line if called.
* **Runtime** — even in builds that compiled it in, the subsystem
  stays dormant unless ``BA_AUTOMATION_FIFO`` is set to a path at
  startup (``tools/pcommand test_game_run`` sets this
  automatically).

This module holds the UI-agnostic helpers. Anything that reaches
into the live widget tree (press/scroll by id or label, widget
inspection, waits) lives in :mod:`bauiv1._automation` so that
base-only spinoffs don't pull in a ``bauiv1`` dependency.

Results of every helper are reported via a single standardized log
line of the form ``[automation] <tag> <status> <payload>`` on the
``ba.app`` logger — external watchers grep that prefix rather than
parse free-form output. ``[automation]`` is the stable marker; the
choice of logger is incidental.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    from typing import Any

automationlog = logging.getLogger('ba.app')

# The automation_* native hooks on _babase are only compiled in when
# BA_ENABLE_AUTOMATION is set. Route dev-hook calls through this
# Any-typed alias so mypy stays happy in builds where the flag is off
# and the stubs reflect that. At runtime we check for the attribute
# explicitly before calling, so public builds emit a structured
# ``not_compiled_in`` failure instead of raising AttributeError.
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

    Emits ``[automation] <tag> fail not_compiled_in`` when the build
    was made without ``BA_ENABLE_AUTOMATION``.
    """
    import os

    if not hasattr(_babase, 'automation_capture_screenshot'):
        _emit(tag, 'fail', 'not_compiled_in')
        return

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

    Exposed so :mod:`bauiv1._automation` can flatten localized labels
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

    Emits ``[automation] <tag> fail not_compiled_in`` when the build
    was made without ``BA_ENABLE_AUTOMATION``, or ``fail
    headless_mode`` when called from a headless build.
    """
    if not hasattr(_babase, 'automation_scroll_at_virtual'):
        _emit(tag, 'fail', 'not_compiled_in')
        return
    try:
        _badev.automation_scroll_at_virtual(x=x, y=y, dx=dx, dy=dy)
    except RuntimeError as exc:
        if 'headless' in str(exc).lower():
            _emit(tag, 'fail', 'headless_mode')
            return
        raise
    _emit(tag, 'ok', f'@ {x:.0f},{y:.0f} d=({dx:+.2f},{dy:+.2f})')
