# Released under the MIT License. See LICENSE for details.
#
"""Display-item related functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

from efro.util import pairs_from_flat
import bacommon.bs
import bauiv1


if TYPE_CHECKING:
    pass


def show_display_item(
    itemwrapper: bacommon.bs.DisplayItemWrapper,
    parent: bauiv1.Widget,
    pos: tuple[float, float],
    width: float,
) -> None:
    """Create ui to depict a display-item."""

    height = width * 0.666

    # Silent no-op if our parent ui is dead.
    if not parent:
        return

    img: str | None = None
    img_y_offs = 0.0
    text_y_offs = 0.0
    show_text = True

    if isinstance(itemwrapper.item, bacommon.bs.TicketsDisplayItem):
        img = 'tickets'
        img_y_offs = width * 0.11
        text_y_offs = width * -0.15
    elif isinstance(itemwrapper.item, bacommon.bs.TokensDisplayItem):
        img = 'coin'
        img_y_offs = width * 0.11
        text_y_offs = width * -0.15
    elif isinstance(itemwrapper.item, bacommon.bs.ChestDisplayItem):
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

    # Enable this for testing spacing.
    if bool(False):
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
                translate=('serverResponses', itemwrapper.description),
                subs=pairs_from_flat(subs),
            ),
            maxwidth=width * 0.9,
            color=(0.0, 1.0, 0.0),
            h_align='center',
            v_align='center',
        )
