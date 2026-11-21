# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

import weakref
from typing import TYPE_CHECKING, override

import bauiv1 as bui
from bauiv1 import _commonassets

from bauiv1lib.docui._host import DocUIPageHost
from bauiv1lib.docui._backbutton import back_button_geometry
from bauiv1lib.docui._frame import window_frames
from bauiv1lib.docui._layout import (
    default_scroll_edge_style,
    resizes_with_screen,
    title_lift,
    window_backing_art,
)
from bauiv1lib.docui._panes import (
    page_geometries,
    scroll_widget_rect,
    apply_edge_fades,
    viewer_pane_rect,
    window_edge_fades,
)
from bauiv1lib.docui._windowparts import (
    ViewerPane,
    show_layout_bounds,
    show_vis_area_bounds,
)
from bauiv1lib.docui._debugdraw import DebugDrawKind, debug_draw_enabled
from bauiv1lib.docui._pagelook import DEFAULT_LOOK, apply_frame_colors
from bauiv1lib.docui._windowoptions import WindowOptions
from bauiv1lib.docui._windowstate import DocUIMainWindowState
from bauiv1lib.docui._scrollrestore import (
    page_scrollers,
    capture_scroll,
    apply_scroll,
    containing_scrollers,
)

if TYPE_CHECKING:
    from typing import Any, Callable

    import bacommon.docui.v2
    from bacommon.docui import DocUIRequest
    from bauiv1lib.docui._controller import DocUIController
    from bauiv1lib.docui._popupwindow import DocUIPopupWindow
    from bauiv1lib.docui._panes import PageGeometries, PaneMode
    from bauiv1lib.docui._scrollrestore import (
        ScrollSnapshot,
        ScrollRestoreMode,
    )
    from bauiv1lib.docui import prep

# Our scroll snapshot's key in a window's shared state.
_SCROLL_STATE_KEY = 'docui_scroll'


