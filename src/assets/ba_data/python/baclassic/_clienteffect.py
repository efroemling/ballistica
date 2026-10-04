# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to running client-effects from the master server."""

import asyncio
import logging
import weakref
from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, assert_never

from efro.util import strict_partial, strip_exception_tracebacks
from bacommon.logging import ClientLoggerName

import bauiv1

import _baclassic

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    import bacommon.clienteffect as clfx
    from bacommon.langstr import LanguageStringNameDecodeContext

#: How long we wait on the asset-package resolve for v2 effects before
#: giving up (effects are decorative; skipping beats hanging).
_RESOLVE_TIMEOUT_SECONDS = 30.0

assetslog = logging.getLogger(ClientLoggerName.ASSETS.value)

#: Keyframe animations with interpolation currently running (kept here
#: so they stay alive until done).
_g_running_animations: set[_InterpolatedAnimation] = set()


class EffectTarget(Protocol):
    """Something client-effects can animate.

    Implemented by whatever UI system the effects run alongside (a
    doc-ui window's widgets, say); effects know nothing about it beyond
    this.
    """

    def set_animation_state(
        self,
        *,
        offset: tuple[float, float],
        scale: float,
        opacity: float | None,
    ) -> None:
        """Show the target offset and scaled from its rest state.

        ``opacity`` is absolute; None for its resting opacity.
        """


class EffectTargets(Protocol):
    """A set of animatable targets client-effects can look up by id."""

    def get_target(self, target_id: str) -> EffectTarget | None:
        """Return the target for an id, if there is a live one."""


@dataclass
class ClientEffectContext:
    """What client-effects are running alongside, if anything.

    Effects that need a context (animating things, say) do nothing
    without the relevant piece.
    """

    #: Targets for ``bacommon.clienteffect.KeyframeAnimation``.
    targets: EffectTargets | None = None


def run_bs_client_effects(
    effects: list[clfx.Effect],
    delay: float = 0.0,
    context: ClientEffectContext | None = None,
) -> None:
    """Run effects."""
    import bacommon.clienteffect as clfx

    # V2 effect forms reference asset-packages (l-string text, sound
    # refs). Those need resolving — possibly downloading — before the
    # effects can run; kick that off and run once ready. Effects with
    # no package refs run immediately as always.
    # Animation targets sit at their first key's state until their
    # animation starts; put them there now rather than after any
    # resolve below, so something laid out to appear later doesn't
    # flash up first.
    if context is not None and context.targets is not None:
        _apply_first_keys(effects, context.targets)

    apvernums: set[ApverNum] = set()
    clfx.collect_apvernums(effects, apvernums)
    if not apvernums:
        _run_effects(effects, delay=delay, context=context)
        return
    # Hold root-ui live updates from right now, not just from once the
    # resolve finishes: the caller is often handing over a hold of its
    # own (a doc-ui request in flight) that ends as soon as we return,
    # and the live values the effects are about to animate are
    # frequently already waiting. _run_effects() takes its own timed
    # hold, so this one only needs to last until then.
    pause = bauiv1.RootUIUpdatePause()
    bauiv1.app.create_async_task(
        _resolve_and_run_effects(
            effects, sorted(apvernums), delay, context, pause
        )
    )


async def _resolve_and_run_effects(
    effects: list[clfx.Effect],
    apvernums: list[ApverNum],
    delay: float,
    context: ClientEffectContext | None,
    pause: bauiv1.RootUIUpdatePause,
) -> None:
    """Resolve referenced asset-packages then run the effects.

    Runs as a logic-thread async task; the per-locale string reads do
    blocking file IO so they hop through the loop's executor. Holds
    ``pause`` until the effects are running (or skipped).
    """
    try:
        await _resolve_and_run_effects_unheld(
            effects, apvernums, delay, context
        )
    finally:
        del pause


