# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui test page for judging window layouts.

The root test page browses here at each
:class:`bacommon.docui.v2.WindowLayout`; the page itself is the same
either way. It carries the things layouts stress: control rows (label to
value distance), titles and short button rows at every alignment, and
long rows, which in a narrow column scroll within it.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.routes.docuitest
    from bacommon.langstr import LangStrSpec


def _lit(text: str) -> LangStrSpecValue:
    # A dev-only page, so baked literals throughout.
    return LangStrSpecValue.literal(text)


def layout_test_decos(debug: bool) -> list[bacommon.docui.v2.Decoration]:
    """Decorations for the test root page's layout-test buttons.

    :meta private:
    """
    from bauiv1 import _classicassets, _docuiv2testassets

    strs = _docuiv2testassets.strings

    return [
        dui2.Image(
            texture=_classicassets.textures.powerup_punch,
            position=(-70, 0),
            size=(40, 40),
            h_align=dui2.HAlign.LEFT,
        ),
        dui2.Image(
            texture=_classicassets.textures.powerup_speed,
            position=(0, 75),
            size=(35, 35),
            v_align=dui2.VAlign.TOP,
        ),
        dui2.Text(
            text=strs.layout.corner_tl.spec,
            position=(-70, 75),
            size=(50, 50),
            h_align=dui2.HAlign.LEFT,
            v_align=dui2.VAlign.TOP,
            debug=debug,
        ),
        dui2.Text(
            text=strs.layout.corner_tr.spec,
            position=(70, 75),
            size=(50, 50),
            h_align=dui2.HAlign.RIGHT,
            v_align=dui2.VAlign.TOP,
            debug=debug,
        ),
        dui2.Text(
            text=strs.layout.corner_bl.spec,
            position=(-70, -75),
            size=(50, 50),
            h_align=dui2.HAlign.LEFT,
            v_align=dui2.VAlign.BOTTOM,
            debug=debug,
        ),
        dui2.Text(
            text=strs.layout.corner_br.spec,
            position=(70, -75),
            size=(50, 50),
            h_align=dui2.HAlign.RIGHT,
            v_align=dui2.VAlign.BOTTOM,
            debug=debug,
        ),
    ]


def _buttons(count: int) -> list[dui2.Button]:
    return [
        dui2.Button(
            label=_lit(str(i + 1)),
            size=(120, 80),
            style=dui2.ButtonStyle.SQUARE,
        )
        for i in range(count)
    ]


