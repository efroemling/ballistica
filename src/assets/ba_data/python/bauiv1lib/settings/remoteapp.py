# Released under the MIT License. See LICENSE for details.
#
"""Settings UI functionality related to the remote app."""

from __future__ import annotations

from typing import override

import bauiv1 as bui


class RemoteAppSettingsWindow(bui.MainWindow):
    """Window showing info/settings related to the remote app."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ) -> None:
        self._r = 'connectMobileDevicesWindow'
        app = bui.app
        uiscale = app.ui_v1.uiscale
        width = 1200 if uiscale is bui.UIScale.SMALL else 700
        height = 800 if uiscale is bui.UIScale.SMALL else 390
        # yoffs = -48 if uiscale is bui.UIScale.SMALL else 0
        spacing = 40
        assert bui.app.classic is not None

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.75
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(width - 60, screensize[0] / scale)
        target_height = min(height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self.get_root_widget(),
                on_cancel_call=self.main_window_back,
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(40, yoffs - 67),
                size=(60, 60),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                text_scale=1.1,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(
                width * 0.5,
                yoffs - (62 if uiscale is bui.UIScale.SMALL else 42),
            ),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            maxwidth=370,
            color=bui.app.ui_v1.title_color,
            scale=0.8,
            h_align='center',
            v_align='center',
        )

        # Generally center the rest of our contents vertically.
        v = height * 0.5 + 140.0
        v -= spacing * 1.2
        bui.textwidget(
            parent=self._root_widget,
            position=(15, v - 26),
            size=(width - 30, 30),
            maxwidth=width * 0.95,
            color=(0.7, 0.9, 0.7, 1.0),
            scale=0.8,
            text=bui.Lstr(
                resource=f'{self._r}.explanationText',
                subs=[
                    ('${APP_NAME}', bui.Lstr(resource='titleText')),
                    ('${REMOTE_APP_NAME}', bui.get_remote_app_name()),
                ],
            ),
            max_height=100,
            h_align='center',
            v_align='center',
        )
        v -= 90

        # Update: now we just show link to the remote webpage.
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, v + 5),
            size=(0, 0),
            color=(0.7, 0.9, 0.7, 1.0),
            scale=1.4,
            text='bombsquadgame.com/remote',
            maxwidth=width * 0.95,
            max_height=60,
            h_align='center',
            v_align='center',
        )
        v -= 30

        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, v - 35),
            size=(0, 0),
            color=(0.7, 0.9, 0.7, 0.8),
            scale=0.65,
            text=bui.Lstr(resource=f'{self._r}.bestResultsText'),
            maxwidth=width * 0.95,
            max_height=100,
            h_align='center',
            v_align='center',
        )

        bui.checkboxwidget(
            parent=self._root_widget,
            position=(width * 0.5 - 150, v - 116),
            size=(300, 30),
            maxwidth=300,
            scale=0.8,
            value=not bui.app.config.resolve('Enable Remote App'),
            autoselect=True,
            text=bui.Lstr(resource='disableRemoteAppConnectionsText'),
            on_value_change_call=self._on_check_changed,
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    def _on_check_changed(self, value: bool) -> None:
        cfg = bui.app.config
        cfg['Enable Remote App'] = not value
        cfg.apply_and_commit()
