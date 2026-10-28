# Released under the MIT License. See LICENSE for details.
#
"""Examples/tests for using DocUI to build UIs."""

from typing import TYPE_CHECKING, override, assert_never

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.routes.docuitest as rt
import bauiv1 as bui
from bauiv1 import _commonassets
from bauiv1 import _uiv1assets, _classiccatalogassets
from bauiv1 import _classiccharacterassets
from bauiv1 import _classicassets

from bauiv1lib.docui import DocUIWindow, TypedDocUIController

if TYPE_CHECKING:
    from bacommon.docui import DocUIResponse
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest

    from bauiv1lib.docui import DocUILocalAction


def show_test_doc_ui_v2_window() -> None:
    """Bust out a doc-ui test window built locally on the client.

    Test pages authored as language-agnostic v2 documents — text as
    ``LangStrSpec`` values from the ``badocuiv2testassets`` package (decoded
    in the client's locale at render time), textures/meshes as typed
    refs, and multi-line labels via wrap-params instead of hand-baked
    newlines. The Cloud-Msg and Web buttons fetch equivalent v2 pages
    from bamaster, keeping the full cloud/web resolve -> decode ->
    render paths exercised.
    """
    bui.app.ui_v1.auxiliary_window_activate(
        win_type=DocUIWindow,
        win_create_call=bui.CallStrict(
            TestDocUIV2Controller().create_window, rt.Root()
        ),
        win_extra_type_id=TestDocUIV2Controller.get_window_extra_type_id(),
    )


