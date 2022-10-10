# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to cloud based assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated
from enum import Enum

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


class AssetPackageFlavor(Enum):
    """Flavors for asset package outputs for different platforms/etc."""

    # DXT3/DXT5 textures
    DESKTOP = 'desktop'

    # ASTC textures
    MOBILE = 'mobile'


class AssetType(Enum):
    """Types for individual assets within a package."""

    TEXTURE = 'texture'
    CUBE_TEXTURE = 'cube_texture'
    SOUND = 'sound'
    DATA = 'data'
    MESH = 'mesh'
    COLLISION_MESH = 'collision_mesh'


@ioprepped
@dataclass
class AssetPackageFlavorManifest:
    """A manifest of asset info for a specific flavor of an asset package."""

    cloudfiles: Annotated[dict[str, str], IOAttrs('cloudfiles')] = field(
        default_factory=dict
    )


@ioprepped
@dataclass
class AssetPackageBuildState:
    """Contains info about an in-progress asset cloud build."""

    # Asset names still being built.
    in_progress_builds: Annotated[list[str], IOAttrs('b')] = field(
        default_factory=list
    )

    # The initial number of assets needing to be built.
    initial_build_count: Annotated[int, IOAttrs('c')] = 0

    # Build error string. If this is present, it should be presented
    # to the user and they should required to explicitly restart the build
    # in some way if desired.
    error: Annotated[str | None, IOAttrs('e')] = None
