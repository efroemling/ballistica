# Released under the MIT License. See LICENSE for details.
#
"""Utility functionality pertaining to gameplay."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, NewType

import babase
import _bascenev1

if TYPE_CHECKING:
    from typing import Sequence

    import bascenev1

Time = NewType('Time', float)
BaseTime = NewType('BaseTime', float)

TROPHY_CHARS = {
    '1': babase.SpecialChar.TROPHY1,
    '2': babase.SpecialChar.TROPHY2,
    '3': babase.SpecialChar.TROPHY3,
    '0a': babase.SpecialChar.TROPHY0A,
    '0b': babase.SpecialChar.TROPHY0B,
    '4': babase.SpecialChar.TROPHY4,
}


@dataclass
class GameTip:
    """Defines a tip presentable to the user at the start of a game.

    Category: **Gameplay Classes**
    """

    text: str
    icon: bascenev1.Texture | None = None
    sound: bascenev1.Sound | None = None


def get_trophy_string(trophy_id: str) -> str:
    """Given a trophy id, returns a string to visualize it."""
    if trophy_id in TROPHY_CHARS:
        return babase.charstr(TROPHY_CHARS[trophy_id])
    return '?'


def animate(
    node: bascenev1.Node,
    attr: str,
    keys: dict[float, float],
    loop: bool = False,
    offset: float = 0,
) -> bascenev1.Node:
    """Animate values on a target bascenev1.Node.

    Category: **Gameplay Functions**

    Creates an 'animcurve' node with the provided values and time as an input,
    connect it to the provided attribute, and set it to die with the target.
    Key values are provided as time:value dictionary pairs.  Time values are
    relative to the current time. By default, times are specified in seconds,
    but timeformat can also be set to MILLISECONDS to recreate the old behavior
    (prior to ba 1.5) of taking milliseconds. Returns the animcurve node.
    """
    items = list(keys.items())
    items.sort()

    curve = _bascenev1.newnode(
        'animcurve',
        owner=node,
        name='Driving ' + str(node) + ' \'' + attr + '\'',
    )

    # We take seconds but operate on milliseconds internally.
    mult = 1000

    curve.times = [int(mult * time) for time, val in items]
    curve.offset = int(_bascenev1.time() * 1000.0) + int(mult * offset)
    curve.values = [val for time, val in items]
    curve.loop = loop

    # If we're not looping, set a timer to kill this curve
    # after its done its job.
    # FIXME: Even if we are looping we should have a way to die once we
    #  get disconnected.
    if not loop:
        # noinspection PyUnresolvedReferences
        _bascenev1.timer(
            (int(mult * items[-1][0]) + 1000) / 1000.0, curve.delete
        )

    # Do the connects last so all our attrs are in place when we push initial
    # values through.

    # We operate in either activities or sessions..
    try:
        globalsnode = _bascenev1.getactivity().globalsnode
    except babase.ActivityNotFoundError:
        globalsnode = _bascenev1.getsession().sessionglobalsnode

    globalsnode.connectattr('time', curve, 'in')
    curve.connectattr('out', node, attr)
    return curve


def animate_array(
    node: bascenev1.Node,
    attr: str,
    size: int,
    keys: dict[float, Sequence[float]],
    *,
    loop: bool = False,
    offset: float = 0,
) -> None:
    """Animate an array of values on a target bascenev1.Node.

    Category: **Gameplay Functions**

    Like bs.animate, but operates on array attributes.
    """
    combine = _bascenev1.newnode('combine', owner=node, attrs={'size': size})
    items = list(keys.items())
    items.sort()

    # We take seconds but operate on milliseconds internally.
    mult = 1000

    # We operate in either activities or sessions..
    try:
        globalsnode = _bascenev1.getactivity().globalsnode
    except babase.ActivityNotFoundError:
        globalsnode = _bascenev1.getsession().sessionglobalsnode

    for i in range(size):
        curve = _bascenev1.newnode(
            'animcurve',
            owner=node,
            name=(
                'Driving ' + str(node) + ' \'' + attr + '\' member ' + str(i)
            ),
        )
        globalsnode.connectattr('time', curve, 'in')
        curve.times = [int(mult * time) for time, val in items]
        curve.values = [val[i] for time, val in items]
        curve.offset = int(_bascenev1.time() * 1000.0) + int(mult * offset)
        curve.loop = loop
        curve.connectattr('out', combine, 'input' + str(i))

        # If we're not looping, set a timer to kill this
        # curve after its done its job.
        if not loop:
            # (PyCharm seems to think item is a float, not a tuple)
            # noinspection PyUnresolvedReferences
            _bascenev1.timer(
                (int(mult * items[-1][0]) + 1000) / 1000.0,
                curve.delete,
            )
    combine.connectattr('output', node, attr)

    # If we're not looping, set a timer to kill the combine once
    # the job is done.
    # FIXME: Even if we are looping we should have a way to die
    #  once we get disconnected.
    if not loop:
        # (PyCharm seems to think item is a float, not a tuple)
        # noinspection PyUnresolvedReferences
        _bascenev1.timer(
            (int(mult * items[-1][0]) + 1000) / 1000.0, combine.delete
        )


def show_damage_count(
    damage: str, position: Sequence[float], direction: Sequence[float]
) -> None:
    """Pop up a damage count at a position in space.

    Category: **Gameplay Functions**
    """
    lifespan = 1.0
    app = babase.app

    # FIXME: Should never vary game elements based on local config.
    #  (connected clients may have differing configs so they won't
    #  get the intended results).
    assert app.classic is not None
    do_big = app.ui_v1.uiscale is babase.UIScale.SMALL or app.env.vr
    txtnode = _bascenev1.newnode(
        'text',
        attrs={
            'text': damage,
            'in_world': True,
            'h_align': 'center',
            'flatness': 1.0,
            'shadow': 1.0 if do_big else 0.7,
            'color': (1, 0.25, 0.25, 1),
            'scale': 0.015 if do_big else 0.01,
        },
    )
    # Translate upward.
    tcombine = _bascenev1.newnode('combine', owner=txtnode, attrs={'size': 3})
    tcombine.connectattr('output', txtnode, 'position')
    v_vals = []
    pval = 0.0
    vval = 0.07
    count = 6
    for i in range(count):
        v_vals.append((float(i) / count, pval))
        pval += vval
        vval *= 0.5
    p_start = position[0]
    p_dir = direction[0]
    animate(
        tcombine,
        'input0',
        {i[0] * lifespan: p_start + p_dir * i[1] for i in v_vals},
    )
    p_start = position[1]
    p_dir = direction[1]
    animate(
        tcombine,
        'input1',
        {i[0] * lifespan: p_start + p_dir * i[1] for i in v_vals},
    )
    p_start = position[2]
    p_dir = direction[2]
    animate(
        tcombine,
        'input2',
        {i[0] * lifespan: p_start + p_dir * i[1] for i in v_vals},
    )
    animate(txtnode, 'opacity', {0.7 * lifespan: 1.0, lifespan: 0.0})
    _bascenev1.timer(lifespan, txtnode.delete)


def cameraflash(duration: float = 999.0) -> None:
    """Create a strobing camera flash effect.

    Category: **Gameplay Functions**

    (as seen when a team wins a game)
    Duration is in seconds.
    """
    # pylint: disable=too-many-locals
    from bascenev1._nodeactor import NodeActor

    x_spread = 10
    y_spread = 5
    positions = [
        [-x_spread, -y_spread],
        [0, -y_spread],
        [0, y_spread],
        [x_spread, -y_spread],
        [x_spread, y_spread],
        [-x_spread, y_spread],
    ]
    times = [0, 2700, 1000, 1800, 500, 1400]

    # Store this on the current activity so we only have one at a time.
    # FIXME: Need a type safe way to do this.
    activity = _bascenev1.getactivity()
    activity.camera_flash_data = []  # type: ignore
    for i in range(6):
        light = NodeActor(
            _bascenev1.newnode(
                'light',
                attrs={
                    'position': (positions[i][0], 0, positions[i][1]),
                    'radius': 1.0,
                    'lights_volumes': False,
                    'height_attenuated': False,
                    'color': (0.2, 0.2, 0.8),
                },
            )
        )
        sval = 1.87
        iscale = 1.3
        tcombine = _bascenev1.newnode(
            'combine',
            owner=light.node,
            attrs={
                'size': 3,
                'input0': positions[i][0],
                'input1': 0,
                'input2': positions[i][1],
            },
        )
        assert light.node
        tcombine.connectattr('output', light.node, 'position')
        xval = positions[i][0]
        yval = positions[i][1]
        spd = 0.5 + random.random()
        spd2 = 0.5 + random.random()
        animate(
            tcombine,
            'input0',
            {
                0.0: xval + 0,
                0.069 * spd: xval + 10.0,
                0.143 * spd: xval - 10.0,
                0.201 * spd: xval + 0,
            },
            loop=True,
        )
        animate(
            tcombine,
            'input2',
            {
                0.0: yval + 0,
                0.15 * spd2: yval + 10.0,
                0.287 * spd2: yval - 10.0,
                0.398 * spd2: yval + 0,
            },
            loop=True,
        )
        animate(
            light.node,
            'intensity',
            {
                0.0: 0,
                0.02 * sval: 0,
                0.05 * sval: 0.8 * iscale,
                0.08 * sval: 0,
                0.1 * sval: 0,
            },
            loop=True,
            offset=times[i],
        )
        _bascenev1.timer(
            (times[i] + random.randint(1, int(duration)) * 40 * sval) / 1000.0,
            light.node.delete,
        )
        activity.camera_flash_data.append(light)  # type: ignore
