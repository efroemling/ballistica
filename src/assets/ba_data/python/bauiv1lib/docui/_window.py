# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

import copy
from dataclasses import replace
from typing import TYPE_CHECKING, override, assert_never

import bauiv1 as bui
from bauiv1 import _commonassets

from bacommon.docui import DocUIRequestTypeID, DocUIResponseTypeID
from bauiv1lib.docui._layout import (
    SMALL_UI_SCROLL_EXTRA,
    SMALL_UI_VIEWER_INSET_V,
    SMALL_UI_VIEWER_NUDGE_X,
    TITLE_BAND_HEIGHT,
    back_button_geometry,
    column_inset,
    layout_geometry,
    show_scroll_border,
    viewer_pane_width,
    window_content_drop,
    window_insets,
    window_scroll_overhang,
)
from bauiv1lib.docui._windowparts import (
    ViewerPane,
    show_vis_area_bounds,
)
from bauiv1lib.docui._pagestate import DocUIPageState
from bauiv1lib.docui._scrollrestore import (
    page_scrollers,
    capture_scroll,
    apply_scroll,
    containing_scrollers,
)
from bauiv1lib.utils import (
    get_screen_margins,
    scroll_fade_bottom,
    scroll_fade_top,
)

if TYPE_CHECKING:
    from typing import Any, Callable

    import bacommon.docui.v2
    from bacommon.docui import DocUIRequest, DocUIResponse
    from bauiv1lib.docui._controller import DocUIController
    from bauiv1lib.docui._scrollrestore import (
        ScrollSnapshot,
        ScrollRestoreMode,
    )
    from bauiv1lib.docui import prep

# How the busy-spinner shown over a pressed widget (a button, an input
# row's control) appears: invisible for this long, then a fade-in this
# long. Quick round trips thus show nothing at all rather than the
# one-frame flash the old instant spinner gave, while slower ones get
# a soft appearance right where the press was. Sharper than the
# widget's default 0.5/0.5, which the window-centered page-load
# spinner keeps. Tuned in one place for every such spinner.
REFRESH_SPINNER_FADE_DELAY = 0.2
REFRESH_SPINNER_FADE_DURATION = 0.2

# Our scroll snapshot's key in a window's shared state.
_SCROLL_STATE_KEY = 'docui_scroll'


