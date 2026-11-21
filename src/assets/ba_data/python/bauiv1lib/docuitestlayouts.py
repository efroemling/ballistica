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
from typing import TYPE_CHECKING, NamedTuple, assert_never

from bacommon.langstr import LangStrSpecValue
import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bauiv1
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


def with_test_viewer(
    viewer_side: dui2.ViewerSide | None,
    theme: bacommon.docui.routes.docuitest.ThemeVariant,
    *,
    title: LangStrSpecValue,
    rows: list[dui2.Row],
    state: dict | None = None,
) -> dui2.Page:
    """A test page in ``theme``, with the test viewer on ``viewer_side``.

    The viewer is a turning punch powerup box over a slightly darkened
    background; at viewer layouts it sits on the given side, or with
    ``viewer_side`` None there's no viewer (the rows span the window).
    Shared by the pages the root's 'Layout Tests' row opens, so each
    looks the same at a picked side and theme. Other layouts ignore the
    viewer.

    :meta private:
    """
    from bauiv1lib.docuitestthemes import themed_page

    viewer: bdep.Depiction | None = None
    side = dui2.ViewerSide.LEFT
    if viewer_side is not None:
        from bauiv1 import _classicassets

        viewer = bdep.MeshViewerDepiction(
            entries=[
                bdep.MeshViewerEntry(
                    mesh=_classicassets.meshes.powerup,
                    texture=_classicassets.textures.powerup_punch,
                )
            ]
        )
        side = viewer_side

    return themed_page(
        dui2.Page(
            title=title,
            state=state,
            rows=rows,
            viewer=viewer,
            viewer_side=side,
            # Mostly the window showing through, a touch darkened (the
            # viewers page's 'Dark 25%').
            viewer_background_color=(0.0, 0.0, 0.0, 0.25),
        ),
        theme,
    )


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

    def _rows(
        title: str,
        count: int,
        align: dui2.HAlign,
        footnote: str | None = None,
    ) -> list[dui2.Row]:
        return [
            dui2.TitleRow(_lit(title)),
            dui2.ButtonRow(
                title_align=align,
                content_align=align,
                debug=debug,
                buttons=_buttons(count),
            ),
            *([] if footnote is None else [dui2.FootnoteRow(_lit(footnote))]),
        ]

    return dui2.Response(
        page=with_test_viewer(
            route.viewer_side,
            route.theme,
            title=_lit('Window Layouts'),
            state=state.encode(),
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
                        # A row title under a section heading: the
                        # heading is larger, so the two read as levels.
                        dui2.TitleRow(_lit('A row title')),
                        wstate.checkbox_row(
                            lambda s: s.plain,
                            label=_lit('A checkbox'),
                            debug=debug,
                        ),
                        wstate.choice_row(
                            lambda s: s.flavor,
                            choice_label=_flavor_label,
                            label=_lit('A choice'),
                            debug=debug,
                        ),
                        dui2.FootnoteRow(_lit('Footnote under a control row.')),
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
                        *_rows('Short row (left)', 3, left),
                        *_rows('Short row (center)', 3, center),
                        *_rows(
                            'Short row (right)',
                            3,
                            right,
                            footnote='Right-aligned footnote.',
                        ),
                        *_rows(
                            'Long row (left)',
                            16,
                            left,
                            footnote=(
                                'Starts at the left; scrolls within its'
                                ' area.'
                            ),
                        ),
                        *_rows('Long row (center)', 16, center),
                        *_rows(
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
                            action=replace(route, debug=not debug).replace(),
                        ),
                    ],
                ),
            ],
        )
    )


class _Promise(NamedTuple):
    """A content-rect size a layout promises, along one axis."""

    size: float
    #: Exactly this (1 over scrolls) rather than at least this.
    exact: bool


def _promised_width(layout: dui2.WindowLayout) -> _Promise | None:
    """The content-rect width a layout promises (at every ui-scale).

    Viewer layouts' are for a page beside its viewer pane. None for
    LARGE, which promises nothing: it gets most of the screen, whatever
    that turns out to be.
    """
    wl = dui2.WindowLayout
    match layout:
        case wl.SMALL | wl.SMALL_TALL | wl.SMALL_TALLER | wl.VIEWER:
            return _Promise(dui2.SMALL_CONTENT_WIDTH, True)
        case wl.VIEWER_NARROW:
            return _Promise(dui2.NARROW_CONTENT_WIDTH, True)
        case wl.WIDE | wl.WIDE_TALL | wl.WIDE_TALLER:
            return _Promise(dui2.WIDE_CONTENT_WIDTH, True)
        case wl.WIDER:
            # (Follows the screen.)
            return _Promise(dui2.WIDE_CONTENT_WIDTH, False)
        case wl.LARGE:
            return None
        case _:
            assert_never(layout)


