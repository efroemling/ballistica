# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

from __future__ import annotations

import time
import copy
from typing import TYPE_CHECKING, override

from efro.error import CleanError
import bauiv1 as bui

from bauiv1lib.decui import DecUIWindow, DecUIController

if TYPE_CHECKING:
    from bacommon.decui import DecUIRequest, DecUIResponse
    import bacommon.decui.v1

    from bauiv1lib.decui import DecUILocalAction


def show_test_cloud_ui_window() -> None:
    """Bust out a dec-ui window."""
    import bacommon.decui.v1 as dui

    # Pop up an auxiliary window wherever we are in the nav stack.
    bui.app.ui_v1.auxiliary_window_activate(
        win_type=DecUIWindow,
        win_create_call=bui.CallStrict(
            TestDecUIController().create_window, dui.Request('/')
        ),
    )


class TestDecUIController(DecUIController):
    """Provides various tests/demonstrations of decui functionality."""

    @override
    def fulfill_request(self, request: DecUIRequest) -> DecUIResponse:
        """Fulfill a request.

        Will be called in a background thread.
        """
        # pylint: disable=too-many-return-statements

        import bacommon.decui.v1 as dui

        # We currently support v1 requests only.
        if not isinstance(request, dui.Request):
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

        # Ship '/webtest/*' off to some webserver to handle.
        if request.path.startswith('/webtest/'):
            return self.fulfill_request_web(
                request, 'https://www.ballistica.net/decuitest'
            )

        # Ship '/cloudmsgtest/*' through our cloud connection to handle.
        if request.path.startswith('/cloudmsgtest/'):
            return self.fulfill_request_cloud(request, 'test')

        raise CleanError('Invalid request path.')

    @override
    def local_action(self, action: DecUILocalAction) -> None:
        bui.screenmessage(
            f'Would do {action.name!r} with args {action.args!r}.'
        )


def _test_page_long(
    request: bacommon.decui.v1.Request,
) -> bacommon.decui.v1.Response:
    """Testing a page that takes a bit of time to load."""
    import bacommon.decui.v1 as dui

    del request  # Unused.

    # Simulate a slow connection or whatnot.
    time.sleep(3.0)

    return dui.Response(
        page=dui.Page(
            title='Test',
            center_vertically=True,
            rows=[
                dui.ButtonRow(
                    title='That took a while',
                    center_title=True,
                    center_content=True,
                    buttons=[
                        dui.Button(
                            'Sure Did',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/')),
                        ),
                    ],
                ),
            ],
        )
    )


def _test_page_timed_actions(
    request: bacommon.decui.v1.Request,
) -> bacommon.decui.v1.Response:
    """Testing a page that takes a bit of time to load."""
    import bacommon.decui.v1 as dui

    val = request.args.get('val')
    if not isinstance(val, int):
        val = 5

    return dui.Response(
        page=dui.Page(
            title='Test',
            center_vertically=True,
            rows=[
                dui.ButtonRow(
                    title=f'Hello there {val}',
                    subtitle='Each change here is a new request/response.',
                    center_title=True,
                    center_content=True,
                    buttons=[
                        dui.Button(
                            'Done',
                            size=(120, 80),
                            action=dui.Local(close_window=True),
                            default=True,
                        ),
                    ],
                ),
            ],
        ),
        # Refresh this page with a countdown until we hit zero and then
        # close the window.
        timed_action=(
            dui.Replace(dui.Request('/timedactions', args={'val': val - 1}))
            if (val - 1) > 0
            else dui.Local(close_window=True)
        ),
        timed_action_delay=1.0,
    )


def _test_page_effects() -> bacommon.decui.v1.Page:
    """Testing effects after a page load."""
    import bacommon.decui.v1 as dui

    return dui.Page(
        title='Effects',
        center_vertically=True,
        rows=[
            dui.ButtonRow(
                title='Have some lovely effects',
                center_title=True,
                center_content=True,
                buttons=[
                    dui.Button(
                        'Nice!',
                        size=(120, 80),
                        action=dui.Local(close_window=True),
                    ),
                ],
            ),
        ],
    )


