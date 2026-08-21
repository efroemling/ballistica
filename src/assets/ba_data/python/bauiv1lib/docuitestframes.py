# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui frames test page.

Frames come in two flavors and this page shows them side by side: a
plain one, which just places its children, and a *sized* one, which
measures them, centers them, and shrinks them to fit its box.

The composition is deliberately far too big for the box it is given, so
the sized version has to both scale and center for it to land -- a
combo that already fitted would prove nothing. The debug toggle draws
every bound involved: the item's box in cyan, the extent the children
occupy in magenta, and each child's own bounds in their usual colors.

See ``docs/initiatives/docui-frames.md``.
"""

from typing import TYPE_CHECKING

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.v2


#: A composition far bigger than any box it is given below, so
#: fitting has to both shrink and re-center for it to land. One that
#: already fitted would not prove much.
_BIG = (80.0, 1.4)  # (icon size, label scale) -- roughly 240x80.

#: A composition comfortably smaller than its box, so alignment is the
#: only thing that moves it.
_SMALL = (28.0, 0.5)  # roughly 90x28.

#: Boxes for the size-to-fit row; each smaller than _BIG in some way.
_BOXES: list[tuple[str, tuple[float, float]]] = [
    ('square', (120.0, 120.0)),
    ('wide', (170.0, 55.0)),
    ('tall', (70.0, 150.0)),
]

#: Box for the alignment row -- bigger than _SMALL, so there is slack
#: for alignment to take up, and inside the button so nothing spills.
_ALIGN_BOX = (170.0, 150.0)


def test_page_frames(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """Testing frames, with and without size-to-fit."""
    from bauiv1 import classicassets, _docuiv2testassets

    strs = _docuiv2testassets.strings

    debug = bool(request.args.get('debug', False))

    def _content(spec: tuple[float, float]) -> list[dui2.Decoration]:
        """An icon with a label beside it, in local units.

        Authored with no idea how big it will end up being -- which is
        the point: the sized frame works that out.
        """
        icon_size, label_scale = spec
        return [
            dui2.Text(
                text=LangStrSpecValue.literal('1414287'),
                position=(0.0, 0.0),
                size=(0.0, 0.0),
                scale=label_scale,
                h_align=dui2.HAlign.RIGHT,
                debug=debug,
            ),
            dui2.Image(
                texture=classicassets.textures.coin,
                position=(icon_size * 0.5, 0.0),
                size=(icon_size, icon_size),
                debug=debug,
            ),
        ]

    def _button(
        label: str,
        size: tuple[float, float] | None,
        *,
        spec: tuple[float, float] = _BIG,
        h_align: dui2.HAlign = dui2.HAlign.CENTER,
        v_align: dui2.VAlign = dui2.VAlign.CENTER,
    ) -> dui2.Button:
        """A square button with one frame drawn over it."""
        return dui2.Button(
            size=(200, 210),
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(label),
                    position=(0.0, 85.0),
                    size=(190.0, 0.0),
                    scale=0.6,
                ),
                dui2.Frame(
                    decorations=_content(spec),
                    position=(0.0, -15.0),
                    size=size,
                    h_align=h_align,
                    v_align=v_align,
                    debug=debug,
                ),
            ],
        )

    return dui2.Response(
        page=dui2.Page(
            padding_left=20,
            padding_right=20,
            title=LangStrSpecValue.literal('Frames'),
            rows=[
                dui2.ButtonRow(
                    debug=debug,
                    padding_left=-10,
                    title=LangStrSpecValue.literal('Size-to-fit'),
                    subtitle=LangStrSpecValue.literal(
                        'Same oversized icon+label in every button;'
                        ' only the frame differs.'
                    ),
                    buttons=[
                        # No size: the frame just places its children,
                        # which overflow the button entirely.
                        _button('no size', None),
                    ]
                    + [_button(f'size {name}', box) for name, box in _BOXES],
                ),
                dui2.ButtonRow(
                    debug=debug,
                    padding_left=-10,
                    title=LangStrSpecValue.literal('Alignment'),
                    subtitle=LangStrSpecValue.literal(
                        'Content smaller than its box, so alignment'
                        ' is the only thing moving it.'
                    ),
                    buttons=[
                        _button(
                            'left/top',
                            _ALIGN_BOX,
                            spec=_SMALL,
                            h_align=dui2.HAlign.LEFT,
                            v_align=dui2.VAlign.TOP,
                        ),
                        _button('center', _ALIGN_BOX, spec=_SMALL),
                        _button(
                            'right/bottom',
                            _ALIGN_BOX,
                            spec=_SMALL,
                            h_align=dui2.HAlign.RIGHT,
                            v_align=dui2.VAlign.BOTTOM,
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
                            action=dui2.Replace(
                                dui2.Request(
                                    request.path, args={'debug': not debug}
                                )
                            ),
                        )
                    ],
                ),
            ],
        )
    )
