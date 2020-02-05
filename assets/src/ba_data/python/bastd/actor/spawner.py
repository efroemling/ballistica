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
"""Defines some lovely Actor(s)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable


# FIXME: Should make this an Actor.
class Spawner:
    """Utility for delayed spawning of objects.

    category: Gameplay Classes

    Creates a light flash and sends a ba.Spawner.SpawnMessage
    to the current activity after a delay.
    """

    class SpawnMessage:
        """Spawn message sent by a ba.Spawner after its delay has passed.

        category: Message Classes

        Attributes:

           spawner
              The ba.Spawner we came from.

           data
              The data object passed by the user.

           pt
              The spawn position.
        """

        def __init__(self, spawner: Spawner, data: Any, pt: Sequence[float]):
            """Instantiate with the given values."""
            self.spawner = spawner
            self.data = data
            self.pt = pt  # pylint: disable=invalid-name

    def __init__(self,
                 data: Any = None,
                 pt: Sequence[float] = (0, 0, 0),
                 spawn_time: float = 1.0,
                 send_spawn_message: bool = True,
                 spawn_callback: Callable[[], Any] = None):
        """Instantiate a Spawner.

        Requires some custom data, a position,
        and a spawn-time in seconds.
        """
        self._spawn_callback = spawn_callback
        self._send_spawn_message = send_spawn_message
        self._spawner_sound = ba.getsound('swip2')
        self._data = data
        self._pt = pt
        # create a light where the spawn will happen
        self._light = ba.newnode('light',
                                 attrs={
                                     'position': tuple(pt),
                                     'radius': 0.1,
                                     'color': (1.0, 0.1, 0.1),
                                     'lights_volumes': False
                                 })
        scl = float(spawn_time) / 3.75
        min_val = 0.4
        max_val = 0.7
        ba.playsound(self._spawner_sound, position=self._light.position)
        ba.animate(
            self._light, 'intensity', {
                0.0: 0.0,
                0.25 * scl: max_val,
                0.500 * scl: min_val,
                0.750 * scl: max_val,
                1.000 * scl: min_val,
                1.250 * scl: 1.1 * max_val,
                1.500 * scl: min_val,
                1.750 * scl: 1.2 * max_val,
                2.000 * scl: min_val,
                2.250 * scl: 1.3 * max_val,
                2.500 * scl: min_val,
                2.750 * scl: 1.4 * max_val,
                3.000 * scl: min_val,
                3.250 * scl: 1.5 * max_val,
                3.500 * scl: min_val,
                3.750 * scl: 2.0,
                4.000 * scl: 0.0
            })
        ba.timer(spawn_time, self._spawn)

    def _spawn(self) -> None:
        ba.timer(1.0, self._light.delete)
        if self._spawn_callback is not None:
            self._spawn_callback()
        if self._send_spawn_message:
            # only run if our activity still exists
            activity = ba.getactivity()
            if activity is not None:
                activity.handlemessage(
                    self.SpawnMessage(self, self._data, self._pt))
