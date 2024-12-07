# Released under the MIT License. See LICENSE for details.
#
"""Testing asset manager functionality."""

from __future__ import annotations

import os
import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_imports() -> None:
    """Test imports for our featureset."""

    # Make sure our package and binary module can be cleanly imported by
    # themselves.
    apprun.python_command('import baclassic', purpose='import testing')
    apprun.python_command('import _baclassic', purpose='import testing')
