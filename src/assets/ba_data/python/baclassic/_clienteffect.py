# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to running client-effects from the master server."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, assert_never

from efro.util import strict_partial

import bauiv1

import _baclassic

if TYPE_CHECKING:
    import bacommon.clienteffect as clfx


def run_bs_client_effects(
    effects: list[clfx.Effect], delay: float = 0.0
) -> None:
    """Run effects."""
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
