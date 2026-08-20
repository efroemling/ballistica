# Released under the MIT License. See LICENSE for details.
"""In-game automation helpers for the opt-in control channel.

.. warning::

   **Unstable, unsupported API.** May change or be removed without
   notice. No backward-compatibility guarantees across versions.
   Use at your own risk.

Automation is an optional dev tool that lets external tools (scripts,
test harnesses, Claude Code, etc.) drive a running game in-process.
These helpers run wherever driver-supplied Python is exec'd: over the
automation channel to the game's basn node (see
:mod:`baplus._automationsession` and ``tools/pcommand
automation_drive``), or through the cloud console.

Gating:

* **Compile time** — the whole subsystem is gated on the
  ``BA_ENABLE_AUTOMATION`` build define (CMake:
  ``-DENABLE_AUTOMATION=ON``). When off, no native hooks are compiled
  in, and the helpers below emit a ``[automation] <tag> fail
  not_compiled_in`` line if called.
* **Runtime** — in builds that compiled it in, the native
  capabilities are stood up on developer builds. Offering the game
  up for *remote* driving additionally requires the channel's own
  runtime opt-in (``BA_AUTOMATION_CHANNEL``; ``tools/pcommand
  test_game_run --automation-channel`` sets it).

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


def available() -> bool:
    """Whether automation was compiled into this build.

    The native hooks are simply absent otherwise, so this is a
    legitimate question to ask in any build -- unlike a build-flavor
    attribute, which may not exist to be read at all.

    Exists for callers outside babase (the automation channel lives
    in baplus, which may not reach the private ``_babase`` module) so
    they need not reimplement the check.
    """
    return hasattr(_babase, 'automation_capture_screenshot')


def ping(tag: str = 'ping') -> None:
    """Round-trip sanity check: emits ``[automation] <tag> ok pong``.

    Useful as a "is the channel alive?" probe at the start of a test
    script; if you see the matching line in the log within a tick of
    sending it, the automation dispatch path is all healthy.
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
    """Save the next-rendered framebuffer as an image file.

    Fire-and-forget — the actual capture happens in the graphics
    context between frames; a ``[automation] <tag> ok|fail <details>``
    line lands in the log (``ba.app``) when it completes.

    The path's extension picks the format — **prefer ``.jpg``**: it
    gets lossy JPEG, which for photographic game frames is a fraction
    of PNG's size (what makes captures cheap to store and move over
    the wire). Any other extension gets lossless PNG, which should
    only be used where pixel-perfect data is actually needed
    (exact-color assertions, render-output comparisons, etc.).

    This writes on the *device*. A remote driver that wants the bytes
    should use ``automation_drive --screenshot`` instead, which
    captures to a temp file and ships the image back.

    Path resolution:

    * **Absolute path** (``/tmp/x.jpg``, ``/Users/.../shot.jpg``) —
      used as-is.
    * **Relative path or bare filename** (``home.jpg``,
      ``menus/main.jpg``) — resolved under ``screenshots/`` beneath
      the process cwd; subdirs are created as needed.

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
        # (e.g. screenshot('menus/main.jpg')).
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    _badev.automation_capture_screenshot(path=abs_path, tag=tag)


def _automation_screenshots_dir() -> str:
    """Dir a relative screenshot path resolves under.

    ``screenshots/`` beneath the process cwd. This is only for code
    that execs ``screenshot('foo.jpg')`` on the device directly; a
    remote driver's ``--screenshot`` captures to a temp file and
    ships the bytes back instead (see ``baplus._automationsession``).
    """
    import os

    return os.path.join(os.getcwd(), 'screenshots')


def _evaluate_lstr_json(raw: str) -> str:
    """Evaluate a JSON-encoded :class:`babase.Lstr` blob to its display text.

    Exposed so :mod:`bauiv1._automation` can flatten localized labels
    without reaching into the private ``_babase`` module directly.
    """
    return str(_babase.evaluate_lstr(raw))


def click_at(x: float, y: float, *, tag: str = 'click') -> None:
    """Synthesize a mouse click at virtual-screen coords.

    Coords are absolute virtual-screen, origin **bottom-left**, y
    growing upward (the OpenGL convention the rest of the automation
    surface uses). To convert from a screenshot pixel ``(px, py)``
    measured top-left in an image of size ``(iw, ih)``::

        vx = px * vw / iw
        vy = vh - py * vh / ih

    where ``(vw, vh)`` is :func:`babase.get_virtual_screen_size()`.

    Prefer :func:`bauiv1._automation.press_by_id` or ``press_by_label``
    whenever the target is a widget you can name -- they are stable
    against layout changes, where coords are not. This exists for the
    cases those cannot reach: overlays and popups that never appear in
    the main-window widget tree (the get-remote window, for one), and
    non-widget hit targets.

    Emits ``[automation] <tag> fail not_compiled_in`` when the build
    was made without ``BA_ENABLE_AUTOMATION``, or ``fail
    headless_mode`` when called from a headless build.
    """
    if not hasattr(_babase, 'automation_press_at_virtual'):
        _emit(tag, 'fail', 'not_compiled_in')
        return
    try:
        _badev.automation_press_at_virtual(button=1, x=x, y=y)
    except RuntimeError as exc:
        if 'headless' in str(exc).lower():
            _emit(tag, 'fail', 'headless_mode')
            return
        raise
    _emit(tag, 'ok', f'@ {x:.0f},{y:.0f}')


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
