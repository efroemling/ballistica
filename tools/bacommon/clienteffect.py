# Released under the MIT License. See LICENSE for details.
#
"""ClientEffect related functionality.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType


class EffectTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    LEGACY_SCREEN_MESSAGE = 'm'
    SCREEN_MESSAGE = 'sm'
    SOUND = 's'
    DELAY = 'd'
    CHEST_WAIT_TIME_ANIMATION = 't'
    TICKETS_ANIMATION = 'ta'
    TOKENS_ANIMATION = 'toa'


class Effect(IOMultiType[EffectTypeID]):
    """Something that can happen on the client.

    This can include screen messages, sounds, visual effects, etc.
    """

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: EffectTypeID) -> type[Effect]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import
        # pylint: disable=too-many-return-statements

        t = EffectTypeID
        if type_id is t.UNKNOWN:
            return Unknown
        if type_id is t.LEGACY_SCREEN_MESSAGE:
            return LegacyScreenMessage
        if type_id is t.SCREEN_MESSAGE:
            return ScreenMessage
        if type_id is t.SOUND:
            return PlaySound
        if type_id is t.DELAY:
            return Delay
        if type_id is t.CHEST_WAIT_TIME_ANIMATION:
            return ChestWaitTimeAnimation
        if type_id is t.TICKETS_ANIMATION:
            return TicketsAnimation
        if type_id is t.TOKENS_ANIMATION:
            return TokensAnimation

        # Important to make sure we provide all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> Effect:
        # If we encounter some future message type we don't know
        # anything about, drop in a placeholder.
        return Unknown()


@ioprepped
@dataclass
class Unknown(Effect):
    """Fallback substitute for types we don't recognize."""

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.UNKNOWN


@ioprepped
@dataclass
class LegacyScreenMessage(Effect):
    """Display a screen-message (Legacy version).

    This will be processed as an Lstr with translation category
    'serverResponses'.

    When possible, migrate to using :class:`ScreenMessage`.
    """

    message: Annotated[str, IOAttrs('m')]
    subs: Annotated[list[str], IOAttrs('s', store_default=False)] = field(
        default_factory=list
    )
    color: Annotated[
        tuple[float, float, float], IOAttrs('c', store_default=False)
    ] = (1.0, 1.0, 1.0)

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.LEGACY_SCREEN_MESSAGE


@ioprepped
@dataclass
class ScreenMessage(Effect):
    """Display a screen-message.

    Supported on engine build 22606 or newer.

    This version does no translation by default (expecting translation
    to happen server-side). Pass a Lstr json string and set is_lstr=True
    for client-side translation.
    """

    message: Annotated[str, IOAttrs('m')]
    color: Annotated[
        tuple[float, float, float], IOAttrs('c', store_default=False)
    ] = (1.0, 1.0, 1.0)
    is_lstr: Annotated[bool, IOAttrs('l', store_default=False)] = False

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.SCREEN_MESSAGE


class Sound(Enum):
    """Sounds that can be played."""

    UNKNOWN = 'u'
    CASH_REGISTER = 'c'
    ERROR = 'e'
    POWER_DOWN = 'p'
    GUN_COCKING = 'g'


@ioprepped
@dataclass
class PlaySound(Effect):
    """Play a sound."""

    sound: Annotated[Sound, IOAttrs('s', enum_fallback=Sound.UNKNOWN)]
    volume: Annotated[float, IOAttrs('v', store_default=False)] = 1.0

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.SOUND


@ioprepped
@dataclass
class ChestWaitTimeAnimation(Effect):
    """Animate chest wait time changing."""

    chestid: Annotated[str, IOAttrs('c')]
    duration: Annotated[float, IOAttrs('u')]
    startvalue: Annotated[datetime.datetime, IOAttrs('o')]
    endvalue: Annotated[datetime.datetime, IOAttrs('n')]

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.CHEST_WAIT_TIME_ANIMATION


@ioprepped
@dataclass
class TicketsAnimation(Effect):
    """Animate tickets count."""

    duration: Annotated[float, IOAttrs('u')]
    startvalue: Annotated[int, IOAttrs('s')]
    endvalue: Annotated[int, IOAttrs('e')]

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.TICKETS_ANIMATION


@ioprepped
@dataclass
class TokensAnimation(Effect):
    """Animate tokens count."""

    duration: Annotated[float, IOAttrs('u')]
    startvalue: Annotated[int, IOAttrs('s')]
    endvalue: Annotated[int, IOAttrs('e')]

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.TOKENS_ANIMATION


@ioprepped
@dataclass
class Delay(Effect):
    """Delay effect processing."""

    seconds: Annotated[float, IOAttrs('s')]

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.DELAY
