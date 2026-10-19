# Released under the MIT License. See LICENSE for details.
#
"""Small doc-ui test pages (navigation, slow loads, timed actions)."""

import time
from typing import TYPE_CHECKING

import bacommon.docui.routes.docuitest as rt

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest


def test_page_2() -> bacommon.docui.v2.Response:
    """More testing (v2 mirror of the v1 '/test2' page)."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    return dui2.Response(
        page=dui2.Page(
            title=strs.nav.test_two_title.spec,
            rows=[
                dui2.ButtonRow(
                    title=strs.nav.more_tests.spec,
                    buttons=[
                        dui2.Button(
                            label=strs.nav.browse.spec,
                            size=(120, 80),
                            style=dui2.ButtonStyle.SQUARE,
                            action=rt.Root().browse(),
                        ),
                        dui2.Button(
                            label=strs.nav.replace.spec,
                            size=(120, 80),
                            style=dui2.ButtonStyle.SQUARE,
                            action=rt.Root().replace(),
                        ),
                        dui2.Button(
                            label=strs.nav.close.spec,
                            size=(120, 80),
                            style=dui2.ButtonStyle.SQUARE,
                            action=dui2.Local(close_window=True),
                            selected=True,  # Testing this
                        ),
                    ],
                ),
            ],
        )
    )


def test_page_long() -> bacommon.docui.v2.Response:
    """Testing a page that takes a bit of time to load (v2 mirror)."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    # Simulate a slow connection or whatnot.
    time.sleep(3.0)

    return dui2.Response(
        page=dui2.Page(
            title=strs.nav.test.spec,
            center_vertically=True,
            rows=[
                dui2.ButtonRow(
                    title=strs.common.that_took_a_while.spec,
                    center_title=True,
                    center_content=True,
                    buttons=[
                        dui2.Button(
                            label=strs.common.sure_did.spec,
                            size=(120, 80),
                            style=dui2.ButtonStyle.SQUARE,
                            action=rt.Root().browse(),
                        ),
                    ],
                ),
            ],
        )
    )


def test_page_timed_actions(
    route: bacommon.docui.routes.docuitest.TimedActions,
) -> bacommon.docui.v2.Response:
    """Testing timed actions (v2 mirror of '/timedactions')."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    strs = _docuiv2testassets.strings

    val = route.val

    return dui2.Response(
        page=dui2.Page(
            title=strs.nav.test.spec,
            center_vertically=True,
            rows=[
                dui2.ButtonRow(
                    title=strs.common.hello_there_num(num=str(val)).spec,
                    subtitle=strs.common.each_change.spec,
                    center_title=True,
                    center_content=True,
                    buttons=[
                        dui2.Button(
                            label=strs.nav.done.spec,
                            size=(120, 80),
                            style=dui2.ButtonStyle.SQUARE,
                            action=dui2.Local(close_window=True),
                            default=True,
                        ),
                    ],
                ),
            ],
        ),
        # Refresh this page with a countdown until we hit zero and then
        # close the window.
        timed_action=(
            rt.TimedActions(val=val - 1).replace()
            if (val - 1) > 0
            else dui2.Local(close_window=True)
        ),
        timed_action_delay=1.0,
    )


def test_page_empty() -> bacommon.docui.v2.Response:
    """An empty page (v2 mirror of '/emptypage')."""
    import bacommon.docui.v2 as dui2

    from bauiv1 import _docuiv2testassets

    return dui2.Response(
        page=dui2.Page(
            title=_docuiv2testassets.strings.layout.empty_page_title.spec,
            rows=[],
        )
    )
