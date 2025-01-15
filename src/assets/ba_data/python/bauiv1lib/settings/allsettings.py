# Released under the MIT License. See LICENSE for details.
#
"""UI for top level settings categories."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable


class AllSettingsWindow(bui.MainWindow):
    """Window for selecting a settings category."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        bui.app.threadpool.submit_no_wait(self._preload_modules)

        bui.set_analytics_screen('Settings Window')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 900
        x_inset = 125 if uiscale is bui.UIScale.SMALL else 0
        height = 500 if uiscale is bui.UIScale.SMALL else 450
        self._r = 'settingsWindow'
        top_extra = 20 if uiscale is bui.UIScale.SMALL else 0
        yoffs = -30 if uiscale is bui.UIScale.SMALL else -30

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
                    else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
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
                position=(40 + x_inset, height - 60 + yoffs),
                size=(70, 70),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
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
            scale=1.1,
            maxwidth=130,
        )

        bwidth = 200
        bheight = 230
        margin = 1
        all_buttons_width = 4.0 * bwidth + 3.0 * margin

        x = width * 0.5 - all_buttons_width * 0.5
        y = height + yoffs - 335.0

        def _button(
            position: tuple[float, float],
            label: bui.Lstr,
            call: Callable[[], None],
            texture: bui.Texture,
            imgsize: float,
            *,
            color: tuple[float, float, float] = (1.0, 1.0, 1.0),
            imgoffs: tuple[float, float] = (0.0, 0.0),
        ) -> bui.Widget:
            x, y = position
            btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(x, y),
                size=(bwidth, bheight),
                button_type='square',
                label='',
                on_activate_call=call,
            )
            bui.textwidget(
                parent=self._root_widget,
                text=label,
                position=(x + bwidth * 0.5, y + bheight * 0.25),
                maxwidth=bwidth * 0.7,
                size=(0, 0),
                h_align='center',
                v_align='center',
                draw_controller=btn,
                color=(0.7, 0.9, 0.7, 1.0),
            )
            bui.imagewidget(
                parent=self._root_widget,
                position=(
                    x + bwidth * 0.5 - imgsize * 0.5 + imgoffs[0],
                    y + bheight * 0.56 - imgsize * 0.5 + imgoffs[1],
                ),
                size=(imgsize, imgsize),
                texture=texture,
                draw_controller=btn,
                color=color,
            )
            return btn

        self._controllers_button = _button(
            position=(x, y),
            label=bui.Lstr(resource=f'{self._r}.controllersText'),
            call=self._do_controllers,
            texture=bui.gettexture('controllerIcon'),
            imgsize=150,
            imgoffs=(-2.0, 2.0),
        )
        x += bwidth + margin

        self._graphics_button = _button(
            position=(x, y),
            label=bui.Lstr(resource=f'{self._r}.graphicsText'),
            call=self._do_graphics,
            texture=bui.gettexture('graphicsIcon'),
            imgsize=135,
            imgoffs=(0, 4.0),
        )
        x += bwidth + margin

        self._audio_button = _button(
            position=(x, y),
            label=bui.Lstr(resource=f'{self._r}.audioText'),
            call=self._do_audio,
            texture=bui.gettexture('audioIcon'),
            imgsize=150,
            color=(1, 1, 0),
        )
        x += bwidth + margin

        self._advanced_button = _button(
            position=(x, y),
            label=bui.Lstr(resource=f'{self._r}.advancedText'),
            call=self._do_advanced,
            texture=bui.gettexture('advancedIcon'),
            imgsize=150,
            color=(0.8, 0.95, 1),
            imgoffs=(0, 5.0),
        )

        # Hmm; we're now wide enough that being limited to pressing up
        # might be ok.
        if bool(False):
            # Left from our leftmost button should go to back button.
            if self._back_button is None:
                bbtn = bui.get_special_widget('back_button')
                bui.widget(edit=self._controllers_button, left_widget=bbtn)

            # Right from our rightmost widget should go to squad button.
            bui.widget(
                edit=self._advanced_button,
                right_widget=bui.get_special_widget('squad_button'),
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
