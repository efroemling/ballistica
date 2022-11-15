# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to cloud based assets."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class LoginType(Enum):
    """Types of logins available."""

    # Email/password
    EMAIL = 'email'

    # Google Play Game Services
    GPGS = 'gpgs'
