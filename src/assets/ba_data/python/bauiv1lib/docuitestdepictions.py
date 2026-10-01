# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui depictions test page.

Shows each depiction kind as a
:class:`bacommon.docui.v2.Depiction` decoration on a button, then on a
disabled button, then fitted into boxes of other shapes and alignments.
Hovering, pressing, and selecting the buttons exercises how depictions
follow their button's emphasis; the disabled row, the standard disabled
look. The precise-fit rows check the fit exactly: a flat white
depiction of a known shape, with a half-black image laid over where
it should land (computed here, independently of the native fit), so
a correct fit is a plain grey rect and any offset shows as a white or
dark fringe. The button-body rows do the same with the white shape as
the button's own body (its depiction).

Characters are composed by the cloud only, so this page carries a few
compositions captured from it (their packages are pinned prod versions,
so they stay resolvable).
"""

from typing import TYPE_CHECKING, assert_never
from dataclasses import replace

from bacommon.langstr import LangStrSpecValue
import bacommon.clienteffect as clfx
import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.assetspec
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest

# Captured from bamaster's charactercompose (page components: name +
# icon).
_SPAZ_JSON = (
    '{"n":{"b":{"t":"Spaz"}},"i":{"b":{"tx":49,"cm":50,"pk":[312],"dg":'
    '"703baf89587ff5f0"}}}'
)
_ZOE_JSON = (
    '{"n":{"b":{"t":"Zoe"}},"i":{"b":{"tx":85,"cm":86,"pk":[312],"dg":"'
    '703baf89587ff5f0","cl":[0.2,0.4,1.0],"hl":[1.0,0.8,0.1]}}}'
)
_KRONK_JSON = (
    '{"n":{"b":{"t":"A Rather Long Name"}},"i":{"b":{"tx":42,"cm":43,"p'
    'k":[312],"dg":"703baf89587ff5f0","cl":[0.4,0.5,0.4],"hl":[1.0,0.5,'
    '0.3]}}}'
)

# Captured from bamaster's charactercompose (viewer components: the
# spaz form alone).
_ZOE_VIEWER_JSON = (
    '{"s":{"b":{"ct":605,"cm":606,"mh":540,"mt":544,"mua":545,"mul":546'
    ',"mll":541,"mto":543,"pk":[316,62],"dg":"6753d437f6245a89","mfa":5'
    '38,"mhn":539,"mp":542,"sj":[276,277,278],"sa":[266,267,268,269],"s'
    'i":[272,273,274,275],"sd":[270],"sp":[279],"sf":[271],"cl":[0.2,0.'
    '4,1.0],"hl":[1.0,0.8,0.1],"tr":0.11,"so":[0.03,0.0,-0.02],"lt":0.0'
    '6,"la":0.045,"ss":0.03,"ia":0.2,"aw":0.3,"iw":0.02,"es":0.95,"eo":'
    '[0.08,-0.036,0.205],"ec":[0.55,0.3,0.7],"eb":[0.54,0.51,0.55],"lc"'
    ':[0.6,0.35,0.31],"ln":15.0,"at":{"h":[{"t":"an","p":[-0.173,0.124,'
    '0.153],"q":[0.89,-0.2665,-0.37,0.0],"s":[{"m":617,"o":[1.0,1.0,1.0'
    ',0.02,0.16,0.05]}],"k":0.2,"d":0.7,"r":0.375},{"t":"an","p":[0.196'
    ',0.098,0.118],"q":[0.8582,-0.2296,0.4592,0.0],"s":[{"m":619,"o":[1'
    '.0,1.0,1.0,-0.01,0.03,0.06,0.9763,0.2164,0.0,0.0]}],"k":0.3,"d":0.'
    '7},{"t":"a2","p":[0.0,0.28,-0.224],"q":[0.0,0.0,0.852525,0.522687]'
    ',"s":[{"m":620,"o":[1.0,1.0,1.0,0.0,0.0,0.0,0.0,0.0,1.0,0.0]},{"m"'
    ':621,"o":[1.0,1.0,1.0,0.0,0.0,0.04,0.0,0.0,1.0,0.0]}],"k":0.67,"d"'
    ':0.8,"l":0.8,"r":0.625,"kc":-0.26}]}}}}'
)


def _part(character_json: str, key: str) -> str:
    """One component of a captured character, as its depiction carries it.

    Depictions carry a single component ('n' name, 'i' icon, 's' spaz),
    never a whole character.
    """
    import json

    return json.dumps(json.loads(character_json)[key], separators=(',', ':'))


def _icon(character_json: str) -> bdep.CharacterIconDepiction:
    return bdep.CharacterIconDepiction(_part(character_json, 'i'))


def _name(character_json: str) -> bdep.NameDepiction:
    return bdep.NameDepiction(_part(character_json, 'n'))


#: Each test button's size, and where its depiction box centers.
_BUTTON_SIZE = (170.0, 190.0)
_BOX_CENTER = (0.0, -12.0)

#: The box most kinds get: square, filling most of the button.
_BOX = (130.0, 130.0)

#: Precise-fit cases: (button size, depiction aspect, h align, v
#: align). Each depiction box fills its button but for a margin and a
#: caption strip.
_PRECISE_SQUARE: list[
    tuple[tuple[float, float], float, dui2.HAlign, dui2.VAlign]
] = [
    ((150.0, 160.0), 2.0, dui2.HAlign.CENTER, dui2.VAlign.TOP),
    ((150.0, 160.0), 2.0, dui2.HAlign.CENTER, dui2.VAlign.CENTER),
    ((150.0, 160.0), 2.0, dui2.HAlign.CENTER, dui2.VAlign.BOTTOM),
    ((150.0, 160.0), 0.5, dui2.HAlign.LEFT, dui2.VAlign.CENTER),
    ((150.0, 160.0), 0.5, dui2.HAlign.CENTER, dui2.VAlign.CENTER),
    ((150.0, 160.0), 0.5, dui2.HAlign.RIGHT, dui2.VAlign.CENTER),
    ((150.0, 160.0), 1.0, dui2.HAlign.CENTER, dui2.VAlign.CENTER),
]
_PRECISE_SHAPED: list[
    tuple[tuple[float, float], float, dui2.HAlign, dui2.VAlign]
] = [
    ((240.0, 130.0), 1.0, dui2.HAlign.LEFT, dui2.VAlign.CENTER),
    ((240.0, 130.0), 1.0, dui2.HAlign.CENTER, dui2.VAlign.CENTER),
    ((240.0, 130.0), 1.0, dui2.HAlign.RIGHT, dui2.VAlign.CENTER),
    ((240.0, 130.0), 3.5, dui2.HAlign.LEFT, dui2.VAlign.BOTTOM),
    ((120.0, 240.0), 1.0, dui2.HAlign.CENTER, dui2.VAlign.TOP),
    ((120.0, 240.0), 1.0, dui2.HAlign.CENTER, dui2.VAlign.CENTER),
    ((120.0, 240.0), 1.0, dui2.HAlign.CENTER, dui2.VAlign.BOTTOM),
    ((120.0, 240.0), 0.3, dui2.HAlign.RIGHT, dui2.VAlign.TOP),
]

#: A precise-fit case for a button body: (button size, button scale,
#: depiction aspect, h align, v align, button style). The depiction is
#: the button itself, so its box is the button's whole box.
type _BodyCase = tuple[
    tuple[float, float],
    float,
    float,
    dui2.HAlign,
    dui2.VAlign,
    dui2.ButtonStyle,
]

_PRECISE_BODIES: list[_BodyCase] = [
    (
        (150.0, 150.0),
        1.0,
        2.0,
        dui2.HAlign.CENTER,
        dui2.VAlign.TOP,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (150.0, 150.0),
        1.0,
        2.0,
        dui2.HAlign.CENTER,
        dui2.VAlign.CENTER,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (150.0, 150.0),
        1.0,
        2.0,
        dui2.HAlign.CENTER,
        dui2.VAlign.BOTTOM,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (150.0, 150.0),
        1.0,
        0.5,
        dui2.HAlign.LEFT,
        dui2.VAlign.CENTER,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (150.0, 150.0),
        1.0,
        0.5,
        dui2.HAlign.RIGHT,
        dui2.VAlign.CENTER,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (150.0, 150.0),
        1.0,
        1.0,
        dui2.HAlign.CENTER,
        dui2.VAlign.CENTER,
        dui2.ButtonStyle.SQUARE,
    ),
]
_PRECISE_BODIES_SCALED: list[_BodyCase] = [
    (
        (240.0, 120.0),
        0.8,
        1.0,
        dui2.HAlign.LEFT,
        dui2.VAlign.CENTER,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (240.0, 120.0),
        0.8,
        1.0,
        dui2.HAlign.RIGHT,
        dui2.VAlign.CENTER,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (120.0, 180.0),
        1.3,
        1.0,
        dui2.HAlign.CENTER,
        dui2.VAlign.TOP,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (120.0, 180.0),
        1.3,
        1.0,
        dui2.HAlign.CENTER,
        dui2.VAlign.BOTTOM,
        dui2.ButtonStyle.SQUARE,
    ),
    (
        (200.0, 100.0),
        1.0,
        2.0,
        dui2.HAlign.CENTER,
        dui2.VAlign.CENTER,
        dui2.ButtonStyle.MEDIUM,
    ),
    (
        (200.0, 100.0),
        1.0,
        3.0,
        dui2.HAlign.LEFT,
        dui2.VAlign.BOTTOM,
        dui2.ButtonStyle.LARGE,
    ),
]

#: Room above a button-body case for its caption.
_PRECISE_BODY_CAPTION = 26.0

#: Precise-fit layout: margin around the box, and the caption strip
#: above it.
_PRECISE_MARGIN = 12.0
_PRECISE_CAPTION = 24.0


def _expected_fit(
    box: tuple[float, float],
    aspect: float,
    h_align: dui2.HAlign,
    v_align: dui2.VAlign,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Where a shape should land in a box: (center offset, size).

    Written out here rather than shared with the native fit, so the
    page checks one against the other.
    """
    bwidth, bheight = box
    if bwidth / bheight > aspect:
        width, height = bheight * aspect, bheight
    else:
        width, height = bwidth, bwidth / aspect
    xslack = (bwidth - width) * 0.5
    yslack = (bheight - height) * 0.5
    if h_align is dui2.HAlign.LEFT:
        xoffs = -xslack
    elif h_align is dui2.HAlign.CENTER:
        xoffs = 0.0
    elif h_align is dui2.HAlign.RIGHT:
        xoffs = xslack
    else:
        assert_never(h_align)
    if v_align is dui2.VAlign.TOP:
        yoffs = yslack
    elif v_align is dui2.VAlign.CENTER:
        yoffs = 0.0
    elif v_align is dui2.VAlign.BOTTOM:
        yoffs = -yslack
    else:
        assert_never(v_align)
    return (xoffs, yoffs), (width, height)


