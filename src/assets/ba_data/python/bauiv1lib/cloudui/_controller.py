# Released under the MIT License. See LICENSE for details.
#
"""Controller functionality for CloudUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never
from dataclasses import dataclass
from enum import Enum
import weakref

from efro.error import CleanError
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

    from bacommon.cloudui import CloudUIRequest, CloudUIResponse


class CloudUIController:
    """Manages interactions between CloudUI clients and servers.

    Can include logic to handle all requests locally or can submit them
    to be handled by some server or can do some combination thereof.
    """

    class ErrorType(Enum):
        """Types of errors that can occur in request processing."""

        GENERIC = 'generic'
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

        if custom_message is not None:
            error_msg = custom_message
        else:
            if error_type is self.ErrorType.GENERIC:
                error_msg = 'An error has occurred; please try again later.'
            elif error_type is self.ErrorType.NEED_UPDATE:
                error_msg = 'You must update the app to view this.'
            else:
                assert_never(error_type)

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
                                is_start_button=True,
                                style=clui1.ButtonStyle.MEDIUM,
                                size=(130, 50),
                                padding_left=200,
                                padding_right=200,
                                padding_top=100,
                                decorations=[
                                    clui1.Text(
                                        bui.Lstr(
                                            translate=(
                                                'serverResponses',
                                                error_msg,
                                            )
                                        ).as_json(),
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
        last_response_success: bool,
    ) -> CloudUIWindow:
        """Restore a window from previous state.

        May immediately display old results or may kick off a new
        request.
        """
        import bacommon.cloudui.v1 as clui1

        assert bui.in_logic_thread()

        can_reuse_response = True
        if last_response is None:
            can_reuse_response = False
        elif not last_response_success:
            can_reuse_response = False
        # TODO: Check cache times/invalidation/etc.

        explicit_response: CloudUIResponse | None = None
        explicit_error: CloudUIController.ErrorType | None = None

        if can_reuse_response:
            print('REUSING RESPONSE')
            # Re-prep our last response.
            explicit_response = last_response
        else:
            # Seems we need to fetch a new response.

            print('FETCHING NEW RESPONSE')
            # If the current request is a POST, never auto-refetch. Just
            # build an error response.
            assert isinstance(win.request, clui1.Request)
            if win.request.method is clui1.RequestMethod.POST:
                # Do we want a specific error for this? Though this case
                # should be rare I think.
                explicit_error = self.ErrorType.GENERIC
            else:
                explicit_error = None

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
                # FIXME: Non-immediate could be appropriate here in
                # *some* cases, right? (like if we're re-submitting a
                # request that was originally non-immediate). Just want
                # to avoid rapid-fire non-immediate restores from window
                # resizes/etc.
                immediate=True,
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
    ) -> None:
        """Kick off a request to replace existing window contents."""
        import bacommon.cloudui.v1 as clui1

        assert bui.in_logic_thread()

        win.request = request

        # If the current request is a POST, never auto-refetch. Just
        # build an error response.
        requesttype = request.get_type_id()

        if requesttype is CloudUIRequestTypeID.V1:
            assert isinstance(win.request, clui1.Request)

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

        response_is_fresh = True

        if explicit_error is not None:
            error = explicit_error
        elif explicit_response is not None:
            response = explicit_response
            response_is_fresh = False
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
                minbuild = response.page.minimum_engine_build
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
                response_is_fresh,
            ),
            from_other_thread=True,
        )

    def _handle_response_in_ui_thread(
        self,
        response: CloudUIResponse,
        weakwin: weakref.ref[CloudUIWindow],
        pageprep: CloudUIPagePrep,
        response_is_fresh: bool,
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

        # Run any effects ONLY when the response is fresh (don't want
        # sounds/etc when we navigate back or resize a window).
        if response_is_fresh and response.effects:
            if bui.app.classic is not None:
                bui.app.classic.run_bs_client_effects(response.effects)


@dataclass
class CloudUILocalAction:
    """Context for a local-action."""

    name: str
    params: dict
    widget: bui.Widget
    window: CloudUIWindow
