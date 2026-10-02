# Released under the MIT License. See LICENSE for details.
#
"""Client-side display-item drawing.

The depiction itself lives in :mod:`bacommon.displayitem` so that one
description of how an item looks serves both the client and the
producer. What lives here is the client's half: lending that depiction
the things it cannot reach on its own (see
``bacommon.displayitem.DepictionAssets``), and drawing the resulting
doc-ui decorations into a plain container widget.
"""

from typing import TYPE_CHECKING

from bacommon.displayitem import (
    DisplayItem,
    DisplayItemStyle,
    DepictionAssets,
)
from bauiv1 import _builtinassets
from bauiv1 import _classiccatalogassets

if TYPE_CHECKING:
    import bacommon.docui.v2 as dui2
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
            coin=_classiccatalogassets.textures.coin,
            tickets=_classiccatalogassets.textures.tickets,
            tickets_purple=_classiccatalogassets.textures.tickets_purple,
            chest_icon=_classiccatalogassets.textures.chest_icon,
            chest_icon_tint=_classiccatalogassets.textures.chest_icon_tint,
            chest_tints={
                appearance: (info.tint, info.tint2, info.tint3)
                for appearance, info in CHEST_APPEARANCE_DISPLAY_INFOS.items()
            },
            chest_tint_default=(
                CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT.tint,
                CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT.tint2,
                CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT.tint3,
            ),
        )
    return _g_assets


def display_item_decorations(
    wrapper: lditm.Wrapper,
    *,
    position: tuple[float, float],
    size: tuple[float, float],
    style: DisplayItemStyle,
    debug: bool = False,
    text_color: tuple[float, float, float] | None = None,
    depth_range: tuple[float, float] | None = None,
    highlight: bool = True,
) -> list[dui2.Decoration]:
    """Return decorations depicting a display-item, using client assets.

    Convenience wrapper over
    ``bacommon.displayitem.DisplayItem.decorations`` for client code,
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
    ).decorations(depiction_assets())


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
    from bauiv1lib.docui.prep import prep_decorations_for_container

    # Silent no-op if our parent ui is dead.
    if not parent:
        return

    # Bounds that make the 4:3 style resolve to exactly this width.
    decorations = display_item_decorations(
        itemwrapper,
        position=pos,
        size=(width, width * 0.75),
        style=DisplayItemStyle.FULL,
        debug=debug,
    )

    # Prepping here blocks the ui thread, which is what the prep call
    # warns about -- but this call is synchronous ui construction with
    # no background pass to hang the work off, so the warning would be
    # noise.
    prep_decorations_for_container(
        decorations, packages=[], allow_logic_thread=True
    )(parent)
