# Released under the MIT License. See LICENSE for details.
#
"""BombSquad specific bits."""

from __future__ import annotations

from enum import Enum
from typing import assert_never


class ClassicChestAppearance(Enum):
    """Appearances bombsquad classic chests can have."""

    UNKNOWN = 'u'
    DEFAULT = 'd'
    L1 = 'l1'
    L2 = 'l2'
    L3 = 'l3'
    L4 = 'l4'
    L5 = 'l5'
    L6 = 'l6'

    @property
    def pretty_name(self) -> str:
        """Pretty name for the chest in English."""
        # pylint: disable=too-many-return-statements
        cls = type(self)

        if self is cls.UNKNOWN:
            return 'Unknown Chest'
        if self is cls.DEFAULT:
            return 'Chest'
        if self is cls.L1:
            return 'L1 Chest'
        if self is cls.L2:
            return 'L2 Chest'
        if self is cls.L3:
            return 'L3 Chest'
        if self is cls.L4:
            return 'L4 Chest'
        if self is cls.L5:
            return 'L5 Chest'
        if self is cls.L6:
            return 'L6 Chest'

        assert_never(self)
