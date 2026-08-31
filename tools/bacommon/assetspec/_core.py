# Released under the MIT License. See LICENSE for details.
#
"""Core types for language-independent asset references.

An asset reference is a minimal, language-independent pointer to a single
asset within a published asset-package-version: its exact ``apverid`` plus
the asset's logical ``name`` (e.g. ``textures/zoe_icon``). It carries no
asset *data* -- the server (bamaster) only ever holds the reference; the
client resolves the package and loads the actual asset for display.

Each asset kind gets its own type (:class:`TextureSpec`, :class:`MeshSpec`,
...) so that a consumer schema can enforce *where* each kind may go -- a
texture-typed field rejects a mesh and vice versa. The types share an
identical shape but are deliberately distinct classes for that reason.

These are ``@ioprepped`` so a reference can be sent directly on the wire
(e.g. as a doc-ui-v2 field); it serializes to a small JSON snippet and the
client resolves+renders it. The qualified engine form is ``<apverid>:<name>``
(e.g. ``a-0.foo.260626:textures/zoe_icon``).
"""

from dataclasses import dataclass
from typing import Annotated

from efro.dataclassio import ioprepped, IOAttrs, IO_SLOTS

# These types are created in large volume -- one per asset-package
# wrapper access mints a spec-subclass (a ref), plus every doc-ui page,
# langstr resolve, etc. -- and each is a tiny two-field object, so the
# per-instance ``__dict__`` is a big relative fraction. They're slotted
# to shed it. Manual ``__slots__`` (rather than ``@dataclass(slots=True)``)
# is used because the fields have no defaults (so there is no slot/
# class-var conflict) and it keeps the decorator stack simple; ``IO_SLOTS``
# reserves dataclassio's per-instance metadata slot. Field-less ref
# subclasses (``bauiv1._assetref``) must add ``__slots__ = ()`` of their
# own to stay ``__dict__``-free.


@ioprepped
@dataclass
class TextureSpec:
    """A language-independent reference to a texture in an asset-package.

    Identity is a package version plus the texture's logical
    path within it (e.g. ``textures/zoe_icon``); the engine resolves the
    qualified ``<apverid>:<name>`` form.

    Both parts are **private**: a spec is produced by a generated
    wrapper module and consumed as a whole, and code that reaches
    in to rebuild a path string by hand is exactly what asset
    renames used to rot. Nothing accepts such a string any more
    (see the ap*get bindings), so reaching in has no destination.
    """

    __slots__ = ('_apverid', '_name', *IO_SLOTS)

    _apverid: Annotated[str, IOAttrs('a')]
    _name: Annotated[str, IOAttrs('n')]


@ioprepped
@dataclass
class MeshSpec:
    """A language-independent reference to a mesh in an asset-package.

    Identity is a package version plus the mesh's logical
    path within it (e.g. ``meshes/box``); the engine resolves the
    qualified ``<apverid>:<name>`` form.

    Both parts are **private**: a spec is produced by a generated
    wrapper module and consumed as a whole, and code that reaches
    in to rebuild a path string by hand is exactly what asset
    renames used to rot. Nothing accepts such a string any more
    (see the ap*get bindings), so reaching in has no destination.
    """

    __slots__ = ('_apverid', '_name', *IO_SLOTS)

    _apverid: Annotated[str, IOAttrs('a')]
    _name: Annotated[str, IOAttrs('n')]


@ioprepped
@dataclass
class SoundSpec:
    """A language-independent reference to a sound in an asset-package.

    Identity is a package version plus the sound's logical
    path within it (e.g. ``audio/swish``); the engine resolves the
    qualified ``<apverid>:<name>`` form.

    Both parts are **private**: a spec is produced by a generated
    wrapper module and consumed as a whole, and code that reaches
    in to rebuild a path string by hand is exactly what asset
    renames used to rot. Nothing accepts such a string any more
    (see the ap*get bindings), so reaching in has no destination.
    """

    __slots__ = ('_apverid', '_name', *IO_SLOTS)

    _apverid: Annotated[str, IOAttrs('a')]
    _name: Annotated[str, IOAttrs('n')]


@ioprepped
@dataclass
class CubeMapTextureSpec:
    """A language-independent reference to a cube-map texture.

    Identity is a package version plus the cube map's logical path
    within it (e.g. ``textures/reflection_sharp``); the engine
    resolves the qualified ``<apverid>:<name>`` form.

    Both parts are **private**; see :class:`TextureSpec` for why.

    A distinct type from :class:`TextureSpec` deliberately: cube maps
    share the 2D textures' logical-path namespace and delivery bucket
    (asset-packages decision #24) but load through a different engine
    call producing a different texture type, and the engine's texture
    registry does not type-check cache hits -- so mixing the two up
    must be a *static* error at the handle tier, not a silent
    wrong-type asset at draw time.
    """

    __slots__ = ('_apverid', '_name', *IO_SLOTS)

    _apverid: Annotated[str, IOAttrs('a')]
    _name: Annotated[str, IOAttrs('n')]


@ioprepped
@dataclass
class CollisionMeshSpec:
    """A language-independent reference to a collision-mesh in a package.

    Identity is a package version plus the collision-mesh's logical
    path within it (e.g. ``meshes/courtyard_level_collide``); the
    engine resolves the qualified ``<apverid>:<name>`` form.

    Both parts are **private**; see :class:`TextureSpec` for why.

    Collision meshes are a scene-only kind (physics; they ride the
    flavor-invariant ``constant`` bucket -- asset-packages decision
    #26), so nothing server-side emits one. The type exists so the
    scene wrapper's handle leaves stay kind-distinct like every
    other kind.
    """

    __slots__ = ('_apverid', '_name', *IO_SLOTS)

    _apverid: Annotated[str, IOAttrs('a')]
    _name: Annotated[str, IOAttrs('n')]
