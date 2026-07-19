# Released under the MIT License. See LICENSE for details.
#
"""ClientEffect related functionality.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon.langstr import LangStr
from bacommon.assetref import SoundRef

#: First engine build carrying the v2 client-effect machinery
#: (``ScreenMessageV2``/``PlaySoundV2`` + resolve-before-run).
#: Servers use this to emit the right form per client build.
V2_EFFECTS_MIN_BUILD = 22931


class EffectTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    LEGACY_SCREEN_MESSAGE = 'm'
    SCREEN_MESSAGE = 'sm'
    SCREEN_MESSAGE_V2 = 'sm2'
    SOUND = 's'
    SOUND_V2 = 's2'
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
    def get_type_id_storage_name(cls) -> str:
        # Pin to the original default for back-compat with stored data.
        return '_dciotype'

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
        if type_id is t.SCREEN_MESSAGE_V2:
            return ScreenMessageV2
        if type_id is t.SOUND:
            return PlaySound
        if type_id is t.SOUND_V2:
            return PlaySoundV2
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

    This will be processed as a legacy client Lstr with translation category
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
    to happen server-side). Pass a LangStr json string and set is_lstr=True
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


@ioprepped
@dataclass
class ScreenMessageV2(Effect):
    """Display a screen-message (asset-package l-string version).

    The message is a language-agnostic
    :class:`~bacommon.langstr.LangStr`; the client resolves the referenced
    asset-package(s) in its own locale and decodes before display (see
    :func:`collect_apverids`). Only understood by clients new enough to
    carry the v2 effect machinery — older ones drop it as
    :class:`Unknown` — so gate on engine build or dual-send with a
    legacy form where the message matters.
    """

    message: Annotated[LangStr, IOAttrs('m')]
    color: Annotated[
        tuple[float, float, float], IOAttrs('c', store_default=False)
    ] = (1.0, 1.0, 1.0)

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.SCREEN_MESSAGE_V2


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
class PlaySoundV2(Effect):
    """Play a sound from an asset-package.

    Unlike :class:`PlaySound`'s fixed :class:`Sound` set, this can play
    any packaged sound via a typed
    :class:`~bacommon.assetref.SoundRef`; the client resolves the
    referenced asset-package before playing (see
    :func:`collect_apverids`). Only understood by clients new enough to
    carry the v2 effect machinery — older ones drop it as
    :class:`Unknown`.
    """

    sound: Annotated[SoundRef, IOAttrs('s')]
    volume: Annotated[float, IOAttrs('v', store_default=False)] = 1.0

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.SOUND_V2


def collect_apverids(effects: list[Effect], acc: set[str]) -> None:
    """Gather every asset-package-version a list of effects references.

    The v2 effect forms are self-describing (name-based ``LangStr`` values
    and typed asset refs), so the packages a client must resolve before
    running the effects are derived by walking them — nothing extra
    rides the wire. Mirrors the doc-ui-v2 pattern.
    """

    def _walk_lstr(lstr: LangStr) -> None:
        from bacommon.langstr import LangStrResource, LangStrValue

        if isinstance(lstr, LangStrResource):
            acc.add(lstr.apverid)
            subvals = lstr.subs.values()
        elif isinstance(lstr, LangStrValue):
            subvals = lstr.subs.values()
        else:
            # Indexed values resolve against an out-of-band context;
            # they carry no apverids of their own.
            return
        for sub in subvals:
            if isinstance(sub, LangStr):
                _walk_lstr(sub)

    for effect in effects:
        if isinstance(effect, ScreenMessageV2):
            _walk_lstr(effect.message)
        elif isinstance(effect, PlaySoundV2):
            acc.add(effect.sound.apverid)


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
