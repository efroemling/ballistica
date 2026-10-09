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

from babase import check_asset_package_load, wrapper_langstr
from bacommon.assetpackage import ApverNum
from bacommon.assetspec import (
    TextureSpec as _TextureSpec,
    MeshSpec as _MeshSpec,
    SoundSpec as _SoundSpec,
    CollisionMeshSpec as _CollisionMeshSpec,
    CubeMapTextureSpec as _CubeMapTextureSpec,
)

if TYPE_CHECKING:
    import babase
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

    @classmethod
    def from_spec(cls, spec: _TextureSpec) -> 'TextureHandle':
        """Loadable handle for a spec that arrived from outside.

        Server-sent content and the wire carry plain specs; this is how
        one becomes loadable without anyone rebuilding a path string.
        Verification still happens in :meth:`get`.
        """
        # pylint: disable=protected-access
        return cls(spec._apvernum, spec._name)

    def get(self) -> 'bascenev1.Texture':
        """Resolve and return the live scene texture for this reference.

        Loads into the current scene context (see module docs).
        """
        check_asset_package_load(self._apvernum, self._name)
        return _bascenev1.aptextureget(self._apvernum, self._name)

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

        return bauiv1.TextureHandle(self._apvernum, self._name)


class MeshHandle(_MeshSpec):
    """A mesh reference that can also load the live scene mesh."""

    __slots__ = ()

    @classmethod
    def from_spec(cls, spec: _MeshSpec) -> 'MeshHandle':
        """Loadable handle for a spec that arrived from outside.

        Server-sent content and the wire carry plain specs; this is how
        one becomes loadable without anyone rebuilding a path string.
        Verification still happens in :meth:`get`.
        """
        # pylint: disable=protected-access
        return cls(spec._apvernum, spec._name)

    def get(self) -> 'bascenev1.Mesh':
        """Resolve and return the live scene mesh for this reference."""
        check_asset_package_load(self._apvernum, self._name)
        return _bascenev1.apmeshget(self._apvernum, self._name)

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

        return bauiv1.MeshHandle(self._apvernum, self._name)


class SoundHandle(_SoundSpec):
    """A sound reference that can also load the live scene sound."""

    __slots__ = ()

    @classmethod
    def from_spec(cls, spec: _SoundSpec) -> 'SoundHandle':
        """Loadable handle for a spec that arrived from outside.

        Server-sent content and the wire carry plain specs; this is how
        one becomes loadable without anyone rebuilding a path string.
        Verification still happens in :meth:`get`.
        """
        # pylint: disable=protected-access
        return cls(spec._apvernum, spec._name)

    def get(self) -> 'bascenev1.Sound':
        """Resolve and return the live scene sound for this reference."""
        check_asset_package_load(self._apvernum, self._name)
        return _bascenev1.apsoundget(self._apvernum, self._name)

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

        return bauiv1.SoundHandle(self._apvernum, self._name)


class CollisionMeshHandle(_CollisionMeshSpec):
    """A collision-mesh reference that can also load the live one."""

    __slots__ = ()

    @classmethod
    def from_spec(cls, spec: _CollisionMeshSpec) -> 'CollisionMeshHandle':
        """Loadable handle for a spec that arrived from outside.

        Server-sent content and the wire carry plain specs; this is how
        one becomes loadable without anyone rebuilding a path string.
        Verification still happens in :meth:`get`.
        """
        # pylint: disable=protected-access
        return cls(spec._apvernum, spec._name)

    def get(self) -> 'bascenev1.CollisionMesh':
        """Resolve and return the live collision-mesh for this reference."""
        check_asset_package_load(self._apvernum, self._name)
        return _bascenev1.apcollisionmeshget(self._apvernum, self._name)


class CubeMapTextureHandle(_CubeMapTextureSpec):
    """A cube-map texture reference (scene wrapper flavor).

    Deliberately has no ``get()``: cube maps never surface as loaded
    Python objects (scene node reflections are engine-side, keyed by
    a :class:`~bascenev1.Node` string attr). The handle exists to be
    passed along -- most notably into base or scene asset-set slots,
    whose native sides read the reference and load the engine asset
    themselves.
    """

    __slots__ = ()


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

    __slots__ = ('_apvernum', '_node', '_prefix')

    def __init__(
        self, apvernum: ApverNum, node: AssetGroupTree, prefix: str
    ) -> None:
        self._apvernum = apvernum
        self._node = node
        self._prefix = prefix

    def __getattr__(
        self, name: str
    ) -> (
        'AssetGroup | TextureHandle | MeshHandle'
        ' | SoundHandle | CollisionMeshHandle | CubeMapTextureHandle'
    ):
        try:
            child = self._node[name]
        except KeyError:
            raise AttributeError(name) from None
        path = f'{self._prefix}/{name}' if self._prefix else name
        if isinstance(child, dict):
            return AssetGroup(self._apvernum, child, path)
        return _make(self._apvernum, path, child)


def _make(
    apvernum: ApverNum, path: str, kind: str
) -> (
    'TextureHandle | MeshHandle | SoundHandle'
    ' | CollisionMeshHandle | CubeMapTextureHandle'
):
    """Build a single leaf reference by its single-char kind code."""
    if kind == 't':
        return TextureHandle(apvernum, path)
    if kind == 'm':
        return MeshHandle(apvernum, path)
    if kind == 's':
        return SoundHandle(apvernum, path)
    if kind == 'c':
        return CollisionMeshHandle(apvernum, path)
    if kind == 'ct':
        return CubeMapTextureHandle(apvernum, path)
    raise ValueError(f'Invalid asset-ref kind {kind!r} for {apvernum}:{path}.')


