# Released under the MIT License. See LICENSE for details.
#
"""Chest related functionality."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bacommon.classic import (
    ClassicChestAppearance,
    CHEST_APPEARANCE_TINTS,
    CHEST_APPEARANCE_TINT_DEFAULT,
)
from bascenev1 import _classicassets

if TYPE_CHECKING:
    import bascenev1


@dataclass
class ChestAppearanceDisplayInfo:
    """Info about how to locally display chest appearances."""

    # NOTE TO SELF: Don't rename these attrs; the C++ layer is hard
    # coded to look for them.

    # Scene-flavor handles; ui consumers convert with .ui(). The native
    # layer reads these by attribute name (see ClassicPython::
    # ChestDisplayFromPython), so it reads the handle's parts.
    texclosed: bascenev1.TextureHandle
    texclosedtint: bascenev1.TextureHandle
    texopen: bascenev1.TextureHandle
    texopentint: bascenev1.TextureHandle
    color: tuple[float, float, float]
    tint: tuple[float, float, float]
    tint2: tuple[float, float, float]


#: Fallback :class:`ChestAppearanceDisplayInfo` used when a chest's
#: declared appearance has no entry in
#: :data:`CHEST_APPEARANCE_DISPLAY_INFOS`.
CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT = ChestAppearanceDisplayInfo(
    texclosed=_classicassets.textures.chest_icon,
    texclosedtint=_classicassets.textures.chest_icon_tint,
    texopen=_classicassets.textures.chest_open_icon,
    texopentint=_classicassets.textures.chest_open_icon_tint,
    color=(1, 1, 1),
    tint=CHEST_APPEARANCE_TINT_DEFAULT[0],
    tint2=CHEST_APPEARANCE_TINT_DEFAULT[1],
)

#: Per-:class:`ClassicChestAppearance` rendering info for chests
#: the engine knows how to draw. Entries absent here fall back to
#: :data:`CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT`.
CHEST_APPEARANCE_DISPLAY_INFOS: dict[
    ClassicChestAppearance, ChestAppearanceDisplayInfo
] = {
    ClassicChestAppearance.L2: ChestAppearanceDisplayInfo(
        texclosed=_classicassets.textures.chest_icon,
        texclosedtint=_classicassets.textures.chest_icon_tint,
        texopen=_classicassets.textures.chest_open_icon,
        texopentint=_classicassets.textures.chest_open_icon_tint,
        color=(0.8, 1.0, 0.93),
        tint=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L2][0],
        tint2=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L2][1],
    ),
    ClassicChestAppearance.L3: ChestAppearanceDisplayInfo(
        texclosed=_classicassets.textures.chest_icon,
        texclosedtint=_classicassets.textures.chest_icon_tint,
        texopen=_classicassets.textures.chest_open_icon,
        texopentint=_classicassets.textures.chest_open_icon_tint,
        color=(0.75, 0.9, 1.3),
        tint=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L3][0],
        tint2=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L3][1],
    ),
    ClassicChestAppearance.L4: ChestAppearanceDisplayInfo(
        texclosed=_classicassets.textures.chest_icon,
        texclosedtint=_classicassets.textures.chest_icon_tint,
        texopen=_classicassets.textures.chest_open_icon,
        texopentint=_classicassets.textures.chest_open_icon_tint,
        color=(0.7, 1.0, 1.4),
        tint=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L4][0],
        tint2=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L4][1],
    ),
    ClassicChestAppearance.L5: ChestAppearanceDisplayInfo(
        texclosed=_classicassets.textures.chest_icon,
        texclosedtint=_classicassets.textures.chest_icon_tint,
        texopen=_classicassets.textures.chest_open_icon,
        texopentint=_classicassets.textures.chest_open_icon_tint,
        color=(0.75, 0.5, 2.4),
        tint=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L5][0],
        tint2=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L5][1],
    ),
    ClassicChestAppearance.L6: ChestAppearanceDisplayInfo(
        texclosed=_classicassets.textures.chest_icon,
        texclosedtint=_classicassets.textures.chest_icon_tint,
        texopen=_classicassets.textures.chest_open_icon,
        texopentint=_classicassets.textures.chest_open_icon_tint,
        color=(1.1, 0.8, 0.0),
        tint=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L6][0],
        tint2=CHEST_APPEARANCE_TINTS[ClassicChestAppearance.L6][1],
    ),
}
