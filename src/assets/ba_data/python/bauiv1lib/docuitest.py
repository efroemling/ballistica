# Released under the MIT License. See LICENSE for details.
#
"""Examples/tests for using DocUI to build UIs."""

# pylint: disable=too-many-lines

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
    import bacommon.docui.v1
    import bacommon.docui.v2
    from bacommon.langstr import LangStr

    from bauiv1lib.docui import DocUILocalAction


def _btex(name: str) -> str:
    """Qualified ref for a texture in the builtin asset-package."""
    return f'{builtinassets.__asset_package__}:textures/{name}'


def _stex(name: str) -> str:
    """Qualified stdassets texture ref."""
    return f'{stdassets.__asset_package__}:textures/{name}'


def show_test_doc_ui_window() -> None:
    """Bust out a doc-ui window."""
    import bacommon.docui.v1 as dui1

    # Pop up an auxiliary window wherever we are in the nav stack.
    bui.app.ui_v1.auxiliary_window_activate(
        win_type=DocUIWindow,
        win_create_call=bui.CallStrict(
            TestDocUIController().create_window, dui1.Request('/')
        ),
        win_extra_type_id=TestDocUIController.get_window_extra_type_id(),
    )


def show_test_doc_ui_v2_window() -> None:
    """Bust out a v2 (l-string) doc-ui window built locally on the client.

    The v2 mirror of :func:`show_test_doc_ui_window`: the same test
    pages, but authored as language-agnostic v2 documents — text as
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
    """The v2 (l-string) mirror of :class:`TestDocUIController`.

    Local pages are authored client-side; the ``/cloudmsgtest/*`` and
    ``/webtest/*`` paths fetch equivalent v2 pages from bamaster.
    """

    @override
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        """Fulfill a v2 request (called in a background thread)."""
        # pylint: disable=too-many-return-statements
        import bacommon.docui.v1 as dui1
        import bacommon.docui.v2 as dui2

        from bauiv1lib.docui._v2transcode import request_to_v2

        if not isinstance(request, (dui2.Request, dui1.Request)):
            raise CleanError('Invalid request version.')

        # Navigation from our (transcoded) pages hands us v1 requests;
        # normalize everything to our native v2 form.
        request = request_to_v2(request)

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
    ``builtinassets``/``stdassets``, and multi-line labels expressed as
    :class:`~bacommon.docui.WrapParams` instead of v1's hand-baked
    newlines. The client resolves the referenced packages in its own
    locale, decodes, and wraps -- so this single response renders in
    any language.
    """
    import bacommon.clienteffect as clfx
    import bacommon.docui.v2 as dui2
    from bacommon.docui import WrapParams

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    # v1 bakes newlines into two-line labels ('Invalid\nRequest'); we
    # instead give every button the same char budget and let labels
    # wrap per-locale. (Short labels staying on one line is fine.)
    label_wrap = WrapParams(max_chars_per_line=12)

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
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/test2')),
                        ),
                        dui2.Button(
                            label=strs.nav.replace,
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Replace(dui2.Request('/test2')),
                        ),
                        dui2.Button(
                            label=strs.nav.close,
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Local(close_window=True),
                        ),
                        dui2.Button(
                            label=strs.common.invalid_request,
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/invalidrequest')),
                        ),
                        dui2.Button(
                            label=strs.effects.immediate_client_effects,
                            label_wrap=label_wrap,
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
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Browse(
                                dui2.Request('/', args={'test_effects': True})
                            ),
                        ),
                        dui2.Button(
                            label=strs.effects.immediate_local_action,
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Local(
                                immediate_local_action='testaction',
                                immediate_local_action_args={'testparam': 123},
                            ),
                        ),
                        dui2.Button(
                            label=strs.effects.response_local_action,
                            label_wrap=label_wrap,
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
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Replace(
                                dui2.Request('/', args={'debug': not debug})
                            ),
                        ),
                        dui2.Button(
                            label=strs.nav.slow_browse,
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/slow')),
                        ),
                        dui2.Button(
                            label=strs.nav.slow_replace,
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Replace(dui2.Request('/slow')),
                        ),
                        dui2.Button(
                            label=strs.common.timed_actions,
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/timedactions')),
                        ),
                        dui2.Button(
                            label=strs.web.web_get,
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/webtest/get')),
                        ),
                        dui2.Button(
                            label=strs.web.web_post,
                            label_wrap=label_wrap,
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
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Browse(dui2.Request('/displayitems')),
                        ),
                        dui2.Button(
                            label=strs.layout.empty_page,
                            label_wrap=label_wrap,
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
                            label_wrap=label_wrap,
                            size=(120, 80),
                            action=dui2.Browse(
                                dui2.Request('/cloudmsgtest/get')
                            ),
                        ),
                        dui2.Button(
                            label=strs.cloud.cloud_msg_post,
                            label_wrap=label_wrap,
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
                            label_wrap=label_wrap,
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
                                    wrap=WrapParams(min_lines=2),
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


class TestDocUIController(DocUIController):
    """Provides various tests/demonstrations of docui functionality."""

    @override
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        """Fulfill a request.

        Will be called in a background thread.
        """
        # pylint: disable=too-many-return-statements

        import bacommon.docui.v1 as dui1

        # We currently support v1 requests only.
        if not isinstance(request, dui1.Request):
            raise CleanError('Invalid request version.')

        # Handle some pages purely locally.
        if request.path == '/':
            return _test_page_root(request)
        if request.path == '/test2':
            return _test_page_2(request)
        if request.path == '/slow':
            return _test_page_long(request)
        if request.path == '/timedactions':
            return _test_page_timed_actions(request)
        if request.path == '/displayitems':
            return _test_page_display_items(request)
        if request.path == '/emptypage':
            return _test_page_empty(request)
        if request.path == '/boundstests':
            return _test_bounds(request)

        # Ship '/webtest/*' off to some webserver to handle.
        if request.path.startswith('/webtest/'):
            return self.fulfill_request_web(
                request, 'https://www.ballistica.net/docuitest'
            )

        # Ship '/cloudmsgtest/*' through our cloud connection to handle.
        if request.path.startswith('/cloudmsgtest/'):
            return self.fulfill_request_cloud(request, 'test')

        raise CleanError('Invalid request path.')

    @override
    def local_action(self, action: DocUILocalAction) -> None:
        bui.screenmessage(
            f'Would do {action.name!r} with args {action.args!r}.'
        )


def _test_page_long(
    request: bacommon.docui.v1.Request,
) -> bacommon.docui.v1.Response:
    """Testing a page that takes a bit of time to load."""
    import bacommon.docui.v1 as dui1

    del request  # Unused.

    # Simulate a slow connection or whatnot.
    time.sleep(3.0)

    return dui1.Response(
        page=dui1.Page(
            title='Test',
            center_vertically=True,
            rows=[
                dui1.ButtonRow(
                    title='That took a while',
                    center_title=True,
                    center_content=True,
                    buttons=[
                        dui1.Button(
                            'Sure Did',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/')),
                        ),
                    ],
                ),
            ],
        )
    )


def _test_page_timed_actions(
    request: bacommon.docui.v1.Request,
) -> bacommon.docui.v1.Response:
    """Testing a page that takes a bit of time to load."""
    import bacommon.docui.v1 as dui1

    val = request.args.get('val')
    if not isinstance(val, int):
        val = 5

    return dui1.Response(
        page=dui1.Page(
            title='Test',
            center_vertically=True,
            rows=[
                dui1.ButtonRow(
                    title=f'Hello there {val}',
                    subtitle='Each change here is a new request/response.',
                    center_title=True,
                    center_content=True,
                    buttons=[
                        dui1.Button(
                            'Done',
                            size=(120, 80),
                            action=dui1.Local(close_window=True),
                            default=True,
                        ),
                    ],
                ),
            ],
        ),
        # Refresh this page with a countdown until we hit zero and then
        # close the window.
        timed_action=(
            dui1.Replace(dui1.Request('/timedactions', args={'val': val - 1}))
            if (val - 1) > 0
            else dui1.Local(close_window=True)
        ),
        timed_action_delay=1.0,
    )


def _test_page_effects() -> bacommon.docui.v1.Page:
    """Testing effects after a page load."""
    import bacommon.docui.v1 as dui1

    return dui1.Page(
        title='Effects',
        center_vertically=True,
        rows=[
            dui1.ButtonRow(
                title='Have some lovely effects',
                center_title=True,
                center_content=True,
                buttons=[
                    dui1.Button(
                        'Nice!',
                        size=(120, 80),
                        action=dui1.Local(close_window=True),
                    ),
                ],
            ),
        ],
    )


def _test_page_2(
    request: bacommon.docui.v1.Request,
) -> bacommon.docui.v1.Response:
    """More testing."""
    import bacommon.docui.v1 as dui1

    del request  # Unused.

    return dui1.Response(
        page=dui1.Page(
            title='Test 2',
            rows=[
                dui1.ButtonRow(
                    title='More Tests',
                    buttons=[
                        dui1.Button(
                            'Browse',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/')),
                        ),
                        dui1.Button(
                            'Replace',
                            size=(120, 80),
                            action=dui1.Replace(dui1.Request('/')),
                        ),
                        dui1.Button(
                            'Close',
                            size=(120, 80),
                            action=dui1.Local(close_window=True),
                            selected=True,  # Testing this
                        ),
                    ],
                ),
            ],
        )
    )


def _test_page_root(
    request: bacommon.docui.v1.Request,
) -> bacommon.docui.v1.Response:
    """Return test page."""

    import bacommon.clienteffect as clfx
    import bacommon.docui.v1 as dui1

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    response = dui1.Response(
        page=dui1.Page(
            title='Test Root',
            rows=[
                dui1.ButtonRow(
                    debug=debug,
                    header_height=100,
                    header_decorations_left=[
                        dui1.Text(
                            'HeaderLeft',
                            position=(0, 10 + 20),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui1.HAlign.LEFT,
                            debug=debug,
                        ),
                    ],
                    header_decorations_center=[
                        dui1.Text(
                            'Hello From DocUI!',
                            position=(0, 10 + 20),
                            size=(300, 30),
                            debug=debug,
                        ),
                        dui1.Text(
                            (
                                'Use this as reference for building'
                                ' UIs with DocUI.'
                                ' Its code lives at bauiv1lib.docuitest'
                            ),
                            scale=0.5,
                            position=(0, -18 + 20),
                            size=(600, 23),
                            debug=debug,
                        ),
                        dui1.Image(
                            _btex('nub'), position=(0, -58 + 20), size=(60, 60)
                        ),
                    ],
                    header_decorations_right=[
                        dui1.Text(
                            'HeaderRight',
                            position=(0, 10 + 20),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui1.HAlign.RIGHT,
                            debug=debug,
                        ),
                    ],
                    title='Some Tests',
                    buttons=[
                        dui1.Button(
                            'Browse',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/test2')),
                        ),
                        dui1.Button(
                            'Replace',
                            size=(120, 80),
                            action=dui1.Replace(dui1.Request('/test2')),
                        ),
                        dui1.Button(
                            'Close',
                            size=(120, 80),
                            action=dui1.Local(close_window=True),
                        ),
                        dui1.Button(
                            'Invalid\nRequest',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/invalidrequest')),
                        ),
                        dui1.Button(
                            'Immediate\nClientEffects',
                            size=(120, 80),
                            action=dui1.Local(
                                immediate_client_effects=[
                                    clfx.ScreenMessage(
                                        'Hello From Immediate Client Effects',
                                        color=(0, 1, 0),
                                    ),
                                    clfx.PlaySound(clfx.Sound.CASH_REGISTER),
                                    clfx.Delay(1.0),
                                    clfx.ScreenMessage(
                                        '{"r":"successText"}',
                                        is_lstr=True,
                                        color=(0, 1, 0),
                                    ),
                                    clfx.PlaySound(clfx.Sound.CASH_REGISTER),
                                ]
                            ),
                        ),
                        dui1.Button(
                            'Response\nClientEffects',
                            size=(120, 80),
                            action=dui1.Browse(
                                dui1.Request('/', args={'test_effects': True})
                            ),
                        ),
                        dui1.Button(
                            'Immediate\nLocalAction',
                            size=(120, 80),
                            action=dui1.Local(
                                immediate_local_action='testaction',
                                immediate_local_action_args={'testparam': 123},
                            ),
                        ),
                        dui1.Button(
                            'Response\nLocalAction',
                            size=(120, 80),
                            action=dui1.Browse(
                                dui1.Request('/', args={'test_action': True})
                            ),
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title='A Few More Tests',
                    buttons=[
                        dui1.Button(
                            'Hide\nDebug' if debug else 'Show\nDebug',
                            size=(120, 80),
                            action=dui1.Replace(
                                dui1.Request('/', args={'debug': not debug})
                            ),
                        ),
                        dui1.Button(
                            'Slow\nBrowse',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/slow')),
                        ),
                        dui1.Button(
                            'Slow\nReplace',
                            size=(120, 80),
                            action=dui1.Replace(dui1.Request('/slow')),
                        ),
                        dui1.Button(
                            'Timed\nActions',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/timedactions')),
                        ),
                        dui1.Button(
                            'Web\nGET',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/webtest/get')),
                        ),
                        dui1.Button(
                            'Web\nPOST',
                            size=(120, 80),
                            action=dui1.Browse(
                                dui1.Request(
                                    '/webtest/post',
                                    method=dui1.RequestMethod.POST,
                                )
                            ),
                        ),
                        dui1.Button(
                            'DisplayItems',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/displayitems')),
                        ),
                        dui1.Button(
                            'Empty\nPage',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/emptypage')),
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title='Even More Tests',
                    buttons=[
                        dui1.Button(
                            'Cloud-Msg\nGET',
                            size=(120, 80),
                            action=dui1.Browse(
                                dui1.Request('/cloudmsgtest/get')
                            ),
                        ),
                        dui1.Button(
                            'Cloud-Msg\nPOST',
                            size=(120, 80),
                            action=dui1.Browse(
                                dui1.Request(
                                    '/cloudmsgtest/post',
                                    method=dui1.RequestMethod.POST,
                                )
                            ),
                        ),
                        dui1.Button(
                            'Bounds\nTests',
                            size=(120, 80),
                            action=dui1.Browse(dui1.Request('/boundstests')),
                        ),
                    ],
                ),
                dui1.ButtonRow(title='Empty Row', buttons=[]),
                dui1.ButtonRow(
                    title='Layout Tests',
                    debug=debug,
                    padding_left=5.0,
                    buttons=[
                        dui1.Button(
                            label='Test',
                            size=(180, 200),
                            decorations=[
                                dui1.Image(
                                    _stex('powerup_punch'),
                                    position=(-70, 0),
                                    size=(40, 40),
                                    h_align=dui1.HAlign.LEFT,
                                ),
                                dui1.Image(
                                    _stex('powerup_speed'),
                                    position=(0, 75),
                                    size=(35, 35),
                                    v_align=dui1.VAlign.TOP,
                                ),
                                dui1.Text(
                                    'TL',
                                    position=(-70, 75),
                                    size=(50, 50),
                                    h_align=dui1.HAlign.LEFT,
                                    v_align=dui1.VAlign.TOP,
                                    debug=debug,
                                ),
                                dui1.Text(
                                    'TR',
                                    position=(70, 75),
                                    size=(50, 50),
                                    h_align=dui1.HAlign.RIGHT,
                                    v_align=dui1.VAlign.TOP,
                                    debug=debug,
                                ),
                                dui1.Text(
                                    'BL',
                                    position=(-70, -75),
                                    size=(50, 50),
                                    h_align=dui1.HAlign.LEFT,
                                    v_align=dui1.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                                dui1.Text(
                                    'BR',
                                    position=(70, -75),
                                    size=(50, 50),
                                    h_align=dui1.HAlign.RIGHT,
                                    v_align=dui1.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                            ],
                        ),
                        dui1.Button(
                            label='Test2',
                            size=(100, 100),
                            color=(1, 0, 0, 1),
                            label_color=(1, 1, 1, 1),
                            padding_right=4,
                        ),
                        # Should look like the first button but
                        # scaled down.
                        dui1.Button(
                            label='Test',
                            size=(180, 200),
                            scale=0.6,
                            padding_bottom=30,  # Should nudge us up.
                            debug=debug,  # Show bounds.
                            decorations=[
                                dui1.Image(
                                    _stex('powerup_punch'),
                                    position=(-70, 0),
                                    size=(40, 40),
                                    h_align=dui1.HAlign.LEFT,
                                ),
                                dui1.Image(
                                    _stex('powerup_speed'),
                                    position=(0, 75),
                                    size=(35, 35),
                                    v_align=dui1.VAlign.TOP,
                                ),
                                dui1.Text(
                                    'TL',
                                    position=(-70, 75),
                                    size=(50, 50),
                                    h_align=dui1.HAlign.LEFT,
                                    v_align=dui1.VAlign.TOP,
                                    debug=debug,
                                ),
                                dui1.Text(
                                    'TR',
                                    position=(70, 75),
                                    size=(50, 50),
                                    h_align=dui1.HAlign.RIGHT,
                                    v_align=dui1.VAlign.TOP,
                                    debug=debug,
                                ),
                                dui1.Text(
                                    'BL',
                                    position=(-70, -75),
                                    size=(50, 50),
                                    h_align=dui1.HAlign.LEFT,
                                    v_align=dui1.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                                dui1.Text(
                                    'BR',
                                    position=(70, -75),
                                    size=(50, 50),
                                    h_align=dui1.HAlign.RIGHT,
                                    v_align=dui1.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                            ],
                        ),
                        # Testing custom button images and opacity.
                        dui1.Button(
                            label='Test3',
                            texture=_btex('button_square_wide'),
                            padding_left=10.0,
                            padding_right=10.0,
                            color=(1, 1, 1, 0.3),
                            size=(200, 100),
                        ),
                        # Testing image drawing vs bounds
                        dui1.Button(
                            label='BoundsTest',
                            texture=_btex('white'),
                            color=(1, 1, 1, 0.3),
                            size=(150, 100),
                            debug=debug,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title='Long Row Test',
                    subtitle='Look - a subtitle!',
                    buttons=[
                        dui1.Button(
                            size=(150, 100),
                            decorations=[
                                dui1.Text(
                                    'MaxWidthTest',
                                    position=(0, 25),
                                    size=(150 * 0.8, 32.0),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                                dui1.Text(
                                    'MaxHeightTest\nSecondLine',
                                    position=(0, -20),
                                    size=(150 * 0.8, 40),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                            ],
                        ),
                        dui1.Button(
                            size=(150, 100),
                            decorations=[
                                dui1.Image(
                                    _stex('zoe_icon'),
                                    position=(0, 0),
                                    size=(70, 70),
                                    tint_texture=_stex('zoe_icon_color_mask'),
                                    tint_color=(1, 0, 0),
                                    tint2_color=(0, 1, 0),
                                    mask_texture=_btex('character_icon_mask'),
                                ),
                            ],
                        ),
                        dui1.Button(
                            size=(150, 100),
                            decorations=[
                                dui1.Image(
                                    _stex('bridgit_preview'),
                                    position=(0, 10),
                                    size=(120, 60),
                                    mask_texture=_stex('map_preview_mask'),
                                    mesh_opaque='level_select_button_opaque',
                                    mesh_transparent=(
                                        'level_select_button_transparent'
                                    ),
                                ),
                            ],
                        ),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(
                            'foo',
                            size=(150, 100),
                            scale=0.4,
                            padding_left=100,
                            padding_right=200,
                        ),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                        dui1.Button(size=(150, 100)),
                    ],
                ),
                dui1.ButtonRow(
                    spacing_top=-15,
                    subtitle='Subtitle only!',
                    buttons=[
                        dui1.Button(size=(200, 120)),
                    ],
                ),
                dui1.ButtonRow(
                    buttons=[
                        dui1.Button(
                            'Row-With-No-Title Test',
                            size=(300, 80),
                            style=dui1.ButtonStyle.MEDIUM,
                            color=(0.8, 0.8, 0.8, 1),
                            icon=_stex('button_punch'),
                            icon_color=(0.5, 0.3, 1.0, 1.0),
                            icon_scale=1.2,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title='Centered Content / Faded Title',
                    title_color=(0.6, 0.6, 1.0, 0.3),
                    title_flatness=1.0,
                    title_shadow=1.0,
                    subtitle='Testing Centered Title/Content',
                    subtitle_color=(1.0, 0.5, 1.0, 0.5),
                    subtitle_flatness=1.0,
                    subtitle_shadow=0.0,
                    center_content=True,
                    center_title=True,
                    buttons=[
                        dui1.Button(
                            'Hello There!',
                            size=(200, 120),
                            color=(0.7, 0.7, 0.9, 1),
                        ),
                    ],
                ),
            ],
        ),
    )

    # Include some client effects if they ask.
    if request.args.get('test_effects', False):
        response.client_effects = [
            clfx.ScreenMessage(
                'Hello From Response Client Effects', color=(0, 1, 0)
            ),
            clfx.PlaySound(clfx.Sound.CASH_REGISTER),
            clfx.Delay(1.0),
            clfx.ScreenMessage(
                '{"r":"successText"}', is_lstr=True, color=(0, 1, 0)
            ),
            clfx.PlaySound(clfx.Sound.CASH_REGISTER),
        ]

    # Include a local-action if they ask.
    if request.args.get('test_action', False):
        response.local_action = 'testaction'
        response.local_action_args = {'testparam': 234}

    return response


def _test_page_empty(
    request: bacommon.docui.v1.Request,
) -> bacommon.docui.v1.Response:
    import bacommon.docui.v1 as dui1

    del request  # Unused.

    return dui1.Response(page=dui1.Page(title='EmptyPage', rows=[]))


def _test_page_display_items(
    request: bacommon.docui.v1.Request,
) -> bacommon.docui.v1.Response:
    """Testing display-items."""
    from bacommon.classic import ClassicChestAppearance, ClassicChestDisplayItem
    import bacommon.docui.v1 as dui1
    import bacommon.displayitem as ditm

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    def _make_test_button(
        scale: float,
        wrapper: ditm.Wrapper,
    ) -> dui1.Button:

        # See how this looks when unrecognized (relying on wrapper info
        # only).
        uwrapper = copy.deepcopy(wrapper)
        uwrapper.item = ditm.Unknown()

        return dui1.Button(
            size=(300, 400),
            scale=scale,
            decorations=[
                dui1.DisplayItem(
                    wrapper=wrapper,
                    style=dui1.DisplayItemStyle.FULL,
                    position=(-62, 100),
                    size=(120, 120),
                    debug=debug,
                ),
                dui1.DisplayItem(
                    wrapper=uwrapper,
                    style=dui1.DisplayItemStyle.FULL,
                    position=(62, 100),
                    size=(120, 120),
                    debug=debug,
                ),
                dui1.DisplayItem(
                    wrapper=wrapper,
                    style=dui1.DisplayItemStyle.COMPACT,
                    position=(-55, -20),
                    size=(80, 80),
                    debug=debug,
                ),
                dui1.DisplayItem(
                    wrapper=uwrapper,
                    style=dui1.DisplayItemStyle.COMPACT,
                    position=(55, -20),
                    size=(80, 80),
                    debug=debug,
                ),
                dui1.DisplayItem(
                    wrapper=wrapper,
                    style=dui1.DisplayItemStyle.ICON,
                    position=(-55, -120),
                    size=(100, 80),
                    debug=debug,
                ),
                dui1.DisplayItem(
                    wrapper=uwrapper,
                    style=dui1.DisplayItemStyle.ICON,
                    position=(55, -120),
                    size=(100, 80),
                    debug=debug,
                ),
            ],
        )

    return dui1.Response(
        page=dui1.Page(
            padding_left=20,
            padding_right=20,
            title='DisplayItems',
            rows=[
                dui1.ButtonRow(
                    debug=debug,
                    padding_left=-10,
                    title='Display Item Tests',
                    subtitle=(
                        'top=FULL, center=COMPACT, bottom=ICON;'
                        ' left=regular, right=unknown'
                    ),
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
                dui1.ButtonRow(
                    buttons=[
                        dui1.Button(
                            'Hide Debug' if debug else 'Show Debug',
                            style=dui1.ButtonStyle.MEDIUM,
                            size=(240, 60),
                            color=(0.6, 0.4, 0.8, 1.0),
                            action=dui1.Replace(
                                dui1.Request(
                                    request.path, args={'debug': not debug}
                                )
                            ),
                        )
                    ],
                ),
            ],
        )
    )


def _test_bounds(
    request: bacommon.docui.v1.Request,
) -> bacommon.docui.v1.Response:
    import bacommon.docui.v1 as dui1

    del request  # Unused.

    def _nm(style: dui1.ButtonStyle) -> str:
        return f'{type(style).__name__}.{style.name}'

    return dui1.Response(
        page=dui1.Page(
            title='BoundsTests',
            rows=[
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.SQUARE),
                    buttons=[
                        dui1.Button('Hello', size=(300, 300), debug=True),
                        dui1.Button('Hello', size=(200, 200), debug=True),
                        dui1.Button('Hello', size=(100, 100), debug=True),
                    ],
                ),
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.SQUARE_WIDE),
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(400, 200),
                            style=dui1.ButtonStyle.SQUARE_WIDE,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 250),
                            style=dui1.ButtonStyle.SQUARE_WIDE,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(60, 100),
                            style=dui1.ButtonStyle.SQUARE_WIDE,
                            debug=True,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title='(background texture)',
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(300, 300),
                            texture=_btex('white'),
                            color=(1, 0, 0, 0.3),
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 200),
                            texture=_btex('white'),
                            color=(1, 0, 0, 0.3),
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(100, 100),
                            texture=_btex('white'),
                            color=(1, 0, 0, 0.3),
                            debug=True,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.TAB),
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(400, 100),
                            style=dui1.ButtonStyle.TAB,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 50),
                            style=dui1.ButtonStyle.TAB,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(100, 60),
                            style=dui1.ButtonStyle.TAB,
                            debug=True,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.LARGER),
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(500, 100),
                            style=dui1.ButtonStyle.LARGER,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 50),
                            style=dui1.ButtonStyle.LARGER,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(100, 60),
                            style=dui1.ButtonStyle.LARGER,
                            debug=True,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.LARGE),
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(400, 100),
                            style=dui1.ButtonStyle.LARGE,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 50),
                            style=dui1.ButtonStyle.LARGE,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(100, 60),
                            style=dui1.ButtonStyle.LARGE,
                            debug=True,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.MEDIUM),
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(300, 100),
                            style=dui1.ButtonStyle.MEDIUM,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 50),
                            style=dui1.ButtonStyle.MEDIUM,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(100, 60),
                            style=dui1.ButtonStyle.MEDIUM,
                            debug=True,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.SMALL),
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(200, 100),
                            style=dui1.ButtonStyle.SMALL,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 50),
                            style=dui1.ButtonStyle.SMALL,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(100, 60),
                            style=dui1.ButtonStyle.SMALL,
                            debug=True,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.BACK),
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(200, 100),
                            style=dui1.ButtonStyle.BACK,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 50),
                            style=dui1.ButtonStyle.BACK,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(100, 60),
                            style=dui1.ButtonStyle.BACK,
                            debug=True,
                        ),
                    ],
                ),
                dui1.ButtonRow(
                    title=_nm(dui1.ButtonStyle.BACK_SMALL),
                    buttons=[
                        dui1.Button(
                            'Hello',
                            size=(200, 100),
                            style=dui1.ButtonStyle.BACK_SMALL,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(200, 50),
                            style=dui1.ButtonStyle.BACK_SMALL,
                            debug=True,
                        ),
                        dui1.Button(
                            'Hello',
                            size=(100, 60),
                            style=dui1.ButtonStyle.BACK_SMALL,
                            debug=True,
                        ),
                    ],
                ),
            ],
        )
    )
