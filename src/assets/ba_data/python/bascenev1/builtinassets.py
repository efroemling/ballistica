# Released under the MIT License. See LICENSE for details.
#
"""Asset-package wrapper for ``a-0.bastdassets.260513a`` (bascenev1).

Auto-generated; do not edit by hand.
"""

# ba_meta require asset-package a-0.bastdassets.260513a
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bascenev1

__asset_package__ = 'a-0.bastdassets.260513a'
_APVERID = __asset_package__


class _Mydir:
    @property
    def helloworld(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:mydir/helloworld')


mydir = _Mydir()
