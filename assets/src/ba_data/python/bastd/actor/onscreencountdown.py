# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor Type(s)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Callable


class OnScreenCountdown(ba.Actor):
    """A Handy On-Screen Timer.

    category: Gameplay Classes

    Useful for time-based games that count down to zero.
    """

    def __init__(self, duration: int, endcall: Callable[[], Any] | None = None):
        """Duration is provided in seconds."""
        super().__init__()
        self._timeremaining = duration
        self._ended = False
        self._endcall = endcall
        self.node = ba.newnode(
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
        self.inputnode = ba.newnode(
            'timedisplay',
            attrs={
                'time2': duration * 1000,
                'timemax': duration * 1000,
                'timemin': 0,
            },
        )
        self.inputnode.connectattr('output', self.node, 'text')
        self._countdownsounds = {
            10: ba.getsound('announceTen'),
            9: ba.getsound('announceNine'),
            8: ba.getsound('announceEight'),
            7: ba.getsound('announceSeven'),
            6: ba.getsound('announceSix'),
            5: ba.getsound('announceFive'),
            4: ba.getsound('announceFour'),
            3: ba.getsound('announceThree'),
            2: ba.getsound('announceTwo'),
            1: ba.getsound('announceOne'),
        }
        self._timer: ba.Timer | None = None

    def start(self) -> None:
        """Start the timer."""
        globalsnode = ba.getactivity().globalsnode
        globalsnode.connectattr('time', self.inputnode, 'time1')
        self.inputnode.time2 = (
            globalsnode.time + (self._timeremaining + 1) * 1000
        )
        self._timer = ba.Timer(1.0, self._update, repeat=True)

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

        # if there's a countdown sound for this time that we
        # haven't played yet, play it
        if tval == 10:
            assert self.node
            assert isinstance(self.node.scale, float)
            self.node.scale *= 1.2
            cmb = ba.newnode('combine', owner=self.node, attrs={'size': 4})
            cmb.connectattr('output', self.node, 'color')
            ba.animate(cmb, 'input0', {0: 1.0, 0.15: 1.0}, loop=True)
            ba.animate(cmb, 'input1', {0: 1.0, 0.15: 0.5}, loop=True)
            ba.animate(cmb, 'input2', {0: 0.1, 0.15: 0.0}, loop=True)
            cmb.input3 = 1.0
        if tval <= 10 and not self._ended:
            ba.playsound(ba.getsound('tick'))
        if tval in self._countdownsounds:
            ba.playsound(self._countdownsounds[tval])
        if tval <= 0 and not self._ended:
            self._ended = True
            if self._endcall is not None:
                self._endcall()
