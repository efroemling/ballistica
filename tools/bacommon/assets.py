# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to cloud based assets."""

from __future__ import annotations

from typing import TYPE_CHECKING
from enum import Enum

from efro import entity

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


class AssetPackageFlavorManifestValue(entity.CompoundValue):
    """A manifest of asset info for a specific flavor of an asset package."""
    assetfiles = entity.DictField('assetfiles', str, entity.StringValue())


class AssetPackageFlavorManifest(entity.EntityMixin,
                                 AssetPackageFlavorManifestValue):
    """A self contained AssetPackageFlavorManifestValue."""


class AssetPackageBuildState(entity.Entity):
    """Contains info about an in-progress asset cloud build."""

    # Asset names still being built.
    in_progress_builds = entity.ListField('b', entity.StringValue())

    # The initial number of assets needing to be built.
    initial_build_count = entity.Field('c', entity.IntValue())

    # Build error string. If this is present, it should be presented
    # to the user and they should required to explicitly restart the build
    # in some way if desired.
    error = entity.Field('e', entity.OptionalStringValue())
