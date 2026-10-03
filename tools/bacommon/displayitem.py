# Released under the MIT License. See LICENSE for details.
#
"""The producer-side display-item: what to show, and in what style.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.

A display-item is a request -- *show this thing in this style, in these
bounds* -- which is what it has always been. It turns into plain doc-ui
decorations (``DisplayItem.decorations``), so the client needs no
knowledge of item types to draw one: new types need no client update.
The same decorations draw into a doc-ui page or, via the doc-ui prep
code, into any plain container widget.

The depiction lives here rather than in either host so there is exactly
one of it, serving both the client and the master server. What each
host must supply is gathered into ``DepictionAssets``.
"""

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

from efro.util import pairs_from_flat

import bacommon.legacydisplayitem as lditm
import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue

if TYPE_CHECKING:
    from bacommon.assetspec import TextureSpec
    from bacommon.classic import ClassicChestAppearance, ChestTints


#: Layout boxes for the currency art beside a count, as (left, bottom,
#: right, top) fractions trimmed from each edge (see
#: :attr:`bacommon.docui.v2.TextImage.insets`). Vertically these trim
#: all of the art's transparent padding, so it centers on the text
#: line; horizontally they leave 15% of the image's width as padding on
#: each side, which is the spacing from the count (the tickets have
#: less padding than that, hence negative insets). Based on the art's
#: measured padding (2026-09-30: coin ~(0.17, 0.12, 0.16, 0.11),
#: counting its faint glow as empty; tickets ~(0.08, 0.09, 0.06,
#: 0.05)), so revisit if the art changes. They belong with the
#: textures themselves eventually (see docs/initiatives/depictions.md).
_COIN_INSETS = (0.02, 0.12, 0.01, 0.11)
_TICKETS_INSETS = (-0.07, 0.09, -0.09, 0.05)


class DisplayItemStyle(Enum):
    """Styles a display-item can be drawn in.

    :meta private:
    """

    #: Fully conveys what the item is. Draws in a 4x3 box and works
    #: best with large-ish displays.
    FULL = 'f'

    #: Fully conveys the item, condensed into a 2x1 box for small sizes.
    COMPACT = 'c'

    #: Graphics-only representation in a 1x1 box, for use alongside a
    #: textual description.
    ICON = 'i'


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

    #: Per-appearance tints (2 or 3; see
    #: :data:`bacommon.classic.ChestTints`). Appearances absent here
    #: get :attr:`chest_tint_default` -- several of them (UNKNOWN,
    #: DEFAULT, L1) have no entry and rely on that.
    chest_tints: dict[ClassicChestAppearance, ChestTints]

    #: Tints for an appearance with no entry above.
    chest_tint_default: ChestTints


