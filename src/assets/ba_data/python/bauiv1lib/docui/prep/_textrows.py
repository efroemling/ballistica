# Released under the MIT License. See LICENSE for details.
#
"""Standalone text and band rows in doc-ui prep.

A :class:`~bacommon.docui.v2.TextRow` (title, subtitle, footnote) or
:class:`~bacommon.docui.v2.BandRow` (header, footer) that attaches to
a row becomes that row's own title, subtitle, footnote, header band or
footer band here (see :func:`fold_text_rows`), so attached ones and a
row's built-in ones are one thing to everything after: identical
layout, tucks and show areas by construction. One that stands alone
becomes a :class:`TextEntry`, laid out like a row's text or band with
no row there.
"""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2

from bauiv1lib.docui.prep._rowbands import (
    prep_row_footer,
    prep_row_header,
    row_footer_height,
    row_header_height,
)
from bauiv1lib.docui.prep._rowtext import (
    prep_row_footnote,
    prep_row_titles,
    row_footnote_height,
    row_titles_height,
)

if TYPE_CHECKING:
    from typing import TypeIs

    from bacommon.assetpackage import ApverNum

    from bauiv1lib.docui.prep._controlrows import ColumnRow
    from bauiv1lib.docui.prep._types import NativeLangStrFn, RowPrep

#: What sits above a row and can attach to it, top to bottom.
type _HeadRow = dui2.HeaderRow | dui2.TitleRow | dui2.SubtitleRow

#: Everything that can attach to a row.
type _AttachRow = dui2.AnyTextRow | dui2.AnyBandRow

_ATTACH_ROW_TYPES = (
    dui2.TitleRow,
    dui2.SubtitleRow,
    dui2.FootnoteRow,
    dui2.HeaderRow,
    dui2.FooterRow,
)


def _takes_text(row: dui2.Row | TextEntry) -> TypeIs[ColumnRow]:
    """Can text and bands attach to this row (any button/control row)?"""
    if isinstance(row, TextEntry):
        return False
    return isinstance(row, dui2.ButtonRow) or dui2.is_control_row(row)


@dataclass
class TextEntry:
    """Layout entry for a text or band row standing alone.

    ``row`` is a buttonless :class:`~bacommon.docui.v2.ButtonRow`
    carrying it as its own title, subtitle, footnote, header band or
    footer band (so the usual row code lays it out). ``upward`` is
    whether it keeps the row before it in view rather than the one
    after (a footnote or footer); ``band`` whether it is a band (which
    wants no room of its own beside it). ``heading`` marks a heading
    (a ``HEADING``-size title, with any header band and subtitle that
    joined it; see :mod:`bauiv1lib.docui.prep._headings`), and ``hug``
    one that sits close above whatever follows it (an attached one).

    :meta private:
    """

    row: dui2.ButtonRow
    upward: bool
    band: bool
    heading: bool = False
    hug: bool = False


def text_entry_height(entry: TextEntry, native: NativeLangStrFn) -> float:
    """Total vertical space a standalone entry takes (spacing included).

    :meta private:
    """
    row = entry.row
    return (
        row.spacing_top
        + row_header_height(row)
        + row_titles_height(row, native)
        + row_footnote_height(row, native)
        + row_footer_height(row)
        + row.spacing_bottom
    )


def prep_text_entry(
    entry: TextEntry,
    rowprep: RowPrep,
    *,
    y: float,
    width: float,
    margins: tuple[float, float, float, float],
    header_insets: tuple[float, float],
    center: tuple[float, float],
    anchors_x: tuple[float, float, float],
    tdelaybase: float | None,
    tscale: float,
    native: NativeLangStrFn,
    packages: list[ApverNum],
) -> float:
    """Prep a standalone entry below ``y``; return the new y.

    Sets the rowprep's bounds (without its spacing).

    :meta private:
    """
    row = entry.row
    banddelay = None if tdelaybase is None else (tdelaybase + 0.05 * tscale)
    y -= row.spacing_top
    rowprep.bounds_top = y
    y = prep_row_header(
        row,
        rowprep,
        y=y,
        anchors_x=anchors_x,
        tdelay=banddelay,
        packages=packages,
    )
    y = prep_row_titles(
        row,
        rowprep,
        y=y,
        width=width,
        margins=margins,
        header_insets=header_insets,
        center=center,
        tdelaybase=tdelaybase,
        tscale=tscale,
        native=native,
    )
    footnote_height = row_footnote_height(row, native)
    y -= footnote_height
    prep_row_footnote(
        row,
        rowprep,
        y=y,
        width=width,
        margins=margins,
        header_insets=header_insets,
        center=center,
        tdelaybase=tdelaybase,
        tscale=tscale,
        native=native,
    )
    y = prep_row_footer(
        row,
        rowprep,
        y=y,
        anchors_x=anchors_x,
        tdelay=banddelay,
        packages=packages,
    )
    rowprep.bounds_bottom = y
    return y - row.spacing_bottom


