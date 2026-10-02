# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui based inbox."""

from typing import override, assert_never, TYPE_CHECKING

import bacommon.docui.routes.classicinbox as iroutes

from bauiv1lib.docui import TypedDocUIController

import bauiv1 as bui

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.classicinbox
    from bacommon.docui import DocUIResponse

    from bauiv1lib.docui import DocUILocalAction


class InboxUIController(
    TypedDocUIController[iroutes.AnyInboxRoute, iroutes.AnyInboxLocalAction]
):
    """DocUI setup for the inbox."""

    @override
    @classmethod
    def get_route_type(
        cls,
    ) -> type[bacommon.docui.routes.classicinbox.InboxRoute]:
        return iroutes.InboxRoute

    @override
    @classmethod
    def get_local_action_type(
        cls,
    ) -> type[bacommon.docui.routes.classicinbox.InboxLocalAction]:
        return iroutes.InboxLocalAction

    @override
    def fulfill_route(
        self, route: bacommon.docui.routes.classicinbox.AnyInboxRoute
    ) -> DocUIResponse:
        return self.fulfill_request_cloud(route, 'classicinbox')

    @override
    def fulfill_unrouted_request(
        self, request: bacommon.docui.v2.Request, error: str
    ) -> DocUIResponse:
        # Something newer than us from the server; let it handle it.
        return self.fulfill_request_cloud(request, 'classicinbox')

    @override
    def run_local_action(
        self,
        action: bacommon.docui.routes.classicinbox.AnyInboxLocalAction,
        context: DocUILocalAction,
    ) -> None:
        match action:
            case iroutes.OpenUrl():
                bui.open_url(action.url)
            case iroutes.TourneyScores():
                self._show_tourney_scores(action.tournament_id, context)
            case _:
                assert_never(action)

    def _show_tourney_scores(
        self, tournament_id: str, context: DocUILocalAction
    ) -> None:
        from bauiv1lib.tournamentscores import TournamentScoresWindow

        widget = bui.existing(context.widget)
        TournamentScoresWindow(
            tournament_id=tournament_id,
            position=(
                (0.0, 0.0)
                if widget is None
                else widget.get_screen_space_center()
            ),
        )


def show_inbox_window(origin_widget: bui.Widget | None = None) -> None:
    """Pop up the inbox wherever we are in the nav stack."""
    from bauiv1lib.docui import DocUIWindow

    bui.app.ui_v1.auxiliary_window_activate(
        win_type=DocUIWindow,
        win_create_call=bui.CallStrict(
            InboxUIController().create_window,
            iroutes.Root(),
            origin_widget=origin_widget,
            uiopenstateid='classicinbox',
        ),
        win_extra_type_id=InboxUIController.get_window_extra_type_id(),
    )
