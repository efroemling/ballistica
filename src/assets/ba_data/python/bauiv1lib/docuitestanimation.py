# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui animation test page.

Decorations carrying an ``anim_id`` animated by
``bacommon.clienteffect.KeyframeAnimation`` effects: a box shakes
with growing amplitude while shrinking (step keys, like the chest
open), then pops back; a label fades and grows in (linear keys). The
effects run when the page arrives and again on 'Replay'.
"""

import math
import random
from typing import TYPE_CHECKING

from bacommon.langstr import LangStrSpecValue
import bacommon.clienteffect as clfx
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.v2

# NEEDS_TRANSLATION: dev-only test page; every label here is a literal.


def _shake_keys(duration: float) -> list[clfx.Keyframe]:
    """Jitter that grows over ``duration``, shrinking as it goes."""
    keys = [clfx.Keyframe(time=0.0)]
    t = 0.0
    sign = 1.0
    while t < duration:
        t += 0.03 * random.uniform(0.5, 1.5)
        sign = -sign
        amt = math.pow(min(1.0, t / duration), 2.0)
        keys.append(
            clfx.Keyframe(
                time=t,
                offset=(20.0 * random.uniform(0.3, 1.0) * amt * sign, 0.0),
                scale=1.0 - 0.2 * amt,
            )
        )
    # Pop back to full size.
    keys.append(clfx.Keyframe(time=t + 0.05))
    return keys


def _effects() -> list[clfx.Effect]:
    return [
        clfx.KeyframeAnimation(target='box', keys=_shake_keys(1.6)),
        clfx.KeyframeAnimation(
            target='label',
            linear=True,
            keys=[
                clfx.Keyframe(time=0.0, opacity=0.0, scale=0.5),
                clfx.Keyframe(time=1.6, opacity=0.0, scale=0.5),
                clfx.Keyframe(time=2.2, opacity=1.0, scale=1.2),
                clfx.Keyframe(time=2.5),
            ],
        ),
    ]


def test_page_animation() -> bacommon.docui.v2.Response:
    """Testing keyframe animation of decorations."""
    from bauiv1 import _builtinassets

    effects = _effects()
    return dui2.Response(
        page=dui2.Page(
            title=LangStrSpecValue.literal('Animation'),
            center_vertically=True,
            rows=[
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            size=(400, 300),
                            style=dui2.ButtonStyle.SQUARE,
                            decorations=[
                                dui2.Image(
                                    texture=_builtinassets.textures.white,
                                    position=(0.0, 30.0),
                                    size=(120.0, 120.0),
                                    color=(0.3, 0.8, 0.4, 1.0),
                                    anim_id='box',
                                ),
                                dui2.Text(
                                    text=LangStrSpecValue.literal('Ta-da!'),
                                    position=(0.0, -90.0),
                                    size=(300.0, 0.0),
                                    scale=1.2,
                                    color=(1.0, 0.9, 0.3, 1.0),
                                    anim_id='label',
                                ),
                            ],
                            action=dui2.Local(
                                immediate_client_effects=_effects()
                            ),
                        ),
                    ],
                ),
            ],
        ),
        client_effects=effects,
    )