def _standalone(item: _AttachRow) -> TextEntry:
    """The layout entry for a text or band row that doesn't attach."""
    base = dui2.ButtonRow(
        buttons=[],
        spacing_top=item.spacing_top,
        spacing_bottom=item.spacing_bottom,
        debug=item.debug,
    )
    if isinstance(item, dui2.HeaderRow):
        return TextEntry(
            replace(
                base,
                header_height=item.height,
                header_scale=item.scale,
                header_decorations_left=item.decorations_left,
                header_decorations_center=item.decorations_center,
                header_decorations_right=item.decorations_right,
            ),
            upward=False,
            band=True,
        )
    if isinstance(item, dui2.FooterRow):
        return TextEntry(
            replace(
                base,
                footer_height=item.height,
                footer_scale=item.scale,
                footer_decorations_left=item.decorations_left,
                footer_decorations_center=item.decorations_center,
                footer_decorations_right=item.decorations_right,
            ),
            upward=True,
            band=True,
        )
    base = replace(base, title_align=item.align)
    if isinstance(item, dui2.TitleRow):
        return TextEntry(
            replace(
                base,
                title=item.text,
                title_color=item.color,
                title_flatness=item.flatness,
                title_shadow=item.shadow,
                title_wrap=item.wrap,
            ),
            upward=False,
            band=False,
        )
    if isinstance(item, dui2.SubtitleRow):
        return TextEntry(
            replace(
                base,
                subtitle=item.text,
                subtitle_color=item.color,
                subtitle_flatness=item.flatness,
                subtitle_shadow=item.shadow,
                subtitle_wrap=item.wrap,
            ),
            upward=False,
            band=False,
        )
    return TextEntry(
        replace(
            base,
            footnote=item.text,
            footnote_color=item.color,
            footnote_flatness=item.flatness,
            footnote_shadow=item.shadow,
            footnote_wrap=item.wrap,
        ),
        upward=True,
        band=False,
    )


def _heading(
    header: dui2.HeaderRow | None,
    title: dui2.TitleRow,
    subtitle: dui2.SubtitleRow | None,
) -> TextEntry:
    """The layout entry for a heading and what joined it.

    Their spacing works as for texts attached to one row: the first's
    ``spacing_top`` above it all, the last's ``spacing_bottom`` below,
    and those facing each other between title and subtitle (a header
    band's ``spacing_bottom``, facing the title, doesn't apply).
    """
    first: _HeadRow = title if header is None else header
    last = title if subtitle is None else subtitle
    texts: list[dui2.TitleRow | dui2.SubtitleRow] = [title]
    if subtitle is not None:
        texts.append(subtitle)
    row = dui2.ButtonRow(
        buttons=[],
        spacing_top=first.spacing_top,
        spacing_bottom=last.spacing_bottom,
        debug=any(t.debug for t in [first, *texts]),
        title_align=next((t.align for t in texts if t.align is not None), None),
        title=title.text,
        title_color=title.color,
        title_flatness=title.flatness,
        title_shadow=title.shadow,
        title_wrap=title.wrap,
    )
    if subtitle is not None:
        row = replace(
            row,
            subtitle=subtitle.text,
            subtitle_color=subtitle.color,
            subtitle_flatness=subtitle.flatness,
            subtitle_shadow=subtitle.shadow,
            subtitle_wrap=subtitle.wrap,
            spacing_subtitle=title.spacing_bottom + subtitle.spacing_top,
        )
    if header is not None:
        row = replace(
            row,
            header_height=header.height,
            header_scale=header.scale,
            header_decorations_left=header.decorations_left,
            header_decorations_center=header.decorations_center,
            header_decorations_right=header.decorations_right,
        )
    return TextEntry(
        row, upward=False, band=False, heading=True, hug=title.attach
    )


