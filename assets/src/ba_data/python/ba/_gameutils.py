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
"""Utility functionality pertaining to gameplay."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._enums import TimeType, TimeFormat, SpecialChar

if TYPE_CHECKING:
    from typing import Any, Dict, Sequence, Optional
    import ba

TROPHY_CHARS = {
    '1': SpecialChar.TROPHY1,
    '2': SpecialChar.TROPHY2,
    '3': SpecialChar.TROPHY3,
    '0a': SpecialChar.TROPHY0A,
    '0b': SpecialChar.TROPHY0B,
    '4': SpecialChar.TROPHY4
}


def get_trophy_string(trophy_id: str) -> str:
    """Given a trophy id, returns a string to visualize it."""
    if trophy_id in TROPHY_CHARS:
        return _ba.charstr(TROPHY_CHARS[trophy_id])
    return '?'


def sharedobj(name: str) -> Any:
    """Return a predefined object for the current Activity, creating if needed.

    Category: Gameplay Functions

    Available values for 'name':

    'globals': returns the 'globals' ba.Node, containing various global
      controls & values.

    'object_material': a ba.Material that should be applied to any small,
      normal, physical objects such as bombs, boxes, players, etc. Other
      materials often check for the  presence of this material as a
      prerequisite for performing certain actions (such as disabling collisions
      between initially-overlapping objects)

    'player_material': a ba.Material to be applied to player parts.  Generally,
      materials related to the process of scoring when reaching a goal, etc
      will look for the presence of this material on things that hit them.

    'pickup_material': a ba.Material; collision shapes used for picking things
      up will have this material applied. To prevent an object from being
      picked up, you can add a material that disables collisions against things
      containing this material.

    'footing_material': anything that can be 'walked on' should have this
      ba.Material applied; generally just terrain and whatnot. A character will
      snap upright whenever touching something with this material so it should
      not be applied to props, etc.

    'attack_material': a ba.Material applied to explosion shapes, punch
      shapes, etc.  An object not wanting to receive impulse/etc messages can
      disable collisions against this material.

    'death_material': a ba.Material that sends a ba.DieMessage() to anything
      that touches it; handy for terrain below a cliff, etc.

    'region_material':  a ba.Material used for non-physical collision shapes
      (regions); collisions can generally be allowed with this material even
      when initially overlapping since it is not physical.

    'railing_material': a ba.Material with a very low friction/stiffness/etc
      that can be applied to invisible 'railings' useful for gently keeping
      characters from falling off of cliffs.
    """
    # pylint: disable=too-many-branches
    from ba._messages import DieMessage

    # We store these on the current context; whether its an activity or
    # session.
    activity: Optional[ba.Activity] = _ba.getactivity(doraise=False)
    if activity is not None:

        # Grab shared-objs dict.
        sharedobjs = getattr(activity, 'sharedobjs', None)

        # Grab item out of it.
        try:
            return sharedobjs[name]
        except Exception:
            pass

        obj: Any

        # Hmm looks like it doesn't yet exist; create it if its a valid value.
        if name == 'globals':
            node_obj = _ba.newnode('globals')
            obj = node_obj
        elif name in [
                'object_material', 'player_material', 'pickup_material',
                'footing_material', 'attack_material'
        ]:
            obj = _ba.Material()
        elif name == 'death_material':
            mat = obj = _ba.Material()
            mat.add_actions(
                ('message', 'their_node', 'at_connect', DieMessage()))
        elif name == 'region_material':
            obj = _ba.Material()
        elif name == 'railing_material':
            mat = obj = _ba.Material()
            mat.add_actions(('modify_part_collision', 'collide', False))
            mat.add_actions(('modify_part_collision', 'stiffness', 0.003))
            mat.add_actions(('modify_part_collision', 'damping', 0.00001))
            mat.add_actions(conditions=('they_have_material',
                                        sharedobj('player_material')),
                            actions=(('modify_part_collision', 'collide',
                                      True), ('modify_part_collision',
                                              'friction', 0.0)))
        else:
            raise ValueError(
                "unrecognized shared object (activity context): '" + name +
                "'")
    else:
        session: Optional[ba.Session] = _ba.getsession(doraise=False)
        if session is not None:

            # Grab shared-objs dict (creating if necessary).
            sharedobjs = session.sharedobjs

            # Grab item out of it.
            obj = sharedobjs.get(name)
            if obj is not None:
                return obj

            # Hmm looks like it doesn't yet exist; create if its a valid value.
            if name == 'globals':
                obj = _ba.newnode('sessionglobals')
            else:
                raise ValueError('unrecognized shared object '
                                 "(session context): '" + name + "'")
        else:
            raise RuntimeError('no current activity or session context')

    # Ok, got a shiny new shared obj; store it for quick access next time.
    sharedobjs[name] = obj
    return obj


def animate(node: ba.Node,
            attr: str,
            keys: Dict[float, float],
            loop: bool = False,
            offset: float = 0,
            timetype: ba.TimeType = TimeType.SIM,
            timeformat: ba.TimeFormat = TimeFormat.SECONDS,
            suppress_format_warning: bool = False) -> ba.Node:
    """Animate values on a target ba.Node.

    Category: Gameplay Functions

    Creates an 'animcurve' node with the provided values and time as an input,
    connect it to the provided attribute, and set it to die with the target.
    Key values are provided as time:value dictionary pairs.  Time values are
    relative to the current time. By default, times are specified in seconds,
    but timeformat can also be set to MILLISECONDS to recreate the old behavior
    (prior to ba 1.5) of taking milliseconds. Returns the animcurve node.
    """
    if timetype is TimeType.SIM:
        driver = 'time'
    else:
        raise Exception('FIXME; only SIM timetype is supported currently.')
    items = list(keys.items())
    items.sort()

    # Temp sanity check while we transition from milliseconds to seconds
    # based time values.
    if __debug__:
        if not suppress_format_warning:
            for item in items:
                _ba.time_format_check(timeformat, item[0])

    curve = _ba.newnode('animcurve',
                        owner=node,
                        name='Driving ' + str(node) + ' \'' + attr + '\'')

    if timeformat is TimeFormat.SECONDS:
        mult = 1000
    elif timeformat is TimeFormat.MILLISECONDS:
        mult = 1
    else:
        raise ValueError(f'invalid timeformat value: {timeformat}')

    curve.times = [int(mult * time) for time, val in items]
    curve.offset = _ba.time(timeformat=TimeFormat.MILLISECONDS) + int(
        mult * offset)
    curve.values = [val for time, val in items]
    curve.loop = loop

    # If we're not looping, set a timer to kill this curve
    # after its done its job.
    # FIXME: Even if we are looping we should have a way to die once we
    #  get disconnected.
    if not loop:
        _ba.timer(int(mult * items[-1][0]) + 1000,
                  curve.delete,
                  timeformat=TimeFormat.MILLISECONDS)

    # Do the connects last so all our attrs are in place when we push initial
    # values through.
    sharedobj('globals').connectattr(driver, curve, 'in')
    curve.connectattr('out', node, attr)
    return curve


def animate_array(node: ba.Node,
                  attr: str,
                  size: int,
                  keys: Dict[float, Sequence[float]],
                  loop: bool = False,
                  offset: float = 0,
                  timetype: ba.TimeType = TimeType.SIM,
                  timeformat: ba.TimeFormat = TimeFormat.SECONDS,
                  suppress_format_warning: bool = False) -> None:
    """Animate an array of values on a target ba.Node.

    Category: Gameplay Functions

    Like ba.animate(), but operates on array attributes.
    """
    # pylint: disable=too-many-locals
    combine = _ba.newnode('combine', owner=node, attrs={'size': size})
    if timetype is TimeType.SIM:
        driver = 'time'
    else:
        raise Exception('FIXME: Only SIM timetype is supported currently.')
    items = list(keys.items())
    items.sort()

    # Temp sanity check while we transition from milliseconds to seconds
    # based time values.
    if __debug__:
        if not suppress_format_warning:
            for item in items:
                # (PyCharm seems to think item is a float, not a tuple)
                _ba.time_format_check(timeformat, item[0])

    if timeformat is TimeFormat.SECONDS:
        mult = 1000
    elif timeformat is TimeFormat.MILLISECONDS:
        mult = 1
    else:
        raise ValueError('invalid timeformat value: "' + str(timeformat) + '"')

    for i in range(size):
        curve = _ba.newnode('animcurve',
                            owner=node,
                            name=('Driving ' + str(node) + ' \'' + attr +
                                  '\' member ' + str(i)))
        sharedobj('globals').connectattr(driver, curve, 'in')
        curve.times = [int(mult * time) for time, val in items]
        curve.values = [val[i] for time, val in items]
        curve.offset = _ba.time(timeformat=TimeFormat.MILLISECONDS) + int(
            mult * offset)
        curve.loop = loop
        curve.connectattr('out', combine, 'input' + str(i))

        # If we're not looping, set a timer to kill this
        # curve after its done its job.
        if not loop:
            # (PyCharm seems to think item is a float, not a tuple)
            _ba.timer(int(mult * items[-1][0]) + 1000,
                      curve.delete,
                      timeformat=TimeFormat.MILLISECONDS)
    combine.connectattr('output', node, attr)

    # If we're not looping, set a timer to kill the combine once
    # the job is done.
    # FIXME: Even if we are looping we should have a way to die
    #  once we get disconnected.
    if not loop:
        # (PyCharm seems to think item is a float, not a tuple)
        _ba.timer(int(mult * items[-1][0]) + 1000,
                  combine.delete,
                  timeformat=TimeFormat.MILLISECONDS)


def show_damage_count(damage: str, position: Sequence[float],
                      direction: Sequence[float]) -> None:
    """Pop up a damage count at a position in space.

    Category: Gameplay Functions
    """
    lifespan = 1.0
    app = _ba.app

    # FIXME: Should never vary game elements based on local config.
    #  (connected clients may have differing configs so they won't
    #  get the intended results).
    do_big = app.interface_type == 'small' or app.vr_mode
    txtnode = _ba.newnode('text',
                          attrs={
                              'text': damage,
                              'in_world': True,
                              'h_align': 'center',
                              'flatness': 1.0,
                              'shadow': 1.0 if do_big else 0.7,
                              'color': (1, 0.25, 0.25, 1),
                              'scale': 0.015 if do_big else 0.01
                          })
    # Translate upward.
    tcombine = _ba.newnode('combine', owner=txtnode, attrs={'size': 3})
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
    animate(tcombine, 'input0',
            {i[0] * lifespan: p_start + p_dir * i[1]
             for i in v_vals})
    p_start = position[1]
    p_dir = direction[1]
    animate(tcombine, 'input1',
            {i[0] * lifespan: p_start + p_dir * i[1]
             for i in v_vals})
    p_start = position[2]
    p_dir = direction[2]
    animate(tcombine, 'input2',
            {i[0] * lifespan: p_start + p_dir * i[1]
             for i in v_vals})
    animate(txtnode, 'opacity', {0.7 * lifespan: 1.0, lifespan: 0.0})
    _ba.timer(lifespan, txtnode.delete)


def timestring(timeval: float,
               centi: bool = True,
               timeformat: ba.TimeFormat = TimeFormat.SECONDS,
               suppress_format_warning: bool = False) -> ba.Lstr:
    """Generate a ba.Lstr for displaying a time value.

    Category: General Utility Functions

    Given a time value, returns a ba.Lstr with:
    (hours if > 0 ) : minutes : seconds : (centiseconds if centi=True).

    Time 'timeval' is specified in seconds by default, or 'timeformat' can
    be set to ba.TimeFormat.MILLISECONDS to accept milliseconds instead.

    WARNING: the underlying Lstr value is somewhat large so don't use this
    to rapidly update Node text values for an onscreen timer or you may
    consume significant network bandwidth.  For that purpose you should
    use a 'timedisplay' Node and attribute connections.

    """
    from ba._lang import Lstr

    # Temp sanity check while we transition from milliseconds to seconds
    # based time values.
    if __debug__:
        if not suppress_format_warning:
            _ba.time_format_check(timeformat, timeval)

    # We operate on milliseconds internally.
    if timeformat is TimeFormat.SECONDS:
        timeval = int(1000 * timeval)
    elif timeformat is TimeFormat.MILLISECONDS:
        pass
    else:
        raise ValueError(f'invalid timeformat: {timeformat}')
    if not isinstance(timeval, int):
        timeval = int(timeval)
    bits = []
    subs = []
    hval = (timeval // 1000) // (60 * 60)
    if hval != 0:
        bits.append('${H}')
        subs.append(('${H}',
                     Lstr(resource='timeSuffixHoursText',
                          subs=[('${COUNT}', str(hval))])))
    mval = ((timeval // 1000) // 60) % 60
    if mval != 0:
        bits.append('${M}')
        subs.append(('${M}',
                     Lstr(resource='timeSuffixMinutesText',
                          subs=[('${COUNT}', str(mval))])))

    # We add seconds if its non-zero *or* we haven't added anything else.
    if centi:
        sval = (timeval / 1000.0 % 60.0)
        if sval >= 0.005 or not bits:
            bits.append('${S}')
            subs.append(('${S}',
                         Lstr(resource='timeSuffixSecondsText',
                              subs=[('${COUNT}', ('%.2f' % sval))])))
    else:
        sval = (timeval // 1000 % 60)
        if sval != 0 or not bits:
            bits.append('${S}')
            subs.append(('${S}',
                         Lstr(resource='timeSuffixSecondsText',
                              subs=[('${COUNT}', str(sval))])))
    return Lstr(value=' '.join(bits), subs=subs)


def cameraflash(duration: float = 999.0) -> None:
    """Create a strobing camera flash effect.

    Category: Gameplay Functions

    (as seen when a team wins a game)
    Duration is in seconds.
    """
    # pylint: disable=too-many-locals
    import random
    from ba._nodeactor import NodeActor
    x_spread = 10
    y_spread = 5
    positions = [[-x_spread, -y_spread], [0, -y_spread], [0, y_spread],
                 [x_spread, -y_spread], [x_spread, y_spread],
                 [-x_spread, y_spread]]
    times = [0, 2700, 1000, 1800, 500, 1400]

    # Store this on the current activity so we only have one at a time.
    # FIXME: Need a type safe way to do this.
    activity = _ba.getactivity()
    activity.camera_flash_data = []  # type: ignore
    for i in range(6):
        light = NodeActor(
            _ba.newnode('light',
                        attrs={
                            'position': (positions[i][0], 0, positions[i][1]),
                            'radius': 1.0,
                            'lights_volumes': False,
                            'height_attenuated': False,
                            'color': (0.2, 0.2, 0.8)
                        }))
        sval = 1.87
        iscale = 1.3
        tcombine = _ba.newnode('combine',
                               owner=light.node,
                               attrs={
                                   'size': 3,
                                   'input0': positions[i][0],
                                   'input1': 0,
                                   'input2': positions[i][1]
                               })
        assert light.node
        tcombine.connectattr('output', light.node, 'position')
        xval = positions[i][0]
        yval = positions[i][1]
        spd = 0.5 + random.random()
        spd2 = 0.5 + random.random()
        animate(tcombine,
                'input0', {
                    0.0: xval + 0,
                    0.069 * spd: xval + 10.0,
                    0.143 * spd: xval - 10.0,
                    0.201 * spd: xval + 0
                },
                loop=True)
        animate(tcombine,
                'input2', {
                    0.0: yval + 0,
                    0.15 * spd2: yval + 10.0,
                    0.287 * spd2: yval - 10.0,
                    0.398 * spd2: yval + 0
                },
                loop=True)
        animate(light.node,
                'intensity', {
                    0.0: 0,
                    0.02 * sval: 0,
                    0.05 * sval: 0.8 * iscale,
                    0.08 * sval: 0,
                    0.1 * sval: 0
                },
                loop=True,
                offset=times[i])
        _ba.timer((times[i] + random.randint(1, int(duration)) * 40 * sval),
                  light.node.delete,
                  timeformat=TimeFormat.MILLISECONDS)
        activity.camera_flash_data.append(light)  # type: ignore
