# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to classic tournament play."""

from __future__ import annotations

from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    from typing import Any


def get_tournament_prize_strings(entry: dict[str, Any]) -> list[str]:
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
    for rng, prize, trophy_type in (
        (range1, prize1, trophy_type_1),
        (range2, prize2, trophy_type_2),
        (range3, prize3, trophy_type_3),
    ):
        prval = (
            ''
            if rng is None
            else ('#' + str(rng[0]))
            if (rng[0] == rng[1])
            else ('#' + str(rng[0]) + '-' + str(rng[1]))
        )
        pvval = ''
        if trophy_type is not None:
            pvval += get_trophy_string(trophy_type)

        # If we've got trophies but not for this entry, throw some space
        # in to compensate so the ticket counts line up.
        if prize is not None:
            pvval = (
                babase.charstr(babase.SpecialChar.TICKET_BACKING)
                + str(prize)
                + pvval
            )
        out_vals.append(prval)
        out_vals.append(pvval)
    return out_vals
