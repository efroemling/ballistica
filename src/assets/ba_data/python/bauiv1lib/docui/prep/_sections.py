# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui sections: their extent, cards and spacing.

A :class:`~bacommon.docui.v2.Section`'s rows lay out like any others,
its heading and note among them as text rows (see
:func:`section_rows`; a section's own heading fields become those
too). Page prep sets a :class:`SectionHead` before them and a
:class:`SectionFoot` after: no content, just the room a section keeps
from its neighbors and a card's padding, marking where a card's
backing starts and ends. Neither is selectable; page prep attaches
each to a neighboring selectable row for navigation.
"""

import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
import bauiv1 as bui
from bauiv1 import _commonassets, _uiv1assets

from bauiv1lib.docui._debugdraw import DebugDrawKind, wants_debug_draw
from bauiv1lib.docui.prep._controlrows import ColumnRow, is_column_row
from bauiv1lib.docui.prep._headings import HEADING_GAP
from bauiv1lib.docui.prep._rowbands import (
    row_header_height,
    row_footer_height,
)
from bauiv1lib.docui.prep._textrows import TextEntry, fold_text_rows

if TYPE_CHECKING:
    from typing import Callable

    from bauiv1lib.docui._pagelook import RowSpacing
    from bauiv1lib.docui.prep._types import RowPrep

#: Standing room a section keeps from whatever precedes it, on top of
#: the spacing between them (none when it is the first thing on the
#: page): it stands apart from what came before more than its rows
#: stand apart from each other, so the grouping reads at a glance.
_SECTION_BEGIN_STANDOFF_ABOVE = 16.0

#: The same below a section that plain rows follow (unless it ends in
#: a standalone note, which stands them apart itself).
_SECTION_END_STANDOFF = 10.0


@dataclass
class SectionHead:
    """Layout entry for a section's start, set before its rows.

    :meta private:
    """

    section: dui2.Section


@dataclass
class SectionFoot:
    """Layout entry for a section's end, set after its rows.

    ``space_below`` is room it leaves below itself (outside any card).

    :meta private:
    """

    section: dui2.Section
    space_below: float = 0.0


#: What page prep lays out: rows, plus sections' headings and notes and
#: text rows standing alone.
type LayoutEntry = (
    dui2.ButtonRow | ColumnRow | SectionHead | SectionFoot | TextEntry
)

#: The layout entries that aren't rows (nothing selectable in them).
MARKER_ENTRY_TYPES = (SectionHead, SectionFoot, TextEntry)


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


#: Pages we've already warned have nothing selectable on them. Each is
#: built again for every redisplay and refresh; once a run says it.
_g_warned_unselectable: set[str] = set()

#: Pages we've already warned have text/band rows that couldn't attach.
_g_warned_unattached: set[str] = set()


def _ok_row() -> dui2.ButtonRow:
    """A lone button that closes the window.

    What we end a page with when it gives us nothing to select. It is
    there for selection to land on, not to be noticed: colored like
    the window behind it, so the page still reads as the page's
    author drew it.
    """
    return dui2.ButtonRow(
        buttons=[
            dui2.Button(
                _commonassets.strings.actions.ok.spec,
                action=dui2.Local(close_window=True),
                style=dui2.ButtonStyle.MEDIUM,
                size=(130, 50),
                # (The window backing's own tint.)
                color=(0.4, 0.37, 0.49, 1.0),
                label_color=(0.75, 0.72, 0.8, 1.0),
            )
        ],
        center_content=True,
    )


def section_rows(sec: dui2.Section) -> list[dui2.Row]:
    """A section's rows with its own heading and note fields as rows.

    The header band, title (``HEADING`` size) and subtitle before its
    rows, as a :class:`~bacommon.docui.v2.HeaderRow`,
    :class:`~bacommon.docui.v2.TitleRow` and
    :class:`~bacommon.docui.v2.SubtitleRow`; the footnote and footer
    band after, as a standalone :class:`~bacommon.docui.v2.FootnoteRow`
    and :class:`~bacommon.docui.v2.FooterRow`. So a section saying it
    the old way lays out exactly as one saying it with those rows.

    :meta private:
    """
    head: list[dui2.Row] = []
    foot: list[dui2.Row] = []
    align = sec.title_align
    if row_header_height(sec) > 0.0:
        head.append(
            dui2.HeaderRow(
                height=sec.header_height,
                scale=sec.header_scale,
                decorations_left=sec.header_decorations_left,
                decorations_center=sec.header_decorations_center,
                decorations_right=sec.header_decorations_right,
            )
        )
    if sec.title is not None:
        head.append(
            dui2.TitleRow(
                sec.title,
                size=dui2.TitleSize.HEADING,
                color=sec.title_color,
                flatness=sec.title_flatness,
                shadow=sec.title_shadow,
                wrap=sec.title_wrap,
                align=align,
                spacing_bottom=(
                    sec.spacing_title if sec.subtitle is None else 0.0
                ),
            )
        )
    if sec.subtitle is not None:
        head.append(
            dui2.SubtitleRow(
                sec.subtitle,
                color=sec.subtitle_color,
                flatness=sec.subtitle_flatness,
                shadow=sec.subtitle_shadow,
                wrap=sec.subtitle_wrap,
                align=align,
                spacing_top=(
                    0.0 if sec.title is None else sec.spacing_subtitle
                ),
                spacing_bottom=sec.spacing_title,
            )
        )
    if sec.footnote is not None:
        foot.append(
            dui2.FootnoteRow(
                sec.footnote,
                attach=False,
                color=sec.footnote_color,
                flatness=sec.footnote_flatness,
                shadow=sec.footnote_shadow,
                wrap=sec.footnote_wrap,
                align=align,
                spacing_top=sec.spacing_footnote,
            )
        )
    if row_footer_height(sec) > 0.0:
        foot.append(
            dui2.FooterRow(
                height=sec.footer_height,
                scale=sec.footer_scale,
                decorations_left=sec.footer_decorations_left,
                decorations_center=sec.footer_decorations_center,
                decorations_right=sec.footer_decorations_right,
                attach=False,
            )
        )
    if not head and not foot:
        return sec.rows
    return head + sec.rows + foot


def layout_entries(
    page: dui2.Page, description: str
) -> tuple[list[LayoutEntry], list[tuple[dui2.Section, int, int]]]:
    """The flat list of what a page lays out, and its sections' spans.

    Rows we know how to display, each section expanded in place into
    its :class:`SectionHead`, its rows (its heading and note among
    them; see :func:`section_rows`) and its :class:`SectionFoot`. Each
    span is (section, first row index, last row index) into the list;
    last < first for a section with no rows.

    A page with nothing selectable on it gets an Ok button at its end.
    Keyboard and controller selection needs something in a window to
    land on: with nothing there it moves into the page and cannot get
    back out to the toolbars.

    ``description`` names the page in anything logged about it.

    :meta private:
    """
    entries: list[LayoutEntry] = []
    spans: list[tuple[dui2.Section, int, int]] = []
    unknown_rows = False

    def _add_row(pagerow: dui2.Row | TextEntry) -> bool:
        """Add a non-section row; return whether we knew how to."""
        if isinstance(pagerow, TextEntry):
            entries.append(pagerow)
            return True
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

    # (Text rows attach to their rows here, or stand alone; see
    # fold_text_rows().)
    unattached: list[str] = []
    pagerows = fold_text_rows(page.rows, unattached=unattached)
    for pageindex, pagerow in enumerate(pagerows):
        if not isinstance(pagerow, dui2.Section):
            if not _add_row(pagerow):
                unknown_rows = True
            continue
        entries.append(SectionHead(pagerow))
        first_row = len(entries)
        for secrow in fold_text_rows(
            section_rows(pagerow), unattached=unattached
        ):
            if isinstance(secrow, dui2.Section):
                bui.uilog.error(
                    'Doc-ui sections do not nest; ignoring one inside another.'
                )
            elif not _add_row(secrow):
                unknown_rows = True
        spans.append((pagerow, first_row, len(entries) - 1))
        # Plain rows after us stand a little apart from the group, as
        # we do from what precedes us. (Another section does that
        # itself, and the page's end needs nothing; nor does a note
        # standing alone at our end, which stands them apart itself.)
        nextrow = (
            pagerows[pageindex + 1] if pageindex + 1 < len(pagerows) else None
        )
        last = entries[-1] if len(entries) > first_row else None
        ends_in_note = isinstance(last, TextEntry) and last.upward
        stand_apart = (
            nextrow is not None
            and not isinstance(nextrow, dui2.Section)
            and not ends_in_note
        )
        entries.append(
            SectionFoot(
                pagerow,
                space_below=_SECTION_END_STANDOFF if stand_apart else 0.0,
            )
        )
    if unknown_rows:
        bui.uilog.error('Got unknown row type(s) in doc-ui; ignoring.')
    if unattached and description not in _g_warned_unattached:
        _g_warned_unattached.add(description)
        bui.uilog.warning(
            'Doc-ui page %s: text/band rows asked to attach but stand'
            ' alone instead (attach only works in drawing order: header,'
            ' title, subtitle, row, footnote, footer; set attach=False'
            ' for ones meant to stand alone): %s.',
            description,
            '; '.join(unattached),
        )
    if all(isinstance(entry, MARKER_ENTRY_TYPES) for entry in entries):
        if description not in _g_warned_unselectable:
            _g_warned_unselectable.add(description)
            bui.uilog.warning(
                'Doc-ui page %s has nothing selectable on it; adding an'
                ' Ok button so selection has somewhere to go. Pages'
                ' should provide one of their own.',
                description,
            )
        entries.append(_ok_row())
    return entries, spans


def _edge_spacing(
    entry: LayoutEntry, spacing: RowSpacing
) -> tuple[float, float]:
    """The room a (non-section) entry wants (above, below) it.

    Its kind's, unless its top edge is a title or subtitle (or its
    bottom edge a footnote); see :class:`bacommon.docui.v2.Spacing`.
    A standalone band wants none: its neighbors' room decides.
    """
    if isinstance(entry, TextEntry) and entry.band:
        return 0.0, 0.0
    row = entry.row if isinstance(entry, TextEntry) else entry
    assert not isinstance(row, SectionHead | SectionFoot)
    base = (
        spacing.button_row
        if isinstance(row, dui2.ButtonRow)
        else spacing.control_row
    )
    if row.title is not None:
        above = spacing.title
    elif row.subtitle is not None:
        above = spacing.subtitle
    elif row.footnote is not None and isinstance(entry, TextEntry):
        above = spacing.footnote
    else:
        above = base
    if row.footnote is not None:
        below = spacing.footnote
    elif isinstance(entry, TextEntry):
        below = above
    else:
        below = base
    return above, below


def entry_gaps(entries: list[LayoutEntry], spacing: RowSpacing) -> list[float]:
    """The space above each layout entry.

    Between two rows (or standalone texts) the larger of the room each
    wants on that side (see :func:`_edge_spacing`); between a section
    and a neighbor, the larger of the page's section spacing and what
    the neighbor wants (just the section spacing between two
    sections). Below an attached heading, its own small gap. Nothing
    above the first entry, nor inside a section's ends: its first entry
    sits right under its start (just a card's padding above), and its
    end right under its last. So a card's rect -- padding to padding --
    holds nothing but what's in it.

    :meta private:
    """
    gaps: list[float] = []
    for i, entry in enumerate(entries):
        prev = entries[i - 1] if i > 0 else None
        if (
            prev is None
            or isinstance(prev, SectionHead)
            or isinstance(entry, SectionFoot)
        ):
            gaps.append(0.0)
        elif isinstance(entry, SectionHead) or isinstance(prev, SectionFoot):
            # (One side is a section; the other may be too.)
            other = prev if isinstance(entry, SectionHead) else entry
            if isinstance(other, SectionHead | SectionFoot):
                gaps.append(spacing.section)
            else:
                side = 1 if other is prev else 0
                gaps.append(
                    max(spacing.section, _edge_spacing(other, spacing)[side])
                )
        elif isinstance(prev, TextEntry) and prev.hug:
            gaps.append(HEADING_GAP)
        else:
            gaps.append(
                max(
                    _edge_spacing(prev, spacing)[1],
                    _edge_spacing(entry, spacing)[0],
                )
            )
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
    backing: dui2.SectionBacking,
    column: tuple[float, float],
    page_inset: float,
) -> tuple[float, float]:
    """A card's left and right x: its max width at most, centered.

    ``column`` is the column's left and right x, which the card keeps
    its margin in from (``page_inset``, the page's side inset, unless
    it sets its own).

    :meta private:
    """
    margin = page_inset if backing.margin is None else backing.margin
    column = (column[0] + margin, column[1] - margin)
    colwidth = max(0.0, column[1] - column[0])
    cardwidth = (
        colwidth
        if backing.max_width is None
        else min(colwidth, backing.max_width)
    )
    center = (column[0] + column[1]) * 0.5
    return center - cardwidth * 0.5, center + cardwidth * 0.5


def section_backing_bounds(
    rows: list[RowPrep],
    first_row: int,
    last_row: int,
) -> tuple[float, float]:
    """The (top, bottom) y of a prepped card's rect.

    From its start's top to its end's bottom: its first entry's top
    and last entry's bottom, with its paddings outside those. ``rows``
    are the page's row preps, indexed like its layout entries (the
    section's start is the one before ``first_row``, its end the one
    after ``last_row``).

    :meta private:
    """
    return rows[first_row - 1].bounds_top, rows[last_row + 1].bounds_bottom


def prep_section_backings(
    spans: list[tuple[dui2.Section, int, int]],
    rows: list[RowPrep],
    *,
    column: tuple[float, float],
    page_inset: float,
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
        left, right = card_edges(backing, column, page_inset)
        top, bottom = section_backing_bounds(rows, first_row, last_row)
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


def prep_section_debug(
    spans: list[tuple[dui2.Section, int, int]],
    entries: list[LayoutEntry],
    rows: list[RowPrep],
    geoms: list[EntryGeom],
    *,
    width: float,
) -> None:
    """Prep debug rects for sections that ask for them.

    Once every row is prepped. Each section shows its own extent and
    its heading's and note's within it. The spacing around a section
    and any room left below it to stand what follows apart are left
    out, so a section's rects depend only on that section.

    :meta private:
    """
    # pylint: disable=cyclic-import
    from bauiv1lib.docui.prep._calls2 import prep_section_debug_rects

    for sec, first_row, last_row in spans:
        if not wants_debug_draw(sec.debug, DebugDrawKind.SECTIONS):
            continue
        start = rows[first_row - 1]
        end = rows[last_row + 1]
        assert isinstance(entries[first_row - 1], SectionHead)
        assert isinstance(entries[last_row + 1], SectionFoot)

        # Its heading: its start (a card's padding) down through the
        # text and bands leading its rows; its note: from those ending
        # them down through its end.
        def _lead(index: int) -> bool:
            entry = entries[index]
            return isinstance(entry, TextEntry) and not entry.upward

        def _tail(index: int) -> bool:
            entry = entries[index]
            return isinstance(entry, TextEntry) and entry.upward

        lead = first_row
        while lead <= last_row and _lead(lead):
            lead += 1
        tail = last_row
        while tail >= lead and _tail(tail):
            tail -= 1
        head_bottom = (
            rows[lead - 1].bounds_bottom
            if lead > first_row
            else start.bounds_bottom
        )
        foot_top = (
            rows[tail + 1].bounds_top if tail < last_row else end.bounds_top
        )
        geom = geoms[first_row - 1]
        prep_section_debug_rects(
            sec,
            x=(geom.cmargin_left, width - geom.cmargin_right),
            top=start.bounds_top,
            bottom=end.bounds_bottom,
            head=(start.bounds_top, head_bottom),
            foot=(foot_top, end.bounds_bottom),
            out_head=start.decorations,
            out_foot=end.decorations,
        )


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

    #: Where content sits in from the column's edges (the page's side
    #: inset).
    inset: float


def column_geometry(
    left: float,
    right: float,
    *,
    width: float,
    clip: tuple[float, float] | None,
    inset: float,
) -> EntryGeom:
    """Geometry for laying out in a column from ``left`` to ``right``.

    Symmetric: text, control rows' contents and button rows' outermost
    buttons sit ``inset`` in from either edge (the page's horizontal
    inset; see :attr:`bacommon.docui.v2.Page.h_inset`), and centered things
    center on the column. The column's margins are what remains of
    ``width`` outside it.

    :meta private:
    """
    center = (left + right) * 0.5
    return EntryGeom(
        cmargin_left=left,
        cmargin_right=width - right,
        # Control rows' labels start where text does; their controls end
        # at its mirror.
        control_left=left + inset,
        control_right=right - inset,
        band_anchors_x=(left + inset, center, right - inset),
        clip=clip,
        center=(center, max(1.0, right - left - 2.0 * inset)),
        inset=inset,
    )


def entry_geometry(
    entries: list[LayoutEntry],
    spans: list[tuple[dui2.Section, int, int]],
    *,
    base: EntryGeom,
    width: float,
    column: tuple[float, float],
) -> list[EntryGeom]:
    """Each layout entry's horizontal geometry (see :class:`EntryGeom`).

    ``base`` is the page-wide geometry and ``column`` the column's left
    and right x. A card's entries (heading, rows, note) get the card's
    own column -- its contents ``content_inset`` in from its edges, as
    the page's are its side inset in from its column -- and clip button
    rows at its edges; the rest get ``base``.

    :meta private:
    """
    geoms = [base] * len(entries)
    for sec, first_row, last_row in spans:
        if sec.backing is None:
            continue
        clip_l, clip_r = card_edges(sec.backing, column, base.inset)
        inset = sec.backing.content_inset
        geom = column_geometry(
            clip_l + inset - base.inset,
            clip_r - inset + base.inset,
            width=width,
            clip=(clip_l, clip_r),
            inset=base.inset,
        )
        # The heading before the rows and any note after them too.
        last = last_row + 1
        if last < len(entries) and isinstance(entries[last], SectionFoot):
            last += 1
        for index in range(first_row - 1, last):
            geoms[index] = geom
    return geoms


def section_head_height(head: SectionHead, *, first: bool) -> float:
    """Total vertical space a section's start takes.

    Its standoff, the section's top spacing and a card's top padding;
    everything but the spacing above it. ``first`` is whether it is
    the first thing on the page (no standoff then).

    :meta private:
    """
    sec = head.section
    return (
        (0.0 if first else _SECTION_BEGIN_STANDOFF_ABOVE)
        + sec.spacing_top
        + padding_top(sec)
    )


def section_foot_height(foot: SectionFoot) -> float:
    """Total vertical space a section's end takes.

    A card's bottom padding, ``space_below`` and the section's bottom
    spacing.

    :meta private:
    """
    sec = foot.section
    return padding_bottom(sec) + foot.space_below + sec.spacing_bottom


def prep_section_head(
    head: SectionHead,
    rowprep: RowPrep,
    *,
    y: float,
    first: bool,
) -> float:
    """Prep a section's start below ``y``; return the new y.

    Top to bottom: standoff (unless ``first``), the section's top
    spacing, a card's top padding (see :func:`section_head_height`).
    Its bounds are where a card's rect starts, padding included (see
    :func:`section_backing_bounds`).

    :meta private:
    """
    sec = head.section
    if not first:
        y -= _SECTION_BEGIN_STANDOFF_ABOVE
    y -= sec.spacing_top
    rowprep.bounds_top = y
    y -= padding_top(sec)
    rowprep.bounds_bottom = y
    return y


def prep_section_foot(
    foot: SectionFoot,
    rowprep: RowPrep,
    *,
    y: float,
) -> float:
    """Prep a section's end below ``y``; return the new y.

    Top to bottom: a card's bottom padding, ``space_below``, the
    section's bottom spacing (see :func:`section_foot_height`). Its
    bounds end where a card's rect does, padding included.

    :meta private:
    """
    sec = foot.section
    rowprep.bounds_top = y
    y -= padding_bottom(sec)
    rowprep.bounds_bottom = y
    return y - foot.space_below - sec.spacing_bottom
