# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for graphics settings."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

from bauiv1lib.popup import PopupMenu
from bauiv1lib.config import ConfigCheckBox
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class GraphicsSettingsWindow(bui.MainWindow):
    """Window for graphics settings."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        self._r = 'graphicsSettingsWindow'
        app = bui.app
        assert app.classic is not None

        spacing = 32
        self._have_selected_child = False
        uiscale = app.ui_v1.uiscale
        width = 450.0
        height = 302.0
        self._max_fps_dirty = False
        self._last_max_fps_set_time = bui.apptime()
        self._last_max_fps_str = ''

        self._show_fullscreen = False
        fullscreen_spacing_top = spacing * 0.2
        fullscreen_spacing = spacing * 1.2
        if bui.fullscreen_control_available():
            self._show_fullscreen = True
            height += fullscreen_spacing + fullscreen_spacing_top

        show_vsync = bui.supports_vsync()
        show_tv_mode = not bui.app.env.vr

        show_max_fps = bui.supports_max_fps()
        if show_max_fps:
            height += 50

        show_resolution = True
        if app.env.vr:
            show_resolution = (
                app.classic.platform == 'android'
                and app.classic.subplatform == 'cardboard'
            )

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        base_scale = (
            1.5
            if uiscale is bui.UIScale.SMALL
            else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        popup_menu_scale = base_scale * 1.2
        v = height - 50
        v -= spacing * 1.15
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                scale=base_scale,
                stack_offset=(
                    (0, -10) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
                toolbar_visibility=(
                    None if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, height - 50),
            size=(60, 60),
            scale=0.8,
            text_scale=1.2,
            autoselect=True,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.main_window_back,
        )

        bui.containerwidget(edit=self._root_widget, cancel_button=back_button)

        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 44),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='top',
        )

        self._fullscreen_checkbox: bui.Widget | None = None
        if self._show_fullscreen:
            v -= fullscreen_spacing_top
            # Fullscreen control does not necessarily talk to the
            # app config so we have to wrangle it manually instead of
            # using a config-checkbox.
            label = bui.Lstr(resource=f'{self._r}.fullScreenText')

            # Show keyboard shortcut alongside the control if they
            # provide one.
            shortcut = bui.fullscreen_control_key_shortcut()
            if shortcut is not None:
                label = bui.Lstr(
                    value='$(NAME) [$(SHORTCUT)]',
                    subs=[('$(NAME)', label), ('$(SHORTCUT)', shortcut)],
                )
            self._fullscreen_checkbox = bui.checkboxwidget(
                parent=self._root_widget,
                position=(100, v),
                value=bui.fullscreen_control_get(),
                on_value_change_call=bui.fullscreen_control_set,
                maxwidth=250,
                size=(300, 30),
                text=label,
            )

            if not self._have_selected_child:
                bui.containerwidget(
                    edit=self._root_widget,
                    selected_child=self._fullscreen_checkbox,
                )
                self._have_selected_child = True
            v -= fullscreen_spacing

        self._selected_color = (0.5, 1, 0.5, 1)
        self._unselected_color = (0.7, 0.7, 0.7, 1)

        # Quality
        bui.textwidget(
            parent=self._root_widget,
            position=(60, v),
            size=(160, 25),
            text=bui.Lstr(resource=f'{self._r}.visualsText'),
            color=bui.app.ui_v1.heading_color,
            scale=0.65,
            maxwidth=150,
            h_align='center',
            v_align='center',
        )
        PopupMenu(
            parent=self._root_widget,
            position=(60, v - 50),
            width=150,
            scale=popup_menu_scale,
            choices=['Auto', 'Higher', 'High', 'Medium', 'Low'],
            choices_disabled=(
                ['Higher', 'High']
                if bui.get_max_graphics_quality() == 'Medium'
                else []
            ),
            choices_display=[
                bui.Lstr(resource='autoText'),
                bui.Lstr(resource=f'{self._r}.higherText'),
                bui.Lstr(resource=f'{self._r}.highText'),
                bui.Lstr(resource=f'{self._r}.mediumText'),
                bui.Lstr(resource=f'{self._r}.lowText'),
            ],
            current_choice=bui.app.config.resolve('Graphics Quality'),
            on_value_change_call=self._set_quality,
        )

        # Texture controls
        bui.textwidget(
            parent=self._root_widget,
            position=(230, v),
            size=(160, 25),
            text=bui.Lstr(resource=f'{self._r}.texturesText'),
            color=bui.app.ui_v1.heading_color,
            scale=0.65,
            maxwidth=150,
            h_align='center',
            v_align='center',
        )
        textures_popup = PopupMenu(
            parent=self._root_widget,
            position=(230, v - 50),
            width=150,
            scale=popup_menu_scale,
            choices=['Auto', 'High', 'Medium', 'Low'],
            choices_display=[
                bui.Lstr(resource='autoText'),
                bui.Lstr(resource=f'{self._r}.highText'),
                bui.Lstr(resource=f'{self._r}.mediumText'),
                bui.Lstr(resource=f'{self._r}.lowText'),
            ],
            current_choice=bui.app.config.resolve('Texture Quality'),
            on_value_change_call=self._set_textures,
        )
        bui.widget(
            edit=textures_popup.get_button(),
            right_widget=bui.get_special_widget('squad_button'),
        )
        v -= 80

        h_offs = 0

        resolution_popup: PopupMenu | None = None

        if show_resolution:
            bui.textwidget(
                parent=self._root_widget,
                position=(h_offs + 60, v),
                size=(160, 25),
                text=bui.Lstr(resource=f'{self._r}.resolutionText'),
                color=bui.app.ui_v1.heading_color,
                scale=0.65,
                maxwidth=150,
                h_align='center',
                v_align='center',
            )

            # On standard android we have 'Auto', 'Native', and a few
            # HD standards.
            if app.classic.platform == 'android':
                # on cardboard/daydream android we have a few
                # render-target-scale options
                if app.classic.subplatform == 'cardboard':
                    rawval = bui.app.config.resolve('GVR Render Target Scale')
                    current_res_cardboard = (
                        str(min(100, max(10, int(round(rawval * 100.0))))) + '%'
                    )
                    resolution_popup = PopupMenu(
                        parent=self._root_widget,
                        position=(h_offs + 60, v - 50),
                        width=120,
                        scale=popup_menu_scale,
                        choices=['100%', '75%', '50%', '35%'],
                        current_choice=current_res_cardboard,
                        on_value_change_call=self._set_gvr_render_target_scale,
                    )
                else:
                    native_res = bui.get_display_resolution()
                    assert native_res is not None
                    choices = ['Auto', 'Native']
                    choices_display = [
                        bui.Lstr(resource='autoText'),
                        bui.Lstr(resource='nativeText'),
                    ]
                    for res in [1440, 1080, 960, 720, 480]:
                        if native_res[1] >= res:
                            res_str = f'{res}p'
                            choices.append(res_str)
                            choices_display.append(bui.Lstr(value=res_str))
                    current_res_android = bui.app.config.resolve(
                        'Resolution (Android)'
                    )
                    resolution_popup = PopupMenu(
                        parent=self._root_widget,
                        position=(h_offs + 60, v - 50),
                        width=120,
                        scale=popup_menu_scale,
                        choices=choices,
                        choices_display=choices_display,
                        current_choice=current_res_android,
                        on_value_change_call=self._set_android_res,
                    )
            else:
                # If we're on a system that doesn't allow setting resolution,
                # set pixel-scale instead.
                current_res = bui.get_display_resolution()
                if current_res is None:
                    rawval = bui.app.config.resolve('Screen Pixel Scale')
                    current_res2 = (
                        str(min(100, max(10, int(round(rawval * 100.0))))) + '%'
                    )
                    resolution_popup = PopupMenu(
                        parent=self._root_widget,
                        position=(h_offs + 60, v - 50),
                        width=120,
                        scale=popup_menu_scale,
                        choices=['100%', '88%', '75%', '63%', '50%'],
                        current_choice=current_res2,
                        on_value_change_call=self._set_pixel_scale,
                    )
                else:
                    raise RuntimeError(
                        'obsolete code path; discrete resolutions'
                        ' no longer supported'
                    )
        if resolution_popup is not None:
            bui.widget(
                edit=resolution_popup.get_button(),
                left_widget=back_button,
            )

        vsync_popup: PopupMenu | None = None
        if show_vsync:
            bui.textwidget(
                parent=self._root_widget,
                position=(230, v),
                size=(160, 25),
                text=bui.Lstr(resource=f'{self._r}.verticalSyncText'),
                color=bui.app.ui_v1.heading_color,
                scale=0.65,
                maxwidth=150,
                h_align='center',
                v_align='center',
            )
            vsync_popup = PopupMenu(
                parent=self._root_widget,
                position=(230, v - 50),
                width=150,
                scale=popup_menu_scale,
                choices=['Auto', 'Always', 'Never'],
                choices_display=[
                    bui.Lstr(resource='autoText'),
                    bui.Lstr(resource=f'{self._r}.alwaysText'),
                    bui.Lstr(resource=f'{self._r}.neverText'),
                ],
                current_choice=bui.app.config.resolve('Vertical Sync'),
                on_value_change_call=self._set_vsync,
            )
            if resolution_popup is not None:
                bui.widget(
                    edit=vsync_popup.get_button(),
                    left_widget=resolution_popup.get_button(),
                )

        if resolution_popup is not None and vsync_popup is not None:
            bui.widget(
                edit=resolution_popup.get_button(),
                right_widget=vsync_popup.get_button(),
            )

        v -= 90
        self._max_fps_text: bui.Widget | None = None
        if show_max_fps:
            v -= 5
            bui.textwidget(
                parent=self._root_widget,
                position=(155, v + 10),
                size=(0, 0),
                text=bui.Lstr(resource=f'{self._r}.maxFPSText'),
                color=bui.app.ui_v1.heading_color,
                scale=0.9,
                maxwidth=90,
                h_align='right',
                v_align='center',
            )

            max_fps_str = str(bui.app.config.resolve('Max FPS'))
            self._last_max_fps_str = max_fps_str
            self._max_fps_text = bui.textwidget(
                parent=self._root_widget,
                position=(170, v - 5),
                size=(105, 30),
                text=max_fps_str,
                max_chars=5,
                editable=True,
                h_align='left',
                v_align='center',
                on_return_press_call=self._on_max_fps_return_press,
            )
            v -= 45

        if self._max_fps_text is not None and resolution_popup is not None:
            bui.widget(
                edit=resolution_popup.get_button(),
                down_widget=self._max_fps_text,
            )
            bui.widget(
                edit=self._max_fps_text,
                up_widget=resolution_popup.get_button(),
            )

        fpsc = ConfigCheckBox(
            parent=self._root_widget,
            position=(69, v - 6),
            size=(210, 30),
            scale=0.86,
            configkey='Show FPS',
            displayname=bui.Lstr(resource=f'{self._r}.showFPSText'),
            maxwidth=130,
        )
        if self._max_fps_text is not None:
            bui.widget(
                edit=self._max_fps_text,
                down_widget=fpsc.widget,
            )
            bui.widget(
                edit=fpsc.widget,
                up_widget=self._max_fps_text,
            )

        if show_tv_mode:
            tvc = ConfigCheckBox(
                parent=self._root_widget,
                position=(240, v - 6),
                size=(210, 30),
                scale=0.86,
                configkey='TV Border',
                displayname=bui.Lstr(resource=f'{self._r}.tvBorderText'),
                maxwidth=130,
            )
            bui.widget(edit=fpsc.widget, right_widget=tvc.widget)
            bui.widget(edit=tvc.widget, left_widget=fpsc.widget)

        v -= spacing

        # Make a timer to update our controls in case the config changes
        # under us.
        self._update_timer = bui.AppTimer(
            0.25, bui.WeakCall(self._update_controls), repeat=True
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

    @override
    def on_main_window_close(self) -> None:
        self._apply_max_fps()

    def _set_quality(self, quality: str) -> None:
        cfg = bui.app.config
        cfg['Graphics Quality'] = quality
        cfg.apply_and_commit()

    def _set_textures(self, val: str) -> None:
        cfg = bui.app.config
        cfg['Texture Quality'] = val
        cfg.apply_and_commit()

    def _set_android_res(self, val: str) -> None:
        cfg = bui.app.config
        cfg['Resolution (Android)'] = val
        cfg.apply_and_commit()

    def _set_pixel_scale(self, res: str) -> None:
        cfg = bui.app.config
        cfg['Screen Pixel Scale'] = float(res[:-1]) / 100.0
        cfg.apply_and_commit()

    def _set_gvr_render_target_scale(self, res: str) -> None:
        cfg = bui.app.config
        cfg['GVR Render Target Scale'] = float(res[:-1]) / 100.0
        cfg.apply_and_commit()

    def _set_vsync(self, val: str) -> None:
        cfg = bui.app.config
        cfg['Vertical Sync'] = val
        cfg.apply_and_commit()

    def _on_max_fps_return_press(self) -> None:
        self._apply_max_fps()
        bui.containerwidget(
            edit=self._root_widget, selected_child=cast(bui.Widget, 0)
        )

    def _apply_max_fps(self) -> None:
        if not self._max_fps_dirty or not self._max_fps_text:
            return

        val: Any = bui.textwidget(query=self._max_fps_text)
        assert isinstance(val, str)
        # If there's a broken value, replace it with the default.
        try:
            ival = int(val)
        except ValueError:
            ival = bui.app.config.default_value('Max FPS')
        assert isinstance(ival, int)

        # Clamp to reasonable limits (allow -1 to mean no max).
        if ival != -1:
            ival = max(10, ival)
            ival = min(99999, ival)

        # Store it to the config.
        cfg = bui.app.config
        cfg['Max FPS'] = ival
        cfg.apply_and_commit()

        # Update the display if we changed the value.
        if str(ival) != val:
            bui.textwidget(edit=self._max_fps_text, text=str(ival))

        self._max_fps_dirty = False

    def _update_controls(self) -> None:
        if self._max_fps_text is not None:
            # Keep track of when the max-fps value changes. Once it
            # remains stable for a few moments, apply it.
            val: Any = bui.textwidget(query=self._max_fps_text)
            assert isinstance(val, str)
            if val != self._last_max_fps_str:
                # Oop; it changed. Note the time and the fact that we'll
                # need to apply it at some point.
                self._max_fps_dirty = True
                self._last_max_fps_str = val
                self._last_max_fps_set_time = bui.apptime()
            else:
                # If its been stable long enough, apply it.
                if (
                    self._max_fps_dirty
                    and bui.apptime() - self._last_max_fps_set_time > 1.0
                ):
                    self._apply_max_fps()

        if self._show_fullscreen:
            # Keep the fullscreen checkbox up to date with the current value.
            bui.checkboxwidget(
                edit=self._fullscreen_checkbox,
                value=bui.fullscreen_control_get(),
            )
