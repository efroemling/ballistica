# Released under the MIT License. See LICENSE for details.
#
"""Runtime support for generated bascenev1 asset-*reference* wrappers.

This is the bascenev1 (scene) flavor of :mod:`bacommon.assetspec` and
the middle tier of the D28 asset ladder: ``TextureSpec`` (authoring
claim) -> ``TextureHandle`` (this module; a *verified-local*
reference -- its wrapper's pin was construct-mode-resolved before use)
-> ``bascenev1.Texture`` (the loaded engine asset). A generated wrapper
exposes per-kind roots (``textures``, ``meshes``, ...) whose leaves here
are thin subclasses of the spec types adding a single ``get()`` method
returning the live scene asset.

Mirrors :mod:`bauiv1._assetref` exactly but for the scene feature-set,
so ``.get()`` here is a *scene-context* load: it registers the asset
into the current scene (giving it a stream id for replication to joined
clients) and is scoped to that scene's lifetime. Consequently it
requires a scene context -- there is no context-free scene load -- which
is precisely why the leaf must stay inert until asked.

That laziness is the point of this tier: a wrapper leaf can now be
*referenced* (stored on a config object, handed around, put on the wire
as its spec base) without being loaded, and the load happens where a
scene context actually exists. The previous eager form made a leaf
access itself a load, so it could only ever be written inside a live
scene context.
"""

from typing import TYPE_CHECKING

import _bascenev1

from babase import check_asset_package_load
from bacommon.assetspec import (
    TextureSpec as _TextureSpec,
    MeshSpec as _MeshSpec,
    SoundSpec as _SoundSpec,
    CollisionMeshSpec as _CollisionMeshSpec,
)

if TYPE_CHECKING:
    import bascenev1
    import bauiv1


# These leaves add only a ``get()`` method (no new fields), so they need no
# ``@dataclass`` -- they inherit the base's fields, ``__init__``, ``__eq__``,
# etc., serialize byte-for-byte as the base, and decode back as the base.
# ``__slots__ = ()`` keeps instances ``__dict__``-free: the spec base is
# slotted, but a subclass that omits ``__slots__`` silently reintroduces a
# ``__dict__``, and the ref is the object actually allocated (and mostly
# thrown away) on every wrapper access, so it's the one that matters.
class TextureHandle(_TextureSpec):
    """A texture reference that can also load the live scene texture."""

    __slots__ = ()

    def get(self) -> 'bascenev1.Texture':
        """Resolve and return the live scene texture for this reference.

        Loads into the current scene context (see module docs).
        """
        check_asset_package_load(self.apverid, self.name)
        return _bascenev1.aptextureget(f'{self.apverid}:{self.name}')

    def ui(self) -> 'bauiv1.TextureHandle':
        """This same verified reference, in ui form.

        Both featuresets' handles assert the same thing -- the
        package was construct-mode-resolved -- so converting between
        them preserves that guarantee; only what :meth:`get` loads
        differs (a ui texture vs a scene-bound one). Use at a ui boundary
        consuming scene-authored config, such as a spaz appearance's
        icon.

        There is deliberately no reverse ``scene()`` on the ui types:
        ``scene_v1`` always pulls in ``ui_v1`` (via ``classic``), but a
        spinoff may include ``ui_v1`` with no ``scene_v1`` at all.
        """
        # Deferred: bauiv1 is guaranteed present wherever bascenev1 is,
        # but this keeps the module-import graph acyclic.
        # pylint: disable-next=cyclic-import
        import bauiv1

        return bauiv1.TextureHandle(self.apverid, self.name)


class MeshHandle(_MeshSpec):
    """A mesh reference that can also load the live scene mesh."""

    __slots__ = ()

    def get(self) -> 'bascenev1.Mesh':
        """Resolve and return the live scene mesh for this reference."""
        check_asset_package_load(self.apverid, self.name)
        return _bascenev1.apmeshget(f'{self.apverid}:{self.name}')

    def ui(self) -> 'bauiv1.MeshHandle':
        """This same verified reference, in ui form.

        Both featuresets' handles assert the same thing -- the
        package was construct-mode-resolved -- so converting between
        them preserves that guarantee; only what :meth:`get` loads
        differs (a ui mesh vs a scene-bound one). Use at a ui boundary
        consuming scene-authored config, such as a spaz appearance's
        icon.

        There is deliberately no reverse ``scene()`` on the ui types:
        ``scene_v1`` always pulls in ``ui_v1`` (via ``classic``), but a
        spinoff may include ``ui_v1`` with no ``scene_v1`` at all.
        """
        # Deferred: bauiv1 is guaranteed present wherever bascenev1 is,
        # but this keeps the module-import graph acyclic.
        # pylint: disable-next=cyclic-import
        import bauiv1

        return bauiv1.MeshHandle(self.apverid, self.name)


