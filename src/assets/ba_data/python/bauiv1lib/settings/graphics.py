# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for graphics settings."""

from __future__ import annotations

import logging

from bauiv1lib.popup import PopupMenu
from bauiv1lib.config import ConfigCheckBox, ConfigNumberEdit
import bauiv1 as bui


class GraphicsSettingsWindow(bui.Window):
    """Window for graphics settings."""

    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        # if they provided an origin-widget, scale up from that
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._r = 'graphicsSettingsWindow'
        app = bui.app
        assert app.classic is not None

        spacing = 32
        self._have_selected_child = False
        uiscale = app.ui_v1.uiscale
        width = 450.0
        height = 302.0

        self._show_fullscreen = False
        fullscreen_spacing_top = spacing * 0.2
        fullscreen_spacing = spacing * 1.2
        if uiscale == bui.UIScale.LARGE and app.classic.platform != 'android':
            self._show_fullscreen = True
            height += fullscreen_spacing + fullscreen_spacing_top

        show_gamma = False
        gamma_spacing = spacing * 1.3
        if bui.has_gamma_control():
            show_gamma = True
            height += gamma_spacing

        show_vsync = False
        if app.classic.platform == 'mac':
            show_vsync = True

        show_resolution = True
        if app.env.vr:
            show_resolution = (
                app.classic.platform == 'android'
                and app.classic.subplatform == 'cardboard'
            )

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        base_scale = (
            2.4
            if uiscale is bui.UIScale.SMALL
            else 1.5
            if uiscale is bui.UIScale.MEDIUM
            else 1.0
        )
        popup_menu_scale = base_scale * 1.2
        v = height - 50
        v -= spacing * 1.15
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition=transition,
                scale_origin_stack_offset=scale_origin,
                scale=base_scale,
                stack_offset=(0, -30)
                if uiscale is bui.UIScale.SMALL
                else (0, 0),
            )
        )

        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, height - 50),
            size=(120, 60),
            scale=0.8,
            text_scale=1.2,
            autoselect=True,
            label=bui.Lstr(resource='backText'),
            button_type='back',
            on_activate_call=self._back,
        )

        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 44),
            size=(width, 25),
            text=bui.Lstr(resource=self._r + '.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='top',
        )

        bui.buttonwidget(
            edit=btn,
            button_type='backSmall',
            size=(60, 60),
            label=bui.charstr(bui.SpecialChar.BACK),
        )

        self._fullscreen_checkbox: bui.Widget | None = None
        self._gamma_controls: ConfigNumberEdit | None = None
        if self._show_fullscreen:
            v -= fullscreen_spacing_top
            self._fullscreen_checkbox = ConfigCheckBox(
                parent=self._root_widget,
                position=(100, v),
                maxwidth=200,
                size=(300, 30),
                configkey='Fullscreen',
                displayname=bui.Lstr(
                    resource=self._r
                    + (
                        '.fullScreenCmdText'
                        if app.classic.platform == 'mac'
                        else '.fullScreenCtrlText'
                    )
                ),
            ).widget
            if not self._have_selected_child:
                bui.containerwidget(
                    edit=self._root_widget,
                    selected_child=self._fullscreen_checkbox,
                )
                self._have_selected_child = True
            v -= fullscreen_spacing

        if show_gamma:
            self._gamma_controls = gmc = ConfigNumberEdit(
                parent=self._root_widget,
                position=(90, v),
                configkey='Screen Gamma',
                displayname=bui.Lstr(resource=self._r + '.gammaText'),
                minval=0.1,
                maxval=2.0,
                increment=0.1,
                xoffset=-70,
                textscale=0.85,
            )
            if bui.app.ui_v1.use_toolbars:
                bui.widget(
                    edit=gmc.plusbutton,
                    right_widget=bui.get_special_widget('party_button'),
                )
            if not self._have_selected_child:
                bui.containerwidget(
                    edit=self._root_widget, selected_child=gmc.minusbutton
                )
                self._have_selected_child = True
            v -= gamma_spacing

        self._selected_color = (0.5, 1, 0.5, 1)
        self._unselected_color = (0.7, 0.7, 0.7, 1)

        # quality
        bui.textwidget(
            parent=self._root_widget,
            position=(60, v),
            size=(160, 25),
            text=bui.Lstr(resource=self._r + '.visualsText'),
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
            choices_disabled=['Higher', 'High']
            if bui.get_max_graphics_quality() == 'Medium'
            else [],
            choices_display=[
                bui.Lstr(resource='autoText'),
                bui.Lstr(resource=self._r + '.higherText'),
                bui.Lstr(resource=self._r + '.highText'),
                bui.Lstr(resource=self._r + '.mediumText'),
                bui.Lstr(resource=self._r + '.lowText'),
            ],
            current_choice=bui.app.config.resolve('Graphics Quality'),
            on_value_change_call=self._set_quality,
        )

        # texture controls
        bui.textwidget(
            parent=self._root_widget,
            position=(230, v),
            size=(160, 25),
            text=bui.Lstr(resource=self._r + '.texturesText'),
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
                bui.Lstr(resource=self._r + '.highText'),
                bui.Lstr(resource=self._r + '.mediumText'),
                bui.Lstr(resource=self._r + '.lowText'),
            ],
            current_choice=bui.app.config.resolve('Texture Quality'),
            on_value_change_call=self._set_textures,
        )
        if bui.app.ui_v1.use_toolbars:
            bui.widget(
                edit=textures_popup.get_button(),
                right_widget=bui.get_special_widget('party_button'),
            )
        v -= 80

        h_offs = 0

        if show_resolution:
            # resolution
            bui.textwidget(
                parent=self._root_widget,
                position=(h_offs + 60, v),
                size=(160, 25),
                text=bui.Lstr(resource=self._r + '.resolutionText'),
                color=bui.app.ui_v1.heading_color,
                scale=0.65,
                maxwidth=150,
                h_align='center',
                v_align='center',
            )

            # on standard android we have 'Auto', 'Native', and a few
            # HD standards
            if app.classic.platform == 'android':
                # on cardboard/daydream android we have a few
                # render-target-scale options
                if app.classic.subplatform == 'cardboard':
                    current_res_cardboard = (
                        str(
                            min(
                                100,
                                max(
                                    10,
                                    int(
                                        round(
                                            bui.app.config.resolve(
                                                'GVR Render Target Scale'
                                            )
                                            * 100.0
                                        )
                                    ),
                                ),
                            )
                        )
                        + '%'
                    )
                    PopupMenu(
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
                        # nav bar is 72px so lets allow for that in what
                        # choices we show
                        if native_res[1] >= res - 72:
                            res_str = str(res) + 'p'
                            choices.append(res_str)
                            choices_display.append(bui.Lstr(value=res_str))
                    current_res_android = bui.app.config.resolve(
                        'Resolution (Android)'
                    )
                    PopupMenu(
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
                    current_res2 = (
                        str(
                            min(
                                100,
                                max(
                                    10,
                                    int(
                                        round(
                                            bui.app.config.resolve(
                                                'Screen Pixel Scale'
                                            )
                                            * 100.0
                                        )
                                    ),
                                ),
                            )
                        )
                        + '%'
                    )
                    PopupMenu(
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
                        'obsolete path; discrete resolutions'
                        ' no longer supported'
                    )

        # vsync
        if show_vsync:
            bui.textwidget(
                parent=self._root_widget,
                position=(230, v),
                size=(160, 25),
                text=bui.Lstr(resource=self._r + '.verticalSyncText'),
                color=bui.app.ui_v1.heading_color,
                scale=0.65,
                maxwidth=150,
                h_align='center',
                v_align='center',
            )

            PopupMenu(
                parent=self._root_widget,
                position=(230, v - 50),
                width=150,
                scale=popup_menu_scale,
                choices=['Auto', 'Always', 'Never'],
                choices_display=[
                    bui.Lstr(resource='autoText'),
                    bui.Lstr(resource=self._r + '.alwaysText'),
                    bui.Lstr(resource=self._r + '.neverText'),
                ],
                current_choice=bui.app.config.resolve('Vertical Sync'),
                on_value_change_call=self._set_vsync,
            )

        v -= 90
        fpsc = ConfigCheckBox(
            parent=self._root_widget,
            position=(69, v - 6),
            size=(210, 30),
            scale=0.86,
            configkey='Show FPS',
            displayname=bui.Lstr(resource=self._r + '.showFPSText'),
            maxwidth=130,
        )

        # (tv mode doesnt apply to vr)
        if not bui.app.env.vr:
            tvc = ConfigCheckBox(
                parent=self._root_widget,
                position=(240, v - 6),
                size=(210, 30),
                scale=0.86,
                configkey='TV Border',
                displayname=bui.Lstr(resource=self._r + '.tvBorderText'),
                maxwidth=130,
            )
            # grumble..
            bui.widget(edit=fpsc.widget, right_widget=tvc.widget)
        try:
            pass

        except Exception:
            logging.exception('Exception wiring up graphics settings UI.')

        v -= spacing

        # Make a timer to update our controls in case the config changes
        # under us.
        self._update_timer = bui.AppTimer(
            0.25, bui.WeakCall(self._update_controls), repeat=True
        )

    def _back(self) -> None:
        from bauiv1lib.settings import allsettings

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            allsettings.AllSettingsWindow(
                transition='in_left'
            ).get_root_widget()
        )

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

    def _update_controls(self) -> None:
        if self._show_fullscreen:
            bui.checkboxwidget(
                edit=self._fullscreen_checkbox,
                value=bui.app.config.resolve('Fullscreen'),
            )
