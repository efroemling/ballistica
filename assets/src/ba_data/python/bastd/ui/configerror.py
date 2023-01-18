# Released under the MIT License. See LICENSE for details.
#
"""UI for dealing with broken config files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import ba.internal

if TYPE_CHECKING:
    pass


class ConfigErrorWindow(ba.Window):
    """Window for dealing with a broken config."""

    def __init__(self) -> None:
        self._config_file_path = ba.app.config_file_path
        width = 800
        super().__init__(
            ba.containerwidget(size=(width, 400), transition='in_right')
        )
        padding = 20
        ba.textwidget(
            parent=self._root_widget,
            position=(padding, 220 + 60),
            size=(width - 2 * padding, 100 - 2 * padding),
            h_align='center',
            v_align='top',
            scale=0.73,
            text=(
                f'Error reading {ba.internal.appnameupper()} config file'
                ':\n\n\nCheck the console'
                ' (press ~ twice) for details.\n\nWould you like to quit and'
                ' try to fix it by hand\nor overwrite it with defaults?\n\n'
                '(high scores, player profiles, etc will be lost if you'
                ' overwrite)'
            ),
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(padding, 198 + 60),
            size=(width - 2 * padding, 100 - 2 * padding),
            h_align='center',
            v_align='top',
            scale=0.5,
            text=self._config_file_path,
        )
        quit_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(35, 30),
            size=(240, 54),
            label='Quit and Edit',
            on_activate_call=self._quit,
        )
        ba.buttonwidget(
            parent=self._root_widget,
            position=(width - 370, 30),
            size=(330, 54),
            label='Overwrite with Defaults',
            on_activate_call=self._defaults,
        )
        ba.containerwidget(
            edit=self._root_widget,
            cancel_button=quit_button,
            selected_child=quit_button,
        )

    def _quit(self) -> None:
        ba.timer(0.001, self._edit_and_quit, timetype=ba.TimeType.REAL)
        ba.internal.lock_all_input()

    def _edit_and_quit(self) -> None:
        ba.internal.open_file_externally(self._config_file_path)
        ba.timer(0.1, ba.quit, timetype=ba.TimeType.REAL)

    def _defaults(self) -> None:
        from ba.internal import commit_app_config

        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.playsound(ba.getsound('gunCocking'))
        ba.screenmessage('settings reset.', color=(1, 1, 0))

        # At this point settings are already set; lets just commit them
        # to disk.
        commit_app_config(force=True)
