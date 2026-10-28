# Released under the MIT License. See LICENSE for details.
#
"""Headings in doc-ui prep: ``HEADING``-size title rows.

A :class:`~bacommon.docui.v2.TitleRow` of size ``HEADING`` (with any
header band before it and subtitle after it) never becomes a row's
own title; it is a :class:`~bauiv1lib.docui.prep._textrows.TextEntry`
drawn here, a bit larger than a row's titles so it reads as heading a
group rather than labeling one row. A section's own heading fields
become one of these (see :func:`~bauiv1lib.docui.prep._sections.section_rows`).
"""

from functools import partial
from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
import bauiv1 as bui

from bauiv1lib.docui.prep._rowbands import prep_row_header, row_header_height
from bauiv1lib.docui.prep._rowtext import (
    line_count,
    row_text_x_and_maxwidth,
)
from bauiv1lib.docui.prep._types import NO_WRAP

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    from bauiv1lib.docui.prep._textrows import TextEntry
    from bauiv1lib.docui.prep._types import NativeLangStrFn, RowPrep

#: Heading title text scale: larger than a row title's (1.15), so a
#: heading reads as a level above the rows' own titles.
HEADING_TITLE_SCALE = 1.35

#: Heading subtitle text scale (a row subtitle's).
_HEADING_SUBTITLE_SCALE = 0.7

#: Row-title flatness/shadow, which headings share.
_HEADING_TITLE_FLATNESS = 0.5
_HEADING_TITLE_SHADOW = 1.0

#: Vertical space a heading title takes per line (the text sits
#: centered in each line's strip).
_HEADING_TITLE_LINE_HEIGHT = 30.0 * HEADING_TITLE_SCALE

#: The same for a subtitle, plus spare room below its last line.
_HEADING_SUBTITLE_LINE_HEIGHT = 22.0
_HEADING_SUBTITLE_PADDING_BOTTOM = 8.0

#: Space between an attached heading and the entry it heads: close, so
#: the heading reads as belonging to what follows. (The 1.8.5 layout:
#: a 2 standoff plus 10 of row spacing.)
HEADING_GAP = 12.0


def _title_height(row: dui2.ButtonRow, native: NativeLangStrFn) -> float:
    if row.title is None:
        return 0.0
    return _HEADING_TITLE_LINE_HEIGHT * line_count(row.title, native)


def _subtitle_height(row: dui2.ButtonRow, native: NativeLangStrFn) -> float:
    if row.subtitle is None:
        return 0.0
    return (
        _HEADING_SUBTITLE_LINE_HEIGHT * line_count(row.subtitle, native)
        + _HEADING_SUBTITLE_PADDING_BOTTOM
    )


def _between(row: dui2.ButtonRow) -> float:
    """The extra space between title and subtitle (with both)."""
    if row.title is None or row.subtitle is None:
        return 0.0
    return row.spacing_subtitle


def heading_entry_height(entry: TextEntry, native: NativeLangStrFn) -> float:
    """Total vertical space a heading takes (its spacing included).

    :meta private:
    """
    row = entry.row
    return (
        row.spacing_top
        + row_header_height(row)
        + _title_height(row, native)
        + _between(row)
        + _subtitle_height(row, native)
        + row.spacing_bottom
    )


def prep_heading_entry(
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
    """Prep a heading below ``y``; return the new y.

    Top to bottom: header band, title, subtitle. Sets the rowprep's
    bounds (without its spacing).

    :meta private:
    """
    row = entry.row
    y -= row.spacing_top
    rowprep.bounds_top = y
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
                text=native(row.title, wrap=NO_WRAP),
                # Row-title coloring (brighter than labels), larger.
                color=(
                    (0.95, 1.0, 0.97, 1.0)
                    if row.title_color is None
                    else row.title_color
                ),
                flatness=(
                    _HEADING_TITLE_FLATNESS
                    if row.title_flatness is None
                    else row.title_flatness
                ),
                shadow=(
                    _HEADING_TITLE_SHADOW
                    if row.title_shadow is None
                    else row.title_shadow
                ),
                scale=HEADING_TITLE_SCALE,
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
    y -= _between(row)
    if row.subtitle is not None:
        height = _subtitle_height(row, native)
        text_height = height - _HEADING_SUBTITLE_PADDING_BOTTOM
        rowprep.titlecalls.append(
            partial(
                bui.textwidget,
                position=(text_x, y - text_height * 0.5),
                size=(0, 0),
                text=native(row.subtitle, wrap=NO_WRAP),
                color=(
                    (0.6, 0.74, 0.6)
                    if row.subtitle_color is None
                    else row.subtitle_color
                ),
                flatness=row.subtitle_flatness,
                shadow=row.subtitle_shadow,
                scale=_HEADING_SUBTITLE_SCALE,
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
    rowprep.bounds_bottom = y
    return y - row.spacing_bottom
