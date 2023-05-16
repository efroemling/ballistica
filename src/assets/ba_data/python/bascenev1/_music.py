# Released under the MIT License. See LICENSE for details.
#
"""Music related bits."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import _bascenev1

if TYPE_CHECKING:
    pass


class MusicType(Enum):
    """Types of music available to play in-game.

    Category: **Enums**

    These do not correspond to specific pieces of music, but rather to
    'situations'. The actual music played for each type can be overridden
    by the game or by the user.
    """

    MENU = 'Menu'
    VICTORY = 'Victory'
    CHAR_SELECT = 'CharSelect'
    RUN_AWAY = 'RunAway'
    ONSLAUGHT = 'Onslaught'
    KEEP_AWAY = 'Keep Away'
    RACE = 'Race'
    EPIC_RACE = 'Epic Race'
    SCORES = 'Scores'
    GRAND_ROMP = 'GrandRomp'
    TO_THE_DEATH = 'ToTheDeath'
    CHOSEN_ONE = 'Chosen One'
    FORWARD_MARCH = 'ForwardMarch'
    FLAG_CATCHER = 'FlagCatcher'
    SURVIVAL = 'Survival'
    EPIC = 'Epic'
    SPORTS = 'Sports'
    HOCKEY = 'Hockey'
    FOOTBALL = 'Football'
    FLYING = 'Flying'
    SCARY = 'Scary'
    MARCHING = 'Marching'


def setmusic(musictype: MusicType | None, continuous: bool = False) -> None:
    """Set the app to play (or stop playing) a certain type of music.

    category: **Gameplay Functions**

    This function will handle loading and playing sound assets as necessary,
    and also supports custom user soundtracks on specific platforms so the
    user can override particular game music with their own.

    Pass None to stop music.

    if 'continuous' is True and musictype is the same as what is already
    playing, the playing track will not be restarted.
    """

    # All we do here now is set a few music attrs on the current globals
    # node. The foreground globals' current playing music then gets fed to
    # the do_play_music call in our music controller. This way we can
    # seamlessly support custom soundtracks in replays/etc since we're being
    # driven purely by node data.
    gnode = _bascenev1.getactivity().globalsnode
    gnode.music_continuous = continuous
    gnode.music = '' if musictype is None else musictype.value
    gnode.music_count += 1
