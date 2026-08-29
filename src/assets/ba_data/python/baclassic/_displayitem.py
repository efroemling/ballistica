# Released under the MIT License. See LICENSE for details.
#
"""Client-side display-item drawing.

The depiction itself lives in :mod:`bacommon.displayitem` so that one
description of how an item looks serves both the client and the
producer. What lives here is the client's half: lending that depiction
the things it cannot reach on its own (see
``bacommon.displayitem.DepictionAssets``), and drawing the result
into a plain container widget.

See ``docs/initiatives/docui-frames.md``.
"""

from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
from bacommon.displayitem import DisplayItem, DepictionAssets
from bauiv1 import _builtinassets
from bauiv1 import _classicassets

if TYPE_CHECKING:
    import bacommon.legacydisplayitem as lditm
    import bauiv1

_g_assets: DepictionAssets | None = None


def depiction_assets() -> DepictionAssets:
    """Return what this client lends a display-item depiction.

    Built once and reused; the refs and colors it gathers are constant
    for the life of the app.

    :meta private:
    """
    # pylint: disable=global-statement
    global _g_assets
    if _g_assets is None:
        from baclassic._chest import (
            CHEST_APPEARANCE_DISPLAY_INFOS,
            CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,
        )

        _g_assets = DepictionAssets(
            white=_builtinassets.textures.white,
            coin=_classicassets.textures.coin,
            tickets=_classicassets.textures.tickets,
            tickets_purple=_classicassets.textures.tickets_purple,
            chest_icon=_classicassets.textures.chest_icon,
            chest_icon_tint=_classicassets.textures.chest_icon_tint,
            chest_tints={
                appearance: (info.tint, info.tint2)
                for appearance, info in CHEST_APPEARANCE_DISPLAY_INFOS.items()
            },
            chest_tint_default=(
                CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT.tint,
                CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT.tint2,
            ),
        )
    return _g_assets


def display_item_frame(
    wrapper: lditm.Wrapper,
    *,
    position: tuple[float, float],
    size: tuple[float, float],
    style: dui2.DisplayItemStyle,
    debug: bool = False,
    text_color: tuple[float, float, float] | None = None,
    depth_range: tuple[float, float] | None = None,
    highlight: bool = True,
) -> dui2.Frame:
    """Return a frame depicting a display-item, using client assets.

    Convenience wrapper over
    ``bacommon.displayitem.DisplayItem.to_frame`` for client code,
    which always wants this client's own assets.

    :meta private:
    """
    return DisplayItem(
        wrapper=wrapper,
        position=position,
        size=size,
        style=style,
        text_color=text_color,
        highlight=highlight,
        depth_range=depth_range,
        debug=debug,
    ).to_frame(depiction_assets())


def show_display_item(
    itemwrapper: lditm.Wrapper,
    parent: bauiv1.Widget,
    pos: tuple[float, float],
    width: float,
    debug: bool = False,
) -> None:
    """Create ui to depict a display-item.

    Draws the same depiction doc-ui draws, into a plain container
    widget instead of a doc-ui page -- so the two agree by
    construction rather than by two renderers being kept in step.

    :meta private:
    """
    # pylint: disable=cyclic-import
    # Safe up-call: bauiv1lib sits above us and is fully imported by
    # the time any ui is being built.
    from bauiv1lib.docui.prep import prep_frames

    # Silent no-op if our parent ui is dead.
    if not parent:
        return

    # Bounds that make the 4:3 style resolve to exactly this width.
    frame = display_item_frame(
        itemwrapper,
        position=pos,
        size=(width, width * 0.75),
        style=dui2.DisplayItemStyle.FULL,
        debug=debug,
    )

    # Prepping here blocks the ui thread, which is what prep_frames
    # warns about -- but this call is synchronous ui construction with
    # no background pass to hang the work off, so the warning would be
    # noise. See decision F8 in the initiative doc.
    prep_frames([frame], packages=[], allow_logic_thread=True)(parent)
