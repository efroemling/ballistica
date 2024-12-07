# Released under the MIT License. See LICENSE for details.
#
"""UI for top level settings categories."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui

if TYPE_CHECKING:
    pass


class AllSettingsWindow(bui.MainWindow):
    """Window for selecting a settings category."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        bui.app.threadpool.submit_no_wait(self._preload_modules)

        bui.set_analytics_screen('Settings Window')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 580
        x_inset = 125 if uiscale is bui.UIScale.SMALL else 0
        height = 500 if uiscale is bui.UIScale.SMALL else 435
        self._r = 'settingsWindow'
        top_extra = 20 if uiscale is bui.UIScale.SMALL else 0
        yoffs = -30 if uiscale is bui.UIScale.SMALL else 0

        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height + top_extra),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    1.5
                    if uiscale is bui.UIScale.SMALL
                    else 1.25 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(40 + x_inset, height - 55 + yoffs),
                size=(130, 60),
                scale=0.8,
                text_scale=1.2,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 44 + yoffs),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            maxwidth=130,
        )

        if self._back_button is not None:
            bui.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )

        v = height - 80 + yoffs
        v -= 145

        basew = 280 if uiscale is bui.UIScale.SMALL else 230
        baseh = 170
        x_offs = (
            x_inset + (105 if uiscale is bui.UIScale.SMALL else 72) - basew
        )  # now unused
        x_offs2 = x_offs + basew - 7
        x_offs3 = x_offs + 2 * (basew - 7)
        x_offs4 = x_offs2
        x_offs5 = x_offs3

        def _b_title(
            x: float, y: float, button: bui.Widget, text: str | bui.Lstr
        ) -> None:
            bui.textwidget(
                parent=self._root_widget,
                text=text,
                position=(x + basew * 0.47, y + baseh * 0.22),
                maxwidth=basew * 0.7,
                size=(0, 0),
                h_align='center',
                v_align='center',
                draw_controller=button,
                color=(0.7, 0.9, 0.7, 1.0),
            )

        ctb = self._controllers_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(x_offs2, v),
            size=(basew, baseh),
            button_type='square',
            label='',
            on_activate_call=self._do_controllers,
        )
        if self._back_button is None:
            bbtn = bui.get_special_widget('back_button')
            bui.widget(edit=ctb, left_widget=bbtn)
        _b_title(
            x_offs2, v, ctb, bui.Lstr(resource=f'{self._r}.controllersText')
        )
        imgw = imgh = 130
        bui.imagewidget(
            parent=self._root_widget,
            position=(x_offs2 + basew * 0.49 - imgw * 0.5, v + 35),
            size=(imgw, imgh),
            texture=bui.gettexture('controllerIcon'),
            draw_controller=ctb,
        )

        gfxb = self._graphics_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(x_offs3, v),
            size=(basew, baseh),
            button_type='square',
            label='',
            on_activate_call=self._do_graphics,
        )
        pbtn = bui.get_special_widget('squad_button')
        bui.widget(edit=gfxb, up_widget=pbtn, right_widget=pbtn)
        _b_title(x_offs3, v, gfxb, bui.Lstr(resource=f'{self._r}.graphicsText'))
        imgw = imgh = 110
        bui.imagewidget(
            parent=self._root_widget,
            position=(x_offs3 + basew * 0.49 - imgw * 0.5, v + 42),
            size=(imgw, imgh),
            texture=bui.gettexture('graphicsIcon'),
            draw_controller=gfxb,
        )

        v -= baseh - 5

        abtn = self._audio_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(x_offs4, v),
            size=(basew, baseh),
            button_type='square',
            label='',
            on_activate_call=self._do_audio,
        )
        _b_title(x_offs4, v, abtn, bui.Lstr(resource=f'{self._r}.audioText'))
        imgw = imgh = 120
        bui.imagewidget(
            parent=self._root_widget,
            position=(x_offs4 + basew * 0.49 - imgw * 0.5 + 5, v + 35),
            size=(imgw, imgh),
            color=(1, 1, 0),
            texture=bui.gettexture('audioIcon'),
            draw_controller=abtn,
        )

        avb = self._advanced_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(x_offs5, v),
            size=(basew, baseh),
            button_type='square',
            label='',
            on_activate_call=self._do_advanced,
        )
        _b_title(x_offs5, v, avb, bui.Lstr(resource=f'{self._r}.advancedText'))
        imgw = imgh = 120
        bui.imagewidget(
            parent=self._root_widget,
            position=(x_offs5 + basew * 0.49 - imgw * 0.5 + 5, v + 35),
            size=(imgw, imgh),
            color=(0.8, 0.95, 1),
            texture=bui.gettexture('advancedIcon'),
            draw_controller=avb,
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

    @staticmethod
    def _preload_modules() -> None:
        """Preload modules we use; avoids hitches (called in bg thread)."""
        import bauiv1lib.mainmenu as _unused1
        import bauiv1lib.settings.controls as _unused2
        import bauiv1lib.settings.graphics as _unused3
        import bauiv1lib.settings.audio as _unused4
        import bauiv1lib.settings.advanced as _unused5

    def _do_controllers(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.controls import ControlsSettingsWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            ControlsSettingsWindow(origin_widget=self._controllers_button)
        )

    def _do_graphics(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.graphics import GraphicsSettingsWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            GraphicsSettingsWindow(origin_widget=self._graphics_button)
        )

    def _do_audio(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.audio import AudioSettingsWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            AudioSettingsWindow(origin_widget=self._audio_button)
        )

    def _do_advanced(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(
            AdvancedSettingsWindow(origin_widget=self._advanced_button)
        )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._controllers_button:
                sel_name = 'Controllers'
            elif sel == self._graphics_button:
                sel_name = 'Graphics'
            elif sel == self._audio_button:
                sel_name = 'Audio'
            elif sel == self._advanced_button:
                sel_name = 'Advanced'
            elif sel == self._back_button:
                sel_name = 'Back'
            else:
                raise ValueError(f'unrecognized selection \'{sel}\'')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = {'sel_name': sel_name}
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get(
                'sel_name'
            )
            sel: bui.Widget | None
            if sel_name == 'Controllers':
                sel = self._controllers_button
            elif sel_name == 'Graphics':
                sel = self._graphics_button
            elif sel_name == 'Audio':
                sel = self._audio_button
            elif sel_name == 'Advanced':
                sel = self._advanced_button
            elif sel_name == 'Back':
                sel = self._back_button
            else:
                sel = self._controllers_button
            if sel is not None:
                bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)
