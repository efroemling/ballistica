# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor Type(s)."""

from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1 import classicassets

if TYPE_CHECKING:
    from typing import Any, Callable


class OnScreenCountdown(bs.Actor):
    """A Handy On-Screen Timer.

    Useful for time-based games that count down to zero.
    """

    def __init__(self, duration: int, endcall: Callable[[], Any] | None = None):
        """Duration is provided in seconds."""
        super().__init__()
        self._timeremaining = duration
        self._ended = False
        self._endcall = endcall
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
            'timedisplay',
            attrs={
                'time2': duration * 1000,
                'timemax': duration * 1000,
                'timemin': 0,
            },
        )
        self.inputnode.connectattr('output', self.node, 'text')
        self._countdownsounds = {
            10: classicassets.audio.announce_ten,
            9: classicassets.audio.announce_nine,
            8: classicassets.audio.announce_eight,
            7: classicassets.audio.announce_seven,
            6: classicassets.audio.announce_six,
            5: classicassets.audio.announce_five,
            4: classicassets.audio.announce_four,
            3: classicassets.audio.announce_three,
            2: classicassets.audio.announce_two,
            1: classicassets.audio.announce_one,
        }
        self._timer: bs.Timer | None = None

    def start(self) -> None:
        """Start the timer."""
        globalsnode = bs.getactivity().globalsnode
        globalsnode.connectattr('time', self.inputnode, 'time1')
        self.inputnode.time2 = (
            globalsnode.time + (self._timeremaining + 1) * 1000
        )
        self._timer = bs.Timer(1.0, self._update, repeat=True)

    @override
    def on_expire(self) -> None:
        super().on_expire()

        # Release callbacks/refs.
        self._endcall = None

    def _update(self, forcevalue: int | None = None) -> None:
        if forcevalue is not None:
            tval = forcevalue
        else:
            self._timeremaining = max(0, self._timeremaining - 1)
            tval = self._timeremaining

        # If there's a countdown sound for this time that we
        # haven't played yet, play it.
        if tval == 10:
            assert self.node
            assert isinstance(self.node.scale, float)
            self.node.scale *= 1.2
            cmb = bs.newnode('combine', owner=self.node, attrs={'size': 4})
            cmb.connectattr('output', self.node, 'color')
            bs.animate(cmb, 'input0', {0: 1.0, 0.15: 1.0}, loop=True)
            bs.animate(cmb, 'input1', {0: 1.0, 0.15: 0.5}, loop=True)
            bs.animate(cmb, 'input2', {0: 0.1, 0.15: 0.0}, loop=True)
            cmb.input3 = 1.0
        if tval <= 10 and not self._ended:
            classicassets.audio.tick.play()
        if tval in self._countdownsounds:
            self._countdownsounds[tval].play()
        if tval <= 0 and not self._ended:
            self._ended = True
            if self._endcall is not None:
                self._endcall()
