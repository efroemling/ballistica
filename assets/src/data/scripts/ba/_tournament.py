"""Functionality related to tournament play."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Dict, List, Any


def get_tournament_prize_strings(entry: Dict[str, Any]) -> List:
    """Given a tournament entry, return strings for its prize levels."""
    # pylint: disable=too-many-locals
    from ba._enums import SpecialChar
    from ba._gameutils import get_trophy_string
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
    for rng, prize, trophy_type in ((range1, prize1, trophy_type_1),
                                    (range2, prize2, trophy_type_2),
                                    (range3, prize3, trophy_type_3)):
        prval = ('' if rng is None else ('#' + str(rng[0])) if
                 (rng[0] == rng[1]) else
                 ('#' + str(rng[0]) + '-' + str(rng[1])))
        pvval = ''
        if trophy_type is not None:
            pvval += get_trophy_string(trophy_type)
            # trophy_chars = {
            #     '1': SpecialChar.TROPHY1,
            #     '2': SpecialChar.TROPHY2,
            #     '3': SpecialChar.TROPHY3,
            #     '0a': SpecialChar.TROPHY0A,
            #     '0b': SpecialChar.TROPHY0B,
            #     '4': SpecialChar.TROPHY4
            # }
            # if trophy_type in trophy_chars:
            #     pvval += _bs.specialchar(trophy_chars[trophy_type])
            # else:
            #     from ba import err
            #     err.print_error(
            #         f"unrecognized trophy type: {trophy_type}", once=True)
        # if we've got trophies but not for this entry, throw some space
        # in to compensate so the ticket counts line up
        if prize is not None:
            pvval = _ba.charstr(
                SpecialChar.TICKET_BACKING) + str(prize) + pvval
        out_vals.append(prval)
        out_vals.append(pvval)
    return out_vals