class TestDocUIV2Controller(
    TypedDocUIController[rt.AnyTestRoute, rt.AnyTestLocalAction]
):
    """Tests/demonstrations of native (v2 / l-string) docui.

    Local pages are authored client-side; the web-test and
    cloud-msg-test routes fetch equivalent v2 pages from bamaster.
    """

    @override
    @classmethod
    def get_route_type(cls) -> type[bacommon.docui.routes.docuitest.TestRoute]:
        return rt.TestRoute

    @override
    @classmethod
    def get_local_action_type(
        cls,
    ) -> type[bacommon.docui.routes.docuitest.TestLocalAction]:
        return rt.TestLocalAction

    @override
    def fulfill_route(
        self, route: bacommon.docui.routes.docuitest.AnyTestRoute
    ) -> DocUIResponse:
        """Fulfill a route (called in a background thread)."""
        import bacommon.docui.v2 as dui2

        response = self._fulfill_route_page(route)

        # No horizontal scroll bars anywhere on our test pages (page
        # arrows and drag/wheel scrolling still carry their rows).
        if isinstance(response, dui2.Response):
            for row in dui2.all_rows(response.page.rows):
                if isinstance(row, dui2.ButtonRow):
                    row.show_scrollbar = False
        return response

    def _fulfill_route_page(
        self, route: bacommon.docui.routes.docuitest.AnyTestRoute
    ) -> DocUIResponse:
        # A flat route-to-page dispatch; every case adds a branch, a
        # return and (its page function's import) a local.
        # pylint: disable=too-many-return-statements, too-many-branches
        # pylint: disable=too-many-locals

        match route:
            # Handle some pages purely locally.
            case rt.Root():
                return _test_v2_page_root(route)
            case rt.Test2():
                from bauiv1lib.docuitestsimple import test_page_2

                return test_page_2()
            case rt.Slow():
                from bauiv1lib.docuitestsimple import test_page_long

                return test_page_long()
            case rt.TimedActions():
                from bauiv1lib.docuitestsimple import (
                    test_page_timed_actions,
                )

                return test_page_timed_actions(route)
            case rt.DisplayItems():
                from bauiv1lib.docuitestitems import test_page_display_items

                return test_page_display_items(route)
            case rt.TextImages():
                from bauiv1lib.docuitesttextimages import (
                    test_page_text_images,
                )

                return test_page_text_images(route)
            case rt.LiveTimes():
                from bauiv1lib.docuitestlivetimes import test_page_live_times

                return test_page_live_times(route)
            case rt.TextWrapping():
                from bauiv1lib.docuitesttextwrap import (
                    test_page_text_wrapping,
                )

                return test_page_text_wrapping(route)
            case rt.Animation():
                from bauiv1lib.docuitestanimation import test_page_animation

                return test_page_animation()
            case rt.Depictions():
                from bauiv1lib.docuitestdepictions import (
                    test_page_depictions,
                )

                return test_page_depictions(route)
            case rt.Viewers():
                from bauiv1lib.docuitestviewers import test_page_viewers

                return test_page_viewers(route)
            case rt.Names():
                from bauiv1lib.docuitestnames import test_page_names

                return test_page_names(route)
            case rt.NinePatch():
                from bauiv1lib.docuitestninepatch import (
                    test_page_nine_patch,
                )

                return test_page_nine_patch(route)
            case rt.Glyphs():
                from bauiv1lib.docuitestglyphs import test_page_glyphs

                return test_page_glyphs(route)
            case rt.EmptyPage():
                from bauiv1lib.docuitestsimple import test_page_empty

                return test_page_empty()
            case rt.BoundsTests():
                from bauiv1lib.docuitestlayouts import test_page_bounds

                return test_page_bounds()
            case rt.Widgets():
                from bauiv1lib.docuitestwidgets import test_page_widgets

                return test_page_widgets(route)
            case rt.NavTest():
                from bauiv1lib.docuitestnav import test_page_nav

                return test_page_nav(route)
            case rt.Drill():
                from bauiv1lib.docuitestdrill import test_page_drill

                return test_page_drill(route)
            case rt.DrillLevel():
                from bauiv1lib.docuitestdrill import test_page_drill_level

                return test_page_drill_level(route)
            case rt.Popups() | rt.PopupsMain() | rt.PopupsOther():
                from bauiv1lib.docuitestpopups import test_page_popups

                return test_page_popups(route)
            case rt.Themes() | rt.ThemesPopup():
                from bauiv1lib.docuitestthemes import test_page_themes

                return test_page_themes(route)
            case rt.WindowLayouts():
                from bauiv1lib.docuitestlayouts import (
                    test_page_window_layouts,
                )

                return test_page_window_layouts(route)
            case rt.Sections():
                from bauiv1lib.docuitestsections import test_page_sections

                return test_page_sections(route)
            case rt.ButtonGrids():
                from bauiv1lib.docuitestgrids import test_page_button_grids

                return test_page_button_grids(route)
            case rt.LayoutFit():
                from bauiv1lib.docuitestlayouts import test_page_layout_fit

                return test_page_layout_fit(route)

            # Ship web-tests off to some webserver to handle.
            case rt.WebTestGet() | rt.WebTestPost():
                return self.fulfill_request_web(
                    route, 'https://www.ballistica.net/docuitest'
                )

            # Ship cloud-msg-tests through our cloud connection.
            case rt.CloudMsgTestGet() | rt.CloudMsgTestPost():
                return self.fulfill_request_cloud(route, 'docuitestv2')

            case _:
                assert_never(route)

    @override
    def run_local_action(
        self,
        action: bacommon.docui.routes.docuitest.AnyTestLocalAction,
        context: DocUILocalAction,
    ) -> None:
        match action:
            case rt.ShowVolume():
                # The live value: the row wrote it to page state before
                # firing us.
                state = context.state(rt.WidgetTestState)
                vol = (
                    'unknown'
                    if state is None
                    else f'{round(state.volume * 100)}%'
                )
                bui.screenmessage(
                    f'Volume: {vol} (trigger={context.trigger!r})'
                )
            case rt.TestAction():
                bui.screenmessage(f'Would do {action!r}.')
            case _:
                assert_never(action)


