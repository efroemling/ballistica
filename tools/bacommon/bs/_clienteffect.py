# Released under the MIT License. See LICENSE for details.
#
"""ClientEffect related functionality."""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType


class ClientEffectTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    SCREEN_MESSAGE = 'm'
    SOUND = 's'
    DELAY = 'd'
    CHEST_WAIT_TIME_ANIMATION = 't'
    TICKETS_ANIMATION = 'ta'
    TOKENS_ANIMATION = 'toa'


class ClientEffect(IOMultiType[ClientEffectTypeID]):
    """Something that can happen on the client.

    This can include screen messages, sounds, visual effects, etc.
    """

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ClientEffectTypeID) -> type[ClientEffect]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import
        # pylint: disable=too-many-return-statements

        t = ClientEffectTypeID
        if type_id is t.UNKNOWN:
            return ClientEffectUnknown
        if type_id is t.SCREEN_MESSAGE:
            return ClientEffectScreenMessage
        if type_id is t.SOUND:
            return ClientEffectSound
        if type_id is t.DELAY:
            return ClientEffectDelay
        if type_id is t.CHEST_WAIT_TIME_ANIMATION:
            return ClientEffectChestWaitTimeAnimation
        if type_id is t.TICKETS_ANIMATION:
            return ClientEffectTicketsAnimation
        if type_id is t.TOKENS_ANIMATION:
            return ClientEffectTokensAnimation

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> ClientEffect:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return ClientEffectUnknown()


@ioprepped
@dataclass
class ClientEffectUnknown(ClientEffect):
    """Fallback substitute for types we don't recognize."""

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.UNKNOWN


@ioprepped
@dataclass
class ClientEffectScreenMessage(ClientEffect):
    """Display a screen-message."""

    message: Annotated[str, IOAttrs('m')]
    subs: Annotated[list[str], IOAttrs('s')] = field(default_factory=list)
    color: Annotated[tuple[float, float, float], IOAttrs('c')] = (1.0, 1.0, 1.0)

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.SCREEN_MESSAGE


@ioprepped
@dataclass
class ClientEffectSound(ClientEffect):
    """Play a sound."""

    class Sound(Enum):
        """Sounds that can be made alongside the message."""

        UNKNOWN = 'u'
        CASH_REGISTER = 'c'
        ERROR = 'e'
        POWER_DOWN = 'p'
        GUN_COCKING = 'g'

    sound: Annotated[Sound, IOAttrs('s', enum_fallback=Sound.UNKNOWN)]
    volume: Annotated[float, IOAttrs('v')] = 1.0

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.SOUND


@ioprepped
@dataclass
class ClientEffectChestWaitTimeAnimation(ClientEffect):
    """Animate chest wait time changing."""

    chestid: Annotated[str, IOAttrs('c')]
    duration: Annotated[float, IOAttrs('u')]
    startvalue: Annotated[datetime.datetime, IOAttrs('o')]
    endvalue: Annotated[datetime.datetime, IOAttrs('n')]

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.CHEST_WAIT_TIME_ANIMATION


@ioprepped
@dataclass
class ClientEffectTicketsAnimation(ClientEffect):
    """Animate tickets count."""

    duration: Annotated[float, IOAttrs('u')]
    startvalue: Annotated[int, IOAttrs('s')]
    endvalue: Annotated[int, IOAttrs('e')]

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.TICKETS_ANIMATION


@ioprepped
@dataclass
class ClientEffectTokensAnimation(ClientEffect):
    """Animate tokens count."""

    duration: Annotated[float, IOAttrs('u')]
    startvalue: Annotated[int, IOAttrs('s')]
    endvalue: Annotated[int, IOAttrs('e')]

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.TOKENS_ANIMATION


@ioprepped
@dataclass
class ClientEffectDelay(ClientEffect):
    """Delay effect processing."""

    seconds: Annotated[float, IOAttrs('s')]

    @override
    @classmethod
    def get_type_id(cls) -> ClientEffectTypeID:
        return ClientEffectTypeID.DELAY
