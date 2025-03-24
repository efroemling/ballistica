# Released under the MIT License. See LICENSE for details.
#
"""Testing rpc functionality."""

from __future__ import annotations

import os
import time
import logging
from typing import TYPE_CHECKING

import pytest

from efro.threadpool import ThreadPoolExecutorEx

if TYPE_CHECKING:
    from typing import Awaitable

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_no_wait_back_pressure(caplog: pytest.LogCaptureFixture) -> None:
    """Make sure we start blocking if too many no-wait calls are submitted."""

    tasktime = 0.1

    def _do_test(max_no_wait_count: int) -> None:
        threadpool = ThreadPoolExecutorEx(
            max_workers=10, max_no_wait_count=max_no_wait_count
        )

        def _long_call() -> None:
            time.sleep(tasktime)
            print('HELLO FROM FINISHED CALL')

        for _i in range(10):
            threadpool.submit_no_wait(_long_call)

        threadpool.shutdown(wait=True)

        assert threadpool.no_wait_count == 0

    # If we limit our no-wait-tasks it should take roughtly 2 * tasktime
    # to get everything through and we should see a warning about
    # hitting the limit.
    print('\nTesting WITH no-wait-tasks bottleneck...')
    starttime = time.monotonic()
    with caplog.at_level(logging.WARNING):
        _do_test(max_no_wait_count=6)
    duration = time.monotonic() - starttime
    print(f'TOOK {duration}')
    assert duration > 2.0 * tasktime
    assert 'hit max no-wait limit' in caplog.text

    # If no-wait-tasks is not the bottleneck, it should take just about
    # tasktime exactly and there should be no warnings.
    print('\nTesting WITHOUT no-wait-tasks bottleneck...')
    starttime = time.monotonic()
    with caplog.at_level(logging.WARNING):
        _do_test(max_no_wait_count=20)
    duration = time.monotonic() - starttime
    print(f'TOOK {duration}')
    assert duration < 1.2 * tasktime
