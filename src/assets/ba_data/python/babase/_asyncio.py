# Released under the MIT License. See LICENSE for details.
#
"""Asyncio related functionality.

Exploring the idea of allowing Python coroutines to run gracefully
besides our internal event loop. They could prove useful for networking
operations or possibly game logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
import logging
import time
import os

if TYPE_CHECKING:
    import babase

# Our timer and event loop for the ballistica logic thread.
_asyncio_timer: babase.AppTimer | None = None
_asyncio_event_loop: asyncio.AbstractEventLoop | None = None

DEBUG_TIMING = os.environ.get('BA_DEBUG_TIMING') == '1'


def setup_asyncio() -> asyncio.AbstractEventLoop:
    """Setup asyncio functionality for the logic thread."""
    # pylint: disable=global-statement

    import _babase
    import babase

    assert _babase.in_logic_thread()

    # Create our event-loop. We don't expect there to be one
    # running on this thread before we do.
    try:
        asyncio.get_running_loop()
        print('Found running asyncio loop; unexpected.')
    except RuntimeError:
        pass

    global _asyncio_event_loop
    _asyncio_event_loop = asyncio.new_event_loop()
    _asyncio_event_loop.set_default_executor(babase.app.threadpool)

    # Ideally we should integrate asyncio into our C++ Thread class's
    # low level event loop so that asyncio timers/sockets/etc. could
    # be true first-class citizens. For now, though, we can explicitly
    # pump an asyncio loop periodically which gets us a decent
    # approximation of that, which should be good enough for
    # all but extremely time sensitive uses.
    # See https://stackoverflow.com/questions/29782377/
    # is-it-possible-to-run-only-a-single-step-of-the-asyncio-event-loop
    def run_cycle() -> None:
        assert _asyncio_event_loop is not None
        _asyncio_event_loop.call_soon(_asyncio_event_loop.stop)
        starttime = time.monotonic() if DEBUG_TIMING else 0
        _asyncio_event_loop.run_forever()
        endtime = time.monotonic() if DEBUG_TIMING else 0

        # Let's aim to have nothing take longer than 1/120 of a second.
        if DEBUG_TIMING:
            warn_time = 1.0 / 120
            duration = endtime - starttime
            if duration > warn_time:
                logging.warning(
                    'Asyncio loop step took %.4fs; ideal max is %.4f',
                    duration,
                    warn_time,
                )

    global _asyncio_timer
    _asyncio_timer = _babase.AppTimer(1.0 / 30.0, run_cycle, repeat=True)

    if bool(False):

        async def aio_test() -> None:
            print('TEST AIO TASK STARTING')
            assert _asyncio_event_loop is not None
            assert asyncio.get_running_loop() is _asyncio_event_loop
            await asyncio.sleep(2.0)
            print('TEST AIO TASK ENDING')

        _testtask = _asyncio_event_loop.create_task(aio_test())

    return _asyncio_event_loop
