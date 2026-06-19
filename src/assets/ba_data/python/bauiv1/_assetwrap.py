# Released under the MIT License. See LICENSE for details.
#
"""Runtime support for generated bauiv1 asset-package wrappers.

The generated wrapper modules (``builtinassets``, ``stdassets``, etc.)
keep their full typed asset tree in an ``if TYPE_CHECKING:`` block, so
the type checker sees every asset as a precisely-typed attribute. At
runtime that block is dead; resolution is driven dynamically by
:class:`AssetDir` from a compact nested-dict the wrapper carries. This
keeps per-wrapper runtime cost to one data dict plus a handful of small
accessor objects no matter how many assets the package contains (see
asset-packages design doc decision #28).

The UI featureset has no physics API, so (unlike bascenev1) there is no
collision-mesh loader here; the generator omits collision meshes from
bauiv1 wrappers.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bauiv1

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
    ) -> AssetDir | bauiv1.Texture | bauiv1.Sound | bauiv1.Mesh:
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
) -> bauiv1.Texture | bauiv1.Sound | bauiv1.Mesh:
    """Load a single leaf asset by its single-char kind code."""
    import bauiv1

    ref = f'{apverid}:{path}'
    if kind == 't':
        return bauiv1.gettexture(ref)
    if kind == 's':
        return bauiv1.getsound(ref)
    if kind == 'm':
        return bauiv1.getmesh(ref)
    raise ValueError(f'Invalid asset kind {kind!r} for {ref!r}.')
