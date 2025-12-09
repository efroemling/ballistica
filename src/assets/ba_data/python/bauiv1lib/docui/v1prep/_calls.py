# Released under the MIT License. See LICENSE for details.
#
"""Prep functionality for our UI.

We do all layout math and bake out partial ui calls in a background
thread so there's as little work to do in the ui thread as possible.
"""

from __future__ import annotations

import copy
from functools import partial
from typing import TYPE_CHECKING, assert_never

from efro.util import strict_partial
import bacommon.docui.v1 as dui1
import bauiv1 as bui

from bauiv1lib.docui.v1prep._types import PagePrep, RowPrep, ButtonPrep

if TYPE_CHECKING:
    from typing import Callable

    from bauiv1lib.docui import DocUIWindow


def prep_page(
    page: dui1.Page,
    *,
    uiscale: bui.UIScale,
    scroll_width: float,
    scroll_height: float,
    idprefix: str,
    immediate: bool = False,
) -> PagePrep:
    """Prep a page."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=cyclic-import

    import bauiv1lib.docui.v1prep._calls2 as prepcalls2

    # Create a filtered list of rows we know how to display.
    page_rows_filtered: list[dui1.ButtonRow] = []
    for pagerow in page.rows:
        if isinstance(pagerow, dui1.ButtonRow):
            if not pagerow.buttons:
                pagerow = copy.deepcopy(pagerow)
                pagerow.buttons.append(
                    dui1.Button(
                        label=bui.Lstr(
                            translate=(
                                'serverResponses',
                                'There is nothing here.',
                            )
                        ).as_json(),
                        label_color=(1, 1, 1, 0.3),
                        label_is_lstr=True,
                        size=(220, 100),
                        label_scale=0.6,
                        texture='buttonSquareWide',
                        padding_top=-8,
                        padding_bottom=-10,
                        color=(0.2, 0.2, 0.2, 0.15),
                        action=dui1.Local(default_sound=False),
                    )
                )
            page_rows_filtered.append(pagerow)
    if len(page_rows_filtered) != len(page.rows):
        bui.uilog.error('Got unknown row type(s) in doc-ui; ignoring.')

    # Ok; we've got some buttons. Build our full UI.
    row_title_height_with_subtitle = 30.0
    row_title_height_no_subtitle = 38.0
    row_subtitle_height = 30.0

    # Buffers for *everything*. Set bases here that look decent and
    # allow page to offset them.
    top_buffer = 20.0 + page.padding_top
    bot_buffer = 20.0 + page.padding_bottom
    left_buffer = 10.0 + page.padding_left
    # Nudge a bit due to scrollbar.
    right_buffer = 20.0 + page.padding_right

    # Extra buffers for title/headers stuff (not in h-scroll).
    header_inset_left = 45.0
    header_inset_right = 30.0

    default_button_width = 150.0
    default_button_height = 100.0

    if uiscale is bui.UIScale.SMALL:
        top_bar_overlap = 70
        bot_bar_overlap = 70
        top_buffer += top_bar_overlap
        bot_buffer += bot_bar_overlap
    else:
        top_bar_overlap = 0
        bot_bar_overlap = 0

    # Should look into why this is necessary.
    fudge = 15.0
    hscrollinset = 15.0

    rootcall: Callable[..., bui.Widget] | None = None
    rows: list[RowPrep] = []
    width: float = scroll_width + fudge
    height: float = (
        top_buffer
        + bot_buffer
        + page.row_spacing * max(0, (len(page_rows_filtered) - 1))
    )
    simple_culling_v: float = page.simple_culling_v
    center_vertically: bool = page.center_vertically
    title: str = page.title
    title_is_lstr: bool = page.title_is_lstr

    # Called with root container after construction completes.
    root_post_calls: list[Callable[[bui.Widget], None]] = []

    nextbuttonid = 0

    have_start_button = False
    have_selected_button = False

    # Precalc basic info like dimensions for all rows.
    for row in page_rows_filtered:

        # assert row.buttons
        this_row_width = (
            left_buffer
            + right_buffer
            + row.padding_left
            + row.padding_right
            + row.button_spacing * (len(row.buttons) - 1)
        )
        button_row_height = 30.0
        for button in row.buttons:
            if button.size is None:
                bwidth = default_button_width
                bheight = default_button_height
            else:
                bwidth = button.size[0]
                bheight = button.size[1]
            bscale = button.scale
            bwidthfull = bwidth * bscale
            bheightfull = bheight * bscale
            # Include button padding when calcing full needed height.
            button_row_height = max(
                button_row_height,
                bheightfull
                + (button.padding_top + button.padding_bottom) * button.scale,
            )
            this_row_width += (
                bwidthfull
                + (button.padding_left + button.padding_right) * button.scale
            )
        # Note: this includes everything in the *scrollable* part of
        # the row.
        this_row_height = (
            row.padding_top + row.padding_bottom + button_row_height
        )
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
        height += row.header_height * row.header_scale
        if row.title is not None:
            height += (
                row_title_height_no_subtitle
                if row.subtitle is None
                else row_title_height_with_subtitle
            )
        if row.subtitle is not None:
            height += row_subtitle_height
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

    for i, (row, rowprep) in enumerate(
        zip(page_rows_filtered, rows, strict=True)
    ):
        tdelaybase = 0.06 * (i + 1)

        y -= row.spacing_top

        if i != 0:
            y -= page.row_spacing

        # Header decorations.
        header_height_full = row.header_height * row.header_scale
        y -= header_height_full
        hdecs_l = (
            []
            if row.header_decorations_left is None
            else row.header_decorations_left
        )
        prepcalls2.prep_decorations(
            hdecs_l,
            left_buffer + header_inset_left,
            y + header_height_full * 0.5,
            row.header_scale,
            tdelay=None if immediate else (tdelaybase + 0.05),
            highlight=False,
            out_decoration_preps=rowprep.decorations,
        )
        hdecs_c = (
            []
            if row.header_decorations_center is None
            else row.header_decorations_center
        )
        prepcalls2.prep_decorations(
            hdecs_c,
            width * 0.5,
            y + header_height_full * 0.5,
            row.header_scale,
            tdelay=None if immediate else (tdelaybase + 0.05),
            highlight=False,
            out_decoration_preps=rowprep.decorations,
        )
        hdecs_r = (
            []
            if row.header_decorations_right is None
            else row.header_decorations_right
        )
        prepcalls2.prep_decorations(
            hdecs_r,
            width - right_buffer - header_inset_right,
            y + header_height_full * 0.5,
            row.header_scale,
            tdelay=None if immediate else (tdelaybase + 0.05),
            highlight=False,
            out_decoration_preps=rowprep.decorations,
        )

        if row.title is not None:
            rowprep.titlecalls.append(
                partial(
                    bui.textwidget,
                    position=(
                        (
                            ((width - left_buffer - right_buffer) * 0.5)
                            + 7.0  # Fudge factor to match hscroll
                            if row.center_title
                            else (left_buffer + header_inset_left)
                        ),
                        y - row_subtitle_height * 0.5,
                    ),
                    size=(0, 0),
                    text=row.title,
                    color=(
                        (0.85, 0.95, 0.89, 1.0)
                        if row.title_color is None
                        else row.title_color
                    ),
                    flatness=row.title_flatness,
                    shadow=row.title_shadow,
                    scale=1.0,
                    maxwidth=(
                        (width - left_buffer - right_buffer)
                        if row.center_title
                        else (
                            width
                            - left_buffer
                            - right_buffer
                            - header_inset_left
                            - header_inset_right
                        )
                    ),
                    h_align='center' if row.center_title else 'left',
                    v_align='center',
                    literal=not row.title_is_lstr,
                    transition_delay=(
                        None if immediate else (tdelaybase + 0.1)
                    ),
                )
            )
            y -= (
                row_title_height_no_subtitle
                if row.subtitle is None
                else row_title_height_with_subtitle
            )
        if row.subtitle is not None:
            rowprep.titlecalls.append(
                partial(
                    bui.textwidget,
                    position=(
                        (
                            ((width - left_buffer - right_buffer) * 0.5)
                            + 7.0  # Fudge factor to match hscroll
                            if row.center_title
                            else (left_buffer + header_inset_left)
                        ),
                        y - row_subtitle_height * 0.5,
                    ),
                    size=(0, 0),
                    text=row.subtitle,
                    color=(
                        (0.6, 0.74, 0.6)
                        if row.subtitle_color is None
                        else row.subtitle_color
                    ),
                    flatness=row.subtitle_flatness,
                    shadow=row.subtitle_shadow,
                    scale=0.7,
                    maxwidth=(
                        (width - left_buffer - right_buffer)
                        if row.center_title
                        else (
                            width
                            - left_buffer
                            - right_buffer
                            - header_inset_left
                            - header_inset_right
                        )
                    ),
                    h_align='center' if row.center_title else 'left',
                    v_align='center',
                    literal=not row.subtitle_is_lstr,
                    transition_delay=(
                        None if immediate else (tdelaybase + 0.2)
                    ),
                )
            )
            y -= row_subtitle_height

        y -= rowprep.height  # includes padding-top/bottom

        if row.debug:
            rowheightfull = (
                rowprep.height + row.header_height * row.header_scale
            )
            if row.title is not None:
                rowheightfull += (
                    row_title_height_no_subtitle
                    if row.subtitle is None
                    else row_title_height_with_subtitle
                )
            if row.subtitle is not None:
                rowheightfull += row_subtitle_height
            prepcalls2.prep_row_debug(
                (
                    width - left_buffer - right_buffer,
                    rowheightfull,
                ),
                (left_buffer, y),
                None if immediate else tdelaybase,
                rowprep.decorations,
            )

        rowprep.hscrollcall = partial(
            bui.hscrollwidget,
            size=(width - hscrollinset, rowprep.height),
            position=(hscrollinset, y),
            claims_left_right=True,
            highlight=False,
            border_opacity=0.0,
            center_small_content=row.center_content,
            simple_culling_h=row.simple_culling_h,
        )
        rowprep.hsubcall = partial(
            bui.containerwidget,
            size=(
                # Ideally we could just always use row-width, but
                # currently that gets us right-aligned stuff when
                # center-small-content is off.
                (
                    rowprep.width
                    if row.center_content
                    else max(width - hscrollinset - fudge, rowprep.width)
                ),
                rowprep.height,
            ),
            background=False,
        )
        x = left_buffer + row.padding_left
        # Calc height of buttons themselves (includes button padding but
        # not row padding).
        button_row_height = (
            rowprep.height - row.padding_top - row.padding_bottom
        )
        bcount = len(row.buttons)

        # Clamp or max delay if we've got lots of buttons.
        bdelaymax = min(0.5, 0.03 * bcount)
        for j, button in enumerate(row.buttons):
            # Calc amt 1 -> 0 across the row.
            tdelayamt = 1.0 - (j / max(1, bcount - 1))
            # Rightmost buttons slide in first.
            tdelay = tdelaybase + tdelayamt * bdelaymax

            xorig = x
            x += button.padding_left * button.scale
            bscale = button.scale
            if button.size is None:
                bwidth = default_button_width
                bheight = default_button_height
            else:
                bwidth = button.size[0]
                bheight = button.size[1]
            bwidthfull = bscale * bwidth
            bheightfull = bscale * bheight
            # Vertically center the button plus its padding.
            to_button_plus_padding_bottom = (
                button_row_height
                - (
                    bheightfull
                    + (button.padding_top + button.padding_bottom)
                    * button.scale
                )
            ) * 0.5
            # Move up past bottom padding to get button bottom.
            to_button_bottom = (
                to_button_plus_padding_bottom
                + button.padding_bottom * button.scale
            )

            center_x = x + bwidthfull * 0.5
            center_y = row.padding_bottom + to_button_bottom + bheightfull * 0.5

            bstyle: str
            if button.style is dui1.ButtonStyle.SQUARE:
                bstyle = 'square'
            elif button.style is dui1.ButtonStyle.TAB:
                bstyle = 'tab'
            elif button.style is dui1.ButtonStyle.SMALL:
                bstyle = 'small'
            elif button.style is dui1.ButtonStyle.MEDIUM:
                bstyle = 'medium'
            elif button.style is dui1.ButtonStyle.LARGE:
                bstyle = 'large'
            elif button.style is dui1.ButtonStyle.LARGER:
                bstyle = 'larger'
            elif button.style is dui1.ButtonStyle.BACK:
                bstyle = 'back'
            elif button.style is dui1.ButtonStyle.BACK_SMALL:
                bstyle = 'backSmall'
            elif button.style is dui1.ButtonStyle.SQUARE_WIDE:
                bstyle = 'squareWide'
            else:
                assert_never(button.style)

            widgetid: str
            if button.widget_id is None:
                widgetid = f'{idprefix}|button{nextbuttonid}'
                nextbuttonid += 1
            else:
                widgetid = f'{idprefix}|{button.widget_id}'

            if button.default:
                if have_start_button:
                    bui.uilog.warning(
                        'Multiple buttons flagged as default.'
                        ' There can be only one per page.'
                    )
                else:
                    have_start_button = True
                    root_post_calls.append(partial(_set_start_button, widgetid))
            if button.selected:
                if have_selected_button:
                    bui.uilog.warning(
                        'Multiple buttons flagged as selected.'
                        ' There can be only one per page.'
                    )
                else:
                    have_selected_button = True
                    root_post_calls.append(
                        partial(_set_selected_button, widgetid)
                    )

            show_buffer_left = button.padding_left * bscale
            show_buffer_right = button.padding_right * bscale

            # Calc the total height of what we're trying to keep on
            # screen, and then nudge that towards the total visible
            # height of the scroll area.
            total_show_width = (
                bwidth + button.padding_left + button.padding_right
            ) * bscale

            # How much to push show-height towards full available space.
            # 1.0 should lead to always perfect centering (but that
            # might feel too aggressive).
            amt = 0.6
            buffer_extra = max(
                0.0, (scroll_width - total_show_width) * 0.5 * amt
            )
            show_buffer_left += buffer_extra
            show_buffer_right += buffer_extra

            buttonprep = ButtonPrep(
                buttoncall=partial(
                    bui.buttonwidget,
                    id=widgetid,
                    position=(x, row.padding_bottom + to_button_bottom),
                    size=(bwidth, bheight),
                    scale=bscale,
                    color=(None if button.color is None else button.color[:3]),
                    textcolor=button.label_color,
                    text_flatness=(button.label_flatness),
                    text_scale=button.label_scale,
                    button_type=bstyle,
                    opacity=(1.0 if button.color is None else button.color[3]),
                    label='' if button.label is None else button.label,
                    text_literal=not button.label_is_lstr,
                    autoselect=True,
                    enable_sound=False,
                    transition_delay=None if immediate else tdelay,
                    icon_color=button.icon_color,
                    iconscale=button.icon_scale,
                    better_bg_fit=True,
                ),
                buttoneditcall=partial(
                    bui.widget,
                    # TODO: Calc left/right vals properly based on
                    # our size and padding.
                    show_buffer_left=show_buffer_left,
                    show_buffer_right=show_buffer_right,
                    depth_range=button.depth_range,
                    # We explicitly assign all neighbor selection;
                    # anything left over should go to toolbars.
                    auto_select_toolbars_only=True,
                ),
                decorations=[],
                textures={},
                widgetid=widgetid,
                action=button.action,
            )
            if button.texture is not None:
                buttonprep.textures['texture'] = button.texture

            if button.icon is not None:
                buttonprep.textures['icon'] = button.icon

            # With row-debug on, visualize the area we try to scroll to
            # show when each button is selected. Note that we're clamped
            # by the h-scroll here so we have to draw a separate box for
            # the row title/subtitle.
            if row.debug:
                prepcalls2.prep_row_debug_button(
                    (
                        bwidthfull
                        + (button.padding_left + button.padding_right)
                        * button.scale,
                        rowprep.height,
                    ),
                    (xorig, 0.0),
                    None if immediate else tdelay,
                    buttonprep.decorations,
                )

            if button.debug:
                prepcalls2.prep_button_debug(
                    (bwidthfull, bheightfull),
                    (center_x, center_y),
                    None if immediate else tdelay,
                    buttonprep.decorations,
                )
            decorations = (
                [] if button.decorations is None else button.decorations
            )
            prepcalls2.prep_decorations(
                decorations,
                center_x,
                center_y,
                bscale,
                None if immediate else tdelay,
                highlight=True,
                out_decoration_preps=buttonprep.decorations,
            )

            rowprep.buttons.append(buttonprep)

            x += (
                bwidthfull
                + (button.padding_right * button.scale)
                + row.button_spacing
            )

        # Add an edit call for our new hscroll to give it proper
        # show-buffers.

        # Incorporate top buffer so we scroll all the way up
        # when selecting the top row (and stay clear of
        # toolbars).
        show_buffer_top = top_buffer
        show_buffer_bottom = bot_buffer

        # Scroll so title/subtitle is in view when selecting.
        # Note that we don't need to account for
        # padding-top/bottom since the h-scroll that we're
        # applying to encompasses both.
        show_buffer_top += row.header_height * row.header_scale
        if row.title is not None:
            show_buffer_top += (
                row_title_height_no_subtitle
                if row.subtitle is None
                else row_title_height_with_subtitle
            )
        if row.subtitle is not None:
            show_buffer_top += row_subtitle_height

        # Calc the total height of what we're trying to keep on
        # screen, and then nudge that towards the total visible
        # height of the scroll area.
        total_show_height = (
            rowprep.height + show_buffer_top + show_buffer_bottom
        )
        # How much to push show-height towards full available space.
        # 1.0 should lead to always perfect centering (but that
        # might feel too aggressive).
        amt = 0.5
        buffer_extra = max(0.0, (scroll_height - total_show_height) * 0.5 * amt)

        show_buffer_top += buffer_extra
        show_buffer_bottom += buffer_extra

        rowprep.hscrolleditcall = partial(
            bui.widget,
            show_buffer_top=show_buffer_top,
            show_buffer_bottom=show_buffer_bottom,
        )
        y -= row.spacing_bottom

    return PagePrep(
        rootcall=rootcall,
        rows=rows,
        width=width,
        height=height,
        simple_culling_v=simple_culling_v,
        center_vertically=center_vertically,
        title=title,
        title_is_lstr=title_is_lstr,
        root_post_calls=root_post_calls,
    )


def doc_ui_v1_instantiate_page_prep(
    pageprep: PagePrep,
    *,
    rootwidget: bui.Widget,
    scrollwidget: bui.Widget,
    backbutton: bui.Widget,
    windowbackbutton: bui.Widget | None,
    window: DocUIWindow,
) -> bui.Widget:
    """Create a UI using prepped data."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    outrows: list[tuple[bui.Widget, list[bui.Widget]]] = []

    # Now go through and run our prepped ui calls to build our
    # widgets, plugging in appropriate parent widgets args and
    # whatnot as we go.
    assert pageprep.rootcall is not None
    subcontainer = pageprep.rootcall(parent=scrollwidget)
    for rowprep in pageprep.rows:
        for uicall in rowprep.titlecalls:
            uicall(parent=subcontainer)
        assert rowprep.hscrollcall is not None
        hscroll = rowprep.hscrollcall(parent=subcontainer)
        for decoration in rowprep.decorations:
            kwds: dict = {'parent': subcontainer}
            for texarg, texname in decoration.textures.items():
                kwds[texarg] = bui.gettexture(texname)
            for mesharg, meshname in decoration.meshes.items():
                kwds[mesharg] = bui.getmesh(meshname)
            decoration.call(**kwds)
        outrow: tuple[bui.Widget, list[bui.Widget]] = (hscroll, [])
        assert rowprep.hsubcall is not None
        hsub = rowprep.hsubcall(parent=hscroll)
        for i, buttonprep in enumerate(rowprep.buttons):
            kwds = {
                'parent': hsub,
                'on_activate_call': strict_partial(
                    window.controller.run_action,
                    window,
                    buttonprep.widgetid,
                    buttonprep.action,
                ),
            }
            for texarg, texname in buttonprep.textures.items():
                kwds[texarg] = bui.gettexture(texname)
            btn = buttonprep.buttoncall(**kwds)
            assert buttonprep.buttoneditcall is not None
            buttonprep.buttoneditcall(edit=btn)
            for decoration in buttonprep.decorations:
                kwds = {'parent': hsub}
                if decoration.highlight:
                    kwds['draw_controller'] = btn
                for texarg, texname in decoration.textures.items():
                    kwds[texarg] = bui.gettexture(texname)
                for mesharg, meshname in decoration.meshes.items():
                    kwds[mesharg] = bui.getmesh(meshname)
                decoration.call(**kwds)

            # Make sure row is scrolled so leftmost button is
            # visible (though it kinda seems like this should happen
            # by default).
            if i == 0:
                bui.containerwidget(edit=hsub, visible_child=btn)
            outrow[1].append(btn)

        outrows.append(outrow)
        assert rowprep.hscrolleditcall is not None
        rowprep.hscrolleditcall(edit=hscroll)

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
        if buttons:
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

    return subcontainer


def _set_start_button(buttonid: str, root: bui.Widget) -> None:
    widget = bui.widget_by_id(buttonid)
    if widget:
        bui.containerwidget(edit=root, start_button=widget)


def _set_selected_button(buttonid: str, root: bui.Widget) -> None:
    del root  # Unused.
    widget = bui.widget_by_id(buttonid)
    if widget:
        widget.global_select()
