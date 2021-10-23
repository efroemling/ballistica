# Released under the MIT License. See LICENSE for details.
#
"""On-screen Keyboard related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Keyboard:
    """Chars definitions for on-screen keyboard.

    Category: App Classes

    Keyboards are discoverable by the meta-tag system
    and the user can select which one they want to use.
    On-screen keyboard uses chars from active ba.Keyboard.
    Attributes:
      name
        Displays when user selecting this keyboard.
      chars
        Used for row/column lengths.
      pages
        Extra chars like emojis.
      nums
        The 'num' page.
    """

    name: str
    chars: list[tuple[str, ...]]
    pages: dict[str, tuple[str, ...]]
    nums: tuple[str, ...]
