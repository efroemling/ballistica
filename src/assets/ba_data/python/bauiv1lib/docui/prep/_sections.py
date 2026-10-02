# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui sections: the heading over and note under their rows.

A :class:`~bacommon.docui.v2.Section`'s rows lay out like any others;
page prep sets a :class:`SectionHead` before them (header band, title,
subtitle) and a :class:`SectionFoot` after (footnote, footer band).
Those draw like a row's own titles and footnote but a bit larger and
standing further from the rows they head or close, so they read as
belonging to the group rather than to one row. They hold no content
and are not selectable; page prep attaches each to a neighboring
selectable row for navigation.
"""

import copy
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
import bauiv1 as bui
from bauiv1 import _commonassets, _uiv1assets

from bauiv1lib.docui._layout import BUTTON_INSET, TEXT_INSET
from bauiv1lib.docui.prep._controlrows import ColumnRow, is_column_row
from bauiv1lib.docui.prep._rowbands import (
    prep_row_header,
    prep_row_footer,
    row_header_height,
    row_footer_height,
)
from bauiv1lib.docui.prep._rowtext import line_count, row_text_x_and_maxwidth

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    from typing import Callable

    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui.prep._types import RowPrep

#: Section title text scale: larger than a row title's (1.15), so a
#: heading reads as a level above the rows' own titles.
_SECTION_TITLE_SCALE = 1.35

#: Row-title flatness/shadow, which section titles share.
_SECTION_TITLE_FLATNESS = 0.5
_SECTION_TITLE_SHADOW = 1.0

#: Vertical space a section title takes: one line's strip plus this
#: much per extra line (the text sits centered in each line's strip).
_SECTION_TITLE_LINE_HEIGHT = 30.0 * _SECTION_TITLE_SCALE

#: The same for a subtitle (row-subtitle scale, 0.7).
_SECTION_SUBTITLE_LINE_HEIGHT = 22.0
#: A subtitle strip's spare room below its last line.
_SECTION_SUBTITLE_PADDING_BOTTOM = 8.0

#: Standing room a heading keeps from whatever precedes it (on top of
#: the page's row spacing; none when it is the first thing on the
#: page) and from the first row of its section. The section stands
#: apart from what came before more than its rows stand apart from
#: each other, and its heading hugs its own rows, so the grouping
#: reads at a glance.
_SECTION_BEGIN_STANDOFF_ABOVE = 16.0
_SECTION_BEGIN_STANDOFF = 2.0

#: A footnote's strip: its lines plus this much padding below (like a
#: row footnote's).
_SECTION_FOOTNOTE_LINE_HEIGHT = 22.0
_SECTION_FOOTNOTE_PADDING_BOTTOM = 10.0

#: Standing room between a section's last row and its closing note
#: (on top of the page's row spacing).
_SECTION_END_STANDOFF = 10.0


@dataclass
class SectionHead:
    """Layout entry for a section's heading, set before its rows.

    :meta private:
    """

    section: dui2.Section


@dataclass
class SectionFoot:
    """Layout entry for a section's note, set after its rows.

    ``space_below`` is room it leaves below itself (outside any card):
    how a note-less section stands plain rows after it apart from its
    own.

    :meta private:
    """

    section: dui2.Section
    space_below: float = 0.0


#: What page prep lays out: rows, plus sections' headings and notes.
type LayoutEntry = dui2.ButtonRow | ColumnRow | SectionHead | SectionFoot


def _nothing_here_row(row: dui2.ButtonRow) -> dui2.ButtonRow:
    """A copy of an empty button row with a placeholder in it."""
    row = copy.deepcopy(row)
    row.buttons.append(
        dui2.Button(
            label=_commonassets.strings.status.nothing_here.spec,
            label_color=(1, 1, 1, 0.3),
            size=(220, 100),
            label_scale=0.6,
            texture=_uiv1assets.textures.button_square_wide,
            padding_top=-8,
            padding_bottom=-10,
            color=(0.2, 0.2, 0.2, 0.15),
            action=dui2.Local(default_sound=False),
        )
    )
    return row


def layout_entries(
    page: dui2.Page,
) -> tuple[list[LayoutEntry], list[tuple[dui2.Section, int, int]]]:
    """The flat list of what a page lays out, and its sections' spans.

    Rows we know how to display, each section expanded in place into
    its :class:`SectionHead`, its rows and (when it has one) its
    :class:`SectionFoot`. Each span is (section, first row index, last
    row index) into the list; last < first for a section with no rows.

    :meta private:
    """
    entries: list[LayoutEntry] = []
    spans: list[tuple[dui2.Section, int, int]] = []
    unknown_rows = False

    def _add_row(pagerow: dui2.Row) -> bool:
        """Add a non-section row; return whether we knew how to."""
        # (Button rows first, whatever their layout: an empty one gets
        # a placeholder.)
        if isinstance(pagerow, dui2.ButtonRow):
            entries.append(
                pagerow if pagerow.buttons else _nothing_here_row(pagerow)
            )
            return True
        if is_column_row(pagerow):
            entries.append(pagerow)
            return True
        return False

    for pageindex, pagerow in enumerate(page.rows):
        if not isinstance(pagerow, dui2.Section):
            if not _add_row(pagerow):
                unknown_rows = True
            continue
        entries.append(SectionHead(pagerow))
        first_row = len(entries)
        for secrow in pagerow.rows:
            if isinstance(secrow, dui2.Section):
                bui.uilog.error(
                    'Doc-ui sections do not nest; ignoring one inside another.'
                )
            elif not _add_row(secrow):
                unknown_rows = True
        spans.append((pagerow, first_row, len(entries) - 1))
        # The note comes only when there's something to it, or to
        # stand plain rows after us apart from the group. (Another
        # section's heading does that itself, and the page's end needs
        # nothing.)
        nextrow = (
            page.rows[pageindex + 1] if pageindex + 1 < len(page.rows) else None
        )
        stand_apart = nextrow is not None and not isinstance(
            nextrow, dui2.Section
        )
        if (
            section_has_note(pagerow)
            or pagerow.spacing_bottom != 0.0
            or padding_bottom(pagerow) != 0.0
            or stand_apart
        ):
            # (A note stands what follows apart itself; without one we
            # leave the room it would have, below everything.)
            entries.append(
                SectionFoot(
                    pagerow,
                    space_below=(
                        _SECTION_END_STANDOFF + page.row_spacing
                        if stand_apart and not section_has_note(pagerow)
                        else 0.0
                    ),
                )
            )
    if unknown_rows:
        bui.uilog.error('Got unknown row type(s) in doc-ui; ignoring.')
    return entries, spans


def section_has_note(sec: dui2.Section) -> bool:
    """Does a section have anything to draw under its rows?

    :meta private:
    """
    return sec.footnote is not None or row_footer_height(sec) > 0.0


def section_has_heading(sec: dui2.Section) -> bool:
    """Does a section have anything to draw over its rows?

    :meta private:
    """
    return (
        sec.title is not None
        or sec.subtitle is not None
        or row_header_height(sec) > 0.0
    )


def entry_gaps(entries: list[LayoutEntry], row_spacing: float) -> list[float]:
    """The space above each layout entry.

    The page's row spacing, except where there's nothing to space: a
    section's first row hugs a heading-less section's top (just its
    padding above), and a note-less section's closing entry hugs its
    last row (just its padding below). So a card's rect -- padding to
    padding -- holds nothing but what's in it.

    :meta private:
    """
    gaps: list[float] = []
    for i, entry in enumerate(entries):
        prev = entries[i - 1] if i > 0 else None
        hugs = (
            prev is None
            or (
                isinstance(entry, SectionFoot)
                and not section_has_note(entry.section)
            )
            or (
                isinstance(prev, SectionHead)
                and not section_has_heading(prev.section)
            )
        )
        gaps.append(0.0 if hugs else row_spacing)
    return gaps


def padding_top(sec: dui2.Section) -> float:
    """A section's card padding above its content (0 if not a card).

    :meta private:
    """
    return 0.0 if sec.backing is None else sec.backing.padding_top


def padding_bottom(sec: dui2.Section) -> float:
    """A section's card padding below its content (0 if not a card).

    :meta private:
    """
    return 0.0 if sec.backing is None else sec.backing.padding_bottom


def card_edges(
    backing: dui2.SectionBacking, column: tuple[float, float]
) -> tuple[float, float]:
    """A card's left and right x: its max width at most, centered.

    ``column`` is the column's left and right x.

    :meta private:
    """
    colwidth = column[1] - column[0]
    cardwidth = (
        colwidth
        if backing.max_width is None
        else min(colwidth, backing.max_width)
    )
    center = (column[0] + column[1]) * 0.5
    return center - cardwidth * 0.5, center + cardwidth * 0.5


def section_backing_bounds(
    sec: dui2.Section,
    rows: list[RowPrep],
    first_row: int,
    last_row: int,
) -> tuple[float, float]:
    """The (top, bottom) y of a prepped card's rect.

    From its heading's top (else its first row's) to its note's bottom
    (else its last row's), its paddings outside those. ``rows`` are the
    page's row preps, indexed like its layout entries (the heading is
    the one before ``first_row``, any note the one after ``last_row``).

    :meta private:
    """
    top = (
        rows[first_row - 1].bounds_top
        if section_has_heading(sec)
        else rows[first_row].bounds_top + padding_top(sec)
    )
    if section_has_note(sec):
        bottom = rows[last_row + 1].bounds_bottom
    else:
        bottom = rows[last_row].bounds_bottom - padding_bottom(sec)
    return top, bottom


def prep_section_backings(
    spans: list[tuple[dui2.Section, int, int]],
    rows: list[RowPrep],
    *,
    column: tuple[float, float],
    tdelay_of: Callable[[int], float] | None,
) -> None:
    """Prep every card's backing image, once its rows are prepped.

    The card's rect is :func:`card_edges` across and
    :func:`section_backing_bounds` down; a texture is stretched past it
    so its pinned points land on its edges (see
    :class:`~bacommon.docui.v2.SectionBacking`). Each goes in its
    heading's decorations, which get created before the section's rows
    and so draw beneath them. ``tdelay_of`` gives a layout entry's
    transition delay by index (None to pop in instantly).

    :meta private:
    """
    # pylint: disable=cyclic-import
    from bauiv1lib.docui.prep._calls2 import prep_section_backing

    for sec, first_row, last_row in spans:
        backing = sec.backing
        if backing is None or first_row > last_row or backing.color[3] <= 0.0:
            continue
        left, right = card_edges(backing, column)
        top, bottom = section_backing_bounds(sec, rows, first_row, last_row)
        # (Pins only mean anything for a texture; a flat fill's edges
        # are its shape's.)
        pin_l, pin_r = (0.0, 0.0) if backing.texture is None else backing.h_pin
        pin_t, pin_b = (0.0, 0.0) if backing.texture is None else backing.v_pin
        imgwidth = (right - left) / max(0.01, 1.0 - pin_l - pin_r)
        imgheight = (top - bottom) / max(0.01, 1.0 - pin_t - pin_b)
        decorations = rows[first_row - 1].decorations
        prep_section_backing(
            (imgwidth, imgheight),
            (left - pin_l * imgwidth, bottom - pin_b * imgheight),
            color=backing.color,
            texture=backing.texture,
            tdelay=None if tdelay_of is None else tdelay_of(first_row),
            out_decoration_preps=decorations,
        )
        # Beneath the heading's own band decorations too (and its text,
        # which instantiation creates after its decorations).
        decorations.insert(0, decorations.pop())


@dataclass
class EntryGeom:
    """Horizontal geometry for laying out one layout entry.

    Everything here derives from a column (see :func:`column_geometry`):
    the page's, or a card's. ``clip`` is where a button row's h-scroll
    clips (left and right x), or None for the page-wide default;
    ``center`` is where centered content centers, and how wide centered
    text may be.

    :meta private:
    """

    cmargin_left: float
    cmargin_right: float
    control_left: float
    control_right: float
    band_anchors_x: tuple[float, float, float]
    clip: tuple[float, float] | None
    center: tuple[float, float]


def column_geometry(
    left: float,
    right: float,
    *,
    width: float,
    buffers: tuple[float, float],
    clip: tuple[float, float] | None,
) -> EntryGeom:
    """Geometry for laying out in a column from ``left`` to ``right``.

    Symmetric: button rows' buttons sit
    :data:`~bauiv1lib.docui._layout.BUTTON_INSET` in from either edge,
    text and control rows' contents
    :data:`~bauiv1lib.docui._layout.TEXT_INSET`, and centered things
    center on the column.
    ``buffers`` are the page's left and right buffers (the column's
    margins are what remains of ``width`` outside them).

    :meta private:
    """
    left_buffer, right_buffer = buffers
    center = (left + right) * 0.5
    return EntryGeom(
        cmargin_left=left - left_buffer,
        cmargin_right=width - right - right_buffer,
        # Control rows' labels start where text does; their controls end
        # at its mirror.
        control_left=left + TEXT_INSET,
        control_right=right - TEXT_INSET,
        band_anchors_x=(left + TEXT_INSET, center, right - TEXT_INSET),
        clip=clip,
        center=(center, max(1.0, right - left - 2.0 * BUTTON_INSET)),
    )


def entry_geometry(
    entries: list[LayoutEntry],
    spans: list[tuple[dui2.Section, int, int]],
    *,
    base: EntryGeom,
    width: float,
    buffers: tuple[float, float],
    column: tuple[float, float],
) -> list[EntryGeom]:
    """Each layout entry's horizontal geometry (see :class:`EntryGeom`).

    ``base`` is the page-wide geometry and ``column`` the column's left
    and right x. A card's entries (heading, rows, note) get the card's
    own column -- its button rows' buttons ``content_inset`` in from its
    edges, as the page's are
    :data:`~bauiv1lib.docui._layout.BUTTON_INSET` in from its column --
    and clip button rows at its edges; the rest get ``base``.

    :meta private:
    """
    geoms = [base] * len(entries)
    for sec, first_row, last_row in spans:
        if sec.backing is None:
            continue
        clip_l, clip_r = card_edges(sec.backing, column)
        inset = sec.backing.content_inset
        geom = column_geometry(
            clip_l + inset - BUTTON_INSET,
            clip_r - inset + BUTTON_INSET,
            width=width,
            buffers=buffers,
            clip=(clip_l, clip_r),
        )
        # The heading before the rows and any note after them too.
        last = last_row + 1
        if last < len(entries) and isinstance(entries[last], SectionFoot):
            last += 1
        for index in range(first_row - 1, last):
            geoms[index] = geom
    return geoms


def _title_height(
    sec: dui2.Section,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> float:
    if sec.title is None:
        return 0.0
    return _SECTION_TITLE_LINE_HEIGHT * line_count(sec.title, native)


def _subtitle_height(
    sec: dui2.Section,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> float:
    if sec.subtitle is None:
        return 0.0
    return (
        _SECTION_SUBTITLE_LINE_HEIGHT * line_count(sec.subtitle, native)
        + _SECTION_SUBTITLE_PADDING_BOTTOM
    )


def section_head_height(
    head: SectionHead,
    native: Callable[[LangStrSpec | int], bui.LangStr],
    *,
    first: bool,
) -> float:
    """Total vertical space a section heading takes.

    Its standoffs, the section's top spacing, header band and text
    strips; everything but the page's row spacing around it. ``first``
    is whether it is the first thing on the page (no standoff above
    then).

    :meta private:
    """
    sec = head.section
    return (
        (0.0 if first else _SECTION_BEGIN_STANDOFF_ABOVE)
        + sec.spacing_top
        + padding_top(sec)
        + row_header_height(sec)
        + _title_height(sec, native)
        + _subtitle_height(sec, native)
        + (_SECTION_BEGIN_STANDOFF if section_has_heading(sec) else 0.0)
    )


def section_foot_height(
    foot: SectionFoot,
    native: Callable[[LangStrSpec | int], bui.LangStr],
) -> float:
    """Total vertical space a section note takes.

    Its standoff (with a note), footnote strip, footer band, padding,
    ``space_below`` and the section's bottom spacing; everything but
    the space above it (see :func:`entry_gaps`).

    :meta private:
    """
    sec = foot.section
    footnote = (
        0.0
        if sec.footnote is None
        else (
            _SECTION_FOOTNOTE_LINE_HEIGHT * line_count(sec.footnote, native)
            + _SECTION_FOOTNOTE_PADDING_BOTTOM
        )
    )
    return (
        (_SECTION_END_STANDOFF if section_has_note(sec) else 0.0)
        + footnote
        + row_footer_height(sec)
        + padding_bottom(sec)
        + foot.space_below
        + sec.spacing_bottom
    )


def prep_section_head(
    head: SectionHead,
    rowprep: RowPrep,
    *,
    y: float,
    width: float,
    margins: tuple[float, float, float, float],
    buffers: tuple[float, float],
    header_insets: tuple[float, float],
    center: tuple[float, float],
    anchors_x: tuple[float, float, float],
    tdelaybase: float | None,
    tscale: float,
    native: Callable[[LangStrSpec | int], bui.LangStr],
    packages: list[ApverNum],
    first: bool,
) -> float:
    """Prep a section heading below ``y``; return the new y.

    Lays out top to bottom: standoff (unless ``first``), the section's
    top spacing, padding, header band, title, subtitle, standoff (with
    a heading; see :func:`section_head_height`).

    :meta private:
    """
    row = head.section
    if not first:
        y -= _SECTION_BEGIN_STANDOFF_ABOVE
    y -= row.spacing_top
    # (Where a backing's top goes, padding included; see
    # :func:`section_backing_bounds`.)
    rowprep.bounds_top = y
    y -= padding_top(row)
    y = prep_row_header(
        row,
        rowprep,
        y=y,
        anchors_x=anchors_x,
        tdelay=None if tdelaybase is None else (tdelaybase + 0.05 * tscale),
        packages=packages,
    )
    align = dui2.HAlign.LEFT if row.title_align is None else row.title_align
    text_x, maxwidth = row_text_x_and_maxwidth(
        align,
        width=width,
        margins=margins,
        buffers=buffers,
        header_insets=header_insets,
        center=center,
    )
    h_align = align.name.lower()
    if row.title is not None:
        height = _title_height(row, native)
        rowprep.titlecalls.append(
            partial(
                bui.textwidget,
                position=(text_x, y - height * 0.5),
                size=(0, 0),
                text=native(row.title),
                # Row-title coloring (brighter than labels), at the
                # larger section scale.
                color=(
                    (0.95, 1.0, 0.97, 1.0)
                    if row.title_color is None
                    else row.title_color
                ),
                flatness=(
                    _SECTION_TITLE_FLATNESS
                    if row.title_flatness is None
                    else row.title_flatness
                ),
                shadow=(
                    _SECTION_TITLE_SHADOW
                    if row.title_shadow is None
                    else row.title_shadow
                ),
                scale=_SECTION_TITLE_SCALE,
                maxwidth=maxwidth,
                h_align=h_align,
                v_align='center',
                literal=True,
                transition_delay=(
                    None if tdelaybase is None else (tdelaybase + 0.1 * tscale)
                ),
                transition_type='scale',
            )
        )
        y -= height
    if row.subtitle is not None:
        height = _subtitle_height(row, native)
        text_height = height - _SECTION_SUBTITLE_PADDING_BOTTOM
        rowprep.titlecalls.append(
            partial(
                bui.textwidget,
                position=(text_x, y - text_height * 0.5),
                size=(0, 0),
                text=native(row.subtitle),
                color=(
                    (0.6, 0.74, 0.6)
                    if row.subtitle_color is None
                    else row.subtitle_color
                ),
                flatness=row.subtitle_flatness,
                shadow=row.subtitle_shadow,
                scale=0.7,
                maxwidth=maxwidth,
                h_align=h_align,
                v_align='center',
                literal=True,
                transition_delay=(
                    None if tdelaybase is None else (tdelaybase + 0.2 * tscale)
                ),
                transition_type='scale',
            )
        )
        y -= height
    return y - (_SECTION_BEGIN_STANDOFF if section_has_heading(row) else 0.0)


def prep_section_foot(
    foot: SectionFoot,
    rowprep: RowPrep,
    *,
    y: float,
    width: float,
    margins: tuple[float, float, float, float],
    buffers: tuple[float, float],
    header_insets: tuple[float, float],
    center: tuple[float, float],
    anchors_x: tuple[float, float, float],
    tdelaybase: float | None,
    tscale: float,
    native: Callable[[LangStrSpec | int], bui.LangStr],
    packages: list[ApverNum],
) -> float:
    """Prep a section note below ``y``; return the new y.

    Lays out top to bottom: standoff (with a note), footnote, footer
    band, padding, ``space_below``, the section's bottom spacing (see
    :func:`section_foot_height`).

    :meta private:
    """
    row = foot.section
    if section_has_note(row):
        y -= _SECTION_END_STANDOFF
    if row.footnote is not None:
        align = dui2.HAlign.LEFT if row.title_align is None else row.title_align
        text_x, maxwidth = row_text_x_and_maxwidth(
            align,
            width=width,
            margins=margins,
            buffers=buffers,
            header_insets=header_insets,
            center=center,
        )
        text_height = _SECTION_FOOTNOTE_LINE_HEIGHT * line_count(
            row.footnote, native
        )
        rowprep.titlecalls.append(
            partial(
                bui.textwidget,
                position=(text_x, y - text_height * 0.5),
                size=(0, 0),
                text=native(row.footnote),
                color=(
                    (0.6, 0.74, 0.6)
                    if row.footnote_color is None
                    else row.footnote_color
                ),
                flatness=row.footnote_flatness,
                shadow=row.footnote_shadow,
                scale=0.7,
                maxwidth=maxwidth,
                h_align=align.name.lower(),
                v_align='center',
                literal=True,
                transition_delay=(
                    None if tdelaybase is None else (tdelaybase + 0.1 * tscale)
                ),
                transition_type='scale',
            )
        )
        y -= text_height + _SECTION_FOOTNOTE_PADDING_BOTTOM
    y = prep_row_footer(
        row,
        rowprep,
        y=y,
        anchors_x=anchors_x,
        tdelay=None if tdelaybase is None else (tdelaybase + 0.05 * tscale),
        packages=packages,
    )
    y -= padding_bottom(row)
    # (Where a backing's bottom goes, padding included.)
    rowprep.bounds_bottom = y
    return y - foot.space_below - row.spacing_bottom
