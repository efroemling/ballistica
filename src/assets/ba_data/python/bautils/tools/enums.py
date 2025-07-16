# Released under the MIT License. See LICENSE for details.
#
"""Collection of useful enums for various plugins."""

# ba_meta require api 9

from enum import Enum
from typing import override


class Color(Enum):
    """Collection of RGB colour values."""

    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    PINK = (255, 192, 203)
    BROWN = (165, 42, 42)
    GREY = (128, 128, 128)
    LIGHT_GREY = (211, 211, 211)
    DARK_GREY = (64, 64, 64)
    LIME = (0, 255, 0)
    TEAL = (0, 128, 128)
    NAVY = (0, 0, 128)
    OLIVE = (128, 128, 0)
    MAROON = (128, 0, 0)
    AQUA = (0, 255, 255)
    SILVER = (192, 192, 192)
    GOLD = (255, 215, 0)
    INDIGO = (75, 0, 130)
    VIOLET = (238, 130, 238)
    BEIGE = (245, 245, 220)
    IVORY = (255, 255, 240)
    TURQUOISE = (64, 224, 208)
    SALMON = (250, 128, 114)
    CORAL = (255, 127, 80)
    KHAKI = (240, 230, 140)
    PLUM = (221, 160, 221)
    TAN = (210, 180, 140)

    @override
    def __str__(self) -> str:
        return f"RGB{self.value}"

    @property
    def float(self) -> tuple[float, float, float]:
        """Returns the floating tuple for rgb colors."""
        r, g, b = self.value
        return (r / 255, g / 255, b / 255)
