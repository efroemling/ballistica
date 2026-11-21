# Released under the MIT License. See LICENSE for details.
#
"""Tests for nearby discovery's route ranking, failover and pacing.

The scenarios live in ``nearbysim.py``, which drives the real discovery
protocol on a simulated network and clock, so the timing they check
(failover, losing a host, noticing a new one, steady-state traffic)
costs no real waiting. ``babase`` only imports inside the engine, so
all of them run in one engine launch, and each is reported here as its
own test.

Gated on ``apprun.test_runs_disabled()`` like the other tests needing
the engine binary.
"""

import os
import json
from pathlib import Path

import pytest

from batools import apprun

#: Every scenario in nearbysim.SCENARIOS (checked by
#: test_scenario_list_complete).
SCENARIOS = [
    'dedupe_and_rank',
    'ipv4_wins_ties',
    'near_equal_routes_dont_flap',
    'faster_route_takes_over',
    'failover_to_spare',
    'lost_answer_with_spare_stays_calm',
    'lost_answer_alone_goes_full_rate',
    'vanished_host_dropped',
    'late_host_found_via_broadcast',
    'late_host_found_via_dns_sd',
    'steady_state_traffic',
    'dead_candidate_backs_off',
    'legacy_hosts_listed',
    'remote_v1_answer_first_no_duplicate',
    'remote_v2_replaces_legacy_twin',
    'ignores_self_and_garbage',
    'targets_only',
    'quiet_best_route_news',
]

_skip = pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)


@pytest.fixture(scope='module', name='results')
def _results(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str | None]:
    """Run every scenario in one engine launch."""
    outpath = tmp_path_factory.mktemp('nearby') / 'results.json'
    testsdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    apprun.python_command(
        f'import sys\n'
        f'sys.path.insert(0, {testsdir!r})\n'
        f'from test_base import nearbysim\n'
        f'nearbysim.run_all({str(outpath)!r})\n',
        purpose='nearby discovery tests',
    )
    output = json.loads(Path(outpath).read_text(encoding='utf-8'))

    # Handy when tuning (shown with pytest -s).
    print('nearbysim measurements:')
    for what, value in output['measurements'].items():
        print(f'  {what}: {value}')
    results: dict[str, str | None] = output['results']
    return results


@_skip
def test_scenario_list_complete(results: dict[str, str | None]) -> None:
    """SCENARIOS here matches what nearbysim runs."""
    assert sorted(results) == sorted(SCENARIOS)


@_skip
@pytest.mark.parametrize('name', SCENARIOS)
def test_scenario(name: str, results: dict[str, str | None]) -> None:
    """One nearbysim scenario."""
    assert name in results, f'{name} did not run'
    error = results[name]
    if error is not None:
        pytest.fail(error, pytrace=False)
