# Released under the MIT License. See LICENSE for details.
#
"""Chest related functionality."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bacommon.bs import ClassicChestAppearance

if TYPE_CHECKING:
    pass


@dataclass
class ChestAppearanceDisplayInfo:
    """Info about how to locally display chest appearances."""

    # NOTE TO SELF: Don't rename these attrs; the C++ layer is hard
    # coded to look for them.

    texclosed: str
    texclosedtint: str
    texopen: str
    texopentint: str
    color: tuple[float, float, float]
    tint: tuple[float, float, float]
    tint2: tuple[float, float, float]


# Info for chest types we know how to draw. Anything not found in here
# should fall back to the DEFAULT entry.
CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT = ChestAppearanceDisplayInfo(
    texclosed='chestIcon',
    texclosedtint='chestIconTint',
    texopen='chestOpenIcon',
    texopentint='chestOpenIconTint',
    color=(1, 1, 1),
    tint=(1, 1, 1),
    tint2=(1, 1, 1),
)

CHEST_APPEARANCE_DISPLAY_INFOS: dict[
    ClassicChestAppearance, ChestAppearanceDisplayInfo
] = {
    ClassicChestAppearance.L2: ChestAppearanceDisplayInfo(
        texclosed='chestIcon',
        texclosedtint='chestIconTint',
        texopen='chestOpenIcon',
        texopentint='chestOpenIconTint',
        color=(0.8, 1.0, 0.93),
        tint=(0.65, 1.0, 0.8),
        tint2=(0.65, 1.0, 0.8),
    ),
    ClassicChestAppearance.L3: ChestAppearanceDisplayInfo(
        texclosed='chestIcon',
        texclosedtint='chestIconTint',
        texopen='chestOpenIcon',
        texopentint='chestOpenIconTint',
        color=(0.75, 0.9, 1.3),
        tint=(0.7, 1, 1.9),
        tint2=(0.7, 1, 1.9),
    ),
    ClassicChestAppearance.L4: ChestAppearanceDisplayInfo(
        texclosed='chestIcon',
        texclosedtint='chestIconTint',
        texopen='chestOpenIcon',
        texopentint='chestOpenIconTint',
        color=(0.7, 1.0, 1.4),
        tint=(1.4, 1.6, 2.0),
        tint2=(1.4, 1.6, 2.0),
    ),
    ClassicChestAppearance.L5: ChestAppearanceDisplayInfo(
        texclosed='chestIcon',
        texclosedtint='chestIconTint',
        texopen='chestOpenIcon',
        texopentint='chestOpenIconTint',
        color=(0.75, 0.5, 2.4),
        tint=(1.0, 0.8, 0.0),
        tint2=(1.0, 0.8, 0.0),
    ),
    ClassicChestAppearance.L6: ChestAppearanceDisplayInfo(
        texclosed='chestIcon',
        texclosedtint='chestIconTint',
        texopen='chestOpenIcon',
        texopentint='chestOpenIconTint',
        color=(1.1, 0.8, 0.0),
        tint=(2, 2, 2),
        tint2=(2, 2, 2),
    ),
}
