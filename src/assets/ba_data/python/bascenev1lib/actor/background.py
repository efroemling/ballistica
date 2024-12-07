# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""

from __future__ import annotations

import random
import weakref
import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any


class Background(bs.Actor):
    """Simple Fading Background Actor."""

    def __init__(
        self,
        fade_time: float = 0.5,
        start_faded: bool = False,
        show_logo: bool = False,
    ):
        super().__init__()
        self._dying = False
        self.fade_time = fade_time
        # We're special in that we create our node in the session
        # scene instead of the activity scene.
        # This way we can overlap multiple activities for fades
        # and whatnot.
        session = bs.getsession()
        self._session = weakref.ref(session)
        with session.context:
            self.node = bs.newnode(
                'image',
                delegate=self,
                attrs={
                    'fill_screen': True,
                    'texture': bs.gettexture('bg'),
                    'tilt_translate': -0.3,
                    'has_alpha_channel': False,
                    'color': (1, 1, 1),
                },
            )
            if not start_faded:
                bs.animate(
                    self.node,
                    'opacity',
                    {0.0: 0.0, self.fade_time: 1.0},
                    loop=False,
                )
            if show_logo:
                logo_texture = bs.gettexture('logo')
                logo_mesh = bs.getmesh('logo')
                logo_mesh_transparent = bs.getmesh('logoTransparent')
                self.logo = bs.newnode(
                    'image',
                    owner=self.node,
                    attrs={
                        'texture': logo_texture,
                        'mesh_opaque': logo_mesh,
                        'mesh_transparent': logo_mesh_transparent,
                        'scale': (0.7, 0.7),
                        'vr_depth': -250,
                        'color': (0.15, 0.15, 0.15),
                        'position': (0, 0),
                        'tilt_translate': -0.05,
                        'absolute_scale': False,
                    },
                )
                self.node.connectattr('opacity', self.logo, 'opacity')
                # add jitter/pulse for a stop-motion-y look unless we're in VR
                # in which case stillness is better
                if not bs.app.env.vr:
                    self.cmb = bs.newnode(
                        'combine', owner=self.node, attrs={'size': 2}
                    )
                    for attr in ['input0', 'input1']:
                        bs.animate(
                            self.cmb,
                            attr,
                            {0.0: 0.693, 0.05: 0.7, 0.5: 0.693},
                            loop=True,
                        )
                    self.cmb.connectattr('output', self.logo, 'scale')
                    cmb = bs.newnode(
                        'combine', owner=self.node, attrs={'size': 2}
                    )
                    cmb.connectattr('output', self.logo, 'position')
                    # Gen some random keys for that stop-motion-y look.
                    keys = {}
                    timeval = 0.0
                    for _i in range(10):
                        keys[timeval] = (random.random() - 0.5) * 0.0015
                        timeval += random.random() * 0.1
                    bs.animate(cmb, 'input0', keys, loop=True)
                    keys = {}
                    timeval = 0.0
                    for _i in range(10):
                        keys[timeval] = (random.random() - 0.5) * 0.0015 + 0.05
                        timeval += random.random() * 0.1
                    bs.animate(cmb, 'input1', keys, loop=True)

    @override
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
            logging.exception(
                'got None session on Background _die'
                ' (and node still exists!)'
            )
        elif session is not None:
            with session.context:
                if not self._dying and self.node:
                    self._dying = True
                    if immediate:
                        self.node.delete()
                    else:
                        bs.animate(
                            self.node,
                            'opacity',
                            {0.0: 1.0, self.fade_time: 0.0},
                            loop=False,
                        )
                        bs.timer(self.fade_time + 0.1, self.node.delete)

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            self._die(msg.immediate)
        else:
            super().handlemessage(msg)
