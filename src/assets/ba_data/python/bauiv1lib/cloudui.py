# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

from __future__ import annotations

import random
from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, override, assert_never

import babase
import bacommon.cloudui.v1 as clui
from bauiv1lib.utils import scroll_fade_bottom, scroll_fade_top
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable


def show_cloud_ui_window() -> None:
    """Bust out a cloud-ui window."""

    # Pop up an auxiliary window wherever we are in the nav stack.
    babase.app.ui_v1.auxiliary_window_activate(
        win_type=CloudUIWindow,
        win_create_call=lambda: CloudUIWindow(state=None),
    )


# Prep structures for our UI - we do all layout math and bake out
# ready-to-run ui calls in a background thread so there's as little work
# as possible to do in the ui thread.


@dataclass
class _ButtonPrep:
    buttoncall: Callable[..., bui.Widget]
    buttoneditcall: Callable | None
    decorationcalls: list[Callable[..., bui.Widget]]


@dataclass
class _RowPrep:
    width: float
    height: float
    titlecalls: list[Callable[..., bui.Widget]]
    hscrollcall: Callable[..., bui.Widget] | None
    hscrolleditcall: Callable | None
    hsubcall: Callable[..., bui.Widget] | None
    buttons: list[_ButtonPrep]


@dataclass
class _UIPrep:
    rootcall: Callable[..., bui.Widget] | None
    rows: list[_RowPrep]
    width: float
    height: float


