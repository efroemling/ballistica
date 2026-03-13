# Released under the MIT License. See LICENSE for details.
#
"""C++-level Object ref-count tests."""

from __future__ import annotations

import os

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_object() -> None:
    """Run C++ Object ref-count self-tests."""
    apprun.python_command(
        'import _babase; _babase.test_object()',
        purpose='Object ref-count testing',
    )
