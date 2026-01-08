# Released under the MIT License. See LICENSE for details.
#
"""Analytics support."""

from __future__ import annotations

from typing import assert_never, override, Annotated

from enum import Enum, unique
from dataclasses import dataclass

from efro.dataclassio import ioprepped, IOMultiType, IOAttrs


class AnalyticsEventTypeID(Enum):
    """Type ID for each of our subclasses."""

    CLASSIC = 'c'


class AnalyticsEvent(IOMultiType[AnalyticsEventTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> AnalyticsEventTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: AnalyticsEventTypeID) -> type[AnalyticsEvent]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = AnalyticsEventTypeID
        if type_id is t.CLASSIC:
            return ClassicAnalyticsEvent

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class ClassicAnalyticsEvent(AnalyticsEvent):
    """Analytics event related to classic."""

    @unique
    class EventType(Enum):
        """Types of classic events."""

        JOIN_PUBLIC_PARTY = 'jpb'
        JOIN_PRIVATE_PARTY = 'jpr'
        JOIN_PARTY_BY_ADDRESS = 'ja'
        JOIN_NEARBY_PARTY = 'jn'
        START_TEAMS_SESSION = 'st'
        START_FFA_SESSION = 'sf'
        START_COOP_SESSION = 'sc'
        START_TOURNEY_COOP_SESSION = 'stc'

    eventtype: Annotated[EventType, IOAttrs('t')]
    extra: Annotated[str | None, IOAttrs('e', store_default=False)] = None

    @override
    @classmethod
    def get_type_id(cls) -> AnalyticsEventTypeID:
        return AnalyticsEventTypeID.CLASSIC
