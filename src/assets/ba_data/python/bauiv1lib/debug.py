# Released under the MIT License. See LICENSE for details.
#
"""UIs for debugging purposes."""

from __future__ import annotations

import logging
from typing import cast

import bauiv1 as bui


class DebugWindow(bui.Window):
    """Window for debugging internal values."""

    def __init__(self, transition: str | None = 'in_right'):
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        from bauiv1lib import popup

        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_location('Benchmarks & Stress Tests')
        uiscale = bui.app.ui_v1.uiscale
        self._width = width = 580
        self._height = height = (
            350
            if uiscale is bui.UIScale.SMALL
            else 420
            if uiscale is bui.UIScale.MEDIUM
            else 520
        )

        self._scroll_width = self._width - 100
        self._scroll_height = self._height - 120

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 520

        self._stress_test_game_type = 'Random'
        self._stress_test_playlist = '__default__'
        self._stress_test_player_count = 8
        self._stress_test_round_duration = 30

        self._r = 'debugWindow'
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition=transition,
                scale=(
                    2.35
                    if uiscale is bui.UIScale.SMALL
                    else 1.55
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
                stack_offset=(0, -30)
                if uiscale is bui.UIScale.SMALL
                else (0, 0),
            )
        )

        self._done_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(40, height - 67),
            size=(120, 60),
            scale=0.8,
            autoselect=True,
            label=bui.Lstr(resource='doneText'),
            on_activate_call=self._done,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 60),
            size=(width, 30),
            text=bui.Lstr(resource=self._r + '.titleText'),
            h_align='center',
            color=bui.app.ui_v1.title_color,
            v_align='center',
            maxwidth=260,
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            position=((self._width - self._scroll_width) * 0.5, 50),
        )
        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
        )

        v = self._sub_height - 70
        button_width = 300
        btn = bui.buttonwidget(
            parent=self._subcontainer,
            position=((self._sub_width - button_width) * 0.5, v),
            size=(button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=self._r + '.runCPUBenchmarkText'),
            on_activate_call=self._run_cpu_benchmark_pressed,
        )
        bui.widget(
            edit=btn, up_widget=self._done_button, left_widget=self._done_button
        )
        v -= 60

        bui.buttonwidget(
            parent=self._subcontainer,
            position=((self._sub_width - button_width) * 0.5, v),
            size=(button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=self._r + '.runGPUBenchmarkText'),
            on_activate_call=self._run_gpu_benchmark_pressed,
        )
        v -= 60

        bui.buttonwidget(
            parent=self._subcontainer,
            position=((self._sub_width - button_width) * 0.5, v),
            size=(button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=self._r + '.runMediaReloadBenchmarkText'),
            on_activate_call=self._run_media_reload_benchmark_pressed,
        )
        v -= 60

        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v + 22),
            size=(0, 0),
            text=bui.Lstr(resource=self._r + '.stressTestTitleText'),
            maxwidth=200,
            color=bui.app.ui_v1.heading_color,
            scale=0.85,
            h_align='center',
            v_align='center',
        )
        v -= 45

        x_offs = 165
        bui.textwidget(
            parent=self._subcontainer,
            position=(x_offs - 10, v + 22),
            size=(0, 0),
            text=bui.Lstr(resource=self._r + '.stressTestPlaylistTypeText'),
            maxwidth=130,
            color=bui.app.ui_v1.heading_color,
            scale=0.65,
            h_align='right',
            v_align='center',
        )

        popup.PopupMenu(
            parent=self._subcontainer,
            position=(x_offs, v),
            width=150,
            choices=['Random', 'Teams', 'Free-For-All'],
            choices_display=[
                bui.Lstr(resource=a)
                for a in [
                    'randomText',
                    'playModes.teamsText',
                    'playModes.freeForAllText',
                ]
            ],
            current_choice='Auto',
            on_value_change_call=self._stress_test_game_type_selected,
        )

        v -= 46
        bui.textwidget(
            parent=self._subcontainer,
            position=(x_offs - 10, v + 22),
            size=(0, 0),
            text=bui.Lstr(resource=self._r + '.stressTestPlaylistNameText'),
            maxwidth=130,
            color=bui.app.ui_v1.heading_color,
            scale=0.65,
            h_align='right',
            v_align='center',
        )

        self._stress_test_playlist_name_field = bui.textwidget(
            parent=self._subcontainer,
            position=(x_offs + 5, v - 5),
            size=(250, 46),
            text=self._stress_test_playlist,
            h_align='left',
            v_align='center',
            autoselect=True,
            color=(0.9, 0.9, 0.9, 1.0),
            description=bui.Lstr(
                resource=self._r + '.stressTestPlaylistDescriptionText'
            ),
            editable=True,
            padding=4,
        )
        v -= 29
        x_sub = 60

        # Player count.
        bui.textwidget(
            parent=self._subcontainer,
            position=(x_offs - 10, v),
            size=(0, 0),
            text=bui.Lstr(resource=self._r + '.stressTestPlayerCountText'),
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='right',
            v_align='center',
            scale=0.65,
            maxwidth=130,
        )
        self._stress_test_player_count_text = bui.textwidget(
            parent=self._subcontainer,
            position=(246 - x_sub, v - 14),
            size=(60, 28),
            editable=False,
            color=(0.3, 1.0, 0.3, 1.0),
            h_align='right',
            v_align='center',
            text=str(self._stress_test_player_count),
            padding=2,
        )
        bui.buttonwidget(
            parent=self._subcontainer,
            position=(330 - x_sub, v - 11),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=bui.Call(self._stress_test_player_count_decrement),
            repeat=True,
            enable_sound=True,
        )
        bui.buttonwidget(
            parent=self._subcontainer,
            position=(380 - x_sub, v - 11),
            size=(28, 28),
            label='+',
            autoselect=True,
            on_activate_call=bui.Call(self._stress_test_player_count_increment),
            repeat=True,
            enable_sound=True,
        )
        v -= 42

        # Round duration.
        bui.textwidget(
            parent=self._subcontainer,
            position=(x_offs - 10, v),
            size=(0, 0),
            text=bui.Lstr(resource=self._r + '.stressTestRoundDurationText'),
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='right',
            v_align='center',
            scale=0.65,
            maxwidth=130,
        )
        self._stress_test_round_duration_text = bui.textwidget(
            parent=self._subcontainer,
            position=(246 - x_sub, v - 14),
            size=(60, 28),
            editable=False,
            color=(0.3, 1.0, 0.3, 1.0),
            h_align='right',
            v_align='center',
            text=str(self._stress_test_round_duration),
            padding=2,
        )
        bui.buttonwidget(
            parent=self._subcontainer,
            position=(330 - x_sub, v - 11),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=bui.Call(
                self._stress_test_round_duration_decrement
            ),
            repeat=True,
            enable_sound=True,
        )
        bui.buttonwidget(
            parent=self._subcontainer,
            position=(380 - x_sub, v - 11),
            size=(28, 28),
            label='+',
            autoselect=True,
            on_activate_call=bui.Call(
                self._stress_test_round_duration_increment
            ),
            repeat=True,
            enable_sound=True,
        )
        v -= 82
        btn = bui.buttonwidget(
            parent=self._subcontainer,
            position=((self._sub_width - button_width) * 0.5, v),
            size=(button_width, 60),
            autoselect=True,
            label=bui.Lstr(resource=self._r + '.runStressTestText'),
            on_activate_call=self._stress_test_pressed,
        )
        bui.widget(btn, show_buffer_bottom=50)

    def _stress_test_player_count_decrement(self) -> None:
        self._stress_test_player_count = max(
            1, self._stress_test_player_count - 1
        )
        bui.textwidget(
            edit=self._stress_test_player_count_text,
            text=str(self._stress_test_player_count),
        )

    def _stress_test_player_count_increment(self) -> None:
        self._stress_test_player_count = self._stress_test_player_count + 1
        bui.textwidget(
            edit=self._stress_test_player_count_text,
            text=str(self._stress_test_player_count),
        )

    def _stress_test_round_duration_decrement(self) -> None:
        self._stress_test_round_duration = max(
            10, self._stress_test_round_duration - 10
        )
        bui.textwidget(
            edit=self._stress_test_round_duration_text,
            text=str(self._stress_test_round_duration),
        )

    def _stress_test_round_duration_increment(self) -> None:
        self._stress_test_round_duration = self._stress_test_round_duration + 10
        bui.textwidget(
            edit=self._stress_test_round_duration_text,
            text=str(self._stress_test_round_duration),
        )

    def _stress_test_game_type_selected(self, game_type: str) -> None:
        self._stress_test_game_type = game_type

    def _run_cpu_benchmark_pressed(self) -> None:
        if bui.app.classic is None:
            logging.warning('run-cpu-benchmark requires classic')
            return
        bui.app.classic.run_cpu_benchmark()

    def _run_gpu_benchmark_pressed(self) -> None:
        if bui.app.classic is None:
            logging.warning('run-gpu-benchmark requires classic')
            return
        bui.app.classic.run_gpu_benchmark()

    def _run_media_reload_benchmark_pressed(self) -> None:
        if bui.app.classic is None:
            logging.warning('run-media-reload-benchmark requires classic')
            return
        bui.app.classic.run_media_reload_benchmark()

    def _stress_test_pressed(self) -> None:
        if bui.app.classic is None:
            logging.warning('stress-test requires classic')
            return

        bui.app.classic.run_stress_test(
            playlist_type=self._stress_test_game_type,
            playlist_name=cast(
                str, bui.textwidget(query=self._stress_test_playlist_name_field)
            ),
            player_count=self._stress_test_player_count,
            round_duration=self._stress_test_round_duration,
        )
        bui.containerwidget(edit=self._root_widget, transition='out_right')

    def _done(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(edit=self._root_widget, transition='out_right')
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            AdvancedSettingsWindow(transition='in_left').get_root_widget(),
            from_window=self._root_widget,
        )
