# Released under the MIT License. See LICENSE for details.
#
"""Provides audio settings UI."""

from __future__ import annotations

from typing import TYPE_CHECKING, override
import logging

import bauiv1 as bui

if TYPE_CHECKING:
    pass


class AudioSettingsWindow(bui.MainWindow):
    """Window for editing audio settings."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bauiv1lib.config import ConfigNumberEdit

        assert bui.app.classic is not None
        music = bui.app.classic.music

        self._r = 'audioSettingsWindow'

        spacing = 50.0
        uiscale = bui.app.ui_v1.uiscale

        width = 1200.0 if uiscale is bui.UIScale.SMALL else 500.0
        height = 800.0 if uiscale is bui.UIScale.SMALL else 350.0

        show_soundtracks = False
        if music.have_music_player():
            show_soundtracks = True

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.2
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(width - 60, screensize[0] / scale)
        target_height = min(height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                scale=scale,
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(35, yoffs - 55),
                size=(60, 60),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
                autoselect=True,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                width * 0.5,
                yoffs - (48 if uiscale is bui.UIScale.SMALL else 32),
            ),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            maxwidth=180,
            h_align='center',
            v_align='center',
        )

        # Roughly center everything else in our window.
        x = width * 0.5 - 160
        y = height * 0.5 + (100 if show_soundtracks else 70)
        y -= spacing * 1.0

        self._sound_volume_numedit = svne = ConfigNumberEdit(
            parent=self._root_widget,
            position=(x, y),
            xoffset=10,
            configkey='Sound Volume',
            displayname=bui.Lstr(resource=f'{self._r}.soundVolumeText'),
            minval=0.0,
            maxval=1.0,
            increment=0.05,
            as_percent=True,
        )
        bui.widget(
            edit=svne.plusbutton,
            right_widget=bui.get_special_widget('squad_button'),
        )
        y -= spacing
        self._music_volume_numedit = ConfigNumberEdit(
            parent=self._root_widget,
            position=(x, y),
            xoffset=10,
            configkey='Music Volume',
            displayname=bui.Lstr(resource=f'{self._r}.musicVolumeText'),
            minval=0.0,
            maxval=1.0,
            increment=0.05,
            callback=music.music_volume_changed,
            changesound=False,
            as_percent=True,
        )

        y -= 0.5 * spacing

        self._soundtrack_button: bui.Widget | None
        if show_soundtracks:
            y -= 1.2 * spacing
            self._soundtrack_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(width * 0.5 - 155, y),
                size=(310, 50),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.soundtrackButtonText'),
                on_activate_call=self._do_soundtracks,
            )
            y -= spacing * 0.3
            bui.textwidget(
                parent=self._root_widget,
                position=(0.5 * width, y),
                size=(0.0, 0.0),
                text=bui.Lstr(resource=f'{self._r}.soundtrackDescriptionText'),
                flatness=1.0,
                h_align='center',
                v_align='center',
                maxwidth=400,
                scale=0.5,
                color=(0.7, 0.8, 0.7, 1.0),
            )
        else:
            self._soundtrack_button = None

        # Tweak a few navigation bits.
        if self._back_button is not None:
            bui.widget(edit=self._back_button, down_widget=svne.minusbutton)
        else:
            spback = bui.get_special_widget('back_button')
            bui.widget(
                edit=svne.minusbutton, up_widget=spback, left_widget=spback
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

    def _do_soundtracks(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.soundtrack.browser import SoundtrackBrowserWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        # We require disk access for soundtracks; request it if we don't
        # have it.
        if not bui.have_permission(bui.Permission.STORAGE):
            bui.getsound('ding').play()
            bui.screenmessage(
                bui.Lstr(resource='storagePermissionAccessText'),
                color=(0.5, 1, 0.5),
            )
            bui.apptimer(
                1.0, bui.Call(bui.request_permission, bui.Permission.STORAGE)
            )
            return

        self.main_window_replace(
            SoundtrackBrowserWindow(origin_widget=self._soundtrack_button)
        )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._sound_volume_numedit.minusbutton:
                sel_name = 'SoundMinus'
            elif sel == self._sound_volume_numedit.plusbutton:
                sel_name = 'SoundPlus'
            elif sel == self._music_volume_numedit.minusbutton:
                sel_name = 'MusicMinus'
            elif sel == self._music_volume_numedit.plusbutton:
                sel_name = 'MusicPlus'
            elif sel == self._soundtrack_button:
                sel_name = 'Soundtrack'
            elif sel == self._back_button:
                sel_name = 'Back'
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
            if sel_name == 'SoundMinus':
                sel = self._sound_volume_numedit.minusbutton
            elif sel_name == 'SoundPlus':
                sel = self._sound_volume_numedit.plusbutton
            elif sel_name == 'MusicMinus':
                sel = self._music_volume_numedit.minusbutton
            elif sel_name == 'MusicPlus':
                sel = self._music_volume_numedit.plusbutton
            elif sel_name == 'Soundtrack':
                sel = self._soundtrack_button
            elif sel_name == 'Back':
                sel = self._back_button
            else:
                sel = self._back_button
            if sel:
                bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)
