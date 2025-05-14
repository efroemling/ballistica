# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to cloud based assets."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


# NOTE TO SELF:
# Whenever adding login types here, make sure to update all
# basn nodes before trying to send values through to bamaster,
# as they need to be extractable by basn en route.


class LoginType(Enum):
    """Types of logins available."""

    #: Email/password
    EMAIL = 'email'

    #: Google Play Game Services
    GPGS = 'gpgs'

    #: Apple's Game Center
    GAME_CENTER = 'game_center'

    @property
    def displayname(self) -> str:
        """A human readable name for this value."""
        cls = type(self)
        match self:
            case cls.EMAIL:
                return 'Email/Password'
            case cls.GPGS:
                return 'Google Play Games'
            case cls.GAME_CENTER:
                return 'Game Center'

    @property
    def displaynameshort(self) -> str:
        """A short human readable name for this value."""
        cls = type(self)
        match self:
            case cls.EMAIL:
                return 'Email'
            case cls.GPGS:
                return 'GPGS'
            case cls.GAME_CENTER:
                return 'Game Center'
