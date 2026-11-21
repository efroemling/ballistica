# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui popup windows: a page shown over another without leaving it."""

import weakref
from typing import TYPE_CHECKING, override

import bacommon.docui.v2 as dui2
import bauiv1 as bui
from bauiv1 import _commonassets

from bauiv1lib.docui._frame import popup_frame
from bauiv1lib.docui._host import DocUIPageHost
from bauiv1lib.docui._layout import (
    POPUP_EDGE_MARGIN,
    POPUP_CLOSE_BUTTON,
    POPUP_CLOSE_BUTTON_INSET,
    POPUP_TITLE_BAND_HEIGHT,
)
from bauiv1lib.docui._debugdraw import DebugDrawKind, debug_draw_enabled
from bauiv1lib.docui._pagelook import DEFAULT_LOOK, apply_frame_colors
from bauiv1lib.docui._panes import (
    PageGeometries,
    ScrollGeometry,
    apply_edge_fades,
    edge_fades,
    scroll_widget_rect,
)
from bauiv1lib.docui._windowparts import show_layout_bounds

if TYPE_CHECKING:
    from bacommon.docui import DocUIRequest
    from bauiv1lib.docui._controller import DocUIController
    from bauiv1lib.docui._frame import WindowFrame
    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui import prep

#: How often a popup checks whether it should go away (see
#: DocUIPopupWindow._check_transient()).
_TRANSIENT_CHECK_INTERVAL = 0.25


def _placement(
    frame: WindowFrame, anchor: tuple[float, float]
) -> tuple[float, tuple[float, float]]:
    """Where a popup goes: (scale, stack offset).

    Centered on ``anchor`` (screen units from the screen's center),
    then moved as needed to lie entirely within the virtual bounds less
    POPUP_EDGE_MARGIN at each edge (always: so the popup is wholly on
    screen and there's always room outside it to press to dismiss it);
    our container lays out cleanly, so that keeps everything on solid
    art on screen. Frames are already sized to fit that area (see
    ``popup_frame()``); should one not (the minimum size on a tiny
    screen, say), it shrinks to.
    """
    vwidth, vheight = bui.get_virtual_screen_size()
    room_w = max(1.0, vwidth - 2.0 * POPUP_EDGE_MARGIN[0])
    room_h = max(1.0, vheight - 2.0 * POPUP_EDGE_MARGIN[1])
    scale = frame.root_scale
    fit = min(
        1.0, room_w / (frame.width * scale), room_h / (frame.height * scale)
    )
    scale *= fit
    xlimit = 0.5 * (room_w - frame.width * scale)
    ylimit = 0.5 * (room_h - frame.height * scale)
    x = max(-xlimit, min(xlimit, anchor[0]))
    y = max(-ylimit, min(ylimit, anchor[1]))
    return scale, (x, y)


