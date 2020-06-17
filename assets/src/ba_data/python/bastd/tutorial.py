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
"""Wrangles the game tutorial sequence."""

# Not too concerned with keeping this old module pretty;
# don't expect to be revisiting it.
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=too-many-lines
# pylint: disable=missing-function-docstring, missing-class-docstring
# pylint: disable=invalid-name
# pylint: disable=too-many-locals
# pylint: disable=unused-argument
# pylint: disable=unused-variable

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import _ba
import ba
from bastd.actor import spaz as basespaz

if TYPE_CHECKING:
    from typing import (Any, Optional, Dict, List, Tuple, Callable, Sequence,
                        Union)


def _safesetattr(node: Optional[ba.Node], attr: str, value: Any) -> None:
    if node:
        setattr(node, attr, value)


class ButtonPress:

    def __init__(self,
                 button: str,
                 delay: int = 0,
                 release: bool = True,
                 release_delay: int = 0):
        self._button = button
        self._delay = delay
        self._release = release
        self._release_delay = release_delay

    def run(self, a: TutorialActivity) -> None:
        s = a.current_spaz
        assert s is not None
        img: Optional[ba.Node]
        release_call: Optional[Callable]
        color: Optional[Sequence[float]]
        if self._button == 'punch':
            call = s.on_punch_press
            release_call = s.on_punch_release
            img = a.punch_image
            color = a.punch_image_color
        elif self._button == 'jump':
            call = s.on_jump_press
            release_call = s.on_jump_release
            img = a.jump_image
            color = a.jump_image_color
        elif self._button == 'bomb':
            call = s.on_bomb_press
            release_call = s.on_bomb_release
            img = a.bomb_image
            color = a.bomb_image_color
        elif self._button == 'pickUp':
            call = s.on_pickup_press
            release_call = s.on_pickup_release
            img = a.pickup_image
            color = a.pickup_image_color
        elif self._button == 'run':
            call = ba.Call(s.on_run, 1.0)
            release_call = ba.Call(s.on_run, 0.0)
            img = None
            color = None
        else:
            raise Exception(f'invalid button: {self._button}')

        brightness = 4.0
        if color is not None:
            c_bright = list(color)
            c_bright[0] *= brightness
            c_bright[1] *= brightness
            c_bright[2] *= brightness
        else:
            c_bright = [1.0, 1.0, 1.0]

        if self._delay == 0:
            call()
            if img is not None:
                img.color = c_bright
                img.vr_depth = -40
        else:
            ba.timer(self._delay, call, timeformat=ba.TimeFormat.MILLISECONDS)
            if img is not None:
                ba.timer(self._delay,
                         ba.Call(_safesetattr, img, 'color', c_bright),
                         timeformat=ba.TimeFormat.MILLISECONDS)
                ba.timer(self._delay,
                         ba.Call(_safesetattr, img, 'vr_depth', -30),
                         timeformat=ba.TimeFormat.MILLISECONDS)
        if self._release:
            if self._delay == 0 and self._release_delay == 0:
                release_call()
            else:
                ba.timer(0.001 * (self._delay + self._release_delay),
                         release_call)
            if img is not None:
                ba.timer(self._delay + self._release_delay + 100,
                         ba.Call(_safesetattr, img, 'color', color),
                         timeformat=ba.TimeFormat.MILLISECONDS)
                ba.timer(self._delay + self._release_delay + 100,
                         ba.Call(_safesetattr, img, 'vr_depth', -20),
                         timeformat=ba.TimeFormat.MILLISECONDS)


class ButtonRelease:

    def __init__(self, button: str, delay: int = 0):
        self._button = button
        self._delay = delay

    def run(self, a: TutorialActivity) -> None:
        s = a.current_spaz
        assert s is not None
        call: Optional[Callable]
        img: Optional[ba.Node]
        color: Optional[Sequence[float]]
        if self._button == 'punch':
            call = s.on_punch_release
            img = a.punch_image
            color = a.punch_image_color
        elif self._button == 'jump':
            call = s.on_jump_release
            img = a.jump_image
            color = a.jump_image_color
        elif self._button == 'bomb':
            call = s.on_bomb_release
            img = a.bomb_image
            color = a.bomb_image_color
        elif self._button == 'pickUp':
            call = s.on_pickup_press
            img = a.pickup_image
            color = a.pickup_image_color
        elif self._button == 'run':
            call = ba.Call(s.on_run, 0.0)
            img = None
            color = None
        else:
            raise Exception('invalid button: ' + self._button)
        if self._delay == 0:
            call()
        else:
            ba.timer(self._delay, call, timeformat=ba.TimeFormat.MILLISECONDS)
        if img is not None:
            ba.timer(self._delay + 100,
                     ba.Call(_safesetattr, img, 'color', color),
                     timeformat=ba.TimeFormat.MILLISECONDS)
            ba.timer(self._delay + 100,
                     ba.Call(_safesetattr, img, 'vr_depth', -20),
                     timeformat=ba.TimeFormat.MILLISECONDS)