def test_page_window_layouts(
    route: bacommon.docui.routes.docuitest.WindowLayouts,
) -> bacommon.docui.v2.Response:
    """Assorted rows for eyeballing a window layout."""
    # pylint: disable=cyclic-import
    import bacommon.docui.routes.docuitest as rt
    from bauiv1lib.docuitestwidgets import _flavor_label

    wstate = rt.WidgetTestState
    arrived = route.get_state(wstate)
    state = wstate() if arrived is None else arrived
    debug = route.debug
    left, center, right = (
        dui2.HAlign.LEFT,
        dui2.HAlign.CENTER,
        dui2.HAlign.RIGHT,
    )

    def _row(
        title: str,
        count: int,
        align: dui2.HAlign,
        footnote: str | None = None,
    ) -> dui2.ButtonRow:
        return dui2.ButtonRow(
            title=_lit(title),
            title_align=align,
            content_align=align,
            footnote=None if footnote is None else _lit(footnote),
            debug=debug,
            buttons=_buttons(count),
        )

    return dui2.Response(
        page=dui2.Page(
            title=_lit('Window Layouts'),
            state=state.encode(),
            rows=[
                # A section of input rows, with a heading and a closing
                # note (selecting its first row brings the heading into
                # view; its last, the note).
                dui2.Section(
                    title=_lit('Inputs'),
                    subtitle=_lit('A section heading and its subtitle.'),
                    footnote=_lit('A section note, under its last row.'),
                    debug=debug,
                    rows=[
                        wstate.checkbox_row(
                            lambda s: s.plain,
                            label=_lit('A checkbox'),
                            # A row title under a section heading: the
                            # heading is larger, so the two read as
                            # levels.
                            title=_lit('A row title'),
                            debug=debug,
                        ),
                        wstate.choice_row(
                            lambda s: s.flavor,
                            choice_label=_flavor_label,
                            label=_lit('A choice'),
                            footnote=_lit('Footnote under a control row.'),
                            debug=debug,
                        ),
                        wstate.slider_row(
                            lambda s: s.volume,
                            min_value=0.0,
                            max_value=1.0,
                            increment=0.05,
                            as_percent=True,
                            label=_lit('A slider'),
                            debug=debug,
                        ),
                        wstate.text_input_row(
                            lambda s: s.text_medium,
                            label=_lit('A text input'),
                            debug=debug,
                        ),
                    ],
                ),
                # A centered heading, with a header band, over the
                # button rows.
                dui2.Section(
                    title=_lit('Button Rows'),
                    title_align=center,
                    header_height=30.0,
                    header_decorations_center=[
                        dui2.Text(
                            text=_lit('(a header band)'),
                            position=(0.0, 0.0),
                            size=(300.0, 30.0),
                            scale=0.6,
                            color=(0.6, 0.74, 0.6, 1.0),
                        )
                    ],
                    debug=debug,
                    rows=[
                        _row('Short row (left)', 3, left),
                        _row('Short row (center)', 3, center),
                        _row(
                            'Short row (right)',
                            3,
                            right,
                            footnote='Right-aligned footnote.',
                        ),
                        _row(
                            'Long row (left)',
                            16,
                            left,
                            footnote=(
                                'Starts at the left; scrolls within its'
                                ' area.'
                            ),
                        ),
                        _row('Long row (center)', 16, center),
                        _row(
                            'Long row (right)',
                            16,
                            right,
                            footnote=(
                                'Ends at the right; scrolls within its' ' area.'
                            ),
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    center_content=True,
                    buttons=[
                        dui2.Button(
                            label=_lit('Hide Debug' if debug else 'Show Debug'),
                            size=(200, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=rt.WindowLayouts(debug=not debug).replace(),
                        ),
                    ],
                ),
            ],
        )
    )


def test_page_wide_fit(
    route: bacommon.docui.routes.docuitest.WideFit,
) -> bacommon.docui.v2.Response:
    """A row exactly as big as wide pages get.

    :meta private:
    """
    from bauiv1lib.docui._layout import (
        BUTTON_ROW_EDGE_INSET,
        WIDE_PAGE_ROWS_HEIGHT,
        WIDE_PAGE_WIDTH,
    )

    # A hair under, so float rounding can't tip it into scrolling (or,
    # when testing the edge, a hair over).
    rowheight = WIDE_PAGE_ROWS_HEIGHT + (1.0 if route.over else -0.5)

    # A button row's h-scroll content is its buttons, spacing and
    # padding plus the room its padding starts in from the column's
    # edges; it fits when all that is no wider than the page.
    spacing = 15.0
    rowwidth = WIDE_PAGE_WIDTH + (1.0 if route.wide_over else -0.5)

    # Square-button art draws a bit past its bounds; padding gives it
    # room inside the row so the page edges don't clip it.
    pad = 15.0
    bheight = rowheight - 2.0 * pad
    bwidth = (
        rowwidth - 2.0 * BUTTON_ROW_EDGE_INSET - 2.0 * pad - 2.0 * spacing
    ) / 3

    # (Wider's width follows the screen, so only wide can overflow it.)
    width_buttons: list[bacommon.docui.v2.Button] = (
        []
        if route.wider
        else [
            dui2.Button(
                label=_lit(
                    f'Width {rowwidth:.1f}: '
                    + (
                        'fits;\ntap to go 1 over'
                        if not route.wide_over
                        else '1 over\n(should scroll);\ntap to fit'
                    )
                ),
                label_scale=0.7,
                size=(bwidth, bheight),
                action=replace(route, wide_over=not route.wide_over).replace(),
            )
        ]
    )

    return dui2.Response(
        page=dui2.Page(
            title=_lit('Wider Fit' if route.wider else 'Wide Fit'),
            rows=[
                dui2.ButtonRow(
                    padding_top=pad,
                    padding_bottom=pad,
                    padding_left=pad,
                    padding_right=pad,
                    button_spacing=spacing,
                    content_align=dui2.HAlign.CENTER,
                    debug=True,
                    buttons=[
                        *width_buttons,
                        dui2.Button(
                            label=_lit(
                                f'Height {rowheight:.1f}: '
                                + (
                                    'fits;\ntap to go 1 over'
                                    if not route.over
                                    else '1 over\n(should scroll);\ntap to fit'
                                )
                            ),
                            label_scale=0.7,
                            size=(bwidth, bheight),
                            action=replace(
                                route, over=not route.over
                            ).replace(),
                        ),
                        dui2.Button(
                            # (Wider's page width follows the screen.)
                            label=_lit(
                                f'Page height {WIDE_PAGE_ROWS_HEIGHT:.1f}'
                                if route.wider
                                else f'Page {WIDE_PAGE_WIDTH:.1f}'
                                f' x {WIDE_PAGE_ROWS_HEIGHT:.1f}'
                            ),
                            label_scale=0.7,
                            size=(bwidth, bheight),
                        ),
                    ],
                )
            ],
        )
    )


def test_page_bounds() -> bacommon.docui.v2.Response:
    """Button-style bounds tests (v2 mirror of '/boundstests')."""
    from bauiv1 import _builtinassets, _docuiv2testassets

    strs = _docuiv2testassets.strings

    def _nm(style: bacommon.docui.v2.ButtonStyle) -> LangStrSpec:
        # Code-literal pass-through: renders the raw enum name
        # verbatim in every locale.
        return strs.common.code_literal(
            text=f'{type(style).__name__}.{style.name}'
        ).spec

    def _hello_row(
        title: LangStrSpec,
        sizes: list[tuple[float, float]],
        style: bacommon.docui.v2.ButtonStyle,
        texture: bool = False,
    ) -> bacommon.docui.v2.ButtonRow:
        return dui2.ButtonRow(
            title=title,
            buttons=[
                dui2.Button(
                    label=strs.layout.hello.spec,
                    size=size,
                    style=style,
                    texture=(
                        _builtinassets.textures.white if texture else None
                    ),
                    color=(1, 0, 0, 0.3) if texture else None,
                    debug=True,
                )
                for size in sizes
            ],
        )

    styles = dui2.ButtonStyle

    return dui2.Response(
        page=dui2.Page(
            title=strs.layout.bounds_tests_title.spec,
            rows=[
                _hello_row(
                    _nm(styles.SQUARE),
                    [(300, 300), (200, 200), (100, 100)],
                    styles.SQUARE,
                ),
                _hello_row(
                    _nm(styles.SQUARE_WIDE),
                    [(400, 200), (200, 250), (60, 100)],
                    styles.SQUARE_WIDE,
                ),
                _hello_row(
                    strs.layout.background_texture.spec,
                    [(300, 300), (200, 200), (100, 100)],
                    styles.SQUARE,
                    texture=True,
                ),
                _hello_row(
                    _nm(styles.TAB),
                    [(400, 100), (200, 50), (100, 60)],
                    styles.TAB,
                ),
                _hello_row(
                    _nm(styles.LARGER),
                    [(500, 100), (200, 50), (100, 60)],
                    styles.LARGER,
                ),
                _hello_row(
                    _nm(styles.LARGE),
                    [(400, 100), (200, 50), (100, 60)],
                    styles.LARGE,
                ),
                _hello_row(
                    _nm(styles.MEDIUM),
                    [(300, 100), (200, 50), (100, 60)],
                    styles.MEDIUM,
                ),
                _hello_row(
                    _nm(styles.SMALL),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.SMALL,
                ),
                _hello_row(
                    _nm(styles.BACK),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.BACK,
                ),
                _hello_row(
                    _nm(styles.BACK_SMALL),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.BACK_SMALL,
                ),
            ],
        )
    )
