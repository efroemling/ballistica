# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui test page for navigation between control rows."""

from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2

from bauiv1lib.docuitestwidgets import _lit, _flavor_label, _map_button

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest


def _kind_name(kind: bacommon.docui.routes.docuitest.ControlRowKind) -> str:
    return kind.name.replace('_', ' ').title()


def test_page_nav(
    route: bacommon.docui.routes.docuitest.NavTest,
) -> bacommon.docui.v2.Response:
    """A button row, then one control row of the route's kind, last."""
    # pylint: disable=cyclic-import
    import bacommon.docui.routes.docuitest as rt

    wstate = rt.WidgetTestState
    arrived = route.get_state(wstate)
    state = wstate() if arrived is None else arrived
    kind = route.kind
    kinds = list(rt.ControlRowKind)

    row: dui2.Row
    match kind:
        case rt.ControlRowKind.CHECKBOX:
            row = wstate.checkbox_row(lambda s: s.plain, label=_lit('Checkbox'))
        case rt.ControlRowKind.TEXT_INPUT:
            row = wstate.text_input_row(
                lambda s: s.text_short, label=_lit('Text')
            )
        case rt.ControlRowKind.CHOICE:
            row = wstate.choice_row(
                lambda s: s.flavor,
                choice_label=_flavor_label,
                label=_lit('Choice'),
            )
        case rt.ControlRowKind.SLIDER:
            row = wstate.slider_row(
                lambda s: s.volume,
                min_value=0.0,
                max_value=1.0,
                increment=0.05,
                as_percent=True,
                label=_lit('Slider'),
            )
        case rt.ControlRowKind.NUMBER:
            row = wstate.number_row(
                lambda s: s.series_length,
                min_value=1.0,
                max_value=21.0,
                increment=2.0,
                label=_lit('Number'),
            )
        case rt.ControlRowKind.COLOR:
            row = wstate.color_row(lambda s: s.tint, label=_lit('Color'))
        case rt.ControlRowKind.BUTTON:
            row = dui2.ButtonControlRow(
                button=_map_button(route.replace()),
                label=_lit('Button Control'),
            )
        case _:
            assert_never(kind)

    return dui2.Response(
        page=dui2.Page(
            title=_lit(f'Nav Test: {_kind_name(kind)}'),
            state=state.encode(),
            # Kind switchers in rows of three (six in one row overflow a
            # small layout), then the row under test, last.
            rows=[
                dui2.ButtonRow(
                    center_content=True,
                    buttons=[
                        dui2.Button(
                            label=_lit(_kind_name(k)),
                            size=(140, 50),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=rt.NavTest(kind=k).replace(),
                        )
                        for k in kinds[i : i + 3]
                    ],
                )
                for i in range(0, len(kinds), 3)
            ]
            + [row],
        )
    )
