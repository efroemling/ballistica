# Released under the MIT License. See LICENSE for details.
#
"""BombSquad specific bits."""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Annotated

from efro.dataclassio import ioprepped, IOAttrs
from bacommon.classic._chest import ClassicChestAppearance


@ioprepped
@dataclass
class ClassicLiveAccountClientData:
    """Live account data fed to the client in the bs classic app mode."""

    @dataclass
    class Chest:
        """A lovely chest."""

        appearance: Annotated[
            ClassicChestAppearance,
            IOAttrs('a', enum_fallback=ClassicChestAppearance.UNKNOWN),
        ]
        create_time: Annotated[datetime.datetime, IOAttrs('c')]
        unlock_time: Annotated[datetime.datetime, IOAttrs('t')]
        unlock_tokens: Annotated[int, IOAttrs('k')]
        ad_allow_time: Annotated[datetime.datetime | None, IOAttrs('at')]

    class LeagueType(Enum):
        """Type of league we are in."""

        BRONZE = 'b'
        SILVER = 's'
        GOLD = 'g'
        DIAMOND = 'd'

    class Flag(Enum):
        """Flags set for our account."""

        ASK_FOR_REVIEW = 'r'

    class StoreStyle(Enum):
        """Special looks for the store."""

        NORMAL = 'n'
        SANTA = 's'

    tickets: Annotated[int, IOAttrs('ti')]

    tokens: Annotated[int, IOAttrs('to')]
    gold_pass: Annotated[bool, IOAttrs('g')]
    remove_ads: Annotated[bool, IOAttrs('r')]

    achievements: Annotated[int, IOAttrs('a')]
    achievements_total: Annotated[int, IOAttrs('at')]

    league_type: Annotated[LeagueType | None, IOAttrs('lt')]
    league_num: Annotated[int | None, IOAttrs('ln')]
    league_rank: Annotated[int | None, IOAttrs('lr')]

    level: Annotated[int, IOAttrs('lv')]
    xp: Annotated[int, IOAttrs('xp')]
    xpmax: Annotated[int, IOAttrs('xpm')]

    inbox_count: Annotated[int, IOAttrs('ibc')]
    inbox_count_is_max: Annotated[bool, IOAttrs('ibcm')]
    inbox_contains_prize: Annotated[bool, IOAttrs('icp')]

    chests: Annotated[dict[str, Chest], IOAttrs('c')]

    # State id of our purchases for builds 22459+.
    purchases_state: Annotated[str | None, IOAttrs('p')]

    flags: Annotated[set[Flag], IOAttrs('f', soft_default_factory=set)]

    store_style: Annotated[
        StoreStyle, IOAttrs('s', enum_fallback=StoreStyle.NORMAL)
    ]
