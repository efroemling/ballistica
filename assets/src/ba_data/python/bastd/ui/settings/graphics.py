# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Provides UI for graphics settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Tuple, Optional


class GraphicsSettingsWindow(ba.Window):
    """Window for graphics settings."""

    def __init__(self,
                 transition: str = 'in_right',
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        from bastd.ui import popup
        from bastd.ui.config import ConfigCheckBox, ConfigNumberEdit
        # if they provided an origin-widget, scale up from that
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._r = 'graphicsSettingsWindow'
        app = ba.app

        spacing = 32
        self._have_selected_child = False
        uiscale = app.ui.uiscale
        width = 450.0
        height = 302.0

        self._show_fullscreen = False
        fullscreen_spacing_top = spacing * 0.2
        fullscreen_spacing = spacing * 1.2
        if uiscale == ba.UIScale.LARGE and app.platform != 'android':
            self._show_fullscreen = True
            height += fullscreen_spacing + fullscreen_spacing_top

        show_gamma = False
        gamma_spacing = spacing * 1.3
        if _ba.has_gamma_control():
            show_gamma = True
            height += gamma_spacing

        show_vsync = False
        if app.platform == 'mac':
            show_vsync = True

        show_resolution = True
        if app.vr_mode:
            show_resolution = (app.platform == 'android'
                               and app.subplatform == 'cardboard')

        uiscale = ba.app.ui.uiscale
        base_scale = (2.4 if uiscale is ba.UIScale.SMALL else
                      1.5 if uiscale is ba.UIScale.MEDIUM else 1.0)
        popup_menu_scale = base_scale * 1.2
        v = height - 50
        v -= spacing * 1.15
        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition=transition,
            scale_origin_stack_offset=scale_origin,
            scale=base_scale,
            stack_offset=(0, -30) if uiscale is ba.UIScale.SMALL else (0, 0)))

        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(35, height - 50),
                              size=(120, 60),
                              scale=0.8,
                              text_scale=1.2,
                              autoselect=True,
                              label=ba.Lstr(resource='backText'),
                              button_type='back',
                              on_activate_call=self._back)

        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(0, height - 44),
                      size=(width, 25),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='top')

        ba.buttonwidget(edit=btn,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        self._fullscreen_checkbox: Optional[ba.Widget]
        if self._show_fullscreen:
            v -= fullscreen_spacing_top
            self._fullscreen_checkbox = ConfigCheckBox(
                parent=self._root_widget,
                position=(100, v),
                maxwidth=200,
                size=(300, 30),
                configkey='Fullscreen',
                displayname=ba.Lstr(resource=self._r +
                                    ('.fullScreenCmdText' if app.platform ==
                                     'mac' else '.fullScreenCtrlText'))).widget
            if not self._have_selected_child:
                ba.containerwidget(edit=self._root_widget,
                                   selected_child=self._fullscreen_checkbox)
                self._have_selected_child = True
            v -= fullscreen_spacing
        else:
            self._fullscreen_checkbox = None

        self._gamma_controls: Optional[ConfigNumberEdit]
        if show_gamma:
            self._gamma_controls = gmc = ConfigNumberEdit(
                parent=self._root_widget,
                position=(90, v),
                configkey='Screen Gamma',
                displayname=ba.Lstr(resource=self._r + '.gammaText'),
                minval=0.1,
                maxval=2.0,
                increment=0.1,
                xoffset=-70,
                textscale=0.85)
            if ba.app.ui.use_toolbars:
                ba.widget(edit=gmc.plusbutton,
                          right_widget=_ba.get_special_widget('party_button'))
            if not self._have_selected_child:
                ba.containerwidget(edit=self._root_widget,
                                   selected_child=gmc.minusbutton)
                self._have_selected_child = True
            v -= gamma_spacing
        else:
            self._gamma_controls = None

        self._selected_color = (0.5, 1, 0.5, 1)
        self._unselected_color = (0.7, 0.7, 0.7, 1)

        # quality
        ba.textwidget(parent=self._root_widget,
                      position=(60, v),
                      size=(160, 25),
                      text=ba.Lstr(resource=self._r + '.visualsText'),
                      color=ba.app.ui.heading_color,
                      scale=0.65,
                      maxwidth=150,
                      h_align='center',
                      v_align='center')
        popup.PopupMenu(
            parent=self._root_widget,
            position=(60, v - 50),
            width=150,
            scale=popup_menu_scale,
            choices=['Auto', 'Higher', 'High', 'Medium', 'Low'],
            choices_disabled=['Higher', 'High']
            if _ba.get_max_graphics_quality() == 'Medium' else [],
            choices_display=[
                ba.Lstr(resource='autoText'),
                ba.Lstr(resource=self._r + '.higherText'),
                ba.Lstr(resource=self._r + '.highText'),
                ba.Lstr(resource=self._r + '.mediumText'),
                ba.Lstr(resource=self._r + '.lowText')
            ],
            current_choice=ba.app.config.resolve('Graphics Quality'),
            on_value_change_call=self._set_quality)

        # texture controls
        ba.textwidget(parent=self._root_widget,
                      position=(230, v),
                      size=(160, 25),
                      text=ba.Lstr(resource=self._r + '.texturesText'),
                      color=ba.app.ui.heading_color,
                      scale=0.65,
                      maxwidth=150,
                      h_align='center',
                      v_align='center')
        textures_popup = popup.PopupMenu(
            parent=self._root_widget,
            position=(230, v - 50),
            width=150,
            scale=popup_menu_scale,
            choices=['Auto', 'High', 'Medium', 'Low'],
            choices_display=[
                ba.Lstr(resource='autoText'),
                ba.Lstr(resource=self._r + '.highText'),
                ba.Lstr(resource=self._r + '.mediumText'),
                ba.Lstr(resource=self._r + '.lowText')
            ],
            current_choice=ba.app.config.resolve('Texture Quality'),
            on_value_change_call=self._set_textures)
        if ba.app.ui.use_toolbars:
            ba.widget(edit=textures_popup.get_button(),
                      right_widget=_ba.get_special_widget('party_button'))
        v -= 80

        h_offs = 0

        if show_resolution:
            # resolution
            ba.textwidget(parent=self._root_widget,
                          position=(h_offs + 60, v),
                          size=(160, 25),
                          text=ba.Lstr(resource=self._r + '.resolutionText'),
                          color=ba.app.ui.heading_color,
                          scale=0.65,
                          maxwidth=150,
                          h_align='center',
                          v_align='center')

            # on standard android we have 'Auto', 'Native', and a few
            # HD standards
            if app.platform == 'android':
                # on cardboard/daydream android we have a few
                # render-target-scale options
                if app.subplatform == 'cardboard':
                    current_res_cardboard = (str(min(100, max(10, int(round(
                        ba.app.config.resolve('GVR Render Target Scale')
                        * 100.0))))) + '%')  # yapf: disable
                    popup.PopupMenu(
                        parent=self._root_widget,
                        position=(h_offs + 60, v - 50),
                        width=120,
                        scale=popup_menu_scale,
                        choices=['100%', '75%', '50%', '35%'],
                        current_choice=current_res_cardboard,
                        on_value_change_call=self._set_gvr_render_target_scale)
                else:
                    native_res = _ba.get_display_resolution()
                    assert native_res is not None
                    choices = ['Auto', 'Native']
                    choices_display = [
                        ba.Lstr(resource='autoText'),
                        ba.Lstr(resource='nativeText')
                    ]
                    for res in [1440, 1080, 960, 720, 480]:
                        # nav bar is 72px so lets allow for that in what
                        # choices we show
                        if native_res[1] >= res - 72:
                            res_str = str(res) + 'p'
                            choices.append(res_str)
                            choices_display.append(ba.Lstr(value=res_str))
                    current_res_android = ba.app.config.resolve(
                        'Resolution (Android)')
                    popup.PopupMenu(parent=self._root_widget,
                                    position=(h_offs + 60, v - 50),
                                    width=120,
                                    scale=popup_menu_scale,
                                    choices=choices,
                                    choices_display=choices_display,
                                    current_choice=current_res_android,
                                    on_value_change_call=self._set_android_res)
            else:
                # if we're on a system that doesn't allow setting resolution,
                # set pixel-scale instead
                current_res = _ba.get_display_resolution()
                if current_res is None:
                    current_res2 = (str(min(100, max(10, int(round(
                        ba.app.config.resolve('Screen Pixel Scale')
                        * 100.0))))) + '%')  # yapf: disable
                    popup.PopupMenu(
                        parent=self._root_widget,
                        position=(h_offs + 60, v - 50),
                        width=120,
                        scale=popup_menu_scale,
                        choices=['100%', '88%', '75%', '63%', '50%'],
                        current_choice=current_res2,
                        on_value_change_call=self._set_pixel_scale)
                else:
                    raise Exception('obsolete path; discrete resolutions'
                                    ' no longer supported')

        # vsync
        if show_vsync:
            ba.textwidget(parent=self._root_widget,
                          position=(230, v),
                          size=(160, 25),
                          text=ba.Lstr(resource=self._r + '.verticalSyncText'),
                          color=ba.app.ui.heading_color,
                          scale=0.65,
                          maxwidth=150,
                          h_align='center',
                          v_align='center')

            popup.PopupMenu(
                parent=self._root_widget,
                position=(230, v - 50),
                width=150,
                scale=popup_menu_scale,
                choices=['Auto', 'Always', 'Never'],
                choices_display=[
                    ba.Lstr(resource='autoText'),
                    ba.Lstr(resource=self._r + '.alwaysText'),
                    ba.Lstr(resource=self._r + '.neverText')
                ],
                current_choice=ba.app.config.resolve('Vertical Sync'),
                on_value_change_call=self._set_vsync)

        v -= 90
        fpsc = ConfigCheckBox(parent=self._root_widget,
                              position=(69, v - 6),
                              size=(210, 30),
                              scale=0.86,
                              configkey='Show FPS',
                              displayname=ba.Lstr(resource=self._r +
                                                  '.showFPSText'),
                              maxwidth=130)

        # (tv mode doesnt apply to vr)
        if not ba.app.vr_mode:
            tvc = ConfigCheckBox(parent=self._root_widget,
                                 position=(240, v - 6),
                                 size=(210, 30),
                                 scale=0.86,
                                 configkey='TV Border',
                                 displayname=ba.Lstr(resource=self._r +
                                                     '.tvBorderText'),
                                 maxwidth=130)
            # grumble..
            ba.widget(edit=fpsc.widget, right_widget=tvc.widget)
        try:
            pass

        except Exception:
            ba.print_exception('Exception wiring up graphics settings UI:')

        v -= spacing

        # make a timer to update our controls in case the config changes
        # under us
        self._update_timer = ba.Timer(0.25,
                                      ba.WeakCall(self._update_controls),
                                      repeat=True,
                                      timetype=ba.TimeType.REAL)

    def _back(self) -> None:
        from bastd.ui.settings import allsettings
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            allsettings.AllSettingsWindow(
                transition='in_left').get_root_widget())

    def _set_quality(self, quality: str) -> None:
        cfg = ba.app.config
        cfg['Graphics Quality'] = quality
        cfg.apply_and_commit()

    def _set_textures(self, val: str) -> None:
        cfg = ba.app.config
        cfg['Texture Quality'] = val
        cfg.apply_and_commit()

    def _set_android_res(self, val: str) -> None:
        cfg = ba.app.config
        cfg['Resolution (Android)'] = val
        cfg.apply_and_commit()

    def _set_pixel_scale(self, res: str) -> None:
        cfg = ba.app.config
        cfg['Screen Pixel Scale'] = float(res[:-1]) / 100.0
        cfg.apply_and_commit()

    def _set_gvr_render_target_scale(self, res: str) -> None:
        cfg = ba.app.config
        cfg['GVR Render Target Scale'] = float(res[:-1]) / 100.0
        cfg.apply_and_commit()

    def _set_vsync(self, val: str) -> None:
        cfg = ba.app.config
        cfg['Vertical Sync'] = val
        cfg.apply_and_commit()

    def _update_controls(self) -> None:
        if self._show_fullscreen:
            ba.checkboxwidget(edit=self._fullscreen_checkbox,
                              value=ba.app.config.resolve('Fullscreen'))
