# Released under the MIT License. See LICENSE for details.
#
"""BombSquad specific bits."""

from enum import Enum
from typing import assert_never, Annotated, override
from dataclasses import dataclass

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.legacydisplayitem as lditm


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
        cls = ClassicChestAppearance

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


#: ``(tint, tint2)`` for depicting a chest of each appearance.
#:
#: Lives here rather than with the client's chest code so a *producer*
#: can depict a chest -- under frames the producer decides how things
#: look, and it has no view of client-side presentation tables. The
#: client's richer :class:`~baclassic.ChestAppearanceDisplayInfo` (which
#: also carries textures the C++ layer reads) is built from these, so
#: there is one source rather than two that can drift.
CHEST_APPEARANCE_TINTS: dict[
    ClassicChestAppearance,
    tuple[tuple[float, float, float], tuple[float, float, float]],
] = {
    ClassicChestAppearance.L2: ((0.65, 1.0, 0.8), (0.65, 1.0, 0.8)),
    ClassicChestAppearance.L3: ((0.7, 1, 1.9), (0.7, 1, 1.9)),
    ClassicChestAppearance.L4: ((1.4, 1.6, 2.0), (1.4, 1.6, 2.0)),
    ClassicChestAppearance.L5: ((1.0, 0.8, 0.0), (1.0, 0.8, 0.0)),
    ClassicChestAppearance.L6: ((2, 2, 2), (2, 2, 2)),
}

#: ``(tint, tint2)`` for an appearance with no entry above -- UNKNOWN,
#: DEFAULT and L1 all rely on this.
CHEST_APPEARANCE_TINT_DEFAULT: tuple[
    tuple[float, float, float], tuple[float, float, float]
] = ((1, 1, 1), (1, 1, 1))


@ioprepped
@dataclass
class ClassicChestDisplayItem(lditm.Item):
    """Display a chest."""

    appearance: Annotated[ClassicChestAppearance, IOAttrs('a')]

    @override
    @classmethod
    def get_type_id(cls) -> lditm.ItemTypeID:
        return lditm.ItemTypeID.CHEST

    @override
    def get_description(self) -> tuple[str, list[tuple[str, str]]]:
        return self.appearance.pretty_name, []