def _with_head(row: ColumnRow, head: list[_HeadRow]) -> ColumnRow | None:
    """A row with an attached header, title and/or subtitle as its own.

    ``head`` is some of a header, a title and a subtitle, in that
    order. None if the row already has one of those of its own.
    """
    header = head[0] if isinstance(head[0], dui2.HeaderRow) else None
    texts = [t for t in head if not isinstance(t, dui2.HeaderRow)]
    title = next((t for t in texts if isinstance(t, dui2.TitleRow)), None)
    subtitle = next((t for t in texts if isinstance(t, dui2.SubtitleRow)), None)
    if (header is not None and row.header_height != 0.0) or (
        texts and (row.title is not None or row.subtitle is not None)
    ):
        return None
    kwargs: dict = {
        # (Above the whole row: the first one's.)
        'spacing_top': row.spacing_top + head[0].spacing_top,
        'debug': row.debug or any(t.debug for t in head),
    }
    if header is not None:
        # (Its spacing_bottom, facing the row, doesn't apply.)
        kwargs.update(
            header_height=header.height,
            header_scale=header.scale,
            header_decorations_left=header.decorations_left,
            header_decorations_center=header.decorations_center,
            header_decorations_right=header.decorations_right,
        )
    if texts:
        # (Between the last text and the row's content.)
        kwargs['spacing_title'] = row.spacing_title + texts[-1].spacing_bottom
        align = next((t.align for t in texts if t.align is not None), None)
        if align is not None:
            kwargs['title_align'] = align
    if title is not None:
        kwargs.update(
            title=title.text,
            title_color=title.color,
            title_flatness=title.flatness,
            title_shadow=title.shadow,
            title_wrap=title.wrap,
        )
    if subtitle is not None:
        kwargs.update(
            subtitle=subtitle.text,
            subtitle_color=subtitle.color,
            subtitle_flatness=subtitle.flatness,
            subtitle_shadow=subtitle.shadow,
            subtitle_wrap=subtitle.wrap,
        )
    if title is not None and subtitle is not None:
        kwargs['spacing_subtitle'] = (
            row.spacing_subtitle + title.spacing_bottom + subtitle.spacing_top
        )
    return replace(row, **kwargs)


def _with_footnote(row: ColumnRow, foot: dui2.FootnoteRow) -> ColumnRow | None:
    """A row with an attached footnote as its own (None if it has one)."""
    if row.footnote is not None:
        return None
    kwargs: dict = {
        'footnote': foot.text,
        'footnote_color': foot.color,
        'footnote_flatness': foot.flatness,
        'footnote_shadow': foot.shadow,
        'footnote_wrap': foot.wrap,
        'spacing_footnote': row.spacing_footnote + foot.spacing_top,
        'spacing_bottom': row.spacing_bottom + foot.spacing_bottom,
        'debug': row.debug or foot.debug,
    }
    if foot.align is not None and row.title_align is None:
        kwargs['title_align'] = foot.align
    return replace(row, **kwargs)


def _with_footer(row: ColumnRow, foot: dui2.FooterRow) -> ColumnRow | None:
    """A row with an attached footer band as its own (None if it has
    one)."""
    if row.footer_height != 0.0:
        return None
    # (Its spacing_top, facing the row, doesn't apply.)
    return replace(
        row,
        footer_height=foot.height,
        footer_scale=foot.scale,
        footer_decorations_left=foot.decorations_left,
        footer_decorations_center=foot.decorations_center,
        footer_decorations_right=foot.decorations_right,
        spacing_bottom=row.spacing_bottom + foot.spacing_bottom,
        debug=row.debug or foot.debug,
    )


def _continues_head(head: list[_HeadRow], item: _HeadRow) -> bool:
    """Can ``item`` join the waiting head (keeping header, title,
    subtitle order, one of each)?"""
    order = (dui2.HeaderRow, dui2.TitleRow, dui2.SubtitleRow)
    if not head:
        return True
    last = next(i for i, t in enumerate(order) if isinstance(head[-1], t))
    mine = next(i for i, t in enumerate(order) if isinstance(item, t))
    return mine > last