def _promised_height(
    layout: dui2.WindowLayout, small_ui: bool
) -> _Promise | None:
    """The content-rect height a layout promises at a ui-scale.

    At small ui-scale windows fill the screen: wide and wider pages get
    exactly theirs on the shortest screens (more on taller ones), and
    the tall and taller layouts are just their base layouts. None for
    LARGE (see :func:`_promised_width`).
    """
    # pylint: disable=too-many-return-statements
    wl = dui2.WindowLayout
    if layout is wl.LARGE:
        return None
    if small_ui:
        match layout:
            case wl.WIDE | wl.WIDER:
                return _Promise(dui2.WIDE_CONTENT_HEIGHT, True)
            case wl.SMALL:
                return _Promise(dui2.SMALL_CONTENT_HEIGHT, False)
            case (
                wl.SMALL_TALL
                | wl.SMALL_TALLER
                | wl.WIDE_TALL
                | wl.WIDE_TALLER
                | wl.VIEWER
                | wl.VIEWER_NARROW
            ):
                return _Promise(dui2.WIDE_CONTENT_HEIGHT, False)
            case _:
                assert_never(layout)
    match layout:
        case wl.SMALL:
            return _Promise(dui2.SMALL_CONTENT_HEIGHT, True)
        case wl.SMALL_TALL | wl.WIDE_TALL:
            return _Promise(dui2.TALL_CONTENT_HEIGHT, True)
        case wl.SMALL_TALLER | wl.WIDE_TALLER:
            # (Follows the screen.)
            return _Promise(dui2.TALL_CONTENT_HEIGHT, False)
        case wl.WIDE | wl.WIDER:
            return _Promise(dui2.WIDE_CONTENT_HEIGHT, True)
        case wl.VIEWER | wl.VIEWER_NARROW:
            return _Promise(dui2.WIDE_CONTENT_HEIGHT, False)
        case _:
            assert_never(layout)


#: The fit test page's vertical inset (the default, spelled out: its
#: rows get the promised content height less twice this).
_FIT_V_INSET = dui2.DEFAULT_V_INSET


def _fit_themed(
    page: bacommon.docui.v2.Page,
    theme: bacommon.docui.routes.docuitest.ThemeVariant,
) -> bacommon.docui.v2.Page:
    """A fit page in a theme, keeping the vertical inset it's sized by."""
    from bauiv1lib.docuitestthemes import themed_page

    return replace(themed_page(page, theme), v_inset=page.v_inset)


def _no_promise_page(
    layout: dui2.WindowLayout,
    uiscale: bauiv1.UIScale,
    actual: tuple[float, float],
    theme: bacommon.docui.routes.docuitest.ThemeVariant,
) -> bacommon.docui.v2.Response:
    """The fit page for a layout promising no size (LARGE).

    Nothing to test: just what it says it is and what it got.
    """
    return dui2.Response(
        page=_fit_themed(
            dui2.Page(
                title=_lit(_layout_title(layout) + ' Fit'),
                v_inset=_FIT_V_INSET,
                rows=[
                    dui2.TitleRow(_lit('No promised size'), attach=False),
                    dui2.SubtitleRow(
                        _lit(
                            'Large makes no guarantees about space: it just'
                            ' gets most of the screen, whatever that turns'
                            ' out to be. Pages wanting a known size should'
                            ' pick another layout.'
                        ),
                        attach=False,
                    ),
                    dui2.ButtonRow(
                        layout=dui2.ButtonRowLayout.FILL,
                        debug=True,
                        buttons=[
                            dui2.Button(
                                label=_lit(
                                    f'This window gets {actual[0]:.1f}'
                                    f' x {actual[1]:.1f}'
                                    f' ({uiscale.name.lower()} ui-scale)'
                                ),
                                label_scale=0.7,
                                size=(300.0, 80.0),
                                # (Wide art; it spans the row.)
                                style=dui2.ButtonStyle.LARGE,
                                action=dui2.Local(),
                            )
                        ],
                    ),
                ],
            ),
            theme,
        )
    )


