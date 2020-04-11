# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Functionality related to tournament play."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Dict, List, Any


def get_tournament_prize_strings(entry: Dict[str, Any]) -> List[str]:
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

        # If we've got trophies but not for this entry, throw some space
        # in to compensate so the ticket counts line up.
        if prize is not None:
            pvval = _ba.charstr(
                SpecialChar.TICKET_BACKING) + str(prize) + pvval
        out_vals.append(prval)
        out_vals.append(pvval)
    return out_vals
