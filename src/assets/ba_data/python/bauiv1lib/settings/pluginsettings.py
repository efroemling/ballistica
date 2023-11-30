# Released under the MIT License. See LICENSE for details.
#
"""Plugin Settings UI."""

from __future__ import annotations

import bauiv1 as bui
from bauiv1lib.confirm import ConfirmWindow


class PluginSettingsWindow(bui.Window):
    """Plugin Settings Window"""

    def __init__(self, transition: str = 'in_right'):
        scale_origin: tuple[float, float] | None
        self._transition_out = 'out_right'
        scale_origin = None

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 470.0 if uiscale is bui.UIScale.SMALL else 470.0
        height = (
            365.0
            if uiscale is bui.UIScale.SMALL
            else 300.0
            if uiscale is bui.UIScale.MEDIUM
            else 370.0
        )
        top_extra = 10 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height + top_extra),
                transition=transition,
                toolbar_visibility='menu_minimal',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    2.06
                    if uiscale is bui.UIScale.SMALL
                    else 1.4
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
                stack_offset=(0, -25)
                if uiscale is bui.UIScale.SMALL
                else (0, 0),
            )
        )

        self._back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(53, height - 60),
            size=(60, 60),
            scale=0.8,
            autoselect=True,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._do_back,
        )
        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._back_button
        )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 52),
            size=(width, 25),
            text=bui.Lstr(resource='pluginSettingsText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='top',
        )

        self._y_position = 170 if uiscale is bui.UIScale.MEDIUM else 205
        self._enable_plugins_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(65, self._y_position),
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
            position=(65, self._y_position),
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
            position=(65, self._y_position),
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

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.plugins import PluginWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            PluginWindow(transition='in_left').get_root_widget(),
            from_window=self._root_widget,
        )
