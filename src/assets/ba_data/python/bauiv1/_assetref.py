# Released under the MIT License. See LICENSE for details.
#
"""Runtime support for generated bauiv1 asset-*reference* wrappers.

This is the bauiv1 (client) flavor of :mod:`bacommon.assetref`. A
generated reference wrapper exposes per-kind roots (``textures``,
``meshes``, ...) whose leaves are language-independent references
(:class:`~bacommon.assetref.TextureRef` / :class:`~bacommon.assetref.MeshRef`)
suitable for authoring doc-ui-v2 documents. Where the server-side wrapper
(:mod:`bacommon.assetref`) yields the bare ``bacommon`` reference types, the
client wants those references to *also* be loadable into real engine assets
for low-level UI calls. So this module's leaves are thin subclasses that add
a single :meth:`TextureRef.get` method returning the live ``bauiv1.Texture``
(etc.) while remaining ordinary references on the wire.

The subclasses add no data fields -- only the ``get()`` accessor -- so an
instance serializes identically to its ``bacommon`` base and decodes back as
the plain base type on the far end (the subclass is an authoring-side
convenience only). This is the inverse of inheriting a field-less abstract
base; it stays within dataclassio's rules (a nested-dataclass field accepts
any ``isinstance`` of its annotated type).
"""

from typing import TYPE_CHECKING

from bacommon.assetref import (
    TextureRef as _TextureRef,
    MeshRef as _MeshRef,
    SoundRef as _SoundRef,
)

if TYPE_CHECKING:
    import bauiv1


# These leaves add only a ``get()`` method (no new fields), so they need no
# ``@dataclass`` -- they inherit the base's fields, ``__init__``, ``__eq__``,
# etc., serialize byte-for-byte as the base, and decode back as the base.
class TextureRef(_TextureRef):
    """A texture reference that can also load the live engine texture."""

    def get(self) -> 'bauiv1.Texture':
        """Resolve and return the live engine texture for this reference."""
        import bauiv1

        return bauiv1.gettexture(f'{self.apverid}:{self.name}')


class MeshRef(_MeshRef):
    """A mesh reference that can also load the live engine mesh."""

    def get(self) -> 'bauiv1.Mesh':
        """Resolve and return the live engine mesh for this reference."""
        import bauiv1

        return bauiv1.getmesh(f'{self.apverid}:{self.name}')


class SoundRef(_SoundRef):
    """A sound reference that can also load the live engine sound."""

    def get(self) -> 'bauiv1.Sound':
        """Resolve and return the live engine sound for this reference."""
        import bauiv1

        return bauiv1.getsound(f'{self.apverid}:{self.name}')


#: A node in a wrapper's kind-code tree: each key is one path segment; a
#: ``dict`` value is a subdirectory and a ``str`` value is a leaf asset
#: whose string is its single-char kind code (see :func:`_make`).
type AssetRefTree = dict[str, 'str | AssetRefTree']


class AssetRefDir:
    """Dynamic accessor for one subdirectory of an asset-package's refs.

    Attribute access resolves against the wrapper's nested kind-code tree:
    a subdirectory yields another :class:`AssetRefDir`; a leaf yields the
    reference for its kind. All real type information lives in the wrapper's
    ``if TYPE_CHECKING:`` shadow, so callers never type-check through this
    class. Mirrors :class:`bauiv1._assetwrap.AssetDir` but yields a
    reference rather than loading the asset directly.
    """

    __slots__ = ('_apverid', '_node', '_prefix')

    def __init__(self, apverid: str, node: AssetRefTree, prefix: str) -> None:
        self._apverid = apverid
        self._node = node
        self._prefix = prefix

    def __getattr__(
        self, name: str
    ) -> 'AssetRefDir | TextureRef | MeshRef | SoundRef':
        try:
            child = self._node[name]
        except KeyError:
            raise AttributeError(name) from None
        path = f'{self._prefix}/{name}' if self._prefix else name
        if isinstance(child, dict):
            return AssetRefDir(self._apverid, child, path)
        return _make(self._apverid, path, child)


def _make(
    apverid: str, path: str, kind: str
) -> TextureRef | MeshRef | SoundRef:
    """Build a single leaf reference by its single-char kind code."""
    if kind == 't':
        return TextureRef(apverid, path)
    if kind == 'm':
        return MeshRef(apverid, path)
    if kind == 's':
        return SoundRef(apverid, path)
    raise ValueError(f'Invalid asset-ref kind {kind!r} for {apverid}:{path}.')
