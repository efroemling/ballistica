# Released under the MIT License. See LICENSE for details.
#
"""A virtual-time asyncio event loop, for testing timer-driven code.

Code under test keeps calling plain :func:`asyncio.sleep`,
``loop.call_later``, and ``loop.time()``; under this loop none of
that takes wall-clock time. Whenever every task is parked and the
only thing left to do is wait for a timer, the loop *jumps* its clock
to that timer instead of sleeping. Two hours of session lifetime run
in milliseconds, and -- the actual point -- tests can use
production-sized windows, so durations that differ in production
stop collapsing into the same number under test.

Time only moves when nothing is runnable, which makes runs
deterministic: there is no 'yield a few times and hope everything
settled' heuristic, because settling is exactly what the loop waits
for before it advances.

It also turns a whole class of hang into a failure. If every task is
parked and *no* timer is pending, nothing can ever wake the program
again; a real loop would sit there until the test runner's timeout,
and this one raises :class:`VirtualTimeDeadlock` on the spot.

The one requirement on code under test: read time from
``asyncio.get_running_loop().time()`` rather than
:func:`time.monotonic`. They are the same clock on a real loop, and
only the former is virtual here.

The opposite failure -- code that never parks at all, such as a
reconnect loop with no backoff -- would spin forever without the
clock moving, since the clock only moves when nothing is runnable.
That raises :class:`VirtualTimeLivelock` after a (large) number of
loop iterations at one instant.

Not for code that does real I/O or uses threads/executors: the loop
never blocks waiting for a file descriptor, so anything that needs
wall-clock time to pass will spin or deadlock-report instead.
"""

import asyncio
import selectors
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from collections.abc import Coroutine, Mapping
    from typing import Any


class VirtualTimeDeadlock(RuntimeError):
    """Every task is parked and no timer is pending.

    Nothing can wake the program, so it would hang forever on a real
    loop. Whatever was awaited can never complete.
    """


class VirtualTimeLivelock(RuntimeError):
    """The program kept running without ever waiting for anything.

    Virtual time only advances when every task is parked, so code
    that is always runnable -- a retry loop with no delay, two tasks
    waking each other forever -- pins the clock in place. On a real
    loop that is a busy-spin at 100% CPU.
    """


#: Loop iterations allowed at a single virtual instant. Far more than
#: real work needs (a big burst of sends is a few thousand) and few
#: enough to fail in seconds rather than hang.
_LIVELOCK_ITERATIONS = 2_000_000


class _VirtualSelector(selectors.BaseSelector):
    """Wraps a real selector; never blocks, advances the clock instead."""

    def __init__(self, loop: VirtualTimeLoop) -> None:
        self._real = selectors.DefaultSelector()
        self._loop = loop
        self._iterations_at_instant = 0

    @override
    def register(
        self, fileobj: Any, events: int, data: Any = None
    ) -> selectors.SelectorKey:
        return self._real.register(fileobj, events, data)

    @override
    def unregister(self, fileobj: Any) -> selectors.SelectorKey:
        return self._real.unregister(fileobj)

    @override
    def modify(
        self, fileobj: Any, events: int, data: Any = None
    ) -> selectors.SelectorKey:
        return self._real.modify(fileobj, events, data)

    @override
    def select(
        self, timeout: float | None = None
    ) -> list[tuple[selectors.SelectorKey, int]]:
        if timeout == 0:
            # Callbacks are already queued; the loop is only polling.
            # Skip the syscall (it is half the cost of a run) and
            # count the pass toward the livelock limit. Descriptors
            # get their look below, whenever the loop would wait.
            self._iterations_at_instant += 1
            if self._iterations_at_instant > _LIVELOCK_ITERATIONS:
                raise VirtualTimeLivelock(
                    f'{_LIVELOCK_ITERATIONS} loop iterations without'
                    f' virtual time advancing (stuck at'
                    f' t={self._loop.time():.3f}); something is spinning'
                    f' instead of waiting.'
                )
            return []
        # Anything actually ready on a descriptor (in practice only
        # the loop's own wakeup pipe) wins over advancing the clock.
        ready = self._real.select(0)
        if ready:
            return ready
        if timeout is None:
            # The loop asks for an unbounded wait only when nothing is
            # runnable and nothing is scheduled.
            raise VirtualTimeDeadlock(
                'All tasks are waiting and no timer is pending;'
                ' nothing can ever wake them.'
            )
        self._loop.advance_virtual_time(timeout)
        self._iterations_at_instant = 0
        return []

    @override
    def close(self) -> None:
        self._real.close()

    @override
    def get_map(self) -> Mapping[Any, selectors.SelectorKey]:
        return self._real.get_map()


class VirtualTimeLoop(asyncio.SelectorEventLoop):
    """An event loop whose clock jumps instead of waiting."""

    def __init__(self) -> None:
        self._virtual_now = 0.0
        super().__init__(selector=_VirtualSelector(self))

    @override
    def time(self) -> float:
        """The virtual clock."""
        return self._virtual_now

    def advance_virtual_time(self, seconds: float) -> None:
        """Move the clock forward. Called by the selector."""
        self._virtual_now += seconds


def run_virtual[T](
    coro: Coroutine[Any, Any, T],
    *,
    limit_seconds: float | None = None,
    debug: bool = False,
) -> T:
    """Run a coroutine to completion under virtual time.

    ``limit_seconds`` bounds the *virtual* time the run may take;
    exceeding it raises :class:`TimeoutError`. That is how a test
    asserts 'this settles within N seconds' about code whose failure
    mode is retrying forever -- which never deadlocks, so
    :class:`VirtualTimeDeadlock` alone would not catch it.

    asyncio's debug mode is off unless ``debug`` asks for it, even
    under ``PYTHONDEVMODE`` (which our test runs set and which would
    otherwise switch it on). Its one time-based feature, slow-callback
    warnings, means nothing on a virtual clock, and recording a
    creation traceback for every handle makes the long schedules this
    loop exists for about seven times slower.
    """

    async def _main() -> T:
        if limit_seconds is None:
            return await coro
        async with asyncio.timeout(limit_seconds):
            return await coro

    with asyncio.Runner(debug=debug, loop_factory=VirtualTimeLoop) as runner:
        return runner.run(_main())