class Player(ba.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.pressed = False


class Team(ba.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        pass


class TutorialActivity(ba.Activity[Player, Team]):

    def __init__(self, settings: dict = None):
        from bastd.maps import Rampage
        if settings is None:
            settings = {}
        super().__init__(settings)
        self.current_spaz: Optional[basespaz.Spaz] = None
        self._benchmark_type = getattr(ba.getsession(), 'benchmark_type', None)
        self.last_start_time: Optional[int] = None
        self.cycle_times: List[int] = []
        self.allow_pausing = True
        self.allow_kick_idle_players = False
        self._issued_warning = False
        self._map_type = Rampage
        self._map_type.preload()
        self._jump_button_tex = ba.gettexture('buttonJump')
        self._pick_up_button_tex = ba.gettexture('buttonPickUp')
        self._bomb_button_tex = ba.gettexture('buttonBomb')
        self._punch_button_tex = ba.gettexture('buttonPunch')
        self._r = 'tutorial'
        self._have_skipped = False
        self.stick_image_position_x = self.stick_image_position_y = 0.0
        self.spawn_sound = ba.getsound('spawn')
        self.map: Optional[ba.Map] = None
        self.text: Optional[ba.Node] = None
        self._skip_text: Optional[ba.Node] = None
        self._skip_count_text: Optional[ba.Node] = None
        self._scale: Optional[float] = None
        self._stick_base_position: Tuple[float, float] = (0.0, 0.0)
        self._stick_nub_position: Tuple[float, float] = (0.0, 0.0)
        self._stick_base_image_color: Sequence[float] = (1.0, 1.0, 1.0, 1.0)
        self._stick_nub_image_color: Sequence[float] = (1.0, 1.0, 1.0, 1.0)
        self._time: int = -1
        self.punch_image_color = (1.0, 1.0, 1.0)
        self.punch_image: Optional[ba.Node] = None
        self.bomb_image: Optional[ba.Node] = None
        self.jump_image: Optional[ba.Node] = None
        self.pickup_image: Optional[ba.Node] = None
        self._stick_base_image: Optional[ba.Node] = None
        self._stick_nub_image: Optional[ba.Node] = None
        self.bomb_image_color = (1.0, 1.0, 1.0)
        self.pickup_image_color = (1.0, 1.0, 1.0)
        self.control_ui_nodes: List[ba.Node] = []
        self.spazzes: Dict[int, basespaz.Spaz] = {}
        self.jump_image_color = (1.0, 1.0, 1.0)
        self._entries: List[Any] = []
        self._read_entries_timer: Optional[ba.Timer] = None
        self._entry_timer: Optional[ba.Timer] = None

    def on_transition_in(self) -> None:
        super().on_transition_in()
        ba.setmusic(ba.MusicType.CHAR_SELECT, continuous=True)
        self.map = self._map_type()

    def on_begin(self) -> None:
        super().on_begin()

        ba.set_analytics_screen('Tutorial Start')
        _ba.increment_analytics_count('Tutorial start')

        if bool(False):
            # Buttons on top.
            text_y = 140
            buttons_y = 250
        else:
            # Buttons on bottom.
            text_y = 260
            buttons_y = 160

        # Need different versions of this: taps/buttons/keys.
        self.text = ba.newnode('text',
                               attrs={
                                   'text': '',
                                   'scale': 1.9,
                                   'position': (0, text_y),
                                   'maxwidth': 500,
                                   'flatness': 0.0,
                                   'shadow': 0.5,
                                   'h_align': 'center',
                                   'v_align': 'center',
                                   'v_attach': 'center'
                               })

        # Need different versions of this: taps/buttons/keys.
        txt = ba.Lstr(
            resource=self._r +
            '.cpuBenchmarkText') if self._benchmark_type == 'cpu' else ba.Lstr(
                resource=self._r + '.toSkipPressAnythingText')
        t = self._skip_text = ba.newnode('text',
                                         attrs={
                                             'text': txt,
                                             'maxwidth': 900,
                                             'scale': 1.1,
                                             'vr_depth': 100,
                                             'position': (0, 30),
                                             'h_align': 'center',
                                             'v_align': 'center',
                                             'v_attach': 'bottom'
                                         })
        ba.animate(t, 'opacity', {1.0: 0.0, 2.0: 0.7})
        self._skip_count_text = ba.newnode('text',
                                           attrs={
                                               'text': '',
                                               'scale': 1.4,
                                               'vr_depth': 90,
                                               'position': (0, 70),
                                               'h_align': 'center',
                                               'v_align': 'center',
                                               'v_attach': 'bottom'
                                           })

        ouya = False

        self._scale = scale = 0.6
        center_offs = 130.0 * scale
        offs = 65.0 * scale
        position = (0, buttons_y)
        image_size = 90.0 * scale
        image_size_2 = 220.0 * scale
        nub_size = 110.0 * scale
        p = (position[0] + center_offs, position[1] - offs)

        def _sc(r: float, g: float, b: float) -> Tuple[float, float, float]:
            return 0.6 * r, 0.6 * g, 0.6 * b

        self.jump_image_color = c = _sc(0.4, 1, 0.4)
        self.jump_image = ba.newnode('image',
                                     attrs={
                                         'texture': self._jump_button_tex,
                                         'absolute_scale': True,
                                         'vr_depth': -20,
                                         'position': p,
                                         'scale': (image_size, image_size),
                                         'color': c
                                     })
        p = (position[0] + center_offs - offs, position[1])
        self.punch_image_color = c = _sc(0.2, 0.6, 1) if ouya else _sc(
            1, 0.7, 0.3)
        self.punch_image = ba.newnode(
            'image',
            attrs={
                'texture': ba.gettexture('buttonPunch'),
                'absolute_scale': True,
                'vr_depth': -20,
                'position': p,
                'scale': (image_size, image_size),
                'color': c
            })
        p = (position[0] + center_offs + offs, position[1])
        self.bomb_image_color = c = _sc(1, 0.3, 0.3)
        self.bomb_image = ba.newnode(
            'image',
            attrs={
                'texture': ba.gettexture('buttonBomb'),
                'absolute_scale': True,
                'vr_depth': -20,
                'position': p,
                'scale': (image_size, image_size),
                'color': c
            })
        p = (position[0] + center_offs, position[1] + offs)
        self.pickup_image_color = c = _sc(1, 0.8, 0.3) if ouya else _sc(
            0.5, 0.5, 1)
        self.pickup_image = ba.newnode(
            'image',
            attrs={
                'texture': ba.gettexture('buttonPickUp'),
                'absolute_scale': True,
                'vr_depth': -20,
                'position': p,
                'scale': (image_size, image_size),
                'color': c
            })

        self._stick_base_position = p = (position[0] - center_offs,
                                         position[1])
        self._stick_base_image_color = c2 = (0.25, 0.25, 0.25, 1.0)
        self._stick_base_image = ba.newnode(
            'image',
            attrs={
                'texture': ba.gettexture('nub'),
                'absolute_scale': True,
                'vr_depth': -40,
                'position': p,
                'scale': (image_size_2, image_size_2),
                'color': c2
            })
        self._stick_nub_position = p = (position[0] - center_offs, position[1])
        self._stick_nub_image_color = c3 = (0.4, 0.4, 0.4, 1.0)
        self._stick_nub_image = ba.newnode('image',
                                           attrs={
                                               'texture': ba.gettexture('nub'),
                                               'absolute_scale': True,
                                               'position': p,
                                               'scale': (nub_size, nub_size),
                                               'color': c3
                                           })
        self.control_ui_nodes = [
            self.jump_image, self.punch_image, self.bomb_image,
            self.pickup_image, self._stick_base_image, self._stick_nub_image
        ]
        for n in self.control_ui_nodes:
            n.opacity = 0.0
        self._read_entries()

    def set_stick_image_position(self, x: float, y: float) -> None:

        # Clamp this to a circle.
        len_squared = x * x + y * y
        if len_squared > 1.0:
            length = math.sqrt(len_squared)
            mult = 1.0 / length
            x *= mult
            y *= mult

        self.stick_image_position_x = x
        self.stick_image_position_y = y
        offs = 50.0
        assert self._scale is not None
        p = [
            self._stick_nub_position[0] + x * offs * self._scale,
            self._stick_nub_position[1] + y * offs * self._scale
        ]
        c = list(self._stick_nub_image_color)
        if abs(x) > 0.1 or abs(y) > 0.1:
            c[0] *= 2.0
            c[1] *= 4.0
            c[2] *= 2.0
        assert self._stick_nub_image is not None
        self._stick_nub_image.position = p
        self._stick_nub_image.color = c
        c = list(self._stick_base_image_color)
        if abs(x) > 0.1 or abs(y) > 0.1:
            c[0] *= 1.5
            c[1] *= 1.5
            c[2] *= 1.5
        assert self._stick_base_image is not None
        self._stick_base_image.color = c

    def _read_entries(self) -> None:
        try:

            class Reset:

                def __init__(self) -> None:
                    pass

                def run(self, a: TutorialActivity) -> None:

                    # if we're looping, print out how long each cycle took
                    # print out how long each cycle took..
                    if a.last_start_time is not None:
                        tval = ba.time(
                            ba.TimeType.REAL,
                            ba.TimeFormat.MILLISECONDS) - a.last_start_time
                        assert isinstance(tval, int)
                        diff = tval
                        a.cycle_times.append(diff)
                        ba.screenmessage(
                            'cycle time: ' + str(diff) + ' (average: ' +
                            str(sum(a.cycle_times) / len(a.cycle_times)) + ')')
                    tval = ba.time(ba.TimeType.REAL,
                                   ba.TimeFormat.MILLISECONDS)
                    assert isinstance(tval, int)
                    a.last_start_time = tval

                    assert a.text
                    a.text.text = ''
                    for spaz in list(a.spazzes.values()):
                        spaz.handlemessage(ba.DieMessage(immediate=True))
                    a.spazzes = {}
                    a.current_spaz = None
                    for n in a.control_ui_nodes:
                        n.opacity = 0.0
                    a.set_stick_image_position(0, 0)

            # Can be used for debugging.
            class SetSpeed:

                def __init__(self, speed: int):
                    self._speed = speed

                def run(self, a: TutorialActivity) -> None:
                    print('setting to', self._speed)
                    _ba.set_debug_speed_exponent(self._speed)

            class RemoveGloves:

                def __init__(self) -> None:
                    pass

                def run(self, a: TutorialActivity) -> None:
                    # pylint: disable=protected-access
                    assert a.current_spaz is not None
                    # noinspection PyProtectedMember
                    a.current_spaz._gloves_wear_off()

            class KillSpaz:

                def __init__(self, num: int, explode: bool = False):
                    self._num = num
                    self._explode = explode

                def run(self, a: TutorialActivity) -> None:
                    if self._explode:
                        a.spazzes[self._num].shatter()
                    del a.spazzes[self._num]

            class SpawnSpaz:

                def __init__(self,
                             num: int,
                             position: Sequence[float],
                             color: Sequence[float] = (1.0, 1.0, 1.0),
                             make_current: bool = False,
                             relative_to: int = None,
                             name: Union[str, ba.Lstr] = '',
                             flash: bool = True,
                             angle: float = 0.0):
                    self._num = num
                    self._position = position
                    self._make_current = make_current
                    self._color = color
                    self._relative_to = relative_to
                    self._name = name
                    self._flash = flash
                    self._angle = angle

                def run(self, a: TutorialActivity) -> None:

                    # if they gave a 'relative to' spaz, position is relative
                    # to them
                    pos: Sequence[float]
                    if self._relative_to is not None:
                        snode = a.spazzes[self._relative_to].node
                        assert snode
                        their_pos = snode.position
                        pos = (their_pos[0] + self._position[0],
                               their_pos[1] + self._position[1],
                               their_pos[2] + self._position[2])
                    else:
                        pos = self._position

                    # if there's already a spaz at this spot, insta-kill it
                    if self._num in a.spazzes:
                        a.spazzes[self._num].handlemessage(
                            ba.DieMessage(immediate=True))

                    s = a.spazzes[self._num] = basespaz.Spaz(
                        color=self._color,
                        start_invincible=self._flash,
                        demo_mode=True)

                    # FIXME: Should extend spaz to support Lstr names.
                    assert s.node
                    if isinstance(self._name, ba.Lstr):
                        s.node.name = self._name.evaluate()
                    else:
                        s.node.name = self._name
                    s.node.name_color = self._color
                    s.handlemessage(ba.StandMessage(pos, self._angle))
                    if self._make_current:
                        a.current_spaz = s
                    if self._flash:
                        ba.playsound(a.spawn_sound, position=pos)

            class Powerup:

                def __init__(self,
                             num: int,
                             position: Sequence[float],
                             color: Sequence[float] = (1.0, 1.0, 1.0),
                             make_current: bool = False,
                             relative_to: int = None):
                    self._position = position
                    self._relative_to = relative_to

                def run(self, a: TutorialActivity) -> None:
                    # If they gave a 'relative to' spaz, position is relative
                    # to them.
                    pos: Sequence[float]
                    if self._relative_to is not None:
                        snode = a.spazzes[self._relative_to].node
                        assert snode
                        their_pos = snode.position
                        pos = (their_pos[0] + self._position[0],
                               their_pos[1] + self._position[1],
                               their_pos[2] + self._position[2])
                    else:
                        pos = self._position
                    from bastd.actor import powerupbox
                    powerupbox.PowerupBox(position=pos,
                                          poweruptype='punch').autoretain()

            class Delay:

                def __init__(self, time: int) -> None:
                    self._time = time

                def run(self, a: TutorialActivity) -> int:
                    return self._time

            class AnalyticsScreen:

                def __init__(self, screen: str) -> None:
                    self._screen = screen

                def run(self, a: TutorialActivity) -> None:
                    ba.set_analytics_screen(self._screen)

            class DelayOld:

                def __init__(self, time: int) -> None:
                    self._time = time

                def run(self, a: TutorialActivity) -> int:
                    return int(0.9 * self._time)

            class DelayOld2:

                def __init__(self, time: int) -> None:
                    self._time = time

                def run(self, a: TutorialActivity) -> int:
                    return int(0.8 * self._time)

            class End:

                def __init__(self) -> None:
                    pass

                def run(self, a: TutorialActivity) -> None:
                    _ba.increment_analytics_count('Tutorial finish')
                    a.end()

            class Move:

                def __init__(self, x: float, y: float):
                    self._x = float(x)
                    self._y = float(y)

                def run(self, a: TutorialActivity) -> None:
                    s = a.current_spaz
                    assert s
                    # FIXME: Game should take floats for this.
                    x_clamped = self._x
                    y_clamped = self._y
                    s.on_move_left_right(x_clamped)
                    s.on_move_up_down(y_clamped)
                    a.set_stick_image_position(self._x, self._y)

            class MoveLR:

                def __init__(self, x: float):
                    self._x = float(x)

                def run(self, a: TutorialActivity) -> None:
                    s = a.current_spaz
                    assert s
                    # FIXME: Game should take floats for this.
                    x_clamped = self._x
                    s.on_move_left_right(x_clamped)
                    a.set_stick_image_position(self._x,
                                               a.stick_image_position_y)

            class MoveUD:

                def __init__(self, y: float):
                    self._y = float(y)

                def run(self, a: TutorialActivity) -> None:
                    s = a.current_spaz
                    assert s
                    # FIXME: Game should take floats for this.
                    y_clamped = self._y
                    s.on_move_up_down(y_clamped)
                    a.set_stick_image_position(a.stick_image_position_x,
                                               self._y)

            class Bomb(ButtonPress):

                def __init__(self,
                             delay: int = 0,
                             release: bool = True,
                             release_delay: int = 500):
                    ButtonPress.__init__(self,
                                         'bomb',
                                         delay=delay,
                                         release=release,
                                         release_delay=release_delay)

            class Jump(ButtonPress):

                def __init__(self,
                             delay: int = 0,
                             release: bool = True,
                             release_delay: int = 500):
                    ButtonPress.__init__(self,
                                         'jump',
                                         delay=delay,
                                         release=release,
                                         release_delay=release_delay)

            class Punch(ButtonPress):

                def __init__(self,
                             delay: int = 0,
                             release: bool = True,
                             release_delay: int = 500):
                    ButtonPress.__init__(self,
                                         'punch',
                                         delay=delay,
                                         release=release,
                                         release_delay=release_delay)

            class PickUp(ButtonPress):

                def __init__(self,
                             delay: int = 0,
                             release: bool = True,
                             release_delay: int = 500):
                    ButtonPress.__init__(self,
                                         'pickUp',
                                         delay=delay,
                                         release=release,
                                         release_delay=release_delay)

            class Run(ButtonPress):

                def __init__(self,
                             delay: int = 0,
                             release: bool = True,
                             release_delay: int = 500):
                    ButtonPress.__init__(self,
                                         'run',
                                         delay=delay,
                                         release=release,
                                         release_delay=release_delay)

            class BombRelease(ButtonRelease):

                def __init__(self, delay: int = 0):
                    super().__init__('bomb', delay=delay)

            class JumpRelease(ButtonRelease):

                def __init__(self, delay: int = 0):
                    super().__init__('jump', delay=delay)

            class PunchRelease(ButtonRelease):

                def __init__(self, delay: int = 0):
                    super().__init__('punch', delay=delay)

            class PickUpRelease(ButtonRelease):

                def __init__(self, delay: int = 0):
                    super().__init__('pickUp', delay=delay)

            class RunRelease(ButtonRelease):

                def __init__(self, delay: int = 0):
                    super().__init__('run', delay=delay)

            class ShowControls:

                def __init__(self) -> None:
                    pass

                def run(self, a: TutorialActivity) -> None:
                    for n in a.control_ui_nodes:
                        ba.animate(n, 'opacity', {0.0: 0.0, 1.0: 1.0})

            class Text:

                def __init__(self, text: Union[str, ba.Lstr]):
                    self.text = text

                def run(self, a: TutorialActivity) -> None:
                    assert a.text
                    a.text.text = self.text

            class PrintPos:

                def __init__(self, spaz_num: int = None):
                    self._spaz_num = spaz_num

                def run(self, a: TutorialActivity) -> None:
                    if self._spaz_num is None:
                        s = a.current_spaz
                    else:
                        s = a.spazzes[self._spaz_num]
                    assert s and s.node
                    t = list(s.node.position)
                    print('RestorePos(' + str((t[0], t[1] - 1.0, t[2])) + '),')

            class RestorePos:

                def __init__(self, pos: Sequence[float]) -> None:
                    self._pos = pos

                def run(self, a: TutorialActivity) -> None:
                    s = a.current_spaz
                    assert s
                    s.handlemessage(ba.StandMessage(self._pos, 0))

            class Celebrate:

                def __init__(self,
                             celebrate_type: str = 'both',
                             spaz_num: int = None,
                             duration: int = 1000):
                    self._spaz_num = spaz_num
                    self._celebrate_type = celebrate_type
                    self._duration = duration

                def run(self, a: TutorialActivity) -> None:
                    if self._spaz_num is None:
                        s = a.current_spaz
                    else:
                        s = a.spazzes[self._spaz_num]
                    assert s and s.node
                    if self._celebrate_type == 'right':
                        s.node.handlemessage('celebrate_r', self._duration)
                    elif self._celebrate_type == 'left':
                        s.node.handlemessage('celebrate_l', self._duration)
                    elif self._celebrate_type == 'both':
                        s.node.handlemessage('celebrate', self._duration)
                    else:
                        raise Exception('invalid celebrate type ' +
                                        self._celebrate_type)

            self._entries = [
                Reset(),
                SpawnSpaz(0, (0, 5.5, -3.0), make_current=True),
                DelayOld(1000),
                AnalyticsScreen('Tutorial Section 1'),
                Text(ba.Lstr(resource=self._r + '.phrase01Text')),  # hi there
                Celebrate('left'),
                DelayOld(2000),
                Text(
                    ba.Lstr(resource=self._r + '.phrase02Text',
                            subs=[
                                ('${APP_NAME}', ba.Lstr(resource='titleText'))
                            ])),  # welcome to <appname>
                DelayOld(80),
                Run(release=False),
                Jump(release=False),
                MoveLR(1),
                MoveUD(0),
                DelayOld(70),
                RunRelease(),
                JumpRelease(),
                DelayOld(60),
                MoveUD(1),
                DelayOld(30),
                MoveLR(0),
                DelayOld(90),
                MoveLR(-1),
                DelayOld(20),
                MoveUD(0),
                DelayOld(70),
                MoveUD(-1),
                DelayOld(20),
                MoveLR(0),
                DelayOld(80),
                MoveUD(0),
                DelayOld(1500),
                Text(ba.Lstr(resource=self._r +
                             '.phrase03Text')),  # here's a few tips
                DelayOld(1000),
                ShowControls(),
                DelayOld(1000),
                Jump(),
                DelayOld(1000),
                Jump(),
                DelayOld(1000),
                AnalyticsScreen('Tutorial Section 2'),
                Text(
                    ba.Lstr(resource=self._r + '.phrase04Text',
                            subs=[
                                ('${APP_NAME}', ba.Lstr(resource='titleText'))
                            ])),  # many things are based on physics
                DelayOld(20),
                MoveUD(0),
                DelayOld(60),
                MoveLR(0),
                DelayOld(10),
                MoveLR(0),
                MoveUD(0),
                DelayOld(10),
                MoveLR(0),
                MoveUD(0),
                DelayOld(20),
                MoveUD(-0.0575579),
                DelayOld(10),
                MoveUD(-0.207831),
                DelayOld(30),
                MoveUD(-0.309793),
                DelayOld(10),
                MoveUD(-0.474502),
                DelayOld(10),
                MoveLR(0.00390637),
                MoveUD(-0.647053),
                DelayOld(20),
                MoveLR(-0.0745262),
                MoveUD(-0.819605),
                DelayOld(10),
                MoveLR(-0.168645),
                MoveUD(-0.937254),
                DelayOld(30),
                MoveLR(-0.294137),
                MoveUD(-1),
                DelayOld(10),
                MoveLR(-0.411786),
                DelayOld(10),
                MoveLR(-0.639241),
                DelayOld(30),
                MoveLR(-0.75689),
                DelayOld(10),
                MoveLR(-0.905911),
                DelayOld(20),
                MoveLR(-1),
                DelayOld(50),
                MoveUD(-0.960784),
                DelayOld(20),
                MoveUD(-0.819605),
                MoveUD(-0.61568),
                DelayOld(20),
                MoveUD(-0.427442),
                DelayOld(20),
                MoveUD(-0.231361),
                DelayOld(10),
                MoveUD(-0.00390637),
                DelayOld(30),
                MoveUD(0.333354),
                MoveUD(0.584338),
                DelayOld(20),
                MoveUD(0.764733),
                DelayOld(30),
                MoveLR(-0.803949),
                MoveUD(0.913755),
                DelayOld(10),
                MoveLR(-0.647084),
                MoveUD(0.992187),
                DelayOld(20),
                MoveLR(-0.435316),
                MoveUD(1),
                DelayOld(20),
                MoveLR(-0.168645),
                MoveUD(0.976501),
                MoveLR(0.0744957),
                MoveUD(0.905911),
                DelayOld(20),
                MoveLR(0.270577),
                MoveUD(0.843165),
                DelayOld(20),
                MoveLR(0.435286),
                MoveUD(0.780419),
                DelayOld(10),
                MoveLR(0.66274),
                MoveUD(0.647084),
                DelayOld(30),
                MoveLR(0.803919),
                MoveUD(0.458846),
                MoveLR(0.929411),
                MoveUD(0.223548),
                DelayOld(20),
                MoveLR(0.95294),
                MoveUD(0.137272),
                DelayOld(20),
                MoveLR(1),
                MoveUD(-0.0509659),
                DelayOld(20),
                MoveUD(-0.247047),
                DelayOld(20),
                MoveUD(-0.443129),
                DelayOld(20),
                MoveUD(-0.694113),
                MoveUD(-0.921567),
                DelayOld(30),
                MoveLR(0.858821),
                MoveUD(-1),
                DelayOld(10),
                MoveLR(0.68627),
                DelayOld(10),
                MoveLR(0.364696),
                DelayOld(20),
                MoveLR(0.0509659),
                DelayOld(20),
                MoveLR(-0.223548),
                DelayOld(10),
                MoveLR(-0.600024),
                MoveUD(-0.913724),
                DelayOld(30),
                MoveLR(-0.858852),
                MoveUD(-0.717643),
                MoveLR(-1),
                MoveUD(-0.474502),
                DelayOld(20),
                MoveUD(-0.396069),
                DelayOld(20),
                MoveUD(-0.286264),
                DelayOld(20),
                MoveUD(-0.137242),
                DelayOld(20),
                MoveUD(0.0353099),
                DelayOld(10),
                MoveUD(0.32551),
                DelayOld(20),
                MoveUD(0.592181),
                DelayOld(10),
                MoveUD(0.851009),
                DelayOld(10),
                MoveUD(1),
                DelayOld(30),
                MoveLR(-0.764733),
                DelayOld(20),
                MoveLR(-0.403943),
                MoveLR(-0.145116),
                DelayOld(30),
                MoveLR(0.0901822),
                MoveLR(0.32548),
                DelayOld(30),
                MoveLR(0.560778),
                MoveUD(0.929441),
                DelayOld(20),
                MoveLR(0.709799),
                MoveUD(0.73336),
                MoveLR(0.803919),
                MoveUD(0.545122),
                DelayOld(20),
                MoveLR(0.882351),
                MoveUD(0.356883),
                DelayOld(10),
                MoveLR(0.968627),
                MoveUD(0.113742),
                DelayOld(20),
                MoveLR(0.992157),
                MoveUD(-0.0823389),
                DelayOld(30),
                MoveUD(-0.309793),
                DelayOld(10),
                MoveUD(-0.545091),
                DelayOld(20),
                MoveLR(0.882351),
                MoveUD(-0.874508),
                DelayOld(20),
                MoveLR(0.756859),
                MoveUD(-1),
                DelayOld(10),
                MoveLR(0.576464),
                DelayOld(20),
                MoveLR(0.254891),
                DelayOld(10),
                MoveLR(-0.0274667),
                DelayOld(10),
                MoveLR(-0.356883),
                DelayOld(30),
                MoveLR(-0.592181),
                MoveLR(-0.827479),
                MoveUD(-0.921567),
                DelayOld(20),
                MoveLR(-1),
                MoveUD(-0.749016),
                DelayOld(20),
                MoveUD(-0.61568),
                DelayOld(10),
                MoveUD(-0.403912),
                DelayOld(20),
                MoveUD(-0.207831),
                DelayOld(10),
                MoveUD(0.121586),
                DelayOld(30),
                MoveUD(0.34904),
                DelayOld(10),
                MoveUD(0.560808),
                DelayOld(10),
                MoveUD(0.827479),
                DelayOld(30),
                MoveUD(1),
                DelayOld(20),
                MoveLR(-0.976501),
                MoveLR(-0.670614),
                DelayOld(20),
                MoveLR(-0.239235),
                DelayOld(20),
                MoveLR(0.160772),
                DelayOld(20),
                MoveLR(0.443129),
                DelayOld(10),
                MoveLR(0.68627),
                MoveUD(0.976501),
                DelayOld(30),
                MoveLR(0.929411),
                MoveUD(0.73336),
                MoveLR(1),
                MoveUD(0.482376),
                DelayOld(20),
                MoveUD(0.34904),
                DelayOld(10),
                MoveUD(0.160802),
                DelayOld(30),
                MoveUD(-0.0744957),
                DelayOld(10),
                MoveUD(-0.333323),
                DelayOld(20),
                MoveUD(-0.647053),
                DelayOld(20),
                MoveUD(-0.937254),
                DelayOld(10),
                MoveLR(0.858821),
                MoveUD(-1),
                DelayOld(10),
                MoveLR(0.576464),
                DelayOld(30),
                MoveLR(0.184301),
                DelayOld(10),
                MoveLR(-0.121586),
                DelayOld(10),
                MoveLR(-0.474532),
                DelayOld(30),
                MoveLR(-0.670614),
                MoveLR(-0.851009),
                DelayOld(30),
                MoveLR(-1),
                MoveUD(-0.968627),
                DelayOld(20),
                MoveUD(-0.843135),
                DelayOld(10),
                MoveUD(-0.631367),
                DelayOld(20),
                MoveUD(-0.403912),
                MoveUD(-0.176458),
                DelayOld(20),
                MoveUD(0.0902127),
                DelayOld(20),
                MoveUD(0.380413),
                DelayOld(10),
                MoveUD(0.717673),
                DelayOld(30),
                MoveUD(1),
                DelayOld(10),
                MoveLR(-0.741203),
                DelayOld(20),
                MoveLR(-0.458846),
                DelayOld(10),
                MoveLR(-0.145116),
                DelayOld(10),
                MoveLR(0.0980255),
                DelayOld(20),
                MoveLR(0.294107),
                DelayOld(30),
                MoveLR(0.466659),
                MoveLR(0.717643),
                MoveUD(0.796106),
                DelayOld(20),
                MoveLR(0.921567),
                MoveUD(0.443159),
                DelayOld(20),
                MoveLR(1),
                MoveUD(0.145116),
                DelayOld(10),
                MoveUD(-0.0274361),
                DelayOld(30),
                MoveUD(-0.223518),
                MoveUD(-0.427442),
                DelayOld(20),
                MoveUD(-0.874508),
                DelayOld(20),
                MoveUD(-1),
                DelayOld(10),
                MoveLR(0.929411),
                DelayOld(20),
                MoveLR(0.68627),
                DelayOld(20),
                MoveLR(0.364696),
                DelayOld(20),
                MoveLR(0.0431227),
                DelayOld(10),
                MoveLR(-0.333354),
                DelayOld(20),
                MoveLR(-0.639241),
                DelayOld(20),
                MoveLR(-0.968657),
                MoveUD(-0.968627),
                DelayOld(20),
                MoveLR(-1),
                MoveUD(-0.890194),
                MoveUD(-0.866665),
                DelayOld(20),
                MoveUD(-0.749016),
                DelayOld(20),
                MoveUD(-0.529405),
                DelayOld(20),
                MoveUD(-0.30195),
                DelayOld(10),
                MoveUD(-0.00390637),
                DelayOld(10),
                MoveUD(0.262764),
                DelayOld(30),
                MoveLR(-0.600024),
                MoveUD(0.458846),
                DelayOld(10),
                MoveLR(-0.294137),
                MoveUD(0.482376),
                DelayOld(20),
                MoveLR(-0.200018),
                MoveUD(0.505905),
                DelayOld(10),
                MoveLR(-0.145116),
                MoveUD(0.545122),
                DelayOld(20),
                MoveLR(-0.0353099),
                MoveUD(0.584338),
                DelayOld(20),
                MoveLR(0.137242),
                MoveUD(0.592181),
                DelayOld(20),
                MoveLR(0.30195),
                DelayOld(10),
                MoveLR(0.490188),
                DelayOld(10),
                MoveLR(0.599994),
                MoveUD(0.529435),
                DelayOld(30),
                MoveLR(0.66274),
                MoveUD(0.3961),
                DelayOld(20),
                MoveLR(0.670583),
                MoveUD(0.231391),
                MoveLR(0.68627),
                MoveUD(0.0745262),
                Move(0, -0.01),
                DelayOld(100),
                Move(0, 0),
                DelayOld(1000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase05Text')),  # for example when you punch..
                DelayOld(510),
                Move(0, -0.01),
                DelayOld(100),
                Move(0, 0),
                DelayOld(500),
                SpawnSpaz(0, (-0.09249162673950195, 4.337906360626221, -2.3),
                          make_current=True,
                          flash=False),
                SpawnSpaz(1, (-3.1, 4.3, -2.0),
                          make_current=False,
                          color=(1, 1, 0.4),
                          name=ba.Lstr(resource=self._r + '.randomName1Text')),
                Move(-1.0, 0),
                DelayOld(1050),
                Move(0, -0.01),
                DelayOld(100),
                Move(0, 0),
                DelayOld(1000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase06Text')),  # your damage is based
                DelayOld(1200),
                Move(-0.05, 0),
                DelayOld(200),
                Punch(),
                DelayOld(800),
                Punch(),
                DelayOld(800),
                Punch(),
                DelayOld(800),
                Move(0, -0.01),
                DelayOld(100),
                Move(0, 0),
                Text(
                    ba.Lstr(resource=self._r + '.phrase07Text',
                            subs=[('${NAME}',
                                   ba.Lstr(resource=self._r +
                                           '.randomName1Text'))
                                  ])),  # see that didn't hurt fred
                DelayOld(2000),
                Celebrate('right', spaz_num=1),
                DelayOld(1400),
                Text(ba.Lstr(
                    resource=self._r +
                    '.phrase08Text')),  # lets jump and spin to get more speed
                DelayOld(30),
                MoveLR(0),
                DelayOld(40),
                MoveLR(0),
                DelayOld(40),
                MoveLR(0),
                DelayOld(130),
                MoveLR(0),
                DelayOld(100),
                MoveLR(0),
                DelayOld(10),
                MoveLR(0.0480667),
                DelayOld(40),
                MoveLR(0.056093),
                MoveLR(0.0681173),
                DelayOld(30),
                MoveLR(0.0801416),
                DelayOld(10),
                MoveLR(0.184301),
                DelayOld(10),
                MoveLR(0.207831),
                DelayOld(20),
                MoveLR(0.231361),
                DelayOld(30),
                MoveLR(0.239204),
                DelayOld(30),
                MoveLR(0.254891),
                DelayOld(40),
                MoveLR(0.270577),
                DelayOld(10),
                MoveLR(0.30195),
                DelayOld(20),
                MoveLR(0.341166),
                DelayOld(30),
                MoveLR(0.388226),
                MoveLR(0.435286),
                DelayOld(30),
                MoveLR(0.490188),
                DelayOld(10),
                MoveLR(0.560778),
                DelayOld(20),
                MoveLR(0.599994),
                DelayOld(10),
                MoveLR(0.647053),
                DelayOld(10),
                MoveLR(0.68627),
                DelayOld(30),
                MoveLR(0.733329),
                DelayOld(20),
                MoveLR(0.764702),
                DelayOld(10),
                MoveLR(0.827448),
                DelayOld(20),
                MoveLR(0.874508),
                DelayOld(20),
                MoveLR(0.929411),
                DelayOld(10),
                MoveLR(1),
                DelayOld(830),
                MoveUD(0.0274667),
                DelayOld(10),
                MoveLR(0.95294),
                MoveUD(0.113742),
                DelayOld(30),
                MoveLR(0.780389),
                MoveUD(0.184332),
                DelayOld(10),
                MoveLR(0.27842),
                MoveUD(0.0745262),
                DelayOld(20),
                MoveLR(0),
                MoveUD(0),
                DelayOld(390),
                MoveLR(0),
                MoveLR(0),
                DelayOld(20),
                MoveLR(0),
                DelayOld(20),
                MoveLR(0),
                DelayOld(10),
                MoveLR(-0.0537431),
                DelayOld(20),
                MoveLR(-0.215705),
                DelayOld(30),
                MoveLR(-0.388256),
                MoveLR(-0.529435),
                DelayOld(30),
                MoveLR(-0.694143),
                DelayOld(20),
                MoveLR(-0.851009),
                MoveUD(0.0588397),
                DelayOld(10),
                MoveLR(-1),
                MoveUD(0.0745262),
                Run(release=False),
                DelayOld(200),
                MoveUD(0.0509964),
                DelayOld(30),
                MoveUD(0.0117801),
                DelayOld(20),
                MoveUD(-0.0901822),
                MoveUD(-0.372539),
                DelayOld(30),
                MoveLR(-0.898068),
                MoveUD(-0.890194),
                Jump(release=False),
                DelayOld(20),
                MoveLR(-0.647084),
                MoveUD(-1),
                MoveLR(-0.427473),
                DelayOld(20),
                MoveLR(-0.00393689),
                DelayOld(10),
                MoveLR(0.537248),
                DelayOld(30),
                MoveLR(1),
                DelayOld(50),
                RunRelease(),
                JumpRelease(),
                DelayOld(50),
                MoveUD(-0.921567),
                MoveUD(-0.749016),
                DelayOld(30),
                MoveUD(-0.552934),
                DelayOld(10),
                MoveUD(-0.247047),
                DelayOld(20),
                MoveUD(0.200018),
                DelayOld(20),
                MoveUD(0.670614),
                MoveUD(1),
                DelayOld(70),
                MoveLR(0.97647),
                DelayOld(20),
                MoveLR(0.764702),
                DelayOld(20),
                MoveLR(0.364696),
                DelayOld(20),
                MoveLR(0.00390637),
                MoveLR(-0.309824),
                DelayOld(20),
                MoveLR(-0.576495),
                DelayOld(30),
                MoveLR(-0.898068),
                DelayOld(10),
                MoveLR(-1),
                MoveUD(0.905911),
                DelayOld(20),
                MoveUD(0.498062),
                DelayOld(20),
                MoveUD(0.0274667),
                MoveUD(-0.403912),
                DelayOld(20),
                MoveUD(-1),
                Run(release=False),
                Jump(release=False),
                DelayOld(10),
                Punch(release=False),
                DelayOld(70),
                JumpRelease(),
                DelayOld(110),
                MoveLR(-0.976501),
                RunRelease(),
                PunchRelease(),
                DelayOld(10),
                MoveLR(-0.952971),
                DelayOld(20),
                MoveLR(-0.905911),
                MoveLR(-0.827479),
                DelayOld(20),
                MoveLR(-0.75689),
                DelayOld(30),
                MoveLR(-0.73336),
                MoveLR(-0.694143),
                DelayOld(20),
                MoveLR(-0.670614),
                DelayOld(30),
                MoveLR(-0.66277),
                DelayOld(10),
                MoveUD(-0.960784),
                DelayOld(20),
                MoveLR(-0.623554),
                MoveUD(-0.874508),
                DelayOld(10),
                MoveLR(-0.545122),
                MoveUD(-0.694113),
                DelayOld(20),
                MoveLR(-0.505905),
                MoveUD(-0.474502),
                DelayOld(20),
                MoveLR(-0.458846),
                MoveUD(-0.356853),
                MoveLR(-0.364727),
                MoveUD(-0.27842),
                DelayOld(20),
                MoveLR(0.00390637),
                Move(0, 0),
                DelayOld(1000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase09Text')),  # ah that's better
                DelayOld(1900),
                AnalyticsScreen('Tutorial Section 3'),
                Text(ba.Lstr(resource=self._r +
                             '.phrase10Text')),  # running also helps
                DelayOld(100),
                SpawnSpaz(0, (-3.2, 4.3, -4.4), make_current=True,
                          flash=False),
                SpawnSpaz(1, (3.3, 4.2, -5.8),
                          make_current=False,
                          color=(0.9, 0.5, 1.0),
                          name=ba.Lstr(resource=self._r + '.randomName2Text')),
                DelayOld(1800),
                Text(ba.Lstr(resource=self._r +
                             '.phrase11Text')),  # hold ANY button to run
                DelayOld(300),
                MoveUD(0),
                DelayOld(20),
                MoveUD(-0.0520646),
                DelayOld(20),
                MoveLR(0),
                MoveUD(-0.223518),
                Run(release=False),
                Jump(release=False),
                DelayOld(10),
                MoveLR(0.0980255),
                MoveUD(-0.309793),
                DelayOld(30),
                MoveLR(0.160772),
                MoveUD(-0.427442),
                DelayOld(20),
                MoveLR(0.231361),
                MoveUD(-0.545091),
                DelayOld(10),
                MoveLR(0.317637),
                MoveUD(-0.678426),
                DelayOld(20),
                MoveLR(0.396069),
                MoveUD(-0.819605),
                MoveLR(0.482345),
                MoveUD(-0.913724),
                DelayOld(20),
                MoveLR(0.560778),
                MoveUD(-1),
                DelayOld(20),
                MoveLR(0.607837),
                DelayOld(10),
                MoveLR(0.623524),
                DelayOld(30),
                MoveLR(0.647053),
                DelayOld(20),
                MoveLR(0.670583),
                MoveLR(0.694113),
                DelayOld(30),
                MoveLR(0.733329),
                DelayOld(20),
                MoveLR(0.764702),
                MoveLR(0.788232),
                DelayOld(20),
                MoveLR(0.827448),
                DelayOld(10),
                MoveLR(0.858821),
                DelayOld(20),
                MoveLR(0.921567),
                DelayOld(30),
                MoveLR(0.97647),
                MoveLR(1),
                DelayOld(130),
                MoveUD(-0.960784),
                DelayOld(20),
                MoveUD(-0.921567),
                DelayOld(30),
                MoveUD(-0.866665),
                MoveUD(-0.819605),
                DelayOld(30),
                MoveUD(-0.772546),
                MoveUD(-0.725486),
                DelayOld(30),
                MoveUD(-0.631367),
                DelayOld(10),
                MoveUD(-0.552934),
                DelayOld(20),
                MoveUD(-0.474502),
                DelayOld(10),
                MoveUD(-0.403912),
                DelayOld(30),
                MoveUD(-0.356853),
                DelayOld(30),
                MoveUD(-0.34901),
                DelayOld(20),
                MoveUD(-0.333323),
                DelayOld(20),
                MoveUD(-0.32548),
                DelayOld(10),
                MoveUD(-0.30195),
                DelayOld(20),
                MoveUD(-0.27842),
                DelayOld(30),
                MoveUD(-0.254891),
                MoveUD(-0.231361),
                DelayOld(30),
                MoveUD(-0.207831),
                DelayOld(20),
                MoveUD(-0.199988),
                MoveUD(-0.176458),
                DelayOld(30),
                MoveUD(-0.137242),
                MoveUD(-0.0823389),
                DelayOld(20),
                MoveUD(-0.0274361),
                DelayOld(20),
                MoveUD(0.00393689),
                DelayOld(40),
                MoveUD(0.0353099),
                DelayOld(20),
                MoveUD(0.113742),
                DelayOld(10),
                MoveUD(0.137272),
                DelayOld(20),
                MoveUD(0.160802),
                MoveUD(0.184332),
                DelayOld(20),
                MoveUD(0.207862),
                DelayOld(30),
                MoveUD(0.247078),
                MoveUD(0.262764),
                DelayOld(20),
                MoveUD(0.270608),
                DelayOld(30),
                MoveUD(0.294137),
                MoveUD(0.32551),
                DelayOld(30),
                MoveUD(0.37257),
                Celebrate('left', 1),
                DelayOld(20),
                MoveUD(0.498062),
                MoveUD(0.560808),
                DelayOld(30),
                MoveUD(0.654927),
                MoveUD(0.694143),
                DelayOld(30),
                MoveUD(0.741203),
                DelayOld(20),
                MoveUD(0.780419),
                MoveUD(0.819636),
                DelayOld(20),
                MoveUD(0.843165),
                DelayOld(20),
                MoveUD(0.882382),
                DelayOld(10),
                MoveUD(0.913755),
                DelayOld(30),
                MoveUD(0.968657),
                MoveUD(1),
                DelayOld(560),
                Punch(release=False),
                DelayOld(210),
                MoveUD(0.968657),
                DelayOld(30),
                MoveUD(0.75689),
                PunchRelease(),
                DelayOld(20),
                MoveLR(0.95294),
                MoveUD(0.435316),
                RunRelease(),
                JumpRelease(),
                MoveLR(0.811762),
                MoveUD(0.270608),
                DelayOld(20),
                MoveLR(0.670583),
                MoveUD(0.160802),
                DelayOld(20),
                MoveLR(0.466659),
                MoveUD(0.0588397),
                DelayOld(10),
                MoveLR(0.317637),
                MoveUD(-0.00390637),
                DelayOld(20),
                MoveLR(0.0801416),
                DelayOld(10),
                MoveLR(0),
                DelayOld(20),
                MoveLR(0),
                DelayOld(30),
                MoveLR(0),
                DelayOld(30),
                MoveLR(0),
                DelayOld(20),
                MoveLR(0),
                DelayOld(100),
                MoveLR(0),
                DelayOld(30),
                MoveUD(0),
                DelayOld(30),
                MoveUD(0),
                DelayOld(50),
                MoveUD(0),
                MoveUD(0),
                DelayOld(30),
                MoveLR(0),
                MoveUD(-0.0520646),
                MoveLR(0),
                MoveUD(-0.0640889),
                DelayOld(20),
                MoveLR(0),
                MoveUD(-0.0881375),
                DelayOld(30),
                MoveLR(-0.0498978),
                MoveUD(-0.199988),
                MoveLR(-0.121586),
                MoveUD(-0.207831),
                DelayOld(20),
                MoveLR(-0.145116),
                MoveUD(-0.223518),
                DelayOld(30),
                MoveLR(-0.152959),
                MoveUD(-0.231361),
                MoveLR(-0.192175),
                MoveUD(-0.262734),
                DelayOld(30),
                MoveLR(-0.200018),
                MoveUD(-0.27842),
                DelayOld(20),
                MoveLR(-0.239235),
                MoveUD(-0.30195),
                MoveUD(-0.309793),
                DelayOld(40),
                MoveUD(-0.333323),
                DelayOld(10),
                MoveUD(-0.34901),
                DelayOld(30),
                MoveUD(-0.372539),
                MoveUD(-0.396069),
                DelayOld(20),
                MoveUD(-0.443129),
                DelayOld(20),
                MoveUD(-0.458815),
                DelayOld(10),
                MoveUD(-0.474502),
                DelayOld(50),
                MoveUD(-0.482345),
                DelayOld(30),
                MoveLR(-0.215705),
                DelayOld(30),
                MoveLR(-0.200018),
                DelayOld(10),
                MoveLR(-0.192175),
                DelayOld(10),
                MoveLR(-0.176489),
                DelayOld(30),
                MoveLR(-0.152959),
                DelayOld(20),
                MoveLR(-0.145116),
                MoveLR(-0.121586),
                MoveUD(-0.458815),
                DelayOld(30),
                MoveLR(-0.098056),
                MoveUD(-0.419599),
                DelayOld(10),
                MoveLR(-0.0745262),
                MoveUD(-0.333323),
                DelayOld(10),
                MoveLR(0.00390637),
                MoveUD(0),
                DelayOld(990),
                MoveLR(0),
                DelayOld(660),
                MoveUD(0),
                AnalyticsScreen('Tutorial Section 4'),
                Text(
                    ba.Lstr(resource=self._r +
                            '.phrase12Text')),  # for extra-awesome punches,...
                DelayOld(200),
                SpawnSpaz(
                    0,
                    (2.368781805038452, 4.337533950805664, -4.360159873962402),
                    make_current=True,
                    flash=False),
                SpawnSpaz(
                    1,
                    (-3.2, 4.3, -4.5),
                    make_current=False,
                    color=(1.0, 0.7, 0.3),
                    # name=R.randomName3Text),
                    name=ba.Lstr(resource=self._r + '.randomName3Text')),
                DelayOld(100),
                Powerup(1, (2.5, 0.0, 0), relative_to=0),
                Move(1, 0),
                DelayOld(1700),
                Move(0, -0.1),
                DelayOld(100),
                Move(0, 0),
                DelayOld(500),
                DelayOld(320),
                MoveLR(0),
                DelayOld(20),
                MoveLR(0),
                DelayOld(10),
                MoveLR(0),
                DelayOld(20),
                MoveLR(-0.333354),
                MoveLR(-0.592181),
                DelayOld(20),
                MoveLR(-0.788263),
                DelayOld(20),
                MoveLR(-1),
                MoveUD(0.0353099),
                MoveUD(0.0588397),
                DelayOld(10),
                Run(release=False),
                DelayOld(780),
                MoveUD(0.0274667),
                MoveUD(0.00393689),
                DelayOld(10),
                MoveUD(-0.00390637),
                DelayOld(440),
                MoveUD(0.0353099),
                DelayOld(20),
                MoveUD(0.0588397),
                DelayOld(10),
                MoveUD(0.0902127),
                DelayOld(260),
                MoveUD(0.0353099),
                DelayOld(30),
                MoveUD(0.00393689),
                DelayOld(10),
                MoveUD(-0.00390637),
                MoveUD(-0.0274361),
                Celebrate('left', 1),
                DelayOld(10),
                MoveUD(-0.0823389),
                DelayOld(30),
                MoveUD(-0.176458),
                MoveUD(-0.286264),
                DelayOld(20),
                MoveUD(-0.498032),
                Jump(release=False),
                MoveUD(-0.764702),
                DelayOld(30),
                MoveLR(-0.858852),
                MoveUD(-1),
                MoveLR(-0.780419),
                DelayOld(20),
                MoveLR(-0.717673),
                DelayOld(10),
                MoveLR(-0.552965),
                DelayOld(10),
                MoveLR(-0.341197),
                DelayOld(10),
                MoveLR(-0.0274667),
                DelayOld(10),
                MoveLR(0.27842),
                DelayOld(20),
                MoveLR(0.811762),
                MoveLR(1),
                RunRelease(),
                JumpRelease(),
                DelayOld(260),
                MoveLR(0.95294),
                DelayOld(30),
                MoveLR(0.756859),
                DelayOld(10),
                MoveLR(0.317637),
                MoveLR(-0.00393689),
                DelayOld(10),
                MoveLR(-0.341197),
                DelayOld(10),
                MoveLR(-0.647084),
                MoveUD(-0.921567),
                DelayOld(10),
                MoveLR(-1),
                MoveUD(-0.599994),
                MoveUD(-0.474502),
                DelayOld(10),
                MoveUD(-0.309793),
                DelayOld(10),
                MoveUD(-0.160772),
                MoveUD(-0.0352794),
                Delay(10),
                MoveUD(0.176489),
                Delay(10),
                MoveUD(0.607868),
                Run(release=False),
                Jump(release=False),
                DelayOld(20),
                MoveUD(1),
                DelayOld(30),
                MoveLR(-0.921598),
                DelayOld(10),
                Punch(release=False),
                MoveLR(-0.639241),
                DelayOld(10),
                MoveLR(-0.223548),
                DelayOld(10),
                MoveLR(0.254891),
                DelayOld(10),
                MoveLR(0.741172),
                MoveLR(1),
                DelayOld(40),
                JumpRelease(),
                DelayOld(40),
                MoveUD(0.976501),
                DelayOld(10),
                MoveUD(0.73336),
                DelayOld(10),
                MoveUD(0.309824),
                DelayOld(20),
                MoveUD(-0.184301),
                DelayOld(20),
                MoveUD(-0.811762),
                MoveUD(-1),
                KillSpaz(1, explode=True),
                DelayOld(10),
                RunRelease(),
                PunchRelease(),
                DelayOld(110),
                MoveLR(0.97647),
                MoveLR(0.898038),
                DelayOld(20),
                MoveLR(0.788232),
                DelayOld(20),
                MoveLR(0.670583),
                DelayOld(10),
                MoveLR(0.505875),
                DelayOld(10),
                MoveLR(0.32548),
                DelayOld(20),
                MoveLR(0.137242),
                DelayOld(10),
                MoveLR(-0.00393689),
                DelayOld(10),
                MoveLR(-0.215705),
                MoveLR(-0.356883),
                DelayOld(20),
                MoveLR(-0.451003),
                DelayOld(10),
                MoveLR(-0.552965),
                DelayOld(20),
                MoveLR(-0.670614),
                MoveLR(-0.780419),
                DelayOld(10),
                MoveLR(-0.898068),
                DelayOld(20),
                MoveLR(-1),
                DelayOld(370),
                MoveLR(-0.976501),
                DelayOld(10),
                MoveLR(-0.952971),
                DelayOld(10),
                MoveLR(-0.929441),
                MoveLR(-0.898068),
                DelayOld(30),
                MoveLR(-0.874538),
                DelayOld(10),
                MoveLR(-0.851009),
                DelayOld(10),
                MoveLR(-0.835322),
                MoveUD(-0.968627),
                DelayOld(10),
                MoveLR(-0.827479),
                MoveUD(-0.960784),
                DelayOld(20),
                MoveUD(-0.945097),
                DelayOld(70),
                MoveUD(-0.937254),
                DelayOld(20),
                MoveUD(-0.913724),
                DelayOld(20),
                MoveUD(-0.890194),
                MoveLR(-0.780419),
                MoveUD(-0.827448),
                DelayOld(20),
                MoveLR(0.317637),
                MoveUD(0.3961),
                MoveLR(0.0195929),
                MoveUD(0.056093),
                DelayOld(20),
                MoveUD(0),
                DelayOld(750),
                MoveLR(0),
                Text(
                    ba.Lstr(resource=self._r + '.phrase13Text',
                            subs=[('${NAME}',
                                   ba.Lstr(resource=self._r +
                                           '.randomName3Text'))
                                  ])),  # whoops sorry bill
                RemoveGloves(),
                DelayOld(2000),
                AnalyticsScreen('Tutorial Section 5'),
                Text(
                    ba.Lstr(resource=self._r + '.phrase14Text',
                            subs=[('${NAME}',
                                   ba.Lstr(resource=self._r +
                                           '.randomName4Text'))])
                ),  # you can pick up and throw things such as chuck here
                SpawnSpaz(0, (-4.0, 4.3, -2.5),
                          make_current=True,
                          flash=False,
                          angle=90),
                SpawnSpaz(1, (5, 0, -1.0),
                          relative_to=0,
                          make_current=False,
                          color=(0.4, 1.0, 0.7),
                          name=ba.Lstr(resource=self._r + '.randomName4Text')),
                DelayOld(1000),
                Celebrate('left', 1, duration=1000),
                Move(1, 0.2),
                DelayOld(2000),
                PickUp(),
                DelayOld(200),
                Move(0.5, 1.0),
                DelayOld(1200),
                PickUp(),
                Move(0, 0),
                DelayOld(1000),
                Celebrate('left'),
                DelayOld(1500),
                Move(0, -1.0),
                DelayOld(800),
                Move(0, 0),
                DelayOld(800),
                SpawnSpaz(0, (1.5, 4.3, -4.0),
                          make_current=True,
                          flash=False,
                          angle=0),
                AnalyticsScreen('Tutorial Section 6'),
                Text(ba.Lstr(resource=self._r +
                             '.phrase15Text')),  # lastly there's bombs
                DelayOld(1900),
                Text(
                    ba.Lstr(resource=self._r +
                            '.phrase16Text')),  # throwing bombs takes practice
                DelayOld(2000),
                Bomb(),
                Move(-0.1, -0.1),
                DelayOld(100),
                Move(0, 0),
                DelayOld(500),
                DelayOld(1000),
                Bomb(),
                DelayOld(2000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase17Text')),  # not a very good throw
                DelayOld(3000),
                Text(
                    ba.Lstr(resource=self._r +
                            '.phrase18Text')),  # moving helps you get distance
                DelayOld(1000),
                Bomb(),
                DelayOld(500),
                Move(-0.3, 0),
                DelayOld(100),
                Move(-0.6, 0),
                DelayOld(100),
                Move(-1, 0),
                DelayOld(800),
                Bomb(),
                DelayOld(400),
                Move(0, -0.1),
                DelayOld(100),
                Move(0, 0),
                DelayOld(2500),
                Text(ba.Lstr(resource=self._r +
                             '.phrase19Text')),  # jumping helps you get height
                DelayOld(2000),
                Bomb(),
                DelayOld(500),
                Move(1, 0),
                DelayOld(300),
                Jump(release_delay=250),
                DelayOld(500),
                Jump(release_delay=250),
                DelayOld(550),
                Jump(release_delay=250),
                DelayOld(160),
                Punch(),
                DelayOld(500),
                Move(0, -0.1),
                DelayOld(100),
                Move(0, 0),
                DelayOld(2000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase20Text')),  # whiplash your bombs
                DelayOld(1000),
                Bomb(release=False),
                DelayOld2(80),
                RunRelease(),
                BombRelease(),
                DelayOld2(620),
                MoveLR(0),
                DelayOld2(10),
                MoveLR(0),
                DelayOld2(40),
                MoveLR(0),
                DelayOld2(10),
                MoveLR(-0.0537431),
                MoveUD(0),
                DelayOld2(20),
                MoveLR(-0.262764),
                DelayOld2(20),
                MoveLR(-0.498062),
                DelayOld2(10),
                MoveLR(-0.639241),
                DelayOld2(20),
                MoveLR(-0.73336),
                DelayOld2(10),
                MoveLR(-0.843165),
                MoveUD(-0.0352794),
                DelayOld2(30),
                MoveLR(-1),
                DelayOld2(10),
                MoveUD(-0.0588092),
                DelayOld2(10),
                MoveUD(-0.160772),
                DelayOld2(20),
                MoveUD(-0.286264),
                DelayOld2(20),
                MoveUD(-0.427442),
                DelayOld2(10),
                MoveUD(-0.623524),
                DelayOld2(20),
                MoveUD(-0.843135),
                DelayOld2(10),
                MoveUD(-1),
                DelayOld2(40),
                MoveLR(-0.890225),
                DelayOld2(10),
                MoveLR(-0.670614),
                DelayOld2(20),
                MoveLR(-0.435316),
                DelayOld2(20),
                MoveLR(-0.184332),
                DelayOld2(10),
                MoveLR(0.00390637),
                DelayOld2(20),
                MoveLR(0.223518),
                DelayOld2(10),
                MoveLR(0.388226),
                DelayOld2(20),
                MoveLR(0.560778),
                DelayOld2(20),
                MoveLR(0.717643),
                DelayOld2(10),
                MoveLR(0.890194),
                DelayOld2(20),
                MoveLR(1),
                DelayOld2(30),
                MoveUD(-0.968627),
                DelayOld2(20),
                MoveUD(-0.898038),
                DelayOld2(10),
                MoveUD(-0.741172),
                DelayOld2(20),
                MoveUD(-0.498032),
                DelayOld2(20),
                MoveUD(-0.247047),
                DelayOld2(10),
                MoveUD(0.00393689),
                DelayOld2(20),
                MoveUD(0.239235),
                DelayOld2(20),
                MoveUD(0.458846),
                DelayOld2(10),
                MoveUD(0.70983),
                DelayOld2(30),
                MoveUD(1),
                DelayOld2(10),
                MoveLR(0.827448),
                DelayOld2(10),
                MoveLR(0.678426),
                DelayOld2(20),
                MoveLR(0.396069),
                DelayOld2(10),
                MoveLR(0.0980255),
                DelayOld2(20),
                MoveLR(-0.160802),
                DelayOld2(20),
                MoveLR(-0.388256),
                DelayOld2(10),
                MoveLR(-0.545122),
                DelayOld2(30),
                MoveLR(-0.73336),
                DelayOld2(10),
                MoveLR(-0.945128),
                DelayOld2(10),
                MoveLR(-1),
                DelayOld2(50),
                MoveUD(0.960814),
                DelayOld2(20),
                MoveUD(0.890225),
                DelayOld2(10),
                MoveUD(0.749046),
                DelayOld2(20),
                MoveUD(0.623554),
                DelayOld2(20),
                MoveUD(0.498062),
                DelayOld2(10),
                MoveUD(0.34904),
                DelayOld2(20),
                MoveUD(0.239235),
                DelayOld2(20),
                MoveUD(0.137272),
                DelayOld2(10),
                MoveUD(0.0117801),
                DelayOld2(20),
                MoveUD(-0.0117496),
                DelayOld2(10),
                MoveUD(-0.0274361),
                DelayOld2(90),
                MoveUD(-0.0352794),
                Run(release=False),
                Jump(release=False),
                Delay(80),
                Punch(release=False),
                DelayOld2(60),
                MoveLR(-0.968657),
                DelayOld2(20),
                MoveLR(-0.835322),
                DelayOld2(10),
                MoveLR(-0.70983),
                JumpRelease(),
                DelayOld2(30),
                MoveLR(-0.592181),
                MoveUD(-0.0588092),
                DelayOld2(10),
                MoveLR(-0.490219),
                MoveUD(-0.0744957),
                DelayOld2(10),
                MoveLR(-0.41963),
                DelayOld2(20),
                MoveLR(0),
                MoveUD(0),
                DelayOld2(20),
                MoveUD(0),
                PunchRelease(),
                RunRelease(),
                DelayOld(500),
                Move(0, -0.1),
                DelayOld(100),
                Move(0, 0),
                DelayOld(2000),
                AnalyticsScreen('Tutorial Section 7'),
                Text(ba.Lstr(
                    resource=self._r +
                    '.phrase21Text')),  # timing your bombs can be tricky
                Move(-1, 0),
                DelayOld(1000),
                Move(0, -0.1),
                DelayOld(100),
                Move(0, 0),
                SpawnSpaz(0, (-0.7, 4.3, -3.9),
                          make_current=True,
                          flash=False,
                          angle=-30),
                SpawnSpaz(1, (6.5, 0, -0.75),
                          relative_to=0,
                          make_current=False,
                          color=(0.3, 0.8, 1.0),
                          name=ba.Lstr(resource=self._r + '.randomName5Text')),
                DelayOld2(1000),
                Move(-1, 0),
                DelayOld2(1800),
                Bomb(),
                Move(0, 0),
                DelayOld2(300),
                Move(1, 0),
                DelayOld2(600),
                Jump(),
                DelayOld2(150),
                Punch(),
                DelayOld2(800),
                Move(-1, 0),
                DelayOld2(1000),
                Move(0, 0),
                DelayOld2(1500),
                Text(ba.Lstr(resource=self._r + '.phrase22Text')),  # dang
                Delay(1500),
                Text(''),
                Delay(200),
                Text(ba.Lstr(resource=self._r +
                             '.phrase23Text')),  # try cooking off
                Delay(1500),
                Bomb(),
                Delay(800),
                Move(1, 0.12),
                Delay(1100),
                Jump(),
                Delay(100),
                Punch(),
                Delay(100),
                Move(0, -0.1),
                Delay(100),
                Move(0, 0),
                Delay(2000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase24Text')),  # hooray nicely cooked
                Celebrate(),
                DelayOld(2000),
                KillSpaz(1),
                Text(''),
                Move(0.5, -0.5),
                DelayOld(1000),
                Move(0, -0.1),
                DelayOld(100),
                Move(0, 0),
                DelayOld(1000),
                AnalyticsScreen('Tutorial Section 8'),
                Text(ba.Lstr(resource=self._r +
                             '.phrase25Text')),  # well that's just about it
                DelayOld(2000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase26Text')),  # go get em tiger
                DelayOld(2000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase27Text')),  # remember you training
                DelayOld(3000),
                Text(ba.Lstr(resource=self._r +
                             '.phrase28Text')),  # well maybe
                DelayOld(1600),
                Text(ba.Lstr(resource=self._r + '.phrase29Text')),  # good luck
                Celebrate('right', duration=10000),
                DelayOld(1000),
                AnalyticsScreen('Tutorial Complete'),
                End(),
            ]

        except Exception:
            ba.print_exception()

        # If we read some, exec them.
        if self._entries:
            self._run_next_entry()
        # Otherwise try again in a few seconds.
        else:
            self._read_entries_timer = ba.Timer(
                3.0, ba.WeakCall(self._read_entries))

    def _run_next_entry(self) -> None:

        while self._entries:
            entry = self._entries.pop(0)
            try:
                result = entry.run(self)
            except Exception:
                result = None
                ba.print_exception()

            # If the entry returns an int value, set a timer;
            # otherwise just keep going.
            if result is not None:
                self._entry_timer = ba.Timer(
                    result,
                    ba.WeakCall(self._run_next_entry),
                    timeformat=ba.TimeFormat.MILLISECONDS)
                return

        # Done with these entries.. start over soon.
        self._read_entries_timer = ba.Timer(1.0,
                                            ba.WeakCall(self._read_entries))

    def _update_skip_votes(self) -> None:
        count = sum(1 for player in self.players if player.pressed)
        assert self._skip_count_text
        self._skip_count_text.text = ba.Lstr(
            resource=self._r + '.skipVoteCountText',
            subs=[('${COUNT}', str(count)),
                  ('${TOTAL}', str(len(self.players)))]) if count > 0 else ''
        if (count >= len(self.players) and self.players
                and not self._have_skipped):
            _ba.increment_analytics_count('Tutorial skip')
            ba.set_analytics_screen('Tutorial Skip')
            self._have_skipped = True
            ba.playsound(ba.getsound('swish'))
            # self._skip_count_text.text = self._r.skippingText
            self._skip_count_text.text = ba.Lstr(resource=self._r +
                                                 '.skippingText')
            assert self._skip_text
            self._skip_text.text = ''
            self.end()

    def _player_pressed_button(self, player: Player) -> None:

        # Special case: if there's only one player, we give them a
        # warning on their first press (some players were thinking the
        # on-screen guide meant they were supposed to press something).
        if len(self.players) == 1 and not self._issued_warning:
            self._issued_warning = True
            assert self._skip_text
            self._skip_text.text = ba.Lstr(resource=self._r +
                                           '.skipConfirmText')
            self._skip_text.color = (1, 1, 1)
            self._skip_text.scale = 1.3
            incr = 50
            t = incr
            for _i in range(6):
                ba.timer(t,
                         ba.Call(setattr, self._skip_text, 'color',
                                 (1, 0.5, 0.1)),
                         timeformat=ba.TimeFormat.MILLISECONDS)
                t += incr
                ba.timer(t,
                         ba.Call(setattr, self._skip_text, 'color', (1, 1, 0)),
                         timeformat=ba.TimeFormat.MILLISECONDS)
                t += incr
            ba.timer(6.0, ba.WeakCall(self._revert_confirm))
            return

        player.pressed = True

        # test...
        if not all(self.players):
            ba.print_error('Nonexistent player in _player_pressed_button: ' +
                           str([str(p) for p in self.players]) + ': we are ' +
                           str(player))

        self._update_skip_votes()

    def _revert_confirm(self) -> None:
        assert self._skip_text
        self._skip_text.text = ba.Lstr(resource=self._r +
                                       '.toSkipPressAnythingText')
        self._skip_text.color = (1, 1, 1)
        self._issued_warning = False

    def on_player_join(self, player: Player) -> None:
        super().on_player_join(player)

        # We just wanna know if this player presses anything.
        player.assigninput(
            (ba.InputType.JUMP_PRESS, ba.InputType.PUNCH_PRESS,
             ba.InputType.BOMB_PRESS, ba.InputType.PICK_UP_PRESS),
            ba.Call(self._player_pressed_button, player))

    def on_player_leave(self, player: Player) -> None:
        if not all(self.players):
            ba.print_error('Nonexistent player in on_player_leave: ' +
                           str([str(p) for p in self.players]) + ': we are ' +
                           str(player))
        super().on_player_leave(player)
        # our leaving may influence the vote total needed/etc
        self._update_skip_votes()
