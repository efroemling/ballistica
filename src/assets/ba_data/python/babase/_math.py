# Released under the MIT License. See LICENSE for details.
#
"""Math related functionality."""

from __future__ import annotations

from collections import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Sequence


def vec3validate(value: Sequence[float]) -> Sequence[float]:
    """Ensure a value is valid for use as a Vec3.

    Raises a TypeError exception if not. Valid values include any type
    of sequence consisting of 3 numeric values. Returns the same value
    as passed in (but with a definite type so this can be used to
    disambiguate 'Any' types). Generally this should be used in 'if
    __debug__' or assert clauses to keep runtime overhead minimal.

    :meta private:
    """
    from numbers import Number

    if not isinstance(value, abc.Sequence):
        raise TypeError(f"Expected a sequence; got {type(value)}")
    if len(value) != 3:
        raise TypeError(f"Expected a length-3 sequence (got {len(value)})")
    if not all(isinstance(i, Number) for i in value):
        raise TypeError(f"Non-numeric value passed for vec3: {value}")
    return value


def is_point_in_box(pnt: Sequence[float], box: Sequence[float]) -> bool:
    """Return whether a given point is within a given box.

    For use with standard def boxes (position|rotate|scale).

    :meta private:
    """
    return (
        (abs(pnt[0] - box[0]) <= box[6] * 0.5)
        and (abs(pnt[1] - box[1]) <= box[7] * 0.5)
        and (abs(pnt[2] - box[2]) <= box[8] * 0.5)
    )


def normalized_color(color: Sequence[float]) -> tuple[float, ...]:
    """Scale a color so its largest value is 1.0; useful for coloring lights."""
    color_biased = tuple(max(c, 0.01) for c in color)  # account for black
    mult = 1.0 / max(color_biased)
    return tuple(c * mult for c in color_biased)
