# Released under the MIT License. See LICENSE for details.
#
"""Implements a flag used for marking bases, capture-the-flag games, etc."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import bascenev1 as bs

from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


class FlagFactory:
    """Wraps up media and other resources used by `Flag`s.

    Category: **Gameplay Classes**

    A single instance of this is shared between all flags
    and can be retrieved via FlagFactory.get().
    """

    flagmaterial: bs.Material
    """The bs.Material applied to all `Flag`s."""

    impact_sound: bs.Sound
    """The bs.Sound used when a `Flag` hits the ground."""

    skid_sound: bs.Sound
    """The bs.Sound used when a `Flag` skids along the ground."""

    no_hit_material: bs.Material
    """A bs.Material that prevents contact with most objects;
       applied to 'non-touchable' flags."""

    flag_texture: bs.Texture
    """The bs.Texture for flags."""

    _STORENAME = bs.storagename()

    def __init__(self) -> None:
        """Instantiate a `FlagFactory`.

        You shouldn't need to do this; call FlagFactory.get() to
        get a shared instance.
        """
        shared = SharedObjects.get()
        self.flagmaterial = bs.Material()
        self.flagmaterial.add_actions(
            conditions=(
                ('we_are_younger_than', 100),
                'and',
                ('they_have_material', shared.object_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )

        self.flagmaterial.add_actions(
            conditions=(
                'they_have_material',
                shared.footing_material,
            ),
            actions=(
                ('message', 'our_node', 'at_connect', 'footing', 1),
                ('message', 'our_node', 'at_disconnect', 'footing', -1),
            ),
        )

        self.impact_sound = bs.getsound('metalHit')
        self.skid_sound = bs.getsound('metalSkid')
        self.flagmaterial.add_actions(
            conditions=(
                'they_have_material',
                shared.footing_material,
            ),
            actions=(
                ('impact_sound', self.impact_sound, 2, 5),
                ('skid_sound', self.skid_sound, 2, 5),
            ),
        )

        self.no_hit_material = bs.Material()
        self.no_hit_material.add_actions(
            conditions=(
                ('they_have_material', shared.pickup_material),
                'or',
                ('they_have_material', shared.attack_material),
            ),
            actions=('modify_part_collision', 'collide', False),
        )

        # We also don't want anything moving it.
        self.no_hit_material.add_actions(
            conditions=(
                ('they_have_material', shared.object_material),
                'or',
                ('they_dont_have_material', shared.footing_material),
            ),
            actions=(
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', False),
            ),
        )

        self.flag_texture = bs.gettexture('flagColor')

    @classmethod
    def get(cls) -> FlagFactory:
        """Get/create a shared `FlagFactory` instance."""
        activity = bs.getactivity()
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = FlagFactory()
            activity.customdata[cls._STORENAME] = factory
        assert isinstance(factory, FlagFactory)
        return factory


@dataclass
class FlagPickedUpMessage:
    """A message saying a `Flag` has been picked up.

    Category: **Message Classes**
    """

    flag: Flag
    """The `Flag` that has been picked up."""

    node: bs.Node
    """The bs.Node doing the picking up."""


@dataclass
class FlagDiedMessage:
    """A message saying a `Flag` has died.

    Category: **Message Classes**
    """

    flag: Flag
    """The `Flag` that died."""

    self_kill: bool = False
    """If the `Flag` killed itself or not."""


@dataclass
class FlagDroppedMessage:
    """A message saying a `Flag` has been dropped.

    Category: **Message Classes**
    """

    flag: Flag
    """The `Flag` that was dropped."""

    node: bs.Node
    """The bs.Node that was holding it."""


class Flag(bs.Actor):
    """A flag; used in games such as capture-the-flag or king-of-the-hill.

    Category: **Gameplay Classes**

    Can be stationary or carry-able by players.
    """

    def __init__(
        self,
        *,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        color: Sequence[float] = (1.0, 1.0, 1.0),
        materials: Sequence[bs.Material] | None = None,
        touchable: bool = True,
        dropped_timeout: int | None = None,
    ):
        """Instantiate a flag.

        If 'touchable' is False, the flag will only touch terrain;
        useful for things like king-of-the-hill where players should
        not be moving the flag around.

        'materials can be a list of extra `bs.Material`s to apply to the flag.

        If 'dropped_timeout' is provided (in seconds), the flag will die
        after remaining untouched for that long once it has been moved
        from its initial position.
        """

        super().__init__()

        self._initial_position: Sequence[float] | None = None
        self._has_moved = False
        shared = SharedObjects.get()
        factory = FlagFactory.get()

        if materials is None:
            materials = []
        elif not isinstance(materials, list):
            # In case they passed a tuple or whatnot.
            materials = list(materials)
        if not touchable:
            materials = [factory.no_hit_material] + materials

        finalmaterials = [
            shared.object_material,
            factory.flagmaterial,
        ] + materials
        self.node = bs.newnode(
            'flag',
            attrs={
                'position': (position[0], position[1] + 0.75, position[2]),
                'color_texture': factory.flag_texture,
                'color': color,
                'materials': finalmaterials,
            },
            delegate=self,
        )

        if dropped_timeout is not None:
            dropped_timeout = int(dropped_timeout)
        self._dropped_timeout = dropped_timeout
        self._counter: bs.Node | None
        if self._dropped_timeout is not None:
            self._count = self._dropped_timeout
            self._tick_timer = bs.Timer(
                1.0, call=bs.WeakCall(self._tick), repeat=True
            )
            self._counter = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'in_world': True,
                    'color': (1, 1, 1, 0.7),
                    'scale': 0.015,
                    'shadow': 0.5,
                    'flatness': 1.0,
                    'h_align': 'center',
                },
            )
        else:
            self._counter = None

        self._held_count = 0
        self._score_text: bs.Node | None = None
        self._score_text_hide_timer: bs.Timer | None = None

    def _tick(self) -> None:
        if self.node:
            # Grab our initial position after one tick (in case we fall).
            if self._initial_position is None:
                self._initial_position = self.node.position

                # Keep track of when we first move; we don't count down
                # until then.
            if not self._has_moved:
                nodepos = self.node.position
                if (
                    max(
                        abs(nodepos[i] - self._initial_position[i])
                        for i in list(range(3))
                    )
                    > 1.0
                ):
                    self._has_moved = True

            if self._held_count > 0 or not self._has_moved:
                assert self._dropped_timeout is not None
                assert self._counter
                self._count = self._dropped_timeout
                self._counter.text = ''
            else:
                self._count -= 1
                if self._count <= 10:
                    nodepos = self.node.position
                    assert self._counter
                    self._counter.position = (
                        nodepos[0],
                        nodepos[1] + 1.3,
                        nodepos[2],
                    )
                    self._counter.text = str(self._count)
                    if self._count < 1:
                        self.handlemessage(
                            bs.DieMessage(how=bs.DeathType.LEFT_GAME)
                        )
                else:
                    assert self._counter
                    self._counter.text = ''

    def _hide_score_text(self) -> None:
        assert self._score_text is not None
        assert isinstance(self._score_text.scale, float)
        bs.animate(
            self._score_text, 'scale', {0: self._score_text.scale, 0.2: 0}
        )

    def set_score_text(self, text: str) -> None:
        """Show a message over the flag; handy for scores."""
        if not self.node:
            return
        if not self._score_text:
            start_scale = 0.0
            math = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (0, 1.4, 0), 'operation': 'add'},
            )
            self.node.connectattr('position', math, 'input2')
            self._score_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': text,
                    'in_world': True,
                    'scale': 0.02,
                    'shadow': 0.5,
                    'flatness': 1.0,
                    'h_align': 'center',
                },
            )
            math.connectattr('output', self._score_text, 'position')
        else:
            assert isinstance(self._score_text.scale, float)
            start_scale = self._score_text.scale
            self._score_text.text = text
        self._score_text.color = bs.safecolor(self.node.color)
        bs.animate(self._score_text, 'scale', {0: start_scale, 0.2: 0.02})
        self._score_text_hide_timer = bs.Timer(
            1.0, bs.WeakCall(self._hide_score_text)
        )

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
                if not msg.immediate:
                    self.activity.handlemessage(
                        FlagDiedMessage(
                            self, (msg.how is bs.DeathType.LEFT_GAME)
                        )
                    )
        elif isinstance(msg, bs.HitMessage):
            assert self.node
            assert msg.force_direction is not None
            self.node.handlemessage(
                'impulse',
                msg.pos[0],
                msg.pos[1],
                msg.pos[2],
                msg.velocity[0],
                msg.velocity[1],
                msg.velocity[2],
                msg.magnitude,
                msg.velocity_magnitude,
                msg.radius,
                0,
                msg.force_direction[0],
                msg.force_direction[1],
                msg.force_direction[2],
            )
        elif isinstance(msg, bs.PickedUpMessage):
            self._held_count += 1
            if self._held_count == 1 and self._counter is not None:
                self._counter.text = ''
            self.activity.handlemessage(FlagPickedUpMessage(self, msg.node))
        elif isinstance(msg, bs.DroppedMessage):
            self._held_count -= 1
            if self._held_count < 0:
                print('Flag held count < 0.')
                self._held_count = 0
            self.activity.handlemessage(FlagDroppedMessage(self, msg.node))
        else:
            super().handlemessage(msg)

    @staticmethod
    def project_stand(pos: Sequence[float]) -> None:
        """Project a flag-stand onto the ground at the given position.

        Useful for games such as capture-the-flag to show where a
        movable flag originated from.
        """
        assert len(pos) == 3
        bs.emitfx(position=pos, emit_type='flag_stand')
