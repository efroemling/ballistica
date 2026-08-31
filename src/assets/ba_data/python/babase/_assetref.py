# Released under the MIT License. See LICENSE for details.
#
"""Runtime support for generated babase asset-*reference* wrappers.

This is the babase flavor of :mod:`bacommon.assetspec` and the middle
tier of the D28 asset ladder: ``SoundSpec`` (authoring claim) ->
``SimpleSoundHandle`` (this module; a *verified-local* reference — its
wrapper's pin was construct-mode-resolved before use) ->
``babase.SimpleSound`` (the loaded engine asset).

Sounds are the only kind here. babase has exactly one classic asset
loader api — ``apsimplesoundget``, yielding the context-free
:class:`~babase.SimpleSound` — and no texture or mesh equivalent, so
babase wrappers carry sounds and strings and nothing else. The
featuresets' ``SoundHandle`` wraps the *same* package asset through
their own scene/ui sound api instead; which handle a wrapper's sound
leaves get is decided by its wrapper type at generation time.

That distinction is what this module exists for: babase code runs
before any feature-set is up (the plugin scan, account and workspace
paths, construct-mode's own bring-up ui), so it needs a typed way to
play a sound that does not route through bascenev1 or bauiv1. Only the
construct/builtin package is legitimately loadable that early, which
:func:`~babase._asset_packages.check_asset_package_load` enforces on
every ``get()`` below.
"""

import warnings
from typing import TYPE_CHECKING

import _babase

from babase._asset_packages import check_asset_package_load
from bacommon.assetspec import (
    SoundSpec as _SoundSpec,
    TextureSpec as _TextureSpec,
    MeshSpec as _MeshSpec,
    CubeMapTextureSpec as _CubeMapTextureSpec,
)

if TYPE_CHECKING:
    import babase


# This leaf adds only a ``get()`` method (no new fields), so it needs no
# ``@dataclass`` -- it inherits the base's fields, ``__init__``, ``__eq__``,
# etc., serializes byte-for-byte as the base, and decodes back as the base.
# ``__slots__ = ()`` keeps instances ``__dict__``-free: the spec base is
# slotted, but a subclass that omits ``__slots__`` silently reintroduces a
# ``__dict__``, and the ref is the object actually allocated (and mostly
# thrown away) on every wrapper access, so it's the one that matters.
class SimpleSoundHandle(_SoundSpec):
    """A sound reference that can also load the live engine sound."""

    __slots__ = ()

    def get(self) -> 'babase.SimpleSound':
        """Resolve and return the live engine sound for this reference."""
        check_asset_package_load(self._apverid, self._name)
        return _babase.apsimplesoundget(self._apverid, self._name)


class TextureHandle(_TextureSpec):
    """A texture reference, as the babase wrapper flavor exposes it.

    Deliberately has no ``get()``: babase has no Python texture-loading
    api. The handle exists to be *passed along* -- most notably into
    the base asset set (:func:`babase.set_base_asset_set`), whose
    native side reads the reference and loads the engine asset itself.
    """

    __slots__ = ()


class MeshHandle(_MeshSpec):
    """A mesh reference, as the babase wrapper flavor exposes it.

    Like :class:`TextureHandle`, has no ``get()``: babase has no
    Python mesh-loading api; the reference is consumed native-side
    (base asset set slots).
    """

    __slots__ = ()


class CubeMapTextureHandle(_CubeMapTextureSpec):
    """A cube-map texture reference (babase wrapper flavor).

    Like :class:`TextureHandle`, has no ``get()`` -- cube maps never
    surface as loaded Python objects; the reference is consumed
    native-side (base asset set slots, engine reflections).
    """

    __slots__ = ()


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
    class. Mirrors :class:`bauiv1._assetref.AssetGroup`, differing only in
    what its leaves' ``get()`` loads (a context-free ``SimpleSound``).
    """

    __slots__ = ('_apverid', '_node', '_prefix')

    def __init__(self, apverid: str, node: AssetGroupTree, prefix: str) -> None:
        self._apverid = apverid
        self._node = node
        self._prefix = prefix

    def __getattr__(
        self, name: str
    ) -> (
        'AssetGroup | SimpleSoundHandle | TextureHandle'
        ' | MeshHandle | CubeMapTextureHandle'
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
) -> 'SimpleSoundHandle | TextureHandle | MeshHandle | CubeMapTextureHandle':
    """Build a single leaf reference by its kind code."""
    if kind == 's':
        return SimpleSoundHandle(apverid, path)
    if kind == 't':
        return TextureHandle(apverid, path)
    if kind == 'm':
        return MeshHandle(apverid, path)
    if kind == 'ct':
        return CubeMapTextureHandle(apverid, path)
    raise ValueError(f'Invalid asset-ref kind {kind!r} for {apverid}:{path}.')


def getsimplesound(name: str) -> 'babase.SimpleSound':
    """Load a sound by legacy bare name.

    .. deprecated:: 1.8.0
       Inert; returns a silent sound. Load sounds through a generated
       asset-package wrapper module instead. Will be removed when api 9
       support ends.

    :meta private:
    """
    # Inert rather than removed so no mod breaks on the spot, and silent
    # rather than best-effort because best-effort is what made it a
    # trap: a bare name only resolves while its package happens to be
    # registered, so the same call worked or failed depending on when it
    # ran and which packages the build bundled. Most of these names live
    # in _classicassets, which is not up at all during bring-up -- and
    # plugin startup hooks (``Plugin.on_app_running``) run there, before
    # construct-mode hands off.
    warnings.warn(
        f"babase.getsimplesound('{name}') is inert and will be removed"
        ' when api 9 support ends; load the sound through a generated'
        ' asset-package wrapper module instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    # Deferred: the wrapper imports this module's AssetGroup, so the
    # cycle is structural only -- by the time anyone can call this, the
    # wrapper is long since imported.
    # pylint: disable-next=cyclic-import
    from babase import _builtinassets

    return _builtinassets.audio.blank.get()


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


def simple_sound_from_ref(ref: str) -> 'babase.SimpleSound':
    """Load a simplesound from a qualified ref string.

    See ``_split_ref()`` -- boundary use only.
    """
    apverid, assetname = _split_ref(ref)
    return _babase.apsimplesoundget(apverid, assetname)
