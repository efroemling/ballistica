# Released under the MIT License. See LICENSE for details.
#
"""On-screen Keyboard related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Keyboard:
    """Chars definitions for on-screen keyboard.

    Category: **App Classes**

    Keyboards are discoverable by the meta-tag system
    and the user can select which one they want to use.
    On-screen keyboard uses chars from active babase.Keyboard.
    """

    name: str
    """Displays when user selecting this keyboard."""

    chars: list[tuple[str, ...]]
    """Used for row/column lengths."""

    pages: dict[str, tuple[str, ...]]
    """Extra chars like emojis."""

    nums: tuple[str, ...]
    """The 'num' page."""
