# Released under the MIT License. See LICENSE for details.
#
"""BombSquad specific bits."""

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

        #: How to draw the chest: a :class:`bacommon.depiction.Depiction`
        #: as json, or None to draw by :attr:`appearance`. Only sent to
        #: builds new enough to draw it.
        depiction: Annotated[str | None, IOAttrs('dp', store_default=False)] = (
            None
        )

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
        """Special looks for the store (legacy; builds before 23097).

        Superseded by :attr:`store_decoration`, which builds 23097+
        draw instead (they ignore this). Remove once those older builds
        have aged out.
        """

        NORMAL = 'n'
        SANTA = 's'

    @dataclass
    class StoreDecoration:
        """Seasonal art drawn with the toolbar's store button.

        Placement is fixed by the client for now (peeking over the top
        of the store button); fields such as a position or size can
        join here later without disturbing builds that predate them.
        """

        #: What to draw: a :class:`bacommon.depiction.Depiction` as json
        #: (an :class:`~bacommon.depiction.ImageDepiction` today).
        depiction: Annotated[str, IOAttrs('dp')]

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

    #: State id of our cloud profiles (builds 23014+); None if the
    #: account has none. Clients refetch via
    #: :class:`GetClassicProfilesMessage` when this changes.
    profiles_state: Annotated[str | None, IOAttrs('ps', soft_default=None)]

    #: Fleet-wide classic cache version (builds 23018+). An opaque
    #: string; when it differs from the one cached classic data (cloud
    #: profiles) was fetched under, that cache is stale and gets
    #: refetched in the background. None means unknown (an older basn
    #: node), which never stales anything.
    cache_version: Annotated[str | None, IOAttrs('cv', soft_default=None)]

    #: How the account's name draws (builds 23025+): a
    #: :class:`bacommon.depiction.NameDepiction` as json, shown by the
    #: toolbar's account button in place of its usual art. None (not
    #: baked yet, or an older basn node) keeps the usual button.
    name_depiction: Annotated[str | None, IOAttrs('nd', soft_default=None)]

    flags: Annotated[set[Flag], IOAttrs('f', soft_default_factory=set)]

    #: Legacy store look for builds before 23097 (see
    #: :class:`StoreStyle`); newer builds ignore it.
    store_style: Annotated[
        StoreStyle, IOAttrs('s', enum_fallback=StoreStyle.NORMAL)
    ]

    #: Seasonal art for the store button (builds 23097+), or None for
    #: none. Picked fleet-wide by bamaster (its occasion table) and
    #: passed along by basn.
    store_decoration: Annotated[
        StoreDecoration | None,
        IOAttrs('sd', soft_default=None, store_default=False),
    ]