#: What a wrapper carries per character: the json of its spaz def, the
#: json of its icon depiction, and the logical path of its name string.
#: A subdirectory of characters is a nested dict of the same.
type CharacterGroupData = dict[str, 'tuple[str, str, str] | CharacterGroupData']

# Where an activity keeps the scene objects made for characters (in its
# customdata, so they go when it does).
_SPAZ_DEFS_KEY = '_ba_character_spaz_defs'
_ICON_DEPICTIONS_KEY = '_ba_character_icon_depictions'


class CharacterHandle:
    """A character from an asset-package, ready to use in a scene.

    Reached through a generated wrapper (``mypackage.characters.zoe``).
    The scene objects it hands out belong to the current activity and
    are made once per activity, so ask in the activity that will use
    them and don't hold one beyond it.
    """

    __slots__ = ('_apvernum', '_path', '_data')

    def __init__(
        self, apvernum: ApverNum, path: str, data: tuple[str, str, str]
    ) -> None:
        self._apvernum = apvernum
        self._path = path
        self._data = data

    def get_spaz_def(self) -> 'bascenev1.SpazDef':
        """Return this character's spaz def for the current activity.

        Assign it to a spaz node's ``spaz_def`` attr. The first call in
        an activity makes it; later ones there return the same object.
        Outside an activity (a session context) a new one is made each
        call.
        """
        check_asset_package_load(self._apvernum, self._path)
        activity = _bascenev1.getactivity(doraise=False)
        if activity is None:
            return _bascenev1.SpazDef(self._data[0])
        made: dict[tuple[ApverNum, str], bascenev1.SpazDef] = (
            activity.customdata.setdefault(_SPAZ_DEFS_KEY, {})
        )
        key = (self._apvernum, self._path)
        spaz_def = made.get(key)
        if spaz_def is None:
            spaz_def = made[key] = _bascenev1.SpazDef(self._data[0])
        return spaz_def

    def get_icon_depiction(self) -> 'bascenev1.Depiction':
        """Return this character's icon for the current activity.

        In the character's own colors. Show it with a
        ``depictiondisplay`` node or anything else accepting a
        :class:`~bascenev1.Depiction`. Made once per activity, as
        :meth:`get_spaz_def` is.
        """
        check_asset_package_load(self._apvernum, self._path)
        activity = _bascenev1.getactivity(doraise=False)
        if activity is None:
            return _bascenev1.Depiction(self._data[1])
        made: dict[tuple[ApverNum, str], bascenev1.Depiction] = (
            activity.customdata.setdefault(_ICON_DEPICTIONS_KEY, {})
        )
        key = (self._apvernum, self._path)
        depiction = made.get(key)
        if depiction is None:
            depiction = made[key] = _bascenev1.Depiction(self._data[1])
        return depiction

    def get_name(self) -> 'babase.LangStr':
        """Return this character's name."""
        return wrapper_langstr(self._apvernum, self._data[2])


class CharacterGroup:
    """Dynamic accessor for one directory of an asset-package's characters.

    Attribute access yields a :class:`CharacterHandle`, or another
    group for a subdirectory; all real type information lives in the
    wrapper's ``if TYPE_CHECKING:`` shadow.
    """

    __slots__ = ('_apvernum', '_data', '_prefix')

    def __init__(
        self, apvernum: ApverNum, data: CharacterGroupData, prefix: str
    ) -> None:
        self._apvernum = apvernum
        self._data = data
        self._prefix = prefix

    def __getattr__(self, name: str) -> 'CharacterHandle | CharacterGroup':
        try:
            data = self._data[name]
        except KeyError:
            raise AttributeError(name) from None
        path = f'{self._prefix}/{name}'
        if isinstance(data, dict):
            return CharacterGroup(self._apvernum, data, path)
        return CharacterHandle(self._apvernum, path, data)


def _split_ref(ref: str) -> tuple[ApverNum, str]:
    """Split a qualified ``<apvernum>:<name>`` ref into its two parts.

    **Boundary use only.** Asset identity inside the app is a typed
    handle from a generated wrapper module; nothing here builds or
    accepts a path string. But refs do still arrive from *outside* as
    strings -- server-sent content, saved app-config, the scene wire,
    stored player profiles -- and something has to turn those into
    assets. That conversion happens here, in one named place, rather
    than ambiently.

    New code should hold a handle and call its ``get()`` instead.
    """
    apvernum, sep, name = ref.partition(':')
    if not sep:
        raise ValueError(
            f"Not a qualified asset-package ref: '{ref}'. Legacy bare"
            f' names load through the legacy get* calls instead.'
        )
    if not apvernum.isdigit():
        raise ValueError(
            f"Not a qualified asset-package ref: '{ref}' (its package"
            f' is not a numeric id).'
        )
    return ApverNum(int(apvernum)), name


def texture_from_ref(ref: str) -> 'bascenev1.Texture':
    """Load a texture from a qualified ref string.

    See ``_split_ref()`` -- boundary use only.
    """
    apvernum, assetname = _split_ref(ref)
    return _bascenev1.aptextureget(apvernum, assetname)


def qualified_ref(spec: '_TextureSpec') -> str:
    """Render a spec as a qualified ``<apvernum>:<name>`` string.

    **Boundary use only**, and the outward twin of ``_split_ref()``:
    for refs *leaving* the app as strings, where the receiver is not
    ours to change -- the scene wire to other clients, stored player
    profiles. Everything staying inside should pass the spec itself.
    """
    # pylint: disable=protected-access
    return f'{spec._apvernum}:{spec._name}'
