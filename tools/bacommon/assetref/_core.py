# Released under the MIT License. See LICENSE for details.
#
"""Core types for language-independent asset references.

An asset reference is a minimal, language-independent pointer to a single
asset within a published asset-package-version: its exact ``apverid`` plus
the asset's logical ``name`` (e.g. ``textures/zoe_icon``). It carries no
asset *data* -- the server (bamaster) only ever holds the reference; the
client resolves the package and loads the actual asset for display.

Each asset kind gets its own type (:class:`TextureRef`, :class:`MeshRef`,
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

from efro.dataclassio import ioprepped, IOAttrs


@ioprepped
@dataclass
class TextureRef:
    """A language-independent reference to a texture in an asset-package.

    ``name`` is the texture's logical path within the package (e.g.
    ``textures/zoe_icon``). The engine resolves the qualified form
    ``<apverid>:<name>``.
    """

    apverid: Annotated[str, IOAttrs('a')]
    name: Annotated[str, IOAttrs('n')]


@ioprepped
@dataclass
class MeshRef:
    """A language-independent reference to a mesh in an asset-package.

    ``name`` is the mesh's logical path within the package (e.g.
    ``meshes/box``). The engine resolves the qualified form
    ``<apverid>:<name>``.
    """

    apverid: Annotated[str, IOAttrs('a')]
    name: Annotated[str, IOAttrs('n')]
