# Released under the MIT License. See LICENSE for details.
#
"""One traversal of a doc-ui page's language-strings and asset refs.

Several things need to visit every string slot or every asset
reference in a page: the client resolves the packages they name before
rendering, the server rewrites them to their indexed wire forms, and so
on. Each of those used to walk the page itself.

That went wrong the same way three times. Every walk matched
decorations with an ``isinstance`` chain and no final else, so a
decoration type a given walk had not been taught about contributed
nothing and the walk returned a plausible answer -- silently short of
the truth. Adding :class:`~bacommon.docui.v2.Frame` missed three of the
four places that needed it.

So the traversal lives here once, and it dispatches on
:class:`~bacommon.docui.v2.DecorationTypeID` with ``assert_never`` on
the end. A new decoration type is now a type error in a single file
rather than a silent omission in an unknown number of them.

Callbacks may return a replacement value (or ``None`` to leave a slot
alone), which is what lets one traversal serve both the read-only
consumers and the ones that rewrite in place.
"""

from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2
from bacommon.assetspec import AssetBucketKind

# Short local names -- these appear on nearly every asset slot below
# and the long form pushes the lines past readable.
_TEX = AssetBucketKind.TEXTURES
_MESH = AssetBucketKind.MESHES

if TYPE_CHECKING:
    from typing import Callable

    from bacommon.langstr import LangStrSpec
    from bacommon.assetspec import TextureSpec, MeshSpec

    #: Anything in a page that names an asset in a package: a spec, or
    #: the flat integer index that addresses the same asset through
    #: ``Response.packages``.
    type AssetRef = TextureSpec | MeshSpec | int

    #: A page's string slot: a spec, or the flat integer index that
    #: addresses the same string through ``Response.packages``.
    type LangStrRef = LangStrSpec | int

    #: Return a replacement, or None to leave the slot as it is.
    type LangStrVisitor = Callable[[LangStrRef], 'LangStrRef | None']

    #: Visits an asset slot. Receives the slot's **bucket kind** as well
    #: as its value, because an integer index is only meaningful
    #: alongside the kind -- the schema fixes it per slot (a texture
    #: slot holds a texture), and nothing about the integer itself says
    #: which domain it belongs to.
    type AssetRefVisitor = Callable[
        [AssetRef, AssetBucketKind], 'AssetRef | None'
    ]


def walk_page(
    page: dui2.Page,
    *,
    langstr: 'LangStrVisitor | None' = None,
    assetref: 'AssetRefVisitor | None' = None,
) -> None:
    """Visit every language-string and asset ref in a page.

    Either callback may return a replacement for what it was handed, in
    which case the page is updated in place; returning ``None`` leaves
    the slot alone. A consumer that only reads returns ``None`` always.

    Covers titles, subtitles and button labels; text and image
    decorations wherever they appear, including nested inside frames;
    button textures and icons. A button's immediate client-effects
    are handed to :func:`bacommon.clienteffect.walk_effects`, which
    owns that vocabulary and is exhaustive over it the same way this
    is over decorations -- so their strings *and* their asset refs
    are both covered.
    """
    import bacommon.clienteffect as clfx

    def _lstr(val: 'LangStrRef') -> 'LangStrRef':
        if langstr is None:
            return val
        out = langstr(val)
        return val if out is None else out

    def _ref(
        val: 'AssetRef | None', kind: 'AssetBucketKind'
    ) -> 'AssetRef | None':
        if assetref is None or val is None:
            return val
        out = assetref(val, kind)
        # None means "leave the slot alone", exactly as for strings --
        # NOT "set the slot to None". Getting this wrong nulled every
        # asset slot for any read-only visitor, ``collect_apverids``
        # included, which stripped the textures off every v2 page
        # during resolve.
        return val if out is None else out

    def _decos(decos: list[dui2.Decoration] | None) -> None:
        for deco in decos or []:
            dectypeid = deco.get_type_id()

            if dectypeid is dui2.DecorationTypeID.TEXT:
                assert isinstance(deco, dui2.Text)
                deco.text = _lstr(deco.text)

            elif dectypeid is dui2.DecorationTypeID.IMAGE:
                assert isinstance(deco, dui2.Image)
                # Note the narrowing casts: the visitor is typed over
                # the union, while each slot holds one specific kind.
                deco.texture = _ref(  # type: ignore[assignment]
                    deco.texture, _TEX
                )
                deco.tint_texture = _ref(  # type: ignore[assignment]
                    deco.tint_texture, _TEX
                )
                deco.mask_texture = _ref(  # type: ignore[assignment]
                    deco.mask_texture, _TEX
                )
                deco.mesh_opaque = _ref(  # type: ignore[assignment]
                    deco.mesh_opaque, _MESH
                )
                deco.mesh_transparent = _ref(  # type: ignore[assignment]
                    deco.mesh_transparent, _MESH
                )

            elif dectypeid is dui2.DecorationTypeID.FRAME:
                assert isinstance(deco, dui2.Frame)
                # A frame's children are page content like any other.
                # Recurses, since frames nest.
                _decos(deco.decorations)

            elif dectypeid is dui2.DecorationTypeID.DISPLAY_ITEM:
                # Names an item rather than describing it, so it holds
                # no strings or refs of its own -- the client derives
                # them. Legacy; producers send frames now.
                pass

            elif dectypeid is dui2.DecorationTypeID.UNKNOWN:
                # A decoration from a newer producer. Nothing here can
                # be said about its contents, so there is nothing to do
                # but leave it be.
                pass

            else:
                # The point of this whole module: a new decoration type
                # fails here, at build time, in one place.
                assert_never(dectypeid)

    page.title = _lstr(page.title)

    for row in page.rows:
        if not isinstance(row, dui2.ButtonRow):
            continue
        if row.title is not None:
            row.title = _lstr(row.title)
        if row.subtitle is not None:
            row.subtitle = _lstr(row.subtitle)
        _decos(row.header_decorations_left)
        _decos(row.header_decorations_center)
        _decos(row.header_decorations_right)

        for button in row.buttons:
            if button.label is not None:
                button.label = _lstr(button.label)
            button.texture = _ref(  # type: ignore[assignment]
                button.texture, _TEX
            )
            button.icon = _ref(button.icon, _TEX)  # type: ignore[assignment]
            _decos(button.decorations)

            if isinstance(button.action, dui2.Local):
                # Delegate rather than reaching in for one field. This
                # used to handle ScreenMessageV2's string and ignore
                # PlaySoundV2's sound, which made the page/effects split
                # arbitrary and would have left indexed sounds
                # un-de-indexed.
                clfx.walk_effects(
                    button.action.immediate_client_effects,
                    langstr=langstr,
                    assetref=assetref,  # type: ignore[arg-type]
                )