def _take_heading(
    title: dui2.TitleRow,
    rows: list[dui2.Row],
    index: int,
    head: list[_HeadRow],
) -> tuple[TextEntry, int]:
    """The entry for a heading title, and the index of what follows it.

    ``index`` is just past the title. A heading never becomes a row's
    own title. Attached, a lone header band waiting in ``head`` joins
    it (and leaves ``head``), as does a subtitle right after.
    """
    header: dui2.HeaderRow | None = None
    subtitle: dui2.SubtitleRow | None = None
    if title.attach:
        if len(head) == 1 and isinstance(head[0], dui2.HeaderRow):
            header = head[0]
            head.clear()
        nextrow = rows[index] if index < len(rows) else None
        if isinstance(nextrow, dui2.SubtitleRow) and nextrow.attach:
            subtitle = nextrow
            index += 1
    return _heading(header, title, subtitle), index


def _fold_below(
    out: list[dui2.Row | TextEntry],
    item: dui2.FootnoteRow | dui2.FooterRow,
    footered: set[int],
) -> bool:
    """Attach a footnote or footer to the last row in ``out``, if we can.

    ``footered`` holds the indices of rows that took a footer (a
    footnote can't follow one). Returns whether it attached.
    """
    prev = out[-1] if out else None
    if prev is None or not _takes_text(prev):
        return False
    folded: ColumnRow | None = None
    if isinstance(item, dui2.FooterRow):
        folded = _with_footer(prev, item)
        if folded is not None:
            footered.add(len(out) - 1)
    elif len(out) - 1 not in footered:
        folded = _with_footnote(prev, item)
    if folded is None:
        return False
    out[-1] = folded
    return True


def fold_text_rows(
    rows: list[dui2.Row], *, unattached: list[str]
) -> list[dui2.Row | TextEntry]:
    """A row list with its text and band rows attached or standing alone.

    An attaching header, title and/or subtitle (in that order) directly
    before a row becomes that row's own, and an attaching footnote
    and/or footer (in that order) directly after one likewise; every
    other text or band row becomes a :class:`TextEntry`, exactly as if
    it didn't attach. A ``HEADING``-size title never attaches as a
    row's title: it becomes a heading entry, taking an attached header
    band just before it and subtitle just after. One that asked to
    attach but couldn't (out of
    order, nothing there to attach to, or the row already has its own)
    gets a line in ``unattached`` saying so. Other rows pass through
    (sections included; their own rows get folded separately).

    :meta private:
    """
    out: list[dui2.Row | TextEntry] = []
    # What's waiting above for a row to attach to.
    head: list[_HeadRow] = []
    # (Rows that took an attached footer: a footnote can't follow.)
    footered: set[int] = set()

    def _alone(item: _AttachRow) -> None:
        side = (
            'before'
            if isinstance(item, dui2.FootnoteRow | dui2.FooterRow)
            else 'after'
        )
        unattached.append(
            f'{type(item).__name__} (entry {len(out)}) has no row {side}'
            ' it can attach to'
        )
        out.append(_standalone(item))

    def _flush() -> None:
        for item in head:
            _alone(item)
        head.clear()

    index = 0
    while index < len(rows):
        row = rows[index]
        index += 1
        if (
            isinstance(row, dui2.TitleRow)
            and row.size is dui2.TitleSize.HEADING
        ):
            entry, index = _take_heading(row, rows, index, head)
            _flush()
            out.append(entry)
        elif isinstance(row, _ATTACH_ROW_TYPES) and not row.attach:
            _flush()
            out.append(_standalone(row))
        elif isinstance(row, dui2.HeaderRow | dui2.TitleRow | dui2.SubtitleRow):
            if not _continues_head(head, row):
                _flush()
            head.append(row)
        elif isinstance(row, dui2.FootnoteRow | dui2.FooterRow):
            _flush()
            if not _fold_below(out, row, footered):
                _alone(row)
        elif _takes_text(row):
            folded = _with_head(row, head) if head else None
            if folded is None:
                _flush()
                out.append(row)
            else:
                head.clear()
                out.append(folded)
        else:
            _flush()
            out.append(row)
    _flush()
    return out
