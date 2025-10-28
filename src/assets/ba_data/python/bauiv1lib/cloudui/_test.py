# Released under the MIT License. See LICENSE for details.
#
"""UIs provided by the cloud (similar-ish to html in concept)."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from bacommon.cloudui import CloudUIRequest
import bauiv1 as bui

from bauiv1lib.cloudui._window import CloudUIWindow
from bauiv1lib.cloudui._controller import CloudUIController

if TYPE_CHECKING:
    from bacommon.cloudui import CloudUIResponse
    import bacommon.cloudui.v1


def show_test_cloud_ui_window() -> None:
    """Bust out a cloud-ui window."""

    # Pop up an auxiliary window wherever we are in the nav stack.
    bui.app.ui_v1.auxiliary_window_activate(
        win_type=CloudUIWindow,
        win_create_call=bui.CallStrict(
            TestCloudUIController().create_window, CloudUIRequest('/')
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

        return clui.Response(
            code=clui.ResponseCode.SUCCESS,
            page=get_test_page(),
        )


def get_test_page() -> bacommon.cloudui.v1.Page:
    """Return test page."""
    import bacommon.cloudui.v1 as clui

    return clui.Page(
        title='Testing',
        rows=[
            clui.Row(
                title='First Row',
                debug=True,
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
                                debug=True,
                            ),
                            clui.Text(
                                'TR',
                                position=(70, 75),
                                size=(50, 50),
                                h_align=clui.HAlign.RIGHT,
                                v_align=clui.VAlign.TOP,
                                debug=True,
                            ),
                            clui.Text(
                                'BL',
                                position=(-70, -75),
                                size=(50, 50),
                                h_align=clui.HAlign.LEFT,
                                v_align=clui.VAlign.BOTTOM,
                                debug=True,
                            ),
                            clui.Text(
                                'BR',
                                position=(70, -75),
                                size=(50, 50),
                                h_align=clui.HAlign.RIGHT,
                                v_align=clui.VAlign.BOTTOM,
                                debug=True,
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
                        debug=True,  # Show bounds.
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
                                debug=True,
                            ),
                            clui.Text(
                                'TR',
                                position=(70, 75),
                                size=(50, 50),
                                h_align=clui.HAlign.RIGHT,
                                v_align=clui.VAlign.TOP,
                                debug=True,
                            ),
                            clui.Text(
                                'BL',
                                position=(-70, -75),
                                size=(50, 50),
                                h_align=clui.HAlign.LEFT,
                                v_align=clui.VAlign.BOTTOM,
                                debug=True,
                            ),
                            clui.Text(
                                'BR',
                                position=(70, -75),
                                size=(50, 50),
                                h_align=clui.HAlign.RIGHT,
                                v_align=clui.VAlign.BOTTOM,
                                debug=True,
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
                title='Second Row',
                subtitle='Second row subtitle.',
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
                                debug=True,
                            ),
                            clui.Text(
                                'MaxHeightTest\nSecondLine',
                                position=(0, -20),
                                size=(150 * 0.8, 40),
                                flatness=1.0,
                                shadow=0.0,
                                debug=True,
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
                ],
            ),
            clui.Row(
                buttons=[
                    clui.Button(
                        size=(100, 100),
                        color=(0.8, 0.8, 0.8),
                    ),
                    clui.Button(
                        size=(100, 100),
                        color=(0.8, 0.8, 0.8),
                    ),
                ],
            ),
            clui.Row(
                title='Last Row (Faded Title)',
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
    )
