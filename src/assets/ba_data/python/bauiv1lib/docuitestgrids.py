# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui button grids test page.

:meta private:
"""

from dataclasses import replace
from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue

if TYPE_CHECKING:
    import bacommon.docui.routes.docuitest
    import bacommon.docui.v2
    from bacommon.assetspec import TextureSpec


def _lit(text: str) -> LangStrSpecValue:
    # Dev-only page, so baked literals.
    return LangStrSpecValue.literal(text)


def _btn(
    label: str,
    size: tuple[float, float] = (100.0, 100.0),
    *,
    style: dui2.ButtonStyle = dui2.ButtonStyle.SQUARE,
) -> bacommon.docui.v2.Button:
    """A do-nothing button."""
    return dui2.Button(
        label=_lit(label), size=size, style=style, action=dui2.Local()
    )


def _wide(label: str) -> bacommon.docui.v2.Button:
    return _btn(label, (180.0, 70.0), style=dui2.ButtonStyle.MEDIUM)


def _icon_btn(
    texture: TextureSpec, size: float = 80.0
) -> bacommon.docui.v2.Button:
    """A do-nothing square button showing an icon."""
    return dui2.Button(
        size=(size, size),
        style=dui2.ButtonStyle.SQUARE,
        action=dui2.Local(),
        decorations=[
            dui2.Image(
                texture=texture,
                position=(0, 0),
                size=(size * 0.7, size * 0.7),
            )
        ],
    )


def _numbered(
    count: int, size: tuple[float, float] = (100.0, 100.0)
) -> list[bacommon.docui.v2.Button]:
    return [_btn(str(i + 1), size) for i in range(count)]


def _mixed() -> list[bacommon.docui.v2.Button]:
    # (Twice through, so it wraps at the widest layouts too.)
    return 2 * [
        _btn('S', (60.0, 60.0)),
        _wide('Wide'),
        _btn('Tall', (80.0, 140.0)),
        _btn('M'),
        _btn('S', (60.0, 60.0)),
        _btn('M'),
        _wide('Wide'),
    ]


def test_page_button_grids(
    route: bacommon.docui.routes.docuitest.ButtonGrids,
) -> bacommon.docui.v2.Response:
    """Grid button rows: columns, cells, alignment and navigation.

    :meta private:
    """
    from bauiv1 import _classicassets
    from bauiv1lib.docuitestlayouts import with_test_viewer

    tex = _classicassets.textures
    debug = route.debug

    def _grid(
        row: bacommon.docui.v2.ButtonRow,
        *,
        title: str | None = None,
        subtitle: str | None = None,
        footnote: str | None = None,
    ) -> list[bacommon.docui.v2.Row]:
        """A grid button row with its texts as standalone text rows."""
        return [
            *([] if title is None else [dui2.TitleRow(_lit(title))]),
            *([] if subtitle is None else [dui2.SubtitleRow(_lit(subtitle))]),
            replace(row, layout=dui2.ButtonRowLayout.GRID, debug=debug),
            *([] if footnote is None else [dui2.FootnoteRow(_lit(footnote))]),
        ]

    icons = [
        tex.powerup_bomb,
        tex.powerup_curse,
        tex.powerup_health,
        tex.powerup_ice_bombs,
        tex.powerup_impact_bombs,
        tex.powerup_land_mines,
        tex.powerup_punch,
        tex.powerup_shield,
        tex.powerup_speed,
        tex.powerup_sticky_bombs,
    ]

    return dui2.Response(
        page=with_test_viewer(
            route.viewer_side,
            route.theme,
            title=_lit('Button Grids'),
            rows=[
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FIXED,
                    buttons=[
                        dui2.Button(
                            label=_lit('Hide Debug' if debug else 'Show Debug'),
                            size=(180.0, 60.0),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=replace(route, debug=not debug).replace(),
                        )
                    ],
                ),
                *_grid(
                    dui2.ButtonRow(buttons=_numbered(14)),
                    title='Auto columns (as many as fit)',
                    subtitle=(
                        'Up/down should move within a column; down from'
                        ' above the short last line goes to its last'
                        ' button.'
                    ),
                ),
                # The same with generous scale bounds at each alignment
                # (which a grid spanning the width ignores; its short
                # last line should start at the left in all three),
                # then a fill row to compare its edges against.
                *(
                    row
                    for align in dui2.HAlign
                    for row in _grid(
                        dui2.ButtonRow(
                            buttons=_numbered(14),
                            grid_min_scale=0.5,
                            grid_max_scale=2.0,
                            content_align=align,
                        ),
                        title=(
                            f'The same, scaling 0.5-2.0 to span,'
                            f' {align.name.lower()}-aligned'
                        ),
                    )
                ),
                dui2.TitleRow(_lit('A fill row, for comparing edges')),
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    buttons=[
                        _btn(
                            'Left', (100.0, 60.0), style=dui2.ButtonStyle.LARGE
                        ),
                        _btn(
                            'Right', (100.0, 60.0), style=dui2.ButtonStyle.LARGE
                        ),
                    ],
                    debug=debug,
                ),
                dui2.FootnoteRow(
                    _lit(
                        'The scaled grids above should span exactly this'
                        ' wide, everything in them scaled alike.'
                    )
                ),
                *_grid(
                    dui2.ButtonRow(
                        buttons=_numbered(10),
                        grid_columns=4,
                        content_align=dui2.HAlign.CENTER,
                    ),
                    title='4 columns, centered, short last line',
                    footnote=(
                        'The grid centers as a block; its last line'
                        " starts at the grid's left so columns stay"
                        ' lined up.'
                    ),
                ),
                *_grid(
                    dui2.ButtonRow(
                        buttons=_numbered(3),
                        content_align=dui2.HAlign.RIGHT,
                    ),
                    title='Fewer buttons than fit, right-aligned',
                ),
                *_grid(
                    dui2.ButtonRow(
                        buttons=_numbered(8),
                        grid_columns=3,
                        content_align=dui2.HAlign.CENTER,
                    ),
                    title='Exactly 3 columns, centered',
                ),
                # Scale bounds, in sets that differ only in them: a grid
                # with a leftover under a column (how much depending on
                # the layout's width) at tight, typical and shrink-only
                # bounds, then grids with lots of room to spare.
                *(
                    row
                    for lo, hi, note in (
                        (
                            0.98,
                            1.02,
                            'Tight bounds: spans the width only when it'
                            ' nearly does already; otherwise grows 2% and'
                            ' falls short.',
                        ),
                        (
                            0.9,
                            1.1,
                            'Typical bounds: grows to fill the room, or'
                            ' shrinks to fit one more column, whichever is'
                            ' the smaller change.',
                        ),
                        (
                            0.85,
                            1.0,
                            'Shrink only: spans the width by fitting one'
                            ' more column when it can; never grows.',
                        ),
                    )
                    for row in _grid(
                        dui2.ButtonRow(
                            buttons=_numbered(12),
                            grid_cell_width=160.0,
                            grid_min_scale=lo,
                            grid_max_scale=hi,
                        ),
                        title=f'160-wide cells, scale {lo:g}-{hi:g}',
                        footnote=note,
                    )
                ),
                *(
                    row
                    for hi, note in (
                        (
                            1.1,
                            'Nowhere near the width: grows 10% and stays'
                            ' centered.',
                        ),
                        (
                            10.0,
                            'Grows until the pair spans the width (or the'
                            ' buttons get very big).',
                        ),
                    )
                    for row in _grid(
                        dui2.ButtonRow(
                            buttons=_numbered(2),
                            grid_min_scale=0.9,
                            grid_max_scale=hi,
                            content_align=dui2.HAlign.CENTER,
                        ),
                        title=f'Two buttons, centered, scale up to {hi:g}',
                        footnote=note,
                    )
                ),
                *(
                    row
                    for hi, note in (
                        (
                            1.1,
                            'Grows 10%, still short of the width,'
                            ' left-aligned.',
                        ),
                        (
                            10.0,
                            'Grows until its 3 columns span the width.',
                        ),
                    )
                    for row in _grid(
                        dui2.ButtonRow(
                            buttons=_numbered(6),
                            grid_columns=3,
                            grid_max_scale=hi,
                        ),
                        title=f'Exactly 3 columns, scale up to {hi:g}',
                        footnote=note,
                    )
                ),
                *_grid(
                    dui2.ButtonRow(
                        buttons=_numbered(20, (140.0, 140.0)),
                        grid_columns=10,
                    ),
                    title='10 columns of big buttons (shrinks to fit)',
                ),
                *_grid(
                    dui2.ButtonRow(
                        buttons=[_icon_btn(t, 70.0) for t in icons],
                        grid_cell_width=160.0,
                        grid_cell_height=110.0,
                        grid_line_spacing=25.0,
                        content_align=dui2.HAlign.CENTER,
                    ),
                    title='Icons in roomy cells (160x110, 25 between lines)',
                ),
                *_grid(
                    dui2.ButtonRow(buttons=_mixed()),
                    title='Mixed sizes in auto cells (cells fit the biggest)',
                ),
                *_grid(
                    dui2.ButtonRow(
                        buttons=_mixed(),
                        grid_cell_width=90.0,
                        grid_cell_height=90.0,
                    ),
                    title='Mixed sizes in 90x90 cells (big ones shrink)',
                ),
                *_grid(
                    dui2.ButtonRow(
                        buttons=[
                            _wide(label)
                            for label in (
                                'Alpha',
                                'Bravo',
                                'Charlie',
                                'Delta',
                                'Echo',
                                'Foxtrot',
                            )
                        ],
                        grid_cell_width=200.0,
                        button_spacing=5.0,
                    ),
                    title='Cell width 200, height from the buttons',
                ),
                *_grid(
                    dui2.ButtonRow(
                        buttons=_numbered(3),
                        grid_cell_width=2000.0,
                    ),
                    title='Cells wider than the row (shrinks to fit)',
                    footnote=(
                        '2000-wide cells: one column, the whole grid'
                        ' shrunk until a cell fits.'
                    ),
                ),
                # Down out of the last grid should land here, and up
                # from here back into its bottom line.
                dui2.TitleRow(_lit('A fill row after the grids')),
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    buttons=[
                        _btn(
                            'One', (100.0, 60.0), style=dui2.ButtonStyle.LARGE
                        ),
                        _btn(
                            'Two', (100.0, 60.0), style=dui2.ButtonStyle.LARGE
                        ),
                    ],
                    debug=debug,
                ),
            ],
        )
    )
