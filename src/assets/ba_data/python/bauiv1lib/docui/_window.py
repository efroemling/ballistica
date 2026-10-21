# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

import copy
from functools import partial
from dataclasses import replace
from typing import TYPE_CHECKING, override, assert_never

import bauiv1 as bui
from bauiv1 import _commonassets

from bacommon.docui import DocUIRequestTypeID, DocUIResponseTypeID
from bauiv1lib.docui._animtargets import DocUIAnimTargets
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
    style_scroll_edges,
    viewer_insets_v,
)
from bauiv1lib.docui._windowparts import (
    ViewerPane,
    make_busy_spinner,
    show_scroll_bounds,
    show_vis_area_bounds,
)
from bauiv1lib.docui._debugdraw import DebugDrawKind, debug_draw_enabled
from bauiv1lib.docui._pagestate import DocUIPageState
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
    from bacommon.docui import DocUIRequest, DocUIResponse
    from bauiv1lib.docui._controller import DocUIController
    from bauiv1lib.docui._panes import PageGeometries, PaneMode
    from bauiv1lib.docui._scrollrestore import (
        ScrollSnapshot,
        ScrollRestoreMode,
    )
    from bauiv1lib.docui import prep

# Our scroll snapshot's key in a window's shared state.
_SCROLL_STATE_KEY = 'docui_scroll'


def _drop(pause: bui.RootUIUpdatePause) -> None:
    """Release a root-ui pause (by letting go of the last reference)."""
    del pause


