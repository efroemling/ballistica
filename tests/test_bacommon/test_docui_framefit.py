# Released under the MIT License. See LICENSE for details.
#
"""Testing doc-ui frame size-to-fit geometry."""

import pytest

from bacommon.docui.v2 import HAlign, VAlign
from bacommon.docui.framefit import Bounds, aligned_box, fit_bounds

#: A 20-wide, 10-tall box sitting well away from the origin, so a test
#: that quietly ignores the offset fails instead of passing by luck.
OFFCENTER = Bounds(100.0, 50.0, 120.0, 60.0)


def test_bounds_extents() -> None:
    """Width and height come off the corners."""
    assert OFFCENTER.width == 20.0
    assert OFFCENTER.height == 10.0


def test_bounds_union() -> None:
    """Union is the smallest box containing both."""
    other = Bounds(-5.0, 55.0, 110.0, 200.0)
    assert OFFCENTER.union(other) == Bounds(-5.0, 50.0, 120.0, 200.0)
    # Union is symmetric and absorbs a fully-contained box.
    assert other.union(OFFCENTER) == OFFCENTER.union(other)
    inner = Bounds(105.0, 52.0, 110.0, 55.0)
    assert OFFCENTER.union(inner) == OFFCENTER


def test_fit_centers_without_scaling() -> None:
    """Content smaller than the box is centered, not resized."""
    fit = fit_bounds(OFFCENTER, (100.0, 100.0))
    assert fit.scale == 1.0
    # Offset must land the content's midpoint (110, 55) on the origin.
    assert fit.offset == pytest.approx((-110.0, -55.0))


def test_fit_never_grows() -> None:
    """A box far larger than the content leaves its size alone."""
    assert fit_bounds(OFFCENTER, (10000.0, 10000.0)).scale == 1.0


def test_fit_shrinks_on_the_binding_axis() -> None:
    """Both axes shrink together by the tighter ratio."""
    # Width binds: 20 wide into 10 -> 0.5, which also fits the height.
    assert fit_bounds(OFFCENTER, (10.0, 100.0)).scale == pytest.approx(0.5)
    # Height binds: 10 tall into 2.5 -> 0.25, tighter than width's 0.5.
    assert fit_bounds(OFFCENTER, (10.0, 2.5)).scale == pytest.approx(0.25)


def test_fit_shrunk_content_is_centered() -> None:
    """Shrinking still centers; the two are independent."""
    fit = fit_bounds(OFFCENTER, (10.0, 100.0))
    # Centering offset does not depend on scale.
    assert fit.offset == pytest.approx((-110.0, -55.0))
    # Check the drawn result: content maps to offset-then-scale.
    left = (OFFCENTER.minx + fit.offset[0]) * fit.scale
    right = (OFFCENTER.maxx + fit.offset[0]) * fit.scale
    assert left == pytest.approx(-5.0)
    assert right == pytest.approx(5.0)


@pytest.mark.parametrize(
    'h_align,want_left,want_right',
    [
        (HAlign.LEFT, -50.0, -30.0),
        (HAlign.CENTER, -10.0, 10.0),
        (HAlign.RIGHT, 30.0, 50.0),
    ],
)
def test_fit_h_align(
    h_align: HAlign, want_left: float, want_right: float
) -> None:
    """Unshrunk content sits where the horizontal alignment says."""
    size = (100.0, 100.0)
    fit = fit_bounds(OFFCENTER, size, h_align=h_align)
    assert fit.scale == 1.0
    left = (OFFCENTER.minx + fit.offset[0]) * fit.scale
    right = (OFFCENTER.maxx + fit.offset[0]) * fit.scale
    assert left == pytest.approx(want_left)
    assert right == pytest.approx(want_right)


