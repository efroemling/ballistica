# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to net play."""
from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    pass


@dataclass
class HostInfo:
    """Info about a host."""

    name: str
    build_number: int

    # Note this can be None for non-ip hosts such as bluetooth.
    address: str | None

    # Note this can be None for non-ip hosts such as bluetooth.
    port: int | None
