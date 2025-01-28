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
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bauiv1lib.popup import PopupMenu
        from bauiv1lib.config import ConfigNumberEdit

        assert bui.app.classic is not None
        music = bui.app.classic.music

        self._r = 'audioSettingsWindow'

        spacing = 50.0
        width = 460.0
        height = 240.0
        uiscale = bui.app.ui_v1.uiscale

        yoffs = -5.0

        # Update: hard-coding head-relative audio to true now,
        # so not showing options.
        # show_vr_head_relative_audio = True if bui.app.vr_mode else False
        show_vr_head_relative_audio = False

        if show_vr_head_relative_audio:
            height += 70

        show_soundtracks = False
        if music.have_music_player():
            show_soundtracks = True
            height += spacing * 2.0

        base_scale = (
            1.9
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        popup_menu_scale = base_scale * 1.2

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                scale=base_scale,
                toolbar_visibility=(
                    None if uiscale is bui.UIScale.SMALL else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        self._back_button = back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, height + yoffs - 55),
            size=(60, 60),
            scale=0.8,
            text_scale=1.2,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.main_window_back,
            autoselect=True,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, height + yoffs - 32),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            maxwidth=180,
            h_align='center',
            v_align='center',
        )

        v = height + yoffs - 60
        v -= spacing * 1.0

        self._sound_volume_numedit = svne = ConfigNumberEdit(
            parent=self._root_widget,
            position=(40, v),
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
        v -= spacing
        self._music_volume_numedit = ConfigNumberEdit(
            parent=self._root_widget,
            position=(40, v),
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

        v -= 0.5 * spacing

        self._vr_head_relative_audio_button: bui.Widget | None
        if show_vr_head_relative_audio:
            v -= 40
            bui.textwidget(
                parent=self._root_widget,
                position=(40, v + 24),
                size=(0, 0),
                text=bui.Lstr(resource=f'{self._r}.headRelativeVRAudioText'),
                color=(0.8, 0.8, 0.8),
                maxwidth=230,
                h_align='left',
                v_align='center',
            )

            popup = PopupMenu(
                parent=self._root_widget,
                position=(290, v),
                width=120,
                button_size=(135, 50),
                scale=popup_menu_scale,
                choices=['Auto', 'On', 'Off'],
                choices_display=[
                    bui.Lstr(resource='autoText'),
                    bui.Lstr(resource='onText'),
                    bui.Lstr(resource='offText'),
                ],
                current_choice=bui.app.config.resolve('VR Head Relative Audio'),
                on_value_change_call=self._set_vr_head_relative_audio,
            )
            self._vr_head_relative_audio_button = popup.get_button()
            bui.textwidget(
                parent=self._root_widget,
                position=(width * 0.5, v - 11),
                size=(0, 0),
                text=bui.Lstr(
                    resource=f'{self._r}.headRelativeVRAudioInfoText'
                ),
                scale=0.5,
                color=(0.7, 0.8, 0.7),
                maxwidth=400,
                flatness=1.0,
                h_align='center',
                v_align='center',
            )
            v -= 30
        else:
            self._vr_head_relative_audio_button = None

        self._soundtrack_button: bui.Widget | None
        if show_soundtracks:
            v -= 1.2 * spacing
            self._soundtrack_button = bui.buttonwidget(
                parent=self._root_widget,
                position=((width - 310) / 2, v),
                size=(310, 50),
                autoselect=True,
                label=bui.Lstr(resource=f'{self._r}.soundtrackButtonText'),
                on_activate_call=self._do_soundtracks,
            )
            v -= spacing * 0.5
            bui.textwidget(
                parent=self._root_widget,
                position=(0, v),
                size=(width, 20),
                text=bui.Lstr(resource=f'{self._r}.soundtrackDescriptionText'),
                flatness=1.0,
                h_align='center',
                scale=0.5,
                color=(0.7, 0.8, 0.7, 1.0),
                maxwidth=400,
            )
        else:
            self._soundtrack_button = None

        # Tweak a few navigation bits.
        try:
            bui.widget(edit=back_button, down_widget=svne.minusbutton)
        except Exception:
            logging.exception('Error wiring AudioSettingsWindow.')

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

    def _set_vr_head_relative_audio(self, val: str) -> None:
        cfg = bui.app.config
        cfg['VR Head Relative Audio'] = val
        cfg.apply_and_commit()

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
            elif sel == self._vr_head_relative_audio_button:
                sel_name = 'VRHeadRelative'
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
            elif sel_name == 'VRHeadRelative':
                sel = self._vr_head_relative_audio_button
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
