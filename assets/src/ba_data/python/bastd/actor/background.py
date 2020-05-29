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

import random
import weakref
from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any


class Background(ba.Actor):
    """Simple Fading Background Actor."""

    def __init__(self,
                 fade_time: float = 0.5,
                 start_faded: bool = False,
                 show_logo: bool = False):
        super().__init__()
        self._dying = False
        self.fade_time = fade_time
        # We're special in that we create our node in the session
        # scene instead of the activity scene.
        # This way we can overlap multiple activities for fades
        # and whatnot.
        session = ba.getsession()
        self._session = weakref.ref(session)
        with ba.Context(session):
            self.node = ba.newnode('image',
                                   delegate=self,
                                   attrs={
                                       'fill_screen': True,
                                       'texture': ba.gettexture('bg'),
                                       'tilt_translate': -0.3,
                                       'has_alpha_channel': False,
                                       'color': (1, 1, 1)
                                   })
            if not start_faded:
                ba.animate(self.node,
                           'opacity', {
                               0.0: 0.0,
                               self.fade_time: 1.0
                           },
                           loop=False)
            if show_logo:
                logo_texture = ba.gettexture('logo')
                logo_model = ba.getmodel('logo')
                logo_model_transparent = ba.getmodel('logoTransparent')
                self.logo = ba.newnode(
                    'image',
                    owner=self.node,
                    attrs={
                        'texture': logo_texture,
                        'model_opaque': logo_model,
                        'model_transparent': logo_model_transparent,
                        'scale': (0.7, 0.7),
                        'vr_depth': -250,
                        'color': (0.15, 0.15, 0.15),
                        'position': (0, 0),
                        'tilt_translate': -0.05,
                        'absolute_scale': False
                    })
                self.node.connectattr('opacity', self.logo, 'opacity')
                # add jitter/pulse for a stop-motion-y look unless we're in VR
                # in which case stillness is better
                if not ba.app.vr_mode:
                    self.cmb = ba.newnode('combine',
                                          owner=self.node,
                                          attrs={'size': 2})
                    for attr in ['input0', 'input1']:
                        ba.animate(self.cmb,
                                   attr, {
                                       0.0: 0.693,
                                       0.05: 0.7,
                                       0.5: 0.693
                                   },
                                   loop=True)
                    self.cmb.connectattr('output', self.logo, 'scale')
                    cmb = ba.newnode('combine',
                                     owner=self.node,
                                     attrs={'size': 2})
                    cmb.connectattr('output', self.logo, 'position')
                    # Gen some random keys for that stop-motion-y look.
                    keys = {}
                    timeval = 0.0
                    for _i in range(10):
                        keys[timeval] = (random.random() - 0.5) * 0.0015
                        timeval += random.random() * 0.1
                    ba.animate(cmb, 'input0', keys, loop=True)
                    keys = {}
                    timeval = 0.0
                    for _i in range(10):
                        keys[timeval] = (random.random() - 0.5) * 0.0015 + 0.05
                        timeval += random.random() * 0.1
                    ba.animate(cmb, 'input1', keys, loop=True)

    def __del__(self) -> None:
        # Normal actors don't get sent DieMessages when their
        # activity is shutting down, but we still need to do so
        # since our node lives in the session and it wouldn't die
        # otherwise.
        self._die()
        super().__del__()

    def _die(self, immediate: bool = False) -> None:
        session = self._session()
        if session is None and self.node:
            # If session is gone, our node should be too,
            # since it was part of the session's scene.
            # Let's make sure that's the case.
            # (since otherwise we have no way to kill it)
            ba.print_error('got None session on Background _die'
                           ' (and node still exists!)')
        elif session is not None:
            with ba.Context(session):
                if not self._dying and self.node:
                    self._dying = True
                    if immediate:
                        self.node.delete()
                    else:
                        ba.animate(self.node,
                                   'opacity', {
                                       0.0: 1.0,
                                       self.fade_time: 0.0
                                   },
                                   loop=False)
                        ba.timer(self.fade_time + 0.1, self.node.delete)

    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, ba.DieMessage):
            self._die(msg.immediate)
        else:
            super().handlemessage(msg)
