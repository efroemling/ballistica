# Released under the MIT License. See LICENSE for details.
#
"""Runtime support for generated bauiv1 asset-*reference* wrappers.

This is the bauiv1 (client) flavor of :mod:`bacommon.assetspec` and the
middle tier of the D28 asset ladder: ``TextureSpec`` (authoring claim)
-> ``TextureHandle`` (this module; a *verified-local* reference — its
wrapper's pin was construct-mode-resolved before use) ->
``bauiv1.Texture`` (the loaded engine asset). A generated reference
wrapper exposes per-kind roots (``textures``, ``meshes``, ...) whose
leaves here are thin subclasses of the spec types adding a single
:meth:`TextureHandle.get` method returning the live ``bauiv1.Texture``
(etc.) while remaining ordinary specs on the wire.

The subclasses add no data fields -- only the ``get()`` accessor -- so
an instance serializes identically to its spec base and decodes back as
the plain base type on the far end (the subclass is an authoring-side
convenience only; verified -> spec is the always-valid direction, here
via plain inheritance rather than langstr's ``.spec`` projection). This
is the inverse of inheriting a field-less abstract base; it stays
within dataclassio's rules (a nested-dataclass field accepts any
``isinstance`` of its annotated type).
"""

from typing import TYPE_CHECKING

import _bauiv1

from babase import check_asset_package_load
from bacommon.assetspec import (
    TextureSpec as _TextureSpec,
    MeshSpec as _MeshSpec,
    SoundSpec as _SoundSpec,
)

if TYPE_CHECKING:
    import bauiv1


# These leaves add only a ``get()`` method (no new fields), so they need no
# ``@dataclass`` -- they inherit the base's fields, ``__init__``, ``__eq__``,
# etc., serialize byte-for-byte as the base, and decode back as the base.
# ``__slots__ = ()`` keeps instances ``__dict__``-free: the spec base is
# slotted, but a subclass that omits ``__slots__`` silently reintroduces a
# ``__dict__``, and the ref is the object actually allocated (and mostly
# thrown away) on every wrapper access, so it's the one that matters.
class TextureHandle(_TextureSpec):
    """A texture reference that can also load the live engine texture."""

    __slots__ = ()

    @classmethod
    def from_spec(cls, spec: _TextureSpec) -> 'TextureHandle':
        """Loadable handle for a spec that arrived from outside.

        Server-sent content and the wire carry plain specs; this is how
        one becomes loadable without anyone rebuilding a path string.
        Verification still happens in :meth:`get`.
        """
        # pylint: disable=protected-access
        return cls(spec._apverid, spec._name)

    def get(self) -> 'bauiv1.Texture':
        """Resolve and return the live engine texture for this reference."""
        check_asset_package_load(self._apverid, self._name)
        return _bauiv1.aptextureget(self._apverid, self._name)


class MeshHandle(_MeshSpec):
    """A mesh reference that can also load the live engine mesh."""

    __slots__ = ()

    @classmethod
    def from_spec(cls, spec: _MeshSpec) -> 'MeshHandle':
        """Loadable handle for a spec that arrived from outside.

        Server-sent content and the wire carry plain specs; this is how
        one becomes loadable without anyone rebuilding a path string.
        Verification still happens in :meth:`get`.
        """
        # pylint: disable=protected-access
        return cls(spec._apverid, spec._name)

    def get(self) -> 'bauiv1.Mesh':
        """Resolve and return the live engine mesh for this reference."""
        check_asset_package_load(self._apverid, self._name)
        return _bauiv1.apmeshget(self._apverid, self._name)


class SoundHandle(_SoundSpec):
    """A sound reference that can also load the live engine sound."""

    __slots__ = ()

    @classmethod
    def from_spec(cls, spec: _SoundSpec) -> 'SoundHandle':
        """Loadable handle for a spec that arrived from outside.

        Server-sent content and the wire carry plain specs; this is how
        one becomes loadable without anyone rebuilding a path string.
        Verification still happens in :meth:`get`.
        """
        # pylint: disable=protected-access
        return cls(spec._apverid, spec._name)

    def get(self) -> 'bauiv1.Sound':
        """Resolve and return the live engine sound for this reference."""
        check_asset_package_load(self._apverid, self._name)
        return _bauiv1.apsoundget(self._apverid, self._name)


#: A node in a wrapper's kind-code tree: each key is one path segment; a
#: ``dict`` value is a subdirectory and a ``str`` value is a leaf asset
#: whose string is its single-char kind code (see :func:`_make`).
type AssetGroupTree = dict[str, 'str | AssetGroupTree']


class AssetGroup:
    """Dynamic accessor for one subdirectory of an asset-package's refs.

    Attribute access resolves against the wrapper's nested kind-code tree:
    a subdirectory yields another :class:`AssetGroup`; a leaf yields the
    reference for its kind. All real type information lives in the wrapper's
    ``if TYPE_CHECKING:`` shadow, so callers never type-check through this
    class. Mirrors :class:`bascenev1._assetref.AssetGroup`, differing only
    in what its leaves' ``get()`` loads (ui vs scene assets).
    """

    __slots__ = ('_apverid', '_node', '_prefix')

    def __init__(self, apverid: str, node: AssetGroupTree, prefix: str) -> None:
        self._apverid = apverid
        self._node = node
        self._prefix = prefix

    def __getattr__(
        self, name: str
    ) -> 'AssetGroup | TextureHandle | MeshHandle' ' | SoundHandle':
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
) -> TextureHandle | MeshHandle | SoundHandle:
    """Build a single leaf reference by its single-char kind code."""
    if kind == 't':
        return TextureHandle(apverid, path)
    if kind == 'm':
        return MeshHandle(apverid, path)
    if kind == 's':
        return SoundHandle(apverid, path)
    raise ValueError(f'Invalid asset-ref kind {kind!r} for {apverid}:{path}.')


def _split_ref(ref: str) -> tuple[str, str]:
    """Split a qualified ``<apverid>:<name>`` ref into its two parts.

    **Boundary use only.** Asset identity inside the app is a typed
    handle from a generated wrapper module; nothing here builds or
    accepts a path string. But refs do still arrive from *outside* as
    strings -- server-sent content, saved app-config, the scene wire,
    stored player profiles -- and something has to turn those into
    assets. That conversion happens here, in one named place, rather
    than ambiently.

    New code should hold a handle and call its ``get()`` instead.
    """
    apverid, sep, name = ref.partition(':')
    if not sep:
        raise ValueError(
            f"Not a qualified asset-package ref: '{ref}'. Legacy bare"
            f' names load through the legacy get* calls instead.'
        )
    return apverid, name


def texture_from_ref(ref: str) -> 'bauiv1.Texture':
    """Load a texture from a qualified ref string.

    See ``_split_ref()`` -- boundary use only.
    """
    apverid, assetname = _split_ref(ref)
    return _bauiv1.aptextureget(apverid, assetname)


def mesh_from_ref(ref: str) -> 'bauiv1.Mesh':
    """Load a mesh from a qualified ref string.

    See ``_split_ref()`` -- boundary use only.
    """
    apverid, assetname = _split_ref(ref)
    return _bauiv1.apmeshget(apverid, assetname)


def sound_from_ref(ref: str) -> 'bauiv1.Sound':
    """Load a sound from a qualified ref string.

    See ``_split_ref()`` -- boundary use only.
    """
    apverid, assetname = _split_ref(ref)
    return _bauiv1.apsoundget(apverid, assetname)
