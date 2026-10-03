# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui based chest window."""

import weakref
from typing import override, assert_never, TYPE_CHECKING

import bacommon.docui.routes.classicchest

from bauiv1lib.docui import TypedDocUIController

import bauiv1 as bui

if TYPE_CHECKING:
    import bacommon.docui.v2
    from bacommon.docui import DocUIResponse

    from bauiv1lib.docui import DocUILocalAction, DocUIWindow

#: Config key for whether to remind about opening chests early.
HIGHLIGHT_TOKEN_PURCHASES_CONFIG_KEY = 'Highlight Potential Token Purchases'


class ChestUIController(
    TypedDocUIController[
        bacommon.docui.routes.classicchest.AnyChestRoute,
        bacommon.docui.routes.classicchest.AnyChestLocalAction,
    ]
):
    """DocUI setup for a chest slot."""

    def __init__(self) -> None:
        super().__init__()
        # Held while an ad is up: showing one can resize our app window
        # (system toolbars coming and going), and a recreated window
        # would cancel the ad flow.
        self._recreate_suppress: bui.MainWindowAutoRecreateSuppress | None = (
            None
        )

    @override
    @classmethod
    def get_route_type(
        cls,
    ) -> type[bacommon.docui.routes.classicchest.ChestRoute]:
        return bacommon.docui.routes.classicchest.ChestRoute

    @override
    @classmethod
    def get_local_action_type(
        cls,
    ) -> type[bacommon.docui.routes.classicchest.ChestLocalAction]:
        return bacommon.docui.routes.classicchest.ChestLocalAction

    @override
    def fulfill_route(
        self, route: bacommon.docui.routes.classicchest.AnyChestRoute
    ) -> DocUIResponse:
        return self.fulfill_request_cloud(route, 'classicchest')

    @override
    def fulfill_unrouted_request(
        self, request: bacommon.docui.v2.Request, error: str
    ) -> DocUIResponse:
        # Something newer than us from the server; let it handle it.
        return self.fulfill_request_cloud(request, 'classicchest')

    @override
    def run_local_action(
        self,
        action: bacommon.docui.routes.classicchest.AnyChestLocalAction,
        context: DocUILocalAction,
    ) -> None:
        match action:
            case bacommon.docui.routes.classicchest.WatchAd():
                self._watch_ad(action.slot, context.window)
            case bacommon.docui.routes.classicchest.StopReminding():
                bui.app.config[HIGHLIGHT_TOKEN_PURCHASES_CONFIG_KEY] = False
                bui.app.config.apply_and_commit()
                self.replace(
                    context.window,
                    slot_route(action.slot).request(),
                    is_refresh=True,
                )
            case bacommon.docui.routes.classicchest.GetTokens():
                # pylint: disable=cyclic-import
                from bauiv1lib.gettokens import show_get_tokens_prompt

                show_get_tokens_prompt(
                    origin_widget=bui.existing(context.widget)
                )
            case _:
                assert_never(action)

    def _watch_ad(self, slot: int, window: DocUIWindow) -> None:
        plus = bui.app.plus
        assert plus is not None
        self._recreate_suppress = bui.MainWindowAutoRecreateSuppress()
        weakwin = weakref.ref(window)
        plus.ads.show_ad_2(
            'reduce_chest_wait',
            on_completion_call=bui.WeakCallPartial(
                self._ad_complete, slot, weakwin
            ),
        )

    def _ad_complete(
        self,
        slot: int,
        weakwin: weakref.ref[DocUIWindow],
        actually_showed: bool,
    ) -> None:
        self._recreate_suppress = None
        window = weakwin()
        if window is None or not actually_showed:
            return
        self.replace(
            window,
            bacommon.docui.routes.classicchest.AdWatched(slot=slot).request(),
        )


def slot_route(slot: int) -> bacommon.docui.routes.classicchest.Root:
    """The root route for a chest slot, with what only we can know."""
    plus = bui.app.plus
    return bacommon.docui.routes.classicchest.Root(
        slot=slot,
        ad_ready=plus is not None and plus.ads.have_incentivized_ad(),
        open_me=bool(
            bui.app.config.resolve(HIGHLIGHT_TOKEN_PURCHASES_CONFIG_KEY)
        ),
    )


def show_chest_window(
    slot: int, origin_widget: bui.Widget | None = None
) -> None:
    """Pop up a chest slot's window wherever we are in the nav stack."""
    from bauiv1lib.docui import DocUIWindow

    bui.app.ui_v1.auxiliary_window_activate(
        win_type=DocUIWindow,
        win_create_call=bui.CallStrict(
            ChestUIController().create_window,
            slot_route(slot),
            origin_widget=origin_widget,
            uiopenstateid=f'classicchest{slot}',
        ),
        # Distinct per slot, so pressing another slot's chest switches
        # to it rather than just closing this one.
        win_extra_type_id=(
            f'{ChestUIController.get_window_extra_type_id()}:{slot}'
        ),
    )
