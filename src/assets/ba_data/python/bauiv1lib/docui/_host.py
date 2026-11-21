# Released under the MIT License. See LICENSE for details.
#
"""What hosts a doc-ui page: a window, or a popup over one."""

import copy
from functools import partial
from dataclasses import replace
from typing import TYPE_CHECKING, assert_never

import bauiv1 as bui

from bacommon.docui import DocUIRequestTypeID, DocUIResponseTypeID
from bauiv1lib.docui._animtargets import DocUIAnimTargets
from bauiv1lib.docui._pagestate import DocUIPageState
from bauiv1lib.docui._windowparts import make_busy_spinner

if TYPE_CHECKING:
    import bacommon.docui.v2
    from bacommon.docui import DocUIRequest, DocUIResponse
    from bauiv1lib.docui._controller import DocUIController
    from bauiv1lib.docui._panes import PageGeometries
    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui import prep


def _drop(pause: bui.RootUIUpdatePause) -> None:
    """Release a root-ui pause (by letting go of the last reference)."""
    del pause


class DocUIPageHost:
    """Something showing a doc-ui page: a window, or a popup over one.

    Holds what any page needs wherever it is shown: the request that
    fetched it, its live page state, the lock held while a request is
    out, and its animatable widgets. Controllers and page prep work
    against this; what differs between the two kinds of host (their
    chrome and geometry, how they close, whether they keep a place in
    the back stack) lives in :class:`~bauiv1lib.docui.DocUIWindow` and
    ``DocUIPopupWindow``.

    A mixin listed after a :class:`bauiv1.Window` subclass, whose
    constructor calls ours first (explicitly; ours is not in the
    window's ``super()`` chain).
    """

    def __init__(
        self, controller: DocUIController, request: DocUIRequest
    ) -> None:
        self._locked = False

        # Held while we're locked (a request in flight); see lock_ui().
        self._ui_pause: bui.RootUIUpdatePause | None = None

        # Note: our hosts and states both hold strong references to the
        # controller, so we need to make sure the opposite is not true
        # to avoid cycles.
        self.controller = controller

        self._request = request
        self._request_state_id = self._default_state_id(request)

        #: Our page's client-effect-animatable widgets.
        self.anim_targets = DocUIAnimTargets()

        #: Our page's navigable rows, each as its selectable widgets
        #: with its vertical extent (top, bottom) in the page, as doc-ui
        #: lays it out. Selection should keep that extent inside our
        #: content rect (see DebugDrawKind.LAYOUT); for checks.
        self.row_bounds: list[tuple[list[bui.Widget], float, float]] = []

        self._last_response: DocUIResponse | None = None
        self._last_response_success: bool = False
        self._last_response_shared_state_id: str | None = None

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
        self._spinner: bui.Widget | None = None

    # -- What each kind of host provides. ----------------------------------

    @property
    def host_id_prefix(self) -> str:
        """Prefix for the ids of widgets in our page.

        :meta private:
        """
        raise NotImplementedError()

    def host_root_widget(self) -> bui.Widget:
        """Our root container widget.

        :meta private:
        """
        raise NotImplementedError()

    def host_page_center(self) -> tuple[float, float]:
        """Where our page area's center is in our root widget.

        (Where the busy-spinner goes for requests no widget fired.)

        :meta private:
        """
        raise NotImplementedError()

    def host_main_window(self) -> DocUIWindow | None:
        """The main window this page belongs to.

        A window's is itself; a popup's is the window it is over (None
        if that has gone away).

        :meta private:
        """
        raise NotImplementedError()

    def page_geometries(self) -> PageGeometries:
        """What our pages lay out against, for each pane they may get.

        :meta private:
        """
        raise NotImplementedError()

    def instantiate_ui(self, pageprep: prep.PagePrep) -> None:
        """Replace any current ui with provided prepped one.

        :meta private:
        """
        raise NotImplementedError()

    def host_alive(self) -> bool:
        """Whether we're still up to show a page.

        (A response arriving for a host that has since gone is
        dropped.)

        :meta private:
        """
        return True

    def save_shared_state(self) -> None:
        """Save selection and such before our page is replaced.

        (So a rebuild of it comes back the same way.) Nothing by
        default.

        :meta private:
        """

    def parent_state_for_requests(self) -> dict | None:
        """The parent page's state, for requests fired from our page.

        (See :attr:`bacommon.docui.v2.Request.parent_state`.) Only a
        popup has a parent page; None by default.

        :meta private:
        """
        return None

    # -- Shared. -----------------------------------------------------------

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
            root_widget=self.host_root_widget(),
            window_center=self.host_page_center(),
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

    def _release_ui_pause(self) -> None:
        """Let go of any root-ui pause now (we're going away)."""
        self._ui_pause = None

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
        self._on_response_set()
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

    def _on_response_set(self) -> None:
        """Called as a response is set (before its state is adopted)."""

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
        # refresh or a restore of this host carries the edits.
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
        ours with the action's ``sets`` applied. Those fired from a
        popup carry the parent page's state too.
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
        # (None but for popups; see parent_state_for_requests().)
        # pylint: disable-next=assignment-from-none
        parent_state = self.parent_state_for_requests()
        if outstate is None and trigger is None and parent_state is None:
            return request
        return replace(
            request,
            state=outstate,
            trigger=trigger,
            parent_state=parent_state,
        )