def _indexed_image(
    texture: bacommon.assetspec.TextureSpec,
) -> bdep.ImageDepiction:
    """An image depiction in the compact (indexed) wire form.

    Built here against the client's own listing, as a producer would
    against its vendored one, so the page exercises the indexed decode
    path (manifest + digest check + index resolve).
    """
    from bacommon.assetspec import AssetIndexContext, wire_digest
    from bauiv1lib.docui._resolve import package_asset_listing

    packages = [texture._apvernum]  # pylint: disable=protected-access
    ctx = AssetIndexContext(packages, package_asset_listing)
    return bdep.ImageDepiction(
        texture=ctx.to_index(texture),
        packages=packages,
        domain_digest=wire_digest(ctx.domain_digest()),
    )


def test_page_depictions(
    route: bacommon.docui.routes.docuitest.Depictions,
) -> bacommon.docui.v2.Response:
    """Testing depictions."""
    from bauiv1 import (
        _builtinassets,
        _classiccatalogassets,
        _docuiv2testassets,
    )

    strs = _docuiv2testassets.strings
    debug = route.debug
    tex = _classiccatalogassets.textures

    chest = bdep.ImageDepiction(
        texture=tex.chest_icon,
        tint_texture=tex.chest_icon_tint,
        tint_color=(0.8, 0.2, 1.0),
        tint2_color=(1.0, 0.8, 0.2),
    )
    kinds: list[tuple[str, bdep.Depiction, tuple[float, float]]] = [
        ('icon', _icon(_SPAZ_JSON), _BOX),
        ('icon (tinted)', _icon(_ZOE_JSON), _BOX),
        ('name', _name(_ZOE_JSON), (140.0, 50.0)),
        ('image (chest)', chest, _BOX),
        ('image (coin)', bdep.ImageDepiction(texture=tex.coin), _BOX),
        ('image (indexed)', _indexed_image(tex.coin), _BOX),
        (
            'viewer',
            bdep.CharacterViewerDepiction(_part(_ZOE_VIEWER_JSON, 's')),
            _BOX,
        ),
        ('unknown kind', bdep.UnknownDepiction(), _BOX),
    ]

    def _button(
        label: str,
        decorations: list[dui2.Decoration],
        *,
        disabled: bool = False,
    ) -> dui2.Button:
        """A test button: a caption over the given decorations."""
        return dui2.Button(
            size=_BUTTON_SIZE,
            disabled=disabled,
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(label),
                    position=(0.0, 75.0),
                    size=(160.0, 0.0),
                    scale=0.55,
                )
            ]
            + decorations,
        )

    def _depiction(
        depiction: bdep.Depiction,
        size: tuple[float, float],
        *,
        position: tuple[float, float] = _BOX_CENTER,
        h_align: dui2.HAlign = dui2.HAlign.CENTER,
        v_align: dui2.VAlign = dui2.VAlign.CENTER,
    ) -> dui2.Depiction:
        return dui2.Depiction(
            depiction=depiction,
            position=position,
            size=size,
            h_align=h_align,
            v_align=v_align,
            debug=debug,
        )

    def _kind_buttons(*, disabled: bool) -> list[dui2.Button]:
        return [
            _button(label, [_depiction(dep, size)], disabled=disabled)
            for label, dep, size in kinds
        ]

    wide = (150.0, 70.0)
    tall = (70.0, 140.0)
    zoe = _icon(_ZOE_JSON)
    fit_buttons = [
        _button(
            'wide, left',
            [_depiction(zoe, wide, h_align=dui2.HAlign.LEFT)],
        ),
        _button('wide, center', [_depiction(zoe, wide)]),
        _button(
            'wide, right',
            [_depiction(zoe, wide, h_align=dui2.HAlign.RIGHT)],
        ),
        _button(
            'tall, top',
            [_depiction(zoe, tall, v_align=dui2.VAlign.TOP)],
        ),
        _button(
            'tall, bottom',
            [_depiction(zoe, tall, v_align=dui2.VAlign.BOTTOM)],
        ),
        _button(
            'long name',
            [_depiction(_name(_KRONK_JSON), (140.0, 50.0))],
        ),
        _button(
            'icon over name',
            [
                _depiction(
                    _icon(_KRONK_JSON),
                    (140.0, 90.0),
                    position=(0.0, 5.0),
                ),
                _depiction(
                    _name(_KRONK_JSON),
                    (140.0, 32.0),
                    position=(0.0, -65.0),
                ),
            ],
        ),
    ]

    white = _builtinassets.textures.white

    def _precise_button(
        size: tuple[float, float],
        aspect: float,
        h_align: dui2.HAlign,
        v_align: dui2.VAlign,
    ) -> dui2.Button:
        """A white shape fitted into a box, the expected fit over it."""
        box = (
            size[0] - 2.0 * _PRECISE_MARGIN,
            size[1] - 2.0 * _PRECISE_MARGIN - _PRECISE_CAPTION,
        )
        boxcenter = (0.0, -0.5 * _PRECISE_CAPTION)
        (xoffs, yoffs), expected = _expected_fit(box, aspect, h_align, v_align)
        caption = (
            f'{aspect:g}:1, {h_align.name.lower()}, {v_align.name.lower()}'
        )
        return dui2.Button(
            size=size,
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(caption),
                    position=(0.0, 0.5 * size[1] - 0.5 * _PRECISE_CAPTION),
                    size=(size[0] - 10.0, 0.0),
                    scale=0.5,
                ),
                dui2.Depiction(
                    depiction=bdep.ImageDepiction(texture=white, aspect=aspect),
                    position=boxcenter,
                    size=box,
                    h_align=h_align,
                    v_align=v_align,
                    highlight=False,
                    debug=debug,
                ),
                dui2.Image(
                    texture=white,
                    position=(boxcenter[0] + xoffs, boxcenter[1] + yoffs),
                    size=expected,
                    color=(0.0, 0.0, 0.0, 0.5),
                    highlight=False,
                ),
            ],
        )

    def _precise_body_button(case: _BodyCase) -> dui2.Button:
        """A button whose body is a white shape, the expected fit over it.

        Decorations sit in the button's own (unscaled) space, centered
        on it, so the expected fit is in the button's box as given.
        """
        size, scale, aspect, h_align, v_align, style = case
        (xoffs, yoffs), expected = _expected_fit(size, aspect, h_align, v_align)
        caption = (
            f'{aspect:g}:1, {h_align.name.lower()}, {v_align.name.lower()}'
            f', x{scale:g}, {style.name.lower()}'
        )
        return dui2.Button(
            size=size,
            scale=scale,
            style=style,
            padding_top=_PRECISE_BODY_CAPTION / scale,
            depiction=bdep.ImageDepiction(texture=white, aspect=aspect),
            depiction_h_align=h_align,
            depiction_v_align=v_align,
            debug=debug,
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(caption),
                    position=(
                        0.0,
                        0.5 * size[1] + 0.5 * _PRECISE_BODY_CAPTION / scale,
                    ),
                    size=(size[0], 0.0),
                    scale=0.45 / scale,
                    highlight=False,
                ),
                dui2.Image(
                    texture=white,
                    position=(xoffs, yoffs),
                    size=expected,
                    color=(0.0, 0.0, 0.0, 0.5),
                    highlight=False,
                ),
            ],
        )

    def _hit_button(
        caption: str,
        size: tuple[float, float],
        h_align: dui2.HAlign,
        *,
        hit_area: bool,
    ) -> dui2.Button:
        """A wide button whose body is an icon at one end.

        Pressing says which button got it, so it's easy to see where
        each one takes presses.
        """
        return dui2.Button(
            size=size,
            padding_top=_PRECISE_BODY_CAPTION,
            depiction=_icon(_ZOE_JSON),
            depiction_h_align=h_align,
            depiction_hit_area=hit_area,
            debug=debug,
            action=dui2.Local(
                immediate_client_effects=[
                    # Plain-string form: a local page has no decode
                    # context for ScreenMessageV2's l-strings.
                    clfx.ScreenMessage(
                        message=f'Pressed: {caption}',
                        color=(0.5, 1.0, 0.5),
                    )
                ]
            ),
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(caption),
                    position=(0.0, 0.5 * size[1] + 0.5 * _PRECISE_BODY_CAPTION),
                    size=(size[0], 0.0),
                    scale=0.5,
                    highlight=False,
                ),
            ],
        )

    hit_buttons = [
        _hit_button(
            'whole button', (320.0, 110.0), dui2.HAlign.LEFT, hit_area=False
        ),
        _hit_button(
            'icon only', (320.0, 110.0), dui2.HAlign.LEFT, hit_area=True
        ),
        _hit_button(
            'icon only (right)',
            (320.0, 110.0),
            dui2.HAlign.RIGHT,
            hit_area=True,
        ),
        _hit_button(
            'thin: icon grown to min size',
            (320.0, 40.0),
            dui2.HAlign.LEFT,
            hit_area=True,
        ),
    ]

    def _row(
        title: str, subtitle: str, buttons: list[dui2.Button]
    ) -> dui2.ButtonRow:
        return dui2.ButtonRow(
            debug=debug,
            padding_left=-10,
            title=LangStrSpecValue.literal(title),
            subtitle=LangStrSpecValue.literal(subtitle),
            buttons=buttons,
        )

    return dui2.Response(
        page=dui2.Page(
            padding_left=20,
            padding_right=20,
            title=LangStrSpecValue.literal('Depictions'),
            rows=[
                _row(
                    'Kinds',
                    'Each kind on a button; hover, press, and select them'
                    ' to see them follow the button.',
                    _kind_buttons(disabled=False),
                ),
                _row(
                    'Disabled',
                    'The same on disabled buttons: faded and greyed.',
                    _kind_buttons(disabled=True),
                ),
                _row(
                    'Fit and alignment',
                    'A square icon fitted into other shapes, a name'
                    ' shrinking to fit, and a composite.',
                    fit_buttons,
                ),
                _row(
                    'Hit area',
                    'Icon bodies on wide buttons. The first takes presses'
                    ' and hover anywhere in its box; the rest only over'
                    ' the icon (grown to a minimum size).',
                    hit_buttons,
                ),
                _row(
                    'Precise fit',
                    'White shapes fitted into boxes, the expected fit'
                    ' half-black over each: any fringe is a misfit.',
                    [_precise_button(*case) for case in _PRECISE_SQUARE],
                ),
                _row(
                    'Precise fit (shaped boxes)',
                    'The same in wide and tall boxes.',
                    [_precise_button(*case) for case in _PRECISE_SHAPED],
                ),
                _row(
                    'Precise fit (button bodies)',
                    'Each white shape is the button itself (its depiction'
                    ' body), the expected fit half-black over it.',
                    [_precise_body_button(case) for case in _PRECISE_BODIES],
                ),
                _row(
                    'Precise fit (button bodies, scaled and styled)',
                    'The same on scaled buttons and other styles.',
                    [
                        _precise_body_button(case)
                        for case in _PRECISE_BODIES_SCALED
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
