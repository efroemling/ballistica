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

    ``name`` is the texture's logical path within the package (e.g.
    ``textures/zoe_icon``). The engine resolves the qualified form
    ``<apverid>:<name>``.
    """

    __slots__ = ('apverid', 'name', *IO_SLOTS)

    apverid: Annotated[str, IOAttrs('a')]
    name: Annotated[str, IOAttrs('n')]


@ioprepped
@dataclass
class MeshSpec:
    """A language-independent reference to a mesh in an asset-package.

    ``name`` is the mesh's logical path within the package (e.g.
    ``meshes/box``). The engine resolves the qualified form
    ``<apverid>:<name>``.
    """

    __slots__ = ('apverid', 'name', *IO_SLOTS)

    apverid: Annotated[str, IOAttrs('a')]
    name: Annotated[str, IOAttrs('n')]


@ioprepped
@dataclass
class SoundSpec:
    """A language-independent reference to a sound in an asset-package.

    ``name`` is the sound's logical path within the package (e.g.
    ``audio/swish``). The engine resolves the qualified form
    ``<apverid>:<name>``.
    """

    __slots__ = ('apverid', 'name', *IO_SLOTS)

    apverid: Annotated[str, IOAttrs('a')]
    name: Annotated[str, IOAttrs('n')]


@ioprepped
@dataclass
class CollisionMeshSpec:
    """A language-independent reference to a collision-mesh in a package.

    ``name`` is the collision-mesh's logical path within the package
    (e.g. ``meshes/courtyard_level_collide``). The engine resolves the
    qualified form ``<apverid>:<name>``.

    Collision meshes are a scene-only kind (physics; they ride the
    flavor-invariant ``constant`` bucket -- asset-packages decision
    #26), so nothing server-side emits one. The type exists so the
    scene wrapper's verified-spec leaves stay kind-distinct like every
    other kind.
    """

    __slots__ = ('apverid', 'name', *IO_SLOTS)

    apverid: Annotated[str, IOAttrs('a')]
    name: Annotated[str, IOAttrs('n')]