async def _resolve_and_run_effects_unheld(
    effects: list[clfx.Effect],
    apvernums: list[ApverNum],
    delay: float,
    context: ClientEffectContext | None,
) -> None:
    from bacommon.langstr import LanguageStringNameDecodeContext

    assert bauiv1.in_logic_thread()

    locale = bauiv1.app.locale.current_locale
    try:
        async with asyncio.timeout(_RESOLVE_TIMEOUT_SECONDS):
            # Client-effects are decorative — resolve at background priority
            # so they queue behind (and never delay) interactive resolves.
            await bauiv1.app.assets.resolve(
                apvernums,
                language=locale,
                background=True,
                label='client-effects',
            )
            loop = asyncio.get_running_loop()
            langdata = {
                apvernum: await loop.run_in_executor(
                    None,
                    partial(
                        bauiv1.app.assets.get_package_language_data,
                        apvernum,
                        locale,
                    ),
                )
                for apvernum in apvernums
            }
    except TimeoutError as exc:
        # Fail soft; effects are decorative. This can legitimately
        # happen under poor connectivity, so it's info, not a warning.
        assetslog.info(
            'Timed out resolving asset-packages %s for client-effects'
            ' (%.0fs); skipping effects.',
            apvernums,
            _RESOLVE_TIMEOUT_SECONDS,
        )
        strip_exception_tracebacks(exc)
        return
    except Exception as exc:
        # Fail soft; effects are decorative.
        logging.warning(
            'Error resolving asset-packages for client-effects;'
            ' skipping effects.',
            exc_info=True,
        )
        strip_exception_tracebacks(exc)
        return
    # Kinds + components let display-formatted params ({size|data_size})
    # render rather than passing raw values through; nearly every
    # package has neither, so pass only non-empty entries.
    _run_effects(
        effects,
        delay=delay,
        context=context,
        decodectx=LanguageStringNameDecodeContext(
            {apvernum: data[0] for apvernum, data in langdata.items()},
            locale,
            param_kinds={
                apvernum: data[1]
                for apvernum, data in langdata.items()
                if data[1]
            },
            components={
                apvernum: data[2]
                for apvernum, data in langdata.items()
                if data[2]
            },
        ),
    )