class DocUIWindow(bui.MainWindow):
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

        self._locked = False

        # Held while we're locked (a request in flight); see lock_ui().
        self._ui_pause: bui.RootUIUpdatePause | None = None

        # Note: our windows and states both hold strong references to
        # the controller, so we need to make sure the opposite is not
        # true to avoid cycles.
        self.controller = controller

        self._suppress_win_extra_type_warning = suppress_win_extra_type_warning
        self._request = request
        self._request_state_id = self._default_state_id(request)

        #: Path of the page our ui was last built for; a rebuild for a
        #: different path starts scrolled to the top (see
        #: instantiate_ui()).
        self._shown_path: str | None = None

        #: Our page's client-effect-animatable widgets.
        self.anim_targets = DocUIAnimTargets()

        #: Our page's navigable rows, each as its selectable widgets
        #: with its vertical extent (top, bottom) in the page, as doc-ui
        #: lays it out. Selection should keep that extent inside our
        #: scroll bounds (see DebugDrawKind.SCROLL_BOUNDS); for checks.
        self.row_bounds: list[tuple[list[bui.Widget], float, float]] = []

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

        # Runs the controller's page-state poll, if it wants one.
        self._state_poll_timer: bui.AppTimer | None = None

        self._last_response: DocUIResponse | None = None
        self._last_response_success: bool = False
        self._last_response_shared_state_id: str | None = None
        self._has_had_response: bool = has_had_response

        #: Live values for the page we are showing (its input rows
        #: edit these).
        #:
        #: :meta private:
        self.pagestate = DocUIPageState()

        # Where to show the busy-spinner for requests fired by
        # particular widgets, for those where their center won't do.
        self._spinner_positions: list[
            tuple[bui.Widget, tuple[float, float]]
        ] = []

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
            dui2.WindowLayout.WIDE
            if self._options.layout is None
            else self._options.layout
        )
        self._scroll_edge_style = (
            default_scroll_edge_style(self._layout)
            if self._options.scroll_edge_style is None
            else self._options.scroll_edge_style
        )
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

        self._subcontainer: bui.Widget | None = None

        self._uiscale = uiscale
        self._toolbar_visibility = toolbar_visibility
        self._viewer_pane: ViewerPane | None = None
        self._scroll_bounds: list[bui.Widget] = []

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

        self._spinner: bui.Widget | None = None

        if not suppress_win_extra_type_warning:
            bui.pushcall(bui.WeakCallStrict(self._sanity_check_win_extra_type))

    def _style_scroll_edges(self) -> None:
        style_scroll_edges(
            self._scrollwidget,
            self._frame,
            uiscale=self._uiscale,
            scroll_edge_style=self._scroll_edge_style,
            toolbar_visibility=self._toolbar_visibility,
        )

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
        self._show_scroll_bounds()

    def _show_scroll_bounds(self) -> None:
        for widget in self._scroll_bounds:
            widget.delete()
        self._scroll_bounds = []
        if debug_draw_enabled(DebugDrawKind.SCROLL_BOUNDS):
            self._scroll_bounds = show_scroll_bounds(
                self._root_widget,
                self._frame,
                self._uiscale,
                has_pane=self._viewer_pane is not None,
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

        f = self._frame
        inset_bottom, inset_top = viewer_insets_v(self._uiscale)
        return ViewerPane(
            self.controller,
            self._root_widget,
            position=(f.viewer_left, f.scroll_bottom + inset_bottom),
            size=(f.viewer_width, f.scroll_height - inset_bottom - inset_top),
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
        self._show_scroll_bounds()

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

    @property
    def request(self) -> DocUIRequest:
        """The current request.

        Should only be accessed from the logic thread while the ui is
        unlocked.
        """
        assert bui.in_logic_thread()
        if self._request is None:
            raise RuntimeError('No request is set.')
        return self._request

    @request.setter
    def request(self, request: DocUIRequest) -> None:
        assert bui.in_logic_thread()
        self._request = request
        self._request_state_id = self._default_state_id(request)

        # New requests immediately blow away existing responses.
        self._last_response = None
        self._last_response_success = False
        self._last_response_shared_state_id = None

    @classmethod
    def _default_state_id(cls, request: DocUIRequest) -> str:
        """Calc a default state id for a request."""
        requesttypeid = request.get_type_id()
        if requesttypeid is DocUIRequestTypeID.V2:
            import bacommon.docui.v2 as dui2

            # One state per path seems like a reasonable default.
            assert isinstance(request, dui2.Request)
            return request.path
        if (
            requesttypeid is DocUIRequestTypeID.V1
            or requesttypeid is DocUIRequestTypeID.UNKNOWN
        ):
            # The client no longer works in v1; treat like unknown.
            return 'unknown'
        assert_never(requesttypeid)

    def lock_ui(self, origin_widget: bui.Widget | None = None) -> None:
        """Stop UI interactions during some operation."""
        assert bui.in_logic_thread()
        assert not self._locked

        self._spinner = make_busy_spinner(
            origin_widget=origin_widget,
            spinner_positions=self._spinner_positions,
            root_widget=self._root_widget,
            window_center=(
                self._vis_left + self._vis_width * 0.5,
                self._vis_top - self._vis_height * 0.5,
            ),
        )

        # Hold root-ui (toolbar) updates while the request is out. A
        # request can change account values the toolbar shows (a claim
        # granting tokens), and the server's update may reach the
        # toolbar before our response does; without this the count
        # would jump to its new total and then the response's effects
        # would animate the climb all over again.
        self._ui_pause = bui.RootUIUpdatePause()
        self._locked = True

    def unlock_ui(self) -> None:
        """Resume normal UI interactions."""
        assert bui.in_logic_thread()
        assert self._locked

        if self._spinner:
            self._spinner.delete()
        self._spinner = None
        self._locked = False

        # Let go of our root-ui pause on the next cycle, not now: the
        # response's client-effects run right after this and take a
        # pause of their own, and releasing first would leave a moment
        # for a pending toolbar update to land.
        if self._ui_pause is not None:
            bui.pushcall(partial(_drop, self._ui_pause))
            self._ui_pause = None

    @override
    def on_main_window_close(self) -> None:
        # Never let a pause outlive us (we may close mid-request).
        self._ui_pause = None
        super().on_main_window_close()

    @property
    def locked(self) -> bool:
        """Are we locked?"""
        assert bui.in_logic_thread()
        return self._locked

    def set_last_response(
        self,
        response: DocUIResponse,
        success: bool,
        *,
        redisplay: bool = False,
    ) -> None:
        """Set a response to a request.

        Pass ``redisplay`` when this is an old response being shown
        again (pending a refresh) rather than a new arrival.
        """
        assert bui.in_logic_thread()
        assert not self._locked
        self._last_response = response
        self._last_response_success = success
        self._has_had_response = True
        self._adopt_page_state(response, redisplay=redisplay)

        # Grab any custom shared-state-id included in this response.
        responsetypeid = response.get_type_id()
        if responsetypeid is DocUIResponseTypeID.V2:
            import bacommon.docui.v2 as dui2

            assert isinstance(response, dui2.Response)
            self._last_response_shared_state_id = response.shared_state_id
        elif (
            responsetypeid is DocUIResponseTypeID.V1
            or responsetypeid is DocUIResponseTypeID.UNKNOWN
        ):
            # The client no longer works in v1; treat like unknown.
            self._last_response_shared_state_id = None
        else:
            assert_never(responsetypeid)

    @property
    def page_state(self) -> dict | None:
        """Current state values for the page we are showing, if any.

        This is the wire form; things knowing the type of state they
        expect can decode it via that type.
        """
        assert bui.in_logic_thread()
        return self.pagestate.values

    def _adopt_page_state(
        self, response: DocUIResponse, *, redisplay: bool
    ) -> None:
        import bacommon.docui.v2 as dui2

        self._spinner_positions = []
        newstate = (
            copy.deepcopy(response.page.state)
            if isinstance(response, dui2.Response)
            else None
        )
        request = self._request
        if isinstance(request, dui2.Request):
            if (
                redisplay
                and newstate is not None
                and request.state is not None
                and request.state.get('_t') == newstate.get('_t')
            ):
                # An old page coming back (pending a refresh). Our
                # request holds any edits made since that page arrived,
                # so show those; the refresh will be sending them.
                newstate = copy.deepcopy(request.state)
            elif redisplay and request.state is None:
                # An old page for a stateless request: a cache hit. Its
                # state is whatever the page had when it was cached, not
                # anything the user did, so leave our request stateless;
                # the refresh then asks for a fresh page just as the
                # original request did, rather than pinning the stale
                # values. (Edits made meanwhile still reach our request
                # via set_page_state_values().)
                pass
            elif newstate is not None:
                # A page's state is the final word on what ours is, so
                # anything re-requesting this page (refreshes, restores)
                # should be sending that.
                self._request = replace(request, state=copy.deepcopy(newstate))
        self.pagestate.adopt(newstate)

    def set_page_state_values(self, values: dict, *, push: bool = True) -> None:
        """Assign values into our page's state.

        With ``push``, input rows showing those values are updated to
        match (input rows reporting their own changes have no need).
        """
        import bacommon.docui.v2 as dui2

        assert bui.in_logic_thread()
        if self.pagestate.values is None:
            bui.uilog.warning(
                'Ignoring doc-ui state values %s; page has no state.',
                list(values),
            )
            return
        self.pagestate.set_values(values, push=push)

        # Keep the request that would re-fetch this page in step, so a
        # refresh or a restore of this window carries the edits.
        # (Assigning to the attr directly; going through our setter
        # would toss our current response.)
        if isinstance(self._request, dui2.Request):
            self._request = replace(
                self._request, state=copy.deepcopy(self.pagestate.values)
            )

    def register_spinner_position(
        self, widget: bui.Widget, position: tuple[float, float]
    ) -> None:
        """Say where the busy-spinner goes for requests a widget fires.

        By default it shows up at the widget's center, which is no good
        for something like a control row spanning the whole page whose
        actual control sits at one end. Position is in the space of
        the widget's parent.

        :meta private:
        """
        self._spinner_positions.append((widget, position))

    def pull_page_state_values(self) -> None:
        """Gather current values from input rows that need asking.

        :meta private:
        """
        changed = self.pagestate.pull_changed()
        if changed:
            self.set_page_state_values(changed, push=False)

    def request_for_action(
        self,
        request: bacommon.docui.v2.Request,
        *,
        sets: dict | None,
        state: dict | None,
        trigger: str | None = None,
    ) -> bacommon.docui.v2.Request:
        """Return an action's request as it should actually go out.

        Requests fired from a page carry that page's current state:
        what the action explicitly provides if anything, or otherwise
        ours with the action's ``sets`` applied.
        """
        assert bui.in_logic_thread()
        self.pull_page_state_values()
        outstate: dict | None
        if state is not None:
            outstate = copy.deepcopy(state)
        elif self.pagestate.values is not None:
            outstate = copy.deepcopy(self.pagestate.values)
            if sets:
                outstate.update(copy.deepcopy(sets))
        else:
            outstate = None
        if outstate is None and trigger is None:
            return request
        return replace(request, state=outstate, trigger=trigger)

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
        # Lay ourself out for the viewer pane (or none) this page was
        # prepped beside; a new pane comes in along with the rows.
        self._set_pane_mode(pageprep.pane, None if pageprep.immediate else 0.1)
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
