# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui test pages: a drill-down that closes back to its top."""

from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
import bacommon.docui.routes.docuitest as rt

from bauiv1lib.docuitestwidgets import _lit

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest

#: Levels below the top; the last one holds the treasures.
_DEPTH = 3

_DOORS = ('Red', 'Green', 'Blue')
_TREASURES = ('Gold Coin', 'Old Map', 'Rubber Duck')


def test_page_drill(
    route: bacommon.docui.routes.docuitest.Drill,
) -> bacommon.docui.v2.Response:
    """The top: what was found, and a way down."""
    arrived = route.get_state(rt.DrillState)
    state = rt.DrillState() if arrived is None else arrived
    found = f'Found: {state.found}' if state.found else 'Nothing found yet.'
    return dui2.Response(
        page=dui2.Page(
            title=_lit('Drill Down'),
            state=state.encode(),
            rows=[
                dui2.TitleRow(_lit(found)),
                dui2.SubtitleRow(
                    _lit(
                        f'Explore opens {_DEPTH} levels, each in a'
                        f' window of its own. Picking a treasure at the'
                        f' bottom closes them all and hands it back'
                        f' here.'
                    )
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=_lit('Explore'),
                            size=(200, 80),
                            action=rt.DrillLevel(depth=1).browse(),
                        ),
                    ],
                ),
            ],
        ),
    )


def test_page_drill_level(
    route: bacommon.docui.routes.docuitest.DrillLevel,
) -> bacommon.docui.v2.Response:
    """One level: doors further down, or treasures at the bottom."""
    depth = max(1, min(route.depth, _DEPTH))
    buttons: list[dui2.Button]
    if depth < _DEPTH:
        buttons = [
            dui2.Button(
                label=_lit(f'{door} Door'),
                size=(160, 80),
                action=rt.DrillLevel(
                    depth=depth + 1, trail=route.trail + door[0]
                ).browse(),
            )
            for door in _DOORS
        ]
    else:
        buttons = [
            dui2.Button(
                label=_lit(treasure),
                size=(160, 80),
                # Back to the top in one step, with the find.
                action=rt.Drill.close_to(
                    rt.DrillState.assign(
                        lambda s: s.found,
                        f'{treasure} (doors: {route.trail})',
                    )
                ),
            )
            for treasure in _TREASURES
        ]
    rows: list[dui2.Row] = [
        dui2.TitleRow(
            _lit(
                f'Level {depth} of {_DEPTH}'
                + (f' (doors: {route.trail})' if route.trail else '')
            )
        ),
        dui2.ButtonRow(buttons=buttons),
    ]
    if depth == _DEPTH:
        # What a bad target looks like: a page we never came through.
        # This should warn (it is a bug in a real page) and close just
        # this one window.
        rows += [
            dui2.TitleRow(_lit('Misuse')),
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        label=_lit('Close To A Page Not Visited'),
                        size=(300, 60),
                        action=rt.NinePatch.close_to(),
                    )
                ],
            ),
        ]
    return dui2.Response(
        page=dui2.Page(title=_lit(f'Level {depth}'), rows=rows),
    )
