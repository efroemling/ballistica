# Released under the MIT License. See LICENSE for details.
#
"""Examples/tests for using DocUI to build UIs."""

import time
import copy
from typing import TYPE_CHECKING, override

from efro.error import CleanError
import bauiv1 as bui
from bauiv1 import builtinassets
from bauiv1 import stdassets

from bauiv1lib.docui import DocUIWindow, DocUIController

if TYPE_CHECKING:
    from bacommon.docui import DocUIRequest, DocUIResponse
    import bacommon.docui.v2
    from bacommon.langstr import LangStr

    from bauiv1lib.docui import DocUILocalAction


def _btex(name: str) -> str:
    """Qualified ref for a texture in the builtin asset-package."""
    return f'{builtinassets.__asset_package__}:textures/{name}'


def _stex(name: str) -> str:
    """Qualified stdassets texture ref."""
    return f'{stdassets.__asset_package__}:textures/{name}'


def show_test_doc_ui_v2_window() -> None:
    """Bust out a doc-ui test window built locally on the client.

    Test pages authored as language-agnostic v2 documents — text as
    ``LangStr`` values from the ``badocuiv2testassets`` asset package (decoded
    in the client's locale at render time), textures/meshes as typed
    refs, and multi-line labels via wrap-params instead of hand-baked
    newlines. The Cloud-Msg and Web buttons fetch equivalent v2 pages
    from bamaster, keeping the full cloud/web resolve -> decode ->
    render paths exercised.
    """
    import bacommon.docui.v2 as dui2

    bui.app.ui_v1.auxiliary_window_activate(
        win_type=DocUIWindow,
        win_create_call=bui.CallStrict(
            TestDocUIV2Controller().create_window, dui2.Request('/')
        ),
        win_extra_type_id=TestDocUIV2Controller.get_window_extra_type_id(),
    )


class TestDocUIV2Controller(DocUIController):
    """Tests/demonstrations of native (v2 / l-string) docui.

    Local pages are authored client-side; the ``/cloudmsgtest/*`` and
    ``/webtest/*`` paths fetch equivalent v2 pages from bamaster.
    """

    @override
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        """Fulfill a v2 request (called in a background thread)."""
        # pylint: disable=too-many-return-statements
        import bacommon.docui.v2 as dui2

        if not isinstance(request, dui2.Request):
            raise CleanError('Invalid request version.')

        # Handle some pages purely locally.
        if request.path == '/':
            return _test_v2_page_root(request)
        if request.path == '/test2':
            return _test_v2_page_2(request)
        if request.path == '/slow':
            return _test_v2_page_long(request)
        if request.path == '/timedactions':
            return _test_v2_page_timed_actions(request)
        if request.path == '/displayitems':
            return _test_v2_page_display_items(request)
        if request.path == '/emptypage':
            return _test_v2_page_empty(request)
        if request.path == '/boundstests':
            return _test_v2_bounds(request)

        # Ship '/webtest/*' off to some webserver to handle.
        if request.path.startswith('/webtest/'):
            return self.fulfill_request_web(
                request, 'https://www.ballistica.net/docuitest'
            )

        # Ship '/cloudmsgtest/*' through our cloud connection to handle.
        if request.path.startswith('/cloudmsgtest/'):
            return self.fulfill_request_cloud(request, 'docuitestv2')

        raise CleanError('Invalid request path.')

    @override
    def local_action(self, action: DocUILocalAction) -> None:
        bui.screenmessage(
            f'Would do {action.name!r} with args {action.args!r}.'
        )


