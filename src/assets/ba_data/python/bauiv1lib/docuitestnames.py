# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui names test page.

Name depictions in their two forms -- basic (colored text) and capsule
(text in a rounded capsule, optionally with an icon covering its left
end) -- fitted into boxes of various shapes and alignments. Builtin
circle textures stand in for real capsule and icon art. With debug on,
each depiction shows its box (red) and the box it reports covering
(blue; what a hit-tested button takes presses over): a capsule's body
should exactly fill the blue box, glow aside.
"""

import json
from typing import TYPE_CHECKING
from dataclasses import replace

from efro.dataclassio import dataclass_to_dict
from bacommon.langstr import LangStrSpecValue
import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    # Any: the name payloads here are hand-built json dicts with mixed
    # value types (the schema itself is server-private).
    from typing import Any

    import bacommon.assetspec
    import bacommon.docui.routes.docuitest
    import bacommon.docui.v2

#: The web account display's colors (bamaster ba_web_tools.css, dark
#: theme): bright green text in a faint green capsule with a green
#: glow, and the purple V2 badge.
_ACCOUNT_TEXT = (0.51, 1.0, 0.42)
_ACCOUNT_CAPSULE = (0.25, 1.0, 0.35, 0.35)
_ACCOUNT_BADGE = (0.43, 0.37, 0.74, 1.0)

#: Tint for the white glowing-capsule art (the web's dark-theme green)
#: and the in-game account name's deep green text, drawn with a text
#: glow.
_WEB_CAPSULE = (0.2, 1.0, 0.1, 1.0)
_WEB_TEXT = (0.2, 1.0, 0.15)

#: Dark buttons for that row, so the glows read as on the dark web
#: page.
_WEB_BG = (0.22, 0.2, 0.26, 1.0)

#: A plain dark capsule for cases about layout rather than looks.
_PLAIN_CAPSULE = (0.3, 0.3, 0.4, 1.0)

#: Room for each button's caption above its box, and around the box.
_CAPTION = 24.0
_MARGIN = 10.0


def test_page_names(
    route: bacommon.docui.routes.docuitest.Names,
) -> bacommon.docui.v2.Response:
    """Testing name depictions."""
    from bauiv1 import _builtinassets, _docuiv2testassets

    strs = _docuiv2testassets.strings
    debug = route.debug
    tex = _builtinassets.textures
    circle = _spec(tex.circle)
    soft_circle = _spec(tex.circle_shadow)

    def _button(
        caption: str,
        depiction: bdep.NameDepiction,
        box: tuple[float, float],
        *,
        h_align: dui2.HAlign = dui2.HAlign.CENTER,
        v_align: dui2.VAlign = dui2.VAlign.CENTER,
        color: tuple[float, float, float, float] | None = None,
    ) -> dui2.Button:
        """A test button: a caption over a name in a box."""
        width = box[0] + 2.0 * _MARGIN
        height = box[1] + 2.0 * _MARGIN + _CAPTION
        return dui2.Button(
            size=(width, height),
            style=(
                dui2.ButtonStyle.MEDIUM
                if width > height
                else dui2.ButtonStyle.SQUARE
            ),
            color=color,
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(caption),
                    position=(0.0, 0.5 * height - 0.5 * _CAPTION - 2.0),
                    size=(width - 10.0, 0.0),
                    scale=0.5,
                ),
                dui2.Depiction(
                    depiction=depiction,
                    position=(0.0, -0.5 * _CAPTION),
                    size=box,
                    h_align=h_align,
                    v_align=v_align,
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

    # The account look: a glowing capsule with a badge at its left end.
    def _account(text: str) -> bdep.NameDepiction:
        return _name(
            text,
            _ACCOUNT_TEXT,
            _capsule(
                texture=soft_circle,
                color=_ACCOUNT_CAPSULE,
                edge=0.7,
                icon=circle,
                icon_color=_ACCOUNT_BADGE,
                icon_scale=0.75,
            ),
        )

    # The web's account name, matched with real art: the glowing
    # capsule (a white 9-patch tinted green) and the V2 badge. Sizes
    # from the CSS: a 54px capsule around 32px text, a 40px badge with
    # a 4px gap, 20px of right padding.
    glow_capsule = _spec(tex.glow_circle)
    v2_badge = _spec(tex.account_v2_icon)

    def _web_account(text: str, *, glow: float = 1.0) -> bdep.NameDepiction:
        return _name(
            text,
            _WEB_TEXT,
            _capsule(
                radius=1.6,
                texture=glow_capsule,
                color=_WEB_CAPSULE,
                edge=0.8,
                icon=v2_badge,
                icon_scale=0.8,
                icon_edge=1.1,
                text_glow=glow,
            ),
        )

    # Striped test art: a greyscale capsule whose middle half tiles,
    # and an rgb tint texture marking its bands for three colors.
    ttex = _docuiv2testassets.textures
    stripes = _spec(ttex.capsule_stripes)
    stripes_tint = _spec(ttex.capsule_stripes_tint)

    def _striped(
        text: str,
        tints: (
            tuple[
                tuple[float, float, float],
                tuple[float, float, float],
                tuple[float, float, float],
            ]
            | None
        ),
        *,
        tile: bool = True,
    ) -> bdep.NameDepiction:
        return _name(
            text,
            (0.12, 0.1, 0.18),
            _capsule(
                radius=1.6,
                texture=stripes,
                insets=(0.25, 0.25),
                tile=tile,
                tint_texture=None if tints is None else stripes_tint,
                tint_colors=tints,
            ),
        )

    candy = ((1.0, 0.15, 0.2), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))
    festive = ((1.0, 0.15, 0.2), (1.0, 1.0, 1.0), (0.2, 0.8, 0.3))
    team = ((0.2, 0.4, 1.0), (1.0, 0.8, 0.2), (0.2, 0.4, 1.0))

    wide = (280.0, 60.0)
    tall = (110.0, 150.0)
    glow_box = (300.0, 90.0)

    return dui2.Response(
        page=dui2.Page(
            title=LangStrSpecValue.literal('Names'),
            rows=[
                _row(
                    'Striped capsules',
                    'Greyscale 9-patch art whose middle tiles at the'
                    ' ends\' scale (tile-fit), tinted three colors by an'
                    ' rgb tint texture.',
                    [
                        _button('untinted', _striped('efro', None), wide),
                        _button('candy cane', _striped('efro', candy), wide),
                        _button('festive', _striped('efro', festive), wide),
                        _button(
                            'team, long',
                            _striped('A Rather Long Name', team),
                            wide,
                        ),
                        _button(
                            'stretched (no tile)',
                            _striped('A Rather Long Name', festive, tile=False),
                            wide,
                        ),
                        _button(
                            'short',
                            _striped('Zoe', festive),
                            (160.0, 60.0),
                        ),
                    ],
                ),
                _row(
                    'Text glow',
                    'A neon look by amount (text_glow): white-hot'
                    ' interiors and a soft glow in the text\'s own color,'
                    ' in place of its drop shadow. 0 is plain text.',
                    [
                        _button(
                            f'text glow {amount}',
                            _web_account('efro', glow=amount),
                            glow_box,
                            color=_WEB_BG,
                        )
                        for amount in (0.0, 0.5, 1.0)
                    ],
                ),
                _row(
                    'Web account look',
                    'The website\'s account name (dark theme), drawn'
                    ' natively: tinted glow capsule art, the V2 badge, and'
                    ' a glow on the text.',
                    [
                        _button(
                            'efro',
                            _web_account('efro'),
                            wide,
                            color=_WEB_BG,
                        ),
                        _button(
                            'big box',
                            _web_account('efro'),
                            (360.0, 100.0),
                            color=_WEB_BG,
                        ),
                        _button(
                            'long name',
                            _web_account('A Rather Long Name'),
                            wide,
                            color=_WEB_BG,
                        ),
                    ],
                ),
                _row(
                    'Basic',
                    'Colored text, as large as fits its box.',
                    [
                        _button('white, center', _name('efro'), wide),
                        _button(
                            'green, left',
                            _name('efro', (0.4, 1.0, 0.4)),
                            wide,
                            h_align=dui2.HAlign.LEFT,
                        ),
                        _button(
                            'orange, right',
                            _name('efro', (1.0, 0.6, 0.2)),
                            wide,
                            h_align=dui2.HAlign.RIGHT,
                        ),
                        _button(
                            'long, shrinks to fit',
                            _name('A Rather Long Name Indeed'),
                            (200.0, 60.0),
                        ),
                        _button(
                            'tall box, top',
                            _name('Zoe'),
                            tall,
                            v_align=dui2.VAlign.TOP,
                        ),
                        _button(
                            'tall box, bottom',
                            _name('Zoe'),
                            tall,
                            v_align=dui2.VAlign.BOTTOM,
                        ),
                    ],
                ),
                _row(
                    'Capsule',
                    'Radius 1.0 = the cap height (hugs the capitals); 2.3 is'
                    ' the default. With an icon, the icon sits at the left'
                    ' end and the text butts against it.',
                    [
                        _button(
                            'radius 1.0',
                            _name(
                                'Efro',
                                None,
                                _capsule(radius=1.0, color=_PLAIN_CAPSULE),
                            ),
                            wide,
                        ),
                        _button(
                            'radius 1.6',
                            _name(
                                'Efro',
                                None,
                                _capsule(radius=1.6, color=_PLAIN_CAPSULE),
                            ),
                            wide,
                        ),
                        _button(
                            'radius 2.3 (default)',
                            _name(
                                'Efro',
                                None,
                                _capsule(radius=2.3, color=_PLAIN_CAPSULE),
                            ),
                            wide,
                        ),
                        _button(
                            'icon, scale 1.0',
                            _name(
                                'efro',
                                None,
                                _capsule(
                                    color=_PLAIN_CAPSULE,
                                    icon=circle,
                                    icon_color=_ACCOUNT_BADGE,
                                ),
                            ),
                            wide,
                        ),
                        _button(
                            'icon, scale 0.75',
                            _name(
                                'efro',
                                None,
                                _capsule(
                                    color=_PLAIN_CAPSULE,
                                    icon=circle,
                                    icon_color=_ACCOUNT_BADGE,
                                    icon_scale=0.75,
                                ),
                            ),
                            wide,
                        ),
                        _button(
                            'icon, long name',
                            _name(
                                'A Rather Long Name Indeed',
                                None,
                                _capsule(
                                    color=_PLAIN_CAPSULE,
                                    icon=circle,
                                    icon_color=_ACCOUNT_BADGE,
                                    icon_scale=0.75,
                                ),
                            ),
                            wide,
                        ),
                    ],
                ),
                _row(
                    'Text inset and icon edge',
                    'Unset inset = automatic: text reaches into the ends as'
                    ' far as the capitals stay inside the curve (0 ='
                    ' straight section only, 1 = to the tip). The icon'
                    ' edge (default 0.9) is where text butts against the'
                    ' scaled icon; it never changes the icon itself.',
                    [
                        _button(
                            'auto, radius 1.0',
                            _name(
                                'Efro',
                                None,
                                _capsule(radius=1.0, color=_PLAIN_CAPSULE),
                            ),
                            wide,
                        ),
                        _button(
                            'auto, radius 3.5',
                            _name(
                                'Efro',
                                None,
                                _capsule(radius=3.5, color=_PLAIN_CAPSULE),
                            ),
                            wide,
                        ),
                        _button(
                            'inset 0',
                            _name(
                                'Efro',
                                None,
                                _capsule(text_inset=0.0, color=_PLAIN_CAPSULE),
                            ),
                            wide,
                        ),
                        _button(
                            'inset 1',
                            _name(
                                'Efro',
                                None,
                                _capsule(text_inset=1.0, color=_PLAIN_CAPSULE),
                            ),
                            wide,
                        ),
                        _button(
                            'inset -0.5',
                            _name(
                                'Efro',
                                None,
                                _capsule(text_inset=-0.5, color=_PLAIN_CAPSULE),
                            ),
                            wide,
                        ),
                        _button(
                            'icon scale 0.6',
                            _name(
                                'Efro',
                                None,
                                _capsule(
                                    color=_PLAIN_CAPSULE,
                                    icon=circle,
                                    icon_color=_ACCOUNT_BADGE,
                                    icon_scale=0.6,
                                ),
                            ),
                            wide,
                        ),
                        _button(
                            'icon edge 0.5',
                            _name(
                                'Efro',
                                None,
                                _capsule(
                                    color=_PLAIN_CAPSULE,
                                    icon=circle,
                                    icon_color=_ACCOUNT_BADGE,
                                    icon_edge=0.5,
                                ),
                            ),
                            wide,
                        ),
                        _button(
                            'icon edge 1.3',
                            _name(
                                'Efro',
                                None,
                                _capsule(
                                    color=_PLAIN_CAPSULE,
                                    icon=circle,
                                    icon_color=_ACCOUNT_BADGE,
                                    icon_edge=1.3,
                                ),
                            ),
                            wide,
                        ),
                    ],
                ),
                _row(
                    'Capsule art with glow',
                    'Soft capsule art whose edge sits inside it'
                    ' (capsule_edge): the glow spills past the box; sizing'
                    ' ignores it. A soft icon instead scales up past its'
                    ' square with its edge pulled in to match.',
                    [
                        _button(
                            'capsule edge 0.7',
                            _name(
                                'efro',
                                _ACCOUNT_TEXT,
                                _capsule(
                                    texture=soft_circle,
                                    color=_ACCOUNT_CAPSULE,
                                    edge=0.7,
                                ),
                            ),
                            wide,
                        ),
                        _button(
                            'capsule edge 0.5',
                            _name(
                                'efro',
                                _ACCOUNT_TEXT,
                                _capsule(
                                    texture=soft_circle,
                                    color=_ACCOUNT_CAPSULE,
                                    edge=0.5,
                                ),
                            ),
                            wide,
                        ),
                        _button(
                            'soft icon, scale 1.4, edge 0.6',
                            _name(
                                'efro',
                                _ACCOUNT_TEXT,
                                _capsule(
                                    color=(0.15, 0.3, 0.15, 1.0),
                                    icon=soft_circle,
                                    icon_color=_ACCOUNT_BADGE,
                                    icon_scale=1.4,
                                    icon_edge=0.6,
                                ),
                            ),
                            wide,
                        ),
                        _button('account look', _account('efro'), wide),
                    ],
                ),
                _row(
                    'Capsule fit and alignment',
                    'The whole capsule is the shape fitted to the box.',
                    [
                        _button(
                            'wide, left',
                            _account('efro'),
                            wide,
                            h_align=dui2.HAlign.LEFT,
                        ),
                        _button(
                            'wide, right',
                            _account('efro'),
                            wide,
                            h_align=dui2.HAlign.RIGHT,
                        ),
                        _button(
                            'tall, top',
                            _account('efro'),
                            tall,
                            v_align=dui2.VAlign.TOP,
                        ),
                        _button(
                            'tall, bottom',
                            _account('efro'),
                            tall,
                            v_align=dui2.VAlign.BOTTOM,
                        ),
                        _button('tiny', _account('efro'), (90.0, 24.0)),
                        _button(
                            'long name',
                            _account('A Rather Long Name Indeed'),
                            wide,
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


def _spec(texture: bacommon.assetspec.TextureSpec) -> dict[str, Any]:
    """A texture in the wire form name definitions carry (a full spec).

    Serialized through the one public wire type that holds a texture
    spec, so this page never reaches into the spec itself.
    """
    out = dataclass_to_dict(bdep.ImageDepiction(texture=texture))['t']
    assert isinstance(out, dict)
    return out


def _name(
    text: str,
    color: tuple[float, float, float] | None = None,
    capsule: dict[str, Any] | None = None,
) -> bdep.NameDepiction:
    """A name depiction: basic text (+ color), optionally a capsule.

    Hand-built in the cloud's name-definition form (the schema is
    server-private; see bamaster ``baserver/character.py``).
    """
    basic: dict[str, Any] = {'t': text}
    if color is not None:
        basic['c'] = list(color)
    block: dict[str, Any] = {'b': basic}
    if capsule is not None:
        block['c'] = capsule
    return bdep.NameDepiction(json.dumps(block, separators=(',', ':')))


def _capsule(
    *,
    radius: float | None = None,
    color: tuple[float, float, float, float] | None = None,
    texture: dict[str, Any] | None = None,
    edge: float | None = None,
    icon: dict[str, Any] | None = None,
    icon_color: tuple[float, float, float, float] | None = None,
    icon_scale: float | None = None,
    icon_edge: float | None = None,
    text_inset: float | None = None,
    text_glow: float | None = None,
    insets: tuple[float, float] | None = None,
    tile: bool | None = None,
    tint_texture: dict[str, Any] | None = None,
    tint_colors: (
        tuple[
            tuple[float, float, float],
            tuple[float, float, float],
            tuple[float, float, float],
        ]
        | None
    ) = None,
) -> dict[str, Any]:
    """A name's capsule tier (unset values take the client defaults)."""
    out: dict[str, Any] = {}
    for key, val in (
        ('r', radius),
        ('cc', None if color is None else list(color)),
        ('ct', texture),
        ('cx', None if insets is None else list(insets)),
        ('cf', None if tile is None else (1 if tile else 0)),
        ('ctt', tint_texture),
        ('ctc1', None if tint_colors is None else list(tint_colors[0])),
        ('ctc2', None if tint_colors is None else list(tint_colors[1])),
        ('ctc3', None if tint_colors is None else list(tint_colors[2])),
        ('ce', edge),
        ('it', icon),
        ('ic', None if icon_color is None else list(icon_color)),
        ('is', icon_scale),
        ('ie', icon_edge),
        ('ti', text_inset),
        ('tg', text_glow),
    ):
        if val is not None:
            out[key] = val
    return out
