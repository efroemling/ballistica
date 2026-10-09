# Released under the MIT License. See LICENSE for details.
#
"""The profile editor for a character being previewed.

Opened from the lobby of a character preview session (see
``baclassic._characterpreview``): the cloud's profile editor, aimed at
the previewed character rather than at one of the player's own
profiles. Saving hands the edited character back to the session.
"""

from typing import override, assert_never, TYPE_CHECKING

# (Referred to by its full path throughout: the docs can't follow an
# alias in signatures.)
import bacommon.docui.routes.classiccharacterpreview

from bauiv1lib.docui import TypedDocUIController

import bauiv1 as bui

if TYPE_CHECKING:
    import bacommon.docui.v2
    from bacommon.docui import DocUIResponse

    from bauiv1lib.docui import DocUILocalAction


class CharacterPreviewUIController(
    TypedDocUIController[
        bacommon.docui.routes.classiccharacterpreview.AnyCharacterPreviewRoute,
        (
            bacommon.docui.routes.classiccharacterpreview
        ).AnyCharacterPreviewLocalAction,
    ]
):
    """DocUI setup for editing a previewed character's profile."""

    @override
    @classmethod
    def get_route_type(
        cls,
    ) -> type[
        bacommon.docui.routes.classiccharacterpreview.CharacterPreviewRoute
    ]:
        return (
            bacommon.docui.routes.classiccharacterpreview
        ).CharacterPreviewRoute

    @override
    @classmethod
    def get_local_action_type(
        cls,
    ) -> type[
        (
            bacommon.docui.routes.classiccharacterpreview
        ).CharacterPreviewLocalAction
    ]:
        return (
            bacommon.docui.routes.classiccharacterpreview
        ).CharacterPreviewLocalAction

    @override
    def fulfill_route(
        self,
        route: (
            bacommon.docui.routes.classiccharacterpreview
        ).AnyCharacterPreviewRoute,
    ) -> DocUIResponse:
        return self.fulfill_request_cloud(route, 'classiccharacterpreview')

    @override
    def fulfill_unrouted_request(
        self, request: bacommon.docui.v2.Request, error: str
    ) -> DocUIResponse:
        # Something newer than us from the server; let it handle it.
        return self.fulfill_request_cloud(request, 'classiccharacterpreview')

    @override
    def run_local_action(
        self,
        action: (
            bacommon.docui.routes.classiccharacterpreview
        ).AnyCharacterPreviewLocalAction,
        context: DocUILocalAction,
    ) -> None:
        match action:
            case bacommon.docui.routes.classiccharacterpreview.Saved():
                classic = bui.app.classic
                if classic is not None:
                    classic.character_preview.apply_edit(
                        action.preview_id, action.character
                    )
            case _:
                assert_never(action)


def show_character_preview_editor(preview_id: str) -> None:
    """Open the profile editor for a previewed character.

    For a preview session's lobby, which runs with no main window up.
    """
    if bui.app.ui_v1.get_main_window() is not None:
        # (As for the lobby's regular profile editing: should not
        # happen, and stacking a window on whatever is up would only
        # confuse matters.)
        return

    bui.app.ui_v1.set_main_window(
        CharacterPreviewUIController().create_window(
            bacommon.docui.routes.classiccharacterpreview.Edit(
                preview_id=preview_id
            ),
            uiopenstateid='classiccharacterpreview',
        ),
        is_top_level=True,
        back_state=None,
        suppress_warning=True,
        extra_type_id=CharacterPreviewUIController.get_window_extra_type_id(),
    )