def test_page_layout_fit(
    route: bacommon.docui.routes.docuitest.LayoutFit,
) -> bacommon.docui.v2.Response:
    """A row exactly as big as a layout promises its pages.

    :meta private:
    """
    from bauiv1lib.docui._frame import window_frames
    from bauiv1lib.docui._layout import BUTTON_ROW_EDGE_INSET
    from bauiv1lib.docui._panes import layout_has_viewer_pane

    import bauiv1 as bui

    layout = route.layout
    viewer = layout_has_viewer_pane(layout)
    side = dui2.ViewerSide.LEFT if viewer else None

    def _measure() -> tuple[bui.UIScale, tuple[float, float]]:
        # The content rect this window actually gets (to show beside
        # the promise; frames are a logic-thread job).
        uiscale = bui.app.ui_v1.uiscale
        frame = window_frames(
            layout, uiscale, dui2.ScrollEdgeStyle.FADE, close_style=False
        )[side]
        return uiscale, (frame.content_width, frame.content_height)

    uiscale, actual = bui.logic_thread_submit(_measure).result(timeout=10.0)
    small_ui = uiscale is bui.UIScale.SMALL
    pwidth = _promised_width(layout)
    pheight = _promised_height(layout, small_ui)
    if pwidth is None or pheight is None:
        return _no_promise_page(layout, uiscale, actual, route.theme)

    def _over_label(promise: _Promise, vertical: bool) -> str:
        if not promise.exact:
            return '1 over\n(a minimum: may not\nscroll here);\ntap to fit'
        if small_ui and vertical:
            return (
                '1 over\n(scrolls only on\nthe shortest screens\nat small'
                ' ui-scale);\ntap to fit'
            )
        return '1 over\n(should scroll);\ntap to fit'

    # A hair under, so float rounding can't tip it into scrolling (or,
    # when testing the edge, a hair over). The row's height is the
    # promised content height less our vertical insets.
    rowheight = (
        pheight.size - 2.0 * _FIT_V_INSET + (1.0 if route.over else -0.5)
    )

    # A button row's h-scroll content is its buttons, spacing and
    # padding plus the room its padding starts in from the content
    # rect's edges; it fits when all that is no wider than the content
    # rect (the page's horizontal inset doesn't come into it).
    spacing = 15.0
    rowwidth = pwidth.size + (1.0 if route.wide_over else -0.5)

    # Square-button art draws a bit past its bounds; padding gives it
    # room inside the row so the page edges don't clip it.
    pad = 15.0
    bheight = rowheight - 2.0 * pad
    bwidth = (
        rowwidth - 2.0 * BUTTON_ROW_EDGE_INSET - 2.0 * pad - 2.0 * spacing
    ) / 3

    def _promise_text(promise: _Promise) -> str:
        return ('' if promise.exact else '>= ') + f'{promise.size:.1f}'

    return dui2.Response(
        page=_fit_themed(
            dui2.Page(
                title=_lit(_layout_title(layout) + ' Fit'),
                v_inset=_FIT_V_INSET,
                viewer=bdep.BlankDepiction() if viewer else None,
                viewer_side=dui2.ViewerSide.LEFT,
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
                            dui2.Button(
                                label=_lit(
                                    f'Width {rowwidth:.1f}: '
                                    + (
                                        _over_label(pwidth, vertical=False)
                                        if route.wide_over
                                        else 'fits;\ntap to go 1 over'
                                    )
                                ),
                                label_scale=0.7,
                                size=(bwidth, bheight),
                                action=replace(
                                    route, wide_over=not route.wide_over
                                ).replace(),
                            ),
                            dui2.Button(
                                label=_lit(
                                    f'Height {rowheight:.1f}: '
                                    + (
                                        _over_label(pheight, vertical=True)
                                        if route.over
                                        else 'fits;\ntap to go 1 over'
                                    )
                                ),
                                label_scale=0.7,
                                size=(bwidth, bheight),
                                action=replace(
                                    route, over=not route.over
                                ).replace(),
                            ),
                            dui2.Button(
                                label=_lit(
                                    f'Content promised\n{_promise_text(pwidth)}'
                                    f' x {_promise_text(pheight)}'
                                    f'\nthis window gets\n{actual[0]:.1f}'
                                    f' x {actual[1]:.1f}'
                                    f'\n(v_inset {_FIT_V_INSET:g};'
                                    f' {uiscale.name.lower()} ui-scale)'
                                ),
                                label_scale=0.6,
                                size=(bwidth, bheight),
                            ),
                        ],
                    )
                ],
            ),
            route.theme,
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

    def _hello_rows(
        title: LangStrSpec,
        sizes: list[tuple[float, float]],
        style: bacommon.docui.v2.ButtonStyle,
        texture: bool = False,
    ) -> list[bacommon.docui.v2.Row]:
        return [
            dui2.TitleRow(title),
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        label=strs.layout.hello.spec,
                        size=size,
                        style=style,
                        texture=(
                            _commonassets.textures.white if texture else None
                        ),
                        color=(1, 0, 0, 0.3) if texture else None,
                        debug=True,
                    )
                    for size in sizes
                ],
            ),
        ]

    styles = dui2.ButtonStyle

    return dui2.Response(
        page=dui2.Page(
            title=strs.layout.bounds_tests_title.spec,
            rows=[
                *_hello_rows(
                    _nm(styles.SQUARE),
                    [(300, 300), (200, 200), (100, 100)],
                    styles.SQUARE,
                ),
                *_hello_rows(
                    _nm(styles.SQUARE_WIDE),
                    [(400, 200), (200, 250), (60, 100)],
                    styles.SQUARE_WIDE,
                ),
                *_hello_rows(
                    strs.layout.background_texture.spec,
                    [(300, 300), (200, 200), (100, 100)],
                    styles.SQUARE,
                    texture=True,
                ),
                *_hello_rows(
                    _nm(styles.TAB),
                    [(400, 100), (200, 50), (100, 60)],
                    styles.TAB,
                ),
                *_hello_rows(
                    _nm(styles.LARGER),
                    [(500, 100), (200, 50), (100, 60)],
                    styles.LARGER,
                ),
                *_hello_rows(
                    _nm(styles.LARGE),
                    [(400, 100), (200, 50), (100, 60)],
                    styles.LARGE,
                ),
                *_hello_rows(
                    _nm(styles.MEDIUM),
                    [(300, 100), (200, 50), (100, 60)],
                    styles.MEDIUM,
                ),
                *_hello_rows(
                    _nm(styles.SMALL),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.SMALL,
                ),
                *_hello_rows(
                    _nm(styles.BACK),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.BACK,
                ),
                *_hello_rows(
                    _nm(styles.BACK_SMALL),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.BACK_SMALL,
                ),
            ],
        )
    )