class SoundHandle(_SoundSpec):
    """A sound reference that can also load the live scene sound."""

    __slots__ = ()

    def get(self) -> 'bascenev1.Sound':
        """Resolve and return the live scene sound for this reference."""
        check_asset_package_load(self.apverid, self.name)
        return _bascenev1.apsoundget(f'{self.apverid}:{self.name}')

    def ui(self) -> 'bauiv1.SoundHandle':
        """This same verified reference, in ui form.

        Both featuresets' handles assert the same thing -- the
        package was construct-mode-resolved -- so converting between
        them preserves that guarantee; only what :meth:`get` loads
        differs (a ui sound vs a scene-bound one). Use at a ui boundary
        consuming scene-authored config, such as a spaz appearance's
        icon.

        There is deliberately no reverse ``scene()`` on the ui types:
        ``scene_v1`` always pulls in ``ui_v1`` (via ``classic``), but a
        spinoff may include ``ui_v1`` with no ``scene_v1`` at all.
        """
        # Deferred: bauiv1 is guaranteed present wherever bascenev1 is,
        # but this keeps the module-import graph acyclic.
        # pylint: disable-next=cyclic-import
        import bauiv1

        return bauiv1.SoundHandle(self.apverid, self.name)


class CollisionMeshHandle(_CollisionMeshSpec):
    """A collision-mesh reference that can also load the live one."""

    __slots__ = ()

    def get(self) -> 'bascenev1.CollisionMesh':
        """Resolve and return the live collision-mesh for this reference."""
        check_asset_package_load(self.apverid, self.name)
        return _bascenev1.apcollisionmeshget(f'{self.apverid}:{self.name}')


#: A node in a wrapper's kind-code tree: each key is one path segment; a
#: ``dict`` value is a subgroup and a ``str`` value is a leaf asset
#: whose string is its single-char kind code (see :func:`_make`).
type AssetGroupTree = dict[str, 'str | AssetGroupTree']


class AssetGroup:
    """Dynamic accessor for one group of an asset-package's refs.

    Attribute access resolves against the wrapper's nested kind-code tree:
    a subgroup yields another :class:`AssetGroup`; a leaf yields the
    reference for its kind. All real type information lives in the wrapper's
    ``if TYPE_CHECKING:`` shadow, so callers never type-check through this
    class. Mirrors :class:`bauiv1._assetref.AssetGroup` but its leaves load
    scene assets.
    """

    __slots__ = ('_apverid', '_node', '_prefix')

    def __init__(self, apverid: str, node: AssetGroupTree, prefix: str) -> None:
        self._apverid = apverid
        self._node = node
        self._prefix = prefix

    def __getattr__(
        self, name: str
    ) -> (
        'AssetGroup | TextureHandle | MeshHandle'
        ' | SoundHandle | CollisionMeshHandle'
    ):
        try:
            child = self._node[name]
        except KeyError:
            raise AttributeError(name) from None
        path = f'{self._prefix}/{name}' if self._prefix else name
        if isinstance(child, dict):
            return AssetGroup(self._apverid, child, path)
        return _make(self._apverid, path, child)


def _make(
    apverid: str, path: str, kind: str
) -> 'TextureHandle | MeshHandle | SoundHandle' ' | CollisionMeshHandle':
    """Build a single leaf reference by its single-char kind code."""
    if kind == 't':
        return TextureHandle(apverid, path)
    if kind == 'm':
        return MeshHandle(apverid, path)
    if kind == 's':
        return SoundHandle(apverid, path)
    if kind == 'c':
        return CollisionMeshHandle(apverid, path)
    raise ValueError(f'Invalid asset-ref kind {kind!r} for {apverid}:{path}.')
