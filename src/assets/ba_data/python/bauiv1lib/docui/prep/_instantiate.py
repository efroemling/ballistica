# Released under the MIT License. See LICENSE for details.
#
"""Turning a prepped doc-ui page into actual widgets."""

from typing import TYPE_CHECKING

import bauiv1 as bui

from bauiv1lib.docui.prep._button import instantiate_button
from bauiv1lib.docui.prep._decorations import instantiate_decorations
from bauiv1lib.docui.prep._controlrows import instantiate_control_row
from bauiv1lib.docui.prep._showareas import (
    grid_line_part,
    widget_show_buffers,
)

if TYPE_CHECKING:
    from bauiv1lib.docui.prep._types import PagePrep, RowPrep
    from bauiv1lib.docui._host import DocUIPageHost


def _instantiate_row_bands(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIPageHost
) -> None:
    """Create a (non-section) row's header/footer band decorations.

    A band's art may reach behind its own row's widgets (a backdrop
    around a button, say), so it draws behind everything else on the
    page. The page's children share one depth slice, where overlaps
    resolve by depth rather than draw order: without this, art laid
    under a button tints its body. (Section backings draw behind as
    well; equal-depth ties go by draw order, and those come first.)
    """
    instantiate_decorations(
        rowprep.decorations,
        parent=parent,
        anim_targets=window.anim_targets,
        draw_behind=True,
    )


def _instantiate_button_row(
    rowprep: RowPrep, *, parent: bui.Widget, window: DocUIPageHost
) -> tuple[bui.Widget, list[bui.Widget]]:
    """Create the widgets for a prepped row of buttons.

    Returns the row's horizontal scroll widget and its buttons, left
    to right.
    """
    _instantiate_row_bands(rowprep, parent=parent, window=window)
    assert rowprep.hscrollcall is not None
    hscroll = rowprep.hscrollcall(parent=parent)
    buttons: list[bui.Widget] = []
    assert rowprep.hsubcall is not None
    hsub = rowprep.hsubcall(parent=hscroll)
    for i, buttonprep in enumerate(rowprep.buttons):
        btn = instantiate_button(buttonprep, parent=hsub, window=window)

        # Make sure row is scrolled so leftmost button is
        # visible (though it kinda seems like this should happen
        # by default).
        if i == 0:
            bui.containerwidget(edit=hsub, visible_child=btn)
        buttons.append(btn)

    # Navigating into the row lands on its entry button (the row
    # remembers its selection after that, as containers do).
    if rowprep.entry_index:
        bui.containerwidget(
            edit=hsub, selected_child=buttons[rowprep.entry_index]
        )

    assert rowprep.hscrolleditcall is not None
    rowprep.hscrolleditcall(edit=hscroll)
    _add_show_areas(rowprep, 0, [hscroll], parent=parent)
    return hscroll, buttons


def _add_show_areas(
    rowprep: RowPrep,
    line: int,
    widgets: list[bui.Widget],
    *,
    parent: bui.Widget,
) -> None:
    """Add a row's (or grid line's) selected-only show-area rects.

    One per widget that can be selected, each showing only while its
    widget is (see :mod:`bauiv1lib.docui.prep._showareas`).
    """
    if not rowprep.show_area_calls:
        return
    for call in rowprep.show_area_calls[line]:
        for widget in widgets:
            call(parent=parent, selected_widget=widget)


def _add_grid_lines(
    rowprep: RowPrep,
    buttons: list[bui.Widget],
    *,
    out: list[tuple[bui.Widget, list[bui.Widget]]],
    grids: list[list[list[bui.Widget]]],
    parent: bui.Widget,
) -> None:
    """Add a grid row's buttons to navigation, a line at a time."""
    columns = rowprep.grid_columns
    lines = [buttons[i : i + columns] for i in range(0, len(buttons), columns)]
    assert len(lines) == len(rowprep.grid_show_buffers)
    assert len(rowprep.control_spans) == len(buttons)
    for index, (line, buffers) in enumerate(
        zip(lines, rowprep.grid_show_buffers, strict=True)
    ):
        _add_show_areas(rowprep, index, line, parent=parent)
        part = grid_line_part(rowprep, index)
        for col, button in enumerate(line):
            # (Each button's own, as it may be smaller than its cell.)
            top, bottom = widget_show_buffers(
                part, rowprep.control_spans[index * columns + col], buffers
            )
            bui.widget(
                edit=button, show_buffer_top=top, show_buffer_bottom=bottom
            )
        # Right from a line's end goes nowhere (as for control rows;
        # see below), rather than hunting for some other row's widget.
        bui.widget(edit=line[-1], right_widget=line[-1])
        # (Entering the line lands on the grid's entry button if it's
        # in this line.)
        entry = rowprep.entry_index - index * columns
        out.append((line[entry] if 0 <= entry < len(line) else line[0], line))
    grids.append(lines)


def _wire_grid_columns(lines: list[list[bui.Widget]]) -> None:
    """Make up/down within a grid move within its columns.

    Down from above a short last line goes to its last button. (Up/down
    out of the grid's top and bottom lines stay as row navigation set
    them up.)
    """
    for upper, lower in zip(lines, lines[1:]):
        for col, button in enumerate(upper):
            bui.widget(edit=button, down_widget=lower[min(col, len(lower) - 1)])
        for col, button in enumerate(lower):
            # (Every line but the last is full.)
            bui.widget(edit=button, up_widget=upper[col])


