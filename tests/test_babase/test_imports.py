# Released under the MIT License. See LICENSE for details.
#
"""Testing asset manager functionality."""

from __future__ import annotations

import pytest

from batools import testrun


@pytest.mark.skipif(
    testrun.test_runs_disabled(),
    reason='Test app runs disabled here.',
)
def test_babase_imports() -> None:
    """Testing."""

    # Make sure our package and binary module can be cleanly imported by
    # themselves.
    testrun.run_command('import babase')
    testrun.run_command('import _babase')
