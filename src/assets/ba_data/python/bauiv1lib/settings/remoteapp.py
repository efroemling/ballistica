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
        width = 800 if uiscale is bui.UIScale.SMALL else 700
        height = 480 if uiscale is bui.UIScale.SMALL else 390
        yoffs = -48 if uiscale is bui.UIScale.SMALL else 0
        spacing = 40
        assert bui.app.classic is not None
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    1.75
                    if uiscale is bui.UIScale.SMALL
                    else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self.get_root_widget(),
                on_cancel_call=self.main_window_back,
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(40, height - 67 + yoffs),
                size=(140, 65),
                scale=0.8,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                text_scale=1.1,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
            bui.buttonwidget(
                edit=btn,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, height - 42 + yoffs),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            maxwidth=370,
            color=bui.app.ui_v1.title_color,
            scale=0.8,
            h_align='center',
            v_align='center',
        )

        v = height - 70.0
        v -= spacing * 1.2
        bui.textwidget(
            parent=self._root_widget,
            position=(15, v - 26 + yoffs),
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
            position=(width * 0.5, v + 5 + yoffs),
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
            position=(width * 0.5, v - 35 + yoffs),
            size=(0, 0),
            color=(0.7, 0.9, 0.7, 0.8),
            scale=0.65,
            text=bui.Lstr(resource=f'{self._r}.bestResultsText'),
            maxwidth=width * 0.95,
            max_height=height * 0.19,
            h_align='center',
            v_align='center',
        )

        bui.checkboxwidget(
            parent=self._root_widget,
            position=(width * 0.5 - 150, v - 116 + yoffs),
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
