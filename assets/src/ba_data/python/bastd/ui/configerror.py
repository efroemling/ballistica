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
"""UI for dealing with broken config files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    pass


class ConfigErrorWindow(ba.Window):
    """Window for dealing with a broken config."""

    def __init__(self) -> None:
        self._config_file_path = ba.app.config_file_path
        width = 800
        super().__init__(
            ba.containerwidget(size=(width, 300), transition='in_right'))
        padding = 20
        ba.textwidget(
            parent=self._root_widget,
            position=(padding, 220),
            size=(width - 2 * padding, 100 - 2 * padding),
            h_align='center',
            v_align='top',
            scale=0.73,
            text=(f'Error reading {_ba.appnameupper()} config file'
                  ':\n\n\nCheck the console'
                  ' (press ~ twice) for details.\n\nWould you like to quit and'
                  ' try to fix it by hand\nor overwrite it with defaults?\n\n'
                  '(high scores, player profiles, etc will be lost if you'
                  ' overwrite)'))
        ba.textwidget(parent=self._root_widget,
                      position=(padding, 198),
                      size=(width - 2 * padding, 100 - 2 * padding),
                      h_align='center',
                      v_align='top',
                      scale=0.5,
                      text=self._config_file_path)
        quit_button = ba.buttonwidget(parent=self._root_widget,
                                      position=(35, 30),
                                      size=(240, 54),
                                      label='Quit and Edit',
                                      on_activate_call=self._quit)
        ba.buttonwidget(parent=self._root_widget,
                        position=(width - 370, 30),
                        size=(330, 54),
                        label='Overwrite with Defaults',
                        on_activate_call=self._defaults)
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=quit_button,
                           selected_child=quit_button)

    def _quit(self) -> None:
        ba.timer(0.001, self._edit_and_quit, timetype=ba.TimeType.REAL)
        _ba.lock_all_input()

    def _edit_and_quit(self) -> None:
        _ba.open_file_externally(self._config_file_path)
        ba.timer(0.1, ba.quit, timetype=ba.TimeType.REAL)

    def _defaults(self) -> None:
        from ba.internal import commit_app_config
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.playsound(ba.getsound('gunCocking'))
        ba.screenmessage('settings reset.', color=(1, 1, 0))

        # At this point settings are already set; lets just commit them
        # to disk.
        commit_app_config(force=True)
