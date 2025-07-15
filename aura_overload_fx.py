# ba_meta require api 9
# ba_meta name Aura Overload FX
# ba_meta description Gives the host player a glowing, smoothly transitioning aura.
# ba_meta author KritarthaT

import bascenev1 as bs
import babase
import random

class AuraEffect:
    def __init__(self, player: bs.Player):
        self._player = player
        self._light = None
        self._colors = [
            (1, 0, 0), (0, 1, 0), (0, 0, 1),
            (1, 1, 0), (0, 1, 1), (1, 0, 1)
        ]
        self._color_index = 0
        self._next_index = 1
        self._t = 0.0

        self._timer = bs.Timer(0.05, self._update, repeat=True)

    def _lerp_color(self, c1, c2, t):
        return tuple(c1[i] + (c2[i] - c1[i]) * t for i in range(3))

    def _update(self):
        if not self._player or not self._player.actor or not self._player.actor.node:
            return

        pos = self._player.actor.node.position
        if not self._light:
            self._light = bs.newnode('light', attrs={
                'position': pos,
                'color': self._colors[self._color_index],
                'radius': 0.3,
                'intensity': 0.8,
                'volume_intensity_scale': 1.0
            })

        # Interpolate color
        self._t += 0.05 / 1.0  # 1 sec per color transition
        if self._t >= 1.0:
            self._t = 0.0
            self._color_index = self._next_index
            self._next_index = (self._next_index + 1) % len(self._colors)

        smooth_color = self._lerp_color(
            self._colors[self._color_index],
            self._colors[self._next_index],
            self._t
        )

        self._light.color = smooth_color
        self._light.position = (pos[0], pos[1] + 0.8, pos[2])  # Follow player

        # Optional visual sparks
        bs.emitfx(
            position=pos,
            velocity=(0, 2, 0),
            count=10,
            scale=0.6,
            spread=0.2,
            chunk_type='spark'
        )


# ba_meta export plugin
class AuraOverloadFX(babase.Plugin):
    def __init__(self):
        bs.Activity.__init__ = self._wrap_activity_init(bs.Activity.__init__)
    
    def _wrap_activity_init(self, original):
        def new_init(activity_self, settings):
            original(activity_self, settings)
            bs.timer(1.0, lambda: self._start_glow(activity_self))
        return new_init

    def _start_glow(self, activity: bs.Activity):
        if activity.players:
            player = activity.players[0]  # Host player
            AuraEffect(player)