def _test_v2_page_root(
    route: bacommon.docui.routes.docuitest.Root,
) -> bacommon.docui.v2.Response:
    """Author the v2 (l-string) test root page purely on the client.

    The full v1 test root page, with all text authored as
    language-agnostic ``LangStrSpec`` values from the ``badocuiv2testassets``
    package, textures/meshes as typed refs from
    ``_commonassets``/``_classicassets``, and multi-line labels wrapped via
    definition-time :class:`~bacommon.langstr.WrapParams` on the
    package's string definitions (decision D-t) instead of v1's
    hand-baked newlines. The client resolves the referenced packages
    in its own locale, decodes, and wraps -- so this single response
    renders in any language.
    """
    import bacommon.clienteffect as clfx
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets
    from bauiv1lib.docuitestlayouts import (
        layout_picker_rows,
        layout_test_decos,
        layout_tests_rows,
        layout_theme_rows,
    )

    strs = _docuiv2testassets.strings

    # Show some specific debug bits if they ask us to.
    debug = route.debug

    # The long-row test's buttons all reload this page unchanged, to
    # check that scroll positions survive a reload.
    reload = route.replace()

    def _long_row_button(num: int) -> bacommon.docui.v2.Button:
        # Dev-only page, so baked literals.
        return dui2.Button(
            label=LangStrSpecValue.literal(str(num)),
            size=(150, 100),
            action=reload,
        )

    # What our 'Window Layouts' row has picked (it rides along with
    # every request we make, so it survives our other buttons).
    arrived = route.get_state(rt.RootState)
    state = rt.RootState() if arrived is None else arrived

    response = dui2.Response(
        page=dui2.Page(
            title=strs.nav.test_root_title.spec,
            state=state.encode(),
            rows=[
                # (Tall enough that the nub at the bottom stays inside
                # the band, with about the room at the bottom that the
                # texts have at the top.)
                dui2.HeaderRow(
                    116,
                    decorations_left=[
                        dui2.Text(
                            text=strs.common.header_left.spec,
                            position=(0, 10 + 28),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui2.HAlign.LEFT,
                            debug=debug,
                        ),
                    ],
                    decorations_center=[
                        dui2.Text(
                            text=strs.common.hello_from_docui.spec,
                            position=(0, 10 + 28),
                            size=(300, 30),
                            debug=debug,
                        ),
                        dui2.Text(
                            text=strs.common.docui_reference.spec,
                            scale=0.5,
                            position=(0, -18 + 28),
                            size=(600, 23),
                            debug=debug,
                        ),
                        dui2.Image(
                            texture=_classicassets.textures.nub,
                            position=(0, -58 + 28),
                            size=(60, 60),
                        ),
                    ],
                    decorations_right=[
                        dui2.Text(
                            text=strs.common.header_right.spec,
                            position=(0, 10 + 28),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui2.HAlign.RIGHT,
                            debug=debug,
                        ),
                    ],
                ),
                dui2.TitleRow(strs.nav.some_tests.spec),
                dui2.ButtonRow(
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=strs.nav.browse.spec,
                            size=(120, 80),
                            action=rt.Test2().browse(),
                        ),
                        dui2.Button(
                            label=strs.nav.replace.spec,
                            size=(120, 80),
                            action=rt.Test2().replace(),
                        ),
                        dui2.Button(
                            label=strs.nav.close.spec,
                            size=(120, 80),
                            action=dui2.Local(close_window=True),
                        ),
                        dui2.Button(
                            label=strs.common.invalid_request.spec,
                            size=(120, 80),
                            # A path with no route, to exercise error
                            # handling; routes can't express that (by
                            # design) so we build it by hand.
                            # pylint: disable-next=docui-raw-request
                            action=dui2.Browse(dui2.Request('/invalidrequest')),
                        ),
                        dui2.Button(
                            label=strs.effects.immediate_client_effects.spec,
                            size=(120, 80),
                            action=dui2.Local(
                                # V2 effect forms: l-string text decoded
                                # in the client's locale + a typed sound
                                # ref from an asset package. The page
                                # resolve pre-warms the referenced
                                # packages, so press-time runs are
                                # cache hits.
                                immediate_client_effects=[
                                    clfx.ScreenMessageV2(
                                        message=(
                                            strs.effects.immediate_effects_hello
                                        ).spec,
                                        color=(0, 1, 0),
                                    ),
                                    clfx.PlaySoundV2(
                                        sound=(
                                            _commonassets.audio
                                        ).cash_register,
                                    ),
                                    clfx.Delay(1.0),
                                    clfx.ScreenMessageV2(
                                        message=(
                                            strs.effects.effect_success
                                        ).spec,
                                        color=(0, 1, 0),
                                    ),
                                    clfx.PlaySoundV2(
                                        sound=(
                                            _commonassets.audio
                                        ).cash_register,
                                    ),
                                ]
                            ),
                        ),
                        dui2.Button(
                            label=strs.effects.response_client_effects.spec,
                            size=(120, 80),
                            action=rt.Root(test_effects=True).browse(),
                        ),
                        dui2.Button(
                            label=strs.effects.immediate_local_action.spec,
                            size=(120, 80),
                            action=rt.TestAction(testparam=123).local(),
                        ),
                        dui2.Button(
                            label=strs.effects.response_local_action.spec,
                            size=(120, 80),
                            action=rt.Root(test_action=True).browse(),
                        ),
                    ],
                ),
                dui2.TitleRow(strs.nav.few_more_tests.spec),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=(
                                strs.common.hide_debug.spec
                                if debug
                                else strs.common.show_debug.spec
                            ),
                            size=(120, 80),
                            action=rt.Root(debug=not debug).replace(),
                        ),
                        dui2.Button(
                            label=strs.nav.slow_browse.spec,
                            size=(120, 80),
                            action=rt.Slow().browse(),
                        ),
                        dui2.Button(
                            label=strs.nav.slow_replace.spec,
                            size=(120, 80),
                            action=rt.Slow().replace(),
                        ),
                        dui2.Button(
                            label=strs.common.timed_actions.spec,
                            size=(120, 80),
                            action=rt.TimedActions().browse(),
                        ),
                        dui2.Button(
                            label=strs.web.web_get.spec,
                            size=(120, 80),
                            action=rt.WebTestGet().browse(),
                        ),
                        dui2.Button(
                            label=strs.web.web_post.spec,
                            size=(120, 80),
                            action=rt.WebTestPost().browse(),
                        ),
                        dui2.Button(
                            label=strs.items.display_items.spec,
                            size=(120, 80),
                            action=rt.DisplayItems().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Text Images'),
                            size=(120, 80),
                            action=rt.TextImages().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Live Times'),
                            size=(120, 80),
                            action=rt.LiveTimes().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Text Wrapping'),
                            size=(120, 80),
                            action=rt.TextWrapping().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Animation'),
                            size=(120, 80),
                            action=rt.Animation().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Depictions'),
                            size=(120, 80),
                            action=rt.Depictions().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Viewers'),
                            size=(120, 80),
                            action=rt.Viewers().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Viewers (Narrow)'),
                            size=(160, 80),
                            action=rt.Viewers().browse(
                                layout=dui2.WindowLayout.VIEWER_NARROW
                            ),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Names'),
                            size=(120, 80),
                            action=rt.Names().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('9-Patch'),
                            size=(120, 80),
                            action=rt.NinePatch().browse(),
                        ),
                        dui2.Button(
                            # Dev-only page, so a baked literal label.
                            label=LangStrSpecValue.literal('Glyphs'),
                            size=(120, 80),
                            action=rt.Glyphs().browse(),
                        ),
                        dui2.Button(
                            label=strs.layout.empty_page.spec,
                            size=(120, 80),
                            action=rt.EmptyPage().browse(),
                        ),
                    ],
                ),
                dui2.TitleRow(strs.nav.even_more_tests.spec),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=strs.cloud.cloud_msg_get.spec,
                            size=(120, 80),
                            action=rt.CloudMsgTestGet().browse(),
                        ),
                        dui2.Button(
                            label=strs.cloud.cloud_msg_post.spec,
                            size=(120, 80),
                            action=rt.CloudMsgTestPost().browse(),
                        ),
                        dui2.Button(
                            label=strs.layout.bounds_tests.spec,
                            size=(120, 80),
                            action=rt.BoundsTests().browse(),
                        ),
                        dui2.Button(
                            label=LangStrSpecValue.literal('Drill Down'),
                            size=(120, 80),
                            action=rt.Drill().browse(),
                        ),
                        dui2.Button(
                            label=LangStrSpecValue.literal('Popups'),
                            size=(120, 80),
                            action=rt.Popups().browse(),
                        ),
                        dui2.Button(
                            label=LangStrSpecValue.literal('Page Themes'),
                            size=(120, 80),
                            action=rt.Themes().browse(),
                        ),
                    ],
                ),
                # Pick a layout for rows below to use.
                *layout_picker_rows(route, state),
                *layout_theme_rows(route, state),
                *layout_tests_rows(state),
                dui2.TitleRow(strs.layout.empty_row.spec),
                dui2.ButtonRow(buttons=[]),
                # Dev-only, so a baked literal.
                dui2.TitleRow(LangStrSpecValue.literal('Button Tests')),
                dui2.ButtonRow(
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=strs.nav.test.spec,
                            size=(180, 200),
                            decorations=layout_test_decos(debug),
                        ),
                        dui2.Button(
                            label=strs.nav.test_two.spec,
                            size=(100, 100),
                            color=(1, 0, 0, 1),
                            label_color=(1, 1, 1, 1),
                            padding_right=4,
                        ),
                        # Should look like the first button but
                        # scaled down.
                        dui2.Button(
                            label=strs.nav.test.spec,
                            size=(180, 200),
                            scale=0.6,
                            padding_bottom=30,  # Should nudge us up.
                            debug=debug,  # Show bounds.
                            decorations=layout_test_decos(debug),
                        ),
                        # Testing custom button images and opacity.
                        dui2.Button(
                            label=strs.nav.test_three.spec,
                            texture=_uiv1assets.textures.button_square_wide,
                            padding_left=10.0,
                            padding_right=10.0,
                            color=(1, 1, 1, 0.3),
                            size=(200, 100),
                            style=dui2.ButtonStyle.MEDIUM,
                        ),
                        # Testing image drawing vs bounds
                        dui2.Button(
                            label=strs.layout.bounds_test.spec,
                            texture=_commonassets.textures.white,
                            color=(1, 1, 1, 0.3),
                            size=(150, 100),
                            debug=debug,
                        ),
                    ],
                ),
                dui2.TitleRow(strs.layout.long_row_test.spec),
                # Dev-only page, so baked literals.
                dui2.SubtitleRow(
                    LangStrSpecValue.literal(
                        'Look - a subtitle! - These buttons reload the page'
                        ' - all scrolling should remain intact.'
                    )
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            size=(150, 100),
                            action=reload,
                            decorations=[
                                dui2.Text(
                                    text=strs.layout.max_width_test.spec,
                                    position=(0, 25),
                                    size=(150 * 0.8, 32.0),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                                # v1 bakes a newline into this one
                                # ('MaxHeightTest\nSecondLine'); we ask
                                # for two balanced lines instead.
                                dui2.Text(
                                    text=strs.layout.max_height_test.spec,
                                    position=(0, -20),
                                    size=(150 * 0.8, 40),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                            ],
                        ),
                        dui2.Button(
                            size=(150, 100),
                            action=reload,
                            decorations=[
                                dui2.Image(
                                    texture=(
                                        _classiccharacterassets.textures
                                    ).zoe_icon,
                                    position=(0, 0),
                                    size=(70, 70),
                                    tint_texture=(
                                        _classiccharacterassets.textures
                                    ).zoe_icon_color_mask,
                                    tint_color=(1, 0, 0),
                                    tint2_color=(0, 1, 0),
                                    mask_texture=(
                                        _classiccatalogassets.textures
                                    ).character_icon_mask,
                                ),
                            ],
                        ),
                        dui2.Button(
                            size=(150, 100),
                            action=reload,
                            decorations=[
                                dui2.Image(
                                    texture=(
                                        _classiccatalogassets.textures
                                    ).bridgit_preview,
                                    position=(0, 10),
                                    size=(120, 60),
                                    mask_texture=(
                                        (
                                            _classiccatalogassets.textures
                                        ).map_preview_mask
                                    ),
                                    mesh_opaque=(
                                        _classiccatalogassets.meshes
                                    ).level_select_button_opaque,
                                    mesh_transparent=(
                                        _classiccatalogassets.meshes
                                    ).level_select_button_transparent,
                                ),
                            ],
                        ),
                        *[_long_row_button(i) for i in range(1, 9)],
                        dui2.Button(
                            label=strs.common.foo.spec,
                            size=(150, 100),
                            scale=0.4,
                            padding_left=100,
                            padding_right=200,
                            action=reload,
                        ),
                        *[_long_row_button(i) for i in range(9, 17)],
                    ],
                ),
                dui2.FootnoteRow(
                    LangStrSpecValue.literal('Look - a footnote!')
                ),
                dui2.SubtitleRow(strs.layout.subtitle_only.spec),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(size=(200, 120)),
                    ],
                ),
                # Same again, so a subtitle-only row can be judged
                # against a plain button row above it as well as
                # against a footnote.
                # Dev-only page, so a baked literal.
                dui2.SubtitleRow(LangStrSpecValue.literal('Subtitle only 2')),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(size=(200, 120)),
                    ],
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=strs.layout.row_with_no_title.spec,
                            size=(300, 80),
                            style=dui2.ButtonStyle.MEDIUM,
                            color=(0.8, 0.8, 0.8, 1),
                            icon=_classicassets.textures.button_punch,
                            icon_color=(0.5, 0.3, 1.0, 1.0),
                            icon_scale=1.2,
                        ),
                    ],
                ),
                dui2.TitleRow(
                    strs.layout.centered_faded_title.spec,
                    color=(0.6, 0.6, 1.0, 0.3),
                    flatness=1.0,
                    shadow=1.0,
                ),
                dui2.SubtitleRow(
                    strs.layout.testing_centered.spec,
                    color=(1.0, 0.5, 1.0, 0.5),
                    flatness=1.0,
                    shadow=0.0,
                ),
                dui2.ButtonRow(
                    center_content=True,
                    center_title=True,
                    buttons=[
                        dui2.Button(
                            label=strs.common.hello_there.spec,
                            size=(200, 120),
                            color=(0.7, 0.7, 0.9, 1),
                        ),
                    ],
                ),
                # Styled on its own, not inheriting the subtitle's
                # overrides. (Dev-only page, so a baked literal.)
                dui2.FootnoteRow(
                    LangStrSpecValue.literal(
                        'Footnote with its own color, flatness and shadow.'
                    ),
                    color=(0.4, 1.0, 1.0, 1.0),
                    flatness=0.0,
                    shadow=1.0,
                ),
                # Right-alignment tests. (Dev-only, so baked literals.)
                dui2.TitleRow(LangStrSpecValue.literal('Right Aligned Title')),
                dui2.SubtitleRow(
                    LangStrSpecValue.literal(
                        'Testing right-aligned title, subtitle, and content'
                    )
                ),
                dui2.ButtonRow(
                    title_align=dui2.HAlign.RIGHT,
                    content_align=dui2.HAlign.RIGHT,
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=LangStrSpecValue.literal('Right'),
                            size=(200, 80),
                            style=dui2.ButtonStyle.MEDIUM,
                            debug=debug,
                        ),
                    ],
                ),
                # Same, but with more buttons than fit; alignment only
                # applies to rows with room to spare, so this one should
                # simply fill its width and scroll like any other.
                dui2.TitleRow(
                    LangStrSpecValue.literal('Right Aligned Scrolling')
                ),
                dui2.SubtitleRow(
                    LangStrSpecValue.literal(
                        'Too many buttons to fit; should scroll normally'
                    )
                ),
                dui2.ButtonRow(
                    title_align=dui2.HAlign.RIGHT,
                    content_align=dui2.HAlign.RIGHT,
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=LangStrSpecValue.literal(str(i + 1)),
                            size=(150, 100),
                        )
                        for i in range(16)
                    ],
                ),
                # The first row's header test, flipped upside down as a
                # footer. (Decorations sit lower than the header's
                # mirror image to keep clear of the scroll-bar strip,
                # which reaches 12 into the band below the row's
                # buttons; the bottom line sits at -36 so its glyphs
                # stay inside the band's -50 edge.)
                dui2.FooterRow(
                    100,
                    decorations_left=[
                        dui2.Text(
                            text=LangStrSpecValue.literal('Footer Left'),
                            position=(0, -36),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui2.HAlign.LEFT,
                            debug=debug,
                        ),
                    ],
                    decorations_center=[
                        dui2.Image(
                            texture=_classicassets.textures.nub,
                            position=(0, 58 - 32),
                            size=(60, 60),
                        ),
                        dui2.Text(
                            text=strs.common.docui_reference.spec,
                            scale=0.5,
                            position=(0, 18 - 32),
                            size=(600, 23),
                            debug=debug,
                        ),
                        dui2.Text(
                            text=LangStrSpecValue.literal(
                                'Hello from a DocUI footer!'
                            ),
                            position=(0, -36),
                            size=(300, 30),
                            debug=debug,
                        ),
                    ],
                    decorations_right=[
                        dui2.Text(
                            text=LangStrSpecValue.literal('Footer Right'),
                            position=(0, -36),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui2.HAlign.RIGHT,
                            debug=debug,
                        ),
                    ],
                ),
            ],
        )
    )

    # Include some client effects if they ask (the 'Response
    # ClientEffects' button). V2 effect forms; see the immediate-effects
    # note above.
    if route.test_effects:
        response.client_effects = [
            clfx.ScreenMessageV2(
                message=strs.effects.response_effects_hello.spec,
                color=(0, 1, 0),
            ),
            clfx.PlaySoundV2(sound=_commonassets.audio.cash_register),
            clfx.Delay(1.0),
            clfx.ScreenMessageV2(
                message=strs.effects.effect_success.spec, color=(0, 1, 0)
            ),
            clfx.PlaySoundV2(sound=_commonassets.audio.cash_register),
        ]

    # Include a local-action if they ask (the 'Response LocalAction'
    # button).
    if route.test_action:
        rt.TestAction(testparam=234).attach(response)

    return response
