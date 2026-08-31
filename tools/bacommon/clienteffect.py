# Released under the MIT License. See LICENSE for details.
#
"""ClientEffect related functionality.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

# pylint: disable=protected-access

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType

from bacommon import langstr as langstrmod
from bacommon.langstr import LangStrSpec
from bacommon.assetspec import SoundSpec

if TYPE_CHECKING:
    from typing import Callable

    from bacommon.assetspec import AssetBucketKind

    #: An effect's asset slot: a spec, or the flat index addressing the
    #: same asset through its payload's package manifest.
    type EffectAssetRef = SoundSpec | int

    #: An effect's string slot: a spec, or its flat integer index.
    type LangStrRef = LangStrSpec | int

    #: Return a replacement, or None to leave the slot as it is.
    type LangStrVisitor = Callable[[LangStrRef], 'LangStrRef | None']
    type AssetRefVisitor = Callable[
        [EffectAssetRef, 'AssetBucketKind'], 'EffectAssetRef | None'
    ]

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
    to happen server-side). Pass a LangStrSpec json string and set is_lstr=True
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
    :class:`~bacommon.langstr.LangStrSpec`; the client resolves the referenced
    asset-package(s) in its own locale and decodes before display (see
    :func:`collect_apverids`). Only understood by clients new enough to
    carry the v2 effect machinery — older ones drop it as
    :class:`Unknown` — so gate on engine build or dual-send with a
    legacy form where the message matters.
    """

    #: The message. An ``int`` is the indexed form (see
    #: ``bacommon.langstr._flatindex``), unfolded during
    #: resolve like every other indexed slot.
    message: Annotated[LangStrSpec | int, IOAttrs('m')]
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
    :class:`~bacommon.assetspec.SoundSpec`; the client resolves the
    referenced asset-package before playing (see
    :func:`collect_apverids`). Only understood by clients new enough to
    carry the v2 effect machinery — older ones drop it as
    :class:`Unknown`.
    """

    #: The sound to play. An ``int`` is the indexed form -- a flat index
    #: into the audio domain of the payload's package manifest (see
    #: ``bacommon.assetspec._index``). The client swaps it for a
    #: :class:`~bacommon.assetspec.SoundSpec` while resolving, because
    #: an effect may run long after the manifest that gave the index
    #: meaning is gone.
    sound: Annotated[SoundSpec | int, IOAttrs('s')]
    volume: Annotated[float, IOAttrs('v', store_default=False)] = 1.0

    @override
    @classmethod
    def get_type_id(cls) -> EffectTypeID:
        return EffectTypeID.SOUND_V2


def walk_effects(
    effects: list[Effect],
    *,
    langstr: 'LangStrVisitor | None' = None,
    assetref: 'AssetRefVisitor | None' = None,
) -> None:
    """Visit every language-string and asset ref in a list of effects.

    The effects counterpart of
    :func:`bacommon.docui.walk.walk_page`, and exhaustive in the same
    way: it dispatches on :class:`EffectTypeID` with ``assert_never`` at
    the end, so an effect type that gains a string or asset ref cannot
    quietly go unvisited.

    That mattered here. This started as an ``isinstance`` chain with no
    final else -- the same shape that silently under-reported doc-ui
    pages three times -- and the doc-ui page walk separately reached in
    for :attr:`ScreenMessageV2.message` while ignoring
    :attr:`PlaySoundV2.sound`, so the split between the two walks was
    arbitrary rather than principled. Effects keep their own entry point
    because they travel outside doc-ui too (bacloud responses), but both
    walks now cover their whole surface.

    Either callback may return a replacement, which is what lets one
    traversal serve readers and rewriters alike.
    """
    from bacommon.assetspec import AssetBucketKind

    def _lstr(val: 'LangStrRef') -> 'LangStrRef':
        if langstr is None:
            return val
        out = langstr(val)
        return val if out is None else out

    for effect in effects:
        typeid = effect.get_type_id()
        t = EffectTypeID

        if typeid is t.SCREEN_MESSAGE_V2:
            assert isinstance(effect, ScreenMessageV2)
            effect.message = _lstr(effect.message)

        elif typeid is t.SOUND_V2:
            assert isinstance(effect, PlaySoundV2)
            if assetref is not None:
                out = assetref(effect.sound, AssetBucketKind.AUDIO)
                if out is not None:
                    effect.sound = out

        elif typeid in (
            t.UNKNOWN,
            t.LEGACY_SCREEN_MESSAGE,
            t.SCREEN_MESSAGE,
            t.SOUND,
            t.DELAY,
            t.CHEST_WAIT_TIME_ANIMATION,
            t.TICKETS_ANIMATION,
            t.TOKENS_ANIMATION,
        ):
            # Carry no language-agnostic strings or typed asset refs:
            # the legacy forms hold pre-localized text and bare asset
            # names, and the animations hold only numbers and ids.
            pass

        else:
            assert_never(typeid)


def collect_apverids(effects: list[Effect], acc: set[str]) -> None:
    """Gather every asset-package-version a list of effects references.

    The v2 effect forms are self-describing (name-based ``LangStrSpec`` values
    and typed asset refs), so the packages a client must resolve before
    running the effects are derived by walking them — nothing extra
    rides the wire. Mirrors the doc-ui-v2 pattern.
    """

    def _lstr(val: 'LangStrSpec | int') -> None:
        # A folded index resolves through its payload's manifest, which
        # the caller seeds from separately; it names no package itself.
        if not isinstance(val, int):
            langstrmod.collect_apverids(val, acc)

    def _ref(ref: 'SoundSpec | int', _kind: 'AssetBucketKind') -> None:
        # An indexed ref resolves through its payload's manifest, which
        # the caller seeds from separately; it names no package itself.
        if not isinstance(ref, int):
            acc.add(ref._apverid)

    walk_effects(effects, langstr=_lstr, assetref=_ref)


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
