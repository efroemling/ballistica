# Released under the MIT License. See LICENSE for details.
#
"""Prep functionality for our UI.

We do all layout math and bake out partial ui calls in a background
thread so there's as little work to do in the ui thread as possible.
"""

from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING

from efro.dataclassio import dataclass_to_json
import bacommon.docui.v2 as dui2
import bauiv1 as bui

from bauiv1lib.docui._layout import BUTTON_ROW_EDGE_INSET
from bauiv1lib.docui._debugdraw import (
    DebugDrawKind,
    selection_centering_disabled,
    wants_debug_draw,
)
from bauiv1lib.docui.prep._types import PagePrep, RowPrep
from bauiv1lib.docui.prep._staticbuttonrow import column_row_edges
from bauiv1lib.docui.prep._button import (
    button_size,
    button_padded_size,
    row_entry_index,
    prep_button,
)
from bauiv1lib.docui.prep._rowtext import (
    row_titles_height,
    prep_row_titles,
    row_footnote_height,
    prep_row_footnote,
    wrap_row_texts,
)
from bauiv1lib.docui.prep._rowbands import (
    row_header_height,
    row_footer_height,
    prep_row_header,
    prep_row_footer,
)
from bauiv1lib.docui.prep._staticbuttonrow import row_content_align
from bauiv1lib.docui.prep._rowdebug import prep_row_part_debug
from bauiv1lib.docui.prep._textstyles import styled_row
from bauiv1lib.docui.prep._headings import (
    HEADING_TITLE_SCALE,
    heading_entry_height,
    prep_heading_entry,
)
from bauiv1lib.docui.prep._textrows import (
    TextEntry,
    prep_text_entry,
    text_entry_height,
)
from bauiv1lib.docui.prep._showareas import (
    control_spans,
    finalize_show_buffers,
)
from bauiv1lib.docui.prep._styling import styled_page
from bauiv1lib.docui._pagelook import PageLook

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    from typing import Callable

    from bauiv1lib.docui.prep._types import DecorationPrep, WrapOverride
    from bacommon.langstr import LangStrSpec
    from bacommon.assetspec import TextureSpec, MeshSpec
    from bauiv1lib.docui._host import DocUIPageHost
    from bauiv1lib.docui._panes import ScrollGeometry


# A scrolling button row's h-scroll reaches this far below the row's
# laid-out bottom: the strip its scroll bar fades in over (the bar
# draws 5-13 up from the h-scroll's bottom). The row doesn't count it,
# so it lands in the row spacing below (or over a footnote, which the
# bar then overlaps while it shows; accepted). At the default button
# row spacing (10) it ends exactly where the next row begins.
_SCROLLBAR_STRIP = 10.0


def refstr(ref: 'TextureSpec | MeshSpec | int') -> str:
    """Qualified engine name for a typed asset ref.

    Accepts the flat-index form only to reject it: indices are replaced
    with specs during resolve (``_resolve.deindex_assets``), so one
    reaching render means that step was skipped or failed. Raising here
    states the assumption once, rather than leaving eleven call sites
    each assuming it silently.
    """
    if isinstance(ref, int):
        raise RuntimeError(
            f'Un-de-indexed asset ref {ref} reached render; the page was'
            f' not resolved, or de-indexing failed.'
        )
    # This is the render boundary; the spec's parts are private
    # precisely so the conversion happens here and not ad hoc.
    # pylint: disable-next=protected-access
    return f'{ref._apvernum}:{ref._name}'


