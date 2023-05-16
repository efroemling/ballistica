# Released under the MIT License. See LICENSE for details.
#
"""Testing asset manager functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
import weakref
import tempfile
from pathlib import Path


from bacommon.assets import AssetPackageFlavor

# import pytest

if TYPE_CHECKING:
    pass


def test_assetmanager() -> None:
    """Testing."""

    # Disabling for now...
    if bool(False):
        # noinspection PyProtectedMember
        from babase._assetmanager import AssetManager

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AssetManager(rootdir=Path(tmpdir))
            wref = weakref.ref(manager)
            manager.start()
            gather = manager.launch_gather(
                packages=['a@2'],
                flavor=AssetPackageFlavor.DESKTOP,
                account_token='dummytoken',
            )
            wref2 = weakref.ref(gather)

            manager.stop()

            # Make sure nothing is keeping itself alive.
            del manager
            del gather
            assert wref() is None
            assert wref2() is None
