# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Prep functionality for our UI.

We do all layout math and bake out partial ui calls in a background
thread so there's as little work to do in the ui thread as possible.
"""

from __future__ import annotations

from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

from efro.util import strict_partial

import bacommon.cloudui.v1 as clui
import bauiv1 as bui


if TYPE_CHECKING:
    from typing import Callable

    from bauiv1lib.cloudui._window import CloudUIWindow


@dataclass
class _DecorationPrep:
    call: Callable[..., bui.Widget]
    textures: dict[str, str]
    meshes: dict[str, str]
    highlight: bool


@dataclass
class _ButtonPrep:
    buttoncall: Callable[..., bui.Widget]
    buttoneditcall: Callable | None
    decorations: list[_DecorationPrep]
    textures: dict[str, str]
    widgetid: str
    action: clui.Action | None


@dataclass
class _RowPrep:
    width: float
    height: float
    titlecalls: list[Callable[..., bui.Widget]]
    hscrollcall: Callable[..., bui.Widget] | None
    hscrolleditcall: Callable | None
    hsubcall: Callable[..., bui.Widget] | None
    buttons: list[_ButtonPrep]
    simple_culling_h: float
    decorations: list[_DecorationPrep]


class CloudUIPagePrep:
    """Preps a page.

    Generally does its work in a background thread.
    """

    def __init__(
        self,
        page: clui.Page,
        *,
        uiscale: bui.UIScale,
        scroll_width: float,
        scroll_height: float,
        idprefix: str,
        immediate: bool = False,
    ) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals

        # Ok; we've got some buttons. Build our full UI.
        row_title_height = 30.0
        row_subtitle_height = 30.0

        # Buffers for *everything*.
        top_buffer = 20.0
        bot_buffer = 20.0
        left_buffer = 0.0
        right_buffer = 10.0  # Nudge a bit due to scrollbar.

        # Extra buffers for title/headers stuff (not in h-scroll).
        header_inset_left = 35.0
        header_inset_right = 20.0

        default_button_width = 200.0
        default_button_height = 200.0

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

        self.rootcall: Callable[..., bui.Widget] | None = None
        self.rows: list[_RowPrep] = []
        self.width: float = scroll_width + fudge
        self.height: float = (
            top_buffer
            + bot_buffer
            + page.row_spacing * max(0, (len(page.rows) - 1))
        )
        self.simple_culling_v: float = page.simple_culling_v
        self.center_vertically: bool = page.center_vertically
        self.title: str = page.title
        self.title_is_lstr: bool = page.title_is_lstr

        # Called with root container after construction completes.
        self.root_post_calls: list[Callable[[bui.Widget], None]] = []

        nextbuttonid = 0

        have_start_button = False
        have_selected_button = False

        # Precalc basic info like dimensions for all rows.
        for row in page.rows:
            assert row.buttons
            this_row_width = (
                left_buffer
                + right_buffer
                + row.padding_left
                + row.padding_right
                + row.button_spacing * (len(row.buttons) - 1)
            )
            button_row_height = 0.0
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
                    + (button.padding_top + button.padding_bottom)
                    * button.scale,
                )
                this_row_width += (
                    bwidthfull
                    + (button.padding_left + button.padding_right)
                    * button.scale
                )
            # Note: this includes everything in the *scrollable* part of
            # the row.
            this_row_height = (
                row.padding_top + row.padding_bottom + button_row_height
            )
            self.rows.append(
                _RowPrep(
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
            self.height += row.header_height * row.header_scale
            if row.title is not None:
                self.height += row_title_height
            if row.subtitle is not None:
                self.height += row_subtitle_height
            self.height += this_row_height

        # Ok; we've got all row dimensions. Now prep calls to make the
        # subcontainers to fit everything and fill out all rows.
        self.rootcall = partial(
            bui.containerwidget,
            size=(self.width, self.height),
            claims_left_right=True,
            background=False,
        )
        y = self.height - top_buffer

        for i, (row, rowprep) in enumerate(
            zip(page.rows, self.rows, strict=True)
        ):
            tdelaybase = 0.12 * (i + 1)

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
            _prep_decorations(
                hdecs_l,
                left_buffer + header_inset_left,
                y + header_height_full * 0.5,
                row.header_scale,
                tdelay=None if immediate else (tdelaybase + 0.1),
                highlight=False,
                decorationpreps=rowprep.decorations,
            )
            hdecs_c = (
                []
                if row.header_decorations_center is None
                else row.header_decorations_center
            )
            _prep_decorations(
                hdecs_c,
                self.width * 0.5,
                y + header_height_full * 0.5,
                row.header_scale,
                tdelay=None if immediate else (tdelaybase + 0.1),
                highlight=False,
                decorationpreps=rowprep.decorations,
            )
            hdecs_r = (
                []
                if row.header_decorations_right is None
                else row.header_decorations_right
            )
            _prep_decorations(
                hdecs_r,
                self.width - right_buffer - header_inset_right,
                y + header_height_full * 0.5,
                row.header_scale,
                tdelay=None if immediate else (tdelaybase + 0.1),
                highlight=False,
                decorationpreps=rowprep.decorations,
            )

            if row.title is not None:
                rowprep.titlecalls.append(
                    partial(
                        bui.textwidget,
                        position=(
                            (
                                (
                                    (self.width - left_buffer - right_buffer)
                                    * 0.5
                                )
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
                            (self.width - left_buffer - right_buffer)
                            if row.center_title
                            else (
                                self.width
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
                            None if immediate else (tdelaybase + 0.2)
                        ),
                    )
                )
                y -= row_title_height
            if row.subtitle is not None:
                rowprep.titlecalls.append(
                    partial(
                        bui.textwidget,
                        position=(
                            (
                                (
                                    (self.width - left_buffer - right_buffer)
                                    * 0.5
                                )
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
                            (self.width - left_buffer - right_buffer)
                            if row.center_title
                            else (
                                self.width
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
                            None if immediate else (tdelaybase + 0.3)
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
                    rowheightfull += row_title_height
                if row.subtitle is not None:
                    rowheightfull += row_subtitle_height
                _prep_row_debug(
                    (
                        self.width - left_buffer - right_buffer,
                        rowheightfull,
                    ),
                    (left_buffer, y),
                    None if immediate else tdelaybase,
                    rowprep.decorations,
                )

            rowprep.hscrollcall = partial(
                bui.hscrollwidget,
                size=(self.width - hscrollinset, rowprep.height),
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
                        else max(
                            self.width - hscrollinset - fudge, rowprep.width
                        )
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
            for j, button in enumerate(row.buttons):
                # Calc amt 1 -> 0 across the row.
                tdelayamt = 1.0 - (j / max(1, bcount - 1))
                # Rightmost buttons slide in first.
                tdelay = tdelaybase + tdelayamt * (0.03 * bcount)

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
                center_y = (
                    row.padding_bottom + to_button_bottom + bheightfull * 0.5
                )

                bstyle: str
                if button.style is clui.ButtonStyle.SQUARE:
                    bstyle = 'square'
                elif button.style is clui.ButtonStyle.TAB:
                    bstyle = 'tab'
                elif button.style is clui.ButtonStyle.SMALL:
                    bstyle = 'small'
                elif button.style is clui.ButtonStyle.MEDIUM:
                    bstyle = 'medium'
                elif button.style is clui.ButtonStyle.LARGE:
                    bstyle = 'large'
                elif button.style is clui.ButtonStyle.LARGER:
                    bstyle = 'larger'
                else:
                    assert_never(button.style)

                widgetid = f'{idprefix}|button{nextbuttonid}'

                if button.default:
                    if have_start_button:
                        bui.uilog.warning(
                            'Multiple buttons flagged as default.'
                            ' There can be only one per page.'
                        )
                    else:
                        have_start_button = True
                        self.root_post_calls.append(
                            partial(self._set_start_button, widgetid)
                        )
                if button.selected:
                    if have_selected_button:
                        bui.uilog.warning(
                            'Multiple buttons flagged as selected.'
                            ' There can be only one per page.'
                        )
                    else:
                        have_selected_button = True
                        self.root_post_calls.append(
                            partial(self._set_selected_button, widgetid)
                        )

                buttonprep = _ButtonPrep(
                    buttoncall=partial(
                        bui.buttonwidget,
                        id=widgetid,
                        position=(x, row.padding_bottom + to_button_bottom),
                        size=(bwidth, bheight),
                        scale=bscale,
                        color=button.color,
                        textcolor=button.text_color,
                        text_flatness=(button.text_flatness),
                        text_scale=button.text_scale,
                        button_type=bstyle,
                        opacity=button.opacity,
                        label='' if button.label is None else button.label,
                        text_literal=not button.text_is_lstr,
                        autoselect=True,
                        enable_sound=False,
                        transition_delay=None if immediate else tdelay,
                        icon_color=button.icon_color,
                        iconscale=button.icon_scale,
                    ),
                    buttoneditcall=partial(
                        bui.widget,
                        # TODO: Calc left/right vals properly based on
                        # our size and padding.
                        show_buffer_left=150,
                        show_buffer_right=150,
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
                nextbuttonid += 1
                if button.texture is not None:
                    buttonprep.textures['texture'] = button.texture

                if button.icon is not None:
                    buttonprep.textures['icon'] = button.icon

                # With row-debug on, visualize the area we try to scroll to
                # show when each button is selected. Note that we're clamped
                # by the h-scroll here so we have to draw a separate box for
                # the row title/subtitle.
                if row.debug:
                    _prep_row_debug_button(
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
                    _prep_button_debug(
                        (bwidthfull, bheightfull),
                        (center_x, center_y),
                        None if immediate else tdelay,
                        buttonprep.decorations,
                    )
                decorations = (
                    [] if button.decorations is None else button.decorations
                )
                _prep_decorations(
                    decorations,
                    center_x,
                    center_y,
                    bscale,
                    None if immediate else tdelay,
                    highlight=True,
                    decorationpreps=buttonprep.decorations,
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
            if row.title is not None:
                show_buffer_top += row_title_height
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
            buffer_extra = max(
                0.0, (scroll_height - total_show_height) * 0.5 * amt
            )

            show_buffer_top += buffer_extra
            show_buffer_bottom += buffer_extra

            rowprep.hscrolleditcall = partial(
                bui.widget,
                show_buffer_top=show_buffer_top,
                show_buffer_bottom=show_buffer_bottom,
            )

    def instantiate(
        self,
        *,
        rootwidget: bui.Widget,
        scrollwidget: bui.Widget,
        backbutton: bui.Widget,
        windowbackbutton: bui.Widget | None,
        window: CloudUIWindow,
    ) -> bui.Widget:
        """Create a UI using prepped data."""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        outrows: list[tuple[bui.Widget, list[bui.Widget]]] = []

        # Clear any existin children.
        for child in scrollwidget.get_children():
            child.delete()

        # Now go through and run our prepped ui calls to build our
        # widgets, plugging in appropriate parent widgets args and
        # whatnot as we go.
        assert self.rootcall is not None
        subcontainer = self.rootcall(parent=scrollwidget)
        for rowprep in self.rows:
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

        for root_post_call in self.root_post_calls:
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

    @staticmethod
    def _set_start_button(buttonid: str, root: bui.Widget) -> None:
        widget = bui.widget_by_id(buttonid)
        if widget:
            bui.containerwidget(edit=root, start_button=widget)

    @staticmethod
    def _set_selected_button(buttonid: str, root: bui.Widget) -> None:
        del root  # Unused.
        widget = bui.widget_by_id(buttonid)
        if widget:
            widget.global_select()


def _prep_text(
    text: clui.Text,
    bcenter: tuple[float, float],
    bscale: float,
    tdelay: float | None,
    decorations: list[_DecorationPrep],
    *,
    highlight: bool,
) -> None:
    # pylint: disable=too-many-branches
    xoffs = bcenter[0] + text.position[0] * bscale
    yoffs = bcenter[1] + text.position[1] * bscale

    if text.h_align is clui.HAlign.LEFT:
        h_align = 'left'
    elif text.h_align is clui.HAlign.CENTER:
        h_align = 'center'
    elif text.h_align is clui.HAlign.RIGHT:
        h_align = 'right'
    else:
        assert_never(text.h_align)

    if text.v_align is clui.VAlign.TOP:
        v_align = 'top'
    elif text.v_align is clui.VAlign.CENTER:
        v_align = 'center'
    elif text.v_align is clui.VAlign.BOTTOM:
        v_align = 'bottom'
    else:
        assert_never(text.v_align)

    decorations.append(
        _DecorationPrep(
            call=partial(
                bui.textwidget,
                position=(xoffs, yoffs),
                scale=text.scale * bscale,
                maxwidth=text.size[0] * bscale,
                max_height=text.size[1] * bscale,
                flatness=text.flatness,
                shadow=text.shadow,
                h_align=h_align,
                v_align=v_align,
                size=(0, 0),
                color=text.color,
                text=text.text,
                literal=not text.is_lstr,
                transition_delay=tdelay,
                depth_range=text.depth_range,
            ),
            textures={},
            meshes={},
            highlight=highlight and text.highlight,
        )
    )
    # Draw square around max width/height in debug mode.
    if text.debug:
        mwfull = bscale * text.size[0]
        mhfull = bscale * text.size[1]

        if text.h_align is clui.HAlign.LEFT:
            mwxoffs = xoffs
        elif text.h_align is clui.HAlign.CENTER:
            mwxoffs = xoffs - mwfull * 0.5
        elif text.h_align is clui.HAlign.RIGHT:
            mwxoffs = xoffs - mwfull
        else:
            assert_never(text.h_align)

        if text.v_align is clui.VAlign.TOP:
            mwyoffs = yoffs - mhfull
        elif text.v_align is clui.VAlign.CENTER:
            mwyoffs = yoffs - mhfull * 0.5
        elif text.v_align is clui.VAlign.BOTTOM:
            mwyoffs = yoffs
        else:
            assert_never(text.v_align)

        decorations.append(
            _DecorationPrep(
                call=partial(
                    bui.imagewidget,
                    position=(mwxoffs, mwyoffs),
                    size=(mwfull, mhfull),
                    color=(1, 0, 0),
                    opacity=0.2,
                    transition_delay=tdelay,
                ),
                textures={'texture': 'white'},
                meshes={},
                highlight=True,
            )
        )


def _prep_decorations(
    decorations: list[clui.Decoration],
    center_x: float,
    center_y: float,
    scale: float,
    tdelay: float | None,
    *,
    highlight: bool,
    decorationpreps: list[_DecorationPrep],
) -> None:
    for decoration in decorations:
        dectypeid = decoration.get_type_id()
        if dectypeid is clui.DecorationTypeID.UNKNOWN:
            if bui.do_once():
                bui.uilog.exception(
                    'CloudUI receieved unknown decoration;'
                    ' this is likely a server error.'
                )
        elif dectypeid is clui.DecorationTypeID.TEXT:
            assert isinstance(decoration, clui.Text)
            _prep_text(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                decorationpreps,
                highlight=highlight,
            )

        elif dectypeid is clui.DecorationTypeID.IMAGE:
            assert isinstance(decoration, clui.Image)
            _prep_image(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                decorationpreps,
                highlight=highlight,
            )
        else:
            assert_never(dectypeid)


def _prep_image(
    image: clui.Image,
    bcenter: tuple[float, float],
    bscale: float,
    tdelay: float | None,
    decorations: list[_DecorationPrep],
    *,
    highlight: bool,
) -> None:
    xoffs = bcenter[0] + image.position[0] * bscale
    yoffs = bcenter[1] + image.position[1] * bscale

    widthfull = bscale * image.size[0]
    heightfull = bscale * image.size[1]

    if image.h_align is clui.HAlign.LEFT:
        xoffsfin = xoffs
    elif image.h_align is clui.HAlign.CENTER:
        xoffsfin = xoffs - widthfull * 0.5
    elif image.h_align is clui.HAlign.RIGHT:
        xoffsfin = xoffs - widthfull
    else:
        assert_never(image.h_align)

    if image.v_align is clui.VAlign.TOP:
        yoffsfin = yoffs - heightfull
    elif image.v_align is clui.VAlign.CENTER:
        yoffsfin = yoffs - heightfull * 0.5
    elif image.v_align is clui.VAlign.BOTTOM:
        yoffsfin = yoffs
    else:
        assert_never(image.v_align)

    textures: dict[str, str] = {'texture': image.texture}
    if image.tint_texture is not None:
        textures['tint_texture'] = image.tint_texture
    if image.mask_texture is not None:
        textures['mask_texture'] = image.mask_texture

    meshes: dict[str, str] = {}
    if image.mesh_opaque is not None:
        meshes['mesh_opaque'] = image.mesh_opaque
    if image.mesh_transparent is not None:
        meshes['mesh_transparent'] = image.mesh_transparent

    decorations.append(
        _DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(xoffsfin, yoffsfin),
                size=(widthfull, heightfull),
                color=image.color,
                opacity=image.opacity,
                tint_color=image.tint_color,
                tint2_color=image.tint2_color,
                transition_delay=tdelay,
                depth_range=image.depth_range,
            ),
            textures=textures,
            meshes=meshes,
            highlight=highlight and image.highlight,
        )
    )


def _prep_row_debug(
    size: tuple[float, float],
    pos: tuple[float, float],
    tdelay: float | None,
    decorations: list[_DecorationPrep],
) -> None:

    textures: dict[str, str] = {'texture': 'white'}

    # Shrink the square we draw a tiny bit so rows butted up to
    # eachother can be seen.
    border_shrink = 1.0

    decorations.append(
        _DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(pos[0], pos[1] + border_shrink),
                size=(size[0], size[1] - 2.0 * border_shrink),
                color=(0, 0, 1.0),
                opacity=0.1,
                transition_delay=tdelay,
            ),
            textures=textures,
            meshes={},
            highlight=True,
        )
    )


def _prep_row_debug_button(
    bsize: tuple[float, float],
    bcorner: tuple[float, float],
    tdelay: float | None,
    decorations: list[_DecorationPrep],
) -> None:
    xoffs = bcorner[0]
    yoffs = bcorner[1]

    textures: dict[str, str] = {'texture': 'white'}

    decorations.append(
        _DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(xoffs, yoffs),
                size=bsize,
                color=(0.0, 0.0, 1),
                opacity=0.15,
                transition_delay=tdelay,
            ),
            textures=textures,
            meshes={},
            highlight=True,
        )
    )


def _prep_button_debug(
    bsize: tuple[float, float],
    bcenter: tuple[float, float],
    tdelay: float | None,
    decorations: list[_DecorationPrep],
) -> None:
    textures: dict[str, str] = {'texture': 'white'}

    decorations.append(
        _DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(
                    bcenter[0] - bsize[0] * 0.5,
                    bcenter[1] - bsize[1] * 0.5,
                ),
                size=bsize,
                color=(0, 1, 0),
                opacity=0.1,
                transition_delay=tdelay,
            ),
            textures=textures,
            meshes={},
            highlight=True,
        )
    )