def _run_effects(
    effects: list[clfx.Effect],
    *,
    delay: float = 0.0,
    context: ClientEffectContext | None = None,
    decodectx: LanguageStringNameDecodeContext | None = None,
) -> None:
    # pylint: disable=too-many-branches
    import bacommon.clienteffect as clfx

    for effect in effects:
        effecttype = effect.get_type_id()
        if effecttype is clfx.EffectTypeID.LEGACY_SCREEN_MESSAGE:
            # Unreachable on current builds: servers only emit this
            # effect to pre-v2-effects builds (< 22311), so a build
            # containing this code never receives one. Ignore rather
            # than carrying the dead legacy-translation display path.
            logging.warning(
                'Ignoring legacy screen-message client-effect'
                ' (should not be sent to this build).'
            )
        elif effecttype is clfx.EffectTypeID.SCREEN_MESSAGE:
            assert isinstance(effect, clfx.ScreenMessage)
            if effect.is_lstr:
                # Legacy Lstr json: servers only send this to builds
                # predating ScreenMessageV2, so it never reaches us;
                # drop it rather than keep a legacy-translation path.
                logging.warning(
                    'Ignoring legacy-lstr screen-message client-effect'
                    ' (should not be sent to this build).'
                )
            else:
                bauiv1.apptimer(
                    delay,
                    strict_partial(
                        bauiv1.screenmessage,
                        effect.message,
                        color=effect.color,
                        literal=True,
                    ),
                )

        elif effecttype is clfx.EffectTypeID.SCREEN_MESSAGE_V2:
            assert isinstance(effect, clfx.ScreenMessageV2)
            if decodectx is None:
                # Should be impossible; v2 effects imply a resolve
                # pass happened (which builds the context).
                logging.error(
                    'Got ScreenMessageV2 effect with no decode context.'
                )
            elif isinstance(effect.message, int):
                # Unfolded during resolve; a folded index here means
                # that failed. Skip loudly rather than guess.
                assetslog.error(
                    'Unfolded string index %d in a client-effect;'
                    ' skipping it.',
                    effect.message,
                )
            else:
                bauiv1.apptimer(
                    delay,
                    strict_partial(
                        bauiv1.screenmessage,
                        decodectx.decode(effect.message),
                        color=effect.color,
                        literal=True,
                    ),
                )

        elif effecttype is clfx.EffectTypeID.SOUND_V2:
            assert isinstance(effect, clfx.PlaySoundV2)
            # The referenced package is resolved at this point, so the
            # qualified '<apvernum>:<name>' ref loads like any asset.
            #
            # An index reaching here means de-indexing was skipped or
            # failed -- effects can run long after their payload's
            # manifest is gone, so they are converted to specs during
            # resolve. Skip the effect loudly rather than play a wrong
            # sound.
            if isinstance(effect.sound, int):
                assetslog.error(
                    'Un-de-indexed sound ref %d in a client-effect;'
                    ' skipping it.',
                    effect.sound,
                )
                continue
            bauiv1.apptimer(
                delay,
                strict_partial(
                    bauiv1.SoundHandle.from_spec(effect.sound).get().play,
                    volume=effect.volume,
                ),
            )

        elif effecttype is clfx.EffectTypeID.SOUND:
            assert isinstance(effect, clfx.PlaySound)
            scls = clfx.Sound
            soundfile: str | None = None
            if effect.sound is scls.UNKNOWN:
                # Server should avoid sending us sounds we don't
                # support. Make some noise if it happens.
                logging.error('Got unrecognized bacommon.classic.Sound.')
            elif effect.sound is scls.CASH_REGISTER:
                soundfile = 'cashRegister'
            elif effect.sound is scls.ERROR:
                soundfile = 'error'
            elif effect.sound is scls.POWER_DOWN:
                soundfile = 'powerdown01'
            elif effect.sound is scls.GUN_COCKING:
                soundfile = 'gunCocking'
            else:
                assert_never(effect.sound)
            if soundfile is not None:
                bauiv1.apptimer(
                    delay,
                    strict_partial(
                        bauiv1.getsound(soundfile).play, volume=effect.volume
                    ),
                )

        elif effecttype is clfx.EffectTypeID.DELAY:
            assert isinstance(effect, clfx.Delay)
            delay += effect.seconds

        elif effecttype is clfx.EffectTypeID.CHEST_WAIT_TIME_ANIMATION:
            assert isinstance(effect, clfx.ChestWaitTimeAnimation)
            bauiv1.apptimer(
                delay,
                strict_partial(
                    _baclassic.animate_root_ui_chest_unlock_time,
                    chestid=effect.chestid,
                    duration=effect.duration,
                    startvalue=effect.startvalue.timestamp(),
                    endvalue=effect.endvalue.timestamp(),
                ),
            )

        elif effecttype is clfx.EffectTypeID.TICKETS_ANIMATION:
            assert isinstance(effect, clfx.TicketsAnimation)
            bauiv1.apptimer(
                delay,
                strict_partial(
                    _baclassic.animate_root_ui_tickets,
                    duration=effect.duration,
                    startvalue=effect.startvalue,
                    endvalue=effect.endvalue,
                ),
            )

        elif effecttype is clfx.EffectTypeID.TOKENS_ANIMATION:
            assert isinstance(effect, clfx.TokensAnimation)
            bauiv1.apptimer(
                delay,
                strict_partial(
                    _baclassic.animate_root_ui_tokens,
                    duration=effect.duration,
                    startvalue=effect.startvalue,
                    endvalue=effect.endvalue,
                ),
            )

        elif effecttype is clfx.EffectTypeID.KEYFRAME_ANIMATION:
            assert isinstance(effect, clfx.KeyframeAnimation)
            if context is not None and context.targets is not None:
                _run_keyframe_animation(effect, context.targets, delay)

        elif effecttype is clfx.EffectTypeID.UNKNOWN:
            # Server should not send us stuff we can't digest. Make
            # some noise if it happens.
            logging.error(
                'Got unrecognized bacommon.classic.Effect; should not happen.'
            )

        else:
            # For type-checking purposes to remind us to implement new
            # types; should this this in real life.
            assert_never(effecttype)

    # Lastly, put a pause on root ui auto-updates so that everything we
    # just scheduled is free to muck with it freely.
    bauiv1.root_ui_pause_updates()
    bauiv1.apptimer(delay + 0.25, bauiv1.root_ui_resume_updates)


