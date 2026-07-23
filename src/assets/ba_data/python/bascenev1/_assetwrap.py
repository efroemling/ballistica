# Released under the MIT License. See LICENSE for details.
#
"""Runtime support for generated bascenev1 asset-package wrappers.

The generated wrapper modules (``builtinassets``, ``classicassets``, etc.)
keep their full typed asset tree in an ``if TYPE_CHECKING:`` block, so
the type checker sees every asset as a precisely-typed attribute. At
runtime that block is dead; resolution is driven dynamically by
:class:`AssetDir` from a compact nested-dict the wrapper carries. This
keeps per-wrapper runtime cost to one data dict plus a handful of small
accessor objects no matter how many assets the package contains (see
asset-packages design doc decision #28).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bascenev1

#: A node in a wrapper's asset tree. Each key is one path segment; a
#: ``dict`` value is a subdirectory and a ``str`` value is a leaf asset
#: whose string is its single-char kind code (see :func:`_load`).
type AssetNode = dict[str, str | AssetNode]


class AssetDir:
    """Dynamic accessor for one subdirectory of an asset package.

    Attribute access resolves against the wrapper's nested-dict tree: a
    subdirectory yields another :class:`AssetDir`, a leaf yields the
    loaded asset. All real type information lives in the wrapper's
    ``if TYPE_CHECKING:`` tree, so callers never type-check through this
    class; its annotations exist only for this module's own checking.
    """

    __slots__ = ('_apverid', '_node', '_prefix')

    def __init__(self, apverid: str, node: AssetNode, prefix: str) -> None:
        self._apverid = apverid
        self._node = node
        self._prefix = prefix

    def __getattr__(
        self, name: str
    ) -> (
        AssetDir
        | bascenev1.Texture
        | bascenev1.Sound
        | bascenev1.Mesh
        | bascenev1.CollisionMesh
    ):
        try:
            child = self._node[name]
        except KeyError:
            raise AttributeError(name) from None
        path = f'{self._prefix}/{name}' if self._prefix else name
        if isinstance(child, dict):
            return AssetDir(self._apverid, child, path)
        return _load(self._apverid, path, child)


def _load(
    apverid: str, path: str, kind: str
) -> (
    bascenev1.Texture
    | bascenev1.Sound
    | bascenev1.Mesh
    | bascenev1.CollisionMesh
):
    """Load a single leaf asset by its single-char kind code."""
    import bascenev1

    ref = f'{apverid}:{path}'
    if kind == 't':
        return bascenev1.gettexture(ref)
    if kind == 's':
        return bascenev1.getsound(ref)
    if kind == 'm':
        return bascenev1.getmesh(ref)
    if kind == 'c':
        return bascenev1.getcollisionmesh(ref)
    raise ValueError(f'Invalid asset kind {kind!r} for {ref!r}.')