def _layout_title(layout: dui2.WindowLayout) -> str:
    """A window layout's name, title-cased (``WIDE_TALL`` -> ``Wide Tall``)."""
    return layout.name.replace('_', ' ').title()


def _side_name(side: dui2.ViewerSide | None) -> str:
    """A viewer pane placement's name (None for no pane)."""
    return 'None' if side is None else side.name.title()


def layout_tests_rows(
    state: bacommon.docui.routes.docuitest.RootState,
) -> list[dui2.Row]:
    """The root page's 'Layout Tests' row, at the picked layout.

    Each button opens a test page at the layout picked in
    :func:`layout_picker_rows`:

    - Fade Scroll / Outline Scroll: the window layouts page (at the
      picked viewer side too) in each scroll edge style; content
      should sit in exactly the same place in both.
    - Fit: the layout's promised content-rect size check (or a note
      that it promises none).
    - Widgets, Sections, Grids: those test pages, to see how they
      behave at the layout's width (grids reflow to it).

    All but Fit show the standard test viewer (see
    :func:`with_test_viewer`) on the picked side, and all show their
    pages in the theme picked in :func:`layout_theme_rows`.

    :meta private:
    """
    import bacommon.docui.routes.docuitest as rt
    from bauiv1lib.docuitestthemes import theme_frame

    layout = state.layout
    side = state.viewer_side
    theme = state.theme
    background_color, cancel_button_color = theme_frame(theme)

    def _button(
        label: str,
        route: bacommon.docui.routes.DocUIRoute,
        scroll_edge_style: dui2.ScrollEdgeStyle | None = None,
    ) -> dui2.Button:
        return dui2.Button(
            label=LangStrSpecValue.literal(label),
            size=(160, 80),
            action=route.browse(
                layout=layout,
                scroll_edge_style=scroll_edge_style,
                # (The theme's frame colors come with the link.)
                background_color=background_color,
                cancel_button_color=cancel_button_color,
            ),
        )

    return [
        # Dev-only, so baked literals.
        dui2.TitleRow(LangStrSpecValue.literal('Layout Tests')),
        dui2.ButtonRow(
            buttons=[
                *(
                    _button(
                        label,
                        rt.WindowLayouts(
                            layout=layout, viewer_side=side, theme=theme
                        ),
                        style,
                    )
                    for label, style in (
                        ('Fade Scroll', dui2.ScrollEdgeStyle.FADE),
                        ('Outline Scroll', dui2.ScrollEdgeStyle.OUTLINE),
                    )
                ),
                _button('Fit', rt.LayoutFit(layout=layout, theme=theme)),
                _button('Widgets', rt.Widgets(viewer_side=side, theme=theme)),
                _button('Sections', rt.Sections(viewer_side=side, theme=theme)),
                _button('Grids', rt.ButtonGrids(viewer_side=side, theme=theme)),
            ],
        ),
    ]


