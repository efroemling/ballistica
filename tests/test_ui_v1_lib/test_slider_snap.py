# Released under the MIT License. See LICENSE for details.
#
"""Tests for bauiv1.snap_slider_value."""

import importlib.util

import pytest

# Client ui modules need the engine binary module (or its dummy);
# skip where neither is around rather than fail.
pytestmark = pytest.mark.skipif(
    importlib.util.find_spec('_babase') is None,
    reason='client ui modules need the engine binary module',
)


def test_snap_slider_value() -> None:
    """Widget values come back at grid points in decimal form."""
    from bauiv1 import snap_slider_value

    # The single-precision form of 16 * 0.05 that the widget reports.
    assert snap_slider_value(
        0.800000011920929, min_value=0.0, max_value=1.0, increment=0.05
    ) == pytest.approx(0.8, abs=0.0)
    assert (
        repr(
            snap_slider_value(
                0.800000011920929, min_value=0.0, max_value=1.0, increment=0.05
            )
        )
        == '0.8'
    )
    # Off-grid values land on the nearest point; the range clamps.
    assert (
        snap_slider_value(0.83, min_value=0.0, max_value=1.0, increment=0.05)
        == 0.85
    )
    assert (
        snap_slider_value(1.2, min_value=0.0, max_value=1.0, increment=0.05)
        == 1.0
    )
    assert (
        snap_slider_value(-3.0, min_value=0.0, max_value=1.0, increment=0.05)
        == 0.0
    )
    # Grids need not start at zero, and no grid means clamp only.
    assert (
        snap_slider_value(1.26, min_value=0.5, max_value=2.0, increment=0.25)
        == 1.25
    )
    assert (
        snap_slider_value(0.123, min_value=0.0, max_value=1.0, increment=0.0)
        == 0.123
    )
