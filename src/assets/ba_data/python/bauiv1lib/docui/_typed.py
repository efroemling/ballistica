# Released under the MIT License. See LICENSE for details.
#
"""Type-safe controller functionality for DocUI."""

from typing import TYPE_CHECKING, cast, override, final

from efro.util import strip_exception_tracebacks
from efro.error import CleanError
import bauiv1 as bui
from bauiv1 import _builtinassets

from bauiv1lib.docui._controller import DocUIController

if TYPE_CHECKING:
    import bacommon.docui.v2
    from bacommon.docui import DocUIRequest, DocUIResponse
    from bacommon.docui.routes import (
        DocUIRoute,
        DocUILocalActionBase,
        PressSound,
    )

    from bauiv1lib.docui._types import DocUILocalAction
    from bauiv1lib.docui._window import DocUIWindow


class TypedDocUIController[
    RouteT: DocUIRoute,
    ActionT: DocUILocalActionBase,
](DocUIController):
    """A controller working in type-safe routes and local-actions.

    Where a plain :class:`~bauiv1lib.docui.DocUIController` deals in
    request paths, arg dicts, and local-action names, this deals purely
    in the dataclasses a domain defines for such things (see
    :mod:`bacommon.docui.routes`). Pass the domain's route and
    local-action unions as type args, point :meth:`get_route_type` and
    :meth:`get_local_action_type` at the matching family classes, and
    implement :meth:`fulfill_route` and :meth:`run_local_action`.
    """

    @classmethod
    def get_route_type(cls) -> type[DocUIRoute]:
        """Return the family class for the routes we handle."""
        raise NotImplementedError()

    @classmethod
    def get_local_action_type(cls) -> type[DocUILocalActionBase]:
        """Return the family class for the local-actions we handle.

        Domains with no local-actions can leave this as is and pass
        :class:`typing.Never` as their local-action type arg.
        """
        from bacommon.docui.routes import NoLocalActions

        return NoLocalActions

    def fulfill_route(self, route: RouteT) -> DocUIResponse:
        """Handle fulfillment for a route.

        The type-safe equivalent of
        :meth:`~bauiv1lib.docui.DocUIController.fulfill_request`; the
        same rules apply (called in a background thread; should always
        return a response).
        """
        raise NotImplementedError()

    def fulfill_unrouted_request(
        self, request: bacommon.docui.v2.Request, error: str
    ) -> DocUIResponse:
        """Handle a request that maps to none of our routes.

        The default shows ``error``. Controllers fronting a server
        should generally forward the request as-is here instead; a
        server is free to grow pages (or arg values) that older clients
        have no routes for, and those should keep working.
        """
        del request  # Unused.
        raise CleanError(error)

    def get_window_route(self, window: DocUIWindow) -> RouteT | None:
        """Return the route a window is showing, if it maps to one."""
        import bacommon.docui.v2 as dui2
        from bacommon.docui.routes import DocUIRouteError

        request = window.request
        if not isinstance(request, dui2.Request):
            return None
        try:
            return cast('RouteT', self.get_route_type().from_request(request))
        except DocUIRouteError as exc:
            strip_exception_tracebacks(exc)
            return None

    def run_local_action(
        self, action: ActionT, context: DocUILocalAction
    ) -> None:
        """Do something locally on behalf of the doc-ui.

        The type-safe equivalent of
        :meth:`~bauiv1lib.docui.DocUIController.local_action`; the
        same cautions apply. The original action is passed as
        ``context`` for access to the originating widget and window.
        """

    @override
    @final
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        import bacommon.docui.v2 as dui2
        from bacommon.docui.routes import DocUIRouteError, validate_page_state

        if not isinstance(request, dui2.Request):
            raise CleanError('Invalid request version.')
        try:
            route = self.get_route_type().from_request(request)
        except DocUIRouteError as exc:
            error = str(exc)
            strip_exception_tracebacks(exc)
            return self.fulfill_unrouted_request(request, error)

        # The family class only promises *some* member of the family;
        # our RouteT union is exactly the set of members. (Type args
        # quoted since pylint doesn't see class-scoped type params.)
        response = self.fulfill_route(cast('RouteT', route))

        # Catch pages whose inputs/sets don't match their state type
        # (nothing static can; see validate_page_state()).
        if isinstance(response, dui2.Response):
            validate_page_state(response.page)
        return response

    @override
    def get_local_action_press_sound(self, name: str) -> PressSound:
        return self.get_local_action_type().press_sound_for_name(name)

    @override
    @final
    def local_action(self, action: DocUILocalAction) -> None:
        from bacommon.docui.routes import DocUIRouteError

        try:
            typedaction = self.get_local_action_type().from_name_and_args(
                action.name, action.args
            )
        except DocUIRouteError as exc:
            bui.uilog.warning('Ignoring doc-ui local-action: %s', exc)
            bui.screenmessage(str(exc), color=(1, 0, 0))
            _builtinassets.audio.error.get().play()
            strip_exception_tracebacks(exc)
            return

        self.run_local_action(cast('ActionT', typedaction), action)
