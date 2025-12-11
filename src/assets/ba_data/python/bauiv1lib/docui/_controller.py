# Released under the MIT License. See LICENSE for details.
#
"""Controller functionality for DocUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never
from dataclasses import dataclass
from enum import Enum
import weakref

from efro.util import asserttype
from efro.error import CleanError, CommunicationError
from efro.dataclassio import dataclass_to_json, dataclass_from_json
from bacommon.docui import (
    DocUIRequestTypeID,
    UnknownDocUIRequest,
    DocUIResponseTypeID,
    UnknownDocUIResponse,
    DocUIWebRequest,
    DocUIWebResponse,
)
import bauiv1 as bui

from bauiv1lib.docui._window import DocUIWindow

if TYPE_CHECKING:
    from typing import Callable

    import bacommon.docui.v1
    from bacommon.docui import DocUIRequest, DocUIResponse
    import bacommon.clienteffect as clfx

    from bauiv1lib.docui import v1prep


class _WinState(Enum):
    """Per-window state."""

    FETCHING_FRESH_REQUEST = 0
    REDISPLAYING_OLD_STATE = 1
    REFRESHING = 2
    ERRORED = 3
    IDLE = 4


@dataclass
class _WinData:
    state: _WinState
    refresh_timer: bui.AppTimer | None = None


class DocUIController:
    """Manages interactions between DocUI clients and servers.

    Can include logic to handle all requests locally or can submit them
    to be handled by some server or can do some combination thereof.
    """

    class ErrorType(Enum):
        """Types of errors that can occur in request processing."""

        GENERIC = 'generic'
        UNDER_CONSTRUCTION = 'under_construction'
        COMMUNICATION_ERROR = 'communication'
        NEED_UPDATE = 'need_update'

    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        """Handle request fulfillment.

        Expected to be overridden by child classes.

        Be aware that this will always be called in a background thread.

        This method is expected to always return a response, even in the
        case of errors. Use
        :meth:`~bauiv1lib.docui.DocUIController.error_response()` to
        translate error conditions to responses.

        The one exception to this rule (no pun intended) is the
        :class:`efro.error.CleanError` exception. This can be raised as a
        quick and dirty way to show custom error messages. The code
        ``raise CleanError('Something broke.')`` will have the same
        effect as ``return self.error_response(custom_message='Something
        broke.')``.
        """
        raise NotImplementedError()

    def local_action(self, action: DocUILocalAction) -> None:
        """Do something locally on behalf of the doc-ui.

        Controller classes can override this to expose named actions
        that can be triggered by doc-ui button presses, responses,
        etc.

        Of course controllers can also perform arbitrary local actions
        alongside their normal request fulfillment; this is simply a way
        to do so without needing to provide actual ui pages alongside.

        Be *very* careful and focused with what you expose here,
        especially if your doc-ui pages are coming from untrusted
        sources. Generally things like launching or joining games are
        good candidates for local actions.
        """

    def fulfill_request_web(
        self, request: DocUIRequest, url: str
    ) -> DocUIResponse:
        """Fulfill a request by sending it to a webserver."""
        import bacommon.docui.v1 as dui1

        import urllib3.util

        if not isinstance(request, dui1.Request):
            raise RuntimeError(f'Unsupported docui request: {type(request)}')

        upool = bui.app.net.urllib3pool

        # Allow compressed results.
        headers = urllib3.util.make_headers(accept_encoding=True)

        # Bundle our doc-ui request with some extra stuff that might
        # be relevant to a remote server (language we're using, etc.).
        webrequest = DocUIWebRequest(
            doc_ui_request=request,
            locale=bui.app.locale.current_locale,
            engine_build_number=bui.app.env.engine_build_number,
        )

        try:
            # Map docui GET requests to http GET and POST to POST.
            if request.method is dui1.RequestMethod.GET:
                # For GET we embed the request into a url param.
                raw_response = upool.request(
                    'GET',
                    url,
                    fields={
                        'doc_ui_web_request': dataclass_to_json(webrequest)
                    },
                    headers=headers,
                )

            elif request.method is dui1.RequestMethod.POST:
                # for POST we send the webrequest as json in body.
                headers['Content-Type'] = 'application/json'
                raw_response = upool.request(
                    'POST',
                    url,
                    headers=headers,
                    body=dataclass_to_json(webrequest),
                )
            elif request.method is dui1.RequestMethod.UNKNOWN:
                raise RuntimeError('Unknown request method.')
            else:
                assert_never(request.method)

            try:
                # We use 'lossy' here so response versions or elements
                # that we don't know about will come through as
                # 'Unknown' types instead of erroring completely.
                webresponse = dataclass_from_json(
                    DocUIWebResponse, raw_response.data.decode(), lossy=True
                )
                if (
                    webresponse.error is None
                    and webresponse.doc_ui_response is None
                ):
                    raise RuntimeError(
                        'Invalid webresponse includes neither error'
                        ' nor doc-ui-response.'
                    )
            except Exception as exc:
                bui.netlog.info(
                    'Error reading docui web-response.', exc_info=True
                )
                raise RuntimeError('Error reading docui web-response.') from exc

            # For now, consider all errors communication errors (should
            # result in retry buttons in some cases). Can get more
            # specific in the future for cases where retries would not
            # help.
            if raw_response.status != 200:

                # If the response bundled an error, log it.
                if webresponse.error is not None:
                    bui.netlog.info(
                        'doc-ui http request returned error: %s',
                        webresponse.error,
                    )
                return self.error_response(
                    request, self.ErrorType.COMMUNICATION_ERROR
                )

        except Exception:
            # For now, consider all errors communication errors (should
            # result in retry buttons in some cases). Can get more
            # specific in the future for cases where retries would not
            # help.
            bui.netlog.info('Error in docui http request.', exc_info=True)
            return self.error_response(
                request, self.ErrorType.COMMUNICATION_ERROR
            )

        assert webresponse.doc_ui_response is not None
        return webresponse.doc_ui_response

    def fulfill_request_cloud(
        self, request: DocUIRequest, domain: str
    ) -> DocUIResponse:
        """Fulfill a request by sending it to ballistica's cloud.

        :meta private:
        """
        import bacommon.cloud

        try:
            plus = bui.app.plus
            if plus is None:
                raise RuntimeError('Plus not available.')

            account = plus.accounts.primary
            if account is not None:
                with account:
                    mresponse = plus.cloud.send_message(
                        bacommon.cloud.FulfillDocUIRequest(
                            request=request, domain=domain
                        )
                    )
            else:
                mresponse = plus.cloud.send_message(
                    bacommon.cloud.FulfillDocUIRequest(
                        request=request, domain=domain
                    )
                )
            assert isinstance(mresponse, bacommon.cloud.FulfillDocUIResponse)

            return mresponse.response

        except CommunicationError:
            # Label comm-errors so we can possibly show retry buttons.
            return self.error_response(
                request, self.ErrorType.COMMUNICATION_ERROR
            )
        except Exception:
            return self.error_response(request)

    def error_response(
        self,
        request: DocUIRequest,
        error_type: ErrorType = ErrorType.GENERIC,
        custom_message: str | None = None,
    ) -> DocUIResponse:
        """Build a simple error message page.

        A message is included based on ``error_type``. Pass
        ``custom_message`` to override this.

        Messages will be translated to the client language using the
        'serverResponses' Lstr translation category.
        """
        import bacommon.docui.v1 as dui1

        error_msg: bui.Lstr | None = None
        error_msg_simple: str | None = None

        status_code = dui1.ResponseStatus.UNKNOWN_ERROR

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
                status_code = dui1.ResponseStatus.COMMUNICATION_ERROR
                error_msg_simple = 'Error talking to server.'
            else:
                assert_never(error_type)
        if error_msg_simple is not None:
            error_msg = bui.Lstr(
                translate=('serverResponses', error_msg_simple)
            )
        assert error_msg is not None

        debug = False

        # Give a retry button for comm-errors on GET requests (POSTs may
        # have unintentional side-effects so holding off on those for
        # now).
        do_retry = (
            isinstance(request, dui1.Request)
            and request.method is dui1.RequestMethod.GET
            and status_code is dui1.ResponseStatus.COMMUNICATION_ERROR
        )

        return dui1.Response(
            status=status_code,
            page=dui1.Page(
                title=bui.Lstr(resource='errorText').as_json(),
                title_is_lstr=True,
                center_vertically=True,
                rows=[
                    dui1.ButtonRow(
                        buttons=[
                            dui1.Button(
                                bui.Lstr(
                                    resource=(
                                        'retryText' if do_retry else 'okText'
                                    )
                                ).as_json(),
                                (
                                    dui1.Replace(
                                        asserttype(request, dui1.Request)
                                    )
                                    if do_retry
                                    else dui1.Local(close_window=True)
                                ),
                                label_is_lstr=True,
                                default=True,
                                style=dui1.ButtonStyle.MEDIUM,
                                size=(130, 50),
                                padding_left=200,
                                padding_right=200,
                                padding_top=100,
                                decorations=[
                                    dui1.Text(
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
        request: DocUIRequest,
        *,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
        uiopenstateid: str | None = None,
        suppress_win_extra_type_warning: bool = False,
    ) -> DocUIWindow:
        """Create a new window to handle a request."""
        assert bui.in_logic_thread()

        # Create a shiny new window.
        win = DocUIWindow(
            self,
            request,
            transition=transition,
            origin_widget=origin_widget,
            auxiliary_style=auxiliary_style,
            uiopenstateid=uiopenstateid,
            suppress_win_extra_type_warning=suppress_win_extra_type_warning,
        )
        self._set_win_data(win, _WinData(_WinState.FETCHING_FRESH_REQUEST))

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

    def save_window_shared_state(
        self, window: DocUIWindow, state: dict
    ) -> None:
        """Called when a window shared state is being saved."""
        del window, state  # Unused.

    def restore_window_shared_state(
        self, window: DocUIWindow, state: dict
    ) -> None:
        """Called when a window shared state is being restored."""
        del window, state  # Unused.

    @classmethod
    def get_window_extra_type_id(cls) -> str:
        """Return a string suitable for the ``window_extra_type_id`` arg to
        :meth:`~bauiv1.UIV1AppSubsystem.auxiliary_window_activate()`.

        This ensures your doc-ui window is identified distinctly from
        other doc-ui windows for navigation purposes.
        """
        # Include the full path of our controller class.
        return f'docui:{cls.__module__}.{cls.__qualname__}'

    def restore(
        self,
        win: DocUIWindow,
        *,
        last_response: DocUIResponse | None,
        has_had_response: bool,
    ) -> DocUIWindow:
        """Restore a window from previous state.

        May immediately display old results or may kick off a new
        request.
        """
        import bacommon.docui.v1 as dui1

        assert bui.in_logic_thread()

        explicit_response: DocUIResponse | None = None
        explicit_error: DocUIController.ErrorType | None = None

        if last_response is not None:
            # Re-prep our restored response so we have something to show
            # immediately. We'll then fetch an updated version in the
            # background to get the latest version.
            explicit_response = last_response
        else:
            # We have no previous response to restore. Fetch a new one.

            # If the current request is a POST, never auto-refetch. Just
            # build an error response.
            assert isinstance(win.request, dui1.Request)
            if win.request.method is dui1.RequestMethod.POST:
                # Do we want a specific error for this? Though this case
                # should be rare I think.
                explicit_error = self.ErrorType.GENERIC
            else:
                explicit_error = None

        # We're either errored or redisplaying an old state.
        if explicit_error is None:
            self._set_win_data(win, _WinData(_WinState.REDISPLAYING_OLD_STATE))
        else:
            self._set_win_data(win, _WinData(_WinState.ERRORED))

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
                # If this window has had a response already, snap things
                # in immediately with no transitions.
                immediate=has_had_response,
                explicit_error=explicit_error,
                explicit_response=explicit_response,
            )
        )
        return win

    def replace(
        self,
        win: DocUIWindow,
        request: DocUIRequest,
        *,
        origin_widget: bui.Widget | None = None,
        is_refresh: bool = False,
    ) -> None:
        """Kick off a request to replace existing window contents."""
        import bacommon.docui.v1 as dui1

        assert bui.in_logic_thread()

        win.request = request

        requesttype = request.get_type_id()

        if requesttype is DocUIRequestTypeID.V1:
            assert isinstance(win.request, dui1.Request)

            self._set_win_data(
                win,
                (
                    _WinData(
                        _WinState.REFRESHING
                        if is_refresh
                        else _WinState.FETCHING_FRESH_REQUEST
                    )
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
        elif requesttype is DocUIRequestTypeID.UNKNOWN:
            assert isinstance(win.request, UnknownDocUIRequest)
            # Got a request type we don't know. Show a 'need a newer
            # build' error.

            self._set_win_data(win, _WinData(_WinState.ERRORED))

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
        window: DocUIWindow,
        widgetid: str | None,
        action: bacommon.docui.v1.Action | None,
        is_timed: bool = False,
    ) -> None:
        """Called when a button is pressed in a v1 ui."""
        # pylint: disable=too-many-branches
        # pylint: disable=cyclic-import

        import bacommon.docui.v1 as dui

        assert bui.in_logic_thread()

        # If locked, been and tell them to try again.
        if window.locked:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource='pageRefreshingTryAgainText'), color=(1, 0, 0)
            )
            return

        widget: bui.Widget | None

        if widgetid is not None:
            # Find the associated button.
            widget = bui.widget_by_id(widgetid)
            if widget is None:
                bui.uilog.warning(
                    'DocUI button press widget not found: %s (not expected)',
                    widgetid,
                )
                return
        else:
            widget = None

        # Play error beeps on buttons with no actions assigned to let
        # the user know nothing is supposed to happen.
        if action is None:
            bui.getsound('error').play()
            return

        action_type = action.get_type_id()

        if action_type is dui.ActionTypeID.BROWSE:
            assert isinstance(action, dui.Browse)
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
                        suppress_win_extra_type_warning=True,
                    )
                )

                self._run_immediate_effects_and_actions(
                    client_effects=action.immediate_client_effects,
                    local_action=action.immediate_local_action,
                    local_action_args=action.immediate_local_action_args,
                    widget=widget,
                    window=window,
                    is_timed=is_timed,
                )

        elif action_type is dui.ActionTypeID.REPLACE:
            assert isinstance(action, dui.Replace)

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
                local_action_args=action.immediate_local_action_args,
                widget=widget,
                window=window,
                is_timed=is_timed,
            )

        elif action_type is dui.ActionTypeID.LOCAL:
            assert isinstance(action, dui.Local)
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
                local_action_args=action.immediate_local_action_args,
                widget=widget,
                window=window,
                is_timed=is_timed,
            )
        elif action_type is dui.ActionTypeID.UNKNOWN:
            assert isinstance(action, dui.UnknownAction)
            bui.screenmessage('Unknown action.', color=(1, 0, 0))
            bui.getsound('error').play()
        else:
            # Make sure we handle all options.
            assert_never(action_type)

    def _run_immediate_effects_and_actions(
        self,
        *,
        client_effects: list[clfx.Effect],
        local_action: str | None,
        local_action_args: dict | None,
        widget: bui.Widget | None,
        window: DocUIWindow,
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
                    DocUILocalAction(
                        name=local_action,
                        args=(
                            {}
                            if local_action_args is None
                            else local_action_args
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

    def _get_win_data(self, window: DocUIWindow) -> _WinData:
        val = getattr(window, '_wcdata')
        assert isinstance(val, _WinData)
        return val

    def _set_win_data(self, window: DocUIWindow, data: _WinData) -> None:
        setattr(window, '_wcdata', data)

    def _process_request_in_bg(
        self,
        request: DocUIRequest,
        *,
        weakwin: weakref.ref[DocUIWindow],
        uiscale: bui.UIScale,
        scroll_width: float,
        scroll_height: float,
        idprefix: str,
        immediate: bool,
        explicit_error: ErrorType | None = None,
        explicit_response: DocUIResponse | None = None,
    ) -> None:
        """Wrangle a request from within a background thread.

        This will always return a response, even on error conditions.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        import bacommon.docui.v1 as dui1
        from bauiv1lib.docui import v1prep

        assert not bui.in_logic_thread()

        response: DocUIResponse | None = None
        error: DocUIController.ErrorType | None = None

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
                response = self.error_response(request, custom_message=str(exc))

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

            if responsetype is DocUIResponseTypeID.V1:

                assert isinstance(response, dui1.Response)

                # If they require a build-number newer than us, say so.
                minbuild = response.minimum_engine_build
                if (
                    minbuild is not None
                    and minbuild > bui.app.env.engine_build_number
                ):
                    error = self.ErrorType.NEED_UPDATE

            elif responsetype is DocUIResponseTypeID.UNKNOWN:
                assert isinstance(response, UnknownDocUIResponse)
                bui.uilog.debug(
                    'Got unsupported docui response.', exc_info=True
                )
                error = self.ErrorType.NEED_UPDATE
                response = None
            else:
                # Make sure we cover all types we're aware of.
                assert_never(responsetype)

        if error is not None:
            response = self.error_response(request, error)

        # Currently must be v1 if it made it to here.
        assert isinstance(response, dui1.Response)

        pageprep = v1prep.prep_page(
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
        response: DocUIResponse,
        weakwin: weakref.ref[DocUIWindow],
        pageprep: v1prep.PagePrep,
    ) -> None:
        import bacommon.docui.v1 as dui1

        assert bui.in_logic_thread()

        # If our target window died since we made the request, no
        # biggie.
        win = weakwin()
        if win is None:
            return

        # Currently should only be sending ourself v1 responses here.
        assert isinstance(response, dui1.Response)

        win.unlock_ui()
        win.set_last_response(
            response,
            response.status == dui1.ResponseStatus.SUCCESS,
        )

        # Set the UI.
        win.instantiate_ui(pageprep)

        state = self._get_win_data(win).state

        # Run client-effects and local-actions ONLY after fresh requests
        # (don't want sounds and other actions firing when we navigate
        # back or resize a window).
        if state is _WinState.FETCHING_FRESH_REQUEST:
            if response.client_effects and bui.app.classic is not None:
                bui.app.classic.run_bs_client_effects(response.client_effects)
            if response.local_action is not None:
                try:
                    self.local_action(
                        DocUILocalAction(
                            name=response.local_action,
                            args=(
                                {}
                                if response.local_action_args is None
                                else response.local_action_args
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
        if state is _WinState.REDISPLAYING_OLD_STATE:
            # Ok; we're done showing old state. For POST this is as far
            # as we go (don't want to repeat POST effects), but for GET
            # we can now kick off a refresh to swap in the latest
            # version of the page.
            assert isinstance(win.request, dui1.Request)
            if win.request.method is dui1.RequestMethod.GET:
                self.replace(win, win.request, is_refresh=True)
            elif (
                win.request.method is dui1.RequestMethod.POST
                or win.request.method is dui1.RequestMethod.UNKNOWN
            ):
                self._set_idle_and_schedule_timed_action(response, weakwin)
            else:
                assert_never(win.request.method)

        elif state is _WinState.ERRORED or state is _WinState.IDLE:
            pass
        elif (
            state is _WinState.FETCHING_FRESH_REQUEST
            or state is _WinState.REFRESHING
        ):
            self._set_idle_and_schedule_timed_action(response, weakwin)
        else:
            assert_never(state)

    def _set_idle_and_schedule_timed_action(
        self, response: DocUIResponse, weakwin: weakref.ref[DocUIWindow]
    ) -> None:
        import bacommon.docui.v1 as dui1

        win = weakwin()
        assert win is not None
        assert self._get_win_data(win).state is not _WinState.IDLE
        assert isinstance(response, dui1.Response)

        refresh_timer: bui.AppTimer | None = None

        if response.timed_action is not None:

            # Limit delay to .25 seconds or more to prevent excessive
            # churn. Can revisit if there is a strong use case.
            refresh_timer = bui.AppTimer(
                max(0.250, response.timed_action_delay),
                bui.WeakCallStrict(
                    self._run_timed_action,
                    weakwin,
                    response.timed_action,
                ),
            )
        self._set_win_data(win, _WinData(_WinState.IDLE, refresh_timer))

    def _run_timed_action(
        self,
        weakwin: weakref.ref[DocUIWindow],
        action: bacommon.docui.v1.Action,
    ) -> None:
        # If our target window died since we set this timer, no biggie.
        win = weakwin()
        if win is None:
            return

        state = self._get_win_data(win).state
        if state is not _WinState.IDLE:
            bui.uilog.warning(
                'win has non-idle state in _run_timed_action; not expected'
            )
            return
        self.run_action(win, widgetid=None, action=action, is_timed=True)


@dataclass
class DocUILocalAction:
    """Context for a local-action."""

    name: str
    args: dict
    widget: bui.Widget | None
    window: DocUIWindow
