# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for Modding Tools."""

from __future__ import annotations

from typing import override

import babase
import bauiv1 as bui
from bauiv1lib.popup import PopupMenu
from bauiv1lib.confirm import ConfirmWindow
from bauiv1lib.config import ConfigCheckBox


class DevToolsWindow(bui.MainWindow):
    """Window for accessing modding tools."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        app = bui.app
        assert app.classic is not None

        uiscale = app.ui_v1.uiscale
        self._width = 1200.0 if uiscale is bui.UIScale.SMALL else 670.0
        self._height = (
            800
            if uiscale is bui.UIScale.SMALL
            else 450.0 if uiscale is bui.UIScale.MEDIUM else 520.0
        )
        self._spacing = 32

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.13
            if uiscale is bui.UIScale.SMALL
            else 1.4 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 80, screensize[0] / scale)
        target_height = min(self._height - 90, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        self._scroll_width = target_width
        self._scroll_height = target_height - 35
        self._scroll_bottom = yoffs - 64 - self._scroll_height

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 300.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
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

        self._r = 'settingsDevTools'

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(53, yoffs - 50),
                size=(140, 60),
                scale=0.8,
                autoselect=True,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (60 if uiscale is bui.UIScale.SMALL else 42),
            ),
            size=(0, 25),
            scale=(0.8 if uiscale is bui.UIScale.SMALL else 1.0),
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
            position=(
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
            ),
            simple_culling_v=20.0,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            selection_loops_to_parent=True,
            border_opacity=0.4,
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

        # Currently this is not wired up. The current official way to test
        # UIScales is either to use the switcher in the dev-console or to
        # set the BA_UI_SCALE env var.
        if bool(False):
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

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
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