def prep_page(
    page: dui2.Page,
    *,
    packages: list[ApverNum],
    geometry: ScrollGeometry,
    idprefix: str,
    immediate: bool = False,
    transition_scale: float = 1.0,
    description: str = '(unnamed)',
) -> PagePrep:
    # pylint: disable=too-many-statements
    """Prep a page.

    ``geometry`` is what it lays out against: its content rect's size,
    and how far its scroll area extends out past that (see
    :class:`~bauiv1lib.docui._frame.WindowFrame`).

    ``transition_scale`` multiplies every scale-in delay (0 pops the
    page in instantly, like ``immediate``; 1 is full speed).

    ``description`` names the page (its controller and path) in
    anything logged about it.
    """
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=cyclic-import

    import bauiv1lib.docui.prep._calls2 as prepcalls2
    from bauiv1lib.docui.prep import _controlrows, _sections

    if transition_scale <= 0.0:
        immediate = True
    tscale = max(0.0, min(1.0, transition_scale))

    def _n(
        lstr: 'LangStrSpec | int', *, wrap: 'WrapOverride | None' = None
    ) -> bui.LangStr:
        """Native handle bound against this payload's package list.

        Accepts a folded index only to reject it: indices are unfolded
        during resolve, so one arriving here means that step was
        skipped or failed. (See :class:`NativeLangStrFn` for ``wrap``.)
        """
        if isinstance(lstr, int):
            raise RuntimeError(
                f'Unfolded language-string index {lstr} reached render;'
                f' the page was not resolved, or unfolding failed.'
            )
        return bui.LangStr(
            dataclass_to_json(lstr), packages=packages, wrap=wrap
        )

    # The look we lay out in (our values, defaults applied). What it
    # says about rows is baked into (copies of) them (see
    # styled_page()).
    look = PageLook.of(page)
    spacing = look.spacing
    page = styled_page(page, look)

    # The flat list of what we lay out: the rows we know how to display,
    # with each section expanded in place into its heading, its rows and
    # its note (sections remember which entries are their rows, for
    # their backings).
    page_rows_filtered, section_spans = _sections.layout_entries(
        page, description
    )

    # Ok; we've got some buttons. Build our full UI.

    # How far our host scroll widget extends out past our content rect
    # (under the title band or toolbars, into screen margins, across a
    # narrow column's sides). Our overall size grows to cover these and
    # h-scroll rows run through them, but content itself stays laid out
    # within the content rect: button rows' content starts and
    # (scrolled to its end) stops at its edges.
    ext_left, ext_right, ext_bottom, ext_top = geometry.extends
    cmargin_left = ext_left
    cmargin_right = ext_right
    cmargins = geometry.extends

    # Buffers for *everything*: the page's vertical inset above and
    # below, clear of the extends; out to the inset rect, then. Rows'
    # show-buffers include these, so selecting a row brings what it
    # must show to the inset rect at least (where no fade reaches).
    top_buffer = look.v_inset + ext_top
    bot_buffer = look.v_inset + ext_bottom

    # Where text (titles, labels, footnotes) sits in from the content
    # rect's edges; the same both sides (our horizontal inset).
    header_inset_left = look.h_inset
    header_inset_right = look.h_inset

    rootcall: Callable[..., bui.Widget] | None = None
    rows: list[RowPrep] = []
    # (Our scroll widget lays out cleanly, so we span exactly its width.)
    width: float = geometry.content_width + ext_left + ext_right
    # (And its height, which is what selection scrolls within.)
    scroll_height = geometry.content_height + ext_bottom + ext_top
    # Where sideways-scrolling rows' page arrows sit in from its sides,
    # and the width between (what's on screen).
    arrow_left, arrow_right = geometry.page_arrow_insets
    visible_width = width - arrow_left - arrow_right
    # The space above each entry (see _sections.entry_gaps()).
    gaps = _sections.entry_gaps(page_rows_filtered, spacing)
    height: float = top_buffer + bot_buffer + sum(gaps)
    simple_culling_v: float = page.simple_culling_v
    center_vertically: bool = page.center_vertically
    show_scrollbar: bool = page.show_scrollbar
    title: bui.LangStr = _n(page.title)

    # Called with root container after construction completes. First,
    # the color our default button (if any) takes from the root (a
    # window's root outlives its pages, so this is set every time).
    root_post_calls: list[Callable[[bui.Widget], None]] = [
        partial(prepcalls2.set_start_button_color, look.default_button_color)
    ]

    nextbuttonid = 0

    have_start_button = False
    selected_widget_id: str | None = None

    def _button_widget_id(button: dui2.Button) -> str:
        """The widget id for a button: its own, or the next in line."""
        nonlocal nextbuttonid
        if button.widget_id is not None:
            return f'{idprefix}|{button.widget_id}'
        nextbuttonid += 1
        return f'{idprefix}|button{nextbuttonid - 1}'

    def _note_button_flags(button: dui2.Button, widgetid: str) -> None:
        """Act on a button's default/selected flags."""
        nonlocal have_start_button, selected_widget_id
        if button.default:
            if have_start_button:
                bui.uilog.warning(
                    'Multiple buttons flagged as default.'
                    ' There can be only one per page.'
                )
            else:
                have_start_button = True
                root_post_calls.append(
                    partial(prepcalls2.set_start_button, widgetid)
                )
        if button.selected:
            if selected_widget_id is not None:
                bui.uilog.warning(
                    'Multiple buttons flagged as selected.'
                    ' There can be only one per page.'
                )
            else:
                selected_widget_id = widgetid
                root_post_calls.append(
                    partial(prepcalls2.set_selected_button, widgetid)
                )

    # How far each control row's control and footnote pull together (see
    # control_row_tucks()); measured once, used by both passes below.
    control_tucks: dict[int, tuple[float, float]] = {}

    # The column (cards center in it), and each layout entry's
    # horizontal geometry: the column's, or a card's own, plus where a
    # button row clips (see _sections.entry_geometry()). Both passes
    # bind these names from it per entry.
    column = (cmargin_left, width - cmargin_right)
    geoms = _sections.entry_geometry(
        page_rows_filtered,
        section_spans,
        base=_sections.column_geometry(
            column[0],
            column[1],
            width=width,
            clip=None,
            inset=look.h_inset,
        ),
        width=width,
        column=column,
    )

    # Word-wrap every row's title/subtitle/footnote to the width its
    # text widget gets, swapping in copies (the page itself may be
    # cached and shared). Everything below then just sees text with more
    # lines: strip heights grow to fit. (Sections' starts and ends hold
    # no text.)
    for i, entry in enumerate(page_rows_filtered):
        geom = geoms[i]
        text_margins = (
            geom.cmargin_left,
            geom.cmargin_right,
            ext_bottom,
            ext_top,
        )
        if isinstance(entry, _sections.SectionHead | _sections.SectionFoot):
            continue
        if isinstance(entry, TextEntry):
            wrapped = wrap_row_texts(
                styled_row(entry.row, page.text),
                width=width,
                margins=text_margins,
                header_insets=(header_inset_left, header_inset_right),
                center=geom.center,
                native=_n,
                where=f'Text row (layout entry {i})',
                title_scale=HEADING_TITLE_SCALE if entry.heading else None,
            )
            assert isinstance(wrapped, dui2.ButtonRow)
            page_rows_filtered[i] = replace(entry, row=wrapped)
        else:
            # (With the page's text looks filled in, too.)
            page_rows_filtered[i] = wrap_row_texts(
                styled_row(entry, page.text),
                width=width,
                margins=text_margins,
                header_insets=(header_inset_left, header_inset_right),
                center=geom.center,
                native=_n,
                where=f'{type(entry).__name__} (layout entry {i})',
            )

    # Precalc basic info like dimensions for all rows.
    for i, row in enumerate(page_rows_filtered):
        cmargin_left, cmargin_right = (
            geoms[i].cmargin_left,
            geoms[i].cmargin_right,
        )
        control_left, control_right = (
            geoms[i].control_left,
            geoms[i].control_right,
        )
        if isinstance(row, _sections.MARKER_ENTRY_TYPES):
            # Text and bands only; its whole height sits outside any
            # scrollable part, so the prep's own is zero.
            rows.append(
                RowPrep(
                    width=0.0,
                    height=0.0,
                    titlecalls=[],
                    hscrollcall=None,
                    hscrolleditcall=None,
                    hsubcall=None,
                    buttons=[],
                    simple_culling_h=0.0,
                    decorations=[],
                    is_section=True,
                )
            )
            if isinstance(row, TextEntry):
                height += (
                    heading_entry_height(row, _n)
                    if row.heading
                    else text_entry_height(row, _n)
                )
            elif isinstance(row, _sections.SectionHead):
                height += _sections.section_head_height(row, first=i == 0)
            else:
                height += _sections.section_foot_height(row)
            continue
        if _controlrows.is_column_row(row):
            titles_tuck, footnote_tuck = control_tucks[id(row)] = (
                _controlrows.control_row_tucks(
                    row, left=control_left, right=control_right, native=_n
                )
            )
            row_left, row_right = column_row_edges(
                row,
                control=(control_left, control_right),
                column=(
                    cmargin_left,
                    width - cmargin_right,
                ),
            )
            cbheight = (
                _controlrows.control_row_height(
                    row, left=row_left, right=row_right
                )
                + row_footnote_height(row, _n)
                - footnote_tuck
            )
            rows.append(
                RowPrep(
                    width=0.0,
                    height=cbheight,
                    titlecalls=[],
                    hscrollcall=None,
                    hscrolleditcall=None,
                    hsubcall=None,
                    buttons=[],
                    simple_culling_h=0.0,
                    decorations=[],
                )
            )
            height += cbheight + row_titles_height(row, _n) - titles_tuck
            height += row_header_height(row) + row_footer_height(row)
            height += row.spacing_top + row.spacing_bottom
            continue

        # Anything else is a (scrolling) row of buttons.
        assert isinstance(row, dui2.ButtonRow)
        padleft, padright, padtop, padbottom = row.get_padding()
        this_row_width = (
            cmargin_left
            + cmargin_right
            + 2.0 * BUTTON_ROW_EDGE_INSET
            + padleft
            + padright
            + row.button_spacing * (len(row.buttons) - 1)
        )
        button_row_height = 30.0
        for button in row.buttons:
            # Include button padding when calcing full needed size.
            bwidthpadded, bheightpadded = button_padded_size(button)
            button_row_height = max(button_row_height, bheightpadded)
            this_row_width += bwidthpadded
        # Clipped narrower than the page (in a section), the h-scroll
        # loses that much from each end of its content too, so what's in
        # it stays exactly where it would be on the page.
        if (clip := geoms[i].clip) is not None:
            this_row_width -= clip[0] + (width - clip[1])
        # Note: this includes everything in the *scrollable* part of
        # the row.
        this_row_height = padtop + padbottom + button_row_height
        rows.append(
            RowPrep(
                width=this_row_width,
                height=this_row_height,
                titlecalls=[],
                hscrollcall=None,
                hscrolleditcall=None,
                hsubcall=None,
                buttons=[],
                simple_culling_h=row.simple_culling_h,
                decorations=[],
            )
        )
        assert this_row_height > 0.0
        assert this_row_width > 0.0

        # Add height that is *not* part of the h-scrollable area.
        height += row_header_height(row) + row_footer_height(row)
        height += row_titles_height(row, _n)
        height += row_footnote_height(row, _n)
        height += this_row_height
        height += row.spacing_top + row.spacing_bottom

    # Ok; we've got all row dimensions. Now prep calls to make the
    # subcontainers to fit everything and fill out all rows.
    rootcall = partial(
        bui.containerwidget,
        size=(width, height),
        claims_left_right=True,
        background=False,
    )
    y = height - top_buffer

    # Section markers attach to a neighboring selectable row for
    # navigation: a heading's height (plus the row spacing between)
    # joins the *next* selectable row's top show-buffer, a note's the
    # *previous* one's bottom show-buffer, so selecting that row keeps
    # the marker in view. Base buffers are gathered on each RowPrep
    # here and finalized after the loop, once every attachment is
    # known.
    pending_top_attach: float | None = None
    last_selectable: RowPrep | None = None

    for i, (row, rowprep) in enumerate(
        zip(page_rows_filtered, rows, strict=True)
    ):
        tdelaybase = (0.15 + 0.06 * i) * tscale
        geom = geoms[i]
        cmargin_left, cmargin_right = geom.cmargin_left, geom.cmargin_right
        cmargins = (cmargin_left, cmargin_right, ext_bottom, ext_top)
        control_left, control_right = geom.control_left, geom.control_right
        band_anchors_x = geom.band_anchors_x

        if isinstance(row, TextEntry):
            # Standalone text or bands keep the next selectable row's
            # view (a footnote or footer, the previous one's), like a
            # section's heading (note). (Those count the row spacing
            # above them; for others it belongs to what came before.)
            ytop = y
            y -= gaps[i]
            if not row.upward:
                ytop = y
            y = (prep_heading_entry if row.heading else prep_text_entry)(
                row,
                rowprep,
                y=y,
                width=width,
                margins=cmargins,
                header_insets=(header_inset_left, header_inset_right),
                center=geom.center,
                anchors_x=band_anchors_x,
                tdelaybase=None if immediate else tdelaybase,
                tscale=tscale,
                native=_n,
                packages=packages,
            )
            if not row.upward:
                pending_top_attach = (pending_top_attach or 0.0) + (ytop - y)
            elif last_selectable is not None:
                last_selectable.show_buffer_bottom += ytop - y
            if wants_debug_draw(row.row.debug, DebugDrawKind.ROWS):
                prepcalls2.prep_row_debug(
                    (
                        width - cmargin_left - cmargin_right,
                        rowprep.bounds_top - rowprep.bounds_bottom,
                    ),
                    (cmargin_left, rowprep.bounds_bottom),
                    None,
                    rowprep.decorations,
                )
            continue

        if isinstance(row, _sections.SectionHead | _sections.SectionFoot):
            ytop = y
            y -= gaps[i]
            if isinstance(row, _sections.SectionHead):
                # (The spacing above a section's start belongs to
                # whatever came before.)
                ytop = y
                y = _sections.prep_section_head(row, rowprep, y=y, first=i == 0)
                # Everything from our top down to the next row's top
                # (its spacing included, added when we get there).
                pending_top_attach = (pending_top_attach or 0.0) + (ytop - y)
            else:
                y = _sections.prep_section_foot(row, rowprep, y=y)
                # (A card's bottom padding stays in view with its last
                # row.)
                if last_selectable is not None:
                    last_selectable.show_buffer_bottom += ytop - y
            continue

        # A selectable row: whatever headings gathered above it are
        # its to keep in view, the row spacing between included.
        if pending_top_attach is not None:
            rowprep.show_buffer_top += pending_top_attach + gaps[i]
            pending_top_attach = None
        last_selectable = rowprep

        if _controlrows.is_column_row(row):
            y -= row.spacing_top
            y -= gaps[i]
            # Debug bounds cover the whole row: header band to footer
            # band (not the spacing outside them).
            ydebugtop = y
            y = prep_row_header(
                row,
                rowprep,
                y=y,
                anchors_x=band_anchors_x,
                tdelay=None if immediate else (tdelaybase + 0.05 * tscale),
                packages=packages,
            )
            y = prep_row_titles(
                row,
                rowprep,
                y=y,
                width=width,
                margins=cmargins,
                header_insets=(header_inset_left, header_inset_right),
                center=geom.center,
                tdelaybase=None if immediate else tdelaybase,
                tscale=tscale,
                native=_n,
            )
            # Label and its surrounding text sit closer than their
            # strips alone would put them (see control_row_tucks()).
            titles_tuck, footnote_tuck = control_tucks[id(row)]
            y += titles_tuck
            y -= rowprep.height
            footnote_height = row_footnote_height(row, _n)
            prep_row_footnote(
                row,
                rowprep,
                y=y,
                width=width,
                margins=cmargins,
                header_insets=(header_inset_left, header_inset_right),
                center=geom.center,
                tdelaybase=None if immediate else tdelaybase,
                tscale=tscale,
                native=_n,
            )
            # A row whose control is a button (or whose contents are
            # buttons) ids and flags them as a row of buttons would.
            rowbuttons: list[dui2.Button] = (
                [row.button]
                if isinstance(row, dui2.ButtonControlRow)
                else row.buttons if isinstance(row, dui2.ButtonRow) else []
            )
            buttonids: list[str] | None = None
            if isinstance(row, dui2.ButtonRow):
                rowprep.entry_index = row_entry_index(row.buttons)
            if rowbuttons:
                buttonids = []
                for rowbutton in rowbuttons:
                    rowbuttonid = _button_widget_id(rowbutton)
                    _note_button_flags(rowbutton, rowbuttonid)
                    buttonids.append(rowbuttonid)
            # (The same edges its height was figured from, above.)
            row_left, row_right = column_row_edges(
                row,
                control=(control_left, control_right),
                column=(
                    cmargin_left,
                    width - cmargin_right,
                ),
            )
            control_bottom = y + footnote_height - footnote_tuck
            # (Our height includes the footnote tucked under the
            # control.)
            rowprep.show_part = (
                control_bottom,
                y + rowprep.height,
            )
            rowprep.show_x = (
                cmargin_left,
                width - cmargin_right,
            )
            _controlrows.prep_control_row(
                row,
                rowprep,
                left=row_left,
                right=row_right,
                bottom=control_bottom,
                center_x=geom.center[0],
                idprefix=idprefix,
                # Same timing as a button row's first button.
                tdelay=None if immediate else tdelaybase,
                native=_n,
                packages=packages,
                buttonids=buttonids,
            )
            rowprep.control_spans = control_spans(rowprep)
            # Selecting the control should bring the whole row -- its
            # header and titles above and footnote and footer below --
            # into view, plus the page's own buffers so the top/bottom
            # rows clear toolbars. (Finalized after the loop, with any
            # section markers attached and a nudge toward the visible
            # height, as button rows are.)
            rowprep.show_buffer_top += (
                top_buffer
                + row_header_height(row)
                + row_titles_height(row, _n)
                - titles_tuck
            )
            rowprep.show_buffer_bottom += (
                bot_buffer
                + footnote_height
                - footnote_tuck
                + row_footer_height(row)
            )
            y = prep_row_footer(
                row,
                rowprep,
                y=y,
                anchors_x=band_anchors_x,
                tdelay=None if immediate else (tdelaybase + 0.05 * tscale),
                packages=packages,
            )
            rowprep.bounds_top, rowprep.bounds_bottom = ydebugtop, y
            if wants_debug_draw(row.debug, DebugDrawKind.ROWS):
                prepcalls2.prep_row_debug(
                    (
                        width - cmargin_left - cmargin_right,
                        ydebugtop - y,
                    ),
                    (cmargin_left, y),
                    None if immediate else tdelaybase,
                    rowprep.decorations,
                )
                prep_row_part_debug(
                    row,
                    rowprep,
                    _n,
                    x=(cmargin_left, width - cmargin_right),
                    content=rowprep.show_part,
                )
            y -= row.spacing_bottom
            continue

        # Anything else is a (scrolling) row of buttons.
        assert isinstance(row, dui2.ButtonRow)
        padleft, _padright, padtop, padbottom = row.get_padding()
        content_align = row_content_align(row)
        rowprep.entry_index = row_entry_index(row.buttons)
        y -= row.spacing_top
        y -= gaps[i]

        # Debug bounds cover the whole row: header band to footer band
        # (not the spacing outside them).
        ydebugtop = y

        y = prep_row_header(
            row,
            rowprep,
            y=y,
            anchors_x=band_anchors_x,
            tdelay=None if immediate else (tdelaybase + 0.05 * tscale),
            packages=packages,
        )

        y = prep_row_titles(
            row,
            rowprep,
            y=y,
            width=width,
            margins=cmargins,
            header_insets=(header_inset_left, header_inset_right),
            center=geom.center,
            tdelaybase=None if immediate else tdelaybase,
            tscale=tscale,
            native=_n,
        )

        y -= rowprep.height  # includes padding-top/bottom

        # The h-scroll's bottom: the scrollable part's, less the strip
        # its bar shows in (see _SCROLLBAR_STRIP).
        hscroll_y = y - _SCROLLBAR_STRIP
        rowprep.show_part = (
            hscroll_y,
            hscroll_y + rowprep.height + _SCROLLBAR_STRIP,
        )
        rowprep.show_x = (
            cmargin_left,
            width - cmargin_right,
        )

        # The footnote strip sits below the scrollable part.
        footnote_height = row_footnote_height(row, _n)
        y -= footnote_height
        prep_row_footnote(
            row,
            rowprep,
            y=y,
            width=width,
            margins=cmargins,
            header_insets=(header_inset_left, header_inset_right),
            center=geom.center,
            tdelaybase=None if immediate else tdelaybase,
            tscale=tscale,
            native=_n,
        )

        y = prep_row_footer(
            row,
            rowprep,
            y=y,
            anchors_x=band_anchors_x,
            tdelay=None if immediate else (tdelaybase + 0.05 * tscale),
            packages=packages,
        )
        rowprep.bounds_top, rowprep.bounds_bottom = ydebugtop, y

        if wants_debug_draw(row.debug, DebugDrawKind.ROWS):
            prepcalls2.prep_row_debug(
                (
                    width - cmargin_left - cmargin_right,
                    ydebugtop - y,
                ),
                (cmargin_left, y),
                None if immediate else tdelaybase,
                rowprep.decorations,
            )
            prep_row_part_debug(
                row, rowprep, _n, x=(cmargin_left, width - cmargin_right)
            )

        # Where we clip: the page's width, or narrower in a section.
        clip_l, clip_r = (0.0, width) if geom.clip is None else geom.clip
        rowprep.hscrollcall = partial(
            bui.hscrollwidget,
            size=(clip_r - clip_l, rowprep.height + _SCROLLBAR_STRIP),
            position=(clip_l, hscroll_y),
            # (Page arrows only; they stay at the screen edges even when
            # our content is indented to a column -- or at our clip
            # edges, when a section narrows us.)
            button_inset_left=arrow_left if geom.clip is None else 0.0,
            button_inset_right=arrow_right if geom.clip is None else 0.0,
            claims_left_right=True,
            highlight=False,
            border_opacity=0.0,
            center_small_content=content_align is dui2.HAlign.CENTER,
            simple_culling_h=row.simple_culling_h,
            scrollbar_visible=row.show_scrollbar,
            clean_layout=True,
            # Have the page-left/right buttons scale in along with our
            # buttons and decorations, but only when those are actually
            # animating; otherwise (a refresh in place, a back-nav to a
            # page we already have) the arrows would be the lone thing
            # transitioning while the rest of the page simply appears.
            transition_in=not immediate,
        )
        # Ideally we could just always use row-width, but currently that
        # gets us right-aligned stuff when center-small-content is off.
        hsubwidth = (
            rowprep.width
            if content_align is dui2.HAlign.CENTER
            else max(clip_r - clip_l, rowprep.width)
        )
        rowprep.hsubcall = partial(
            bui.containerwidget,
            size=(hsubwidth, rowprep.height + _SCROLLBAR_STRIP),
            background=False,
        )
        # (Less whatever a narrower clip cut off our content's start, so
        # buttons land where they would on the page.)
        x = cmargin_left + BUTTON_ROW_EDGE_INSET + padleft
        x -= clip_l
        if content_align is dui2.HAlign.RIGHT:
            # Shove everything over by whatever room is left. (Content
            # at least as wide as the row has none, and simply scrolls.)
            x += hsubwidth - rowprep.width
        # Calc height of buttons themselves (includes button padding but
        # not row padding).
        button_row_height = rowprep.height - padtop - padbottom
        bcount = len(row.buttons)

        # Clamp or max delay if we've got lots of buttons.
        bdelaymax = min(0.5, 0.03 * bcount) * tscale
        for j, button in enumerate(row.buttons):
            # Leftmost buttons appear first; pop-in sweeps left-to-right.
            tdelayamt = j / max(1, bcount - 1)
            tdelay = tdelaybase + tdelayamt * bdelaymax

            xorig = x
            x += button.padding_left * button.scale
            bscale = button.scale
            bwidthfull = bscale * button_size(button)[0]
            bwidthpadded, bheightpadded = button_padded_size(button)

            # Vertically center the button plus its padding, then move
            # up past bottom padding to get button bottom.
            to_button_bottom = (
                button_row_height - bheightpadded
            ) * 0.5 + button.padding_bottom * button.scale

            widgetid = _button_widget_id(button)
            _note_button_flags(button, widgetid)

            # Nudge what we try to keep on screen (the button and its
            # padding) towards the total visible width of the scroll
            # area. (1.0 should lead to always perfect centering, but
            # that might feel too aggressive.)
            amt = 0.0 if selection_centering_disabled() else 0.6
            buffer_extra = max(0.0, (visible_width - bwidthpadded) * 0.5 * amt)

            buttonprep = prep_button(
                button,
                position=(x, _SCROLLBAR_STRIP + padbottom + to_button_bottom),
                widgetid=widgetid,
                tdelay=None if immediate else tdelay,
                packages=packages,
                native=_n,
                show_buffers_h=(
                    button.padding_left * bscale + buffer_extra,
                    button.padding_right * bscale + buffer_extra,
                ),
                disabled=button.disabled,
            )

            # With row-debug on, visualize the area we try to scroll to
            # show when each button is selected. Note that we're clamped
            # by the h-scroll here so we have to draw a separate box for
            # the row title/subtitle. (Drawn ahead of the button's own
            # decorations.)
            if wants_debug_draw(row.debug, DebugDrawKind.ROWS):
                rowdebug: list[DecorationPrep] = []
                prepcalls2.prep_row_debug_button(
                    (bwidthpadded, rowprep.height),
                    (xorig, _SCROLLBAR_STRIP),
                    None if immediate else tdelay,
                    rowdebug,
                )
                buttonprep.decorations[:0] = rowdebug

            rowprep.buttons.append(buttonprep)

            x += (
                bwidthfull
                + (button.padding_right * button.scale)
                + row.button_spacing
            )

        # Show-buffers for our h-scroll (finalized after the loop).

        # Incorporate top buffer so we scroll all the way up
        # when selecting the top row (and stay clear of
        # toolbars).
        rowprep.show_buffer_top += top_buffer
        rowprep.show_buffer_bottom += bot_buffer

        # Scroll so header/titles and footnote/footer are in view
        # when selecting. Note that we don't need to account for
        # padding-top/bottom since the h-scroll that we're
        # applying to encompasses both -- and its bar's strip, which
        # covers that much of what's below.
        rowprep.show_buffer_top += row_header_height(row)
        rowprep.show_buffer_top += row_titles_height(row, _n)
        rowprep.show_buffer_bottom += footnote_height
        rowprep.show_buffer_bottom += row_footer_height(row)
        rowprep.show_buffer_bottom -= _SCROLLBAR_STRIP

        y -= row.spacing_bottom

    # A heading with nothing selectable after it: the last selectable
    # row above it keeps it in view instead. (There always is one; a
    # page with nothing selectable gets an Ok button at its end.)
    if pending_top_attach is not None and last_selectable is not None:
        last_selectable.show_buffer_bottom += pending_top_attach

    _sections.prep_section_backings(
        section_spans,
        rows,
        column=column,
        page_inset=look.h_inset,
        tdelay_of=None if immediate else (lambda i: (0.15 + 0.06 * i) * tscale),
    )
    _sections.prep_section_debug(
        section_spans,
        page_rows_filtered,
        rows,
        geoms,
        width=width,
    )

    # Every attachment is known now; finalize each selectable row's
    # show-buffers.
    finalize_show_buffers(
        page_rows_filtered,
        rows,
        scroll_height=scroll_height,
        page=(top_buffer, bot_buffer),
        scrollbar_strip=_SCROLLBAR_STRIP,
    )

    return PagePrep(
        rootcall=rootcall,
        rows=rows,
        width=width,
        height=height,
        simple_culling_v=simple_culling_v,
        center_vertically=center_vertically,
        show_scrollbar=show_scrollbar,
        title=title,
        root_post_calls=root_post_calls,
        immediate=immediate,
        look=look,
        selected_widget_id=selected_widget_id,
    )
