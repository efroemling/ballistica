# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui based league presidency ui."""

from typing import override, assert_never, TYPE_CHECKING

import bacommon.docui.routes.classicleaguepresidency as lroutes

from bauiv1lib.docui import TypedDocUIController

import bauiv1 as bui

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.classicleaguepresidency
    from bacommon.docui import DocUIResponse

    from bauiv1lib.docui import DocUILocalAction


class LeaguePresidencyUIController(
    TypedDocUIController[
        lroutes.AnyLeaguePresidencyRoute,
        lroutes.AnyLeaguePresidencyLocalAction,
    ]
):
    """DocUI setup for league presidency."""

    @override
    @classmethod
    def get_route_type(
        cls,
    ) -> type[
        bacommon.docui.routes.classicleaguepresidency.LeaguePresidencyRoute
    ]:
        return lroutes.LeaguePresidencyRoute

    @override
    @classmethod
    def get_local_action_type(
        cls,
    ) -> type[
        (
            bacommon.docui.routes.classicleaguepresidency
        ).LeaguePresidencyLocalAction
    ]:
        return lroutes.LeaguePresidencyLocalAction

    @override
    def fulfill_route(
        self,
        route: (
            bacommon.docui.routes.classicleaguepresidency
        ).AnyLeaguePresidencyRoute,
    ) -> DocUIResponse:
        return self.fulfill_request_cloud(route, 'classicleaguepresidency')

    @override
    def fulfill_unrouted_request(
        self, request: bacommon.docui.v2.Request, error: str
    ) -> DocUIResponse:
        # Something newer than us from the server; let it handle it.
        return self.fulfill_request_cloud(request, 'classicleaguepresidency')

    @override
    def run_local_action(
        self,
        action: (
            bacommon.docui.routes.classicleaguepresidency
        ).AnyLeaguePresidencyLocalAction,
        context: DocUILocalAction,
    ) -> None:
        match action:
            case lroutes.GetTokens():
                self._get_tokens(context)
            case _:
                assert_never(action)

    def _get_tokens(self, action: DocUILocalAction) -> None:
        from bauiv1lib.gettokens import show_get_tokens_window

        bui.play_swish()
        show_get_tokens_window(origin_widget=bui.existing(action.widget))
