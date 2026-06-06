# Released under the MIT License. See LICENSE for details.
#
"""Asyncio related functionality.

Python coroutines run on the logic thread alongside our internal event
loop. They are useful for networking operations and game logic. The
asyncio loop is integrated directly into the logic thread's C++ event
loop (see :class:`~babase._baeventloop.BAEventLoop`) so that work posted
from other threads — ``run_in_executor`` completions in particular —
wakes the logic thread immediately rather than waiting for a poll.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
import logging

from efro.util import strip_exception_tracebacks

if TYPE_CHECKING:
    from typing import Any

# Our event loop for the ballistica logic thread.
_g_asyncio_event_loop: asyncio.AbstractEventLoop | None = None


def setup_asyncio() -> asyncio.AbstractEventLoop:
    """Setup asyncio functionality for the logic thread."""
    # pylint: disable=global-statement

    import threading

    import _babase
    import babase

    from babase._baeventloop import BAEventLoop

    assert _babase.in_logic_thread()

    # We don't expect an asyncio loop to be running on this thread before
    # we set ours up.
    try:
        asyncio.get_running_loop()
        logging.warning(
            'Found running asyncio loop on logic thread; unexpected.'
        )
    except RuntimeError:
        pass

    global _g_asyncio_event_loop
    loop = BAEventLoop()
    loop.set_default_executor(babase.app.threadpool)

    # Try to avoid reference loops from exceptions.
    loop.set_exception_handler(_exception_handler)

    # Mark this as the thread's running loop *without* ever calling
    # run_forever(); the C++ EventLoop drives it. This makes
    # get_running_loop(), is_running(), and Task/Future creation all work
    # normally. This bit of asyncio-internal coupling is the one thing to
    # re-verify on Python upgrades.
    # pylint: disable=protected-access
    loop._thread_id = threading.get_ident()
    asyncio.events._set_running_loop(loop)
    # pylint: enable=protected-access
    asyncio.set_event_loop(loop)

    _g_asyncio_event_loop = loop
    return loop


def _exception_handler(
    loop: asyncio.AbstractEventLoop, context: dict[str, Any]
) -> None:
    # Do default behavior (should log the exception) and then rip out
    # exception tracebacks to hopefully avoid reference cycles which
    # would require cyclic garbage collection.
    loop.default_exception_handler(context)
    exc = context.get('exception')
    if isinstance(exc, BaseException):
        strip_exception_tracebacks(exc)
