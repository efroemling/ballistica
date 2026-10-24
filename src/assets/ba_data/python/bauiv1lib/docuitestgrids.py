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

    tex = _classicassets.textures
    debug = route.debug

    def _grid(row: bacommon.docui.v2.ButtonRow) -> bacommon.docui.v2.ButtonRow:
        return replace(row, layout=dui2.ButtonRowLayout.GRID, debug=debug)

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
        page=dui2.Page(
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
                _grid(
                    dui2.ButtonRow(
                        title=_lit('Auto columns (as many as fit)'),
                        subtitle=_lit(
                            'Up/down should move within a column; down from'
                            ' above the short last line goes to its last'
                            ' button.'
                        ),
                        buttons=_numbered(14),
                    )
                ),
                # The same with a generous grid_max_spread at each
                # alignment (which a stretched grid's full lines ignore;
                # its short last line should start at the left in all
                # three), then a fill row to compare its edges against.
                *(
                    _grid(
                        dui2.ButtonRow(
                            title=_lit(
                                f'The same with grid_max_spread=1000,'
                                f' {align.name.lower()}-aligned'
                            ),
                            buttons=_numbered(14),
                            grid_max_spread=1000.0,
                            content_align=align,
                        )
                    )
                    for align in dui2.HAlign
                ),
                dui2.ButtonRow(
                    title=_lit('A fill row, for comparing edges'),
                    footnote=_lit(
                        'The stretched grids above should span exactly this'
                        ' wide, their buttons at their own size.'
                    ),
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
                _grid(
                    dui2.ButtonRow(
                        title=_lit('4 columns, centered, short last line'),
                        footnote=_lit(
                            'The grid centers as a block; its last line'
                            " starts at the grid's left so columns stay"
                            ' lined up.'
                        ),
                        buttons=_numbered(10),
                        grid_columns=4,
                        content_align=dui2.HAlign.CENTER,
                    )
                ),
                _grid(
                    dui2.ButtonRow(
                        title=_lit('Fewer buttons than fit, right-aligned'),
                        buttons=_numbered(3),
                        content_align=dui2.HAlign.RIGHT,
                    )
                ),
                _grid(
                    dui2.ButtonRow(
                        title=_lit('Exactly 3 columns, centered'),
                        buttons=_numbered(8),
                        grid_columns=3,
                        content_align=dui2.HAlign.CENTER,
                    )
                ),
                # grid_max_spread caps, in pairs that differ only in it:
                # a grid with a smallish leftover (under a column, how
                # much depending on the layout's width) at a small cap
                # and a generous one, then two with lots of room to
                # spare at a moderate cap and a huge one.
                *(
                    _grid(
                        dui2.ButtonRow(
                            title=_lit(
                                f'160-wide cells, grid_max_spread={amt:g}'
                            ),
                            footnote=_lit(note),
                            buttons=_numbered(12),
                            grid_cell_width=160.0,
                            grid_max_spread=amt,
                        )
                    )
                    for amt, note in (
                        (
                            4.0,
                            'Each gap grows by at most 4, so it usually'
                            ' falls a little short of the right edge.',
                        ),
                        (
                            1000.0,
                            'The same, but the cap never binds, so it'
                            ' always spans the width.',
                        ),
                    )
                ),
                *(
                    _grid(
                        dui2.ButtonRow(
                            title=_lit(
                                f'Two buttons, centered, grid_max_spread='
                                f'{amt:g}'
                            ),
                            footnote=_lit(note),
                            buttons=_numbered(2),
                            grid_max_spread=amt,
                            content_align=dui2.HAlign.CENTER,
                        )
                    )
                    for amt, note in (
                        (
                            40.0,
                            'Its one gap grows by 40, and the pair stays'
                            ' centered.',
                        ),
                        (
                            1000.0,
                            'Spreads all the way: one button at each edge.',
                        ),
                    )
                ),
                *(
                    _grid(
                        dui2.ButtonRow(
                            title=_lit(
                                f'Exactly 3 columns, grid_max_spread={amt:g}'
                            ),
                            footnote=_lit(note),
                            buttons=_numbered(6),
                            grid_columns=3,
                            grid_max_spread=amt,
                        )
                    )
                    for amt, note in (
                        (
                            40.0,
                            'Each gap grows by 40, still well short of'
                            ' the width, left-aligned.',
                        ),
                        (
                            1000.0,
                            'Spreads all the way: wide gaps between'
                            ' columns.',
                        ),
                    )
                ),
                _grid(
                    dui2.ButtonRow(
                        title=_lit(
                            '10 columns of big buttons (shrinks to fit)'
                        ),
                        buttons=_numbered(20, (140.0, 140.0)),
                        grid_columns=10,
                    )
                ),
                _grid(
                    dui2.ButtonRow(
                        title=_lit(
                            'Icons in roomy cells (160x110, 25 between lines)'
                        ),
                        buttons=[_icon_btn(t, 70.0) for t in icons],
                        grid_cell_width=160.0,
                        grid_cell_height=110.0,
                        grid_line_spacing=25.0,
                        content_align=dui2.HAlign.CENTER,
                    )
                ),
                _grid(
                    dui2.ButtonRow(
                        title=_lit(
                            'Mixed sizes in auto cells (cells fit the biggest)'
                        ),
                        buttons=_mixed(),
                    )
                ),
                _grid(
                    dui2.ButtonRow(
                        title=_lit(
                            'Mixed sizes in 90x90 cells (big ones shrink)'
                        ),
                        buttons=_mixed(),
                        grid_cell_width=90.0,
                        grid_cell_height=90.0,
                    )
                ),
                _grid(
                    dui2.ButtonRow(
                        title=_lit('Cell width 200, height from the buttons'),
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
                    )
                ),
                _grid(
                    dui2.ButtonRow(
                        title=_lit('Cells wider than the row (shrinks to fit)'),
                        footnote=_lit(
                            '2000-wide cells: one column, the whole grid'
                            ' shrunk until a cell fits.'
                        ),
                        buttons=_numbered(3),
                        grid_cell_width=2000.0,
                    )
                ),
                # Down out of the last grid should land here, and up
                # from here back into its bottom line.
                dui2.ButtonRow(
                    title=_lit('A fill row after the grids'),
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
