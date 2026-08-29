# Released under the MIT License. See LICENSE for details.
#
"""The producer-side display-item: what to show, and in what style.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.

A display-item is a request -- *show this thing in this style, in these
bounds* -- which is what it has always been. What changes here is what
that request turns into. It can depict itself two ways:

* ``DisplayItem.to_frame`` -- a :class:`~bacommon.docui.v2.Frame`
  carrying the depiction, for clients that understand frames.
* ``DisplayItem.to_legacy`` -- a
  :class:`~bacommon.docui.v2.DisplayItem` decoration naming the item,
  for clients that predate them and must derive the drawing themselves.

Both describe the same picture; which one a producer sends is a
question about the audience, not about the item. Serving the two by
client build is the last step of the migration, not this one.

The depiction lives here rather than in either host so there is exactly
one of it -- the whole point of the preceding work was collapsing two
renderers into one, and a second copy on the producer side would undo
that. What each host must supply is gathered into
``DepictionAssets``.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

from efro.util import pairs_from_flat

import bacommon.legacydisplayitem as lditm
import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue

if TYPE_CHECKING:
    from bacommon.assetspec import TextureSpec
    from bacommon.classic import ClassicChestAppearance


#: First engine build that renders doc-ui frames. Below this a
#: producer must send the legacy display-item decoration instead and
#: let the client derive the drawing, since a frame would arrive as an
#: unrecognized decoration and draw nothing at all.
FRAME_DEPICTION_MIN_BUILD = 22992


@dataclass(frozen=True)
class DepictionAssets:
    """What a host must lend a depiction to draw itself.

    Everything here is something ``bacommon`` cannot reach on its own:
    each host keeps its asset-reference wrappers in its own place (the
    client's ``bauiv1._classicassets``, the master server's vendored
    ``bamaster.assets.baclassicassets``), and the chest appearance
    colors live with the client's chest code.

    Making these parameters rather than imports is what lets one
    depiction serve both hosts. Note there is deliberately nothing here
    that a server could not supply -- text measurement in particular,
    which the layout used to need and pointedly no longer does.
    """

    white: TextureSpec
    coin: TextureSpec
    tickets: TextureSpec
    tickets_purple: TextureSpec
    chest_icon: TextureSpec
    chest_icon_tint: TextureSpec

    #: Per-appearance ``(tint, tint2)``. Appearances absent here get
    #: :attr:`chest_tint_default` -- several of them (UNKNOWN, DEFAULT,
    #: L1) have no entry and rely on that.
    chest_tints: dict[
        ClassicChestAppearance,
        tuple[tuple[float, float, float], tuple[float, float, float]],
    ]

    #: ``(tint, tint2)`` for an appearance with no entry above.
    chest_tint_default: tuple[
        tuple[float, float, float], tuple[float, float, float]
    ]


@dataclass
class DisplayItem:
    """Something to show, and how much room to use showing it.

    Mirrors :class:`~bacommon.docui.v2.DisplayItem` field for field, so
    a producer can hand either to a call site that lays out
    decorations.

    :meta private:
    """

    wrapper: lditm.Wrapper
    position: tuple[float, float]
    size: tuple[float, float]
    style: dui2.DisplayItemStyle = dui2.DisplayItemStyle.FULL
    text_color: tuple[float, float, float] | None = None
    highlight: bool = True
    depth_range: tuple[float, float] | None = None
    debug: bool = False

    def to_legacy(self) -> dui2.DisplayItem:
        """Depict as a decoration naming the item, for older clients.

        The client derives the drawing from the item type, which is
        why it can only draw types its build already knows.
        """
        return dui2.DisplayItem(
            wrapper=self.wrapper,
            position=self.position,
            size=self.size,
            style=self.style,
            text_color=self.text_color,
            highlight=self.highlight,
            depth_range=self.depth_range,
            debug=self.debug,
        )

    def depict(
        self, assets: DepictionAssets, for_build: int | None
    ) -> dui2.Decoration:
        """Depict for a client of this build, whichever form it reads.

        ``for_build`` of None means the audience is unknown, which is
        treated as old: the legacy decoration renders on every build,
        while a frame sent to a client that predates them draws
        nothing.
        """
        if for_build is not None and for_build >= FRAME_DEPICTION_MIN_BUILD:
            return self.to_frame(assets)
        return self.to_legacy()

    def to_frame(self, assets: DepictionAssets) -> dui2.Frame:
        """Depict as a frame carrying the drawing itself.

        An item type this producer does not recognize still gets the
        wrapper's baked description drawn, exactly as the legacy path
        does. Callers that would rather draw nothing should decide that
        for themselves: these wrappers can carry types newer than the
        code depicting them, and silently dropping one is how a reward
        goes missing.
        """
        item = self.wrapper.item
        itemtype = item.get_type_id()

        aspect_ratio, compact, icon = _style_params(self.style)

        # Fit our aspect ratio inside the provided bounds.
        if self.size[0] * aspect_ratio > self.size[1]:
            height = self.size[1]
            width = height / aspect_ratio
        else:
            width = self.size[0]
            height = width * aspect_ratio

        # Draw our bounds in debug mode (or if we're a test-item).
        decorations: list[dui2.Decoration] = (
            _debug_bounds(assets, self.size, width, height)
            if self.debug or itemtype is lditm.ItemTypeID.TEST
            else []
        )

        if itemtype is lditm.ItemTypeID.CHEST:
            decorations.append(
                _chest_image(
                    assets,
                    item,
                    width,
                    compact=compact,
                    icon=icon,
                    depth_range=self.depth_range,
                )
            )
            return dui2.Frame(
                decorations=decorations,
                position=self.position,
                highlight=self.highlight,
            )

        layout = _text_and_image_layout(
            assets, itemtype, item, width, compact=compact, icon=icon
        )

        # A layout that could not place its pieces itself hands them
        # to a sized frame, which centers and fits them client-side.
        fitted: list[dui2.Decoration] = []
        target = decorations if layout.fit_size is None else fitted

        if layout.imgtex is not None:
            target.append(
                dui2.Image(
                    texture=layout.imgtex,
                    position=(layout.img_x_offs, layout.img_y_offs),
                    size=(layout.imgsize, layout.imgsize),
                    depth_range=self.depth_range,
                )
            )

        if layout.show_text:
            target.append(
                dui2.Text(
                    text=_item_text(self.wrapper, layout.text),
                    position=(layout.text_x_offs, layout.text_y_offs),
                    # A zero max-width/height disables that constraint,
                    # which is what the legacy path's None means.
                    size=(layout.text_max_width or 0.0, 0.0),
                    h_align=layout.text_h_align,
                    scale=width * layout.text_mult,
                    color=(
                        (1.0, 1.0, 1.0, 1.0)
                        if self.text_color is None
                        else (*self.text_color, 1.0)
                    ),
                    flatness=1.0,
                    shadow=1.0,
                    depth_range=self.depth_range,
                )
            )

        if layout.fit_size is not None:
            decorations.append(
                dui2.Frame(
                    decorations=fitted,
                    position=(0.0, 0.0),
                    size=layout.fit_size,
                    highlight=self.highlight,
                    # Carry debug in so the fit box is visible next to
                    # the item's own bounds, which is where you would
                    # look to see whether centering landed.
                    debug=self.debug,
                )
            )

        return dui2.Frame(
            decorations=decorations,
            position=self.position,
            highlight=self.highlight,
        )


def _style_params(style: dui2.DisplayItemStyle) -> tuple[float, bool, bool]:
    """Return (aspect-ratio, compact, icon) for a display-item style."""
    if style is dui2.DisplayItemStyle.FULL:
        # Bit less tall than wide (graphic centric).
        return 0.75, False, False
    if style is dui2.DisplayItemStyle.COMPACT:
        # Significantly wider (text centric).
        return 0.5, True, False
    if style is dui2.DisplayItemStyle.ICON:
        # Square.
        return 1.0, False, True

    # Make sure we cover all possibilities.
    assert_never(style)


def _debug_bounds(
    assets: DepictionAssets,
    size: tuple[float, float],
    width: float,
    height: float,
) -> list[dui2.Decoration]:
    """Return the provided-bounds and constrained-bounds debug rects."""
    return [
        dui2.Image(
            texture=assets.white,
            position=(0.0, 0.0),
            size=size,
            color=(1, 1, 0, 0.1),
        ),
        dui2.Image(
            texture=assets.white,
            position=(0.0, 0.0),
            size=(width, height),
            color=(1, 0.5, 0, 0.2),
        ),
    ]


def _chest_image(
    assets: DepictionAssets,
    item: lditm.Item,
    width: float,
    *,
    compact: bool,
    icon: bool,
    depth_range: tuple[float, float] | None,
) -> dui2.Image:
    """Return the image depicting a chest item."""
    from bacommon.classic import ClassicChestDisplayItem

    assert isinstance(item, ClassicChestDisplayItem)

    tint, tint2 = assets.chest_tints.get(
        item.appearance, assets.chest_tint_default
    )
    c_size = width * (0.66 if compact else 1.05 if icon else 0.83)
    return dui2.Image(
        texture=assets.chest_icon,
        tint_texture=assets.chest_icon_tint,
        position=(0.0, 0.0),
        size=(c_size, c_size),
        tint_color=tint,
        tint2_color=tint2,
        depth_range=depth_range,
    )


@dataclass
class _Layout:
    """Where an item's image and text go, in unscaled bounds units."""

    imgtex: TextureSpec | None = None
    imgsize: float = 0.0
    img_x_offs: float = 0.0
    img_y_offs: float = 0.0
    show_text: bool = True
    text: str | None = None  # Uses the baked description if None.
    text_mult: float = 0.006
    text_x_offs: float = 0.0
    text_y_offs: float = 0.0
    text_max_width: float | None = None
    text_h_align: dui2.HAlign = dui2.HAlign.CENTER

    #: When set, wrap the image and text in a frame of this size so the
    #: client centers and fits them (it can measure text; we cannot).
    fit_size: tuple[float, float] | None = None