class _LayoutOption(NamedTuple):
    """One way to open a window: a layout and (at viewer layouts) a side."""

    layout: dui2.WindowLayout
    side: dui2.ViewerSide | None
    label: str
    size: tuple[float, float]


def _layout_options() -> list[_LayoutOption]:
    """Every layout, with a left/none/right option for viewer layouts.

    Built from :class:`~bacommon.docui.v2.WindowLayout`, so a layout
    added later shows up everywhere these are offered.
    """
    from bauiv1lib.docui._panes import layout_has_viewer_pane

    out: list[_LayoutOption] = []
    for layout in dui2.WindowLayout:
        name = _layout_title(layout)
        if not layout_has_viewer_pane(layout):
            out.append(_LayoutOption(layout, None, name, (120.0, 80.0)))
            continue
        for side in (dui2.ViewerSide.LEFT, None, dui2.ViewerSide.RIGHT):
            out.append(
                _LayoutOption(
                    layout, side, f'{name} ({_side_name(side)})', (200.0, 80.0)
                )
            )
    return out


#: The picked button in the root page's 'Layout Test Options' rows.
_PICKED_COLOR = (0.35, 0.8, 1.0, 1.0)

#: :attr:`~bacommon.docui.v2.ButtonRow.button_spacing`'s default.
_DEFAULT_BUTTON_SPACING = dui2.ButtonRow(buttons=[]).button_spacing


def layout_picker_rows(
    route: bacommon.docui.routes.docuitest.Root,
    state: bacommon.docui.routes.docuitest.RootState,
) -> list[dui2.Row]:
    """The root page's 'Layout Test Options' layout row: pick a layout.

    A button per layout option (see ``_layout_options()``), at 0.6
    scale. Pressing one just stores it in the page's state (rows below
    can open their pages at it); the picked one shows brightly.

    :meta private:
    """
    import bacommon.docui.routes.docuitest as rt

    def _picked(option: _LayoutOption) -> bool:
        # (A pick sets both, so they match together.)
        return (
            option.layout is state.layout and option.side is state.viewer_side
        )

    return [
        # (Titles both this row and the themes row below it.)
        dui2.TitleRow(LangStrSpecValue.literal('Layout Test Options')),
        dui2.SubtitleRow(LangStrSpecValue.literal('Layout')),
        dui2.ButtonRow(
            buttons=[
                dui2.Button(
                    label=LangStrSpecValue.literal(option.label),
                    size=option.size,
                    scale=0.6,
                    color=_PICKED_COLOR if _picked(option) else None,
                    # (Just updates our state; the page comes back with
                    # the new pick showing.)
                    action=rt.Root(debug=route.debug).replace(
                        sets=[
                            rt.RootState.assign(
                                lambda s: s.layout, option.layout
                            ),
                            rt.RootState.assign(
                                lambda s: s.viewer_side, option.side
                            ),
                        ]
                    ),
                )
                for option in _layout_options()
            ],
            # (Tighter, to go with the smaller buttons.)
            button_spacing=_DEFAULT_BUTTON_SPACING * 0.6,
        ),
    ]


def layout_theme_rows(
    route: bacommon.docui.routes.docuitest.Root,
    state: bacommon.docui.routes.docuitest.RootState,
) -> list[dui2.Row]:
    """The root page's 'Layout Test Options' themes row: pick a theme.

    A button per :class:`~bacommon.docui.routes.docuitest.ThemeVariant`
    (the page-themes test page's set), small and picked the same way as
    in :func:`layout_picker_rows`; the 'Layout Tests' pages show in the
    picked one.

    :meta private:
    """
    import bacommon.docui.routes.docuitest as rt
    from bauiv1lib.docuitestthemes import theme_label
    from bauiv1lib.docuitestwidgets import style_for_size

    size = (150.0, 60.0)
    return [
        # (No title: the layout row's 'Layout Test Options' covers both.)
        dui2.SubtitleRow(LangStrSpecValue.literal('Themes')),
        dui2.ButtonRow(
            buttons=[
                dui2.Button(
                    label=LangStrSpecValue.literal(theme_label(theme)),
                    size=size,
                    style=style_for_size(size),
                    scale=0.6,
                    color=_PICKED_COLOR if theme is state.theme else None,
                    action=rt.Root(debug=route.debug).replace(
                        sets=[rt.RootState.assign(lambda s: s.theme, theme)]
                    ),
                )
                for theme in rt.ThemeVariant
            ],
            button_spacing=_DEFAULT_BUTTON_SPACING * 0.6,
        ),
    ]
