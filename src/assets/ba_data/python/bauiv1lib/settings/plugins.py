# Released under the MIT License. See LICENSE for details.
#
"""Plugin Window UI."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, assert_never, override

import bauiv1 as bui
from bauiv1lib import popup

if TYPE_CHECKING:
    pass


class Category(Enum):
    """Categories we can display."""

    ALL = 'all'
    ENABLED = 'enabled'
    DISABLED = 'disabled'

    @property
    def resource(self) -> str:
        """Resource name for us."""
        return f'{self.value}Text'


class PluginWindow(bui.MainWindow):
    """Window for configuring plugins."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        app = bui.app

        self._category = Category.ALL

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 870.0 if uiscale is bui.UIScale.SMALL else 670.0
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        yoffs = -55.0 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            450.0
            if uiscale is bui.UIScale.SMALL
            else 450.0 if uiscale is bui.UIScale.MEDIUM else 520.0
        )
        top_extra = 0 if uiscale is bui.UIScale.SMALL else 0
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + top_extra),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    1.9
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

        self._scroll_width = self._width - (100 + 2 * x_inset)
        self._scroll_height = self._height - (
            200.0 if uiscale is bui.UIScale.SMALL else 115.0
        )
        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 724.0

        assert app.classic is not None
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(53 + x_inset, self._height - 60 + yoffs),
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
            position=(self._width * 0.5, self._height - 41 + yoffs),
            size=(0, 0),
            text=bui.Lstr(resource='pluginsText'),
            color=app.ui_v1.title_color,
            maxwidth=170,
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

        settings_button_x = 670 if uiscale is bui.UIScale.SMALL else 570

        self._num_plugins_text = bui.textwidget(
            parent=self._root_widget,
            position=(settings_button_x - 130, self._height - 41 + yoffs),
            size=(0, 0),
            text='',
            h_align='center',
            v_align='center',
        )

        self._category_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(settings_button_x - 105, self._height - 60 + yoffs),
            size=(130, 60),
            label=bui.Lstr(resource='allText'),
            autoselect=True,
            on_activate_call=bui.WeakCall(self._show_category_options),
            color=(0.55, 0.73, 0.25),
            iconscale=1.2,
        )

        self._settings_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(settings_button_x, self._height - 58 + yoffs),
            size=(40, 40),
            label='',
            on_activate_call=self._open_settings,
        )

        bui.imagewidget(
            parent=self._root_widget,
            position=(settings_button_x + 3, self._height - 57 + yoffs),
            draw_controller=self._settings_button,
            size=(35, 35),
            texture=bui.gettexture('settingsIcon'),
        )

        bui.widget(
            edit=self._settings_button,
            up_widget=self._settings_button,
            right_widget=self._settings_button,
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(
                50 + x_inset,
                (135 if uiscale is bui.UIScale.SMALL else 50) + yoffs,
            ),
            simple_culling_v=20.0,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            selection_loops_to_parent=True,
            claims_left_right=True,
        )
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)

        self._no_plugins_installed_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            text='',
            color=(0.6, 0.6, 0.6),
            scale=0.8,
            h_align='center',
            v_align='center',
        )

        if bui.app.meta.scanresults is None:
            bui.screenmessage(
                'Still scanning plugins; please try again.', color=(1, 0, 0)
            )
            bui.getsound('error').play()
        plugspecs = bui.app.plugins.plugin_specs
        plugstates: dict[str, dict] = bui.app.config.get('Plugins', {})
        assert isinstance(plugstates, dict)

        plug_line_height = 50
        sub_width = self._scroll_width
        sub_height = len(plugspecs) * plug_line_height
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(sub_width, sub_height),
            background=False,
        )
        self._show_plugins()
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )
        self._restore_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _check_value_changed(self, plug: bui.PluginSpec, value: bool) -> None:
        bui.screenmessage(
            bui.Lstr(resource='settingsWindowAdvanced.mustRestartText'),
            color=(1.0, 0.5, 0.0),
        )
        plugstates: dict[str, dict] = bui.app.config.setdefault('Plugins', {})
        assert isinstance(plugstates, dict)
        plugstate = plugstates.setdefault(plug.class_path, {})
        plugstate['enabled'] = value
        bui.app.config.commit()

    def _open_settings(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.pluginsettings import PluginSettingsWindow

        # no-op if we don't have control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(PluginSettingsWindow(transition='in_right'))

    def _show_category_options(self) -> None:
        uiscale = bui.app.ui_v1.uiscale

        popup.PopupMenuWindow(
            position=self._category_button.get_screen_space_center(),
            scale=(
                2.3
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            ),
            choices=[c.value for c in Category],
            choices_display=[bui.Lstr(resource=c.resource) for c in Category],
            current_choice=self._category.value,
            delegate=self,
        )

    def popup_menu_selected_choice(
        self, popup_window: popup.PopupMenuWindow, choice: str
    ) -> None:
        """Called when a choice is selected in the popup."""
        del popup_window  # unused
        self._category = Category(choice)
        self._clear_scroll_widget()
        self._show_plugins()

        bui.buttonwidget(
            edit=self._category_button,
            label=bui.Lstr(resource=self._category.resource),
        )

    def popup_menu_closing(self, popup_window: popup.PopupWindow) -> None:
        """Called when the popup is closing."""

    def _clear_scroll_widget(self) -> None:
        existing_widgets = self._subcontainer.get_children()
        if existing_widgets:
            for i in existing_widgets:
                i.delete()

    def _show_plugins(self) -> None:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        plugspecs = bui.app.plugins.plugin_specs
        plugstates: dict[str, dict] = bui.app.config.setdefault('Plugins', {})
        assert isinstance(plugstates, dict)

        plug_line_height = 50
        sub_width = self._scroll_width
        num_enabled = 0
        num_disabled = 0

        plugspecs_sorted = sorted(plugspecs.items())

        bui.textwidget(
            edit=self._no_plugins_installed_text,
            text='',
        )

        for _classpath, plugspec in plugspecs_sorted:
            # counting number of enabled and disabled plugins
            # plugstate = plugstates.setdefault(plugspec[0], {})
            if plugspec.enabled:
                num_enabled += 1
            else:
                num_disabled += 1

        if self._category is Category.ALL:
            sub_height = len(plugspecs) * plug_line_height
            bui.containerwidget(
                edit=self._subcontainer, size=(self._scroll_width, sub_height)
            )
        elif self._category is Category.ENABLED:
            sub_height = num_enabled * plug_line_height
            bui.containerwidget(
                edit=self._subcontainer, size=(self._scroll_width, sub_height)
            )
        elif self._category is Category.DISABLED:
            sub_height = num_disabled * plug_line_height
            bui.containerwidget(
                edit=self._subcontainer, size=(self._scroll_width, sub_height)
            )
        else:
            # Make sure we handle all cases.
            assert_never(self._category)

        num_shown = 0
        for classpath, plugspec in plugspecs_sorted:
            plugin = plugspec.plugin
            enabled = plugspec.enabled

            if self._category is Category.ALL:
                show = True
            elif self._category is Category.ENABLED:
                show = enabled
            elif self._category is Category.DISABLED:
                show = not enabled
            else:
                assert_never(self._category)

            if not show:
                continue

            item_y = sub_height - (num_shown + 1) * plug_line_height
            check = bui.checkboxwidget(
                parent=self._subcontainer,
                text=bui.Lstr(value=classpath),
                autoselect=True,
                value=enabled,
                maxwidth=self._scroll_width
                - (
                    200
                    if plugin is not None and plugin.has_settings_ui()
                    else 80
                ),
                position=(10, item_y),
                size=(self._scroll_width - 40, 50),
                on_value_change_call=bui.Call(
                    self._check_value_changed, plugspec
                ),
                textcolor=(
                    (0.8, 0.3, 0.3)
                    if (plugspec.attempted_load and plugspec.plugin is None)
                    else (
                        (0.6, 0.6, 0.6)
                        if plugspec.plugin is None
                        else (0, 1, 0)
                    )
                ),
            )
            # noinspection PyUnresolvedReferences
            if plugin is not None and plugin.has_settings_ui():
                button = bui.buttonwidget(
                    parent=self._subcontainer,
                    label=bui.Lstr(resource='mainMenu.settingsText'),
                    autoselect=True,
                    size=(100, 40),
                    position=(sub_width - 130, item_y + 6),
                )
                # noinspection PyUnresolvedReferences
                bui.buttonwidget(
                    edit=button,
                    on_activate_call=bui.Call(plugin.show_settings_ui, button),
                )
            else:
                button = None

            # Allow getting back to back button.
            if num_shown == 0:
                bui.widget(
                    edit=check,
                    up_widget=self._back_button,
                    left_widget=self._back_button,
                    right_widget=(
                        self._settings_button if button is None else button
                    ),
                )
                if button is not None:
                    bui.widget(edit=button, up_widget=self._back_button)

            # Make sure we scroll all the way to the end when using
            # keyboard/button nav.
            bui.widget(edit=check, show_buffer_top=40, show_buffer_bottom=40)
            num_shown += 1

        bui.textwidget(
            edit=self._num_plugins_text,
            text=str(num_shown),
        )

        if num_shown == 0:
            bui.textwidget(
                edit=self._no_plugins_installed_text,
                text=bui.Lstr(resource='noPluginsInstalledText'),
            )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._category_button:
                sel_name = 'Category'
            elif sel == self._settings_button:
                sel_name = 'Settings'
            elif sel == self._back_button:
                sel_name = 'Back'
            elif sel == self._scrollwidget:
                sel_name = 'Scroll'
            else:
                raise ValueError(f'unrecognized selection \'{sel}\'')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = sel_name
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self))
            sel: bui.Widget | None
            if sel_name == 'Category':
                sel = self._category_button
            elif sel_name == 'Settings':
                sel = self._settings_button
            elif sel_name == 'Back':
                sel = self._back_button
            else:
                sel = self._scrollwidget
            if sel:
                bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)
