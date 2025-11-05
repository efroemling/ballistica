# Released under the MIT License. See LICENSE for details.
#
"""Controller functionality for CloudUI."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, assert_never
from dataclasses import dataclass
from enum import Enum
import weakref

from efro.error import CleanError
from efro.dataclassio import dataclass_to_dict
from bacommon.cloudui import (
    CloudUIRequestTypeID,
    UnknownCloudUIRequest,
    CloudUIResponseTypeID,
    UnknownCloudUIResponse,
)
import bauiv1 as bui

from bauiv1lib.cloudui._prep import CloudUIPagePrep
from bauiv1lib.cloudui._window import CloudUIWindow

if TYPE_CHECKING:
    from typing import Callable

    import bacommon.cloudui.v1
    from bacommon.cloudui import CloudUIRequest, CloudUIResponse
    from bacommon.bs import ClientEffect


class CloudUIController:
    """Manages interactions between CloudUI clients and servers.

    Can include logic to handle all requests locally or can submit them
    to be handled by some server or can do some combination thereof.
    """

    class ErrorType(Enum):
        """Types of errors that can occur in request processing."""

        GENERIC = 'generic'
        UNDER_CONSTRUCTION = 'under_construction'
        COMMUNICATION_ERROR = 'communication'
        NEED_UPDATE = 'need_update'

    def fulfill_request(self, request: CloudUIRequest) -> CloudUIResponse:
        """Handle request fulfillment.

        Expected to be overridden by child classes.

        Be aware that this will always be called in a background thread.

        This method is expected to always return a response, even in the
        case of errors. Use :meth:`error_response()` to translate error
        conditions to responses.

        The one exception to this rule (no pun intended) is the
        :class:`efro.error.CleanError` exception. This can be raised as a
        quick and dirty way to show custom error messages. The code
        ``raise CleanError('Something broke.')`` will have the same
        effect as ``return self.error_response(custom_message='Something
        broke.')``.
        """
        raise NotImplementedError()

    def local_action(self, action: CloudUILocalAction) -> None:
        """Do something locally on behalf of the cloud-ui.

        Controller classes can override this to expose named actions
        that can be triggered by cloud-ui button presses, responses,
        etc.

        Of course controllers can also perform arbitrary local actions
        alongside their normal request fulfillment; this is simply a way
        to do so without needing to provide actual ui pages alongside.

        Be *very* careful and focused with what you expose here,
        especially if your cloud-ui pages are coming from untrusted
        sources. Generally things like launching or joining games are
        good candidates for local actions.
        """

    def fulfill_request_http(
        self, request: CloudUIRequest, url: str
    ) -> CloudUIResponse:
        """Fulfill a request by sending it to a webserver."""
        import bacommon.cloudui.v1 as clui1

        import urllib3.util

        if not isinstance(request, clui1.Request):
            raise RuntimeError(f'Unsupported cloudui request: {type(request)}')

        upool = bui.app.net.urllib3pool

        # Allow compressed results.
        headers = urllib3.util.make_headers(accept_encoding=True)

        # Map cloudui GET requests to http GET and POST to POST.
        if request.method is clui1.RequestMethod.GET:
            httpmeth = 'GET'
        elif request.method is clui1.RequestMethod.POST:
            httpmeth = 'POST'
        elif request.method is clui1.RequestMethod.UNKNOWN:
            raise RuntimeError('Unknown request method.')
        else:
            assert_never(request.method)

        # Stuff our request (and possibly other stuff) into a dict and
        # ship it to the server as json.
        data = {'r': dataclass_to_dict(request)}
        datastr = json.dumps(data, separators=(',', ':'))
        headers['Content-Type'] = 'application/json'

        raw_response = upool.request(
            httpmeth, url, body=datastr, headers=headers
        )
        print('GOT STATUS:', raw_response.status)
        if raw_response.status != 200:
            return self.error_response(self.ErrorType.COMMUNICATION_ERROR)

        return self.error_response(self.ErrorType.UNDER_CONSTRUCTION)

    def error_response(
        self,
        error_type: ErrorType = ErrorType.GENERIC,
        custom_message: str | None = None,
    ) -> CloudUIResponse:
        """Build a simple error message page.

        A message is included based on ``error_type``. Pass
        ``custom_message`` to override this.

        Messages will be translated to the client language using the
        'serverResponses' Lstr translation category.
        """
        import bacommon.cloudui.v1 as clui1

        error_msg: bui.Lstr | None = None
        error_msg_simple: str | None = None

        if custom_message is not None:
            error_msg_simple = custom_message
        else:
            if error_type is self.ErrorType.GENERIC:
                error_msg_simple = 'An error has occurred.'
            elif error_type is self.ErrorType.NEED_UPDATE:
                error_msg_simple = 'You must update the app to view this.'
            elif error_type is self.ErrorType.UNDER_CONSTRUCTION:
                error_msg_simple = 'Under construction - check back soon.'
            elif error_type is self.ErrorType.COMMUNICATION_ERROR:
                error_msg_simple = 'Error talking to server.'
            else:
                assert_never(error_type)
        if error_msg_simple is not None:
            error_msg = bui.Lstr(
                translate=('serverResponses', error_msg_simple)
            )
        assert error_msg is not None

        debug = False
        return clui1.Response(
            status=clui1.StatusCode.UNKNOWN_ERROR,
            page=clui1.Page(
                title=bui.Lstr(resource='errorText').as_json(),
                title_is_lstr=True,
                center_vertically=True,
                rows=[
                    clui1.Row(
                        buttons=[
                            clui1.Button(
                                bui.Lstr(resource='okText').as_json(),
                                clui1.Local(close_window=True),
                                text_is_lstr=True,
                                default=True,
                                style=clui1.ButtonStyle.MEDIUM,
                                size=(130, 50),
                                padding_left=200,
                                padding_right=200,
                                padding_top=100,
                                decorations=[
                                    clui1.Text(
                                        error_msg.as_json(),
                                        is_lstr=True,
                                        position=(0, 80),
                                        size=(480, 50),
                                        highlight=False,
                                        debug=debug,
                                    ),
                                ],
                                debug=debug,
                            ),
                        ],
                        center_content=True,
                        debug=debug,
                    ),
                ],
            ),
        )

    def create_window(
        self,
        request: CloudUIRequest,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
    ) -> CloudUIWindow:
        """Create a new window to handle a request."""
        assert bui.in_logic_thread()

        # Create a shiny new window.
        win = CloudUIWindow(
            self,
            request,
            transition=transition,
            origin_widget=origin_widget,
            auxiliary_style=auxiliary_style,
        )
        self._set_win_state(win, self._WinState.FETCHING_FRESH_REQUEST)

        # Lock its ui and kick off a bg task to populate it.
        win.lock_ui()
        bui.app.threadpool.submit_no_wait(
            bui.CallStrict(
                self._process_request_in_bg,
                request,
                weakwin=weakref.ref(win),
                uiscale=bui.app.ui_v1.uiscale,
                scroll_width=win.scroll_width,
                scroll_height=win.scroll_height,
                idprefix=win.main_window_id_prefix,
                immediate=False,
            )
        )
        return win

    def restore(
        self,
        win: CloudUIWindow,
        *,
        last_response: CloudUIResponse | None,
    ) -> CloudUIWindow:
        """Restore a window from previous state.

        May immediately display old results or may kick off a new
        request.
        """
        import bacommon.cloudui.v1 as clui1

        assert bui.in_logic_thread()

        explicit_response: CloudUIResponse | None = None
        explicit_error: CloudUIController.ErrorType | None = None

        if last_response is not None:
            # Re-prep our restored response so we have something to show
            # immediately. We'll then fetch an updated version in the
            # background to get the latest version.
            explicit_response = last_response
        else:
            # We have no previous response to restore. Fetch a new one.

            # If the current request is a POST, never auto-refetch. Just
            # build an error response.
            assert isinstance(win.request, clui1.Request)
            if win.request.method is clui1.RequestMethod.POST:
                # Do we want a specific error for this? Though this case
                # should be rare I think.
                explicit_error = self.ErrorType.GENERIC
            else:
                explicit_error = None

        # We're either errored or redisplaying an old state.
        if explicit_error is None:
            self._set_win_state(win, self._WinState.REDISPLAYING_OLD_STATE)
        else:
            self._set_win_state(win, self._WinState.ERRORED)

        # Lock the ui and kick off this update.
        win.lock_ui()
        bui.app.threadpool.submit_no_wait(
            bui.CallStrict(
                self._process_request_in_bg,
                win.request,
                weakwin=weakref.ref(win),
                uiscale=bui.app.ui_v1.uiscale,
                scroll_width=win.scroll_width,
                scroll_height=win.scroll_height,
                idprefix=win.main_window_id_prefix,
                # If we're restoring an old response, snap it in
                # immediately. If we're doing a fresh fetch, allow a
                # transition to hide delays.
                immediate=last_response is not None,
                explicit_error=explicit_error,
                explicit_response=explicit_response,
            )
        )
        return win

    def replace(
        self,
        win: CloudUIWindow,
        request: CloudUIRequest,
        *,
        origin_widget: bui.Widget | None = None,
        is_refresh: bool = False,
    ) -> None:
        """Kick off a request to replace existing window contents."""
        import bacommon.cloudui.v1 as clui1

        assert bui.in_logic_thread()

        win.request = request

        requesttype = request.get_type_id()

        if requesttype is CloudUIRequestTypeID.V1:
            assert isinstance(win.request, clui1.Request)

            self._set_win_state(
                win,
                (
                    self._WinState.REFRESHING
                    if is_refresh
                    else self._WinState.FETCHING_FRESH_REQUEST
                ),
            )

            # Lock the ui and kick off this update.
            win.lock_ui(origin_widget)
            bui.app.threadpool.submit_no_wait(
                bui.CallStrict(
                    self._process_request_in_bg,
                    win.request,
                    weakwin=weakref.ref(win),
                    uiscale=bui.app.ui_v1.uiscale,
                    scroll_width=win.scroll_width,
                    scroll_height=win.scroll_height,
                    idprefix=win.main_window_id_prefix,
                    immediate=True,
                )
            )
        elif requesttype is CloudUIRequestTypeID.UNKNOWN:
            assert isinstance(win.request, UnknownCloudUIRequest)
            # Got a request type we don't know. Show a 'need a newer
            # build' error.

            self._set_win_state(win, self._WinState.ERRORED)

            # Lock the ui and kick off this update.
            win.lock_ui(origin_widget)
            bui.app.threadpool.submit_no_wait(
                bui.CallStrict(
                    self._process_request_in_bg,
                    win.request,
                    weakwin=weakref.ref(win),
                    uiscale=bui.app.ui_v1.uiscale,
                    scroll_width=win.scroll_width,
                    scroll_height=win.scroll_height,
                    idprefix=win.main_window_id_prefix,
                    immediate=True,
                    explicit_error=self.ErrorType.NEED_UPDATE,
                )
            )
        else:
            assert_never(requesttype)

    def run_action(
        self,
        window: CloudUIWindow,
        widgetid: str | None,
        action: bacommon.cloudui.v1.Action | None,
        is_timed: bool = False,
    ) -> None:
        """Called when a button is pressed in a v1 ui."""
        # pylint: disable=too-many-branches
        # pylint: disable=cyclic-import

        import bacommon.cloudui.v1 as clui

        assert bui.in_logic_thread()

        # If locked, just beep.
        if window.locked:
            bui.getsound('error').play()
            return

        widget: bui.Widget | None

        if widgetid is not None:
            # Find the associated button.
            widget = bui.widget_by_id(widgetid)
            if widget is None:
                bui.uilog.warning(
                    'CloudUI button press widget not found: %s (not expected)',
                    widgetid,
                )
                return
        else:
            widget = None

        # Buttons with no actions assigned.
        if action is None:
            bui.getsound('click01').play()
            return

        action_type = action.get_type_id()

        if action_type is clui.ActionTypeID.BROWSE:
            assert isinstance(action, clui.Browse)
            if is_timed:
                # Don't let timers pop up new windows. Untrusted servers
                # would have a field-day with this.
                bui.uilog.warning(
                    'Ignoring BROWSE action (disallowed in timed actions).'
                )
            else:
                if action.default_sound:
                    bui.getsound('swish').play()
                window.main_window_replace(
                    lambda: self.create_window(
                        action.request,
                        origin_widget=widget,
                        auxiliary_style=False,
                    )
                )
                if bui.app.classic is not None and action.immediate_effects:
                    bui.app.classic.run_bs_client_effects(
                        action.immediate_effects
                    )
        elif action_type is clui.ActionTypeID.REPLACE:
            assert isinstance(action, clui.Replace)

            # Play default click sound only if this is coming from a
            # button.
            if widget is not None and action.default_sound:
                bui.getsound('click01').play()

            # Force a state save so if our UI gets rebuilt with the same
            # IDs we'll wind up with the same selection and whatnot.
            window.main_window_save_shared_state()
            self.replace(window, action.request, origin_widget=widget)

            self._run_immediate_effects_and_actions(
                client_effects=action.immediate_client_effects,
                local_action=action.immediate_local_action,
                local_action_params=action.immediate_local_action_params,
                widget=widget,
                window=window,
                is_timed=is_timed,
            )

        elif action_type is clui.ActionTypeID.LOCAL:
            assert isinstance(action, clui.Local)
            if action.default_sound:
                if action.close_window:
                    # Always play close-window swish, even if we don't have
                    # a source button.
                    bui.getsound('swish').play()
                else:
                    # Only play click sound if this is coming from a button.
                    if widget is not None:
                        bui.getsound('click01').play()
            if action.close_window:
                window.main_window_back()

            self._run_immediate_effects_and_actions(
                client_effects=action.immediate_client_effects,
                local_action=action.immediate_local_action,
                local_action_params=action.immediate_local_action_params,
                widget=widget,
                window=window,
                is_timed=is_timed,
            )
        else:
            # Make sure we handle all options.
            assert_never(action_type)

    def _run_immediate_effects_and_actions(
        self,
        *,
        client_effects: list[ClientEffect],
        local_action: str | None,
        local_action_params: dict | None,
        widget: bui.Widget | None,
        window: CloudUIWindow,
        is_timed: bool,
    ) -> None:
        # We don't allow timed actions to trigger immediate
        # client-effects/local-actions. It would be too easy for such
        # things to get unintentionally re-triggered when navigating
        # back/etc. We only want those to happen due to direct button
        # presses or initial (non-refresh) responses, which should keep
        # things feeling mostly intentional.
        if is_timed:
            if client_effects:
                bui.uilog.warning(
                    'Ignoring client-effects (disallowed in timed actions).'
                )
            if local_action is not None:
                bui.uilog.warning(
                    'Ignoring local-action (disallowed in timed actions).'
                )
            return

        if bui.app.classic is not None and client_effects:
            bui.app.classic.run_bs_client_effects(client_effects)
        if local_action is not None:
            try:
                self.local_action(
                    CloudUILocalAction(
                        name=local_action,
                        params=(
                            {}
                            if local_action_params is None
                            else local_action_params
                        ),
                        widget=widget,
                        window=window,
                    )
                )
            except Exception:
                bui.uilog.exception(
                    'Error running local-action %s.',
                    local_action,
                )

    class _WinState(Enum):
        """Per-window state."""

        FETCHING_FRESH_REQUEST = 0
        REDISPLAYING_OLD_STATE = 1
        REFRESHING = 2
        ERRORED = 3
        IDLE = 4

    def _get_win_state(self, window: CloudUIWindow) -> _WinState:
        val = getattr(window, '_cstate')
        assert isinstance(val, self._WinState)
        return val

    def _set_win_state(self, window: CloudUIWindow, state: _WinState) -> None:
        setattr(window, '_cstate', state)

    def _process_request_in_bg(
        self,
        request: CloudUIRequest,
        *,
        weakwin: weakref.ref[CloudUIWindow],
        uiscale: bui.UIScale,
        scroll_width: float,
        scroll_height: float,
        idprefix: str,
        immediate: bool,
        explicit_error: ErrorType | None = None,
        explicit_response: CloudUIResponse | None = None,
    ) -> None:
        """Wrangle a request from within a background thread.

        This will always return a response, even on error conditions.
        """
        # pylint: disable=too-many-locals
        import bacommon.cloudui.v1 as clui1

        assert not bui.in_logic_thread()

        response: CloudUIResponse | None = None
        error: CloudUIController.ErrorType | None = None

        if explicit_error is not None:
            error = explicit_error
        elif explicit_response is not None:
            response = explicit_response
        else:
            try:
                response = self.fulfill_request(request)
            except CleanError as exc:
                # The one exception case we officially handle. Translate
                # this to an error response with a custom message.
                response = self.error_response(custom_message=str(exc))

            except Exception:
                # fulfill_request is expected to gracefully return even
                # on errors. Make noise if it didn't.
                bui.uilog.exception(
                    'Error in fulfill_request().\n'
                    'It should always return responses; not throw exceptions.\n'
                    'Use error_response() when errors occur.',
                    exc_info=True,
                )
                error = self.ErrorType.GENERIC

        # Validate any response we got.
        if response is not None:
            assert error is None
            responsetype = response.get_type_id()

            if responsetype is CloudUIResponseTypeID.V1:

                assert isinstance(response, clui1.Response)

                # If they require a build-number newer than us, say so.
                minbuild = response.minimum_engine_build
                if (
                    minbuild is not None
                    and minbuild > bui.app.env.engine_build_number
                ):
                    error = self.ErrorType.NEED_UPDATE
                else:

                    # Make sure there's at least one row and that all rows
                    # contain at least one button.
                    if not response.page.rows or not all(
                        row.buttons for row in response.page.rows
                    ):
                        bui.uilog.exception(
                            'Got invalid cloud-ui response;'
                            ' page must contain at least one row'
                            ' and all rows must contain buttons.'
                        )
                        error = self.ErrorType.GENERIC

            elif responsetype is CloudUIResponseTypeID.UNKNOWN:
                assert isinstance(response, UnknownCloudUIResponse)
                bui.uilog.debug(
                    'Got unsupported cloudui response.', exc_info=True
                )
                error = self.ErrorType.NEED_UPDATE
                response = None
            else:
                # Make sure we cover all types we're aware of.
                assert_never(responsetype)

        if error is not None:
            response = self.error_response(error)

        # Currently must be v1 if it made it to here.
        assert isinstance(response, clui1.Response)

        pageprep = CloudUIPagePrep(
            response.page,
            uiscale=uiscale,
            scroll_width=scroll_width,
            scroll_height=scroll_height,
            immediate=immediate,
            idprefix=idprefix,
        )

        # Go ahead and just push the response along with our weakref
        # back to the logic thread for handling. We could quick-out here
        # if the window is dead, but wrangling its refs here could
        # theoretically lead to it being deallocated here which could be
        # problematic.
        bui.pushcall(
            bui.CallStrict(
                self._handle_response_in_ui_thread,
                response,
                weakwin,
                pageprep,
            ),
            from_other_thread=True,
        )

    def _handle_response_in_ui_thread(
        self,
        response: CloudUIResponse,
        weakwin: weakref.ref[CloudUIWindow],
        pageprep: CloudUIPagePrep,
    ) -> None:
        import bacommon.cloudui.v1 as clui1

        assert bui.in_logic_thread()

        # If our target window died since we made the request, no
        # biggie.
        win = weakwin()
        if win is None:
            return

        # Currently should only be sending ourself v1 responses here.
        assert isinstance(response, clui1.Response)

        win.unlock_ui()
        win.set_last_response(
            response,
            response.status == clui1.StatusCode.SUCCESS,
        )

        # Set the UI.
        win.instantiate_ui(pageprep)

        state = self._get_win_state(win)

        # Run client-effects and local-actions ONLY after fresh requests
        # (don't want sounds and other actions firing when we navigate
        # back or resize a window).
        if state is self._WinState.FETCHING_FRESH_REQUEST:
            if response.client_effects and bui.app.classic is not None:
                bui.app.classic.run_bs_client_effects(response.client_effects)
            if response.local_action is not None:
                try:
                    self.local_action(
                        CloudUILocalAction(
                            name=response.local_action,
                            params=(
                                {}
                                if response.local_action_params is None
                                else response.local_action_params
                            ),
                            widget=None,
                            window=win,
                        )
                    )
                except Exception:
                    bui.uilog.exception(
                        'Error running local-action %s.',
                        response.local_action,
                    )

        # Possibly take further action depending on state.
        if state is self._WinState.REDISPLAYING_OLD_STATE:
            # Ok; we're done showing old state. For POST this is as far
            # as we go (don't want to repeat POST effects), but for GET
            # we can now kick off a refresh to swap in the latest
            # version of the page.
            assert isinstance(win.request, clui1.Request)
            if win.request.method is clui1.RequestMethod.GET:
                self.replace(win, win.request, is_refresh=True)
            elif (
                win.request.method is clui1.RequestMethod.POST
                or win.request.method is clui1.RequestMethod.UNKNOWN
            ):
                self._set_idle_and_schedule_timed_action(response, weakwin)
            else:
                assert_never(win.request.method)

        elif state is self._WinState.ERRORED or state is self._WinState.IDLE:
            pass
        elif (
            state is self._WinState.FETCHING_FRESH_REQUEST
            or state is self._WinState.REFRESHING
        ):
            self._set_idle_and_schedule_timed_action(response, weakwin)
        else:
            assert_never(state)

    def _set_idle_and_schedule_timed_action(
        self, response: CloudUIResponse, weakwin: weakref.ref[CloudUIWindow]
    ) -> None:
        import bacommon.cloudui.v1 as clui1

        win = weakwin()
        assert win is not None
        assert self._get_win_state(win) is not self._WinState.IDLE
        assert isinstance(response, clui1.Response)

        self._set_win_state(win, self._WinState.IDLE)
        if response.timed_action is not None:

            # Limit delay to .25 seconds or more to prevent excessive
            # churn. Can revisit if there is a strong use case.
            bui.apptimer(
                max(0.250, response.timed_action_delay),
                bui.WeakCallStrict(
                    self._run_timed_action,
                    weakwin,
                    response.timed_action,
                ),
            )

    def _run_timed_action(
        self,
        weakwin: weakref.ref[CloudUIWindow],
        action: bacommon.cloudui.v1.Action,
    ) -> None:
        # If our target window died since we set this timer, no biggie.
        win = weakwin()
        if win is None:
            return

        state = self._get_win_state(win)
        if state is not self._WinState.IDLE:
            bui.uilog.warning(
                'win has non-idle state in _run_timed_action; not expected'
            )
            return
        self.run_action(win, widgetid=None, action=action, is_timed=True)


@dataclass
class CloudUILocalAction:
    """Context for a local-action."""

    name: str
    params: dict
    widget: bui.Widget | None
    window: CloudUIWindow
