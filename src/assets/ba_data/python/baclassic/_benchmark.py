# Released under the MIT License. See LICENSE for details.
#
"""Benchmark/Stress-Test related functionality."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import babase
import bascenev1
import _baclassic

if TYPE_CHECKING:
    from typing import Any, Sequence


def run_cpu_benchmark() -> None:
    """Run a cpu benchmark."""
    # pylint: disable=cyclic-import
    from bascenev1lib import tutorial

    # Save our UI state that we'll return to when done.
    if babase.app.classic is not None:
        babase.app.classic.save_ui_state()

    class BenchmarkSession(bascenev1.Session):
        """Session type for cpu benchmark."""

        def __init__(self) -> None:
            depsets: Sequence[bascenev1.DependencySet] = []

            super().__init__(depsets)

            # Store old graphics settings.
            self._old_quality = babase.app.config.resolve('Graphics Quality')
            cfg = babase.app.config
            cfg['Graphics Quality'] = 'Low'
            cfg.apply()
            self.benchmark_type = 'cpu'
            self.setactivity(bascenev1.newactivity(tutorial.TutorialActivity))

        def __del__(self) -> None:
            # When we're torn down, restore old graphics settings.
            cfg = babase.app.config
            cfg['Graphics Quality'] = self._old_quality
            cfg.apply()

        @override
        def on_player_request(self, player: bascenev1.SessionPlayer) -> bool:
            return False

    bascenev1.new_host_session(BenchmarkSession, benchmark_type='cpu')


@dataclass
class _StressTestArgs:
    playlist_type: str
    playlist_name: str
    player_count: int
    round_duration: int
    attract_mode: bool


def run_stress_test(
    playlist_type: str = 'Random',
    playlist_name: str = '__default__',
    player_count: int = 8,
    round_duration: int = 30,
    attract_mode: bool = False,
) -> None:
    """Run a stress test."""

    with babase.ContextRef.empty():
        if not attract_mode:
            babase.screenmessage(
                "Beginning stress test.. use 'End Test' to stop testing.",
                color=(1, 1, 0),
            )
        _start_stress_test(
            _StressTestArgs(
                playlist_type=playlist_type,
                playlist_name=playlist_name,
                player_count=player_count,
                round_duration=round_duration,
                attract_mode=attract_mode,
            )
        )


def stop_stress_test() -> None:
    """End a running stress test."""

    assert babase.app.classic is not None

    _baclassic.set_stress_testing(False, 0, False)
    babase.app.classic.stress_test_update_timer = None
    babase.app.classic.stress_test_update_timer_2 = None


def _start_stress_test(args: _StressTestArgs) -> None:
    """(internal)"""
    from bascenev1 import DualTeamSession, FreeForAllSession

    classic = babase.app.classic

    assert classic is not None

    appconfig = babase.app.config
    playlist_type = args.playlist_type
    if playlist_type == 'Random':
        if random.random() < 0.5:
            playlist_type = 'Teams'
        else:
            playlist_type = 'Free-For-All'
    if not args.attract_mode:
        babase.screenmessage(
            'Running Stress Test (listType="'
            + playlist_type
            + '", listName="'
            + args.playlist_name
            + '")...'
        )

    # Save where we are in the UI so we'll return there when done.
    classic.save_ui_state()

    if playlist_type == 'Teams':
        appconfig['Team Tournament Playlist Selection'] = args.playlist_name
        appconfig['Team Tournament Playlist Randomize'] = 1
        babase.apptimer(
            1.0,
            babase.Call(
                babase.pushcall,
                babase.Call(bascenev1.new_host_session, DualTeamSession),
            ),
        )
    else:
        appconfig['Free-for-All Playlist Selection'] = args.playlist_name
        appconfig['Free-for-All Playlist Randomize'] = 1
        babase.apptimer(
            1.0,
            babase.Call(
                babase.pushcall,
                babase.Call(bascenev1.new_host_session, FreeForAllSession),
            ),
        )
    _baclassic.set_stress_testing(True, args.player_count, args.attract_mode)
    classic.stress_test_update_timer = babase.AppTimer(
        args.round_duration, babase.Call(_reset_stress_test, args)
    )
    if args.attract_mode:
        classic.stress_test_update_timer_2 = babase.AppTimer(
            0.48, babase.Call(_update_attract_mode_test, args), repeat=True
        )


def _update_attract_mode_test(args: _StressTestArgs) -> None:
    if babase.get_input_idle_time() < 5.0:
        _reset_stress_test(args)


def _reset_stress_test(args: _StressTestArgs) -> None:
    _baclassic.set_stress_testing(False, args.player_count, False)
    if not args.attract_mode:
        babase.screenmessage('Resetting stress test...')
    session = bascenev1.get_foreground_host_session()
    assert session is not None
    session.end()

    assert babase.app.classic is not None
    babase.app.classic.stress_test_update_timer = None
    babase.app.classic.stress_test_update_timer_2 = None

    # For regular stress tests we keep the party going. For attract-mode
    # we just end back at the main menu. If things are idle there then
    # we'll get sent back to a new stress test.
    if not args.attract_mode:
        babase.apptimer(1.0, babase.Call(_start_stress_test, args))


def run_media_reload_benchmark() -> None:
    """Kick off a benchmark to test media reloading speeds."""
    babase.reload_media()
    babase.show_progress_bar()

    def delay_add(start_time: float) -> None:
        def doit(start_time_2: float) -> None:
            babase.screenmessage(
                babase.app.lang.get_resource(
                    'debugWindow.totalReloadTimeText'
                ).replace('${TIME}', str(babase.apptime() - start_time_2))
            )
            babase.print_load_info()
            if babase.app.config.resolve('Texture Quality') != 'High':
                babase.screenmessage(
                    babase.app.lang.get_resource(
                        'debugWindow.reloadBenchmarkBestResultsText'
                    ),
                    color=(1, 1, 0),
                )

        babase.add_clean_frame_callback(babase.Call(doit, start_time))

    # The reload starts (should add a completion callback to the reload
    # func to fix this).
    babase.apptimer(0.05, babase.Call(delay_add, babase.apptime()))
