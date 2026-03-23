# Released under the MIT License. See LICENSE for details.
#
"""Tests for efro.util."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any

FAST_MODE = os.environ.get('EFRO_TEST_FAST_MODE') == '1'


def test_do_once() -> None:
    """Test do_once() fires exactly on the requested iteration."""
    from efro.util import do_once

    # Default (on_iteration=1): True only on the first call.
    results = [do_once() for _ in range(5)]
    assert results == [True, False, False, False, False]

    # on_iteration=3: True only on the third call.
    results2 = [do_once(on_iteration=3) for _ in range(5)]
    assert results2 == [False, False, True, False, False]


def test_do_once_periodically_threshold() -> None:
    """Test do_once_periodically() fires on the right iteration (no sleep)."""
    from efro.util import do_once_periodically

    # on_iteration=2: True only on the second call within the period.
    results = [do_once_periodically(on_iteration=2) for _ in range(5)]
    assert results == [False, True, False, False, False]


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_do_once_periodically_reset() -> None:
    """Test do_once_periodically() count resets after period expires."""
    import time
    from datetime import timedelta
    from efro.util import do_once_periodically

    def call(**kwargs: Any) -> bool:
        return do_once_periodically(**kwargs)  # stable call site

    td = timedelta(seconds=0.05)
    assert not call(on_iteration=2, period=td)  # count=1, False
    assert call(on_iteration=2, period=td)  # count=2, True
    assert not call(on_iteration=2, period=td)  # count=3, False

    time.sleep(0.06)  # let the slice boundary pass

    assert not call(on_iteration=2, period=td)  # count reset to 1, False
    assert call(on_iteration=2, period=td)  # count=2, True again
