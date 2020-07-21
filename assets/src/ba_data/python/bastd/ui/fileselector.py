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
"""UI functionality for selecting files."""

from __future__ import annotations

import os
import threading
import time
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence, List, Optional


class FileSelectorWindow(ba.Window):
    """Window for selecting files."""

    def __init__(self,
                 path: str,
                 callback: Callable[[Optional[str]], Any] = None,
                 show_base_path: bool = True,
                 valid_file_extensions: Sequence[str] = None,
                 allow_folders: bool = False):
        if valid_file_extensions is None:
            valid_file_extensions = []
        uiscale = ba.app.ui.uiscale
        self._width = 700 if uiscale is ba.UIScale.SMALL else 600
        self._x_inset = x_inset = 50 if uiscale is ba.UIScale.SMALL else 0
        self._height = 365 if uiscale is ba.UIScale.SMALL else 418
        self._callback = callback
        self._base_path = path
        self._path: Optional[str] = None
        self._recent_paths: List[str] = []
        self._show_base_path = show_base_path
        self._valid_file_extensions = [
            '.' + ext for ext in valid_file_extensions
        ]
        self._allow_folders = allow_folders
        self._subcontainer: Optional[ba.Widget] = None
        self._subcontainerheight: Optional[float] = None
        self._scroll_width = self._width - (80 + 2 * x_inset)
        self._scroll_height = self._height - 170
        self._r = 'fileSelectorWindow'
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition='in_right',
            scale=(2.23 if uiscale is ba.UIScale.SMALL else
                   1.4 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -35) if uiscale is ba.UIScale.SMALL else (0, 0)))
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 42),
            size=(0, 0),
            color=ba.app.ui.title_color,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource=self._r + '.titleFolderText') if
            (allow_folders and not valid_file_extensions) else ba.Lstr(
                resource=self._r +
                '.titleFileText') if not allow_folders else ba.Lstr(
                    resource=self._r + '.titleFileFolderText'),
            maxwidth=210)

        self._button_width = 146
        self._cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(35 + x_inset, self._height - 67),
            autoselect=True,
            size=(self._button_width, 50),
            label=ba.Lstr(resource='cancelText'),
            on_activate_call=self._cancel)
        ba.widget(edit=self._cancel_button, left_widget=self._cancel_button)

        b_color = (0.6, 0.53, 0.63)

        self._back_button = ba.buttonwidget(
            parent=self._root_widget,
            button_type='square',
            position=(43 + x_inset, self._height - 113),
            color=b_color,
            textcolor=(0.75, 0.7, 0.8),
            enable_sound=False,
            size=(55, 35),
            label=ba.charstr(ba.SpecialChar.LEFT_ARROW),
            on_activate_call=self._on_back_press)

        self._folder_tex = ba.gettexture('folder')
        self._folder_color = (1.1, 0.8, 0.2)
        self._file_tex = ba.gettexture('file')
        self._file_color = (1, 1, 1)
        self._use_folder_button: Optional[ba.Widget] = None
        self._folder_center = self._width * 0.5 + 15
        self._folder_icon = ba.imagewidget(parent=self._root_widget,
                                           size=(40, 40),
                                           position=(40, self._height - 117),
                                           texture=self._folder_tex,
                                           color=self._folder_color)
        self._path_text = ba.textwidget(parent=self._root_widget,
                                        position=(self._folder_center,
                                                  self._height - 98),
                                        size=(0, 0),
                                        color=ba.app.ui.title_color,
                                        h_align='center',
                                        v_align='center',
                                        text=self._path,
                                        maxwidth=self._width * 0.9)
        self._scrollwidget: Optional[ba.Widget] = None
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button)
        self._set_path(path)

    def _on_up_press(self) -> None:
        self._on_entry_activated('..')

    def _on_back_press(self) -> None:
        if len(self._recent_paths) > 1:
            ba.playsound(ba.getsound('swish'))
            self._recent_paths.pop()
            self._set_path(self._recent_paths.pop())
        else:
            ba.playsound(ba.getsound('error'))

    def _on_folder_entry_activated(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        if self._callback is not None:
            assert self._path is not None
            self._callback(self._path)

    def _on_entry_activated(self, entry: str) -> None:
        # pylint: disable=too-many-branches
        new_path = None
        try:
            assert self._path is not None
            if entry == '..':
                chunks = self._path.split('/')
                if len(chunks) > 1:
                    new_path = '/'.join(chunks[:-1])
                    if new_path == '':
                        new_path = '/'
                else:
                    ba.playsound(ba.getsound('error'))
            else:
                if self._path == '/':
                    test_path = self._path + entry
                else:
                    test_path = self._path + '/' + entry
                if os.path.isdir(test_path):
                    ba.playsound(ba.getsound('swish'))
                    new_path = test_path
                elif os.path.isfile(test_path):
                    if self._is_valid_file_path(test_path):
                        ba.playsound(ba.getsound('swish'))
                        ba.containerwidget(edit=self._root_widget,
                                           transition='out_right')
                        if self._callback is not None:
                            self._callback(test_path)
                    else:
                        ba.playsound(ba.getsound('error'))
                else:
                    print(('Error: FileSelectorWindow found non-file/dir:',
                           test_path))
        except Exception:
            ba.print_exception(
                'Error in FileSelectorWindow._on_entry_activated().')

        if new_path is not None:
            self._set_path(new_path)

    class _RefreshThread(threading.Thread):

        def __init__(self, path: str,
                     callback: Callable[[List[str], Optional[str]], Any]):
            super().__init__()
            self._callback = callback
            self._path = path

        def run(self) -> None:
            try:
                starttime = time.time()
                files = os.listdir(self._path)
                duration = time.time() - starttime
                min_time = 0.1

                # Make sure this takes at least 1/10 second so the user
                # has time to see the selection highlight.
                if duration < min_time:
                    time.sleep(min_time - duration)
                ba.pushcall(ba.Call(self._callback, files, None),
                            from_other_thread=True)
            except Exception as exc:
                # Ignore permission-denied.
                if 'Errno 13' not in str(exc):
                    ba.print_exception()
                nofiles: List[str] = []
                ba.pushcall(ba.Call(self._callback, nofiles, str(exc)),
                            from_other_thread=True)

    def _set_path(self, path: str, add_to_recent: bool = True) -> None:
        self._path = path
        if add_to_recent:
            self._recent_paths.append(path)
        self._RefreshThread(path, self._refresh).start()

    def _refresh(self, file_names: List[str], error: Optional[str]) -> None:
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        if not self._root_widget:
            return

        scrollwidget_selected = (self._scrollwidget is None
                                 or self._root_widget.get_selected_child()
                                 == self._scrollwidget)

        in_top_folder = (self._path == self._base_path)
        hide_top_folder = in_top_folder and self._show_base_path is False

        if hide_top_folder:
            folder_name = ''
        elif self._path == '/':
            folder_name = '/'
        else:
            assert self._path is not None
            folder_name = os.path.basename(self._path)

        b_color = (0.6, 0.53, 0.63)
        b_color_disabled = (0.65, 0.65, 0.65)

        if len(self._recent_paths) < 2:
            ba.buttonwidget(edit=self._back_button,
                            color=b_color_disabled,
                            textcolor=(0.5, 0.5, 0.5))
        else:
            ba.buttonwidget(edit=self._back_button,
                            color=b_color,
                            textcolor=(0.75, 0.7, 0.8))

        max_str_width = 300.0
        str_width = min(
            max_str_width,
            _ba.get_string_width(folder_name, suppress_warning=True))
        ba.textwidget(edit=self._path_text,
                      text=folder_name,
                      maxwidth=max_str_width)
        ba.imagewidget(edit=self._folder_icon,
                       position=(self._folder_center - str_width * 0.5 - 40,
                                 self._height - 117),
                       opacity=0.0 if hide_top_folder else 1.0)

        if self._scrollwidget is not None:
            self._scrollwidget.delete()

        if self._use_folder_button is not None:
            self._use_folder_button.delete()
            ba.widget(edit=self._cancel_button, right_widget=self._back_button)

        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            position=((self._width - self._scroll_width) * 0.5,
                      self._height - self._scroll_height - 119),
            size=(self._scroll_width, self._scroll_height))

        if scrollwidget_selected:
            ba.containerwidget(edit=self._root_widget,
                               selected_child=self._scrollwidget)

        # show error case..
        if error is not None:
            self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                    size=(self._scroll_width,
                                                          self._scroll_height),
                                                    background=False)
            ba.textwidget(parent=self._subcontainer,
                          color=(1, 1, 0, 1),
                          text=error,
                          maxwidth=self._scroll_width * 0.9,
                          position=(self._scroll_width * 0.48,
                                    self._scroll_height * 0.57),
                          size=(0, 0),
                          h_align='center',
                          v_align='center')

        else:
            file_names = [f for f in file_names if not f.startswith('.')]
            file_names.sort(key=lambda x: x[0].lower())

            entries = file_names
            entry_height = 35
            folder_entry_height = 100
            show_folder_entry = False
            show_use_folder_button = (self._allow_folders
                                      and not in_top_folder)

            self._subcontainerheight = entry_height * len(entries) + (
                folder_entry_height if show_folder_entry else 0)
            v = self._subcontainerheight - (folder_entry_height
                                            if show_folder_entry else 0)

            self._subcontainer = ba.containerwidget(
                parent=self._scrollwidget,
                size=(self._scroll_width, self._subcontainerheight),
                background=False)

            ba.containerwidget(edit=self._scrollwidget,
                               claims_left_right=False,
                               claims_tab=False)
            ba.containerwidget(edit=self._subcontainer,
                               claims_left_right=False,
                               claims_tab=False,
                               selection_loops=False,
                               print_list_exit_instructions=False)
            ba.widget(edit=self._subcontainer, up_widget=self._back_button)

            if show_use_folder_button:
                self._use_folder_button = btn = ba.buttonwidget(
                    parent=self._root_widget,
                    position=(self._width - self._button_width - 35 -
                              self._x_inset, self._height - 67),
                    size=(self._button_width, 50),
                    label=ba.Lstr(resource=self._r +
                                  '.useThisFolderButtonText'),
                    on_activate_call=self._on_folder_entry_activated)
                ba.widget(edit=btn,
                          left_widget=self._cancel_button,
                          down_widget=self._scrollwidget)
                ba.widget(edit=self._cancel_button, right_widget=btn)
                ba.containerwidget(edit=self._root_widget, start_button=btn)

            folder_icon_size = 35
            for num, entry in enumerate(entries):
                cnt = ba.containerwidget(
                    parent=self._subcontainer,
                    position=(0, v - entry_height),
                    size=(self._scroll_width, entry_height),
                    root_selectable=True,
                    background=False,
                    click_activate=True,
                    on_activate_call=ba.Call(self._on_entry_activated, entry))
                if num == 0:
                    ba.widget(edit=cnt, up_widget=self._back_button)
                is_valid_file_path = self._is_valid_file_path(entry)
                assert self._path is not None
                is_dir = os.path.isdir(self._path + '/' + entry)
                if is_dir:
                    ba.imagewidget(parent=cnt,
                                   size=(folder_icon_size, folder_icon_size),
                                   position=(10, 0.5 * entry_height -
                                             folder_icon_size * 0.5),
                                   draw_controller=cnt,
                                   texture=self._folder_tex,
                                   color=self._folder_color)
                else:
                    ba.imagewidget(parent=cnt,
                                   size=(folder_icon_size, folder_icon_size),
                                   position=(10, 0.5 * entry_height -
                                             folder_icon_size * 0.5),
                                   opacity=1.0 if is_valid_file_path else 0.5,
                                   draw_controller=cnt,
                                   texture=self._file_tex,
                                   color=self._file_color)
                ba.textwidget(parent=cnt,
                              draw_controller=cnt,
                              text=entry,
                              h_align='left',
                              v_align='center',
                              position=(10 + folder_icon_size * 1.05,
                                        entry_height * 0.5),
                              size=(0, 0),
                              maxwidth=self._scroll_width * 0.93 - 50,
                              color=(1, 1, 1, 1) if
                              (is_valid_file_path or is_dir) else
                              (0.5, 0.5, 0.5, 1))
                v -= entry_height

    def _is_valid_file_path(self, path: str) -> bool:
        return any(path.lower().endswith(ext)
                   for ext in self._valid_file_extensions)

    def _cancel(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        if self._callback is not None:
            self._callback(None)
