# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to classic tournament play."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bacommon.bs import ClassicChestAppearance
import babase
import bauiv1
import bascenev1

from baclassic._chest import (
    CHEST_APPEARANCE_DISPLAY_INFOS,
    CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,
)

if TYPE_CHECKING:
    from typing import Any


def get_tournament_prize_strings(
    entry: dict[str, Any], include_tickets: bool
) -> list[str]:
    """Given a tournament entry, return strings for its prize levels."""
    # pylint: disable=too-many-locals
    from bascenev1 import get_trophy_string

    range1 = entry.get('prizeRange1')
    range2 = entry.get('prizeRange2')
    range3 = entry.get('prizeRange3')
    prize1 = entry.get('prize1')
    prize2 = entry.get('prize2')
    prize3 = entry.get('prize3')
    trophy_type_1 = entry.get('prizeTrophy1')
    trophy_type_2 = entry.get('prizeTrophy2')
    trophy_type_3 = entry.get('prizeTrophy3')
    out_vals = []
    for rng, ticket_prize, trophy_type in (
        (range1, prize1, trophy_type_1),
        (range2, prize2, trophy_type_2),
        (range3, prize3, trophy_type_3),
    ):
        prval = (
            ''
            if rng is None
            else (
                ('#' + str(rng[0]))
                if (rng[0] == rng[1])
                else ('#' + str(rng[0]) + '-' + str(rng[1]))
            )
        )
        pvval = ''
        if trophy_type is not None:
            pvval += get_trophy_string(trophy_type)

        if ticket_prize is not None and include_tickets:
            pvval = (
                babase.charstr(babase.SpecialChar.TICKET_BACKING)
                + str(ticket_prize)
                + pvval
            )
        out_vals.append(prval)
        out_vals.append(pvval)
    return out_vals


def set_tournament_prize_chest_image(
    entry: dict[str, Any], index: int, image: bauiv1.Widget
) -> None:
    """Set image attrs representing a tourney prize chest."""
    ranges = [
        entry.get('prizeRange1'),
        entry.get('prizeRange2'),
        entry.get('prizeRange3'),
    ]
    chests = [
        entry.get('prizeChest1'),
        entry.get('prizeChest2'),
        entry.get('prizeChest3'),
    ]

    assert 0 <= index < 3

    # If tourney doesn't include this prize, just hide the image.
    if ranges[index] is None:
        bauiv1.imagewidget(edit=image, opacity=0.0)
        return

    try:
        appearance = ClassicChestAppearance(chests[index])
    except ValueError:
        appearance = ClassicChestAppearance.DEFAULT
    chestdisplayinfo = CHEST_APPEARANCE_DISPLAY_INFOS.get(
        appearance, CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT
    )
    bauiv1.imagewidget(
        edit=image,
        opacity=1.0,
        color=chestdisplayinfo.color,
        texture=bauiv1.gettexture(chestdisplayinfo.texclosed),
        tint_texture=bauiv1.gettexture(chestdisplayinfo.texclosedtint),
        tint_color=chestdisplayinfo.tint,
        tint2_color=chestdisplayinfo.tint2,
    )


def create_in_game_tournament_prize_image(
    entry: dict[str, Any], index: int, position: tuple[float, float]
) -> None:
    """Create a display for the prize chest (if any) in-game."""
    from bascenev1lib.actor.image import Image

    ranges = [
        entry.get('prizeRange1'),
        entry.get('prizeRange2'),
        entry.get('prizeRange3'),
    ]
    chests = [
        entry.get('prizeChest1'),
        entry.get('prizeChest2'),
        entry.get('prizeChest3'),
    ]

    # If tourney doesn't include this prize, no-op.
    if ranges[index] is None:
        return

    try:
        appearance = ClassicChestAppearance(chests[index])
    except ValueError:
        appearance = ClassicChestAppearance.DEFAULT
    chestdisplayinfo = CHEST_APPEARANCE_DISPLAY_INFOS.get(
        appearance, CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT
    )
    Image(
        # Provide magical extended dict version of texture that Image
        # actor supports.
        texture={
            'texture': bascenev1.gettexture(chestdisplayinfo.texclosed),
            'tint_texture': bascenev1.gettexture(
                chestdisplayinfo.texclosedtint
            ),
            'tint_color': chestdisplayinfo.tint,
            'tint2_color': chestdisplayinfo.tint2,
            'mask_texture': None,
        },
        color=chestdisplayinfo.color + (1.0,),
        position=position,
        scale=(48.0, 48.0),
        transition=Image.Transition.FADE_IN,
        transition_delay=2.0,
    ).autoretain()
