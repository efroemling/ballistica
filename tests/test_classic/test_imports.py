# Released under the MIT License. See LICENSE for details.
#
"""Testing asset manager functionality."""

from __future__ import annotations

import pytest

from batools import testrun


@pytest.mark.skipif(
    testrun.test_runs_disabled(), reason=testrun.test_runs_disabled_reason()
)
def test_imports() -> None:
    """Test imports for our featureset."""

    # Make sure our package and binary module can be cleanly imported by
    # themselves.
    testrun.run_command('import baclassic')
    testrun.run_command('import _baclassic')