def _instantiate_row(
    rowprep: RowPrep,
    *,
    subcontainer: bui.Widget,
    window: DocUIPageHost,
    out: list[tuple[bui.Widget, list[bui.Widget]]],
    grids: list[list[list[bui.Widget]]],
) -> None:
    """Create a prepped row's widgets, adding any navigable ones to out.

    A grid row adds each of its lines to ``out`` as a row of its own,
    and its lines (as a list of them) to ``grids``.
    """
    if rowprep.is_section:
        # Text and decorations only; nothing to navigate to (the
        # neighboring row it attached to keeps it in view). The
        # decorations come first: a card's backing is among them,
        # and must sit beneath the heading's text.
        instantiate_decorations(
            rowprep.decorations,
            parent=subcontainer,
            anim_targets=window.anim_targets,
        )
        for uicall in rowprep.titlecalls:
            uicall(parent=subcontainer)
        return
    for uicall in rowprep.titlecalls:
        uicall(parent=subcontainer)
    if rowprep.is_control_row():
        # The row's selectable widgets (usually one lone control,
        # a '-'/'+' pair for a number row) stand in for the row's
        # 'buttons' as far as navigation goes, with the first also
        # standing in for the row itself.
        _instantiate_row_bands(rowprep, parent=subcontainer, window=window)
        controls = instantiate_control_row(
            rowprep, parent=subcontainer, window=window
        )
        if rowprep.grid_columns:
            _add_grid_lines(
                rowprep, controls, out=out, grids=grids, parent=subcontainer
            )
            window.row_bounds.append(
                (controls, rowprep.bounds_top, rowprep.bounds_bottom)
            )
            return
        # (Each control's own, as it may sit inside the row's control
        # area: within its padding, say.)
        for control, span in zip(controls, rowprep.control_spans, strict=True):
            top, bottom = widget_show_buffers(
                rowprep.show_part,
                span,
                (rowprep.show_buffer_top, rowprep.show_buffer_bottom),
            )
            bui.widget(
                edit=control, show_buffer_top=top, show_buffer_bottom=bottom
            )
        # Unlike button rows, whose h-scroll swallows a right press
        # past their last button, our controls sit right in the
        # page's container, where an autoselect widget's right press
        # would go hunting for the nearest widget to its right
        # (possibly in some other row). Pointing it at itself makes
        # it a no-op instead. (Sliders consume left/right presses
        # themselves, so this never comes up for them.)
        bui.widget(edit=controls[-1], right_widget=controls[-1])
        _add_show_areas(rowprep, 0, controls, parent=subcontainer)
        # (Rows above and below aim at the row's entry button.)
        out.append((controls[rowprep.entry_index], controls))
        window.row_bounds.append(
            (controls, rowprep.bounds_top, rowprep.bounds_bottom)
        )
        return
    hscroll, buttons = _instantiate_button_row(
        rowprep, parent=subcontainer, window=window
    )
    out.append((hscroll, buttons))
    window.row_bounds.append(
        ([hscroll, *buttons], rowprep.bounds_top, rowprep.bounds_bottom)
    )


def instantiate_page_prep(
    pageprep: PagePrep,
    *,
    rootwidget: bui.Widget,
    scrollwidget: bui.Widget,
    backbutton: bui.Widget | None,
    windowbackbutton: bui.Widget | None,
    window: DocUIPageHost,
) -> bui.Widget:
    """Create a UI using prepped data."""
    outrows: list[tuple[bui.Widget, list[bui.Widget]]] = []
    grids: list[list[list[bui.Widget]]] = []

    # Now go through and run our prepped ui calls to build our
    # widgets, plugging in appropriate parent widgets args and
    # whatnot as we go.
    assert pageprep.rootcall is not None
    subcontainer = pageprep.rootcall(parent=scrollwidget)

    # On a page with nothing selectable (an empty list showing only a
    # message, say) this container itself ends up as the selection.
    # There is nothing in that worth saving or restoring.
    bui.widget(edit=subcontainer, allow_preserve_selection=False)
    for rowprep in pageprep.rows:
        _instantiate_row(
            rowprep,
            subcontainer=subcontainer,
            window=window,
            out=outrows,
            grids=grids,
        )

    for root_post_call in pageprep.root_post_calls:
        root_post_call(rootwidget)

    # Ok; we've got all widgets. Now wire up directional nav between
    # rows/buttons.

    # Up press on any top-row button should select window back button
    # (if there is one).
    if outrows and windowbackbutton is not None:
        _scroll, buttons = outrows[0]
        for button in buttons:
            bui.widget(edit=button, up_widget=windowbackbutton)
    for _scroll, buttons in outrows:
        # Left press on first button in any row should select back
        # button (either system one or window one).
        if buttons and backbutton is not None:
            bui.widget(edit=buttons[0], left_widget=backbutton)
        # Left/right presses should select neighbor button in
        # row (when there is one).
        for i in range(0, len(buttons) - 1):
            leftbutton = buttons[i]
            rightbutton = buttons[i + 1]
            bui.widget(edit=leftbutton, right_widget=rightbutton)
            bui.widget(edit=rightbutton, left_widget=leftbutton)
    # Down/up presses should select next/prev row (when there is
    # one).
    for i in range(0, len(outrows) - 1):
        topscroll, topbuttons = outrows[i]
        botscroll, botbuttons = outrows[i + 1]
        for topbutton in topbuttons:
            bui.widget(edit=topbutton, down_widget=botscroll)
        for botbutton in botbuttons:
            bui.widget(edit=botbutton, up_widget=topscroll)

    # Within a grid, up/down follow its columns (which the line-to-line
    # wiring just above, aimed at each line's first button, doesn't).
    for lines in grids:
        _wire_grid_columns(lines)

    return subcontainer