def _test_v2_page_root(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """Author the v2 (l-string) test root page purely on the client.

    The full v1 test root page, with all text authored as
    language-agnostic ``LangStr`` values from the ``badocuiv2testassets``
    package, textures/meshes as typed refs from
    ``builtinassets``/``stdassets``, and multi-line labels wrapped via
    definition-time :class:`~bacommon.langstr.WrapParams` on the
    package's string definitions (decision D-t) instead of v1's
    hand-baked newlines. The client resolves the referenced packages
    in its own locale, decodes, and wraps -- so this single response
    renders in any language.
    """
    import bacommon.clienteffect as clfx
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    response = dui2.Response(
        page=dui2.Page(
            title=strs.nav.test_root_title,
            rows=[
                dui2.ButtonRow(
                    debug=debug,
                    header_height=100,
                    header_decorations_left=[
                        dui2.Text(
                            text=strs.common.header_left,
                            position=(0, 10 + 20),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui2.HAlign.LEFT,
                            debug=debug,
                        ),
                    ],
                    header_decorations_center=[
                        dui2.Text(
                            text=strs.common.hello_from_docui,
                            position=(0, 10 + 20),
                            size=(300, 30),
                            debug=debug,
                        ),
                        dui2.Text(
                            text=strs.common.docui_reference,
                            scale=0.5,
                            position=(0, -18 + 20),
                            size=(600, 23),
                            debug=debug,
                        ),
                        dui2.Image(
                            texture=builtinassets.textures.nub,
                            position=(0, -58 + 20),
                            size=(60, 60),
                        ),
                    ],
                    header_decorations_right=[
                        dui2.Text(
                            text=strs.common.header_right,
                            position=(0, 10 + 20),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui2.HAlign.RIGHT,
                            debug=debug,
                        ),
                    ],
                    title=strs.nav.some_tests,
                    buttons=[
                        dui2.Button(
                            label=strs.nav.browse,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/test2')),
                        ),
                        dui2.Button(
                            label=strs.nav.replace,
                            size=(120, 80),
                            action=dui2.Replace(dui2.Request('/test2')),
                        ),
                        dui2.Button(
                            label=strs.nav.close,
                            size=(120, 80),
                            action=dui2.Local(close_window=True),
                        ),
                        dui2.Button(
                            label=strs.common.invalid_request,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/invalidrequest')),
                        ),
                        dui2.Button(
                            label=strs.effects.immediate_client_effects,
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
                                        ),
                                        color=(0, 1, 0),
                                    ),
                                    clfx.PlaySoundV2(
                                        sound=(
                                            builtinassets.audio
                                        ).cash_register,
                                    ),
                                    clfx.Delay(1.0),
                                    clfx.ScreenMessageV2(
                                        message=strs.effects.effect_success,
                                        color=(0, 1, 0),
                                    ),
                                    clfx.PlaySoundV2(
                                        sound=(
                                            builtinassets.audio
                                        ).cash_register,
                                    ),
                                ]
                            ),
                        ),
                        dui2.Button(
                            label=strs.effects.response_client_effects,
                            size=(120, 80),
                            action=dui2.Browse(
                                dui2.Request('/', args={'test_effects': True})
                            ),
                        ),
                        dui2.Button(
                            label=strs.effects.immediate_local_action,
                            size=(120, 80),
                            action=dui2.Local(
                                immediate_local_action='testaction',
                                immediate_local_action_args={'testparam': 123},
                            ),
                        ),
                        dui2.Button(
                            label=strs.effects.response_local_action,
                            size=(120, 80),
                            action=dui2.Browse(
                                dui2.Request('/', args={'test_action': True})
                            ),
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    title=strs.nav.few_more_tests,
                    buttons=[
                        dui2.Button(
                            label=(
                                strs.common.hide_debug
                                if debug
                                else strs.common.show_debug
                            ),
                            size=(120, 80),
                            action=dui2.Replace(
                                dui2.Request('/', args={'debug': not debug})
                            ),
                        ),
                        dui2.Button(
                            label=strs.nav.slow_browse,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/slow')),
                        ),
                        dui2.Button(
                            label=strs.nav.slow_replace,
                            size=(120, 80),
                            action=dui2.Replace(dui2.Request('/slow')),
                        ),
                        dui2.Button(
                            label=strs.common.timed_actions,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/timedactions')),
                        ),
                        dui2.Button(
                            label=strs.web.web_get,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/webtest/get')),
                        ),
                        dui2.Button(
                            label=strs.web.web_post,
                            size=(120, 80),
                            action=dui2.Browse(
                                dui2.Request(
                                    '/webtest/post',
                                    method=dui2.RequestMethod.POST,
                                )
                            ),
                        ),
                        dui2.Button(
                            label=strs.items.display_items,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/displayitems')),
                        ),
                        dui2.Button(
                            label=strs.layout.empty_page,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/emptypage')),
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    title=strs.nav.even_more_tests,
                    buttons=[
                        dui2.Button(
                            label=strs.cloud.cloud_msg_get,
                            size=(120, 80),
                            action=dui2.Browse(
                                dui2.Request('/cloudmsgtest/get')
                            ),
                        ),
                        dui2.Button(
                            label=strs.cloud.cloud_msg_post,
                            size=(120, 80),
                            action=dui2.Browse(
                                dui2.Request(
                                    '/cloudmsgtest/post',
                                    method=dui2.RequestMethod.POST,
                                )
                            ),
                        ),
                        dui2.Button(
                            label=strs.layout.bounds_tests,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/boundstests')),
                        ),
                    ],
                ),
                dui2.ButtonRow(title=strs.layout.empty_row, buttons=[]),
                dui2.ButtonRow(
                    title=strs.layout.layout_tests,
                    debug=debug,
                    padding_left=5.0,
                    buttons=[
                        dui2.Button(
                            label=strs.nav.test,
                            size=(180, 200),
                            decorations=_layout_test_decos(debug),
                        ),
                        dui2.Button(
                            label=strs.nav.test_two,
                            size=(100, 100),
                            color=(1, 0, 0, 1),
                            label_color=(1, 1, 1, 1),
                            padding_right=4,
                        ),
                        # Should look like the first button but
                        # scaled down.
                        dui2.Button(
                            label=strs.nav.test,
                            size=(180, 200),
                            scale=0.6,
                            padding_bottom=30,  # Should nudge us up.
                            debug=debug,  # Show bounds.
                            decorations=_layout_test_decos(debug),
                        ),
                        # Testing custom button images and opacity.
                        dui2.Button(
                            label=strs.nav.test_three,
                            texture=builtinassets.textures.button_square_wide,
                            padding_left=10.0,
                            padding_right=10.0,
                            color=(1, 1, 1, 0.3),
                            size=(200, 100),
                        ),
                        # Testing image drawing vs bounds
                        dui2.Button(
                            label=strs.layout.bounds_test,
                            texture=builtinassets.textures.white,
                            color=(1, 1, 1, 0.3),
                            size=(150, 100),
                            debug=debug,
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    title=strs.layout.long_row_test,
                    subtitle=strs.layout.look_a_subtitle,
                    buttons=[
                        dui2.Button(
                            size=(150, 100),
                            decorations=[
                                dui2.Text(
                                    text=strs.layout.max_width_test,
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
                                    text=strs.layout.max_height_test,
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
                            decorations=[
                                dui2.Image(
                                    texture=stdassets.textures.zoe_icon,
                                    position=(0, 0),
                                    size=(70, 70),
                                    tint_texture=(
                                        stdassets.textures.zoe_icon_color_mask
                                    ),
                                    tint_color=(1, 0, 0),
                                    tint2_color=(0, 1, 0),
                                    mask_texture=(
                                        builtinassets.textures
                                    ).character_icon_mask,
                                ),
                            ],
                        ),
                        dui2.Button(
                            size=(150, 100),
                            decorations=[
                                dui2.Image(
                                    texture=stdassets.textures.bridgit_preview,
                                    position=(0, 10),
                                    size=(120, 60),
                                    mask_texture=(
                                        stdassets.textures.map_preview_mask
                                    ),
                                    mesh_opaque=(
                                        stdassets.meshes
                                    ).level_select_button_opaque,
                                    mesh_transparent=(
                                        stdassets.meshes
                                    ).level_select_button_transparent,
                                ),
                            ],
                        ),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(
                            label=strs.common.foo,
                            size=(150, 100),
                            scale=0.4,
                            padding_left=100,
                            padding_right=200,
                        ),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                        dui2.Button(size=(150, 100)),
                    ],
                ),
                dui2.ButtonRow(
                    spacing_top=-15,
                    subtitle=strs.layout.subtitle_only,
                    buttons=[
                        dui2.Button(size=(200, 120)),
                    ],
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=strs.layout.row_with_no_title,
                            size=(300, 80),
                            style=dui2.ButtonStyle.MEDIUM,
                            color=(0.8, 0.8, 0.8, 1),
                            icon=stdassets.textures.button_punch,
                            icon_color=(0.5, 0.3, 1.0, 1.0),
                            icon_scale=1.2,
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    title=strs.layout.centered_faded_title,
                    title_color=(0.6, 0.6, 1.0, 0.3),
                    title_flatness=1.0,
                    title_shadow=1.0,
                    subtitle=strs.layout.testing_centered,
                    subtitle_color=(1.0, 0.5, 1.0, 0.5),
                    subtitle_flatness=1.0,
                    subtitle_shadow=0.0,
                    center_content=True,
                    center_title=True,
                    buttons=[
                        dui2.Button(
                            label=strs.common.hello_there,
                            size=(200, 120),
                            color=(0.7, 0.7, 0.9, 1),
                        ),
                    ],
                ),
            ],
        )
    )

    # Include some client effects if they ask (the 'Response
    # ClientEffects' button). V2 effect forms; see the immediate-effects
    # note above.
    if request.args.get('test_effects', False):
        response.client_effects = [
            clfx.ScreenMessageV2(
                message=strs.effects.response_effects_hello, color=(0, 1, 0)
            ),
            clfx.PlaySoundV2(sound=builtinassets.audio.cash_register),
            clfx.Delay(1.0),
            clfx.ScreenMessageV2(
                message=strs.effects.effect_success, color=(0, 1, 0)
            ),
            clfx.PlaySoundV2(sound=builtinassets.audio.cash_register),
        ]

    # Include a local-action if they ask (the 'Response LocalAction'
    # button).
    if request.args.get('test_action', False):
        response.local_action = 'testaction'
        response.local_action_args = {'testparam': 234}

    return response


def _layout_test_decos(debug: bool) -> list[bacommon.docui.v2.Decoration]:
    """Decorations for the layout-test buttons (used on two buttons)."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    return [
        dui2.Image(
            texture=stdassets.textures.powerup_punch,
            position=(-70, 0),
            size=(40, 40),
            h_align=dui2.HAlign.LEFT,
        ),
        dui2.Image(
            texture=stdassets.textures.powerup_speed,
            position=(0, 75),
            size=(35, 35),
            v_align=dui2.VAlign.TOP,
        ),
        dui2.Text(
            text=strs.layout.corner_tl,
            position=(-70, 75),
            size=(50, 50),
            h_align=dui2.HAlign.LEFT,
            v_align=dui2.VAlign.TOP,
            debug=debug,
        ),
        dui2.Text(
            text=strs.layout.corner_tr,
            position=(70, 75),
            size=(50, 50),
            h_align=dui2.HAlign.RIGHT,
            v_align=dui2.VAlign.TOP,
            debug=debug,
        ),
        dui2.Text(
            text=strs.layout.corner_bl,
            position=(-70, -75),
            size=(50, 50),
            h_align=dui2.HAlign.LEFT,
            v_align=dui2.VAlign.BOTTOM,
            debug=debug,
        ),
        dui2.Text(
            text=strs.layout.corner_br,
            position=(70, -75),
            size=(50, 50),
            h_align=dui2.HAlign.RIGHT,
            v_align=dui2.VAlign.BOTTOM,
            debug=debug,
        ),
    ]


def _test_v2_page_2(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """More testing (v2 mirror of the v1 '/test2' page)."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    del request  # Unused.

    strs = _docuiv2testassets.strings

    return dui2.Response(
        page=dui2.Page(
            title=strs.nav.test_two_title,
            rows=[
                dui2.ButtonRow(
                    title=strs.nav.more_tests,
                    buttons=[
                        dui2.Button(
                            label=strs.nav.browse,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/')),
                        ),
                        dui2.Button(
                            label=strs.nav.replace,
                            size=(120, 80),
                            action=dui2.Replace(dui2.Request('/')),
                        ),
                        dui2.Button(
                            label=strs.nav.close,
                            size=(120, 80),
                            action=dui2.Local(close_window=True),
                            selected=True,  # Testing this
                        ),
                    ],
                ),
            ],
        )
    )


def _test_v2_page_long(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """Testing a page that takes a bit of time to load (v2 mirror)."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    del request  # Unused.

    strs = _docuiv2testassets.strings

    # Simulate a slow connection or whatnot.
    time.sleep(3.0)

    return dui2.Response(
        page=dui2.Page(
            title=strs.nav.test,
            center_vertically=True,
            rows=[
                dui2.ButtonRow(
                    title=strs.common.that_took_a_while,
                    center_title=True,
                    center_content=True,
                    buttons=[
                        dui2.Button(
                            label=strs.common.sure_did,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/')),
                        ),
                    ],
                ),
            ],
        )
    )


def _test_v2_page_timed_actions(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """Testing timed actions (v2 mirror of '/timedactions')."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    val = request.args.get('val')
    if not isinstance(val, int):
        val = 5

    return dui2.Response(
        page=dui2.Page(
            title=strs.nav.test,
            center_vertically=True,
            rows=[
                dui2.ButtonRow(
                    title=strs.common.hello_there_num(num=str(val)),
                    subtitle=strs.common.each_change,
                    center_title=True,
                    center_content=True,
                    buttons=[
                        dui2.Button(
                            label=strs.nav.done,
                            size=(120, 80),
                            action=dui2.Local(close_window=True),
                            default=True,
                        ),
                    ],
                ),
            ],
        ),
        # Refresh this page with a countdown until we hit zero and then
        # close the window.
        timed_action=(
            dui2.Replace(dui2.Request('/timedactions', args={'val': val - 1}))
            if (val - 1) > 0
            else dui2.Local(close_window=True)
        ),
        timed_action_delay=1.0,
    )


def _test_v2_page_empty(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """An empty page (v2 mirror of '/emptypage')."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    del request  # Unused.

    return dui2.Response(
        page=dui2.Page(
            title=_docuiv2testassets.strings.layout.empty_page_title, rows=[]
        )
    )


def _test_v2_page_display_items(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """Testing display-items (v2 mirror of '/displayitems')."""
    from bacommon.classic import ClassicChestAppearance, ClassicChestDisplayItem
    import bacommon.displayitem as ditm
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    def _make_test_button(
        scale: float,
        wrapper: ditm.Wrapper,
    ) -> bacommon.docui.v2.Button:

        # See how this looks when unrecognized (relying on wrapper info
        # only).
        uwrapper = copy.deepcopy(wrapper)
        uwrapper.item = ditm.Unknown()

        return dui2.Button(
            size=(300, 400),
            scale=scale,
            decorations=[
                dui2.DisplayItem(
                    wrapper=wrapper,
                    style=dui2.DisplayItemStyle.FULL,
                    position=(-62, 100),
                    size=(120, 120),
                    debug=debug,
                ),
                dui2.DisplayItem(
                    wrapper=uwrapper,
                    style=dui2.DisplayItemStyle.FULL,
                    position=(62, 100),
                    size=(120, 120),
                    debug=debug,
                ),
                dui2.DisplayItem(
                    wrapper=wrapper,
                    style=dui2.DisplayItemStyle.COMPACT,
                    position=(-55, -20),
                    size=(80, 80),
                    debug=debug,
                ),
                dui2.DisplayItem(
                    wrapper=uwrapper,
                    style=dui2.DisplayItemStyle.COMPACT,
                    position=(55, -20),
                    size=(80, 80),
                    debug=debug,
                ),
                dui2.DisplayItem(
                    wrapper=wrapper,
                    style=dui2.DisplayItemStyle.ICON,
                    position=(-55, -120),
                    size=(100, 80),
                    debug=debug,
                ),
                dui2.DisplayItem(
                    wrapper=uwrapper,
                    style=dui2.DisplayItemStyle.ICON,
                    position=(55, -120),
                    size=(100, 80),
                    debug=debug,
                ),
            ],
        )

    return dui2.Response(
        page=dui2.Page(
            padding_left=20,
            padding_right=20,
            title=strs.items.display_items,
            rows=[
                dui2.ButtonRow(
                    debug=debug,
                    padding_left=-10,
                    title=strs.items.display_item_tests,
                    subtitle=strs.items.display_items_sub,
                    buttons=[
                        _make_test_button(
                            1.0,
                            ditm.Wrapper.for_item(ditm.Tickets(count=213)),
                        ),
                        _make_test_button(
                            0.47,
                            ditm.Wrapper.for_item(ditm.Tickets(count=213)),
                        ),
                        _make_test_button(
                            1.0,
                            ditm.Wrapper.for_item(
                                ClassicChestDisplayItem(
                                    appearance=ClassicChestAppearance.L3
                                )
                            ),
                        ),
                        _make_test_button(
                            1.0,
                            ditm.Wrapper.for_item(ditm.Tokens(count=3)),
                        ),
                        _make_test_button(
                            1.0,
                            ditm.Wrapper.for_item(ditm.Tokens(count=1414287)),
                        ),
                        _make_test_button(
                            1.0,
                            ditm.Wrapper.for_item(ditm.Test()),
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=(
                                strs.common.hide_debug
                                if debug
                                else strs.common.show_debug
                            ),
                            style=dui2.ButtonStyle.MEDIUM,
                            size=(240, 60),
                            color=(0.6, 0.4, 0.8, 1.0),
                            action=dui2.Replace(
                                dui2.Request(
                                    request.path, args={'debug': not debug}
                                )
                            ),
                        )
                    ],
                ),
            ],
        )
    )


def _test_v2_bounds(
    request: bacommon.docui.v2.Request,
) -> bacommon.docui.v2.Response:
    """Button-style bounds tests (v2 mirror of '/boundstests')."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    del request  # Unused.

    strs = _docuiv2testassets.strings

    def _nm(style: bacommon.docui.v2.ButtonStyle) -> LangStr:
        # Code-literal pass-through: renders the raw enum name
        # verbatim in every locale.
        return strs.common.code_literal(
            text=f'{type(style).__name__}.{style.name}'
        )

    def _hello_row(
        title: LangStr,
        sizes: list[tuple[float, float]],
        style: bacommon.docui.v2.ButtonStyle,
        texture: bool = False,
    ) -> bacommon.docui.v2.ButtonRow:
        return dui2.ButtonRow(
            title=title,
            buttons=[
                dui2.Button(
                    label=strs.layout.hello,
                    size=size,
                    style=style,
                    texture=(builtinassets.textures.white if texture else None),
                    color=(1, 0, 0, 0.3) if texture else None,
                    debug=True,
                )
                for size in sizes
            ],
        )

    styles = dui2.ButtonStyle

    return dui2.Response(
        page=dui2.Page(
            title=strs.layout.bounds_tests_title,
            rows=[
                _hello_row(
                    _nm(styles.SQUARE),
                    [(300, 300), (200, 200), (100, 100)],
                    styles.SQUARE,
                ),
                _hello_row(
                    _nm(styles.SQUARE_WIDE),
                    [(400, 200), (200, 250), (60, 100)],
                    styles.SQUARE_WIDE,
                ),
                _hello_row(
                    strs.layout.background_texture,
                    [(300, 300), (200, 200), (100, 100)],
                    styles.SQUARE,
                    texture=True,
                ),
                _hello_row(
                    _nm(styles.TAB),
                    [(400, 100), (200, 50), (100, 60)],
                    styles.TAB,
                ),
                _hello_row(
                    _nm(styles.LARGER),
                    [(500, 100), (200, 50), (100, 60)],
                    styles.LARGER,
                ),
                _hello_row(
                    _nm(styles.LARGE),
                    [(400, 100), (200, 50), (100, 60)],
                    styles.LARGE,
                ),
                _hello_row(
                    _nm(styles.MEDIUM),
                    [(300, 100), (200, 50), (100, 60)],
                    styles.MEDIUM,
                ),
                _hello_row(
                    _nm(styles.SMALL),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.SMALL,
                ),
                _hello_row(
                    _nm(styles.BACK),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.BACK,
                ),
                _hello_row(
                    _nm(styles.BACK_SMALL),
                    [(200, 100), (200, 50), (100, 60)],
                    styles.BACK_SMALL,
                ),
            ],
        )
    )
