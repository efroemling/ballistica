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
"""Functionality related to player profiles."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import List, Tuple, Any, Dict, Optional

# NOTE: player color options are enforced server-side for non-pro accounts
# so don't change these or they won't stick...
PLAYER_COLORS = [(1, 0.15, 0.15), (0.2, 1, 0.2), (0.1, 0.1, 1), (0.2, 1, 1),
                 (0.5, 0.25, 1.0), (1, 1, 0), (1, 0.5, 0), (1, 0.3, 0.5),
                 (0.1, 0.1, 0.5), (0.4, 0.2, 0.1), (0.1, 0.35, 0.1),
                 (1, 0.8, 0.5), (0.4, 0.05, 0.05), (0.13, 0.13, 0.13),
                 (0.5, 0.5, 0.5), (1, 1, 1)]


def get_player_colors() -> List[Tuple[float, float, float]]:
    """Return user-selectable player colors."""
    return PLAYER_COLORS


def get_player_profile_icon(profilename: str) -> str:
    """Given a profile name, returns an icon string for it.

    (non-account profiles only)
    """
    from ba._enums import SpecialChar

    appconfig = _ba.app.config
    icon: str
    try:
        is_global = appconfig['Player Profiles'][profilename]['global']
    except KeyError:
        is_global = False
    if is_global:
        try:
            icon = appconfig['Player Profiles'][profilename]['icon']
        except KeyError:
            icon = _ba.charstr(SpecialChar.LOGO)
    else:
        icon = ''
    return icon


def get_player_profile_colors(
    profilename: Optional[str],
    profiles: Dict[str, Dict[str, Any]] = None
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """Given a profile, return colors for them."""
    appconfig = _ba.app.config
    if profiles is None:
        profiles = appconfig['Player Profiles']

    # Special case: when being asked for a random color in kiosk mode,
    # always return default purple.
    if _ba.app.kiosk_mode and profilename is None:
        color = (0.5, 0.4, 1.0)
        highlight = (0.4, 0.4, 0.5)
    else:
        try:
            assert profilename is not None
            color = profiles[profilename]['color']
        except (KeyError, AssertionError):
            # Key off name if possible.
            if profilename is None:
                # First 6 are bright-ish.
                color = PLAYER_COLORS[random.randrange(6)]
            else:
                # First 6 are bright-ish.
                color = PLAYER_COLORS[sum([ord(c) for c in profilename]) % 6]

        try:
            assert profilename is not None
            highlight = profiles[profilename]['highlight']
        except (KeyError, AssertionError):
            # Key off name if possible.
            if profilename is None:
                # Last 2 are grey and white; ignore those or we
                # get lots of old-looking players.
                highlight = PLAYER_COLORS[random.randrange(
                    len(PLAYER_COLORS) - 2)]
            else:
                highlight = PLAYER_COLORS[sum(
                    [ord(c) + 1
                     for c in profilename]) % (len(PLAYER_COLORS) - 2)]

    return color, highlight