def _text_and_image_layout(
    assets: DepictionAssets,
    itemtype: lditm.ItemTypeID,
    item: lditm.Item,
    width: float,
    *,
    compact: bool,
    icon: bool,
) -> _Layout:
    """Lay out the image and text for the non-chest item types."""
    out = _Layout(
        imgsize=width * (0.5 if compact else 1.0 if icon else 0.33),
        text_max_width=width * 0.9,
    )

    if itemtype is lditm.ItemTypeID.TEST:
        assert isinstance(item, lditm.Test)
        # Nothing to draw here; this type exists to enable debug
        # drawing.
        if icon or compact:
            out.text_mult = 0.02  # Very large text.
        return out

    if itemtype is lditm.ItemTypeID.UNKNOWN:
        assert isinstance(item, lditm.Unknown)
        # All we have is the wrapper's baked description, so draw that.
        if icon:
            out.text_mult = 0.02  # Very large text.
        return out

    if itemtype is lditm.ItemTypeID.TOKENS:
        assert isinstance(item, lditm.Tokens)
        out.imgtex = assets.coin
        count = item.count
    elif itemtype is lditm.ItemTypeID.TICKETS:
        assert isinstance(item, lditm.Tickets)
        out.imgtex = assets.tickets
        count = item.count
    elif itemtype is lditm.ItemTypeID.TICKETS_PURPLE:
        assert isinstance(item, lditm.PurpleTickets)
        out.imgtex = assets.tickets_purple
        count = item.count
    elif itemtype is lditm.ItemTypeID.CHEST:
        # Answered before we are reached; naming it keeps the
        # assert_never below meaning "a type nobody has handled".
        raise RuntimeError(f'Unexpected item type {itemtype}.')
    else:
        # Make sure we cover all possibilities.
        assert_never(itemtype)

    if compact:
        out.text = str(count)
        _lay_out_compact_currency(out, width)
    elif icon:
        out.img_y_offs = 0.0
        out.show_text = False
    else:
        out.img_y_offs = width * 0.11
        out.text_y_offs = width * -0.15

    return out


