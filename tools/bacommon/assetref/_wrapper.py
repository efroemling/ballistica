# Released under the MIT License. See LICENSE for details.
#
"""Runtime accessor for generated asset-reference wrapper packages.

A generated wrapper module exposes per-kind roots (``textures``,
``meshes``, ...) built from a compact nested kind-code tree; its precise
types live in the module's ``if TYPE_CHECKING`` shadow (a ``FooGroup``
class per subdir, each asset a typed property). This drives the *runtime*
side: a leaf reads as a property yielding the kind's reference type, a
subdir is a nested :class:`AssetRefDir`.

This mirrors the client-side asset wrappers (``bauiv1._assetwrap.AssetDir``)
except it yields a language-independent *reference* (:class:`TextureSpec` /
:class:`MeshSpec`) rather than loading the actual engine asset -- so the
same ergonomics (``pkg.textures.zoe_icon``) work server-side where no real
assets exist.
"""

from bacommon.assetref._core import TextureSpec, MeshSpec, SoundSpec

#: A node in a wrapper's kind-code tree: each key is one path segment; a
#: ``dict`` value is a subdirectory and a ``str`` value is a leaf asset
#: whose string is its single-char kind code (see :func:`_make`).
type AssetRefTree = dict[str, 'str | AssetRefTree']


class AssetRefDir:
    """Dynamic accessor for one subdirectory of an asset-package's refs.

    Attribute access resolves against the wrapper's nested kind-code tree:
    a subdirectory yields another :class:`AssetRefDir`; a leaf yields the
    reference for its kind. All real type information lives in the
    wrapper's ``if TYPE_CHECKING:`` shadow, so callers never type-check
    through this class.
    """

    __slots__ = ('_apverid', '_node', '_prefix')

    def __init__(self, apverid: str, node: AssetRefTree, prefix: str) -> None:
        self._apverid = apverid
        self._node = node
        self._prefix = prefix

    def __getattr__(
        self, name: str
    ) -> 'AssetRefDir | TextureSpec | MeshSpec | SoundSpec':
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
) -> TextureSpec | MeshSpec | SoundSpec:
    """Build a single leaf reference by its single-char kind code."""
    if kind == 't':
        return TextureSpec(apverid, path)
    if kind == 'm':
        return MeshSpec(apverid, path)
    if kind == 's':
        return SoundSpec(apverid, path)
    raise ValueError(f'Invalid asset-ref kind {kind!r} for {apverid}:{path}.')
