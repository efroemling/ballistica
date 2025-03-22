# Released under the MIT License. See LICENSE for details.
#
"""Functionality for wrangling locale info."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Locale(Enum):
    """A distinct combination of language and possibly country/etc.

    Note that some locales here may be superseded by other more specific
    ones (for instance PORTUGUESE -> PORTUGUESE_BRAZIL), but the
    originals must continue to exist here since they may remain in use
    in the wild.
    """

    ENGLISH = 'en'
