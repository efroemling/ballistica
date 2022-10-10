# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to player profiles."""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any

# NOTE: player color options are enforced server-side for non-pro accounts
# so don't change these or they won't stick...
PLAYER_COLORS = [
    (1, 0.15, 0.15),
    (0.2, 1, 0.2),
    (0.1, 0.1, 1),
    (0.2, 1, 1),
    (0.5, 0.25, 1.0),
    (1, 1, 0),
    (1, 0.5, 0),
    (1, 0.3, 0.5),
    (0.1, 0.1, 0.5),
    (0.4, 0.2, 0.1),
    (0.1, 0.35, 0.1),
    (1, 0.8, 0.5),
    (0.4, 0.05, 0.05),
    (0.13, 0.13, 0.13),
    (0.5, 0.5, 0.5),
    (1, 1, 1),
]


def get_player_colors() -> list[tuple[float, float, float]]:
    """Return user-selectable player colors."""
    return PLAYER_COLORS


def get_player_profile_icon(profilename: str) -> str:
    """Given a profile name, returns an icon string for it.

    (non-account profiles only)
    """
    from ba._generated.enums import SpecialChar

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
    profilename: str | None, profiles: dict[str, dict[str, Any]] | None = None
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Given a profile, return colors for them."""
    appconfig = _ba.app.config
    if profiles is None:
        profiles = appconfig['Player Profiles']

    # Special case: when being asked for a random color in kiosk mode,
    # always return default purple.
    if (_ba.app.demo_mode or _ba.app.arcade_mode) and profilename is None:
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
                color = PLAYER_COLORS[sum(ord(c) for c in profilename) % 6]

        try:
            assert profilename is not None
            highlight = profiles[profilename]['highlight']
        except (KeyError, AssertionError):
            # Key off name if possible.
            if profilename is None:
                # Last 2 are grey and white; ignore those or we
                # get lots of old-looking players.
                highlight = PLAYER_COLORS[
                    random.randrange(len(PLAYER_COLORS) - 2)
                ]
            else:
                highlight = PLAYER_COLORS[
                    sum(ord(c) + 1 for c in profilename)
                    % (len(PLAYER_COLORS) - 2)
                ]

    return color, highlight
