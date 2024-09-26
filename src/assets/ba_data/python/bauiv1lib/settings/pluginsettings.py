# Released under the MIT License. See LICENSE for details.
#
"""Plugin Settings UI."""

from __future__ import annotations

from typing import override

import bauiv1 as bui
from bauiv1lib.confirm import ConfirmWindow


class PluginSettingsWindow(bui.MainWindow):
    """Plugin Settings Window"""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 750.0 if uiscale is bui.UIScale.SMALL else 470.0
        height = 400.0 if uiscale is bui.UIScale.SMALL else 300.0
        yoffs = -20 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    2.06
                    if uiscale is bui.UIScale.SMALL
                    else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        if uiscale is bui.UIScale.SMALL:
            xoffs = 135
            self._back_button = bui.get_special_widget('back_button')
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            xoffs = 0
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(53, height - 60 + yoffs),
                size=(60, 60),
                scale=0.8,
                autoselect=True,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(
                width * 0.5,
                height - (55 if uiscale is bui.UIScale.SMALL else 35) + yoffs,
            ),
            size=(0, 0),
            text=bui.Lstr(resource='pluginSettingsText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        self._y_position = height - 140 + yoffs
        self._enable_plugins_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(xoffs + 65, self._y_position + yoffs),
            size=(350, 60),
            autoselect=True,
            label=bui.Lstr(resource='pluginsEnableAllText'),
            text_scale=1.0,
            on_activate_call=lambda: ConfirmWindow(
                action=self._enable_all_plugins,
            ),
        )

        self._y_position -= 70
        self._disable_plugins_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(xoffs + 65, self._y_position + yoffs),
            size=(350, 60),
            autoselect=True,
            label=bui.Lstr(resource='pluginsDisableAllText'),
            text_scale=1.0,
            on_activate_call=lambda: ConfirmWindow(
                action=self._disable_all_plugins,
            ),
        )

        self._y_position -= 70
        self._enable_new_plugins_check_box = bui.checkboxwidget(
            parent=self._root_widget,
            position=(xoffs + 65, self._y_position + yoffs),
            size=(350, 60),
            value=bui.app.config.get(
                bui.app.plugins.AUTO_ENABLE_NEW_PLUGINS_CONFIG_KEY,
                bui.app.plugins.AUTO_ENABLE_NEW_PLUGINS_DEFAULT,
            ),
            text=bui.Lstr(resource='pluginsAutoEnableNewText'),
            scale=1.0,
            maxwidth=308,
            on_value_change_call=self._update_value,
        )

        if uiscale is not bui.UIScale.SMALL:
            bui.widget(
                edit=self._back_button, down_widget=self._enable_plugins_button
            )

        bui.widget(
            edit=self._disable_plugins_button,
            left_widget=self._disable_plugins_button,
        )

        bui.widget(
            edit=self._enable_new_plugins_check_box,
            left_widget=self._enable_new_plugins_check_box,
            right_widget=self._enable_new_plugins_check_box,
            down_widget=self._enable_new_plugins_check_box,
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

    def _enable_all_plugins(self) -> None:
        cfg = bui.app.config
        plugs: dict[str, dict] = cfg.setdefault('Plugins', {})
        for plug in plugs.values():
            plug['enabled'] = True
        cfg.apply_and_commit()

        bui.screenmessage(
            bui.Lstr(resource='settingsWindowAdvanced.mustRestartText'),
            color=(1.0, 0.5, 0.0),
        )

    def _disable_all_plugins(self) -> None:
        cfg = bui.app.config
        plugs: dict[str, dict] = cfg.setdefault('Plugins', {})
        for plug in plugs.values():
            plug['enabled'] = False
        cfg.apply_and_commit()

        bui.screenmessage(
            bui.Lstr(resource='settingsWindowAdvanced.mustRestartText'),
            color=(1.0, 0.5, 0.0),
        )

    def _update_value(self, val: bool) -> None:
        cfg = bui.app.config
        cfg[bui.app.plugins.AUTO_ENABLE_NEW_PLUGINS_CONFIG_KEY] = val
        cfg.apply_and_commit()