def _apply_first_keys(
    effects: list[clfx.Effect], targets: EffectTargets
) -> None:
    import bacommon.clienteffect as clfx

    targets_ref = weakref.ref(targets)
    for effect in effects:
        if isinstance(effect, clfx.KeyframeAnimation) and effect.keys:
            first = min(effect.keys, key=lambda k: k.time)
            _apply_keyframe(
                targets_ref,
                effect.target,
                first.offset,
                first.scale,
                first.opacity,
            )


def _apply_keyframe(
    targets_ref: weakref.ref[EffectTargets],
    target_id: str,
    offset: tuple[float, float],
    scale: float,
    opacity: float | None,
) -> None:
    targets = targets_ref()
    if targets is None:
        return
    target = targets.get_target(target_id)
    if target is None:
        return
    target.set_animation_state(offset=offset, scale=scale, opacity=opacity)


def _run_keyframe_animation(
    effect: clfx.KeyframeAnimation, targets: EffectTargets, delay: float
) -> None:
    keys = sorted(effect.keys, key=lambda k: k.time)
    if not keys:
        return

    # Look the target up afresh at every step, through a weak ref:
    # the target set (a window, say) can rebuild or go away mid-run.
    targets_ref = weakref.ref(targets)

    if effect.linear:
        bauiv1.apptimer(
            delay,
            strict_partial(
                _InterpolatedAnimation.start, targets_ref, effect.target, keys
            ),
        )
        return

    # Step mode: each key's state holds from its time to the next's
    # (and the first key's from the start).
    for i, key in enumerate(keys):
        bauiv1.apptimer(
            delay + (0.0 if i == 0 else key.time),
            strict_partial(
                _apply_keyframe,
                targets_ref,
                effect.target,
                key.offset,
                key.scale,
                key.opacity,
            ),
        )


class _InterpolatedAnimation:
    """A running linearly-interpolated keyframe animation."""

    def __init__(
        self,
        targets_ref: weakref.ref[EffectTargets],
        target_id: str,
        keys: list[clfx.Keyframe],
    ) -> None:
        self._targets_ref = targets_ref
        self._target_id = target_id
        self._keys = keys
        self._start_time = bauiv1.apptime()
        self._timer: bauiv1.AppTimer | None = bauiv1.AppTimer(
            1.0 / 60.0, self._update, repeat=True
        )

    @classmethod
    def start(
        cls,
        targets_ref: weakref.ref[EffectTargets],
        target_id: str,
        keys: list[clfx.Keyframe],
    ) -> None:
        """Start running one."""
        anim = cls(targets_ref, target_id, keys)
        _g_running_animations.add(anim)
        anim._update()

    def _update(self) -> None:
        keys = self._keys
        elapsed = bauiv1.apptime() - self._start_time
        done = elapsed >= keys[-1].time or self._targets_ref() is None
        if elapsed <= keys[0].time:
            state = keys[0]
            offset, scale, opacity = state.offset, state.scale, state.opacity
        elif done:
            state = keys[-1]
            offset, scale, opacity = state.offset, state.scale, state.opacity
        else:
            nxt = next(i for i, k in enumerate(keys) if k.time > elapsed)
            k0, k1 = keys[nxt - 1], keys[nxt]
            amt = (elapsed - k0.time) / max(0.0001, k1.time - k0.time)
            offset = (
                k0.offset[0] + (k1.offset[0] - k0.offset[0]) * amt,
                k0.offset[1] + (k1.offset[1] - k0.offset[1]) * amt,
            )
            scale = k0.scale + (k1.scale - k0.scale) * amt
            opacity = (
                k1.opacity
                if k0.opacity is None
                else (
                    k0.opacity
                    if k1.opacity is None
                    else k0.opacity + (k1.opacity - k0.opacity) * amt
                )
            )
        _apply_keyframe(
            self._targets_ref, self._target_id, offset, scale, opacity
        )
        if done:
            self._timer = None
            _g_running_animations.discard(self)
