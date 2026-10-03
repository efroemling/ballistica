# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui live-times test page.

Text holding a moment in time
(:class:`bacommon.langstr.LangStrSpecTimeTarget`) re-renders itself as
time passes: each widget re-evaluates exactly when its visible text is
due to change, so a seconds countdown ticks once a second, one showing
milliseconds every frame, and one showing only minutes once a minute.
Nothing on this page asks the server (or Python) for updates.

Every moment is a fixed offset from when the page was built; the
restart button rebuilds it.
"""

import datetime
from typing import TYPE_CHECKING

from bacommon.langstr import LangStrSpecTimeTarget, LangStrSpecValue
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest

# NEEDS_TRANSLATION: dev-only test page; every label here is a literal.


def test_page_live_times(
    route: bacommon.docui.routes.docuitest.LiveTimes,
) -> bacommon.docui.v2.Response:
    """Testing time-varying text."""
    import babase
    from bauiv1 import _builtinassets

    start = babase.utc_now_cloud()

    def _at(**kwargs: float) -> LangStrSpecTimeTarget:
        return LangStrSpecTimeTarget.at(start + datetime.timedelta(**kwargs))

    def _button(
        label: str,
        template: str,
        moment: LangStrSpecTimeTarget,
        *,
        scale: float = 0.9,
    ) -> dui2.Button:
        """A button showing one live text with a caption above it."""
        return dui2.Button(
            size=(220, 130),
            style=dui2.ButtonStyle.MEDIUM,
            decorations=[
                dui2.Text(
                    text=LangStrSpecValue.literal(label),
                    position=(0.0, 40.0),
                    size=(200.0, 0.0),
                    scale=0.55,
                ),
                dui2.Text(
                    text=LangStrSpecValue(template, {'t': moment}),
                    position=(0.0, -10.0),
                    size=(200.0, 60.0),
                    scale=scale,
                ),
            ],
        )

    # The one authored duration string so far: a bare duration with no
    # direction, so it goes negative once its moment passes. Fetched
    # through the native wrapper and projected back to a spec, which
    # also exercises the time target's native round trip.
    authored = _builtinassets.strings.time.duration_value(
        t=start + datetime.timedelta(seconds=15)
    ).spec

    return dui2.Response(
        page=dui2.Page(
            title=LangStrSpecValue.literal('Live Times'),
            rows=[
                dui2.ButtonRow(
                    title=LangStrSpecValue.literal('Countdowns'),
                    subtitle=LangStrSpecValue.literal(
                        'Each re-renders only when its visible text'
                        ' changes, then rests at zero.'
                    ),
                    buttons=[
                        _button(
                            'seconds (crosses a minute)',
                            'Ends in {t|duration(dir=future)}',
                            _at(seconds=75),
                        ),
                        _button(
                            'tenths',
                            '{t|duration(dir=future,decimals=1)}',
                            _at(seconds=12),
                            scale=1.2,
                        ),
                        _button(
                            'milliseconds (every frame)',
                            '{t|duration(dir=future,decimals=3)}',
                            _at(seconds=20),
                            scale=1.2,
                        ),
                        _button(
                            'one unit (minutes, then seconds)',
                            '{t|duration(dir=future,maxparts=1)}',
                            _at(seconds=65),
                            scale=1.2,
                        ),
                        _button(
                            'days (changes hourly)',
                            '{t|duration(dir=future)} left',
                            _at(days=2, hours=3, seconds=30),
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    title=LangStrSpecValue.literal('Elapsed and crossing zero'),
                    subtitle=LangStrSpecValue.literal(
                        'Counting up from the page start, and values that'
                        ' pass their moment while you watch.'
                    ),
                    buttons=[
                        _button(
                            'since page start',
                            'Opened {t|duration(dir=past)} ago',
                            _at(),
                        ),
                        _button(
                            'past, not yet started',
                            'Started {t|duration(dir=past)} ago',
                            _at(seconds=8),
                        ),
                        _button(
                            'no direction (goes negative)',
                            '{t|duration}',
                            _at(seconds=8),
                            scale=1.2,
                        ),
                        dui2.Button(
                            size=(220, 130),
                            style=dui2.ButtonStyle.MEDIUM,
                            decorations=[
                                dui2.Text(
                                    text=LangStrSpecValue.literal(
                                        'authored string (time/duration_value)'
                                    ),
                                    position=(0.0, 40.0),
                                    size=(200.0, 0.0),
                                    scale=0.55,
                                ),
                                dui2.Text(
                                    text=authored,
                                    position=(0.0, -10.0),
                                    size=(200.0, 60.0),
                                    scale=1.2,
                                ),
                            ],
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    title=LangStrSpecValue.literal(
                        'OS-rendered text and button labels'
                    ),
                    subtitle=LangStrSpecValue.literal(
                        'Non-Latin words around ticking digits must reuse'
                        ' one OS text texture (a warning fires if not);'
                        ' labels tick too.'
                    ),
                    buttons=[
                        _button(
                            'Japanese',
                            '残り {t|duration(dir=future)}',
                            _at(seconds=90),
                        ),
                        _button(
                            'Russian',
                            'Осталось {t|duration(dir=future,decimals=2)}',
                            _at(seconds=40),
                        ),
                        dui2.Button(
                            label=LangStrSpecValue(
                                'Claim in {t|duration(dir=future)}',
                                {'t': _at(seconds=30)},
                            ),
                            size=(220, 130),
                            style=dui2.ButtonStyle.MEDIUM,
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=LangStrSpecValue.literal('Restart'),
                            style=dui2.ButtonStyle.MEDIUM,
                            size=(240, 60),
                            color=(0.6, 0.4, 0.8, 1.0),
                            action=route.replace(),
                        )
                    ],
                ),
            ],
        )
    )
