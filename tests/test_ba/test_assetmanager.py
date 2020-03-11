# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Testing asset manager functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
import weakref
import tempfile
from pathlib import Path
# noinspection PyProtectedMember
from ba._assetmanager import AssetManager

from bacommon.assets import AssetPackageFlavor

# import pytest

if TYPE_CHECKING:
    pass


def test_assetmanager() -> None:
    """Testing."""

    with tempfile.TemporaryDirectory() as tmpdir:
        man = AssetManager(rootdir=Path(tmpdir))
        wref = weakref.ref(man)

        gather = man.launch_gather(packages=['a@2'],
                                   flavor=AssetPackageFlavor.DESKTOP,
                                   account_token='dummytoken')
        wref2 = weakref.ref(gather)

        # Make sure nothing is keeping itself alive
        del man
        del gather
        assert wref() is None
        assert wref2() is None
