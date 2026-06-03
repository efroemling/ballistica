# Released under the MIT License. See LICENSE for details.
#
"""An asyncio event loop backed by the logic thread's C++ EventLoop."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
import asyncio

import _babase

if TYPE_CHECKING:
    from typing import Callable
    import contextvars


class _BATimerHandle(asyncio.TimerHandle):
    """A TimerHandle that owns the babase.AppTimer backing it.

    asyncio's Handle/TimerHandle use ``__slots__``, so we add a slot to
    stash the AppTimer. Dropping that reference cancels the underlying C++
    timer (see babase.AppTimer's dealloc), which is how call_later
    cancellation is implemented.
    """

    __slots__ = ('_ba_timer',)

    _ba_timer: _babase.AppTimer | None


class BAEventLoop(asyncio.base_events.BaseEventLoop):
    """An asyncio event loop driven by the logic thread's C++ EventLoop.

    Rather than running its own selector-based loop, this routes asyncio's
    scheduling primitives onto the engine's event loop:

    - ``call_soon`` / ``call_soon_threadsafe`` ->
      ``_babase.pushcall(.., raw=True)`` (a PushCall to the logic thread,
      which is thread-safe and immediately notifies the loop's condition
      variable). That CV wake is the whole point: ``run_in_executor``
      completions resume the awaiting coroutine with sub-millisecond
      latency instead of waiting for a periodic pump.
    - ``call_later`` / ``call_at`` -> ``_babase.AppTimer`` (app-time timer).
    - ``time()`` -> ``_babase.apptime()``.

    The loop is never run via ``run_forever()``; the C++ EventLoop's own
    run loop drains the scheduled runnables/timers each cycle. We inherit
    ``create_task`` / ``create_future`` / ``run_in_executor`` /
    exception-handling from BaseEventLoop and never enter its selector path
    (``_ready`` / ``_scheduled`` / ``_run_once``), so the socket/networking
    surface stays unimplemented — the logic thread does no asyncio socket
    I/O (that goes through executors).
    """

    # CPython BaseEventLoop sets this in __init__ but typeshed does not
    # expose it; we assign it in setup_asyncio() to mark the loop running
    # without run_forever(). Declare it so that assignment typechecks.
    _thread_id: int | None

    @override
    def time(self) -> float:
        """Return current loop time (engine app-time, in seconds)."""
        return _babase.apptime()

    @override
    def is_running(self) -> bool:
        """Return whether the loop is running (always True here)."""
        # The C++ Run_ loop is always running while the app is alive.
        return True

    @override
    def is_closed(self) -> bool:
        """Return whether the loop is closed (always False here)."""
        return False

    @override
    def call_soon(
        self,
        callback: Callable[..., object],
        *args: object,
        context: contextvars.Context | None = None,
    ) -> asyncio.Handle:
        """Schedule a callback to run soon on the logic thread."""
        handle = asyncio.Handle(callback, args, self, context)
        # raw=True: no thread-check and no ballistica-context save/restore
        # (Handle._run manages its own contextvars.Context). This single
        # call is optimal for both call_soon and call_soon_threadsafe:
        # PushCall routes through PushRunnable, which on the logic thread
        # does a lock-free local append (serviced on the next event-loop
        # cycle, since the loop never waits while runnables are pending) and
        # from a worker thread locks + notifies the loop's condition
        # variable to wake it immediately.
        _babase.pushcall(handle._run, raw=True)  # pylint: disable=W0212
        return handle

    # call_soon_threadsafe needs nothing extra: pushcall(raw) already works
    # cross-thread and wakes the loop. This single fact is the whole reason
    # executor completions now resume promptly.
    @override
    def call_soon_threadsafe(
        self,
        callback: Callable[..., object],
        *args: object,
        context: contextvars.Context | None = None,
    ) -> asyncio.Handle:
        """Schedule a callback to run soon; safe to call from any thread."""
        return self.call_soon(callback, *args, context=context)

    @override
    def call_at(
        self,
        when: float,
        callback: Callable[..., object],
        *args: object,
        context: contextvars.Context | None = None,
    ) -> asyncio.TimerHandle:
        """Schedule a callback to run at the given loop time."""
        handle = _BATimerHandle(when, callback, args, self, context)
        delay = max(0.0, when - self.time())

        def _fire() -> None:
            # Break the handle<->AppTimer reference cycle before running so
            # the timer is freed by refcount (no cyclic-gc required).
            handle._ba_timer = None  # pylint: disable=W0212
            handle._run()  # pylint: disable=W0212

        # pylint: disable=protected-access
        handle._ba_timer = _babase.AppTimer(delay, _fire, repeat=False)
        return handle

    @override
    def call_later(
        self,
        delay: float,
        callback: Callable[..., object],
        *args: object,
        context: contextvars.Context | None = None,
    ) -> asyncio.TimerHandle:
        """Schedule a callback to run after the given delay."""
        return self.call_at(
            self.time() + delay, callback, *args, context=context
        )

    # NOTE: no @override here — this *does* override BaseEventLoop's method
    # at runtime, but typeshed doesn't expose that private method so mypy
    # can't see the base (and errors if told it's an override).
    def _timer_handle_cancelled(self, handle: asyncio.TimerHandle) -> None:
        """Handle cancellation of a timer we scheduled."""
        # Drop our AppTimer reference to cancel the underlying engine timer
        # so a cancelled call_later doesn't needlessly wake the loop.
        if isinstance(handle, _BATimerHandle):
            handle._ba_timer = None  # pylint: disable=protected-access

    @override
    def run_forever(self) -> None:
        """Unsupported; this loop is driven by the engine event loop."""
        raise RuntimeError(
            'BAEventLoop is driven by the engine event loop;'
            ' run_forever() is not supported.'
        )

    @override
    def close(self) -> None:
        """No-op; this loop lives for the lifetime of the logic thread."""
        # Nothing to tear down, and closing it would be a mistake.
