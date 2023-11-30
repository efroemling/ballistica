# Released under the MIT License. See LICENSE for details.
#
"""Provides audio settings UI."""

from __future__ import annotations

from typing import TYPE_CHECKING
import logging

import bauiv1 as bui

if TYPE_CHECKING:
    pass


class AudioSettingsWindow(bui.Window):
    """Window for editing audio settings."""

    def __init__(
        self,
        transition: str = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bauiv1lib.popup import PopupMenu
        from bauiv1lib.config import ConfigNumberEdit

        assert bui.app.classic is not None
        music = bui.app.classic.music

        # If they provided an origin-widget, scale up from that.
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._r = 'audioSettingsWindow'

        spacing = 50.0
        width = 460.0
        height = 210.0

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

        uiscale = bui.app.ui_v1.uiscale
        base_scale = (
            2.05
            if uiscale is bui.UIScale.SMALL
            else 1.6
            if uiscale is bui.UIScale.MEDIUM
            else 1.0
        )
        popup_menu_scale = base_scale * 1.2

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition=transition,
                scale=base_scale,
                scale_origin_stack_offset=scale_origin,
                stack_offset=(0, -20)
                if uiscale is bui.UIScale.SMALL
                else (0, 0),
            )
        )

        self._back_button = back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, height - 55),
            size=(120, 60),
            scale=0.8,
            text_scale=1.2,
            label=bui.Lstr(resource='backText'),
            button_type='back',
            on_activate_call=self._back,
            autoselect=True,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        v = height - 60
        v -= spacing * 1.0
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, height - 32),
            size=(0, 0),
            text=bui.Lstr(resource=self._r + '.titleText'),
            color=bui.app.ui_v1.title_color,
            maxwidth=180,
            h_align='center',
            v_align='center',
        )

        bui.buttonwidget(
            edit=self._back_button,
            button_type='backSmall',
            size=(60, 60),
            label=bui.charstr(bui.SpecialChar.BACK),
        )

        self._sound_volume_numedit = svne = ConfigNumberEdit(
            parent=self._root_widget,
            position=(40, v),
            xoffset=10,
            configkey='Sound Volume',
            displayname=bui.Lstr(resource=self._r + '.soundVolumeText'),
            minval=0.0,
            maxval=1.0,
            increment=0.05,
            as_percent=True,
        )
        if bui.app.ui_v1.use_toolbars:
            bui.widget(
                edit=svne.plusbutton,
                right_widget=bui.get_special_widget('party_button'),
            )
        v -= spacing
        self._music_volume_numedit = ConfigNumberEdit(
            parent=self._root_widget,
            position=(40, v),
            xoffset=10,
            configkey='Music Volume',
            displayname=bui.Lstr(resource=self._r + '.musicVolumeText'),
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
                text=bui.Lstr(resource=self._r + '.headRelativeVRAudioText'),
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
                    resource=self._r + '.headRelativeVRAudioInfoText'
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
                label=bui.Lstr(resource=self._r + '.soundtrackButtonText'),
                on_activate_call=self._do_soundtracks,
            )
            v -= spacing * 0.5
            bui.textwidget(
                parent=self._root_widget,
                position=(0, v),
                size=(width, 20),
                text=bui.Lstr(resource=self._r + '.soundtrackDescriptionText'),
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

    def _set_vr_head_relative_audio(self, val: str) -> None:
        cfg = bui.app.config
        cfg['VR Head Relative Audio'] = val
        cfg.apply_and_commit()

    def _do_soundtracks(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.soundtrack import browser as stb

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        # We require disk access for soundtracks;
        # if we don't have it, request it.
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

        self._save_state()
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            stb.SoundtrackBrowserWindow(
                origin_widget=self._soundtrack_button
            ).get_root_widget(),
            from_window=self._root_widget,
        )

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings import allsettings

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self._save_state()
        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            allsettings.AllSettingsWindow(
                transition='in_left'
            ).get_root_widget(),
            from_window=self._root_widget,
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
