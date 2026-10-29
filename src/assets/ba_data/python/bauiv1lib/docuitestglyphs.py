# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui glyphs test page.

Every custom glyph (:class:`bacommon.text.SpecialChar`), drawn large
and centered on a crosshair, inside a debug box sized to what text
measuring reports for it (``get_string_width()``/``get_string_height()``,
which is what layout code centers by). A glyph whose ink sits off the
crosshair, or off-center in its box, will look off-center wherever it
is used as a centered label. Some ordinary characters come first for
comparison, and a row of small buttons shows the glyphs buttons use
most, with lines through their bounds' centers. Checkboxes at the top
turn the crosshairs and bounds boxes on and off.
"""

from typing import TYPE_CHECKING

import bauiv1 as bui
from bacommon.text import SpecialChar
from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2
import bacommon.docui.routes.docuitest as rt

if TYPE_CHECKING:
    import bacommon.docui.routes.docuitest
    import bacommon.docui.v2

#: Glyph cells: their size, the glyphs' scale in them, and how far
#: above a cell's center its glyph's anchor sits (its name goes below).
_CELL = 120.0
_GLYPH_SCALE = 2.0
_GLYPH_LIFT = 10.0

#: Crosshair lines. At least a pixel wide at every ui-scale, so they
#: don't shimmer as the window tilts.
_LINE_COLOR = (1.0, 1.0, 0.0, 0.6)
_LINE_WIDTH = 2.0

#: Where a small clean-layout button anchors a centered label, as
#: fractions of its size (mirrors kSmallFitLabelCenterX/Y in the
#: engine's button_widget.cc; keep the two in sync).
_SMALL_LABEL_CENTER = (0.47, 0.545)

#: Ordinary characters shown alongside, for comparison.
_PLAIN = ('H', 'x', 'X', '+', '-', '0', '?')

#: Characters our font lacks, which the OS renders (whose placement
#: is separate from our font's).
_OS_RENDERED = ('Ж', 'Я', 'Щ', 'あ', '中', '한', 'ש')

#: Everything the big font has (lower case shares upper case's).
_BIG = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?.-:%#\u00a1'

#: Glyphs shown as small-button labels.
_BUTTON_GLYPHS = (
    SpecialChar.CLOSE.value,
    SpecialChar.BACK.value,
    '+',
    '-',
    '?',
)


def _lit(text: str) -> LangStrSpecValue:
    return LangStrSpecValue.literal(text)


def _crosshair(
    center: tuple[float, float], size: tuple[float, float]
) -> list[dui2.Decoration]:
    """Lines crossing at a point, spanning a size."""
    from bauiv1 import _commonassets

    return [
        dui2.Image(
            texture=_commonassets.textures.white,
            position=center,
            size=lsize,
            color=_LINE_COLOR,
        )
        for lsize in ((size[0], _LINE_WIDTH), (_LINE_WIDTH, size[1]))
    ]


#: Icons shown in their superscript form before sample names.
_SUPERSCRIPT_SAMPLES = (
    SpecialChar.FEDORA,
    SpecialChar.CROWN,
    SpecialChar.SKULL,
    SpecialChar.POTATO,
    SpecialChar.ANNIVERSARY_15_BOMB,
    SpecialChar.FLAG_UNITED_STATES,
    SpecialChar.V2_LOGO,
    SpecialChar.DISCORD_LOGO,
)


def _superscript_sample(char: SpecialChar) -> dui2.Button:
    """An icon full-size, then superscript before two sample names."""
    full = char.full_size
    assert full is not None
    return dui2.Button(
        # (Room for the full-size icon to sit clear of the left edge.)
        size=(340.0, 120.0),
        color=(0.12, 0.12, 0.16, 1.0),
        decorations=[
            dui2.Text(
                text=_lit(full.value),
                position=(-110.0, 0.0),
                size=(80.0, 80.0),
                scale=2.0,
            ),
            dui2.Text(
                text=_lit(f'{char.value}efro'),
                position=(60.0, 22.0),
                size=(200.0, 40.0),
                scale=1.3,
            ),
            dui2.Text(
                text=_lit(f'{char.value}Player Name'),
                position=(60.0, -22.0),
                size=(200.0, 40.0),
                scale=0.9,
            ),
        ],
    )


def _cell(
    glyph: str, name: str, show: rt.GlyphsState, *, big: bool = False
) -> dui2.Button:
    """A glyph on a crosshair, in a box its measured size."""
    width = (
        bui.get_string_width(glyph, suppress_warning=True, big=big)
        * _GLYPH_SCALE
    )
    height = bui.get_string_height(glyph, suppress_warning=True) * _GLYPH_SCALE
    decorations: list[dui2.Decoration] = []
    if show.crosshairs:
        decorations += _crosshair(
            (0.0, _GLYPH_LIFT), (_CELL - 10.0, _CELL - 30.0)
        )
    decorations += [
        dui2.Text(
            text=_lit(glyph),
            position=(0.0, _GLYPH_LIFT),
            # A hair over its measured size, so it never shrinks.
            size=(width + 1.0, height + 1.0),
            scale=_GLYPH_SCALE,
            debug=show.bounds,
            big=big,
        ),
        dui2.Text(
            text=_lit(f'{name}  {width:.0f}x{height:.0f}'),
            position=(0.0, -0.5 * _CELL + 12.0),
            size=(_CELL - 10.0, 14.0),
            scale=0.4,
        ),
    ]
    return dui2.Button(
        size=(_CELL, _CELL),
        color=(0.12, 0.12, 0.16, 1.0),
        decorations=decorations,
    )


def _small_button(
    glyph: str, size: tuple[float, float], show: rt.GlyphsState
) -> dui2.Button:
    """A small button labeled with a glyph; lines cross its label anchor.

    (Decorations are placed relative to the button's center.)
    """
    width, height = size
    anchor = (
        (_SMALL_LABEL_CENTER[0] - 0.5) * width,
        (_SMALL_LABEL_CENTER[1] - 0.5) * height,
    )
    return dui2.Button(
        label=_lit(glyph),
        style=dui2.ButtonStyle.SMALL,
        size=size,
        decorations=(
            _crosshair(anchor, (width + 30.0, height + 30.0))
            if show.crosshairs
            else []
        ),
    )


def test_page_glyphs(
    route: bacommon.docui.routes.docuitest.Glyphs,
) -> bacommon.docui.v2.Response:
    """Testing custom glyphs' placement."""
    arrived = route.get_state(rt.GlyphsState)
    show = rt.GlyphsState() if arrived is None else arrived

    def _grid(
        title: str, subtitle: str, buttons: list[dui2.Button]
    ) -> list[dui2.Row]:
        return [
            dui2.TitleRow(_lit(title)),
            dui2.SubtitleRow(_lit(subtitle)),
            dui2.ButtonRow(
                layout=dui2.ButtonRowLayout.GRID,
                buttons=buttons,
            ),
        ]

    # Either checkbox rebuilds the page with the change.
    rebuild = rt.Glyphs().replace(default_sound=False)
    return dui2.Response(
        page=dui2.Page(
            title=_lit('Glyphs'),
            state=show.encode(),
            rows=[
                rt.GlyphsState.checkbox_row(
                    lambda s: s.crosshairs,
                    label=_lit('Show crosshairs'),
                    on_change=rebuild,
                ),
                rt.GlyphsState.checkbox_row(
                    lambda s: s.bounds,
                    label=_lit('Show measured bounds'),
                    on_change=rebuild,
                ),
                dui2.TitleRow(_lit('In small buttons')),
                dui2.SubtitleRow(
                    _lit(
                        'The lines cross where each button anchors its'
                        ' label: a little up and left of its art\'s'
                        ' center, so labels read as centered on it.'
                    )
                ),
                dui2.ButtonRow(
                    buttons=[
                        _small_button(g, size, show)
                        for size in ((55.0, 47.0), (64.0, 55.0))
                        for g in _BUTTON_GLYPHS
                    ],
                ),
                *_grid(
                    'Plain characters',
                    'For comparison. Each is centered on its crosshair, in'
                    ' a box its measured size (what layout centers by;'
                    ' its height is always a full text row).',
                    [_cell(c, repr(c), show) for c in _PLAIN],
                ),
                *_grid(
                    'OS-rendered characters',
                    'Ones our font lacks, which the OS draws; they are'
                    ' placed separately from our font\'s.',
                    [_cell(c, f'U+{ord(c):04X}', show) for c in _OS_RENDERED],
                ),
                *_grid(
                    'Big font',
                    'Every character the big font has (text with big set;'
                    ' lower case draws as upper).',
                    [_cell(c, repr(c), show, big=True) for c in _BIG],
                ),
                *_grid(
                    'Custom glyphs',
                    'Every SpecialChar, likewise. Icons show their full-size'
                    ' forms (superscript forms are derived from them; see'
                    ' below).',
                    [
                        _cell(c.value, c.name.lower(), show)
                        for c in SpecialChar
                        if not c.is_superscript
                    ],
                ),
                dui2.TitleRow(_lit('Superscript icons')),
                dui2.SubtitleRow(
                    _lit(
                        'Icons\' raised forms, as shown before names, next to'
                        ' their full-size twins. All are derived by one scale'
                        ' and raise (kSuperscriptIcon* in text_graphics.cc).'
                    )
                ),
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.GRID,
                    buttons=[
                        _superscript_sample(c) for c in _SUPERSCRIPT_SAMPLES
                    ],
                ),
            ],
        )
    )
