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
"""Various utilities useful for gameplay."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Sequence, Optional


class SharedObjects:
    """Various common components for use in games.

    Category: Gameplay Classes

    Objects contained here are created on-demand as accessed and shared
    by everything in the current activity. This includes things such as
    standard materials.
    """

    _STORENAME = ba.storagename()

    def __init__(self) -> None:
        activity = ba.getactivity()
        if hasattr(activity, self._STORENAME):
            raise RuntimeError('Use SharedObjects.get() to fetch the'
                               ' shared instance for this activity.')
        self._object_material: Optional[ba.Material] = None
        self._player_material: Optional[ba.Material] = None
        self._pickup_material: Optional[ba.Material] = None
        self._footing_material: Optional[ba.Material] = None
        self._attack_material: Optional[ba.Material] = None
        self._death_material: Optional[ba.Material] = None
        self._region_material: Optional[ba.Material] = None
        self._railing_material: Optional[ba.Material] = None

    @classmethod
    def get(cls) -> SharedObjects:
        """Fetch/create the instance of this class for the current activity."""
        activity = ba.getactivity()
        shobs = activity.customdata.get(cls._STORENAME)
        if shobs is None:
            shobs = SharedObjects()
            activity.customdata[cls._STORENAME] = shobs
        assert isinstance(shobs, SharedObjects)
        return shobs

    @property
    def player_material(self) -> ba.Material:
        """a ba.Material to be applied to player parts. Generally,
        materials related to the process of scoring when reaching a goal, etc
        will look for the presence of this material on things that hit them.
        """
        if self._player_material is None:
            self._player_material = ba.Material()
        return self._player_material

    @property
    def object_material(self) -> ba.Material:
        """A ba.Material that should be applied to any small,
        normal, physical objects such as bombs, boxes, players, etc. Other
        materials often check for the  presence of this material as a
        prerequisite for performing certain actions (such as disabling
        collisions between initially-overlapping objects)
        """
        if self._object_material is None:
            self._object_material = ba.Material()
        return self._object_material

    @property
    def pickup_material(self) -> ba.Material:
        """A ba.Material; collision shapes used for picking things
        up will have this material applied. To prevent an object from being
        picked up, you can add a material that disables collisions against
        things containing this material.
        """
        if self._pickup_material is None:
            self._pickup_material = ba.Material()
        return self._pickup_material

    @property
    def footing_material(self) -> ba.Material:
        """Anything that can be 'walked on' should have this
        ba.Material applied; generally just terrain and whatnot. A character
        will snap upright whenever touching something with this material so it
        should not be applied to props, etc.
        """
        if self._footing_material is None:
            self._footing_material = ba.Material()
        return self._footing_material

    @property
    def attack_material(self) -> ba.Material:
        """A ba.Material applied to explosion shapes, punch
        shapes, etc.  An object not wanting to receive impulse/etc messages can
        disable collisions against this material.
        """
        if self._attack_material is None:
            self._attack_material = ba.Material()
        return self._attack_material

    @property
    def death_material(self) -> ba.Material:
        """A ba.Material that sends a ba.DieMessage() to anything
        that touches it; handy for terrain below a cliff, etc.
        """
        if self._death_material is None:
            mat = self._death_material = ba.Material()
            mat.add_actions(
                ('message', 'their_node', 'at_connect', ba.DieMessage()))
        return self._death_material

    @property
    def region_material(self) -> ba.Material:
        """A ba.Material used for non-physical collision shapes
        (regions); collisions can generally be allowed with this material even
        when initially overlapping since it is not physical.
        """
        if self._region_material is None:
            self._region_material = ba.Material()
        return self._region_material

    @property
    def railing_material(self) -> ba.Material:
        """A ba.Material with a very low friction/stiffness/etc
        that can be applied to invisible 'railings' useful for gently keeping
        characters from falling off of cliffs.
        """
        if self._railing_material is None:
            mat = self._railing_material = ba.Material()
            mat.add_actions(('modify_part_collision', 'collide', False))
            mat.add_actions(('modify_part_collision', 'stiffness', 0.003))
            mat.add_actions(('modify_part_collision', 'damping', 0.00001))
            mat.add_actions(
                conditions=('they_have_material', self.player_material),
                actions=(
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'friction', 0.0),
                ),
            )
        return self._railing_material
