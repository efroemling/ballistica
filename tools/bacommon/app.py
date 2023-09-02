# Released under the MIT License. See LICENSE for details.
#
"""Common high level values/functionality related to apps."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class AppExperience(Enum):
    """Overall experience that can be provided by a Ballistica app.

    This corresponds generally, but not exactly, to distinct apps built
    with Ballistica. However, a single app may support multiple experiences,
    or there may be multiple apps targeting one experience. Cloud components
    such as leagues are generally associated with an AppExperience.
    """

    # A special experience category that is supported everywhere. Used
    # for the default empty AppMode when starting the app, etc.
    EMPTY = 'empty'

    # The traditional BombSquad experience: multiple players using
    # controllers in a single arena small enough for all action to be
    # viewed on a single screen.
    MELEE = 'melee'

    # The traditional BombSquad Remote experience; buttons on a
    # touch-screen allowing a mobile device to be used as a game
    # controller.
    REMOTE = 'remote'
