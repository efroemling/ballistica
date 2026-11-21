# Released under the MIT License. See LICENSE for details.
#
"""Applying a page's look values to its rows before they are laid out."""

from dataclasses import replace
from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2

from bauiv1lib.docui._layout import BUTTON_ROW_EDGE_INSET

if TYPE_CHECKING:
    from bauiv1lib.docui._pagelook import PageLook


def styled_page(page: dui2.Page, look: PageLook) -> dui2.Page:
    """A page with its look baked into its rows, for layout.

    What the look says about rows becomes plain row and button fields,
    so everything after lays out as though the page had set them on
    each row itself: button rows' default side padding follows the side
    inset (putting their outermost buttons where text starts), and
    buttons with no color of their own get the page's button color. A
    page's default button keeps none, so it takes its container's
    start-button color (the page's default-button color; see page
    instantiation), and a role color never has to fight a color written
    into the button.

    Swaps in changed copies, as word-wrapping does; the page itself may
    be cached and shared. Returns ``page`` itself if nothing changes.
    """
    rows = _styled_rows(page.rows, look)
    return page if rows is page.rows else replace(page, rows=rows)


def _styled_rows(rows: list[dui2.Row], look: PageLook) -> list[dui2.Row]:
    """Rows with the look applied; ``rows`` itself if none change."""
    out: list[dui2.Row] = []
    changed = False
    for row in rows:
        new = _styled_row(row, look)
        changed = changed or new is not row
        out.append(new)
    return out if changed else rows


def _styled_row(row: dui2.Row, look: PageLook) -> dui2.Row:
    if isinstance(row, dui2.Section):
        secrows = _styled_rows(row.rows, look)
        return row if secrows is row.rows else replace(row, rows=secrows)
    if isinstance(row, dui2.ButtonRow):
        return _styled_button_row(row, look)
    if isinstance(row, dui2.ButtonControlRow):
        button = _styled_button(row.button, look)
        return row if button is row.button else replace(row, button=button)
    return row


def _styled_button_row(row: dui2.ButtonRow, look: PageLook) -> dui2.ButtonRow:
    buttons = [_styled_button(b, look) for b in row.buttons]
    if all(new is old for new, old in zip(buttons, row.buttons)):
        buttons = row.buttons
    # Side padding the row leaves to its layout's default, set to ours
    # where that differs (so the default inset copies nothing).
    side = _default_side_padding(row.layout, look.h_inset)
    pad_left = row.padding_left
    pad_right = row.padding_right
    if side is not None:
        default_left, default_right, _top, _bottom = row.get_padding()
        if pad_left is None and side != default_left:
            pad_left = side
        if pad_right is None and side != default_right:
            pad_right = side
    if (
        buttons is row.buttons
        and pad_left == row.padding_left
        and pad_right == row.padding_right
    ):
        return row
    return replace(
        row, buttons=buttons, padding_left=pad_left, padding_right=pad_right
    )


def _default_side_padding(
    layout: dui2.ButtonRowLayout, h_inset: float
) -> float | None:
    """A button row's default side padding for a horizontal inset.

    None where the layout's own default doesn't depend on it.
    """
    match layout:
        case dui2.ButtonRowLayout.SCROLL | dui2.ButtonRowLayout.FIXED:
            # Their padding starts BUTTON_ROW_EDGE_INSET in (inside the
            # h-scroll); the default takes their buttons on to the
            # inset. (With the default inset that's the wire's own
            # default, 15.)
            return h_inset - BUTTON_ROW_EDGE_INSET
        case dui2.ButtonRowLayout.FILL | dui2.ButtonRowLayout.GRID:
            # (These lay out from where control rows' contents start,
            # which already follows the inset.)
            return None
        case _:
            assert_never(layout)


def _styled_button(button: dui2.Button, look: PageLook) -> dui2.Button:
    if button.color is not None or button.default:
        return button
    if look.button_color is None:
        return button
    return replace(button, color=(*look.button_color, 1.0))
