# Released under the MIT License. See LICENSE for details.
#
"""Testing asset manager functionality."""

from __future__ import annotations

import pytest

from batools import apprun


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_imports() -> None:
    """Test imports for our featureset."""

    # Make sure our package and binary module can be cleanly imported by
    # themselves.
    apprun.python_command('import baplus', purpose='import testing')
    apprun.python_command('import _baplus', purpose='import testing')
