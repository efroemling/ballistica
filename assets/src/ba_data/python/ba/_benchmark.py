# Released under the MIT License. See LICENSE for details.
#
"""Benchmark/Stress-Test related functionality."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any, Sequence
    import ba


def run_cpu_benchmark() -> None:
    """Run a cpu benchmark."""
    # pylint: disable=cyclic-import
    from bastd import tutorial
    from ba._session import Session

    class BenchmarkSession(Session):
        """Session type for cpu benchmark."""

        def __init__(self) -> None:

            # print('FIXME: BENCHMARK SESSION WOULD CALC DEPS.')
            depsets: Sequence[ba.DependencySet] = []

            super().__init__(depsets)

            # Store old graphics settings.
            self._old_quality = _ba.app.config.resolve('Graphics Quality')
            cfg = _ba.app.config
            cfg['Graphics Quality'] = 'Low'
            cfg.apply()
            self.benchmark_type = 'cpu'
            self.setactivity(_ba.newactivity(tutorial.TutorialActivity))

        def __del__(self) -> None:

            # When we're torn down, restore old graphics settings.
            cfg = _ba.app.config
            cfg['Graphics Quality'] = self._old_quality
            cfg.apply()

        def on_player_request(self, player: ba.SessionPlayer) -> bool:
            return False

    _ba.new_host_session(BenchmarkSession, benchmark_type='cpu')


def run_stress_test(
    playlist_type: str = 'Random',
    playlist_name: str = '__default__',
    player_count: int = 8,
    round_duration: int = 30,
) -> None:
    """Run a stress test."""
    from ba import modutils
    from ba._general import Call
    from ba._generated.enums import TimeType

    _ba.screenmessage(
        "Beginning stress test.. use 'End Test' to stop testing.",
        color=(1, 1, 0),
    )
    with _ba.Context('ui'):
        start_stress_test(
            {
                'playlist_type': playlist_type,
                'playlist_name': playlist_name,
                'player_count': player_count,
                'round_duration': round_duration,
            }
        )
        _ba.timer(
            7.0,
            Call(
                _ba.screenmessage,
                (
                    'stats will be written to '
                    + modutils.get_human_readable_user_scripts_path()
                    + '/stress_test_stats.csv'
                ),
            ),
            timetype=TimeType.REAL,
        )


def stop_stress_test() -> None:
    """End a running stress test."""
    _ba.set_stress_testing(False, 0)
    try:
        if _ba.app.stress_test_reset_timer is not None:
            _ba.screenmessage('Ending stress test...', color=(1, 1, 0))
    except Exception:
        pass
    _ba.app.stress_test_reset_timer = None


def start_stress_test(args: dict[str, Any]) -> None:
    """(internal)"""
    from ba._general import Call
    from ba._dualteamsession import DualTeamSession
    from ba._freeforallsession import FreeForAllSession
    from ba._generated.enums import TimeType, TimeFormat

    appconfig = _ba.app.config
    playlist_type = args['playlist_type']
    if playlist_type == 'Random':
        if random.random() < 0.5:
            playlist_type = 'Teams'
        else:
            playlist_type = 'Free-For-All'
    _ba.screenmessage(
        'Running Stress Test (listType="'
        + playlist_type
        + '", listName="'
        + args['playlist_name']
        + '")...'
    )
    if playlist_type == 'Teams':
        appconfig['Team Tournament Playlist Selection'] = args['playlist_name']
        appconfig['Team Tournament Playlist Randomize'] = 1
        _ba.timer(
            1.0,
            Call(_ba.pushcall, Call(_ba.new_host_session, DualTeamSession)),
            timetype=TimeType.REAL,
        )
    else:
        appconfig['Free-for-All Playlist Selection'] = args['playlist_name']
        appconfig['Free-for-All Playlist Randomize'] = 1
        _ba.timer(
            1.0,
            Call(_ba.pushcall, Call(_ba.new_host_session, FreeForAllSession)),
            timetype=TimeType.REAL,
        )
    _ba.set_stress_testing(True, args['player_count'])
    _ba.app.stress_test_reset_timer = _ba.Timer(
        args['round_duration'] * 1000,
        Call(_reset_stress_test, args),
        timetype=TimeType.REAL,
        timeformat=TimeFormat.MILLISECONDS,
    )


def _reset_stress_test(args: dict[str, Any]) -> None:
    from ba._general import Call
    from ba._generated.enums import TimeType

    _ba.set_stress_testing(False, args['player_count'])
    _ba.screenmessage('Resetting stress test...')
    session = _ba.get_foreground_host_session()
    assert session is not None
    session.end()
    _ba.timer(1.0, Call(start_stress_test, args), timetype=TimeType.REAL)


def run_gpu_benchmark() -> None:
    """Kick off a benchmark to test gpu speeds."""
    # FIXME: Not wired up yet.
    _ba.screenmessage('Not wired up yet.', color=(1, 0, 0))


def run_media_reload_benchmark() -> None:
    """Kick off a benchmark to test media reloading speeds."""
    from ba._general import Call
    from ba._generated.enums import TimeType

    _ba.reload_media()
    _ba.show_progress_bar()

    def delay_add(start_time: float) -> None:
        def doit(start_time_2: float) -> None:
            _ba.screenmessage(
                _ba.app.lang.get_resource(
                    'debugWindow.totalReloadTimeText'
                ).replace(
                    '${TIME}', str(_ba.time(TimeType.REAL) - start_time_2)
                )
            )
            _ba.print_load_info()
            if _ba.app.config.resolve('Texture Quality') != 'High':
                _ba.screenmessage(
                    _ba.app.lang.get_resource(
                        'debugWindow.reloadBenchmarkBestResultsText'
                    ),
                    color=(1, 1, 0),
                )

        _ba.add_clean_frame_callback(Call(doit, start_time))

    # The reload starts (should add a completion callback to the
    # reload func to fix this).
    _ba.timer(
        0.05, Call(delay_add, _ba.time(TimeType.REAL)), timetype=TimeType.REAL
    )