def _test_page_2(
    request: bacommon.decui.v1.Request,
) -> bacommon.decui.v1.Response:
    """More testing."""
    import bacommon.decui.v1 as dui

    del request  # Unused.

    return dui.Response(
        page=dui.Page(
            title='Test 2',
            rows=[
                dui.ButtonRow(
                    title='More Tests',
                    buttons=[
                        dui.Button(
                            'Browse',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/')),
                        ),
                        dui.Button(
                            'Replace',
                            size=(120, 80),
                            action=dui.Replace(dui.Request('/')),
                        ),
                        dui.Button(
                            'Close',
                            size=(120, 80),
                            action=dui.Local(close_window=True),
                            selected=True,  # Testing this
                        ),
                    ],
                ),
            ],
        )
    )


def _test_page_root(
    request: bacommon.decui.v1.Request,
) -> bacommon.decui.v1.Response:
    """Return test page."""

    import bacommon.clienteffect as clfx
    import bacommon.decui.v1 as dui

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    response = dui.Response(
        page=dui.Page(
            title='Test Root',
            rows=[
                dui.ButtonRow(
                    debug=debug,
                    header_height=100,
                    header_decorations_left=[
                        dui.Text(
                            'HeaderLeft',
                            position=(0, 10 + 20),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui.HAlign.LEFT,
                            debug=debug,
                        ),
                    ],
                    header_decorations_center=[
                        dui.Text(
                            'Hello From DecUI!',
                            position=(0, 10 + 20),
                            size=(300, 30),
                            debug=debug,
                        ),
                        dui.Text(
                            (
                                'Use this as reference for building'
                                ' UIs with DecUI.'
                                ' Its code lives at bauiv1lib.decuitest'
                            ),
                            scale=0.5,
                            position=(0, -18 + 20),
                            size=(600, 23),
                            debug=debug,
                        ),
                        dui.Image('nub', position=(0, -58 + 20), size=(60, 60)),
                    ],
                    header_decorations_right=[
                        dui.Text(
                            'HeaderRight',
                            position=(0, 10 + 20),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=dui.HAlign.RIGHT,
                            debug=debug,
                        ),
                    ],
                    title='Some Tests',
                    buttons=[
                        dui.Button(
                            'Browse',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/test2')),
                        ),
                        dui.Button(
                            'Replace',
                            size=(120, 80),
                            action=dui.Replace(dui.Request('/test2')),
                        ),
                        dui.Button(
                            'Close',
                            size=(120, 80),
                            action=dui.Local(close_window=True),
                        ),
                        dui.Button(
                            'Invalid\nRequest',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/invalidrequest')),
                        ),
                        dui.Button(
                            'Immediate\nClientEffects',
                            size=(120, 80),
                            action=dui.Local(
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
                        dui.Button(
                            'Response\nClientEffects',
                            size=(120, 80),
                            action=dui.Browse(
                                dui.Request('/', args={'test_effects': True})
                            ),
                        ),
                        dui.Button(
                            'Immediate\nLocalAction',
                            size=(120, 80),
                            action=dui.Local(
                                immediate_local_action='testaction',
                                immediate_local_action_args={'testparam': 123},
                            ),
                        ),
                        dui.Button(
                            'Response\nLocalAction',
                            size=(120, 80),
                            action=dui.Browse(
                                dui.Request('/', args={'test_action': True})
                            ),
                        ),
                    ],
                ),
                dui.ButtonRow(
                    title='A Few More Tests',
                    buttons=[
                        dui.Button(
                            'Hide\nDebug' if debug else 'Show\nDebug',
                            size=(120, 80),
                            action=dui.Replace(
                                dui.Request('/', args={'debug': not debug})
                            ),
                        ),
                        dui.Button(
                            'Slow\nBrowse',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/slow')),
                        ),
                        dui.Button(
                            'Slow\nReplace',
                            size=(120, 80),
                            action=dui.Replace(dui.Request('/slow')),
                        ),
                        dui.Button(
                            'Timed\nActions',
                            size=(120, 80),
                            action=dui.Replace(dui.Request('/timedactions')),
                        ),
                        dui.Button(
                            'Web\nGET',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/webtest/get')),
                        ),
                        dui.Button(
                            'Web\nPOST',
                            size=(120, 80),
                            action=dui.Browse(
                                dui.Request(
                                    '/webtest/post',
                                    method=dui.RequestMethod.POST,
                                )
                            ),
                        ),
                        dui.Button(
                            'DisplayItems',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/displayitems')),
                        ),
                        dui.Button(
                            'Empty\nPage',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/emptypage')),
                        ),
                    ],
                ),
                dui.ButtonRow(
                    title='Even More Tests',
                    buttons=[
                        dui.Button(
                            'Cloud-Msg\nGET',
                            size=(120, 80),
                            action=dui.Browse(dui.Request('/cloudmsgtest/get')),
                        ),
                        dui.Button(
                            'Cloud-Msg\nPOST',
                            size=(120, 80),
                            action=dui.Browse(
                                dui.Request(
                                    '/cloudmsgtest/post',
                                    method=dui.RequestMethod.POST,
                                )
                            ),
                        ),
                    ],
                ),
                dui.ButtonRow(title='Empty Row', buttons=[]),
                dui.ButtonRow(
                    title='Layout Tests',
                    debug=debug,
                    padding_left=5.0,
                    buttons=[
                        dui.Button(
                            label='Test',
                            size=(180, 200),
                            decorations=[
                                dui.Image(
                                    'powerupPunch',
                                    position=(-70, 0),
                                    size=(40, 40),
                                    h_align=dui.HAlign.LEFT,
                                ),
                                dui.Image(
                                    'powerupSpeed',
                                    position=(0, 75),
                                    size=(35, 35),
                                    v_align=dui.VAlign.TOP,
                                ),
                                dui.Text(
                                    'TL',
                                    position=(-70, 75),
                                    size=(50, 50),
                                    h_align=dui.HAlign.LEFT,
                                    v_align=dui.VAlign.TOP,
                                    debug=debug,
                                ),
                                dui.Text(
                                    'TR',
                                    position=(70, 75),
                                    size=(50, 50),
                                    h_align=dui.HAlign.RIGHT,
                                    v_align=dui.VAlign.TOP,
                                    debug=debug,
                                ),
                                dui.Text(
                                    'BL',
                                    position=(-70, -75),
                                    size=(50, 50),
                                    h_align=dui.HAlign.LEFT,
                                    v_align=dui.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                                dui.Text(
                                    'BR',
                                    position=(70, -75),
                                    size=(50, 50),
                                    h_align=dui.HAlign.RIGHT,
                                    v_align=dui.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                            ],
                        ),
                        dui.Button(
                            label='Test2',
                            size=(100, 100),
                            color=(1, 0, 0, 1),
                            label_color=(1, 1, 1, 1),
                            padding_right=4,
                        ),
                        # Should look like the first button but
                        # scaled down.
                        dui.Button(
                            label='Test',
                            size=(180, 200),
                            scale=0.6,
                            padding_bottom=30,  # Should nudge us up.
                            debug=debug,  # Show bounds.
                            decorations=[
                                dui.Image(
                                    'powerupPunch',
                                    position=(-70, 0),
                                    size=(40, 40),
                                    h_align=dui.HAlign.LEFT,
                                ),
                                dui.Image(
                                    'powerupSpeed',
                                    position=(0, 75),
                                    size=(35, 35),
                                    v_align=dui.VAlign.TOP,
                                ),
                                dui.Text(
                                    'TL',
                                    position=(-70, 75),
                                    size=(50, 50),
                                    h_align=dui.HAlign.LEFT,
                                    v_align=dui.VAlign.TOP,
                                    debug=debug,
                                ),
                                dui.Text(
                                    'TR',
                                    position=(70, 75),
                                    size=(50, 50),
                                    h_align=dui.HAlign.RIGHT,
                                    v_align=dui.VAlign.TOP,
                                    debug=debug,
                                ),
                                dui.Text(
                                    'BL',
                                    position=(-70, -75),
                                    size=(50, 50),
                                    h_align=dui.HAlign.LEFT,
                                    v_align=dui.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                                dui.Text(
                                    'BR',
                                    position=(70, -75),
                                    size=(50, 50),
                                    h_align=dui.HAlign.RIGHT,
                                    v_align=dui.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                            ],
                        ),
                        # Testing custom button images and opacity.
                        dui.Button(
                            label='Test3',
                            texture='buttonSquareWide',
                            padding_left=10.0,
                            padding_right=10.0,
                            color=(1, 1, 1, 0.3),
                            size=(200, 100),
                        ),
                    ],
                ),
                dui.ButtonRow(
                    title='Long Row Test',
                    subtitle='Look - a subtitle!',
                    buttons=[
                        dui.Button(
                            size=(150, 100),
                            decorations=[
                                dui.Text(
                                    'MaxWidthTest',
                                    position=(0, 25),
                                    size=(150 * 0.8, 32.0),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                                dui.Text(
                                    'MaxHeightTest\nSecondLine',
                                    position=(0, -20),
                                    size=(150 * 0.8, 40),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                            ],
                        ),
                        dui.Button(
                            size=(150, 100),
                            decorations=[
                                dui.Image(
                                    'zoeIcon',
                                    position=(0, 0),
                                    size=(70, 70),
                                    tint_texture='zoeIconColorMask',
                                    tint_color=(1, 0, 0),
                                    tint2_color=(0, 1, 0),
                                    mask_texture='characterIconMask',
                                ),
                            ],
                        ),
                        dui.Button(
                            size=(150, 100),
                            decorations=[
                                dui.Image(
                                    'bridgitPreview',
                                    position=(0, 10),
                                    size=(120, 60),
                                    mask_texture='mapPreviewMask',
                                    mesh_opaque='level_select_button_opaque',
                                    mesh_transparent=(
                                        'level_select_button_transparent'
                                    ),
                                ),
                            ],
                        ),
                        dui.Button(size=(150, 100)),
                        dui.Button(size=(150, 100)),
                        dui.Button(size=(150, 100)),
                        dui.Button(size=(150, 100)),
                        dui.Button(size=(150, 100)),
                    ],
                ),
                dui.ButtonRow(
                    buttons=[
                        dui.Button(
                            'Row-With-No-Title Test',
                            size=(300, 80),
                            style=dui.ButtonStyle.MEDIUM,
                            color=(0.8, 0.8, 0.8, 1),
                            icon='buttonPunch',
                            icon_color=(0.5, 0.3, 1.0, 1.0),
                            icon_scale=1.2,
                        ),
                    ],
                ),
                dui.ButtonRow(
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
                        dui.Button(
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
    request: bacommon.decui.v1.Request,
) -> bacommon.decui.v1.Response:
    import bacommon.decui.v1 as dui

    del request  # Unused.

    return dui.Response(page=dui.Page(title='EmptyPage', rows=[]))


def _test_page_display_items(
    request: bacommon.decui.v1.Request,
) -> bacommon.decui.v1.Response:
    """Testing display-items."""
    from bacommon.bs import ClassicChestAppearance, ClassicChestDisplayItem
    import bacommon.decui.v1 as dui
    import bacommon.displayitem as ditm

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    def _make_test_button(
        scale: float,
        wrapper: ditm.Wrapper,
    ) -> dui.Button:

        # See how this looks when unrecognized (relying on wrapper info
        # only).
        uwrapper = copy.deepcopy(wrapper)
        uwrapper.item = ditm.Unknown()

        return dui.Button(
            size=(300, 300),
            scale=scale,
            decorations=[
                dui.DisplayItem(
                    wrapper=wrapper,
                    style=dui.DisplayItemStyle.FULL,
                    position=(-62, 55),
                    size=(120, 120),
                    debug=debug,
                ),
                dui.DisplayItem(
                    wrapper=uwrapper,
                    style=dui.DisplayItemStyle.FULL,
                    position=(62, 55),
                    size=(120, 120),
                    debug=debug,
                ),
                dui.DisplayItem(
                    wrapper=wrapper,
                    style=dui.DisplayItemStyle.COMPACT,
                    position=(-55, -55),
                    size=(80, 80),
                    debug=debug,
                ),
                dui.DisplayItem(
                    wrapper=uwrapper,
                    style=dui.DisplayItemStyle.COMPACT,
                    position=(55, -55),
                    size=(80, 80),
                    debug=debug,
                ),
            ],
        )

    return dui.Response(
        page=dui.Page(
            padding_left=50,
            padding_top=50,
            padding_right=50,
            padding_bottom=50,
            title='DisplayItems',
            rows=[
                dui.ButtonRow(
                    debug=debug,
                    padding_left=-10,
                    title='Display Item Tests',
                    subtitle=(
                        'top=FULL, bottom=COMPACT, left=regular, right=unknown'
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
                dui.ButtonRow(
                    buttons=[
                        dui.Button(
                            'Hide Debug' if debug else 'Show Debug',
                            style=dui.ButtonStyle.LARGE,
                            size=(240, 40),
                            action=dui.Replace(
                                dui.Request(
                                    request.path, args={'debug': not debug}
                                )
                            ),
                        )
                    ],
                ),
            ],
        )
    )
