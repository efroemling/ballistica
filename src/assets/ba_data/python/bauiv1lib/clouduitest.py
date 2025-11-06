# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, override

from efro.error import CleanError
import bauiv1 as bui

from bauiv1lib.cloudui import CloudUIWindow, CloudUIController

if TYPE_CHECKING:
    from bacommon.cloudui import CloudUIRequest, CloudUIResponse
    import bacommon.cloudui.v1

    from bauiv1lib.cloudui import CloudUILocalAction


def show_test_cloud_ui_window() -> None:
    """Bust out a cloud-ui window."""
    import bacommon.cloudui.v1 as clui

    # Pop up an auxiliary window wherever we are in the nav stack.
    bui.app.ui_v1.auxiliary_window_activate(
        win_type=CloudUIWindow,
        win_create_call=bui.CallStrict(
            TestCloudUIController().create_window, clui.Request('/')
        ),
    )


class TestCloudUIController(CloudUIController):
    """Provides various tests/demonstrations of cloudui functionality."""

    @override
    def fulfill_request(self, request: CloudUIRequest) -> CloudUIResponse:
        """Fulfill a request.

        Will be called in a background thread.
        """
        import bacommon.cloudui.v1 as clui

        # We currently support v1 requests only.
        if not isinstance(request, clui.Request):
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

        # Ship '/webtest/*' off to some server to handle.
        if request.path.startswith('/webtest/'):
            return self.fulfill_request_http(
                request, 'https://www.ballistica.net/clouduitest'
            )

        raise CleanError('Invalid request path.')

    @override
    def local_action(self, action: CloudUILocalAction) -> None:
        bui.screenmessage(
            f'Would do {action.name!r} with args {action.args!r}.'
        )


def _test_page_long(
    request: bacommon.cloudui.v1.Request,
) -> bacommon.cloudui.v1.Response:
    """Testing a page that takes a bit of time to load."""
    import bacommon.cloudui.v1 as clui

    del request  # Unused.

    # Simulate a slow connection or whatnot.
    time.sleep(3.0)

    return clui.Response(
        page=clui.Page(
            title='Test',
            center_vertically=True,
            rows=[
                clui.Row(
                    title='That took a while',
                    center_title=True,
                    center_content=True,
                    buttons=[
                        clui.Button(
                            'Sure Did',
                            size=(120, 80),
                            action=clui.Browse(clui.Request('/')),
                        ),
                    ],
                ),
            ],
        )
    )


def _test_page_timed_actions(
    request: bacommon.cloudui.v1.Request,
) -> bacommon.cloudui.v1.Response:
    """Testing a page that takes a bit of time to load."""
    import bacommon.cloudui.v1 as clui

    val = request.args.get('val')
    if not isinstance(val, int):
        val = 5

    return clui.Response(
        page=clui.Page(
            title='Test',
            center_vertically=True,
            rows=[
                clui.Row(
                    title=f'Hello there {val}',
                    subtitle='Each change here is a new request/response.',
                    center_title=True,
                    center_content=True,
                    buttons=[
                        clui.Button(
                            'Done',
                            size=(120, 80),
                            action=clui.Local(close_window=True),
                            default=True,
                        ),
                    ],
                ),
            ],
        ),
        # Refresh this page with a countdown until we hit zero and then
        # close the window.
        timed_action=(
            clui.Replace(clui.Request('/timedactions', args={'val': val - 1}))
            if (val - 1) > 0
            else clui.Local(close_window=True)
        ),
        timed_action_delay=1.0,
    )


def _test_page_effects() -> bacommon.cloudui.v1.Page:
    """Testing effects after a page load."""
    import bacommon.cloudui.v1 as clui

    return clui.Page(
        title='Effects',
        center_vertically=True,
        rows=[
            clui.Row(
                title='Have some lovely effects',
                center_title=True,
                center_content=True,
                buttons=[
                    clui.Button(
                        'Nice!',
                        size=(120, 80),
                        action=clui.Local(close_window=True),
                    ),
                ],
            ),
        ],
    )


