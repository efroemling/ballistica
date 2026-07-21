# Released under the MIT License. See LICENSE for details.
#
"""Asset *specs*: authoring-level references to asset-package assets.

A spec is a minimal claim about an asset -- an ``apverid`` plus a
logical name -- carrying no asset data and no guarantee the package is
locally present (or still exists). Per the D28 semantic split (see
``strings-asset-migration.md`` in ballistica-internal), assets ladder
through three tiers: ``TextureSpec`` (this claim form; wire/model
currency) -> client ``bauiv1.TextureRef`` (a verified-local subclass
adding ``.get()``; its wrapper pin resolved before use) ->
``bauiv1.Texture`` (the loaded engine asset). Servers hold only specs;
consuming clients verify/resolve before display. Each kind gets a
distinct type (:class:`TextureSpec`, :class:`MeshSpec`) so a consumer
schema can enforce where each kind may go.

Type-safe, ergonomic access to a package's references comes from a generated
wrapper module (emitted server-side; the codegen lives in
``baserver.assetwrappergen``), whose per-kind roots (``textures``, ``meshes``)
are driven at runtime by :class:`AssetRefDir` -- mirroring the client-side
asset-package wrappers.
"""

from bacommon.assetref._core import TextureSpec, MeshSpec, SoundSpec
from bacommon.assetref._wrapper import AssetRefDir, AssetRefTree

__all__ = [
    'TextureSpec',
    'MeshSpec',
    'SoundSpec',
    'AssetRefDir',
    'AssetRefTree',
]
