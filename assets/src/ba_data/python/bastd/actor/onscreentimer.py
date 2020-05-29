# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Defines Actor(s)."""
from __future__ import annotations

from typing import TYPE_CHECKING, overload

import ba

if TYPE_CHECKING:
    from typing import Optional, Union, Any
    from typing_extensions import Literal


class OnScreenTimer(ba.Actor):
    """A handy on-screen timer.

    category: Gameplay Classes

    Useful for time-based games where time increases.
    """

    def __init__(self) -> None:
        super().__init__()
        self._starttime_ms: Optional[int] = None
        self.node = ba.newnode('text',
                               attrs={
                                   'v_attach': 'top',
                                   'h_attach': 'center',
                                   'h_align': 'center',
                                   'color': (1, 1, 0.5, 1),
                                   'flatness': 0.5,
                                   'shadow': 0.5,
                                   'position': (0, -70),
                                   'scale': 1.4,
                                   'text': ''
                               })
        self.inputnode = ba.newnode('timedisplay',
                                    attrs={
                                        'timemin': 0,
                                        'showsubseconds': True
                                    })
        self.inputnode.connectattr('output', self.node, 'text')

    def start(self) -> None:
        """Start the timer."""
        tval = ba.time(timeformat=ba.TimeFormat.MILLISECONDS)
        assert isinstance(tval, int)
        self._starttime_ms = tval
        self.inputnode.time1 = self._starttime_ms
        ba.getactivity().globalsnode.connectattr('time', self.inputnode,
                                                 'time2')

    def has_started(self) -> bool:
        """Return whether this timer has started yet."""
        return self._starttime_ms is not None

    def stop(self,
             endtime: Union[int, float] = None,
             timeformat: ba.TimeFormat = ba.TimeFormat.SECONDS) -> None:
        """End the timer.

        If 'endtime' is not None, it is used when calculating
        the final display time; otherwise the current time is used.

        'timeformat' applies to endtime and can be SECONDS or MILLISECONDS
        """
        if endtime is None:
            endtime = ba.time(timeformat=ba.TimeFormat.MILLISECONDS)
            timeformat = ba.TimeFormat.MILLISECONDS

        if self._starttime_ms is None:
            print('Warning: OnScreenTimer.stop() called without start() first')
        else:
            endtime_ms: int
            if timeformat is ba.TimeFormat.SECONDS:
                endtime_ms = int(endtime * 1000)
            elif timeformat is ba.TimeFormat.MILLISECONDS:
                assert isinstance(endtime, int)
                endtime_ms = endtime
            else:
                raise ValueError(f'invalid timeformat: {timeformat}')

            self.inputnode.timemax = endtime_ms - self._starttime_ms

    # Overloads so type checker knows our exact return type based in args.
    @overload
    def getstarttime(
        self,
        timeformat: Literal[ba.TimeFormat.SECONDS] = ba.TimeFormat.SECONDS
    ) -> float:
        ...

    @overload
    def getstarttime(self,
                     timeformat: Literal[ba.TimeFormat.MILLISECONDS]) -> int:
        ...

    def getstarttime(
        self,
        timeformat: ba.TimeFormat = ba.TimeFormat.SECONDS
    ) -> Union[int, float]:
        """Return the sim-time when start() was called.

        Time will be returned in seconds if timeformat is SECONDS or
        milliseconds if it is MILLISECONDS.
        """
        val_ms: Any
        if self._starttime_ms is None:
            print('WARNING: getstarttime() called on un-started timer')
            val_ms = ba.time(timeformat=ba.TimeFormat.MILLISECONDS)
        else:
            val_ms = self._starttime_ms
        assert isinstance(val_ms, int)
        if timeformat is ba.TimeFormat.SECONDS:
            return 0.001 * val_ms
        if timeformat is ba.TimeFormat.MILLISECONDS:
            return val_ms
        raise ValueError(f'invalid timeformat: {timeformat}')

    @property
    def starttime(self) -> float:
        """Shortcut for start time in seconds."""
        return self.getstarttime()

    def handlemessage(self, msg: Any) -> Any:
        # if we're asked to die, just kill our node/timer
        if isinstance(msg, ba.DieMessage):
            if self.node:
                self.node.delete()
