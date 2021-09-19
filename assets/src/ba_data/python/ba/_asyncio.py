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

if TYPE_CHECKING:
    from typing import Optional
    import ba

# Our timer and event loop for the ballistica game thread.
_asyncio_timer: Optional[ba.Timer] = None
_asyncio_event_loop: Optional[asyncio.AbstractEventLoop] = None


def setup_asyncio() -> None:
    """Setup asyncio functionality for our game thread."""
    # pylint: disable=global-statement

    import _ba
    from ba._generated.enums import TimeType

    assert _ba.in_game_thread()

    # Create our event-loop. We don't expect there to be one
    # running on this thread before we do.
    try:
        asyncio.get_running_loop()
        print('Found running asyncio loop; unexpected.')
    except RuntimeError:
        pass

    global _asyncio_event_loop  # pylint: disable=invalid-name
    _asyncio_event_loop = asyncio.new_event_loop()

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
        _asyncio_event_loop.run_forever()

    global _asyncio_timer  # pylint: disable=invalid-name
    _asyncio_timer = _ba.Timer(1.0 / 30.0,
                               run_cycle,
                               timetype=TimeType.REAL,
                               repeat=True)

    async def aio_test() -> None:
        print('TEST AIO TASK STARTING')
        assert _asyncio_event_loop is not None
        assert asyncio.get_running_loop() is _asyncio_event_loop
        await asyncio.sleep(2.0)
        print('TEST AIO TASK ENDING')

    if bool(False):
        _asyncio_event_loop.create_task(aio_test())
