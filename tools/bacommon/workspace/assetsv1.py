# Released under the MIT License. See LICENSE for details.
#
"""Defines workspace behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs


if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class AssetsV1GlobalVals:
    """Global values for an assets_v1 workspace."""

    # Just dummy testing values for now.
    emit: Annotated[bool, IOAttrs('emit')]
    aggro: Annotated[float, IOAttrs('aggro')]


@ioprepped
@dataclass
class AssetsV1PathVals:
    """Path-specific values for an assets_v1 workspace path."""

    # Just dummy testing values for now.
    width: Annotated[int, IOAttrs('width')]
    height: Annotated[int, IOAttrs('height')]
