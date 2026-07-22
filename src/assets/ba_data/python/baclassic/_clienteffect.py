# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to running client-effects from the master server."""

import asyncio
import logging
from functools import partial
from typing import TYPE_CHECKING, assert_never

from efro.util import strict_partial, strip_exception_tracebacks
from bacommon.logging import ClientLoggerName

import bauiv1

import _baclassic

if TYPE_CHECKING:
    import bacommon.clienteffect as clfx
    from bacommon.langstr import LanguageStringNameDecodeContext

#: How long we wait on the asset-package resolve for v2 effects before
#: giving up (effects are decorative; skipping beats hanging).
_RESOLVE_TIMEOUT_SECONDS = 30.0

assetslog = logging.getLogger(ClientLoggerName.ASSETS.value)


def run_bs_client_effects(
    effects: list[clfx.Effect], delay: float = 0.0
) -> None:
    """Run effects."""
    import bacommon.clienteffect as clfx

    # V2 effect forms reference asset-packages (l-string text, sound
    # refs). Those need resolving — possibly downloading — before the
    # effects can run; kick that off and run once ready. Effects with
    # no package refs run immediately as always.
    apverids: set[str] = set()
    clfx.collect_apverids(effects, apverids)
    if not apverids:
        _run_effects(effects, delay=delay)
        return
    bauiv1.app.create_async_task(
        _resolve_and_run_effects(effects, sorted(apverids), delay)
    )


async def _resolve_and_run_effects(
    effects: list[clfx.Effect], apverids: list[str], delay: float
) -> None:
    """Resolve referenced asset-packages then run the effects.

    Runs as a logic-thread async task; the per-locale string reads do
    blocking file IO so they hop through the loop's executor.
    """
    from bacommon.langstr import LanguageStringNameDecodeContext

    assert bauiv1.in_logic_thread()

    locale = bauiv1.app.locale.current_locale
    try:
        async with asyncio.timeout(_RESOLVE_TIMEOUT_SECONDS):
            # Client-effects are decorative — resolve at background priority
            # so they queue behind (and never delay) interactive resolves.
            await bauiv1.app.assets.resolve(
                apverids, language=locale, background=True
            )
            loop = asyncio.get_running_loop()
            language = {
                apverid: await loop.run_in_executor(
                    None,
                    partial(
                        bauiv1.app.assets.get_package_strings,
                        apverid,
                        locale,
                    ),
                )
                for apverid in apverids
            }
    except TimeoutError as exc:
        # Fail soft; effects are decorative. This can legitimately
        # happen under poor connectivity, so it's info, not a warning.
        assetslog.info(
            'Timed out resolving asset-packages %s for client-effects'
            ' (%.0fs); skipping effects.',
            apverids,
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
    _run_effects(
        effects,
        delay=delay,
        decodectx=LanguageStringNameDecodeContext(language, locale),
    )


def _run_effects(
    effects: list[clfx.Effect],
    *,
    delay: float = 0.0,
    decodectx: LanguageStringNameDecodeContext | None = None,
) -> None:
    # pylint: disable=too-many-branches
    import bacommon.clienteffect as clfx

    for effect in effects:
        effecttype = effect.get_type_id()
        if effecttype is clfx.EffectTypeID.LEGACY_SCREEN_MESSAGE:
            assert isinstance(effect, clfx.LegacyScreenMessage)
            textfin = bauiv1.Lstr(
                translate=('serverResponses', effect.message)
            ).evaluate()
            if effect.subs is not None:
                # Should always be even.
                assert len(effect.subs) % 2 == 0
                for j in range(0, len(effect.subs) - 1, 2):
                    textfin = textfin.replace(
                        effect.subs[j],
                        effect.subs[j + 1],
                    )
            bauiv1.apptimer(
                delay,
                strict_partial(
                    bauiv1.screenmessage, textfin, color=effect.color
                ),
            )
        elif effecttype is clfx.EffectTypeID.SCREEN_MESSAGE:
            assert isinstance(effect, clfx.ScreenMessage)
            bauiv1.apptimer(
                delay,
                strict_partial(
                    bauiv1.screenmessage,
                    effect.message,
                    color=effect.color,
                    literal=not effect.is_lstr,
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
            # qualified '<apverid>:<name>' ref loads like any asset.
            bauiv1.apptimer(
                delay,
                strict_partial(
                    bauiv1.getsound(
                        f'{effect.sound.apverid}:{effect.sound.name}'
                    ).play,
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
