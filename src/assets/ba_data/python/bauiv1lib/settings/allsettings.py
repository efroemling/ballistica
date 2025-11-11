# Released under the MIT License. See LICENSE for details.
#
"""UI for top level settings categories."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable


class AllSettingsWindow(bui.MainWindow):
    """Window for selecting a settings category."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        auxiliary_style: bool = True,
    ):
        # pylint: disable=too-many-locals

        # Preload some modules we use in a background thread so we won't
        # have a visual hitch when the user taps them.
        bui.app.threadpool.submit_no_wait(self._preload_modules)

        self._uiopenstate = bui.UIOpenState('settings')

        bui.set_analytics_screen('Settings Window')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1000 if uiscale is bui.UIScale.SMALL else 900
        height = 800 if uiscale is bui.UIScale.SMALL else 450
        self._r = 'settingsWindow'

        uiscale = bui.app.ui_v1.uiscale

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        safesize = bui.get_virtual_safe_area_size()

        # We're a generally widescreen shaped window, so bump our
        # overall scale up a bit when screen width is wider than safe
        # bounds to take advantage of the extra space.
        smallscale = min(2.0, 1.5 * screensize[0] / safesize[0])

        scale = (
            smallscale
            if uiscale is bui.UIScale.SMALL
            else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.8
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_height = min(height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_full' if bui.in_main_menu() else 'menu_minimal'
                ),
                toolbar_cancel_button_style=(
                    'close' if auxiliary_style else 'back'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|back',
                autoselect=True,
                position=(50, yoffs - 80.0),
                size=(70, 70),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(
                    bui.SpecialChar.CLOSE
                    if auxiliary_style
                    else bui.SpecialChar.BACK
                ),
                button_type=None if auxiliary_style else 'backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - (70 if uiscale is bui.UIScale.SMALL else 60)),
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

        # This looks more visualy balanced slid down a bit (except in
        # small mode when we're showing full toolbars around it).
        ynudge = (
            0.0
            if uiscale is bui.UIScale.SMALL and bui.in_main_menu()
            else -20.0
        )
        y = height * 0.5 - bheight * 0.5 + ynudge

        def _button(
            *,
            widgetid: str,
            position: tuple[float, float],
            label: bui.Lstr,
            call: Callable[[], None],
            texture: bui.Texture,
            imgsize: float,
            color: tuple[float, float, float] = (1.0, 1.0, 1.0),
            imgoffs: tuple[float, float] = (0.0, 0.0),
        ) -> bui.Widget:
            x, y = position
            btn = bui.buttonwidget(
                parent=self._root_widget,
                id=widgetid,
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
            widgetid=f'{self.main_window_id_prefix}|controllers',
            position=(x, y),
            label=bui.Lstr(resource=f'{self._r}.controllersText'),
            call=self._do_controllers,
            texture=bui.gettexture('controllerIcon'),
            imgsize=150,
            imgoffs=(-2.0, 2.0),
        )
        x += bwidth + margin

        self._graphics_button = _button(
            widgetid=f'{self.main_window_id_prefix}|graphics',
            position=(x, y),
            label=bui.Lstr(resource=f'{self._r}.graphicsText'),
            call=self._do_graphics,
            texture=bui.gettexture('graphicsIcon'),
            imgsize=135,
            imgoffs=(0, 4.0),
        )
        x += bwidth + margin

        self._audio_button = _button(
            widgetid=f'{self.main_window_id_prefix}|audio',
            position=(x, y),
            label=bui.Lstr(resource=f'{self._r}.audioText'),
            call=self._do_audio,
            texture=bui.gettexture('audioIcon'),
            imgsize=150,
            color=(1, 1, 0),
        )
        x += bwidth + margin

        self._advanced_button = _button(
            widgetid=f'{self.main_window_id_prefix}|advanced',
            position=(x, y),
            label=bui.Lstr(resource=f'{self._r}.advancedText'),
            call=self._do_advanced,
            texture=bui.gettexture('advancedIcon'),
            imgsize=150,
            color=(0.8, 0.95, 1),
            imgoffs=(0, 5.0),
        )

        # Select controllers by default.
        bui.containerwidget(
            edit=self._root_widget, selected_child=self._controllers_button
        )

        # Hmm; we're now wide enough that being limited to pressing up
        # might be ok.
        if bool(True):
            # Left from our leftmost button should go to back button.
            if self._back_button is None:
                bbtn = bui.get_special_widget('back_button')
                bui.widget(edit=self._controllers_button, left_widget=bbtn)

            # Right from our rightmost widget should go to squad button.
            bui.widget(
                edit=self._advanced_button,
                right_widget=bui.get_special_widget('squad_button'),
            )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            ),
            # Keeps our icon glowing as long as this is in the back
            # stack.
            uiopenstate=self._uiopenstate,
        )

    @override
    def main_window_should_preserve_selection(self) -> bool:
        return True

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

        self.main_window_replace(
            lambda: ControlsSettingsWindow(
                origin_widget=self._controllers_button
            )
        )

    def _do_graphics(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.graphics import GraphicsSettingsWindow

        self.main_window_replace(
            lambda: GraphicsSettingsWindow(origin_widget=self._graphics_button)
        )

    def _do_audio(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.audio import AudioSettingsWindow

        self.main_window_replace(
            lambda: AudioSettingsWindow(origin_widget=self._audio_button)
        )

    def _do_advanced(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        self.main_window_replace(
            lambda: AdvancedSettingsWindow(origin_widget=self._advanced_button)
        )
