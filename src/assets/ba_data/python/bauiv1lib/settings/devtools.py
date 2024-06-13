# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for Modding Tools."""

from __future__ import annotations

import babase
import bauiv1 as bui
from bauiv1lib.popup import PopupMenu
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.config import ConfigCheckBox


class DevToolsWindow(bui.Window):
    """Window for accessing modding tools."""

    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        app = bui.app
        assert app.classic is not None

        # If they provided an origin-widget, scale up from that.
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        uiscale = app.ui_v1.uiscale
        self._width = 970.0 if uiscale is bui.UIScale.SMALL else 670.0
        x_inset = 150 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            390.0
            if uiscale is bui.UIScale.SMALL
            else 450.0 if uiscale is bui.UIScale.MEDIUM else 520.0
        )

        self._spacing = 32
        top_extra = 10 if uiscale is bui.UIScale.SMALL else 0

        self._scroll_width = self._width - (100 + 2 * x_inset)
        self._scroll_height = self._height - 115.0
        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 350.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                transition=transition,
                toolbar_visibility='menu_minimal',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    2.06
                    if uiscale is bui.UIScale.SMALL
                    else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, -25) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            )
        )

        self._r = 'settingsDevTools'

        if app.ui_v1.use_toolbars and uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self._do_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(53 + x_inset, self._height - 60),
                size=(140, 60),
                scale=0.8,
                autoselect=True,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self._do_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 48),
            size=(0, 25),
            maxwidth=self._width - 200,
            text=bui.Lstr(resource='settingsWindowAdvanced.devToolsText'),
            color=app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        if self._back_button is not None:
            bui.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(50 + x_inset, 50),
            simple_culling_v=20.0,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            selection_loops_to_parent=True,
        )
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            selection_loops_to_parent=True,
        )

        v = self._sub_height - 35
        this_button_width = 410

        v -= self._spacing * 2.5
        self._show_dev_console_button_check_box = ConfigCheckBox(
            parent=self._subcontainer,
            position=(90, v + 40),
            size=(self._sub_width - 100, 30),
            configkey='Show Dev Console Button',
            displayname=bui.Lstr(
                resource='settingsWindowAdvanced.showDevConsoleButtonText'
            ),
            scale=1.0,
            maxwidth=400,
        )
        if self._back_button is not None:
            bui.widget(
                edit=self._show_dev_console_button_check_box.widget,
                up_widget=self._back_button,
            )

        v -= self._spacing * 1.2
        self._create_user_system_scripts_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource='userSystemScriptsCreateText'),
            text_scale=1.0,
            on_activate_call=babase.modutils.create_user_system_scripts,
        )

        v -= self._spacing * 2.5
        self._delete_user_system_scripts_button = bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width / 2 - this_button_width / 2, v - 10),
            size=(this_button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource='userSystemScriptsDeleteText'),
            text_scale=1.0,
            on_activate_call=lambda: ConfirmWindow(
                action=babase.modutils.delete_user_system_scripts,
            ),
        )

        v -= self._spacing * 2.5
        bui.textwidget(
            parent=self._subcontainer,
            position=(170, v + 10),
            size=(0, 0),
            text=bui.Lstr(resource='uiScaleText'),
            color=app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        PopupMenu(
            parent=self._subcontainer,
            position=(230, v - 20),
            button_size=(200.0, 60.0),
            width=100.0,
            choices=[
                'auto',
                'small',
                'medium',
                'large',
            ],
            choices_display=[
                bui.Lstr(resource='autoText'),
                bui.Lstr(resource='sizeSmallText'),
                bui.Lstr(resource='sizeMediumText'),
                bui.Lstr(resource='sizeLargeText'),
            ],
            current_choice=app.config.get('UI Scale', 'auto'),
            on_value_change_call=self._set_uiscale,
        )

    def _set_uiscale(self, val: str) -> None:
        cfg = bui.app.config
        cfg['UI Scale'] = val
        cfg.apply_and_commit()
        if bui.app.ui_v1.uiscale.name != val.upper():
            bui.screenmessage(
                bui.Lstr(resource='settingsWindowAdvanced.mustRestartText'),
                color=(1.0, 0.5, 0.0),
            )

    def _do_back(self) -> None:
        from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            AdvancedSettingsWindow(transition='in_left').get_root_widget(),
            from_window=self._root_widget,
        )
