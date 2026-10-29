# Released under the MIT License. See LICENSE for details.
#
"""Debug boxes for the parts of a doc-ui row.

A row's own debug box covers all of it: header band to footer band,
its bands, titles and footnote included (whether given inline or as
attached text and band rows). These boxes go inside it, one per band
and text strip plus one for the content between, so the pieces and
the gaps between them show.
"""

from functools import partial
from typing import TYPE_CHECKING

import bauiv1 as bui

from bauiv1lib.docui.prep._rowbands import row_footer_height, row_header_height
from bauiv1lib.docui.prep._rowtext import row_footnote_height, row_titles_height
from bauiv1lib.docui.prep._types import DecorationPrep

if TYPE_CHECKING:
    from bauiv1lib.docui.prep._controlrows import ColumnRow
    from bauiv1lib.docui.prep._types import NativeLangStrFn, RowPrep

_TITLES_COLOR = (0.0, 0.85, 0.85)
_CONTENT_COLOR = (0.75, 0.75, 0.75)
_FOOTNOTE_COLOR = (0.85, 0.3, 1.0)
_BAND_COLOR = (1.0, 0.7, 0.0)


def _box(
    x: tuple[float, float],
    top: float,
    bottom: float,
    color: tuple[float, float, float],
    info: str | None,
) -> DecorationPrep:
    return DecorationPrep(
        call=partial(
            bui.debugrectwidget,
            position=(x[0], bottom),
            size=(x[1] - x[0], top - bottom),
            color=color,
            opacity=0.7,
            edge_width=1.5,
            info=info,
            info_anchor='top_right',
        ),
        textures={},
        meshes={},
        highlight=False,
    )


def prep_row_part_debug(
    row: ColumnRow,
    rowprep: RowPrep,
    native: NativeLangStrFn,
    *,
    x: tuple[float, float],
    content: tuple[float, float] | None = None,
) -> None:
    """Prep debug boxes for a row's bands, titles, content and footnote.

    Once its bounds are set. Nothing for a row with no text or bands
    (its own box says it all). ``x`` is the boxes' left and right; ``content``
    the content's (bottom, top) if it isn't simply what's between the
    text strips (a control row's control area, which its text tucks
    in beside).

    :meta private:
    """
    titles = row_titles_height(row, native)
    footnote = row_footnote_height(row, native)
    header = row_header_height(row)
    footer = row_footer_height(row)
    if titles <= 0.0 and footnote <= 0.0 and header <= 0.0 and footer <= 0.0:
        return
    titles_top = rowprep.bounds_top - header
    footnote_bottom = rowprep.bounds_bottom + footer
    if content is None:
        content = (footnote_bottom + footnote, titles_top - titles)
    out = rowprep.decorations
    if header > 0.0:
        out.append(
            _box(
                x,
                rowprep.bounds_top,
                titles_top,
                _BAND_COLOR,
                f'header {header:.4g}',
            )
        )
    if footer > 0.0:
        out.append(
            _box(
                x,
                footnote_bottom,
                rowprep.bounds_bottom,
                _BAND_COLOR,
                f'footer {footer:.4g}',
            )
        )
    if titles > 0.0:
        label = ' + '.join(
            name
            for name, text in (('title', row.title), ('subtitle', row.subtitle))
            if text is not None
        )
        out.append(
            _box(
                x,
                titles_top,
                titles_top - titles,
                _TITLES_COLOR,
                f'{label} {titles:.4g}',
            )
        )
    out.append(_box(x, content[1], content[0], _CONTENT_COLOR, None))
    if footnote > 0.0:
        out.append(
            _box(
                x,
                footnote_bottom + footnote,
                footnote_bottom,
                _FOOTNOTE_COLOR,
                f'footnote {footnote:.4g}',
            )
        )
