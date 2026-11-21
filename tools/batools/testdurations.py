# Released under the MIT License. See LICENSE for details.
#
"""Freshness tracking for the pytest-split test-duration database.

The ``test-ex-splitN`` shards balance themselves using per-test
timings recorded in :data:`DURATIONS_PATH`. Those timings rot as tests
are added and change, and nothing about a stale file looks broken; CI
just gets slower because one shard ends up carrying most of the work.
So ``make test-ex-split-durations`` stamps the file with the date it
was recorded (under :data:`RECORDED_KEY`) and the project check fails
once that stamp is older than :data:`MAX_AGE_DAYS`.

The stamp lives inside the durations file itself so the date and the
data can't drift apart. pytest-split tolerates the extra key: it drops
any entry that doesn't match a collected test id before using the
timings.
"""

import json
import datetime
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    from pathlib import Path

#: Project-relative path of the durations file. Must match
#: ``TEST_EX_DURATIONS_PATH`` in the Makefile.
DURATIONS_PATH = 'pconfig/test_ex_durations'

#: Key holding the ISO date the durations were recorded.
RECORDED_KEY = '__recorded__'

#: How old the recording may get before the project check fails.
MAX_AGE_DAYS = 120


def stamp_recorded_date(projroot: Path) -> None:
    """Stamp today's date into the durations file.

    Run right after a successful ``--store-durations`` pytest run.
    """
    path = projroot / DURATIONS_PATH
    durations = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(durations, dict):
        raise CleanError(f'Expected a dict in {DURATIONS_PATH}.')
    durations[RECORDED_KEY] = _today().isoformat()

    # Match pytest-split's own formatting so recordings diff cleanly.
    path.write_text(
        json.dumps(durations, sort_keys=True, indent=4), encoding='utf-8'
    )


def check_recorded_date(projroot: Path) -> None:
    """Fail if the durations file is missing its stamp or is too old."""
    fixcmd = 'make test-ex-split-durations'
    path = projroot / DURATIONS_PATH
    try:
        durations = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise CleanError(
            f'{DURATIONS_PATH} not found; run "{fixcmd}" to record it.'
        ) from None
    recorded = (
        durations.get(RECORDED_KEY) if isinstance(durations, dict) else None
    )
    if not isinstance(recorded, str):
        raise CleanError(
            f'{DURATIONS_PATH} has no "{RECORDED_KEY}" date stamp'
            f' (the last recording may have failed partway);'
            f' run "{fixcmd}" to re-record it.'
        )
    try:
        recorded_date = datetime.date.fromisoformat(recorded)
    except ValueError:
        raise CleanError(
            f'Invalid "{RECORDED_KEY}" value {recorded!r} in'
            f' {DURATIONS_PATH}; run "{fixcmd}" to re-record it.'
        ) from None
    age = (_today() - recorded_date).days
    if age > MAX_AGE_DAYS:
        raise CleanError(
            f'Test durations in {DURATIONS_PATH} were recorded {age} days'
            f' ago ({recorded}; limit is {MAX_AGE_DAYS}), so test-ex-splitN'
            f' CI shards are likely unbalanced. Run "{fixcmd}" (unsandboxed;'
            f' the whole suite must pass) and commit the result.'
        )


def _today() -> datetime.date:
    return datetime.datetime.now(datetime.UTC).date()
