# Released under the MIT License. See LICENSE for details.
#
"""UI for dealing with broken config files."""

from __future__ import annotations

import bauiv1 as bui


class ConfigErrorWindow(bui.Window):
    """Window for dealing with a broken config."""

    def __init__(self) -> None:
        self._config_file_path = bui.app.env.config_file_path
        width = 800
        super().__init__(
            bui.containerwidget(size=(width, 400), transition='in_right')
        )
        padding = 20
        bui.textwidget(
            parent=self._root_widget,
            position=(padding, 220 + 60),
            size=(width - 2 * padding, 100 - 2 * padding),
            h_align='center',
            v_align='top',
            scale=0.73,
            text=(
                f'Error reading {bui.appnameupper()} config file'
                ':\n\n\nCheck the console'
                ' (press ~ twice) for details.\n\nWould you like to quit and'
                ' try to fix it by hand\nor overwrite it with defaults?\n\n'
                '(high scores, player profiles, etc will be lost if you'
                ' overwrite)'
            ),
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(padding, 198 + 60),
            size=(width - 2 * padding, 100 - 2 * padding),
            h_align='center',
            v_align='top',
            scale=0.5,
            text=self._config_file_path,
        )
        quit_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(35, 30),
            size=(240, 54),
            label='Quit and Edit',
            on_activate_call=self._quit,
        )
        bui.buttonwidget(
            parent=self._root_widget,
            position=(width - 370, 30),
            size=(330, 54),
            label='Overwrite with Defaults',
            on_activate_call=self._defaults,
        )
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=quit_button,
            selected_child=quit_button,
        )

    def _quit(self) -> None:
        bui.apptimer(0.001, self._edit_and_quit)
        bui.lock_all_input()

    def _edit_and_quit(self) -> None:
        bui.open_file_externally(self._config_file_path)
        bui.apptimer(0.1, bui.quit)

    def _defaults(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_left')
        bui.getsound('gunCocking').play()
        bui.screenmessage('settings reset.', color=(1, 1, 0))

        # At this point settings are already set; lets just commit them
        # to disk.
        bui.commit_app_config(force=True)