def _prep_ui(
    ui: clui.UI, uiscale: babase.UIScale, scroll_width: float
) -> _UIPrep:
    """Prep a ui."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals

    # Ok; we've got some buttons. Build our full UI.
    row_title_height = 30.0
    row_subtitle_height = 30.0
    top_buffer = 20.0
    bot_buffer = 20.0
    left_buffer = 0.0
    right_buffer = 10.0  # Nudge a bit due to scrollbar.
    title_inset = 35.0
    default_button_width = 200.0
    default_button_height = 200.0

    if uiscale is babase.UIScale.SMALL:
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

    uiprep = _UIPrep(
        rootcall=None,
        rows=[],
        width=scroll_width + fudge,
        height=top_buffer + bot_buffer,
    )

    # Precalc basic row info like dimensions.
    for row in ui.rows:
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
                bheightfull + button.padding_top + button.padding_bottom,
            )
            this_row_width += (
                bwidthfull + button.padding_left + button.padding_right
            )
        this_row_height = (
            row.padding_top + row.padding_bottom + button_row_height
        )
        uiprep.rows.append(
            _RowPrep(
                width=this_row_width,
                height=this_row_height,
                titlecalls=[],
                hscrollcall=None,
                hscrolleditcall=None,
                hsubcall=None,
                buttons=[],
            )
        )
        assert this_row_height > 0.0
        assert this_row_width > 0.0
        if row.title is not None:
            uiprep.height += row_title_height
        if row.subtitle is not None:
            uiprep.height += row_subtitle_height
        uiprep.height += this_row_height

    # Ok; we've got overall dimensions. Now prep a call to make the
    # subcontainer and then fill in its rows.
    uiprep.rootcall = partial(
        bui.containerwidget,
        size=(uiprep.width, uiprep.height),
        claims_left_right=True,
        background=False,
    )
    y = uiprep.height - top_buffer
    for row, rowprep in zip(ui.rows, uiprep.rows, strict=True):
        if row.title is not None:
            rowprep.titlecalls.append(
                partial(
                    bui.textwidget,
                    position=(
                        left_buffer + title_inset,
                        y - row_title_height * 0.5,
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
                        uiprep.width - left_buffer - right_buffer - title_inset
                    ),
                    h_align='left',
                    v_align='center',
                    literal=True,
                )
            )
            y -= row_title_height
        if row.subtitle is not None:
            rowprep.titlecalls.append(
                partial(
                    bui.textwidget,
                    position=(
                        left_buffer + title_inset,
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
                        uiprep.width - left_buffer - right_buffer - title_inset
                    ),
                    h_align='left',
                    v_align='center',
                    literal=True,
                )
            )
            y -= row_subtitle_height

        y -= rowprep.height  # includes padding-top/bottom
        rowprep.hscrollcall = partial(
            bui.hscrollwidget,
            size=(uiprep.width - hscrollinset, rowprep.height),
            position=(hscrollinset, y),
            claims_left_right=True,
            highlight=False,
            border_opacity=0.0,
            center_small_content=row.center,
            simple_culling_h=10.0,
        )
        rowprep.hsubcall = partial(
            bui.containerwidget,
            size=(
                # Ideally we could just always use row-width, but
                # currently that gets us right-aligned stuff when
                # center-small-content is off.
                (
                    rowprep.width
                    if row.center
                    else max(uiprep.width - hscrollinset - fudge, rowprep.width)
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
        for button in row.buttons:
            x += button.padding_left
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
                - (bheightfull + button.padding_top + button.padding_bottom)
            ) * 0.5
            # Move up past bottom padding to get button bottom.
            to_button_bottom = (
                to_button_plus_padding_bottom + button.padding_bottom
            )

            center_x = x + bwidthfull * 0.5
            center_y = row.padding_bottom + to_button_bottom + bheightfull * 0.5
            buttonprep = _ButtonPrep(
                buttoncall=partial(
                    bui.buttonwidget,
                    position=(x, row.padding_bottom + to_button_bottom),
                    size=(bwidth, bheight),
                    scale=bscale,
                    color=button.color,
                    textcolor=button.text_color,
                    text_flatness=(button.text_flatness),
                    text_scale=button.text_scale,
                    button_type='square',
                    label='' if button.label is None else button.label,
                    text_literal=True,
                    autoselect=True,
                ),
                buttoneditcall=partial(
                    bui.widget,
                    show_buffer_left=150,
                    show_buffer_right=150,
                ),
                decorationcalls=[],
            )
            for decoration in button.decorations:
                dectypeid = decoration.get_type_id()
                if dectypeid is clui.DecorationTypeID.UNKNOWN:
                    pass
                elif dectypeid is clui.DecorationTypeID.TEXT:
                    assert isinstance(decoration, clui.Text)
                    buttonprep.decorationcalls.append(
                        partial(
                            bui.textwidget,
                            position=(center_x, center_y),
                            scale=bscale,
                            maxwidth=bscale * decoration.max_width,
                            flatness=decoration.flatness,
                            shadow=decoration.shadow,
                            h_align='center',
                            v_align='center',
                            size=(0, 0),
                            color=(0.5, 0.5, 0.5, 1.0),
                            text=decoration.text,
                        )
                    )
                else:
                    assert_never(dectypeid)

            rowprep.buttons.append(buttonprep)

            x += bwidthfull + button.padding_right + row.button_spacing

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

        rowprep.hscrolleditcall = partial(
            bui.widget,
            show_buffer_top=show_buffer_top,
            show_buffer_bottom=show_buffer_bottom,
        )
    return uiprep


def _instantiate_ui(
    uiprep: _UIPrep,
    scrollwidget: bui.Widget,
    backbutton: bui.Widget,
    windowbackbutton: bui.Widget | None,
) -> bui.Widget:
    # pylint: disable=too-many-locals
    outrows: list[tuple[bui.Widget, list[bui.Widget]]] = []

    # Now go through and run our prepped ui calls to build our
    # widgets, plugging in appropriate parent widgets args and
    # whatnot as we go.
    assert uiprep.rootcall is not None
    subcontainer = uiprep.rootcall(parent=scrollwidget)
    for rowprep in uiprep.rows:
        for uicall in rowprep.titlecalls:
            uicall(parent=subcontainer)
        assert rowprep.hscrollcall is not None
        hscroll = rowprep.hscrollcall(parent=subcontainer)
        outrow: tuple[bui.Widget, list[bui.Widget]] = (hscroll, [])
        assert rowprep.hsubcall is not None
        hsub = rowprep.hsubcall(parent=hscroll)
        for i, buttonprep in enumerate(rowprep.buttons):
            btn = buttonprep.buttoncall(parent=hsub)
            assert buttonprep.buttoneditcall is not None
            buttonprep.buttoneditcall(edit=btn)
            for deccall in buttonprep.decorationcalls:
                deccall(parent=hsub, draw_controller=btn)

            # Make sure row is scrolled so leftmost button is
            # visible (though kinda seems like this should happen by
            # default).
            if i == 0:
                bui.containerwidget(edit=hsub, visible_child=btn)
            outrow[1].append(btn)

        outrows.append(outrow)
        assert rowprep.hscrolleditcall is not None
        rowprep.hscrolleditcall(edit=hscroll)

    # Ok; we've got all widgets. Now wire up directional nav between
    # rows/buttons.
    for i in range(0, len(outrows) - 1):
        topscroll, topbuttons = outrows[i]
        botscroll, botbuttons = outrows[i + 1]
        for topbutton in topbuttons:
            bui.widget(edit=topbutton, down_widget=botscroll)
            if i == 0 and windowbackbutton is not None:
                bui.widget(edit=topbutton, up_widget=windowbackbutton)
        for botbutton in botbuttons:
            bui.widget(edit=botbutton, up_widget=topscroll)
        bui.widget(edit=topbuttons[0], left_widget=backbutton)
        bui.widget(edit=botbuttons[0], left_widget=backbutton)
    return subcontainer


class CloudUIWindow(bui.MainWindow):
    """UI provided by the cloud."""

    @dataclass
    class State:
        """Final state window can be set to show."""

        ui: clui.UI | None

    def __init__(
        self,
        state: State | None,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
    ):
        ui = babase.app.ui_v1

        self._state: CloudUIWindow.State | None = None

        # We want to display differently whether we're an auxiliary
        # window or not, but unfortunately that value is not yet
        # available until we're added to the main-window-stack so it
        # must be explicitly passed in.
        self._auxiliary_style = auxiliary_style

        # Calc scale and size for our backing window. For medium & large
        # ui-scale we aim for a window small enough to always be fully
        # visible on-screen and for small mode we aim for a window big
        # enough that we never see the window edges; only the window
        # texture covering the whole screen.
        uiscale = ui.uiscale
        self._width = (
            1400
            if uiscale is babase.UIScale.SMALL
            else 800 if uiscale is babase.UIScale.MEDIUM else 900
        )
        self._height = (
            1200
            if uiscale is babase.UIScale.SMALL
            else 520 if uiscale is babase.UIScale.MEDIUM else 600
        )
        self._root_scale = (
            1.5
            if uiscale is babase.UIScale.SMALL
            else 1.25 if uiscale is babase.UIScale.MEDIUM else 1.0
        )

        # Do some fancy math to calculate our visible area; this will be
        # limited by the screen size in small mode and our backing size
        # otherwise.
        screensize = babase.get_virtual_screen_size()
        self._vis_width = min(
            self._width - 100, screensize[0] / self._root_scale
        )
        self._vis_height = min(
            self._height - 70, screensize[1] / self._root_scale
        )
        self._vis_top = 0.5 * self._height + 0.5 * self._vis_height
        self._vis_left = 0.5 * self._width - 0.5 * self._vis_width

        self._scroll_width = self._vis_width
        self._scroll_left = self._vis_left + 0.5 * (
            self._vis_width - self._scroll_width
        )
        # Go with full-screen scrollable aread in small ui.
        self._scroll_height = self._vis_height - (
            -1 if uiscale is babase.UIScale.SMALL else 43
        )
        self._scroll_bottom = (
            self._vis_top
            - (-1 if uiscale is babase.UIScale.SMALL else 32)
            - self._scroll_height
        )

        # Nudge our vis area up a bit when we can see the full backing
        # (visual fudge factor).
        if uiscale is not babase.UIScale.SMALL:
            self._vis_top += 12.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility='menu_full',
                toolbar_cancel_button_style=(
                    'close' if auxiliary_style else 'back'
                ),
                scale=self._root_scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We respond to screen size changes only at small ui-scale;
            # in other cases we assume our window remains fully visible
            # always (flip to windowed mode and resize the app window to
            # confirm this).
            refresh_on_screen_size_changes=uiscale is babase.UIScale.SMALL,
        )
        # Avoid complaints if nothing is selected under us.
        bui.widget(edit=self._root_widget, allow_preserve_selection=False)

        self._subcontainer: bui.Widget | None = None

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            position=(self._scroll_left, self._scroll_bottom),
            border_opacity=0.4,
            center_small_content_horizontally=True,
            claims_left_right=True,
            simple_culling_v=10.0,
        )
        # Avoid having to deal with selecting this while its empty.
        bui.containerwidget(edit=self._scrollwidget, selectable=False)

        # With full-screen scrolling, fade content as it approaches
        # toolbars.
        if uiscale is babase.UIScale.SMALL and bool(True):
            scroll_fade_top(
                self._root_widget,
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
            )
            scroll_fade_bottom(
                self._root_widget,
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
            )

        # Title.
        self._title = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._vis_top - 20),
            size=(0, 0),
            text='',
            color=ui.title_color,
            scale=0.9 if uiscale is babase.UIScale.SMALL else 1.0,
            # Make sure we avoid overlapping meters in small mode.
            maxwidth=(130 if uiscale is babase.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )
        # Needed to display properly over scrolled content.
        bui.widget(edit=self._title, depth_range=(0.9, 1.0))

        # For small UI-scale we use the system back/close button;
        # otherwise we make our own.
        if uiscale is babase.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button: bui.Widget | None = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|close',
                scale=0.8,
                position=(self._vis_left + 2, self._vis_top - 35),
                size=(50, 50) if auxiliary_style else (60, 55),
                extra_touch_border_scale=2.0,
                button_type=None if auxiliary_style else 'backSmall',
                on_activate_call=self.main_window_back,
                autoselect=True,
                label=babase.charstr(
                    babase.SpecialChar.CLOSE
                    if auxiliary_style
                    else babase.SpecialChar.BACK
                ),
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        # Show our vis-area bounds (for debugging).
        if bool(False):
            # Skip top-left since its always overlapping back/close
            # buttons.
            if bool(False):
                bui.textwidget(
                    parent=self._root_widget,
                    position=(self._vis_left, self._vis_top),
                    size=(0, 0),
                    color=(1, 1, 1, 0.5),
                    scale=0.5,
                    text='TL',
                    h_align='left',
                    v_align='top',
                )
            bui.textwidget(
                parent=self._root_widget,
                position=(self._vis_left + self._vis_width, self._vis_top),
                size=(0, 0),
                color=(1, 1, 1, 0.5),
                scale=0.5,
                text='TR',
                h_align='right',
                v_align='top',
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(self._vis_left, self._vis_top - self._vis_height),
                size=(0, 0),
                color=(1, 1, 1, 0.5),
                scale=0.5,
                text='BL',
                h_align='left',
                v_align='bottom',
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._vis_left + self._vis_width,
                    self._vis_top - self._vis_height,
                ),
                size=(0, 0),
                scale=0.5,
                color=(1, 1, 1, 0.5),
                text='BR',
                h_align='right',
                v_align='bottom',
            )

        self._spinner: bui.Widget | None = bui.spinnerwidget(
            parent=self._root_widget,
            position=(
                self._vis_left + self._vis_width * 0.5,
                self._vis_top - self._vis_height * 0.5,
            ),
            size=48,
            style='bomb',
        )

        if state is not None:
            self._set_state(state)
        else:
            if random.random() < 0.0:
                babase.apptimer(
                    1.0, babase.WeakCallStrict(self._on_error_response)
                )
            else:
                babase.apptimer(1.0, babase.WeakCallStrict(self._on_response))

    def _on_error_response(self) -> None:
        self._set_state(self.State(None))

    def _on_response(self) -> None:
        self._set_state(
            self.State(
                clui.UI(
                    title='Testing',
                    rows=[
                        clui.Row(
                            title='First Row',
                            padding_left=5.0,
                            buttons=[
                                clui.Button(
                                    label='Test',
                                    size=(180, 200),
                                ),
                                clui.Button(
                                    label='Test2',
                                    size=(100, 100),
                                    color=(1, 0, 0),
                                    text_color=(1, 1, 1, 1),
                                    padding_right=4,
                                ),
                                clui.Button(
                                    label='TestS',
                                    size=(180, 200),
                                    scale=0.6,
                                    padding_bottom=30,
                                ),
                            ],
                        ),
                        clui.Row(
                            title='Second Row',
                            subtitle='Second row subtitle.',
                            buttons=[
                                clui.Button(
                                    size=(150, 100),
                                    decorations=[
                                        clui.Text(
                                            'DecorReallyLongTest',
                                            max_width=150 * 0.8,
                                            flatness=1.0,
                                            shadow=0.0,
                                        ),
                                    ],
                                ),
                                clui.Button(size=(150, 100)),
                                clui.Button(size=(150, 100)),
                                clui.Button(size=(150, 100)),
                                clui.Button(size=(150, 100)),
                                clui.Button(size=(150, 100)),
                            ],
                        ),
                        clui.Row(
                            buttons=[
                                clui.Button(
                                    size=(100, 100),
                                    color=(0.8, 0.8, 0.8),
                                ),
                                clui.Button(
                                    size=(100, 100),
                                    color=(0.8, 0.8, 0.8),
                                ),
                            ]
                        ),
                        clui.Row(
                            title='Last Row',
                            title_color=(0.5, 0.5, 1.0, 0.5),
                            title_flatness=1.0,
                            title_shadow=1.0,
                            subtitle='Last Row Subtitle',
                            subtitle_color=(1.0, 0.5, 1.0, 0.5),
                            subtitle_flatness=1.0,
                            subtitle_shadow=0.0,
                            center=True,
                            buttons=[
                                clui.Button(
                                    size=(100, 100),
                                    color=(0.8, 0.8, 0.8),
                                ),
                            ],
                        ),
                    ],
                )
            )
        )

    def _set_state(self, state: State) -> None:
        """Set a final state (error or page contents).

        This state may be instantly restored if the window is recreated
        (depending on cache lifespan/etc.)
        """

        assert self._state is None
        self._state = state

        ui = babase.app.ui_v1
        uiscale = ui.uiscale

        if self._spinner:
            self._spinner.delete()
            self._spinner = None

        if state.ui is None:
            bui.textwidget(
                edit=self._title,
                literal=False,  # Allow Lstr.
                text=babase.Lstr(resource='errorText'),
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._vis_left + 0.5 * self._vis_width,
                    self._vis_top - 0.5 * self._vis_height,
                ),
                size=(0, 0),
                scale=0.6,
                text=babase.Lstr(resource='store.loadErrorText'),
                h_align='center',
                v_align='center',
            )
            return

        # Ok; we've got content.
        bui.textwidget(
            edit=self._title,
            literal=True,  # Never interpret as Lstr.
            text=state.ui.title,
        )

        # Make sure there's at least one row and that all rows contain
        # at least one button. Otherwise show a 'nothing here' message.
        if not state.ui.rows or not all(row.buttons for row in state.ui.rows):
            babase.uilog.exception(
                'Got invalid cloud-ui state;'
                ' must contain at least one row'
                ' and all rows must contain buttons.'
            )
            bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._vis_left + 0.5 * self._vis_width,
                    self._vis_top - 0.5 * self._vis_height,
                ),
                size=(0, 0),
                scale=0.6,
                text=babase.Lstr(
                    translate=('serverResponses', 'There is nothing here.')
                ),
                h_align='center',
                v_align='center',
            )
            return

        uiprep = _prep_ui(state.ui, uiscale, self._scroll_width)

        bui.containerwidget(edit=self._scrollwidget, selectable=True)

        self._subcontainer = _instantiate_ui(
            uiprep,
            self._scrollwidget,
            backbutton=(
                bui.get_special_widget('back_button')
                if self._back_button is None
                else self._back_button
            ),
            windowbackbutton=self._back_button,
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # IMPORTANT - Pull values from self HERE; if we do it in the
        # lambda below it'll keep self alive which will lead to
        # 'ui-not-getting-cleaned-up' warnings and memory leaks.
        auxiliary_style = self._auxiliary_style
        state = self._state

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                state=state,
                transition=transition,
                origin_widget=origin_widget,
                auxiliary_style=auxiliary_style,
            ),
        )

    @override
    def main_window_should_preserve_selection(self) -> bool:
        return True

    @override
    def get_main_window_shared_state_id(self) -> str | None:
        return 'cloudui'