@pytest.mark.parametrize(
    'v_align,want_bottom,want_top',
    [
        (VAlign.BOTTOM, -50.0, -40.0),
        (VAlign.CENTER, -5.0, 5.0),
        (VAlign.TOP, 40.0, 50.0),
    ],
)
def test_fit_v_align(
    v_align: VAlign, want_bottom: float, want_top: float
) -> None:
    """Unshrunk content sits where the vertical alignment says."""
    size = (100.0, 100.0)
    fit = fit_bounds(OFFCENTER, size, v_align=v_align)
    bottom = (OFFCENTER.miny + fit.offset[1]) * fit.scale
    top = (OFFCENTER.maxy + fit.offset[1]) * fit.scale
    assert bottom == pytest.approx(want_bottom)
    assert top == pytest.approx(want_top)


def test_fit_align_edges_hold_after_shrinking() -> None:
    """A shrunk edge-aligned box still touches that edge.

    The alignment offset is applied before scaling, so it has to be
    divided by the scale to land on the box edge -- this is the case
    that catches getting that backwards.
    """
    size = (10.0, 100.0)
    fit = fit_bounds(OFFCENTER, size, h_align=HAlign.LEFT)
    assert fit.scale == pytest.approx(0.5)
    left = (OFFCENTER.minx + fit.offset[0]) * fit.scale
    assert left == pytest.approx(-5.0)

    fit = fit_bounds(OFFCENTER, size, h_align=HAlign.RIGHT)
    right = (OFFCENTER.maxx + fit.offset[0]) * fit.scale
    assert right == pytest.approx(5.0)


def test_fit_degenerate_content() -> None:
    """Zero-extent content neither divides by zero nor scales."""
    point = Bounds(7.0, 7.0, 7.0, 7.0)
    fit = fit_bounds(point, (10.0, 10.0))
    assert fit.scale == 1.0
    assert fit.offset == pytest.approx((-7.0, -7.0))


def test_fit_zero_size_box() -> None:
    """A zero-size box collapses content rather than misbehaving."""
    fit = fit_bounds(OFFCENTER, (0.0, 0.0))
    assert fit.scale == 0.0
    assert fit.offset == (0.0, 0.0)


@pytest.mark.parametrize(
    'h_align,want_minx',
    [(HAlign.LEFT, 10.0), (HAlign.CENTER, 8.0), (HAlign.RIGHT, 6.0)],
)
def test_aligned_box_horizontal(h_align: HAlign, want_minx: float) -> None:
    """A box is placed relative to its position by its alignment."""
    box = aligned_box((10.0, 0.0), 4.0, 2.0, h_align, VAlign.CENTER)
    assert box.minx == pytest.approx(want_minx)
    assert box.width == pytest.approx(4.0)


@pytest.mark.parametrize(
    'v_align,want_miny',
    [(VAlign.BOTTOM, 10.0), (VAlign.CENTER, 9.0), (VAlign.TOP, 8.0)],
)
def test_aligned_box_vertical(v_align: VAlign, want_miny: float) -> None:
    """Vertical placement mirrors horizontal."""
    box = aligned_box((0.0, 10.0), 4.0, 2.0, HAlign.CENTER, v_align)
    assert box.miny == pytest.approx(want_miny)
    assert box.height == pytest.approx(2.0)


def test_icon_and_label_compose_and_fit() -> None:
    """The case this exists for: an icon beside a label, too big to fit.

    Mirrors how a display-item composes a count with its currency icon
    -- authored side by side in local units with no idea of the final
    size, then centered and shrunk by the frame.
    """
    label = aligned_box((0.0, 0.0), 30.0, 8.0, HAlign.RIGHT, VAlign.CENTER)
    icon = aligned_box((10.0, 0.0), 20.0, 20.0, HAlign.CENTER, VAlign.CENTER)
    content = label.union(icon)

    # Spans the label's left edge to the icon's right edge.
    assert content.minx == pytest.approx(-30.0)
    assert content.maxx == pytest.approx(20.0)
    assert content.width == pytest.approx(50.0)
    assert content.height == pytest.approx(20.0)

    # Into a box half as wide: shrinks by half and centers.
    fit = fit_bounds(content, (25.0, 100.0))
    assert fit.scale == pytest.approx(0.5)
    left = (content.minx + fit.offset[0]) * fit.scale
    right = (content.maxx + fit.offset[0]) * fit.scale
    assert left == pytest.approx(-12.5)
    assert right == pytest.approx(12.5)
