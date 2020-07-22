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
"""Provides UI for editing a soundtrack."""

from __future__ import annotations

import copy
import os
from typing import TYPE_CHECKING, cast

import ba

if TYPE_CHECKING:
    from typing import Any, Dict, Union, Optional


class SoundtrackEditWindow(ba.Window):
    """Window for editing a soundtrack."""

    def __init__(self,
                 existing_soundtrack: Optional[Union[str, Dict[str, Any]]],
                 transition: str = 'in_right'):
        # pylint: disable=too-many-statements
        appconfig = ba.app.config
        self._r = 'editSoundtrackWindow'
        self._folder_tex = ba.gettexture('folder')
        self._file_tex = ba.gettexture('file')
        uiscale = ba.app.ui.uiscale
        self._width = 848 if uiscale is ba.UIScale.SMALL else 648
        x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (395 if uiscale is ba.UIScale.SMALL else
                        450 if uiscale is ba.UIScale.MEDIUM else 560)
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition=transition,
            scale=(2.08 if uiscale is ba.UIScale.SMALL else
                   1.5 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -48) if uiscale is ba.UIScale.SMALL else (
                0, 15) if uiscale is ba.UIScale.MEDIUM else (0, 0)))
        cancel_button = ba.buttonwidget(parent=self._root_widget,
                                        position=(38 + x_inset,
                                                  self._height - 60),
                                        size=(160, 60),
                                        autoselect=True,
                                        label=ba.Lstr(resource='cancelText'),
                                        scale=0.8)
        save_button = ba.buttonwidget(parent=self._root_widget,
                                      position=(self._width - (168 + x_inset),
                                                self._height - 60),
                                      autoselect=True,
                                      size=(160, 60),
                                      label=ba.Lstr(resource='saveText'),
                                      scale=0.8)
        ba.widget(edit=save_button, left_widget=cancel_button)
        ba.widget(edit=cancel_button, right_widget=save_button)
        ba.textwidget(
            parent=self._root_widget,
            position=(0, self._height - 50),
            size=(self._width, 25),
            text=ba.Lstr(resource=self._r +
                         ('.editSoundtrackText' if existing_soundtrack
                          is not None else '.newSoundtrackText')),
            color=ba.app.ui.title_color,
            h_align='center',
            v_align='center',
            maxwidth=280)
        v = self._height - 110
        if 'Soundtracks' not in appconfig:
            appconfig['Soundtracks'] = {}

        self._soundtrack_name: Optional[str]
        self._existing_soundtrack_name: Optional[str]
        if existing_soundtrack is not None:
            # if they passed just a name, pull info from that soundtrack
            if isinstance(existing_soundtrack, str):
                self._soundtrack = copy.deepcopy(
                    appconfig['Soundtracks'][existing_soundtrack])
                self._soundtrack_name = existing_soundtrack
                self._existing_soundtrack_name = existing_soundtrack
                self._last_edited_song_type = None
            else:
                # otherwise they can pass info on an in-progress edit
                self._soundtrack = existing_soundtrack['soundtrack']
                self._soundtrack_name = existing_soundtrack['name']
                self._existing_soundtrack_name = (
                    existing_soundtrack['existing_name'])
                self._last_edited_song_type = (
                    existing_soundtrack['last_edited_song_type'])
        else:
            self._soundtrack_name = None
            self._existing_soundtrack_name = None
            self._soundtrack = {}
            self._last_edited_song_type = None

        ba.textwidget(parent=self._root_widget,
                      text=ba.Lstr(resource=self._r + '.nameText'),
                      maxwidth=80,
                      scale=0.8,
                      position=(105 + x_inset, v + 19),
                      color=(0.8, 0.8, 0.8, 0.5),
                      size=(0, 0),
                      h_align='right',
                      v_align='center')

        # if there's no initial value, find a good initial unused name
        if existing_soundtrack is None:
            i = 1
            st_name_text = ba.Lstr(resource=self._r +
                                   '.newSoundtrackNameText').evaluate()
            if '${COUNT}' not in st_name_text:
                # make sure we insert number *somewhere*
                st_name_text = st_name_text + ' ${COUNT}'
            while True:
                self._soundtrack_name = st_name_text.replace(
                    '${COUNT}', str(i))
                if self._soundtrack_name not in appconfig['Soundtracks']:
                    break
                i += 1

        self._text_field = ba.textwidget(
            parent=self._root_widget,
            position=(120 + x_inset, v - 5),
            size=(self._width - (160 + 2 * x_inset), 43),
            text=self._soundtrack_name,
            h_align='left',
            v_align='center',
            max_chars=32,
            autoselect=True,
            description=ba.Lstr(resource=self._r + '.nameText'),
            editable=True,
            padding=4,
            on_return_press_call=self._do_it_with_sound)

        scroll_height = self._height - 180
        self._scrollwidget = scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=(40 + x_inset, v - (scroll_height + 10)),
            size=(self._width - (80 + 2 * x_inset), scroll_height),
            simple_culling_v=10,
            claims_left_right=True,
            claims_tab=True,
            selection_loops_to_parent=True)
        ba.widget(edit=self._text_field, down_widget=self._scrollwidget)
        self._col = ba.columnwidget(parent=scrollwidget,
                                    claims_left_right=True,
                                    claims_tab=True,
                                    selection_loops_to_parent=True)

        self._song_type_buttons: Dict[str, ba.Widget] = {}
        self._refresh()
        ba.buttonwidget(edit=cancel_button, on_activate_call=self._cancel)
        ba.containerwidget(edit=self._root_widget, cancel_button=cancel_button)
        ba.buttonwidget(edit=save_button, on_activate_call=self._do_it)
        ba.containerwidget(edit=self._root_widget, start_button=save_button)
        ba.widget(edit=self._text_field, up_widget=cancel_button)
        ba.widget(edit=cancel_button, down_widget=self._text_field)

    def _refresh(self) -> None:
        from ba.deprecated import get_resource
        for widget in self._col.get_children():
            widget.delete()

        types = [
            'Menu',
            'CharSelect',
            'ToTheDeath',
            'Onslaught',
            'Keep Away',
            'Race',
            'Epic Race',
            'ForwardMarch',
            'FlagCatcher',
            'Survival',
            'Epic',
            'Hockey',
            'Football',
            'Flying',
            'Scary',
            'Marching',
            'GrandRomp',
            'Chosen One',
            'Scores',
            'Victory',
        ]
        # FIXME: We should probably convert this to use translations.
        type_names_translated = get_resource('soundtrackTypeNames')
        prev_type_button: Optional[ba.Widget] = None
        prev_test_button: Optional[ba.Widget] = None

        for index, song_type in enumerate(types):
            row = ba.rowwidget(parent=self._col,
                               size=(self._width - 40, 40),
                               claims_left_right=True,
                               claims_tab=True,
                               selection_loops_to_parent=True)
            type_name = type_names_translated.get(song_type, song_type)
            ba.textwidget(parent=row,
                          size=(230, 25),
                          always_highlight=True,
                          text=type_name,
                          scale=0.7,
                          h_align='left',
                          v_align='center',
                          maxwidth=190)

            if song_type in self._soundtrack:
                entry = self._soundtrack[song_type]
            else:
                entry = None

            if entry is not None:
                # Make sure they don't muck with this after it gets to us.
                entry = copy.deepcopy(entry)

            icon_type = self._get_entry_button_display_icon_type(entry)
            self._song_type_buttons[song_type] = btn = ba.buttonwidget(
                parent=row,
                size=(230, 32),
                label=self._get_entry_button_display_name(entry),
                text_scale=0.6,
                on_activate_call=ba.Call(self._get_entry, song_type, entry,
                                         type_name),
                icon=(self._file_tex if icon_type == 'file' else
                      self._folder_tex if icon_type == 'folder' else None),
                icon_color=(1.1, 0.8, 0.2) if icon_type == 'folder' else
                (1, 1, 1),
                left_widget=self._text_field,
                iconscale=0.7,
                autoselect=True,
                up_widget=prev_type_button)
            if index == 0:
                ba.widget(edit=btn, up_widget=self._text_field)
            ba.widget(edit=btn, down_widget=btn)

            if (self._last_edited_song_type is not None
                    and song_type == self._last_edited_song_type):
                ba.containerwidget(edit=row,
                                   selected_child=btn,
                                   visible_child=btn)
                ba.containerwidget(edit=self._col,
                                   selected_child=row,
                                   visible_child=row)
                ba.containerwidget(edit=self._scrollwidget,
                                   selected_child=self._col,
                                   visible_child=self._col)
                ba.containerwidget(edit=self._root_widget,
                                   selected_child=self._scrollwidget,
                                   visible_child=self._scrollwidget)

            if prev_type_button is not None:
                ba.widget(edit=prev_type_button, down_widget=btn)
            prev_type_button = btn
            ba.textwidget(parent=row, size=(10, 32), text='')  # spacing
            btn = ba.buttonwidget(
                parent=row,
                size=(50, 32),
                label=ba.Lstr(resource=self._r + '.testText'),
                text_scale=0.6,
                on_activate_call=ba.Call(self._test, ba.MusicType(song_type)),
                up_widget=prev_test_button
                if prev_test_button is not None else self._text_field)
            if prev_test_button is not None:
                ba.widget(edit=prev_test_button, down_widget=btn)
            ba.widget(edit=btn, down_widget=btn, right_widget=btn)
            prev_test_button = btn

    @classmethod
    def _restore_editor(cls, state: Dict[str, Any], musictype: str,
                        entry: Any) -> None:
        music = ba.app.music

        # Apply the change and recreate the window.
        soundtrack = state['soundtrack']
        existing_entry = (None if musictype not in soundtrack else
                          soundtrack[musictype])
        if existing_entry != entry:
            ba.playsound(ba.getsound('gunCocking'))

        # Make sure this doesn't get mucked with after we get it.
        if entry is not None:
            entry = copy.deepcopy(entry)

        entry_type = music.get_soundtrack_entry_type(entry)
        if entry_type == 'default':
            # For 'default' entries simply exclude them from the list.
            if musictype in soundtrack:
                del soundtrack[musictype]
        else:
            soundtrack[musictype] = entry

        ba.app.ui.set_main_menu_window(
            cls(state, transition='in_left').get_root_widget())

    def _get_entry(self, song_type: str, entry: Any,
                   selection_target_name: str) -> None:
        music = ba.app.music
        if selection_target_name != '':
            selection_target_name = "'" + selection_target_name + "'"
        state = {
            'name': self._soundtrack_name,
            'existing_name': self._existing_soundtrack_name,
            'soundtrack': self._soundtrack,
            'last_edited_song_type': song_type
        }
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(music.get_music_player().select_entry(
            ba.Call(self._restore_editor, state, song_type), entry,
            selection_target_name).get_root_widget())

    def _test(self, song_type: ba.MusicType) -> None:
        music = ba.app.music

        # Warn if volume is zero.
        if ba.app.config.resolve('Music Volume') < 0.01:
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource=self._r +
                                     '.musicVolumeZeroWarning'),
                             color=(1, 0.5, 0))
        music.set_music_play_mode(ba.MusicPlayMode.TEST)
        music.do_play_music(song_type,
                            mode=ba.MusicPlayMode.TEST,
                            testsoundtrack=self._soundtrack)

    def _get_entry_button_display_name(self,
                                       entry: Any) -> Union[str, ba.Lstr]:
        music = ba.app.music
        etype = music.get_soundtrack_entry_type(entry)
        ename: Union[str, ba.Lstr]
        if etype == 'default':
            ename = ba.Lstr(resource=self._r + '.defaultGameMusicText')
        elif etype in ('musicFile', 'musicFolder'):
            ename = os.path.basename(music.get_soundtrack_entry_name(entry))
        else:
            ename = music.get_soundtrack_entry_name(entry)
        return ename

    def _get_entry_button_display_icon_type(self, entry: Any) -> Optional[str]:
        music = ba.app.music
        etype = music.get_soundtrack_entry_type(entry)
        if etype == 'musicFile':
            return 'file'
        if etype == 'musicFolder':
            return 'folder'
        return None

    def _cancel(self) -> None:
        from bastd.ui.soundtrack import browser as stb
        music = ba.app.music

        # Resets music back to normal.
        music.set_music_play_mode(ba.MusicPlayMode.REGULAR)
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            stb.SoundtrackBrowserWindow(
                transition='in_left').get_root_widget())

    def _do_it(self) -> None:
        from bastd.ui.soundtrack import browser as stb
        music = ba.app.music
        cfg = ba.app.config
        new_name = cast(str, ba.textwidget(query=self._text_field))
        if (new_name != self._soundtrack_name
                and new_name in cfg['Soundtracks']):
            ba.screenmessage(
                ba.Lstr(resource=self._r + '.cantSaveAlreadyExistsText'))
            ba.playsound(ba.getsound('error'))
            return
        if not new_name:
            ba.playsound(ba.getsound('error'))
            return
        if new_name == ba.Lstr(resource=self._r +
                               '.defaultSoundtrackNameText').evaluate():
            ba.screenmessage(
                ba.Lstr(resource=self._r + '.cantOverwriteDefaultText'))
            ba.playsound(ba.getsound('error'))
            return

        # Make sure config exists.
        if 'Soundtracks' not in cfg:
            cfg['Soundtracks'] = {}

        # If we had an old one, delete it.
        if (self._existing_soundtrack_name is not None
                and self._existing_soundtrack_name in cfg['Soundtracks']):
            del cfg['Soundtracks'][self._existing_soundtrack_name]
        cfg['Soundtracks'][new_name] = self._soundtrack
        cfg['Soundtrack'] = new_name

        cfg.commit()
        ba.playsound(ba.getsound('gunCocking'))
        ba.containerwidget(edit=self._root_widget, transition='out_right')

        # Resets music back to normal.
        music.set_music_play_mode(ba.MusicPlayMode.REGULAR, force_restart=True)

        ba.app.ui.set_main_menu_window(
            stb.SoundtrackBrowserWindow(
                transition='in_left').get_root_widget())

    def _do_it_with_sound(self) -> None:
        ba.playsound(ba.getsound('swish'))
        self._do_it()
