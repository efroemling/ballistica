# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to running client-effects from the master server."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, assert_never

from efro.util import strict_partial

import bacommon.bs
import bauiv1

if TYPE_CHECKING:
    pass


def run_bs_client_effects(effects: list[bacommon.bs.ClientEffect]) -> None:
    """Run effects."""
    # pylint: disable=too-many-branches

    delay = 0.0
    for effect in effects:
        if isinstance(effect, bacommon.bs.ClientEffectScreenMessage):
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

        elif isinstance(effect, bacommon.bs.ClientEffectSound):
            smcls = bacommon.bs.ClientEffectSound.Sound
            soundfile: str | None = None
            if effect.sound is smcls.UNKNOWN:
                # Server should avoid sending us sounds we don't
                # support. Make some noise if it happens.
                logging.error('Got unrecognized bacommon.bs.ClientEffectSound.')
            elif effect.sound is smcls.CASH_REGISTER:
                soundfile = 'cashRegister'
            elif effect.sound is smcls.ERROR:
                soundfile = 'error'
            elif effect.sound is smcls.POWER_DOWN:
                soundfile = 'powerdown01'
            elif effect.sound is smcls.GUN_COCKING:
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

        elif isinstance(effect, bacommon.bs.ClientEffectDelay):
            delay += effect.seconds
        else:
            # Server should not send us stuff we can't digest. Make
            # some noise if it happens.
            logging.error(
                'Got unrecognized bacommon.bs.ClientEffect;'
                ' should not happen.'
            )
