# Released under the MIT License. See LICENSE for details.
#
"""One traversal of a doc-ui page's language-strings and asset refs.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.

Several things need to visit every string slot or every asset
reference in a page: the client resolves the packages they name before
rendering, the server rewrites them to their indexed wire forms, and so
on. Each of those used to walk the page itself.

That went wrong the same way three times. Every walk matched
decorations with an ``isinstance`` chain and no final else, so a
decoration type a given walk had not been taught about contributed
nothing and the walk returned a plausible answer -- silently short of
the truth. Adding a (since-retired) frame decoration missed three of
the four places that needed it.

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
import bacommon.depiction as bdep
from bacommon.assetspec import AssetBucketKind

# Short local names -- these appear on nearly every asset slot below
# and the long form pushes the lines past readable.
_TEX = AssetBucketKind.TEXTURES
_MESH = AssetBucketKind.MESHES

if TYPE_CHECKING:
    from typing import Callable, Iterator

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

    #: The slot-level wrappers :func:`walk_page` hands to
    #: :func:`_walk_decorations`. Unlike the public visitors these
    #: always return a value (the original when the visitor declined),
    #: so callers can assign the result straight into a slot.
    type LangStrSlot = Callable[[LangStrRef], LangStrRef]
    type AssetRefSlot = Callable[
        ['AssetRef | None', AssetBucketKind], 'AssetRef | None'
    ]


def _walk_depiction(depiction: bdep.Depiction | None) -> None:
    """Visit a depiction (a decoration's, a button's, or a page's viewer).

    Nothing holds anything for either callback: depictions are
    self-sufficient, so their asset refs are acquired in the background
    behind a standin and never added to (or indexed against) the page's
    packages. This exists so a new kind has to decide whether that
    still holds (the ``assert_never``).
    """
    if depiction is None:
        return
    t = bdep.DepictionTypeID
    typeid = depiction.get_type_id()
    if typeid is t.UNKNOWN:
        pass
    elif typeid is t.IMAGE:
        # Its textures are fetched on demand, never page packages --
        # full specs, or indices into its *own* domain (its pk/dg;
        # see ImageDepiction), never the page's -- so deliberately
        # not visited.
        pass
    elif typeid is t.CHARACTER_ICON:
        pass
    elif typeid is t.NAME:
        pass
    elif typeid is t.CHARACTER_VIEWER:
        pass
    else:
        assert_never(typeid)


def _walk_decorations(
    decos: list[dui2.Decoration] | None,
    lstr: 'LangStrSlot',
    ref: 'AssetRefSlot',
) -> None:
    """Visit one decoration list.

    Module level rather than nested inside :func:`walk_page`. Should
    decorations ever nest again, keep it that way: a *self-recursive*
    nested function holds itself in its own closure cell -- a reference
    cycle minted on every call, which pins the visitor closures (and
    whatever they capture, e.g. an index context) until a cyclic-gc
    pass runs.
    """
    for deco in decos or []:
        dectypeid = deco.get_type_id()

        if dectypeid is dui2.DecorationTypeID.TEXT:
            assert isinstance(deco, dui2.Text)
            deco.text = lstr(deco.text)
            for timg in (deco.image_left, deco.image_right):
                if timg is not None:
                    timg.texture = ref(  # type: ignore[assignment]
                        timg.texture, _TEX
                    )

        elif dectypeid is dui2.DecorationTypeID.IMAGE:
            assert isinstance(deco, dui2.Image)
            # Note the narrowing casts: the visitor is typed over
            # the union, while each slot holds one specific kind.
            deco.texture = ref(deco.texture, _TEX)  # type: ignore[assignment]
            deco.tint_texture = ref(  # type: ignore[assignment]
                deco.tint_texture, _TEX
            )
            deco.mask_texture = ref(  # type: ignore[assignment]
                deco.mask_texture, _TEX
            )
            deco.mesh_opaque = ref(  # type: ignore[assignment]
                deco.mesh_opaque, _MESH
            )
            deco.mesh_transparent = ref(  # type: ignore[assignment]
                deco.mesh_transparent, _MESH
            )

        elif dectypeid is dui2.DecorationTypeID.DEPICTION:
            assert isinstance(deco, dui2.Depiction)
            _walk_depiction(deco.depiction)

        elif dectypeid is dui2.DecorationTypeID.UNKNOWN:
            # A decoration from a newer producer. Nothing here can
            # be said about its contents, so there is nothing to do
            # but leave it be.
            pass

        else:
            # The point of this whole module: a new decoration type
            # fails here, at build time, in one place.
            assert_never(dectypeid)


def flatten_action(action: dui2.Action | None) -> 'Iterator[dui2.Action]':
    """Yield an action and, for a menu, the actions of its items.

    Menus don't nest (a client refuses to open one from a menu item),
    so a menu sitting in a menu item is yielded but not descended into.
    """
    if action is None:
        return
    yield action
    if isinstance(action, dui2.Menu):
        for item in action.items:
            if item.action is not None:
                yield item.action


def page_actions(page: dui2.Page) -> 'Iterator[dui2.Action]':
    """Yield every action in a page, menu items' included.

    For consumers that care about what actions carry (client-effects,
    state assignments) rather than where they hang.
    """
    for row in dui2.all_rows(page.rows):
        if dui2.is_input_row(row):
            yield from flatten_action(row.on_change)
            if isinstance(row, dui2.TextInputRow):
                yield from flatten_action(row.on_submit)
            elif isinstance(row, dui2.SliderRow):
                yield from flatten_action(row.on_drag)
        elif isinstance(row, dui2.ButtonControlRow):
            yield from flatten_action(row.button.action)
        elif isinstance(row, dui2.ButtonRow):
            for button in row.buttons:
                yield from flatten_action(button.action)


def _walk_control_row(
    row: dui2.AnyControlRow,
    lstr: 'LangStrSlot',
    action: 'Callable[[dui2.Action | None], None]',
    button: 'Callable[[dui2.Button], None]',
) -> None:
    """Visit a control row's strings and actions (see :func:`walk_page`)."""
    if row.title is not None:
        row.title = lstr(row.title)
    if row.subtitle is not None:
        row.subtitle = lstr(row.subtitle)
    if row.label is not None:
        row.label = lstr(row.label)
    if row.footnote is not None:
        row.footnote = lstr(row.footnote)
    if isinstance(row, dui2.ButtonControlRow):
        button(row.button)
        return
    if isinstance(row, dui2.TextInputRow):
        if row.description is not None:
            row.description = lstr(row.description)
        action(row.on_submit)
    elif isinstance(row, dui2.ChoiceRow):
        for choice in row.choices:
            choice.label = lstr(choice.label)
    action(row.on_change)
    if isinstance(row, dui2.SliderRow):
        action(row.on_drag)


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

    Covers titles, subtitles, button labels, control-row labels and
    menu item labels; text and image
    decorations wherever they appear, including a text's end images;
    button textures and icons. A button's immediate client-effects
    are handed to :func:`bacommon.clienteffect.walk_effects`, which
    owns that vocabulary and is exhaustive over it the same way this
    is over decorations -- so their strings *and* their asset refs
    are both covered. Depictions (in decorations, and the page's
    viewer) are visited but hold nothing for either callback: they are
    self-sufficient and deliberately outside the page's manifest.
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
        # asset slot for any read-only visitor, ``collect_apvernums``
        # included, which stripped the textures off every v2 page
        # during resolve.
        return val if out is None else out

    def _decos(decos: list[dui2.Decoration] | None) -> None:
        _walk_decorations(decos, _lstr, _ref)

    def _action(action: dui2.Action | None) -> None:
        for act in flatten_action(action):
            acttypeid = act.get_type_id()

            if acttypeid is dui2.ActionTypeID.LOCAL:
                assert isinstance(act, dui2.Local)
                # Delegate rather than reaching in for one field. This
                # used to handle ScreenMessageV2's string and ignore
                # PlaySoundV2's sound, which made the page/effects
                # split arbitrary and would have left indexed sounds
                # un-de-indexed.
                clfx.walk_effects(
                    act.immediate_client_effects,
                    langstr=langstr,
                    assetref=assetref,  # type: ignore[arg-type]
                )

            elif acttypeid is dui2.ActionTypeID.MENU:
                assert isinstance(act, dui2.Menu)
                # (Its items' actions come through flatten_action.)
                for item in act.items:
                    item.label = _lstr(item.label)

            elif acttypeid is dui2.ActionTypeID.POPUP_TEXT:
                assert isinstance(act, dui2.PopupText)
                act.text = _lstr(act.text)

            elif (
                acttypeid is dui2.ActionTypeID.BROWSE
                or acttypeid is dui2.ActionTypeID.REPLACE
                or acttypeid is dui2.ActionTypeID.UNKNOWN
            ):
                # Nothing to visit: requests hold no strings or refs,
                # and nothing can be said about an action from a newer
                # producer.
                pass

            else:
                # As with decorations: a new action type fails here,
                # at build time, in one place.
                assert_never(acttypeid)

    page.title = _lstr(page.title)
    _walk_depiction(page.viewer)

    def _bands(
        row: dui2.ButtonRow | dui2.AnyControlRow | dui2.Section,
    ) -> None:
        # Every row type has a header and a footer band.
        _decos(row.header_decorations_left)
        _decos(row.header_decorations_center)
        _decos(row.header_decorations_right)
        _decos(row.footer_decorations_left)
        _decos(row.footer_decorations_center)
        _decos(row.footer_decorations_right)

    def _button(button: dui2.Button) -> None:
        if button.label is not None:
            button.label = _lstr(button.label)
        button.texture = _ref(button.texture, _TEX)  # type: ignore[assignment]
        button.icon = _ref(button.icon, _TEX)  # type: ignore[assignment]
        _walk_depiction(button.depiction)
        _decos(button.decorations)
        _action(button.action)

    # (A section's rows come right after it.)
    for row in dui2.all_rows(page.rows):
        if dui2.is_control_row(row):
            _bands(row)
            _walk_control_row(row, _lstr, _action, _button)
            continue
        if isinstance(row, dui2.Section):
            _bands(row)
            if row.backing is not None and row.backing.texture is not None:
                row.backing.texture = _ref(  # type: ignore[assignment]
                    row.backing.texture, _TEX
                )
            if row.title is not None:
                row.title = _lstr(row.title)
            if row.subtitle is not None:
                row.subtitle = _lstr(row.subtitle)
            if row.footnote is not None:
                row.footnote = _lstr(row.footnote)
            continue
        if not isinstance(row, dui2.ButtonRow):
            continue
        if row.title is not None:
            row.title = _lstr(row.title)
        if row.subtitle is not None:
            row.subtitle = _lstr(row.subtitle)
        if row.footnote is not None:
            row.footnote = _lstr(row.footnote)
        _bands(row)

        for button in row.buttons:
            _button(button)
