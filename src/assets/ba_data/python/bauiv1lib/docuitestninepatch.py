# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui 9-patch test page.

Images drawn as 9-patches (:class:`bacommon.docui.v2.ImageNinePatch`):
striped capsule art whose middle half either stretches or repeats at
its ends' scale (tile-fit), optionally tinted three colors through an
rgb tint texture. A 9-patch fills its image's box exactly, so with
debug on each image's outline (its box) should sit right on the
capsule's edge, with no gap or overhang anywhere.
"""

from typing import TYPE_CHECKING
from dataclasses import replace

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.routes.docuitest
    import bacommon.docui.v2

#: Tints through the tint texture's red, green and blue bands.
type _Tints = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]

_CANDY: _Tints = ((1.0, 0.15, 0.2), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))
_FESTIVE: _Tints = ((1.0, 0.15, 0.2), (1.0, 1.0, 1.0), (0.2, 0.8, 0.3))
_TEAM: _Tints = ((0.2, 0.4, 1.0), (1.0, 0.8, 0.2), (0.2, 0.4, 1.0))

#: Room for each button's caption above its image, and around it.
_CAPTION = 24.0
_MARGIN = 12.0


def test_page_nine_patch(
    route: bacommon.docui.routes.docuitest.NinePatch,
) -> bacommon.docui.v2.Response:
    """Testing 9-patch images."""
    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings
    ttex = _docuiv2testassets.textures
    debug = route.debug

    def _button(
        caption: str,
        size: tuple[float, float],
        *,
        tile: bool = True,
        tints: _Tints | None = None,
        borders: tuple[float, float] | None = None,
    ) -> dui2.Button:
        """A button showing one 9-patch capsule filling a box.

        The art is a stadium whose ends are its outer quarters (horizontal
        insets 0.25); vertically it splits at its middle. ``borders``
        defaults to half the height on each end (the ends exactly round)
        and the full half-height top and bottom.
        """
        width, height = size
        bx, by = (
            borders if borders is not None else (height * 0.5, height * 0.5)
        )
        return dui2.Button(
            size=(width + 2.0 * _MARGIN, height + 2.0 * _MARGIN + _CAPTION),
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(caption),
                    position=(0.0, 0.5 * (height + 2.0 * _MARGIN) - 2.0),
                    size=(width, 0.0),
                    scale=0.5,
                ),
                dui2.Image(
                    texture=ttex.capsule_stripes,
                    position=(0.0, -0.5 * _CAPTION),
                    size=size,
                    tint_texture=(
                        None if tints is None else ttex.capsule_stripes_tint
                    ),
                    tint_color=None if tints is None else tints[0],
                    tint2_color=None if tints is None else tints[1],
                    tint3_color=None if tints is None else tints[2],
                    nine_patch=dui2.ImageNinePatch(
                        insets=(0.25, 0.5, 0.25, 0.5),
                        borders=(bx, by, bx, by),
                        tile_h=tile,
                    ),
                    debug=debug,
                ),
            ],
        )

    def _bounds_check(size: tuple[float, float]) -> dui2.Button:
        """An opaque white 9-patch: exactly as big as its debug box."""
        from bauiv1 import _builtinassets

        width, height = size
        return dui2.Button(
            size=(width + 2.0 * _MARGIN, height + 2.0 * _MARGIN),
            color=(0.1, 0.1, 0.1, 1.0),
            decorations=[
                dui2.Image(
                    texture=_builtinassets.textures.white,
                    position=(0.0, 0.0),
                    size=size,
                    color=(1.0, 0.3, 0.3, 1.0),
                    nine_patch=dui2.ImageNinePatch(
                        insets=(0.25, 0.25, 0.25, 0.25),
                        borders=(20.0, 20.0, 20.0, 20.0),
                        tile_h=True,
                        tile_v=True,
                    ),
                    debug=debug,
                ),
            ],
        )

    def _row(
        title: str, subtitle: str, buttons: list[dui2.Button]
    ) -> dui2.ButtonRow:
        return dui2.ButtonRow(
            debug=debug,
            title=LangStrSpecValue.literal(title),
            subtitle=LangStrSpecValue.literal(subtitle),
            buttons=buttons,
        )

    return dui2.Response(
        page=dui2.Page(
            title=LangStrSpecValue.literal('9-Patch'),
            rows=[
                _row(
                    'Bounds check',
                    'Opaque 9-patches (red) on dark buttons. With debug on,'
                    ' each should be one solid tint edge to edge: any dark'
                    ' rim inside its outline means it misses its box.',
                    [
                        _bounds_check((120.0, 60.0)),
                        _bounds_check((260.0, 90.0)),
                        _bounds_check((90.0, 140.0)),
                    ],
                ),
                _row(
                    'Tile-fit',
                    'The middle repeats at the ends\' scale, fitted to a'
                    ' whole number of copies; stripes run straight through.',
                    [
                        _button('short', (110.0, 50.0)),
                        _button('medium', (240.0, 50.0)),
                        _button('long', (420.0, 50.0)),
                        _button('tall', (240.0, 90.0)),
                    ],
                ),
                _row(
                    'Stretch',
                    'The same art with its middle stretched instead; stripes'
                    ' flatten between the ends.',
                    [
                        _button('short', (110.0, 50.0), tile=False),
                        _button('medium', (240.0, 50.0), tile=False),
                        _button('long', (420.0, 50.0), tile=False),
                        _button('tall', (240.0, 90.0), tile=False),
                    ],
                ),
                _row(
                    'Tinted',
                    'Greyscale art tinted three colors through an rgb tint'
                    ' texture sharing its 9-patch layout.',
                    [
                        _button('candy cane', (240.0, 50.0), tints=_CANDY),
                        _button('festive', (240.0, 50.0), tints=_FESTIVE),
                        _button('team, long', (420.0, 50.0), tints=_TEAM),
                    ],
                ),
                _row(
                    'Borders',
                    'Smaller ends than the height, and ends too big for the'
                    ' box (they shrink to fit; the box never grows).',
                    [
                        _button(
                            'small ends', (240.0, 60.0), borders=(15.0, 30.0)
                        ),
                        _button(
                            'oversized ends',
                            (80.0, 50.0),
                            borders=(60.0, 25.0),
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
