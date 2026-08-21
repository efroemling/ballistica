# Released under the MIT License. See LICENSE for details.
#
"""Geometry for fitting a doc-ui frame's children into its bounds.

Kept apart from the client's prep code on purpose. Fitting splits into
two halves: working out how big each child is, which needs a font and
so only a client can do, and working out where that puts everything,
which is arithmetic. This is the arithmetic half -- no engine, no
measurement, and therefore testable on its own.

See :attr:`bacommon.docui.v2.Frame.size`.
"""

from dataclasses import dataclass
from typing import assert_never

from bacommon.docui.v2 import HAlign, VAlign


@dataclass(frozen=True)
class Bounds:
    """An axis-aligned box in a frame's local units."""

    minx: float
    miny: float
    maxx: float
    maxy: float

    @property
    def width(self) -> float:
        """Horizontal extent."""
        return self.maxx - self.minx

    @property
    def height(self) -> float:
        """Vertical extent."""
        return self.maxy - self.miny

    def union(self, other: Bounds) -> Bounds:
        """Return the smallest box containing both."""
        return Bounds(
            min(self.minx, other.minx),
            min(self.miny, other.miny),
            max(self.maxx, other.maxx),
            max(self.maxy, other.maxy),
        )


@dataclass(frozen=True)
class Fit:
    """How to place content in a frame's box.

    ``offset`` is in the frame's local units and applies *before*
    ``scale``, matching the order the prep transform composes in.
    """

    offset: tuple[float, float]
    scale: float


def fit_bounds(
    content: Bounds,
    size: tuple[float, float],
    h_align: HAlign = HAlign.CENTER,
    v_align: VAlign = VAlign.CENTER,
) -> Fit:
    """Place ``content`` inside a box of ``size`` centered on the origin.

    Shrinks to fit but never grows -- content smaller than the box is
    left at its own size and aligned within it. Both axes shrink
    together by the tighter of the two ratios, so nothing is distorted.
    """
    scale = 1.0
    if content.width > size[0] and content.width > 0.0:
        scale = min(scale, size[0] / content.width)
    if content.height > size[1] and content.height > 0.0:
        scale = min(scale, size[1] / content.height)

    # Guard the divisions below; a zero scale would mean nothing is
    # visible anyway.
    if scale <= 0.0:
        return Fit((0.0, 0.0), scale)

    half_w = size[0] * 0.5
    half_h = size[1] * 0.5

    if h_align is HAlign.LEFT:
        offs_x = -half_w / scale - content.minx
    elif h_align is HAlign.CENTER:
        offs_x = -(content.minx + content.maxx) * 0.5
    elif h_align is HAlign.RIGHT:
        offs_x = half_w / scale - content.maxx
    else:
        assert_never(h_align)

    if v_align is VAlign.BOTTOM:
        offs_y = -half_h / scale - content.miny
    elif v_align is VAlign.CENTER:
        offs_y = -(content.miny + content.maxy) * 0.5
    elif v_align is VAlign.TOP:
        offs_y = half_h / scale - content.maxy
    else:
        assert_never(v_align)

    return Fit((offs_x, offs_y), scale)


def aligned_box(
    position: tuple[float, float],
    width: float,
    height: float,
    h_align: HAlign,
    v_align: VAlign,
) -> Bounds:
    """Return a box of this size placed at position by its alignment.

    Mirrors how the decoration renderers interpret position plus
    alignment, so measured bounds land where the thing will draw.
    """
    if h_align is HAlign.LEFT:
        minx = position[0]
    elif h_align is HAlign.CENTER:
        minx = position[0] - width * 0.5
    elif h_align is HAlign.RIGHT:
        minx = position[0] - width
    else:
        assert_never(h_align)

    if v_align is VAlign.TOP:
        miny = position[1] - height
    elif v_align is VAlign.CENTER:
        miny = position[1] - height * 0.5
    elif v_align is VAlign.BOTTOM:
        miny = position[1]
    else:
        assert_never(v_align)

    return Bounds(minx, miny, minx + width, miny + height)