class DocUIWindow(bui.MainWindow, DocUIPageHost):
    """Window showing doc-ui content."""

    def __init__(
        self,
        controller: DocUIController,
        request: DocUIRequest,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
        uiopenstateid: str | None = None,
        suppress_win_extra_type_warning: bool = False,
        has_had_response: bool = False,
        options: WindowOptions | None = None,
        pane: PaneMode | None = None,
    ):
        """``pane`` is the viewer pane to start out with, for a window
        coming back (back-navigation, a reflow) to the page it showed;
        a fresh window has none until a page asks for one.
        """
        import bacommon.docui.v2 as dui2

        ui = bui.app.ui_v1

        self._uiopenstate = (
            None if uiopenstateid is None else bui.UIOpenState(uiopenstateid)
        )

        DocUIPageHost.__init__(self, controller, request)

        self._suppress_win_extra_type_warning = suppress_win_extra_type_warning

        #: Path of the page our ui was last built for; a rebuild for a
        #: different path starts scrolled to the top (see
        #: instantiate_ui()).
        self._shown_path: str | None = None

        # The popup over us, if any (it keeps itself alive; see
        # DocUIPopupWindow).
        self._popup: weakref.ref[DocUIPopupWindow] | None = None

        #: Where this window was scrolled to when last navigated away
        #: from, if it is coming back; applied on our first build.
        self._returning_scroll: ScrollSnapshot | None = None

        #: Whether we're coming back via an auto-recreate (a screen-size
        #: or ui-scale reflow) rather than back-navigation; see
        #: instantiate_ui().
        self._returning_from_recreate = False

        #: Scrolling widgets our last build put back exactly where they
        #: were (see _apply_scroll()); a restored selection inside only
        #: these is already where it was, so needn't be scrolled to.
        self._restored_scrollers: list[bui.Widget] = []

        self._has_had_response: bool = has_had_response

        # Runs the controller's page-state poll, if it wants one.
        self._state_poll_timer: bui.AppTimer | None = None

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

        # What we were asked for (kept as is, so a rebuilt window asks
        # for the same) and what that comes to.
        self._options = WindowOptions() if options is None else options
        self._layout = (
            dui2.WindowLayout.WIDE_TALL
            if self._options.layout is None
            else self._options.layout
        )
        self._scroll_edge_style = (
            default_scroll_edge_style(self._layout)
            if self._options.scroll_edge_style is None
            else self._options.scroll_edge_style
        )
        # The look of the page we show (each page may set its own
        # insets, which our scroll-area fades suit); the default until
        # one arrives.
        self._page_look = DEFAULT_LOOK
        # Our frame for each viewer pane our pages may ask for (none,
        # or one on either side); the window and visible area are the
        # same in all, only the scroll area and pane differ. Each page
        # picks one (see instantiate_ui()); until one arrives we have
        # no pane, unless we're coming back with one.
        self._frames = window_frames(
            self._layout,
            uiscale,
            self._scroll_edge_style,
            close_style=auxiliary_style,
        )
        self._pane_mode = pane
        frame = self._frames[None if pane is None else pane.side]
        self._vis_left, self._vis_top = frame.vis_left, frame.vis_top
        self._vis_width, self._vis_height = frame.vis_width, frame.vis_height
        self._frame = frame

        toolbar_visibility = controller.get_window_toolbar_visibility()
        super().__init__(
            # Laid out cleanly: our bounds are our backing art's solid
            # part, sized to what must sit on it (see window_frames()).
            root_widget=bui.containerwidget(
                size=(frame.width, frame.height),
                toolbar_visibility=toolbar_visibility,
                toolbar_cancel_button_style=(
                    'close' if auxiliary_style else 'back'
                ),
                scale=frame.root_scale,
                stack_offset=frame.stack_offset,
                clean_layout=True,
                background_art=window_backing_art(self._layout, uiscale),
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We rebuild for screen size changes when our size depends on
            # the screen's (always at small ui-scale); otherwise we assume
            # our window remains fully visible always.
            refresh_on_screen_size_changes=resizes_with_screen(
                self._layout, uiscale
            ),
        )
        # Avoid complaints if nothing is selected under us.
        bui.widget(edit=self._root_widget, allow_preserve_selection=False)

        # Our frame's colors (before our back button is made our cancel
        # button, though it'd pick them up either way).
        apply_frame_colors(
            self._root_widget,
            self._options.background_color,
            self._options.cancel_button_color,
        )

        self._subcontainer: bui.Widget | None = None

        self._uiscale = uiscale
        self._toolbar_visibility = toolbar_visibility
        self._viewer_pane: ViewerPane | None = None
        self._layout_bounds: list[bui.Widget] = []

        # Created before our scroll widget, as the two can overlap (see
        # _create_viewer_pane()): presses go to the last-created widget
        # that wants them, and the page should win there.
        if pane is not None:
            self._viewer_pane = self._create_viewer_pane(pane, None)

        rect = scroll_widget_rect(self._frame)
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=True,  # Will turn off once we have UI.
            size=rect[2:],
            position=rect[:2],
            border_opacity=0.4,
            # A border around content that doesn't scroll is just
            # clutter (the audio settings page, say).
            hide_border_when_fits=True,
            center_small_content_horizontally=True,
            # A bar fading in over content (none set aside for one), and
            # content laid out against our exact bounds.
            fading_scrollbar=True,
            clean_layout=True,
            claims_left_right=True,
            # Selection-preserving needs an id on every selectable
            # widget; without one, landing here on window save warns and
            # loses the user's place on return.
            id=f'{self.main_window_id_prefix}|scroll',
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)

        self._style_scroll_edges()

        # Our back button's geometry (medium/large ui-scale); the title
        # is centered vertically on it.
        back_scale, back_size, back_offset = back_button_geometry(
            self._layout, self._scroll_edge_style, close_style=auxiliary_style
        )
        back_bottom = (
            self._vis_top + back_offset[1] + title_lift(self._layout, uiscale)
        )
        title_y = (
            self._vis_top - 20
            if uiscale is bui.UIScale.SMALL
            else back_bottom + back_size[1] * back_scale * 0.5
        )

        # Title.
        self._title = bui.textwidget(
            parent=self._root_widget,
            # Centered on the window, panes or not; the title belongs to
            # the window as a whole.
            position=(frame.vis_center[0], title_y),
            size=(0, 0),
            text='',
            color=ui.title_color,
            scale=0.9 if uiscale is bui.UIScale.SMALL else 1.0,
            # Make sure we avoid overlapping meters in small mode.
            maxwidth=(130 if uiscale is bui.UIScale.SMALL else 200),
            h_align='center',
            v_align='center',
        )
        # Needed to display properly over scrolled content.
        bui.widget(edit=self._title, depth_range=(0.9, 1.0))

        # For small UI-scale we use the system back/close button;
        # otherwise we make our own.
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button: bui.Widget | None = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|close',
                scale=back_scale,
                position=(self._vis_left + back_offset[0], back_bottom),
                size=back_size,
                extra_touch_border_scale=2.0,
                button_type=None if auxiliary_style else 'backSmall',
                clean_layout=True,
                on_activate_call=self.main_window_back,
                autoselect=True,
                label=(
                    bui.SpecialChar.CLOSE
                    if auxiliary_style
                    else bui.SpecialChar.BACK
                ).value,
            )
            # In front of anything scrolled up behind it (a fading
            # scroll area reaches up there).
            bui.widget(edit=self._back_button, depth_range=(0.9, 1.0))
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        self._show_debug_bounds()

        if not suppress_win_extra_type_warning:
            bui.pushcall(bui.WeakCallStrict(self._sanity_check_win_extra_type))

    def _edge_fades(self) -> tuple[float, float, float, float] | None:
        return window_edge_fades(
            self._frame,
            uiscale=self._uiscale,
            toolbar_visibility=self._toolbar_visibility,
            look=self._page_look,
        )

    def _style_scroll_edges(self) -> None:
        # (Set up again whenever our frame or our page's insets change.)
        apply_edge_fades(self._scrollwidget, self._edge_fades())

    def _show_debug_bounds(self) -> None:
        # Our vis-area corners (flip on by hand when needed).
        if bool(False):
            show_vis_area_bounds(
                self._root_widget,
                self._vis_left,
                self._vis_top,
                self._vis_width,
                self._vis_height,
            )
        self._show_layout_bounds()

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
            pane_rect=(
                None
                if self._viewer_pane is None
                else viewer_pane_rect(self._frame, self._uiscale)
            ),
        )

    def _create_viewer_pane(
        self, pane: PaneMode, transition_delay: float | None
    ) -> ViewerPane:
        """Create a viewer pane for our current frame.

        It sits alongside our scroll area and spans its height, its
        edges nudged per ui-scale (see ``viewer_insets_v()``; in small
        ui that clears the toolbars the scroll area runs under). With a
        ``transition_delay`` it fades in rather than just appearing.
        """
        import bacommon.docui.v2 as dui2

        rect = viewer_pane_rect(self._frame, self._uiscale)
        return ViewerPane(
            self.controller,
            self._root_widget,
            position=rect[:2],
            size=rect[2:],
            framed=pane.frame_style is dui2.ViewerFrameStyle.DEFAULT,
            transition_delay=transition_delay,
        )

    def _set_pane_mode(
        self, pane: PaneMode | None, transition_delay: float | None
    ) -> None:
        """Lay ourself out for a page's viewer pane (or none).

        Our scroll area moves and resizes to suit, and any pane we had
        goes; a new one is made where the page wants it. (A live viewer
        behind the pane survives that, being kept by key.)
        """
        if pane == self._pane_mode:
            return
        self._pane_mode = pane
        self._frame = self._frames[None if pane is None else pane.side]
        if self._viewer_pane is not None:
            self._viewer_pane.widget.delete()
            self._viewer_pane = None
        if pane is not None:
            self._viewer_pane = self._create_viewer_pane(pane, transition_delay)
        rect = scroll_widget_rect(self._frame)
        bui.scrollwidget(
            edit=self._scrollwidget, position=rect[:2], size=rect[2:]
        )
        self._style_scroll_edges()
        self._show_layout_bounds()

    @override
    def page_geometries(self) -> PageGeometries:
        """What our pages lay out against, for each pane they may get.

        :meta private:
        """
        return page_geometries(self._layout, self._frames)

    @override
    def window_describe(self) -> str:
        import bacommon.docui.v2 as dui2

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

    def _sanity_check_win_extra_type(self) -> None:
        # There will be lots of windows with this same type, so we really
        # need the user to provide extra-type-ids so our logic can tell
        # all of us apart for navigation purposes.
        if not self.main_window_extra_type_id:
            bui.uilog.warning(
                '%s created by %s was not assigned an extra-type-id.'
                ' Always pass a "win_extra_type_id" when calling'
                ' `auxiliary_window_activate()` with a DocUIWindow.',
                type(self).__name__,
                type(self.controller),
            )

    @override
    def on_main_window_close(self) -> None:
        # Never let a pause outlive us (we may close mid-request).
        self._release_ui_pause()

        # Popups are transient: they go when we do.
        self.dismiss_popup()
        super().on_main_window_close()

    @property
    @override
    def host_id_prefix(self) -> str:
        return self.main_window_id_prefix

    @override
    def host_root_widget(self) -> bui.Widget:
        return self._root_widget

    @override
    def host_page_center(self) -> tuple[float, float]:
        return (
            self._vis_left + self._vis_width * 0.5,
            self._vis_top - self._vis_height * 0.5,
        )

    @override
    def host_main_window(self) -> DocUIWindow | None:
        return self

    @override
    def save_shared_state(self) -> None:
        self.main_window_save_shared_state()

    @override
    def _on_response_set(self) -> None:
        self._has_had_response = True

    @property
    def popup(self) -> DocUIPopupWindow | None:
        """The popup currently over us, if any.

        :meta private:
        """
        popup = None if self._popup is None else self._popup()
        if popup is None or not popup.alive:
            return None
        return popup

    def set_popup(self, popup: DocUIPopupWindow | None) -> None:
        """Note the popup now over us (dismissing any other).

        :meta private:
        """
        current = self.popup
        if current is not None and current is not popup:
            current.dismiss()
        self._popup = None if popup is None else weakref.ref(popup)

    def dismiss_popup(self) -> None:
        """Close any popup over us.

        :meta private:
        """
        self.set_popup(None)

    @override
    def instantiate_ui(self, pageprep: prep.PagePrep) -> None:
        """Replace any current ui with provided prepped one.

        :meta private:
        """
        import bacommon.docui.v2 as dui2

        from bauiv1lib.docui.prep._instantiate import instantiate_page_prep

        assert bui.in_logic_thread()

        # Set title (a native language-string handle).
        bui.textwidget(
            edit=self._title,
            literal=True,
            text=pageprep.title,
        )
        # This page's look; our fades suit its insets.
        old_look = self._page_look
        self._page_look = pageprep.look
        if pageprep.look.fade_key() != old_look.fade_key():
            self._style_scroll_edges()

        # Lay ourself out for the viewer pane (or none) this page was
        # prepped beside; a new pane comes in along with the rows.
        self._set_pane_mode(pageprep.pane, None if pageprep.immediate else 0.1)
        if pageprep.look != old_look:
            self._show_layout_bounds()
        if self._viewer_pane is not None:
            self._viewer_pane.apply_response(self._last_response)

        # Note where the outgoing ui was scrolled to, so a rebuild of the
        # same page can put everything back (see _apply_scroll()).
        outgoing_scroll = self._capture_scroll()
        path = (
            self._request.path
            if isinstance(self._request, dui2.Request)
            else None
        )
        first_build = self._shown_path is None
        same_page = not first_build and path == self._shown_path
        self._shown_path = path

        # Clear any existing children.
        self.anim_targets.clear()
        self.row_bounds.clear()
        for child in self._scrollwidget.get_children():
            child.delete()

        if pageprep.rows:
            # Stop showing scroll-widget highlights now that we've got
            # child stuff to be highlighted.
            bui.scrollwidget(
                edit=self._scrollwidget,
                highlight=False,
                simple_culling_v=pageprep.simple_culling_v,
                center_small_content=(pageprep.center_vertically),
                scrollbar_visible=pageprep.show_scrollbar,
            )
            self._subcontainer = instantiate_page_prep(
                pageprep,
                rootwidget=self._root_widget,
                scrollwidget=self._scrollwidget,
                backbutton=(
                    bui.get_special_widget('back_button')
                    if self._back_button is None
                    else self._back_button
                ),
                windowbackbutton=self._back_button,
                window=self,
            )
            if first_build:
                # A window coming back (back-navigation) returns to where
                # it was left, if its layout is unchanged. One recreated
                # to reflow is the same page rebuilt for a new layout, so
                # its page holds position through the size change.
                self._apply_scroll(
                    self._returning_scroll,
                    mode=(
                        'reflow'
                        if self._returning_from_recreate
                        else 'returning'
                    ),
                )
            else:
                self._apply_scroll(
                    outgoing_scroll,
                    mode='same_page' if same_page else 'new_page',
                )
            # The page's selected button, scrolled into view, unless what
            # holds it was just restored to where it was left (returning
            # to a page keeps its scroll; see PagePrep.selected_widget_id).
            if pageprep.selected_widget_id is not None:
                selected = bui.widget_by_id(pageprep.selected_widget_id)
                if (
                    selected
                    and self.main_window_should_scroll_to_restored_selection(
                        selected
                    )
                ):
                    selected.scroll_into_view(animate=False)
        else:
            # No child stuff to show so let the scroll-widget highlight.
            bui.scrollwidget(
                edit=self._scrollwidget,
                highlight=True,
                simple_culling_v=0.0,
                center_small_content=True,
                scrollbar_visible=True,
            )
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

        # Most of our UI won't exist until this point so we need to
        # explicitly restore state for selection restore to work.
        #
        # Note to self: perhaps we should *not* do this if significant
        # time has passed since the window was made or if input commands
        # have happened.
        #
        # Any scroll to the restored selection snaps (the default), even
        # when the page itself scales in: individual widgets popping in
        # reads as intentional, the whole page scrolling reads as
        # broken. Our scroll-widget has already drawn by now (it was up
        # with a spinner while this page was fetched and prepped), so
        # its own not-yet-drawn snap can't cover this case.
        self.main_window_restore_shared_state()

        # (Re)start the controller's state poll for this page.
        interval = self.controller.get_page_state_poll_interval()
        self._state_poll_timer = (
            None
            if interval is None or self.pagestate.values is None
            else bui.AppTimer(
                interval,
                bui.WeakCallStrict(self._poll_page_state),
                repeat=True,
            )
        )

    def _poll_page_state(self) -> None:
        """Push anything the controller's poll says has changed."""
        # A request in flight will bring a page with fresh values.
        if self._locked or self.pagestate.values is None:
            return
        values = self.controller.poll_page_state(self)
        if not values:
            return
        current = self.pagestate.values
        changed = {
            key: val
            for key, val in values.items()
            if key in current and current[key] != val
        }
        if changed:
            self.set_page_state_values(changed, push=True)

    def _scrollers(self) -> dict[str, bui.Widget]:
        # (see _scrollrestore.page_scrollers()).
        return page_scrollers(self._scrollwidget, self._subcontainer)

    def _capture_scroll(self) -> ScrollSnapshot:
        return capture_scroll(self._scrollers())

    def _apply_scroll(
        self, saved: ScrollSnapshot | None, *, mode: ScrollRestoreMode
    ) -> None:
        # (see _scrollrestore.apply_scroll()).
        self._restored_scrollers = apply_scroll(
            self._scrollers(), saved, mode=mode
        )

    @override
    def main_window_should_scroll_to_restored_selection(
        self, widget: bui.Widget
    ) -> bool:
        # Only needed if something between it and us wasn't restored
        # exactly (or it's somewhere we don't manage).
        containing = containing_scrollers(
            self._scrollers(), self._subcontainer, widget
        )
        if not containing:
            return True
        return not all(
            any(scroller is done for done in self._restored_scrollers)
            for scroller in containing
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        assert bui.in_logic_thread()

        # IMPORTANT - Pull values from self HERE; if we do it in the
        # lambda below it'll keep self alive which will lead to
        # 'ui-not-getting-cleaned-up' warnings and memory leaks.
        auxiliary_style = self._auxiliary_style
        controller = self.controller
        last_response = self._last_response
        has_had_response = self._has_had_response
        options = self._options
        pane = self._pane_mode
        uiopenstateid = (
            None if self._uiopenstate is None else self._uiopenstate.stateid
        )
        suppress_win_extra_type_warning = self._suppress_win_extra_type_warning

        return DocUIMainWindowState(
            create_call=(
                lambda transition, origin_widget, req: controller.restore(
                    cls(
                        controller=controller,
                        request=req,
                        transition=transition,
                        origin_widget=origin_widget,
                        auxiliary_style=auxiliary_style,
                        uiopenstateid=uiopenstateid,
                        suppress_win_extra_type_warning=(
                            suppress_win_extra_type_warning
                        ),
                        has_had_response=has_had_response,
                        options=options,
                        pane=pane,
                    ),
                    last_response=last_response,
                    has_had_response=has_had_response,
                )
            ),
            request=self._request,
            uiopenstate=self._uiopenstate,
            controller_type=type(controller),
        )

    @override
    def main_window_do_save_shared_state(self, state: dict) -> None:
        # Where we were scrolled to, for when navigation brings us back
        # (see _apply_scroll()).
        state[_SCROLL_STATE_KEY] = self._capture_scroll()

        # Give our controller a stab at this.
        self.controller.save_window_shared_state(self, state)

    @override
    def main_window_do_restore_shared_state(self, state: dict) -> None:
        # This runs as we're created, before our ui exists; hold onto
        # where we were left for our first build to apply. (It runs again
        # after each build, when there's nothing further to do with it.)
        if self._shown_path is None:
            saved = state.get(_SCROLL_STATE_KEY)
            self._returning_scroll = saved if isinstance(saved, dict) else None
            self._returning_from_recreate = (
                bui.app.ui_v1.main_window_recreate_in_progress
            )

        # Give our controller a stab at this.
        self.controller.restore_window_shared_state(self, state)

    @override
    def main_window_should_preserve_selection(self) -> bool:
        return True

    @override
    def get_main_window_shared_state_id(self) -> str | None:
        base_id = (
            self._request_state_id
            if self._last_response_shared_state_id is None
            else self._last_response_shared_state_id
        )

        # Each controller has its own unique domain, so include that in
        # the id.
        ctp = type(self.controller)
        out = f'{ctp.__module__}.{ctp.__qualname__}:{base_id}'
        return out
