# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui pages about an account, from the master server.

The ``classicaccount`` domain (see
:mod:`bacommon.docui.routes.classicaccount`). Other domains' pages
open these through local-actions of their own, via
:meth:`bauiv1lib.docui.TypedDocUIController.browse_from` on a
:class:`ClassicAccountUIController`.
"""

from typing import TYPE_CHECKING, override, assert_never

import bacommon.docui.routes.classicaccount as aroutes

from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.classicaccount
    from bacommon.docui import DocUIResponse

    from bauiv1lib.docui import DocUILocalAction


class ClassicAccountUIController(
    TypedDocUIController[
        aroutes.AnyClassicAccountRoute,
        aroutes.AnyClassicAccountLocalAction,
    ]
):
    """DocUI setup for account pages."""

    @override
    @classmethod
    def get_route_type(cls) -> type[aroutes.ClassicAccountRoute]:
        return aroutes.ClassicAccountRoute

    @override
    @classmethod
    def get_local_action_type(
        cls,
    ) -> type[aroutes.ClassicAccountLocalAction]:
        return aroutes.ClassicAccountLocalAction

    @override
    def fulfill_route(
        self, route: bacommon.docui.routes.classicaccount.AnyClassicAccountRoute
    ) -> DocUIResponse:
        return self.fulfill_request_cloud(route, 'classicaccount')

    @override
    def fulfill_unrouted_request(
        self, request: bacommon.docui.v2.Request, error: str
    ) -> DocUIResponse:
        # Something newer than us from the server; let it handle it.
        return self.fulfill_request_cloud(request, 'classicaccount')

    @override
    def run_local_action(
        self,
        action: (
            bacommon.docui.routes.classicaccount.AnyClassicAccountLocalAction
        ),
        context: DocUILocalAction,
    ) -> None:
        match action:
            case aroutes.Placeholder():
                pass
            case _:
                assert_never(action)
