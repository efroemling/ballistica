# Released under the MIT License. See LICENSE for details.
#
"""Language-independent references to assets within asset-packages.

A reference is a minimal pointer -- an ``apverid`` plus an asset's logical
name -- carrying no asset data. The server (bamaster) holds only references;
the client resolves the package and loads the real asset for display. Each
kind gets a distinct type (:class:`TextureRef`, :class:`MeshRef`) so a
consumer schema can enforce where each kind may go.

Type-safe, ergonomic access to a package's references comes from a generated
wrapper module (see :func:`generate_asset_ref_wrapper_module`), whose
per-kind roots (``textures``, ``meshes``) are driven at runtime by
:class:`AssetRefDir` -- mirroring the client-side asset-package wrappers.
"""

from bacommon.assetref._core import TextureRef, MeshRef, SoundRef
from bacommon.assetref._wrapper import AssetRefDir, AssetRefTree
from bacommon.assetref._codegen import generate_asset_ref_wrapper_module

__all__ = [
    'TextureRef',
    'MeshRef',
    'SoundRef',
    'AssetRefDir',
    'AssetRefTree',
    'generate_asset_ref_wrapper_module',
]
