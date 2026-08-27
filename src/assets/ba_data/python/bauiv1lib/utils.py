# Released under the MIT License. See LICENSE for details.
#
"""Useful bits to use with UIs."""

from typing import TYPE_CHECKING

import bauiv1 as bui
from bauiv1 import classicassets
from bauiv1 import builtinassets

if TYPE_CHECKING:
    pass


def get_screen_margins(root_scale: float) -> tuple[float, float, float, float]:
    """Return visible-screen margins outside the virtual rect.

    Returns ``(left, right, bottom, top)`` distances between the
    virtual rect edges and the virtual outer rect (true visible area)
    edges, converted into a window's local coordinate space via its
    root container's ``root_scale``. All values are zero unless the
    virtual bounds are inset (camera cutouts and such).

    Windows that fill the screen at small ui-scale should extend
    backing elements such as scroll areas outward by these amounts
    (insetting their content by the same amounts so it stays put) so
    the backing reaches the true screen edges instead of stopping at
    the virtual rect.
    """
    outer = bui.get_virtual_outer_rect()
    vsize = bui.get_virtual_screen_size()
    return (
        max(0.0, 0.0 - outer[0]) / root_scale,
        max(0.0, outer[2] - vsize[0]) / root_scale,
        max(0.0, 0.0 - outer[1]) / root_scale,
        max(0.0, outer[3] - vsize[1]) / root_scale,
    )


def scroll_fade_top(
    container: bui.Widget,
    scrollleft: float,
    scrollbottom: float,
    scrollwidth: float,
    scrollheight: float,
    *,
    yscale: float = 1.0,
    yoffs_extra: float = 0.0,
) -> None:
    """Make content appear to fade towards the top of a scroll area.

    This works by drawing background-texture-ish soft shapes obscuring
    the edge of the scroll area. The most opaque part of the shapes
    lands on the top edge of the provided scroll rect; use
    ``yoffs_extra`` to nudge them up or down from there (e.g. to
    center them on a title above the scroll area).
    """
    return _scroll_fade(
        container,
        scrollleft,
        scrollbottom,
        scrollwidth,
        scrollheight,
        yoffs=scrollheight + yoffs_extra,
        center=True,
        yscale=yscale,
    )


def scroll_fade_bottom(
    container: bui.Widget,
    scrollleft: float,
    scrollbottom: float,
    scrollwidth: float,
    scrollheight: float,
    *,
    center: bool = False,
    yscale: float = 1.0,
    yoffs_extra: float = 0.0,
) -> None:
    """Make content appear to fade towards the bottom of a scroll area.

    This works by drawing background-texture-ish soft shapes obscuring
    the edge of the scroll area. The most opaque part of the shapes
    lands on the bottom edge of the provided scroll rect; use
    ``yoffs_extra`` to nudge them up or down from there (e.g. to
    center them on a note below the scroll area).
    """
    return _scroll_fade(
        container,
        scrollleft,
        scrollbottom,
        scrollwidth,
        scrollheight,
        yoffs=yoffs_extra,
        center=center,
        yscale=yscale,
    )


def _scroll_fade(
    container: bui.Widget,
    scrollleft: float,
    scrollbottom: float,
    scrollwidth: float,
    scrollheight: float,
    *,
    yoffs: float,
    center: bool,
    yscale: float,
) -> None:

    del scrollheight  # Unused.

    clr = (0.4, 0.37, 0.49)
    # clr = (1, 0, 0)

    blotchwidth = scrollwidth * 0.57
    blotchheight = scrollwidth * 0.23
    bimg = bui.imagewidget(
        parent=container,
        texture=builtinassets.textures.ui_atlas.get(),
        mesh_transparent=classicassets.meshes.window_bgblotch.get(),
        position=(
            scrollleft + 60.0 - blotchwidth * 0.5,
            scrollbottom + yoffs - yscale * blotchheight * 0.5,
        ),
        size=(blotchwidth, yscale * blotchheight),
        color=clr,
    )
    bui.widget(edit=bimg, depth_range=(0.9, 1.0))
    bimg = bui.imagewidget(
        parent=container,
        texture=builtinassets.textures.ui_atlas.get(),
        mesh_transparent=classicassets.meshes.window_bgblotch.get(),
        position=(
            scrollleft + scrollwidth - 60.0 - blotchwidth * 0.5,
            scrollbottom + yoffs - yscale * blotchheight * 0.5,
        ),
        size=(blotchwidth, yscale * blotchheight),
        color=clr,
    )
    bui.widget(edit=bimg, depth_range=(0.9, 1.0))

    if center:
        bimg = bui.imagewidget(
            parent=container,
            texture=builtinassets.textures.ui_atlas.get(),
            mesh_transparent=classicassets.meshes.window_bgblotch.get(),
            position=(
                scrollleft + scrollwidth * 0.5 - blotchwidth * 0.5,
                scrollbottom + yoffs - yscale * blotchheight * 0.5,
            ),
            size=(blotchwidth, yscale * blotchheight),
            color=clr,
        )
        bui.widget(edit=bimg, depth_range=(0.9, 1.0))