class DocUIWindow(bui.MainWindow):
    """Window showing doc-ui content."""

    # pylint: disable=too-many-public-methods

    def __init__(
        self,
        controller: DocUIController,
        request: DocUIRequest,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
        restored: bool = False,
        uiopenstateid: str | None = None,
        suppress_win_extra_type_warning: bool = False,
        has_had_response: bool = False,
        layout: bacommon.docui.v2.WindowLayout | None = None,
    ):
        # pylint: disable=too-many-statements
        import bacommon.docui.v2 as dui2

        ui = bui.app.ui_v1

        self._uiopenstate = (
            None if uiopenstateid is None else bui.UIOpenState(uiopenstateid)
        )

        self._locked = False

        self._restored = restored

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
        self._layout = dui2.WindowLayout.LARGE if layout is None else layout
        self._width, self._height, self._root_scale = layout_geometry(
            self._layout, uiscale
        )

        # Do some fancy math to calculate our visible area; this will be
        # limited by the screen size in small mode and our backing size
        # otherwise.
        screensize = bui.get_virtual_screen_size()
        side_insets, vertical_insets = window_insets(self._layout)
        self._vis_width = min(
            self._width - side_insets, screensize[0] / self._root_scale
        )
        self._vis_height = min(
            self._height - vertical_insets, screensize[1] / self._root_scale
        )

        # At medium/large scale, then grow the backing (only) around that,
        # uniformly so its shape -- and thus which backing art it gets --
        # is unchanged; without this our scroll area and buttons (the
        # back button especially) creep out toward its visible edges.
        # Everything else is laid out relative to the visible area, which
        # stays centered. (Small ui-scale windows fill the screen, so
        # there is no edge to keep clear of.)
        backing_pad = 1.0 if uiscale is bui.UIScale.SMALL else 1.02
        self._width *= backing_pad
        self._height *= backing_pad

        self._vis_top = 0.5 * self._height + 0.5 * self._vis_height
        if uiscale is not bui.UIScale.SMALL:
            self._vis_top -= window_content_drop(self._layout)
        self._vis_left = 0.5 * self._width - 0.5 * self._vis_width

        self._scroll_width = self._vis_width + (
            0.0
            if uiscale is bui.UIScale.SMALL
            else window_scroll_overhang(self._layout)
        )
        self._scroll_left = self._vis_left + 0.5 * (
            self._vis_width - self._scroll_width
        )
        # Go with full-screen scrollable aread in small ui.
        self._scroll_height = self._vis_height + (
            SMALL_UI_SCROLL_EXTRA
            if uiscale is bui.UIScale.SMALL
            else -TITLE_BAND_HEIGHT
        )
        self._scroll_bottom = (
            self._vis_top
            - (-1 if uiscale is bui.UIScale.SMALL else 27)
            - self._scroll_height
        )

        # Nudge our vis area up a bit when we can see the full backing
        # (visual fudge factor).
        if uiscale is not bui.UIScale.SMALL:
            self._vis_top += 12.0

        # In small ui we extend our scrollable area out into the screen
        # margins (space between the virtual bounds and the actual
        # screen edges) while keeping content laid out within the
        # virtual bounds (page prep gets these margins so it can lay
        # things out accordingly).
        (
            self._margin_left,
            self._margin_right,
            self._margin_bottom,
            self._margin_top,
        ) = (
            get_screen_margins(self._root_scale)
            if uiscale is bui.UIScale.SMALL
            else (0.0, 0.0, 0.0, 0.0)
        )

        # Narrow where content is laid out, if our layout calls for it.
        col_inset = column_inset(self._layout, uiscale, self._scroll_width)
        self._column_insets = (col_inset, col_inset)

        # A viewer pane takes the left of our scroll area (the page
        # scrolls in what remains), so our scroll-widget stops at the
        # pane instead of extending into the screen margin. Unlike
        # scrolling content, the viewer's content doesn't move, so it
        # stays within the virtual bounds (none of it may be cut off by
        # the screen edge) and, in small ui, clear of the toolbars.
        self._viewer_width = viewer_pane_width(self._layout, self._scroll_width)
        if self._viewer_width > 0.0:
            self._scroll_left += self._viewer_width
            self._scroll_width -= self._viewer_width
            self._margin_left = 0.0

        toolbar_visibility = controller.get_window_toolbar_visibility()
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=toolbar_visibility,
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
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
        # Avoid complaints if nothing is selected under us.
        bui.widget(edit=self._root_widget, allow_preserve_selection=False)

        self._subcontainer: bui.Widget | None = None

        # Created before our scroll widget, as the two can overlap (see
        # _create_viewer_pane()): presses go to the last-created widget
        # that wants them, and the page should win there.
        self._viewer_pane = self._create_viewer_pane(controller, uiscale)

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=True,  # Will turn off once we have UI.
            size=(
                self._scroll_width + self._margin_left + self._margin_right,
                self._scroll_height + self._margin_bottom + self._margin_top,
            ),
            position=(
                self._scroll_left - self._margin_left,
                self._scroll_bottom - self._margin_bottom,
            ),
            border_opacity=0.4 if show_scroll_border(self._layout) else 0.0,
            # A border around content that doesn't scroll is just
            # clutter (the audio settings page, say).
            hide_border_when_fits=True,
            center_small_content_horizontally=True,
            claims_left_right=True,
            # Selection-preserving needs an id on every selectable
            # widget; without one, landing here on window save warns and
            # loses the user's place on return.
            id=f'{self.main_window_id_prefix}|scroll',
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)

        # With full-screen scrolling, fade content as it approaches
        # toolbars. A minimal toolbar has nothing along the bottom, so
        # no fade there.
        if uiscale is bui.UIScale.SMALL:
            scroll_fade_top(
                self._root_widget,
                self._scroll_left,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
            )
        if (
            uiscale is bui.UIScale.SMALL
            and toolbar_visibility != 'menu_minimal'
        ):
            scroll_fade_bottom(
                self._root_widget,
                self._scroll_left,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
            )

        # Our back button's geometry (medium/large ui-scale); the title
        # is centered vertically on it.
        back_scale, back_size, back_offset = back_button_geometry(
            self._layout, close_style=auxiliary_style
        )
        back_bottom = self._vis_top + back_offset[1]
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
            position=(self._width * 0.5, title_y),
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
                label=bui.charstr(
                    bui.SpecialChar.CLOSE
                    if auxiliary_style
                    else bui.SpecialChar.BACK
                ),
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        # Show our vis-area bounds (for debugging).
        if bool(False):
            show_vis_area_bounds(
                self._root_widget,
                self._vis_left,
                self._vis_top,
                self._vis_width,
                self._vis_height,
            )

        self._spinner: bui.Widget | None = None

        if not suppress_win_extra_type_warning:
            bui.pushcall(bui.WeakCallStrict(self._sanity_check_win_extra_type))

    def _create_viewer_pane(
        self, controller: DocUIController, uiscale: bui.UIScale
    ) -> ViewerPane | None:
        """Create our viewer pane, if our layout has one.

        It sits alongside our scroll area and is as tall as it, less
        toolbar clearance in small ui (where the scroll area runs under
        the toolbars). In small ui it is also nudged right a bit so it
        sits evenly between the virtual bounds and the page content,
        overlapping the scroll area's (empty) left edge.
        """
        if self._viewer_width <= 0.0:
            return None
        small = uiscale is bui.UIScale.SMALL
        inset_v = SMALL_UI_VIEWER_INSET_V if small else 0.0
        nudge_x = SMALL_UI_VIEWER_NUDGE_X if small else 0.0
        return ViewerPane(
            controller,
            self._root_widget,
            position=(
                self._scroll_left - self._viewer_width + nudge_x,
                self._scroll_bottom + inset_v,
            ),
            size=(self._viewer_width, self._scroll_height - 2.0 * inset_v),
        )

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

        # If a spinner-position is provided, make the spinner in our
        # subcontainer at the provided spot (a press should show its
        # spinner where the press was).
        parent = None if origin_widget is None else origin_widget.parent
        if parent is not None:
            assert origin_widget is not None
            position = origin_widget.center
            for widget, widgetposition in self._spinner_positions:
                if widget == origin_widget:
                    position = widgetposition
                    break
            self._spinner = bui.spinnerwidget(
                parent=parent,
                position=position,
                size=48,
                fade_delay=REFRESH_SPINNER_FADE_DELAY,
                fade_duration=REFRESH_SPINNER_FADE_DURATION,
            )
        else:
            # Otherwise do one at the center of our window (not in our
            # subcontainer).
            self._spinner = bui.spinnerwidget(
                parent=self._root_widget,
                position=(
                    self._vis_left + self._vis_width * 0.5,
                    self._vis_top - self._vis_height * 0.5,
                ),
                size=48,
                # With restored windows we're likely to have stuff under
                # the spinner. Bomb looks nicer but simple is more
                # readable in those cases.
                style='simple' if self._restored else 'bomb',
                # (Default fade timing: this one was never instant.)
            )
        self._locked = True

    def unlock_ui(self) -> None:
        """Resume normal UI interactions."""
        assert bui.in_logic_thread()
        assert self._locked

        if self._spinner:
            self._spinner.delete()
        self._spinner = None
        self._locked = False

    @property
    def locked(self) -> bool:
        """Are we locked?"""
        assert bui.in_logic_thread()
        return self._locked

    @property
    def scroll_width(self) -> float:
        """Width of our scroll area."""
        return self._scroll_width

    @property
    def scroll_height(self) -> float:
        """Height of our scroll area."""
        return self._scroll_height

    @property
    def column_insets(self) -> tuple[float, float]:
        """Extra left/right insets narrowing where content is laid out
        (within :attr:`screen_margins`) to a column.
        """
        return self._column_insets

    @property
    def screen_margins(self) -> tuple[float, float, float, float]:
        """Screen margins (left, right, bottom, top) our scroll extends
        into beyond its standard scroll-width/height area.
        """
        return (
            self._margin_left,
            self._margin_right,
            self._margin_bottom,
            self._margin_top,
        )

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
        request = self._request
        last_response = self._last_response
        has_had_response = self._has_had_response
        layout = self._layout
        uiopenstateid = (
            None if self._uiopenstate is None else self._uiopenstate.stateid
        )
        suppress_win_extra_type_warning = self._suppress_win_extra_type_warning

        return bui.BasicMainWindowState(
            create_call=(
                lambda transition, origin_widget: controller.restore(
                    cls(
                        controller=controller,
                        request=request,
                        transition=transition,
                        origin_widget=origin_widget,
                        auxiliary_style=auxiliary_style,
                        uiopenstateid=uiopenstateid,
                        suppress_win_extra_type_warning=(
                            suppress_win_extra_type_warning
                        ),
                        restored=True,
                        has_had_response=has_had_response,
                        layout=layout,
                    ),
                    last_response=last_response,
                    has_had_response=has_had_response,
                )
            ),
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