class DocUIPopupWindow(bui.Window, DocUIPageHost):
    """A doc-ui page shown in a popup over a doc-ui window's page.

    The page under it (its *parent*) stays as it is. Popups are
    transient: never saved or restored with their window, and closed by
    anything that would rebuild it (a screen-size, ui-scale or language
    change, the window going away). They keep themselves alive through
    their widgets' callbacks, as long as those exist.

    Created by the controller for a :class:`bacommon.docui.v2.Popup`
    action; see :meth:`DocUIController.run_action()
    <bauiv1lib.docui.DocUIController.run_action>`.
    """

    def __init__(
        self,
        controller: DocUIController,
        request: DocUIRequest,
        *,
        parent: DocUIWindow,
        action: dui2.Popup,
        origin_widget: bui.Widget | None,
        opener_widget_id: str | None,
    ) -> None:
        DocUIPageHost.__init__(self, controller, request)

        self._parent = weakref.ref(parent)

        #: Id of the widget (in our parent's page) that opened us, for
        #: actions we run on the parent on our way out; it may be gone
        #: by then (the parent's page refreshed under us, say).
        self.opener_widget_id = opener_widget_id

        self._closing = False
        self._idprefix = bui.app.ui_v1.new_id_prefix(
            type(self).__name__.lower()
        )

        uiscale = bui.app.ui_v1.uiscale

        # Our frame colors: our link's, else the popup look's green.
        self._frame_colors = (
            (
                dui2.POPUP_BACKGROUND_COLOR
                if action.background_color is None
                else action.background_color
            ),
            (
                dui2.POPUP_BACKGROUND_COLOR
                if action.cancel_button_color is None
                else action.cancel_button_color
            ),
        )
        # The look of the page we show (its insets suit our fades); the
        # default until one arrives.
        self._page_look = DEFAULT_LOOK
        self._layout_bounds: list[bui.Widget] = []

        title_band = action.show_title or action.show_close_button
        frame = popup_frame(
            action.size,
            uiscale,
            bui.get_virtual_screen_size(),
            title_band=title_band,
            scroll_edge_style=action.scroll_edge_style,
        )
        self._frame = frame

        anchor = (
            (0.0, 0.0)
            if origin_widget is None
            else origin_widget.get_screen_space_center()
        )
        scale, stack_offset = _placement(frame, anchor)

        # The world we were built for; any change to it closes us (see
        # _check_transient()).
        self._built_for = (
            uiscale,
            bui.get_virtual_screen_size(),
            bui.app.locale.current_locale,
        )

        root_widget = bui.containerwidget(
            parent=bui.get_special_widget('overlay_stack'),
            size=(frame.width, frame.height),
            scale=scale,
            stack_offset=stack_offset,
            scale_origin_stack_offset=anchor,
            transition='in_scale',
            toolbar_visibility='inherit',
            # Laid out cleanly: our bounds are our backing art's solid
            # part, which is what we keep on screen (see _placement()).
            clean_layout=True,
            # (These callbacks are what keep us alive.)
            claim_outside_clicks=True,
            on_outside_click_call=self._on_cancel,
            on_cancel_call=self._on_cancel,
            darken_behind=action.dim_background,
        )
        # Unlike most windows we don't hold off main-window recreates;
        # we let them happen and go away with the window they replace.
        bui.Window.__init__(
            self, root_widget, prevent_main_window_auto_recreate=False
        )
        apply_frame_colors(root_widget, *self._frame_colors)

        rect = scroll_widget_rect(frame)
        self._scrollwidget = bui.scrollwidget(
            parent=root_widget,
            highlight=False,
            size=rect[2:],
            position=rect[:2],
            border_opacity=0.4,
            hide_border_when_fits=True,
            center_small_content_horizontally=True,
            fading_scrollbar=True,
            clean_layout=True,
            claims_left_right=True,
            id=f'{self._idprefix}|scroll',
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)
        self._style_scroll_edges()
        self._show_layout_bounds()
        self._subcontainer: bui.Widget | None = None

        band_center_y = frame.height - 0.5 * POPUP_TITLE_BAND_HEIGHT
        close_scale, close_size = POPUP_CLOSE_BUTTON
        close_width = close_size[0] * close_scale

        self._title: bui.Widget | None = None
        if action.show_title:
            self._title = bui.textwidget(
                parent=root_widget,
                position=(0.5 * frame.width, band_center_y),
                size=(0, 0),
                text='',
                color=bui.app.ui_v1.title_color,
                # Clear of the close button at either end.
                maxwidth=frame.width
                - 2.0 * (POPUP_CLOSE_BUTTON_INSET + close_width),
                h_align='center',
                v_align='center',
            )
            # Over anything scrolled up behind it.
            bui.widget(edit=self._title, depth_range=(0.9, 1.0))

        self._close_button: bui.Widget | None = None
        if action.show_close_button:
            self._close_button = bui.buttonwidget(
                parent=root_widget,
                id=f'{self._idprefix}|close',
                scale=close_scale,
                position=(
                    POPUP_CLOSE_BUTTON_INSET,
                    band_center_y - 0.5 * close_size[1] * close_scale,
                ),
                size=close_size,
                extra_touch_border_scale=2.0,
                button_type=None,
                # Art drawn within our bounds (as page buttons), so the
                # title can run right up to them.
                clean_layout=True,
                autoselect=True,
                # Closing makes its own sound (see _on_cancel()).
                enable_sound=False,
                label=bui.SpecialChar.CLOSE.value,
                on_activate_call=self._on_cancel,
            )
            bui.widget(edit=self._close_button, depth_range=(0.9, 1.0))
            bui.containerwidget(
                edit=root_widget, cancel_button=self._close_button
            )

        self._transient_timer: bui.AppTimer | None = bui.AppTimer(
            _TRANSIENT_CHECK_INTERVAL,
            bui.WeakCallStrict(self._check_transient),
            repeat=True,
        )

    def _edge_fades(self) -> tuple[float, float, float, float] | None:
        return edge_fades(self._frame, self._page_look)

    def _style_scroll_edges(self) -> None:
        # (Set up again whenever our page's insets change.)
        apply_edge_fades(self._scrollwidget, self._edge_fades())

    def _show_layout_bounds(self) -> None:
        for widget in self._layout_bounds:
            widget.delete()
        self._layout_bounds = []
        if not debug_draw_enabled(DebugDrawKind.LAYOUT):
            return
        look = self._page_look
        self._layout_bounds = show_layout_bounds(
            self._root_widget,
            self._frame,
            insets=(look.h_inset, look.v_inset),
            fades=self._edge_fades(),
        )

    @override
    def window_describe(self) -> str:
        request = self._request
        where = (
            repr(request.path)
            if isinstance(request, dui2.Request)
            else type(request).__name__
        )
        return (
            f'{type(self).__name__}'
            f'[{type(self.controller).__name__} {where}]'
        )

    @property
    def parent(self) -> DocUIWindow | None:
        """The window we are over, if it is still around."""
        return self._parent()

    @property
    def alive(self) -> bool:
        """Whether we're up (not closed or on our way out)."""
        return (
            not self._closing
            and bool(self._root_widget)
            and not self._root_widget.transitioning_out
        )

    def dismiss(self) -> None:
        """Close (if we haven't yet)."""
        if self._closing:
            return
        self._closing = True
        self._transient_timer = None
        self._release_ui_pause()
        # (Our parent's popup property stops naming us as of now.)
        if self._root_widget and not self._root_widget.transitioning_out:
            bui.containerwidget(edit=self._root_widget, transition='out_scale')

    def _on_cancel(self) -> None:
        # A press outside us, back/escape, or our close button.
        if self._closing:
            return
        bui.play_swish()
        self.dismiss()

    def _check_transient(self) -> None:
        """Go away if what we were opened over has changed."""
        parent = self._parent()
        if (
            parent is None
            or parent.popup is not self
            or not parent.main_window_has_control()
            or self._built_for
            != (
                bui.app.ui_v1.uiscale,
                bui.get_virtual_screen_size(),
                bui.app.locale.current_locale,
            )
        ):
            self.dismiss()

    # -- DocUIPageHost. -----------------------------------------------------

    @property
    @override
    def host_id_prefix(self) -> str:
        return self._idprefix

    @override
    def host_root_widget(self) -> bui.Widget:
        return self._root_widget

    @override
    def host_page_center(self) -> tuple[float, float]:
        f = self._frame
        return (
            f.content_left + 0.5 * f.content_width,
            f.content_bottom + 0.5 * f.content_height,
        )

    @override
    def host_main_window(self) -> DocUIWindow | None:
        return self._parent()

    @override
    def host_alive(self) -> bool:
        return self.alive

    @override
    def page_geometries(self) -> PageGeometries:
        geometry = ScrollGeometry.from_frame(self._frame)
        # (No layout of ours has room for a viewer pane.)
        return PageGeometries(
            layout=dui2.WindowLayout.WIDE,
            no_pane=geometry,
            left_pane=geometry,
            right_pane=geometry,
        )

    @override
    def parent_state_for_requests(self) -> dict | None:
        parent = self._parent()
        if parent is None:
            return None
        parent.pull_page_state_values()
        return parent.page_state

    @override
    def instantiate_ui(self, pageprep: prep.PagePrep) -> None:
        from bauiv1lib.docui.prep._instantiate import instantiate_page_prep

        assert bui.in_logic_thread()

        if self._title is not None:
            bui.textwidget(edit=self._title, literal=True, text=pageprep.title)

        # This page's look; our fades suit its insets.
        old_look = self._page_look
        self._page_look = pageprep.look
        if pageprep.look.fade_key() != old_look.fade_key():
            self._style_scroll_edges()
        if pageprep.look != old_look:
            self._show_layout_bounds()

        self.anim_targets.clear()
        self.row_bounds.clear()
        for child in self._scrollwidget.get_children():
            child.delete()

        if pageprep.rows:
            bui.scrollwidget(
                edit=self._scrollwidget,
                simple_culling_v=pageprep.simple_culling_v,
                center_small_content=pageprep.center_vertically,
                scrollbar_visible=pageprep.show_scrollbar,
            )
            self._subcontainer = instantiate_page_prep(
                pageprep,
                rootwidget=self._root_widget,
                scrollwidget=self._scrollwidget,
                backbutton=self._close_button,
                windowbackbutton=self._close_button,
                window=self,
            )
        else:
            self._subcontainer = None
            bui.textwidget(
                parent=self._scrollwidget,
                h_align='center',
                v_align='center',
                text=_commonassets.strings.status.nothing_here,
                scale=0.75,
                color=(1, 1, 1, 0.5),
                size=(0, 0),
            )

        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )
