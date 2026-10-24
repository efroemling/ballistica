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
from typing import TYPE_CHECKING, assert_never

from bacommon.langstr import LangStrSpecValue
import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.routes.docuitest
    from bacommon.langstr import LangStrSpec


def _layout_description(layout: dui2.WindowLayout) -> str:
    """What a layout is for (shown on the page after its name)."""
    # pylint: disable=too-many-return-statements
    # (Other layouts are named by their enum names, so renames follow.)
    wl = dui2.WindowLayout
    match layout:
        case dui2.WindowLayout.SMALL:
            return (
                'Use this layout for small dialogs or bits of content you'
                ' want to frame tightly. If you are showing enough to need'
                ' to scroll here, you should choose a bigger layout. This'
                ' layout provides the same narrow horizontal space at all'
                ' ui scales, so content can be tailored to fit it.'
            )
        case dui2.WindowLayout.SMALL_TALL:
            return (
                f'Has the same fixed width as {wl.SMALL.name} at all ui'
                ' scales, but has a larger fixed height on medium/large ui'
                ' scales. A good step up once content no longer fits on'
                f' {wl.SMALL.name} without scrolling.'
            )
        case dui2.WindowLayout.SMALL_TALLER:
            return (
                f'Has the same fixed width as {wl.SMALL.name} at all ui'
                ' scales, but has a variable height that grows to fit your'
                ' screen on'
                ' medium/large ui scales. Use this if you are showing lots'
                ' of content where scrolling will always be necessary.'
            )
        case dui2.WindowLayout.WIDE:
            return (
                'Use this layout to show content designed to fill a'
                ' standard phone shaped screen area. This provides a fixed'
                ' width and mostly fixed height (possibly more on phone'
                ' screens) so content can be tailored to fit it.'
            )
        case dui2.WindowLayout.WIDE_TALL:
            return (
                f'Provides the same fixed width as {wl.WIDE.name}, but a'
                ' larger fixed amount of vertical space on medium and'
                ' large ui scales.'
            )
        case dui2.WindowLayout.WIDE_TALLER:
            return (
                f'Provides the same fixed width as {wl.WIDE.name}, but with'
                ' a height that expands to take advantage of all screen'
                ' sizes. Use this when you expect to have a lot of'
                ' scrollable wide content.'
            )
        case dui2.WindowLayout.WIDER:
            return (
                'This layout provides the same mostly-fixed height as'
                f' {wl.WIDE.name}, but expands to take advantage of your'
                ' full screen width at all ui scales. Use this when showing'
                ' large amounts of horizontally scrollable content.'
            )
        case dui2.WindowLayout.LARGE:
            return (
                'This layout expands to use most of your screen area in all'
                ' ui scales, so use it only when you can actually fill that'
                ' space on a large screen. Good for things like stores and'
                ' inventories where there might be lots of vertical and'
                ' horizontal scrolling happening.'
            )
        case dui2.WindowLayout.VIEWER_NARROW:
            return (
                f'Like {wl.VIEWER.name}, but with a controls column two'
                ' thirds as wide, giving the viewer more of the room (and a'
                ' somewhat narrower window at medium and large ui scales).'
                ' Use this when a page has just a few simple controls'
                ' beside a big view.'
            )
        case dui2.WindowLayout.VIEWER:
            return (
                f'Provides the same fixed width as {wl.SMALL.name}, but with'
                ' a viewer alongside for showing content, on whichever side'
                ' the page asks for. A page with no viewer gets no pane:'
                ' its rows span the whole window instead.'
            )
        case _:
            assert_never(layout)


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

    # At viewer layouts, a turning powerup box in a pane on the side
    # asked for (or no viewer, the rows spanning the window).
    viewer: bdep.Depiction | None = None
    side = dui2.ViewerSide.LEFT
    if route.viewer_side is not None:
        from bauiv1 import _classicassets

        viewer = bdep.MeshViewerDepiction(
            entries=[
                bdep.MeshViewerEntry(
                    mesh=_classicassets.meshes.powerup,
                    texture=_classicassets.textures.powerup_punch,
                )
            ]
        )
        side = route.viewer_side

    return dui2.Response(
        page=dui2.Page(
            title=_lit('Window Layouts'),
            state=state.encode(),
            viewer=viewer,
            viewer_side=side,
            # Mostly the window showing through, a touch darkened (the
            # viewers page's 'Dark 25%').
            viewer_background_color=(0.0, 0.0, 0.0, 0.25),
            rows=[
                # Info about the layout: a row-less section with just a
                # subtitle, which joins the heading below it in latching
                # onto the first selectable row (no note: there's no
                # selectable row above for one to latch onto).
                *(
                    []
                    if route.layout is None
                    else [
                        dui2.Section(
                            subtitle=_lit(
                                route.layout.name.replace('_', ' ').title()
                                + ' - '
                                + _layout_description(route.layout)
                            ),
                            rows=[],
                        )
                    ]
                ),
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


def _wide_rows_height(layout: dui2.WindowLayout) -> tuple[float, str]:
    """Height a wide-family page has for its rows, and what it depends on.

    Wide and wider pages promise :data:`WIDE_PAGE_ROWS_HEIGHT`
    everywhere, so that's what we test against for them. Wide-tall and
    wide-taller ones get more at medium/large ui-scale (wide-taller's
    following the screen), so we take theirs from the window frame
    their windows are laid out with, less page prep's base buffers. At
    small ui-scale they are wide layouts, so they get wide's.
    (Called from a background thread; frames are a logic-thread job.)
    """
    import bauiv1 as bui
    from bauiv1lib.docui._frame import window_frames
    from bauiv1lib.docui._layout import (
        PAGE_BASE_BUFFER,
        WIDE_PAGE_ROWS_HEIGHT,
    )

    match layout:
        case dui2.WindowLayout.WIDE | dui2.WindowLayout.WIDER:
            return WIDE_PAGE_ROWS_HEIGHT, 'the same everywhere'
        case dui2.WindowLayout.WIDE_TALL | dui2.WindowLayout.WIDE_TALLER:
            pass
        case _:
            raise RuntimeError(f'Not a wide-family layout: {layout}.')

    def _measure() -> tuple[float, bui.UIScale]:
        uiscale = bui.app.ui_v1.uiscale
        frame = window_frames(
            layout, uiscale, dui2.ScrollEdgeStyle.FADE, close_style=False
        )[None]
        return frame.scroll_height - 2.0 * PAGE_BASE_BUFFER, uiscale

    height, uiscale = bui.logic_thread_submit(_measure).result(timeout=10.0)

    # At small ui-scale these are just wide layouts, so there's no
    # height of their own to check; test wide's promise instead (what
    # the wide page does).
    if uiscale is bui.UIScale.SMALL:
        return (
            WIDE_PAGE_ROWS_HEIGHT,
            'small ui-scale: the same as wide, so nothing new to check',
        )
    # (At medium/large the window is its layout's size, so this is
    # exactly what it gets.)
    depends = (
        'this ui-scale'
        if layout is dui2.WindowLayout.WIDE_TALL
        else 'this ui-scale and screen'
    )
    return height, f'{depends}: {uiscale.name.lower()}'


def test_page_wide_fit(
    route: bacommon.docui.routes.docuitest.WideFit,
) -> bacommon.docui.v2.Response:
    """A row exactly as big as wide pages get.

    :meta private:
    """
    from bauiv1lib.docui._layout import (
        BUTTON_ROW_EDGE_INSET,
        WIDE_PAGE_WIDTH,
    )

    import bauiv1 as bui

    layout = route.layout
    wider = layout is dui2.WindowLayout.WIDER
    rowsheight, height_note = _wide_rows_height(layout)

    # At small ui-scale, pages are at least wide's size but get more on
    # screens bigger than the smallest (the window fills the screen),
    # so going 1 over only scrolls on the smallest ones.
    small = (
        bui.logic_thread_submit(lambda: bui.app.ui_v1.uiscale).result(
            timeout=10.0
        )
        is bui.UIScale.SMALL
    )
    over_label = (
        '1 over\n(scrolls only on\nthe smallest screens\nat small ui-scale);'
        '\ntap to fit'
        if small
        else '1 over\n(should scroll);\ntap to fit'
    )

    # A hair under, so float rounding can't tip it into scrolling (or,
    # when testing the edge, a hair over).
    rowheight = rowsheight + (1.0 if route.over else -0.5)

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

    # (Wider's width follows the screen, so only the others can
    # overflow it.)
    width_buttons: list[bacommon.docui.v2.Button] = (
        []
        if wider
        else [
            dui2.Button(
                label=_lit(
                    f'Width {rowwidth:.1f}: '
                    + (
                        'fits;\ntap to go 1 over'
                        if not route.wide_over
                        else over_label
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
            title=_lit(layout.name.replace('_', ' ').title() + ' Fit'),
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
                                    else over_label
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
                                (
                                    f'Page height {rowsheight:.1f}'
                                    if wider
                                    else f'Page {WIDE_PAGE_WIDTH:.1f}'
                                    f' x {rowsheight:.1f}'
                                )
                                + f'\n({height_note})'
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
    from bauiv1 import _commonassets, _docuiv2testassets

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
                    texture=(_commonassets.textures.white if texture else None),
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
