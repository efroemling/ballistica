# Released under the MIT License. See LICENSE for details.
#
"""Benchmark/Stress-Test related functionality."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _babase
import _bauiv1
import _bascenev1

if TYPE_CHECKING:
    from typing import Any, Sequence

    import babase
    import bascenev1


def run_cpu_benchmark() -> None:
    """Run a cpu benchmark."""
    # pylint: disable=cyclic-import
    from bascenev1lib import tutorial
    from bascenev1._session import Session

    class BenchmarkSession(Session):
        """Session type for cpu benchmark."""

        def __init__(self) -> None:
            # print('FIXME: BENCHMARK SESSION WOULD CALC DEPS.')
            depsets: Sequence[bascenev1.DependencySet] = []

            super().__init__(depsets)

            # Store old graphics settings.
            self._old_quality = _babase.app.config.resolve('Graphics Quality')
            cfg = _babase.app.config
            cfg['Graphics Quality'] = 'Low'
            cfg.apply()
            self.benchmark_type = 'cpu'
            self.setactivity(_bascenev1.newactivity(tutorial.TutorialActivity))

        def __del__(self) -> None:
            # When we're torn down, restore old graphics settings.
            cfg = _babase.app.config
            cfg['Graphics Quality'] = self._old_quality
            cfg.apply()

        def on_player_request(self, player: bascenev1.SessionPlayer) -> bool:
            return False

    _bascenev1.new_host_session(BenchmarkSession, benchmark_type='cpu')


def run_stress_test(
    playlist_type: str = 'Random',
    playlist_name: str = '__default__',
    player_count: int = 8,
    round_duration: int = 30,
) -> None:
    """Run a stress test."""
    from babase import modutils
    from babase._general import Call

    _babase.screenmessage(
        "Beginning stress test.. use 'End Test' to stop testing.",
        color=(1, 1, 0),
    )
    with _babase.ContextRef.empty():
        start_stress_test(
            {
                'playlist_type': playlist_type,
                'playlist_name': playlist_name,
                'player_count': player_count,
                'round_duration': round_duration,
            }
        )
        _babase.apptimer(
            7.0,
            Call(
                _babase.screenmessage,
                (
                    'stats will be written to '
                    + modutils.get_human_readable_user_scripts_path()
                    + '/stress_test_stats.csv'
                ),
            ),
        )


def stop_stress_test() -> None:
    """End a running stress test."""
    _babase.set_stress_testing(False, 0)
    assert _babase.app.classic is not None
    try:
        if _babase.app.classic.stress_test_reset_timer is not None:
            _babase.screenmessage('Ending stress test...', color=(1, 1, 0))
    except Exception:
        pass
    _babase.app.classic.stress_test_reset_timer = None


def start_stress_test(args: dict[str, Any]) -> None:
    """(internal)"""
    from babase._general import Call
    from bascenev1._dualteamsession import DualTeamSession
    from bascenev1._freeforallsession import FreeForAllSession

    assert _babase.app.classic is not None

    appconfig = _babase.app.config
    playlist_type = args['playlist_type']
    if playlist_type == 'Random':
        if random.random() < 0.5:
            playlist_type = 'Teams'
        else:
            playlist_type = 'Free-For-All'
    _babase.screenmessage(
        'Running Stress Test (listType="'
        + playlist_type
        + '", listName="'
        + args['playlist_name']
        + '")...'
    )
    if playlist_type == 'Teams':
        appconfig['Team Tournament Playlist Selection'] = args['playlist_name']
        appconfig['Team Tournament Playlist Randomize'] = 1
        _babase.apptimer(
            1.0,
            Call(
                _babase.pushcall,
                Call(_bascenev1.new_host_session, DualTeamSession),
            ),
        )
    else:
        appconfig['Free-for-All Playlist Selection'] = args['playlist_name']
        appconfig['Free-for-All Playlist Randomize'] = 1
        _babase.apptimer(
            1.0,
            Call(
                _babase.pushcall,
                Call(_bascenev1.new_host_session, FreeForAllSession),
            ),
        )
    _babase.set_stress_testing(True, args['player_count'])
    _babase.app.classic.stress_test_reset_timer = _babase.AppTimer(
        args['round_duration'], Call(_reset_stress_test, args)
    )


def _reset_stress_test(args: dict[str, Any]) -> None:
    from babase._general import Call

    _babase.set_stress_testing(False, args['player_count'])
    _babase.screenmessage('Resetting stress test...')
    session = _bascenev1.get_foreground_host_session()
    assert session is not None
    session.end()
    _babase.apptimer(1.0, Call(start_stress_test, args))


def run_gpu_benchmark() -> None:
    """Kick off a benchmark to test gpu speeds."""
    # FIXME: Not wired up yet.
    _babase.screenmessage('Not wired up yet.', color=(1, 0, 0))


def run_media_reload_benchmark() -> None:
    """Kick off a benchmark to test media reloading speeds."""
    from babase._general import Call

    _babase.reload_media()
    _bauiv1.show_progress_bar()

    def delay_add(start_time: float) -> None:
        def doit(start_time_2: float) -> None:
            _babase.screenmessage(
                _babase.app.lang.get_resource(
                    'debugWindow.totalReloadTimeText'
                ).replace('${TIME}', str(_babase.apptime() - start_time_2))
            )
            _babase.print_load_info()
            if _babase.app.config.resolve('Texture Quality') != 'High':
                _babase.screenmessage(
                    _babase.app.lang.get_resource(
                        'debugWindow.reloadBenchmarkBestResultsText'
                    ),
                    color=(1, 1, 0),
                )

        _babase.add_clean_frame_callback(Call(doit, start_time))

    # The reload starts (should add a completion callback to the
    # reload func to fix this).
    _babase.apptimer(0.05, Call(delay_add, _babase.apptime()))
