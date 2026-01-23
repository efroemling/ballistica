# Released under the MIT License. See LICENSE for details.
#
"""Display-item related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from efro.util import pairs_from_flat
import bacommon.displayitem as ditm
import bacommon.classic
import bauiv1

if TYPE_CHECKING:
    pass


# FIXME - migrate to use the doc-ui rendering for these instead.
def show_display_item(
    itemwrapper: ditm.Wrapper,
    parent: bauiv1.Widget,
    pos: tuple[float, float],
    width: float,
    debug: bool = False,
) -> None:
    """Create ui to depict a display-item."""
    # pylint: disable=too-many-locals

    # Let's go with 4:3 aspect ratio.
    height = width * 0.75

    # Silent no-op if our parent ui is dead.
    if not parent:
        return

    img: str | None = None
    img_y_offs = 0.0
    text_y_offs = 0.0
    show_text = True

    itemtype = itemwrapper.item.get_type_id()

    if itemtype is ditm.ItemTypeID.TICKETS:
        img = 'tickets'
        img_y_offs = width * 0.11
        text_y_offs = width * -0.15
    elif itemtype is ditm.ItemTypeID.TICKETS_PURPLE:
        img = 'ticketsPurple'
        img_y_offs = width * 0.11
        text_y_offs = width * -0.15
    elif itemtype is ditm.ItemTypeID.TOKENS:
        img = 'coin'
        img_y_offs = width * 0.11
        text_y_offs = width * -0.15
    elif itemtype is ditm.ItemTypeID.CHEST:
        assert isinstance(
            itemwrapper.item, bacommon.classic.ClassicChestDisplayItem
        )
        from baclassic._chest import (
            CHEST_APPEARANCE_DISPLAY_INFOS,
            CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,
        )

        img = None
        show_text = False
        c_info = CHEST_APPEARANCE_DISPLAY_INFOS.get(
            itemwrapper.item.appearance, CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT
        )
        c_size = width * 0.85
        bauiv1.imagewidget(
            parent=parent,
            position=(pos[0] - c_size * 0.5, pos[1] - c_size * 0.5),
            color=c_info.color,
            size=(c_size, c_size),
            texture=bauiv1.gettexture(c_info.texclosed),
            tint_texture=bauiv1.gettexture(c_info.texclosedtint),
            tint_color=c_info.tint,
            tint2_color=c_info.tint2,
        )
    elif (
        itemtype is ditm.ItemTypeID.TEST or itemtype is ditm.ItemTypeID.UNKNOWN
    ):
        pass
    else:
        assert_never(itemtype)

    if debug:
        bauiv1.imagewidget(
            parent=parent,
            position=(
                pos[0] - width * 0.5,
                pos[1] - height * 0.5,
            ),
            size=(width, height),
            texture=bauiv1.gettexture('white'),
            color=(0, 1, 0),
            opacity=0.1,
        )

    imgsize = width * 0.33
    if img is not None:
        bauiv1.imagewidget(
            parent=parent,
            position=(
                pos[0] - imgsize * 0.5,
                pos[1] + img_y_offs - imgsize * 0.5,
            ),
            size=(imgsize, imgsize),
            texture=bauiv1.gettexture(img),
        )
    if show_text:
        subs = itemwrapper.description_subs
        if subs is None:
            subs = []
        bauiv1.textwidget(
            parent=parent,
            position=(pos[0], pos[1] + text_y_offs),
            scale=width * 0.006,
            size=(0, 0),
            text=bauiv1.Lstr(
                translate=('displayItemNames', itemwrapper.description),
                subs=pairs_from_flat(subs),
            ),
            maxwidth=width * 0.9,
            color=(0.0, 1.0, 0.0),
            h_align='center',
            v_align='center',
        )