def _lay_out_compact_currency(out: _Layout, width: float) -> None:
    """Place a count beside its currency image, fitted to the bounds.

    Deliberately does **not** measure the text. Centering the count and
    its image as a pair needs the count's rendered width, which only
    the client knows -- a producer that had to measure could not run on
    a server at all.

    So it does not centre them here. The two are authored side by side
    in their own local coordinates and handed to a *sized* frame, which
    measures and centres them at prep time (see
    :attr:`bacommon.docui.v2.Frame.size`). The producer states the
    composition; the client resolves it.

    Overflow rides the same mechanism: the frame shrinks the pair to
    fit its box, exactly as the old measuring code shrank both parts.
    """
    assert out.text is not None
    out.text_mult = 0.01
    out.fit_size = (width * 0.95, width * 0.5)

    # Count first, image immediately after it, in local units. Nothing
    # here compensates for anything: the frame centers the true extent
    # of what it is given.
    #
    # The old code carried an `imgamt = 0.85` here, counting only 85%
    # of the image when centering, because the currency art has a
    # transparent margin and its texture box is wider than the visible
    # coin. That made the drawn result sit fractionally off-center and
    # the pair fractionally tighter. Both are art facts leaking into
    # layout; if the margin ever wants correcting, the honest place is
    # the image's declared bounds, not a constant here.
    out.text_h_align = dui2.HAlign.RIGHT
    out.text_x_offs = 0.0
    out.text_max_width = None  # The frame handles fitting.

    out.img_x_offs = out.imgsize * 0.5


def _item_text(wrapper: lditm.Wrapper, text: str | None) -> LangStrSpecValue:
    """Return the language-string for an item's text.

    ``text`` overrides the item's description when the depiction wants
    something else (a bare count, say).

    The description case bakes the wrapper's English rather than
    referencing an asset-package string, because the strings it draws
    on live in the legacy ``displayItemNames`` translate category and
    are deliberately not being ported -- they die with the legacy
    renderer. That makes this exactly as localized as the baked
    description it comes from, which is the point of that fallback but
    not good enough long-term; a real producer wants proper string
    references here.
    """
    if text is not None:
        return LangStrSpecValue.literal(text)

    out = wrapper.description
    for key, val in pairs_from_flat(wrapper.description_subs or []):
        out = out.replace(key, val)
    return LangStrSpecValue.literal(out)
