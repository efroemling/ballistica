# Released under the MIT License. See LICENSE for details.
#
"""Useful bits to use with UIs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    pass


def scroll_fade_top(
    container: bui.Widget,
    scrollleft: float,
    scrollbottom: float,
    scrollwidth: float,
    scrollheight: float,
    *,
    yscale: float = 1.0,
) -> None:
    """Make content appear to fade towards the top of a scroll area.

    This works by drawing background-texture-ish soft shapes obscuring
    the edge of the scroll area.
    """
    return _scroll_fade(
        container,
        scrollleft,
        scrollbottom,
        scrollwidth,
        scrollheight,
        yoffs=scrollheight,
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
) -> None:
    """Make content appear to fade towards the bottom of a scroll area.

    This works by drawing background-texture-ish soft shapes obscuring
    the edge of the scroll area.
    """
    return _scroll_fade(
        container,
        scrollleft,
        scrollbottom,
        scrollwidth,
        scrollheight,
        yoffs=0.0,
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
        texture=bui.gettexture('uiAtlas'),
        mesh_transparent=bui.getmesh('windowBGBlotch'),
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
        texture=bui.gettexture('uiAtlas'),
        mesh_transparent=bui.getmesh('windowBGBlotch'),
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
            texture=bui.gettexture('uiAtlas'),
            mesh_transparent=bui.getmesh('windowBGBlotch'),
            position=(
                scrollleft + scrollwidth * 0.5 - blotchwidth * 0.5,
                scrollbottom + yoffs - yscale * blotchheight * 0.5,
            ),
            size=(blotchwidth, yscale * blotchheight),
            color=clr,
        )
        bui.widget(edit=bimg, depth_range=(0.9, 1.0))
