# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui text-images test page.

A text can carry an image at either end
(:attr:`bacommon.docui.v2.Text.image_left` /
:attr:`~bacommon.docui.v2.Text.image_right`); the client measures the
text and its images as one unit, shrinks that to fit the text's size
box, and aligns it there. This page exercises each part.

The first row's composition is deliberately far too big for the boxes
it is given, so fitting has to both scale and center for it to land --
one that already fitted would prove nothing. The debug toggle draws each
text's size box.
"""

from typing import TYPE_CHECKING
from dataclasses import replace

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest

#: Label scales for a composition far bigger than any box below, and
#: for one comfortably smaller than its box.
_BIG_SCALE = 1.4
_SMALL_SCALE = 0.5

#: Boxes for the size-to-fit row; each smaller than the big
#: composition in some way.
_BOXES: list[tuple[str, tuple[float, float]]] = [
    ('square', (120.0, 120.0)),
    ('wide', (170.0, 55.0)),
    ('tall', (70.0, 150.0)),
]

#: Box for the alignment row -- bigger than the small composition, so
#: there is slack for alignment to take up.
_ALIGN_BOX = (170.0, 150.0)


#: Where each test button centers its text's size box.
_BOX_CENTER = (0.0, -15.0)


def _anchor(
    size: tuple[float, float], h_align: dui2.HAlign, v_align: dui2.VAlign
) -> tuple[float, float]:
    """The text position that centers its size box on the button.

    A text's position is its alignment anchor, not its box center: a
    left-aligned text's box starts at its position, a top-aligned one's
    hangs below it. So place the anchor on the matching box edge.
    """
    x, y = _BOX_CENTER
    if h_align is dui2.HAlign.LEFT:
        x -= size[0] * 0.5
    elif h_align is dui2.HAlign.RIGHT:
        x += size[0] * 0.5
    if v_align is dui2.VAlign.TOP:
        y += size[1] * 0.5
    elif v_align is dui2.VAlign.BOTTOM:
        y -= size[1] * 0.5
    return (x, y)


def test_page_text_images(
    route: bacommon.docui.routes.docuitest.TextImages,
) -> bacommon.docui.v2.Response:
    """Testing text with images fixed to its ends."""
    from bauiv1 import _classiccatalogassets, _docuiv2testassets

    strs = _docuiv2testassets.strings
    debug = route.debug

    coin = dui2.TextImage(
        texture=_classiccatalogassets.textures.coin, size=(55.0, 55.0)
    )
    tickets = dui2.TextImage(
        texture=_classiccatalogassets.textures.tickets, size=(55.0, 55.0)
    )

    def _button(
        label: str,
        size: tuple[float, float],
        *,
        scale: float = _BIG_SCALE,
        text: str = '1414287',
        h_align: dui2.HAlign = dui2.HAlign.CENTER,
        v_align: dui2.VAlign = dui2.VAlign.CENTER,
        image_left: dui2.TextImage | None = None,
        image_right: dui2.TextImage | None = coin,
    ) -> dui2.Button:
        """A square button with one text-with-images drawn over it."""
        return dui2.Button(
            size=(200, 210),
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(label),
                    position=(0.0, 85.0),
                    size=(190.0, 0.0),
                    scale=0.6,
                ),
                dui2.Text(
                    text=LangStrSpecValue.literal(text),
                    position=_anchor(size, h_align, v_align),
                    size=size,
                    scale=scale,
                    h_align=h_align,
                    v_align=v_align,
                    image_left=image_left,
                    image_right=image_right,
                    debug=debug,
                ),
            ],
        )

    return dui2.Response(
        page=dui2.Page(
            title=LangStrSpecValue.literal('Text Images'),
            rows=[
                dui2.ButtonRow(
                    debug=debug,
                    title=LangStrSpecValue.literal('Size-to-fit'),
                    subtitle=LangStrSpecValue.literal(
                        'Same oversized count+coin in every button;'
                        ' only the box differs.'
                    ),
                    buttons=[
                        # Unconstrained: overflows the button entirely.
                        _button('no size', (0.0, 0.0)),
                    ]
                    + [_button(f'size {name}', box) for name, box in _BOXES],
                ),
                dui2.ButtonRow(
                    debug=debug,
                    title=LangStrSpecValue.literal('Alignment'),
                    subtitle=LangStrSpecValue.literal(
                        'Content smaller than its box, so alignment'
                        ' is the only thing moving it.'
                    ),
                    buttons=[
                        _button(
                            'left/top',
                            _ALIGN_BOX,
                            scale=_SMALL_SCALE,
                            h_align=dui2.HAlign.LEFT,
                            v_align=dui2.VAlign.TOP,
                        ),
                        _button('center', _ALIGN_BOX, scale=_SMALL_SCALE),
                        _button(
                            'right/bottom',
                            _ALIGN_BOX,
                            scale=_SMALL_SCALE,
                            h_align=dui2.HAlign.RIGHT,
                            v_align=dui2.VAlign.BOTTOM,
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    debug=debug,
                    title=LangStrSpecValue.literal('Variations'),
                    subtitle=LangStrSpecValue.literal(
                        'Left image, both ends, a visual offset, art'
                        ' insets, a tint.'
                    ),
                    buttons=[
                        _button(
                            'left',
                            (180.0, 100.0),
                            scale=0.8,
                            text='250',
                            image_left=tickets,
                            image_right=None,
                        ),
                        _button(
                            'both',
                            (180.0, 100.0),
                            scale=0.8,
                            text='x3',
                            image_left=tickets,
                        ),
                        _button(
                            'visual offset',
                            (180.0, 100.0),
                            scale=0.8,
                            text='250',
                            # Moves the drawn coin only; the pair stays
                            # centered as if it hadn't moved.
                            image_right=replace(coin, offset=(15.0, 15.0)),
                        ),
                        _button(
                            'insets',
                            (180.0, 100.0),
                            scale=0.8,
                            text='250',
                            image_right=replace(
                                coin, insets=(0.15, 0.15, 0.15, 0.15)
                            ),
                        ),
                        _button(
                            'tinted',
                            (180.0, 100.0),
                            scale=0.8,
                            text='250',
                            image_right=replace(
                                coin, color=(0.4, 1.0, 0.4, 0.6)
                            ),
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=(
                                strs.common.hide_debug.spec
                                if debug
                                else strs.common.show_debug.spec
                            ),
                            style=dui2.ButtonStyle.MEDIUM,
                            size=(240, 60),
                            color=(0.6, 0.4, 0.8, 1.0),
                            action=replace(route, debug=not debug).replace(),
                        )
                    ],
                ),
            ],
        )
    )
