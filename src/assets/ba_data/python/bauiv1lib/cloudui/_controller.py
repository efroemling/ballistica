# Released under the MIT License. See LICENSE for details.
#
"""Controller functionality for CloudUI."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never
import weakref

from bacommon.cloudui import CloudUIResponseTypeID, UnknownCloudUIResponse
import bauiv1 as bui

from bauiv1lib.cloudui._window import CloudUIWindow

if TYPE_CHECKING:
    from typing import Callable

    from bacommon.cloudui import CloudUIRequest, CloudUIResponse


class CloudUIController:
    """Manages interactions between CloudUI clients and servers.

    Can include logic to handle all requests locally or can submit them
    to be handled by some server or can do some combination thereof.
    """

    def __init__(self) -> None:
        pass

    def create_window(self, request: CloudUIRequest) -> CloudUIWindow:
        """Create a window for some initial request."""
        assert bui.in_logic_thread()
        win = CloudUIWindow(state=None)

        bui.app.threadpool.submit_no_wait(
            bui.CallStrict(self._request_in_bg, request, weakref.ref(win))
        )
        return win

    def _error_response(self) -> CloudUIResponse:
        """Build a simple error dialog."""
        import bacommon.cloudui.v1 as clui1

        debug = True
        return clui1.Response(
            code=clui1.ResponseCode.UNKNOWN_ERROR,
            page=clui1.Page(
                title=bui.Lstr(resource='errorText').as_json(),
                title_is_lstr=True,
                center_vertically=True,
                rows=[
                    clui1.Row(
                        buttons=[
                            clui1.Button(
                                bui.Lstr(resource='okText').as_json(),
                                text_is_lstr=True,
                                style=clui1.Button.Style.MEDIUM,
                                size=(130, 50),
                                padding_left=200,
                                padding_right=200,
                                padding_top=100,
                                decorations=[
                                    clui1.Text(
                                        bui.Lstr(
                                            translate=(
                                                'serverResponses',
                                                'An error has occurred;'
                                                ' please try again later.',
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

    def _request_in_bg(
        self, request: CloudUIRequest, weakwin: weakref.ref[CloudUIWindow]
    ) -> None:
        """Submit a request to the controller.

        This must be called from the UI thread and results will be
        delivered in the UI thread.

        This will always return a response, even on error conditions.
        """
        assert not bui.in_logic_thread()

        response: CloudUIResponse | None

        try:
            response = self.fulfill_request(request)
        except Exception:
            bui.uilog.debug('Error fulfilling cloudui request.', exc_info=True)
            response = None

        # Validate any response we got.
        if response is not None:
            responsetype = response.get_type_id()

            if responsetype is CloudUIResponseTypeID.V1:
                import bacommon.cloudui.v1 as clui1

                assert isinstance(response, clui1.Response)

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
                    response = None
            elif responsetype is CloudUIResponseTypeID.UNKNOWN:
                assert isinstance(response, UnknownCloudUIResponse)
                bui.uilog.debug(
                    'Got unsupported cloudui response.', exc_info=True
                )
                response = None
            else:
                # Make sure we cover all types we're aware of.
                assert_never(responsetype)

        if response is None:
            response = self._error_response()

        # Go ahead and just push the response along with our weakref
        # back to the logic thread for handling. We could quick-out here
        # if the window is dead, but wrangling its refs here could
        # theoretically lead to it being deallocated here which could be
        # problematic.
        bui.pushcall(
            bui.CallStrict(
                self._handle_response_in_ui_thread, response, weakwin
            ),
            from_other_thread=True,
        )

    def _handle_response_in_ui_thread(
        self, response: CloudUIResponse, weakwin: weakref.ref[CloudUIWindow]
    ) -> None:
        import bacommon.cloudui.v1 as clui1

        assert bui.in_logic_thread()

        # Our target window died since we made the request; no biggie.
        win = weakwin()
        if win is None:
            return

        # Currently should only be sending ourself v1 responses here.
        assert isinstance(response, clui1.Response)

        win.set_state(win.State(self, response.page))

    def fulfill_request(self, request: CloudUIRequest) -> CloudUIResponse:
        """Override this to handle request fulfillment.

        Exceptions should be raised for any errors; the base class will
        handle converting those to a Response.

        Be aware that this will always be called in a background thread.
        """
        raise NotImplementedError()
