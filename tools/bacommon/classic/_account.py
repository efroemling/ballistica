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
class ClassicPlayerProfile:
    """A *cloud profile*: a player profile stored on the v2 master server.

    Mirrors the shape of the client's local (*legacy*) ``Player
    Profiles`` config entries: a character appearance name plus the
    two tint colors and an optional icon glyph. The profile's name is
    the key it is stored under, not a field here. Authored and edited
    through the cloud-rendered inventory UI; delivered to game hosts
    with v2-auth so a joiner's profiles come from the server rather
    than from the joiner.
    """

    character: Annotated[str, IOAttrs('c')]
    color: Annotated[tuple[float, float, float], IOAttrs('cl')]
    highlight: Annotated[tuple[float, float, float], IOAttrs('h')]
    #: Icon glyph shown beside the name (a purchased icon's special
    #: char, or empty for none).
    icon: Annotated[str, IOAttrs('i', store_default=False)] = ''


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

    store_style: Annotated[
        StoreStyle, IOAttrs('s', enum_fallback=StoreStyle.NORMAL)
    ]
