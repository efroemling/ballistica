# Released under the MIT License. See LICENSE for details.
#
"""Tests for doc-ui layouts' promised content-rect sizes."""

import bacommon.docui.v2 as dui2


def test_content_sizes_relate() -> None:
    """The promised sizes keep their order (the docs lean on it)."""
    # Widths: a narrow viewer's column is narrower than a small layout's,
    # which is narrower than a wide one's.
    assert (
        dui2.NARROW_CONTENT_WIDTH
        < dui2.SMALL_CONTENT_WIDTH
        < dui2.WIDE_CONTENT_WIDTH
    )

    # Heights: small is the least any layout gives; tall ones give more
    # (at medium/large ui-scale).
    assert (
        dui2.SMALL_CONTENT_HEIGHT
        <= dui2.WIDE_CONTENT_HEIGHT
        < dui2.TALL_CONTENT_HEIGHT
    )

    # The wide sizes are the smallest screen's at small ui-scale.
    assert abs(dui2.WIDE_CONTENT_WIDTH - 882.7586) < 0.001
    assert abs(dui2.WIDE_CONTENT_HEIGHT - 357.5517) < 0.001
