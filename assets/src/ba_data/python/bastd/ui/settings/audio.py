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
"""Provides audio settings UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Tuple, Optional


class AudioSettingsWindow(ba.Window):
    """Window for editing audio settings."""

    def __init__(self,
                 transition: str = 'in_right',
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import
        from bastd.ui.popup import PopupMenu
        from bastd.ui.config import ConfigNumberEdit

        music = ba.app.music

        # If they provided an origin-widget, scale up from that.
        scale_origin: Optional[Tuple[float, float]]
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
        # show_vr_head_relative_audio = True if ba.app.vr_mode else False
        show_vr_head_relative_audio = False

        if show_vr_head_relative_audio:
            height += 70

        show_soundtracks = False
        if music.have_music_player():
            show_soundtracks = True
            height += spacing * 2.0

        uiscale = ba.app.ui.uiscale
        base_scale = (2.05 if uiscale is ba.UIScale.SMALL else
                      1.6 if uiscale is ba.UIScale.MEDIUM else 1.0)
        popup_menu_scale = base_scale * 1.2

        super().__init__(root_widget=ba.containerwidget(
            size=(width, height),
            transition=transition,
            scale=base_scale,
            scale_origin_stack_offset=scale_origin,
            stack_offset=(0, -20) if uiscale is ba.UIScale.SMALL else (0, 0)))

        self._back_button = back_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(35, height - 55),
            size=(120, 60),
            scale=0.8,
            text_scale=1.2,
            label=ba.Lstr(resource='backText'),
            button_type='back',
            on_activate_call=self._back,
            autoselect=True)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        v = height - 60
        v -= spacing * 1.0
        ba.textwidget(parent=self._root_widget,
                      position=(width * 0.5, height - 32),
                      size=(0, 0),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      color=ba.app.ui.title_color,
                      maxwidth=180,
                      h_align='center',
                      v_align='center')

        ba.buttonwidget(edit=self._back_button,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        self._sound_volume_numedit = svne = ConfigNumberEdit(
            parent=self._root_widget,
            position=(40, v),
            xoffset=10,
            configkey='Sound Volume',
            displayname=ba.Lstr(resource=self._r + '.soundVolumeText'),
            minval=0.0,
            maxval=1.0,
            increment=0.1)
        if ba.app.ui.use_toolbars:
            ba.widget(edit=svne.plusbutton,
                      right_widget=_ba.get_special_widget('party_button'))
        v -= spacing
        self._music_volume_numedit = ConfigNumberEdit(
            parent=self._root_widget,
            position=(40, v),
            xoffset=10,
            configkey='Music Volume',
            displayname=ba.Lstr(resource=self._r + '.musicVolumeText'),
            minval=0.0,
            maxval=1.0,
            increment=0.1,
            callback=music.music_volume_changed,
            changesound=False)

        v -= 0.5 * spacing

        self._vr_head_relative_audio_button: Optional[ba.Widget]
        if show_vr_head_relative_audio:
            v -= 40
            ba.textwidget(parent=self._root_widget,
                          position=(40, v + 24),
                          size=(0, 0),
                          text=ba.Lstr(resource=self._r +
                                       '.headRelativeVRAudioText'),
                          color=(0.8, 0.8, 0.8),
                          maxwidth=230,
                          h_align='left',
                          v_align='center')

            popup = PopupMenu(
                parent=self._root_widget,
                position=(290, v),
                width=120,
                button_size=(135, 50),
                scale=popup_menu_scale,
                choices=['Auto', 'On', 'Off'],
                choices_display=[
                    ba.Lstr(resource='autoText'),
                    ba.Lstr(resource='onText'),
                    ba.Lstr(resource='offText')
                ],
                current_choice=ba.app.config.resolve('VR Head Relative Audio'),
                on_value_change_call=self._set_vr_head_relative_audio)
            self._vr_head_relative_audio_button = popup.get_button()
            ba.textwidget(parent=self._root_widget,
                          position=(width * 0.5, v - 11),
                          size=(0, 0),
                          text=ba.Lstr(resource=self._r +
                                       '.headRelativeVRAudioInfoText'),
                          scale=0.5,
                          color=(0.7, 0.8, 0.7),
                          maxwidth=400,
                          flatness=1.0,
                          h_align='center',
                          v_align='center')
            v -= 30
        else:
            self._vr_head_relative_audio_button = None

        self._soundtrack_button: Optional[ba.Widget]
        if show_soundtracks:
            v -= 1.2 * spacing
            self._soundtrack_button = ba.buttonwidget(
                parent=self._root_widget,
                position=((width - 310) / 2, v),
                size=(310, 50),
                autoselect=True,
                label=ba.Lstr(resource=self._r + '.soundtrackButtonText'),
                on_activate_call=self._do_soundtracks)
            v -= spacing * 0.5
            ba.textwidget(parent=self._root_widget,
                          position=(0, v),
                          size=(width, 20),
                          text=ba.Lstr(resource=self._r +
                                       '.soundtrackDescriptionText'),
                          flatness=1.0,
                          h_align='center',
                          scale=0.5,
                          color=(0.7, 0.8, 0.7, 1.0),
                          maxwidth=400)
        else:
            self._soundtrack_button = None

        # Tweak a few navigation bits.
        try:
            ba.widget(edit=back_button, down_widget=svne.minusbutton)
        except Exception:
            ba.print_exception('Error wiring AudioSettingsWindow.')

        self._restore_state()

    def _set_vr_head_relative_audio(self, val: str) -> None:
        cfg = ba.app.config
        cfg['VR Head Relative Audio'] = val
        cfg.apply_and_commit()

    def _do_soundtracks(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.soundtrack import browser as stb

        # We require disk access for soundtracks;
        # if we don't have it, request it.
        if not _ba.have_permission(ba.Permission.STORAGE):
            ba.playsound(ba.getsound('ding'))
            ba.screenmessage(ba.Lstr(resource='storagePermissionAccessText'),
                             color=(0.5, 1, 0.5))
            ba.timer(1.0,
                     ba.Call(_ba.request_permission, ba.Permission.STORAGE),
                     timetype=ba.TimeType.REAL)
            return

        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            stb.SoundtrackBrowserWindow(
                origin_widget=self._soundtrack_button).get_root_widget())

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings import allsettings
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            allsettings.AllSettingsWindow(
                transition='in_left').get_root_widget())

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
            ba.app.ui.window_states[self.__class__.__name__] = sel_name
        except Exception:
            ba.print_exception(f'Error saving state for {self.__class__}.')

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(self.__class__.__name__)
            sel: Optional[ba.Widget]
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
                ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self.__class__}.')
