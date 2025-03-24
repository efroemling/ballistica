# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""
from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


class OnScreenTimer(bs.Actor):
    """A handy on-screen timer.

    Useful for time-based games where time increases.
    """

    def __init__(self) -> None:
        super().__init__()
        self._starttime_ms: int | None = None
        self.node = bs.newnode(
            'text',
            attrs={
                'v_attach': 'top',
                'h_attach': 'center',
                'h_align': 'center',
                'color': (1, 1, 0.5, 1),
                'flatness': 0.5,
                'shadow': 0.5,
                'position': (0, -70),
                'scale': 1.4,
                'text': '',
            },
        )
        self.inputnode = bs.newnode(
            'timedisplay', attrs={'timemin': 0, 'showsubseconds': True}
        )
        self.inputnode.connectattr('output', self.node, 'text')

    def start(self) -> None:
        """Start the timer."""
        tval = int(bs.time() * 1000.0)
        assert isinstance(tval, int)
        self._starttime_ms = tval
        self.inputnode.time1 = self._starttime_ms
        bs.getactivity().globalsnode.connectattr(
            'time', self.inputnode, 'time2'
        )

    def has_started(self) -> bool:
        """Return whether this timer has started yet."""
        return self._starttime_ms is not None

    def stop(self, endtime: int | float | None = None) -> None:
        """End the timer.

        If 'endtime' is not None, it is used when calculating
        the final display time; otherwise the current time is used.
        """
        if endtime is None:
            endtime = bs.time()

        if self._starttime_ms is None:
            logging.warning(
                'OnScreenTimer.stop() called without first calling start()'
            )
        else:
            endtime_ms = int(endtime * 1000)
            self.inputnode.timemax = endtime_ms - self._starttime_ms

    def getstarttime(self) -> float:
        """Return the scene-time when start() was called.

        Time will be returned in seconds if timeformat is SECONDS or
        milliseconds if it is MILLISECONDS.
        """
        val_ms: Any
        if self._starttime_ms is None:
            print('WARNING: getstarttime() called on un-started timer')
            val_ms = int(bs.time() * 1000.0)
        else:
            val_ms = self._starttime_ms
        assert isinstance(val_ms, int)
        return 0.001 * val_ms

    @property
    def starttime(self) -> float:
        """Shortcut for start time in seconds."""
        return self.getstarttime()

    @override
    def handlemessage(self, msg: Any) -> Any:
        # if we're asked to die, just kill our node/timer
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
