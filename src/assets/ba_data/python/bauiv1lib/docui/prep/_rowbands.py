# Released under the MIT License. See LICENSE for details.
#
"""Prep for the decoration bands every doc-ui row can carry.

A row's header band sits above everything else in it (its title
included) and its footer band below everything (its footnote
included). Each is a strip of free-form decorations in three lists,
positioned relative to points on the band's vertical midline: left,
center and right. All row types share these, so they are laid out
here once; a :class:`~bacommon.docui.v2.Section` carries both too (its
header over its heading, its footer under its note), hence the
structural row types below.
"""

from typing import TYPE_CHECKING, Protocol

from bauiv1lib.docui.prep._calls2 import prep_decorations

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    import bacommon.docui.v2 as dui2

    from bauiv1lib.docui.prep._types import RowPrep


class HeaderBandRow(Protocol):
    """Whatever carries a header band: every row and a section-begin.

    :meta private:
    """

    header_height: float
    header_scale: float
    header_decorations_left: list[dui2.Decoration] | None
    header_decorations_center: list[dui2.Decoration] | None
    header_decorations_right: list[dui2.Decoration] | None


class FooterBandRow(Protocol):
    """Whatever carries a footer band: every row and a section-end.

    :meta private:
    """

    footer_height: float
    footer_scale: float
    footer_decorations_left: list[dui2.Decoration] | None
    footer_decorations_center: list[dui2.Decoration] | None
    footer_decorations_right: list[dui2.Decoration] | None


def row_header_height(row: HeaderBandRow) -> float:
    """Vertical space a row's header band takes (0 for none).

    :meta private:
    """
    return row.header_height * row.header_scale


def row_footer_height(row: FooterBandRow) -> float:
    """Vertical space a row's footer band takes (0 for none).

    :meta private:
    """
    return row.footer_height * row.footer_scale


def prep_row_header(
    row: HeaderBandRow,
    rowprep: RowPrep,
    *,
    y: float,
    anchors_x: tuple[float, float, float],
    tdelay: float | None,
    packages: list[ApverNum],
) -> float:
    """Prep a row's header band in the strip below ``y``; return the new y.

    ``anchors_x`` are the left, center and right x positions its
    decoration lists are placed relative to.

    :meta private:
    """
    height = row_header_height(row)
    y -= height
    _prep_band(
        (
            row.header_decorations_left,
            row.header_decorations_center,
            row.header_decorations_right,
        ),
        center_y=y + height * 0.5,
        scale=row.header_scale,
        anchors_x=anchors_x,
        tdelay=tdelay,
        packages=packages,
        rowprep=rowprep,
    )
    return y


def prep_row_footer(
    row: FooterBandRow,
    rowprep: RowPrep,
    *,
    y: float,
    anchors_x: tuple[float, float, float],
    tdelay: float | None,
    packages: list[ApverNum],
) -> float:
    """Prep a row's footer band in the strip below ``y``; return the new y.

    The mirror image of :func:`prep_row_header`.

    :meta private:
    """
    height = row_footer_height(row)
    y -= height
    _prep_band(
        (
            row.footer_decorations_left,
            row.footer_decorations_center,
            row.footer_decorations_right,
        ),
        center_y=y + height * 0.5,
        scale=row.footer_scale,
        anchors_x=anchors_x,
        tdelay=tdelay,
        packages=packages,
        rowprep=rowprep,
    )
    return y


def _prep_band(
    decoration_lists: tuple[
        list[dui2.Decoration] | None,
        list[dui2.Decoration] | None,
        list[dui2.Decoration] | None,
    ],
    *,
    center_y: float,
    scale: float,
    anchors_x: tuple[float, float, float],
    tdelay: float | None,
    packages: list[ApverNum],
    rowprep: RowPrep,
) -> None:
    for decorations, anchor_x in zip(decoration_lists, anchors_x, strict=True):
        if not decorations:
            continue
        prep_decorations(
            decorations,
            anchor_x,
            center_y,
            scale,
            tdelay=tdelay,
            packages=packages,
            highlight=False,
            out_decoration_preps=rowprep.decorations,
        )