def _test_page_2(
    request: bacommon.cloudui.v1.Request,
) -> bacommon.cloudui.v1.Response:
    """More testing."""
    import bacommon.cloudui.v1 as clui

    del request  # Unused.

    return clui.Response(
        page=clui.Page(
            title='Test 2',
            rows=[
                clui.Row(
                    title='More Tests',
                    buttons=[
                        clui.Button(
                            'Browse',
                            size=(120, 80),
                            action=clui.Browse(clui.Request('/')),
                        ),
                        clui.Button(
                            'Replace',
                            size=(120, 80),
                            action=clui.Replace(clui.Request('/')),
                        ),
                        clui.Button(
                            'Close',
                            size=(120, 80),
                            action=clui.Local(close_window=True),
                            selected=True,  # Testing this
                        ),
                    ],
                ),
            ],
        )
    )


def _test_page_root(
    request: bacommon.cloudui.v1.Request,
) -> bacommon.cloudui.v1.Response:
    """Return test page."""

    import bacommon.bs
    import bacommon.cloudui.v1 as clui

    # Show some specific debug bits if they ask us to.
    debug = bool(request.args.get('debug', False))

    response = clui.Response(
        page=clui.Page(
            title='Test Root',
            rows=[
                clui.Row(
                    debug=debug,
                    header_height=100,
                    header_decorations_left=[
                        clui.Text(
                            'HeaderLeft',
                            position=(0, 10 + 20),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=clui.HAlign.LEFT,
                            debug=debug,
                        ),
                    ],
                    header_decorations_center=[
                        clui.Text(
                            'Look, a row header!',
                            position=(0, 10 + 20),
                            size=(300, 30),
                            debug=debug,
                        ),
                        clui.Text(
                            (
                                'Use this as reference for building'
                                ' UIs with CloudUI.'
                                ' It lives at bauiv1lib.clouduitest'
                            ),
                            scale=0.5,
                            position=(0, -18 + 20),
                            size=(600, 23),
                            debug=debug,
                        ),
                        clui.Image(
                            'nub', position=(0, -58 + 20), size=(60, 60)
                        ),
                    ],
                    header_decorations_right=[
                        clui.Text(
                            'HeaderRight',
                            position=(0, 10 + 20),
                            color=(1, 1, 1, 0.3),
                            size=(150, 30),
                            h_align=clui.HAlign.RIGHT,
                            debug=debug,
                        ),
                    ],
                    title='Action Tests',
                    buttons=[
                        clui.Button(
                            'Browse',
                            size=(120, 80),
                            action=clui.Browse(clui.Request('/test2')),
                        ),
                        clui.Button(
                            'Replace',
                            size=(120, 80),
                            action=clui.Replace(clui.Request('/test2')),
                        ),
                        clui.Button(
                            'Close',
                            size=(120, 80),
                            action=clui.Local(close_window=True),
                        ),
                        clui.Button(
                            'Invalid\nRequest',
                            size=(120, 80),
                            action=clui.Browse(clui.Request('/invalidrequest')),
                        ),
                        clui.Button(
                            'Immediate\nClientEffects',
                            size=(120, 80),
                            action=clui.Local(
                                immediate_client_effects=[
                                    bacommon.bs.ClientEffectScreenMessage(
                                        'Hello From Immediate Client Effects',
                                        color=(0, 1, 0),
                                    ),
                                    bacommon.bs.ClientEffectSound(
                                        sound=(
                                            bacommon.bs.ClientEffectSound
                                        ).Sound.CASH_REGISTER
                                    ),
                                    bacommon.bs.ClientEffectDelay(1.0),
                                    bacommon.bs.ClientEffectScreenMessage(
                                        '{"r":"successText"}',
                                        is_lstr=True,
                                        color=(0, 1, 0),
                                    ),
                                    bacommon.bs.ClientEffectSound(
                                        sound=(
                                            bacommon.bs.ClientEffectSound
                                        ).Sound.CASH_REGISTER
                                    ),
                                ]
                            ),
                        ),
                        clui.Button(
                            'Response\nClientEffects',
                            size=(120, 80),
                            action=clui.Browse(
                                clui.Request('/', args={'test_effects': True})
                            ),
                        ),
                        clui.Button(
                            'Immediate\nLocalAction',
                            size=(120, 80),
                            action=clui.Local(
                                immediate_local_action='testaction',
                                immediate_local_action_args={'testparam': 123},
                            ),
                        ),
                        clui.Button(
                            'Response\nLocalAction',
                            size=(120, 80),
                            action=clui.Browse(
                                clui.Request('/', args={'test_action': True})
                            ),
                        ),
                    ],
                ),
                clui.Row(
                    title='Other Tests',
                    buttons=[
                        clui.Button(
                            'Hide\nDebug' if debug else 'Show\nDebug',
                            size=(120, 80),
                            action=clui.Replace(
                                clui.Request('/', args={'debug': not debug})
                            ),
                        ),
                        clui.Button(
                            'Slow\nBrowse',
                            size=(120, 80),
                            action=clui.Browse(clui.Request('/slow')),
                        ),
                        clui.Button(
                            'Slow\nReplace',
                            size=(120, 80),
                            action=clui.Replace(clui.Request('/slow')),
                        ),
                        clui.Button(
                            'Timed\nActions',
                            size=(120, 80),
                            action=clui.Replace(clui.Request('/timedactions')),
                        ),
                        clui.Button(
                            'Web\nGET',
                            size=(120, 80),
                            action=clui.Browse(clui.Request('/webtest/get')),
                        ),
                        clui.Button(
                            'Web\nPOST',
                            size=(120, 80),
                            action=clui.Browse(
                                clui.Request(
                                    '/webtest/post',
                                    method=clui.RequestMethod.POST,
                                )
                            ),
                        ),
                    ],
                ),
                clui.Row(
                    title='Layout Tests',
                    debug=debug,
                    padding_left=5.0,
                    buttons=[
                        clui.Button(
                            label='Test',
                            size=(180, 200),
                            decorations=[
                                clui.Image(
                                    'powerupPunch',
                                    position=(-70, 0),
                                    size=(40, 40),
                                    h_align=clui.HAlign.LEFT,
                                ),
                                clui.Image(
                                    'powerupSpeed',
                                    position=(0, 75),
                                    size=(35, 35),
                                    v_align=clui.VAlign.TOP,
                                ),
                                clui.Text(
                                    'TL',
                                    position=(-70, 75),
                                    size=(50, 50),
                                    h_align=clui.HAlign.LEFT,
                                    v_align=clui.VAlign.TOP,
                                    debug=debug,
                                ),
                                clui.Text(
                                    'TR',
                                    position=(70, 75),
                                    size=(50, 50),
                                    h_align=clui.HAlign.RIGHT,
                                    v_align=clui.VAlign.TOP,
                                    debug=debug,
                                ),
                                clui.Text(
                                    'BL',
                                    position=(-70, -75),
                                    size=(50, 50),
                                    h_align=clui.HAlign.LEFT,
                                    v_align=clui.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                                clui.Text(
                                    'BR',
                                    position=(70, -75),
                                    size=(50, 50),
                                    h_align=clui.HAlign.RIGHT,
                                    v_align=clui.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                            ],
                        ),
                        clui.Button(
                            label='Test2',
                            size=(100, 100),
                            color=(1, 0, 0),
                            text_color=(1, 1, 1, 1),
                            padding_right=4,
                        ),
                        # Should look like the first button but
                        # scaled down.
                        clui.Button(
                            label='Test',
                            size=(180, 200),
                            scale=0.6,
                            padding_bottom=30,  # Should nudge us up.
                            debug=debug,  # Show bounds.
                            decorations=[
                                clui.Image(
                                    'powerupPunch',
                                    position=(-70, 0),
                                    size=(40, 40),
                                    h_align=clui.HAlign.LEFT,
                                ),
                                clui.Image(
                                    'powerupSpeed',
                                    position=(0, 75),
                                    size=(35, 35),
                                    v_align=clui.VAlign.TOP,
                                ),
                                clui.Text(
                                    'TL',
                                    position=(-70, 75),
                                    size=(50, 50),
                                    h_align=clui.HAlign.LEFT,
                                    v_align=clui.VAlign.TOP,
                                    debug=debug,
                                ),
                                clui.Text(
                                    'TR',
                                    position=(70, 75),
                                    size=(50, 50),
                                    h_align=clui.HAlign.RIGHT,
                                    v_align=clui.VAlign.TOP,
                                    debug=debug,
                                ),
                                clui.Text(
                                    'BL',
                                    position=(-70, -75),
                                    size=(50, 50),
                                    h_align=clui.HAlign.LEFT,
                                    v_align=clui.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                                clui.Text(
                                    'BR',
                                    position=(70, -75),
                                    size=(50, 50),
                                    h_align=clui.HAlign.RIGHT,
                                    v_align=clui.VAlign.BOTTOM,
                                    debug=debug,
                                ),
                            ],
                        ),
                        # Testing custom button images and opacity.
                        clui.Button(
                            label='Test3',
                            texture='buttonSquareWide',
                            padding_left=10.0,
                            padding_right=10.0,
                            color=(1, 1, 1),
                            opacity=0.3,
                            size=(200, 100),
                        ),
                    ],
                ),
                clui.Row(
                    title='Long Row Test',
                    subtitle='Look - a subtitle!',
                    buttons=[
                        clui.Button(
                            size=(150, 100),
                            decorations=[
                                clui.Text(
                                    'MaxWidthTest',
                                    position=(0, 25),
                                    size=(150 * 0.8, 32.0),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                                clui.Text(
                                    'MaxHeightTest\nSecondLine',
                                    position=(0, -20),
                                    size=(150 * 0.8, 40),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                            ],
                        ),
                        clui.Button(
                            size=(150, 100),
                            decorations=[
                                clui.Image(
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
                        clui.Button(
                            size=(150, 100),
                            decorations=[
                                clui.Image(
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
                        clui.Button(size=(150, 100)),
                        clui.Button(size=(150, 100)),
                        clui.Button(size=(150, 100)),
                        clui.Button(size=(150, 100)),
                        clui.Button(size=(150, 100)),
                    ],
                ),
                clui.Row(
                    buttons=[
                        clui.Button(
                            'Row-With-No-Title Test',
                            size=(300, 80),
                            style=clui.ButtonStyle.MEDIUM,
                            color=(0.8, 0.8, 0.8),
                            icon='buttonPunch',
                            icon_color=(0.5, 0.3, 1.0, 1.0),
                            icon_scale=1.2,
                        ),
                    ],
                ),
                clui.Row(
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
                        clui.Button(
                            'Hello There!',
                            size=(200, 120),
                            color=(0.7, 0.7, 0.9),
                        ),
                    ],
                ),
            ],
        ),
    )

    # Include some client effects if they ask.
    if request.args.get('test_effects', False):
        response.client_effects = [
            bacommon.bs.ClientEffectScreenMessage(
                'Hello From Response Client Effects',
                color=(0, 1, 0),
            ),
            bacommon.bs.ClientEffectSound(
                sound=(bacommon.bs.ClientEffectSound).Sound.CASH_REGISTER
            ),
            bacommon.bs.ClientEffectDelay(1.0),
            bacommon.bs.ClientEffectScreenMessage(
                '{"r":"successText"}',
                is_lstr=True,
                color=(0, 1, 0),
            ),
            bacommon.bs.ClientEffectSound(
                sound=(bacommon.bs.ClientEffectSound).Sound.CASH_REGISTER
            ),
        ]

    # Include a local-action if they ask.
    if request.args.get('test_action', False):
        response.local_action = 'testaction'
        response.local_action_args = {'testparam': 234}

    return response