@dataclass
class DisplayItem:
    """Something to show, and how much room to use showing it.

    :meta private:
    """

    wrapper: lditm.Wrapper
    position: tuple[float, float]
    size: tuple[float, float]
    style: DisplayItemStyle = DisplayItemStyle.FULL
    text_color: tuple[float, float, float] | None = None
    highlight: bool = True
    depth_range: tuple[float, float] | None = None
    debug: bool = False

    def decorations(self, assets: DepictionAssets) -> list[dui2.Decoration]:
        """Depict as plain doc-ui decorations, placed at our position.

        An item type this producer does not recognize still gets the
        wrapper's baked description drawn. Callers that would rather
        draw nothing should decide that for themselves: these wrappers
        can carry types newer than the code depicting them, and
        silently dropping one is how a reward goes missing.
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

        # Everything below is authored relative to the item's center;
        # this places it.
        px, py = self.position

        def _at(x: float, y: float) -> tuple[float, float]:
            return (px + x, py + y)

        # Draw our bounds in debug mode (or if we're a test-item).
        decorations: list[dui2.Decoration] = (
            _debug_bounds(assets, self.position, self.size, width, height)
            if self.debug or itemtype is lditm.ItemTypeID.TEST
            else []
        )

        if itemtype is lditm.ItemTypeID.CHEST:
            decorations.append(
                _chest_image(
                    assets,
                    item,
                    width,
                    position=self.position,
                    compact=compact,
                    icon=icon,
                    highlight=self.highlight,
                    depth_range=self.depth_range,
                )
            )
            return decorations

        layout = _text_and_image_layout(
            assets, itemtype, item, width, compact=compact, icon=icon
        )

        text_color = (
            (1.0, 1.0, 1.0, 1.0)
            if self.text_color is None
            else (*self.text_color, 1.0)
        )

        # A count beside its currency: one text carrying its image, so
        # the client can measure and center the pair (we can't; see
        # _lay_out_compact_currency).
        if layout.pair_size is not None:
            assert layout.imgtex is not None
            text_scale = width * layout.text_mult
            decorations.append(
                dui2.Text(
                    text=_item_text(self.wrapper, layout.text),
                    position=self.position,
                    size=layout.pair_size,
                    scale=text_scale,
                    color=text_color,
                    flatness=1.0,
                    shadow=1.0,
                    highlight=self.highlight,
                    depth_range=self.depth_range,
                    debug=self.debug,
                    image_right=dui2.TextImage(
                        texture=layout.imgtex,
                        # Text units; the text's scale maps them back.
                        size=(
                            layout.imgsize / text_scale,
                            layout.imgsize / text_scale,
                        ),
                        insets=layout.img_insets,
                    ),
                )
            )
            return decorations

        if layout.imgtex is not None:
            decorations.append(
                dui2.Image(
                    texture=layout.imgtex,
                    position=_at(layout.img_x_offs, layout.img_y_offs),
                    size=(layout.imgsize, layout.imgsize),
                    highlight=self.highlight,
                    depth_range=self.depth_range,
                )
            )

        if layout.show_text:
            decorations.append(
                dui2.Text(
                    text=_item_text(self.wrapper, layout.text),
                    position=_at(layout.text_x_offs, layout.text_y_offs),
                    # A zero max-width/height disables that constraint.
                    size=(layout.text_max_width or 0.0, 0.0),
                    h_align=layout.text_h_align,
                    scale=width * layout.text_mult,
                    color=text_color,
                    flatness=1.0,
                    shadow=1.0,
                    highlight=self.highlight,
                    depth_range=self.depth_range,
                )
            )

        return decorations


def _style_params(style: DisplayItemStyle) -> tuple[float, bool, bool]:
    """Return (aspect-ratio, compact, icon) for a display-item style."""
    if style is DisplayItemStyle.FULL:
        # Bit less tall than wide (graphic centric).
        return 0.75, False, False
    if style is DisplayItemStyle.COMPACT:
        # Significantly wider (text centric).
        return 0.5, True, False
    if style is DisplayItemStyle.ICON:
        # Square.
        return 1.0, False, True

    # Make sure we cover all possibilities.
    assert_never(style)


def _debug_bounds(
    assets: DepictionAssets,
    position: tuple[float, float],
    size: tuple[float, float],
    width: float,
    height: float,
) -> list[dui2.Decoration]:
    """Return the provided-bounds and constrained-bounds debug rects."""
    return [
        dui2.Image(
            texture=assets.white,
            position=position,
            size=size,
            color=(1, 1, 0, 0.1),
        ),
        dui2.Image(
            texture=assets.white,
            position=position,
            size=(width, height),
            color=(1, 0.5, 0, 0.2),
        ),
    ]


def _chest_image(
    assets: DepictionAssets,
    item: lditm.Item,
    width: float,
    *,
    position: tuple[float, float],
    compact: bool,
    icon: bool,
    highlight: bool,
    depth_range: tuple[float, float] | None,
) -> dui2.Image:
    """Return the image depicting a chest item."""
    from bacommon.classic import ClassicChestDisplayItem, chest_tint3

    assert isinstance(item, ClassicChestDisplayItem)

    tints = assets.chest_tints.get(item.appearance, assets.chest_tint_default)
    tint3 = chest_tint3(tints)
    c_size = width * (0.66 if compact else 1.05 if icon else 0.83)
    return dui2.Image(
        texture=assets.chest_icon,
        tint_texture=assets.chest_icon_tint,
        position=position,
        size=(c_size, c_size),
        tint_color=tints[0],
        tint2_color=tints[1],
        # Omitted when white so older clients' payloads are unchanged.
        tint3_color=None if tint3 == (1.0, 1.0, 1.0) else tint3,
        highlight=highlight,
        depth_range=depth_range,
    )


@dataclass
class _Layout:
    """Where an item's image and text go, in unscaled bounds units."""

    imgtex: TextureSpec | None = None

    #: The image's transparent margins (see
    #: :attr:`bacommon.docui.v2.TextImage.insets`); used for the
    #: count-beside-currency pair.
    img_insets: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
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

    #: When set, draw the text with the image fixed to its right, the
    #: pair centered and fitted in a box of this size by the client (it
    #: can measure text; we cannot). The offsets above go unused.
    pair_size: tuple[float, float] | None = None


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
        out.img_insets = _COIN_INSETS
        count = item.count
    elif itemtype is lditm.ItemTypeID.TICKETS:
        assert isinstance(item, lditm.Tickets)
        out.imgtex = assets.tickets
        out.img_insets = _TICKETS_INSETS
        count = item.count
    elif itemtype is lditm.ItemTypeID.TICKETS_PURPLE:
        assert isinstance(item, lditm.PurpleTickets)
        out.imgtex = assets.tickets_purple
        out.img_insets = _TICKETS_INSETS
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

    So the count is sent as a text carrying its image
    (:attr:`bacommon.docui.v2.Text.image_right`), which the client
    measures, centers, and shrinks to fit as one unit. The producer
    states the composition; the client resolves it.
    """
    # The currency art's transparent margins ride along as the image's
    # insets (set by the caller), so the pair measures and centers on
    # what is actually visible.
    assert out.text is not None
    out.text_mult = 0.01
    out.pair_size = (width * 0.95, width * 0.5)


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
