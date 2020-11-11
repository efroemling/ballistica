# Released under the MIT License. See LICENSE for details.
#
"""Error related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class RemoteError(Exception):
    """An error occurred on the other end of some connection."""

    def __str__(self) -> str:
        s = ''.join(str(arg) for arg in self.args)
        return f'Remote Exception Follows:\n{s}'
