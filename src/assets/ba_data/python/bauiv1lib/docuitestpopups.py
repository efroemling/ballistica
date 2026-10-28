# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui test pages: popup windows and what they do to their parent."""

from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2
import bacommon.docui.routes.docuitest as rt

from bauiv1lib.docuitestwidgets import _lit, style_for_size

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest
    from bacommon.langstr import LangStrSpec

_COLORS = ('Red', 'Green', 'Blue')


def test_page_popups(
    route: (
        bacommon.docui.routes.docuitest.Popups
        | bacommon.docui.routes.docuitest.PopupsMain
        | bacommon.docui.routes.docuitest.PopupsOther
    ),
) -> bacommon.docui.v2.Response:
    """The popups test pages: the parent and its popups."""
    match route:
        case rt.Popups():
            return _page_parent(route)
        case rt.PopupsMain():
            return _page_main(route)
        case rt.PopupsOther():
            return _page_other(route)
        case _:
            assert_never(route)


def _describe(state: rt.PopupsState | None) -> str:
    if state is None:
        return 'No parent state.'
    color = state.color or '(none)'
    opened = state.opened_with or '(nothing)'
    return f'Color: {color}   Count: {state.count}   Opened with: {opened}'


def _edge_style_label(style: dui2.ScrollEdgeStyle) -> LangStrSpec:
    match style:
        case dui2.ScrollEdgeStyle.FADE:
            return _lit('Fade')
        case dui2.ScrollEdgeStyle.OUTLINE:
            return _lit('Outline')
        case _:
            assert_never(style)


def _edge_style(state: rt.PopupsState | None) -> dui2.ScrollEdgeStyle:
    """The scroll edge style the parent page has picked for popups."""
    return dui2.ScrollEdgeStyle.FADE if state is None else state.edge_style


def _button(label: str, action: dui2.Action, width: float = 180) -> dui2.Button:
    size = (width, 60.0)
    return dui2.Button(
        label=_lit(label),
        size=size,
        style=style_for_size(size),
        action=action,
    )


def _page_parent(
    route: bacommon.docui.routes.docuitest.Popups,
) -> bacommon.docui.v2.Response:
    """The parent: shows what popups have done to it, and opens them."""
    arrived = route.get_state(rt.PopupsState)
    state = rt.PopupsState() if arrived is None else arrived
    es = state.edge_style
    return dui2.Response(
        page=dui2.Page(
            title=_lit('Popups'),
            state=state.encode(),
            rows=[
                rt.PopupsState.choice_row(
                    lambda s: s.edge_style,
                    choice_label=_edge_style_label,
                    label=_lit('Popup Scroll Edges'),
                    # (Rebuilds this page so its links carry the pick.)
                    on_change=rt.Popups().replace(),
                ),
                dui2.TitleRow(_lit(_describe(state))),
                dui2.SubtitleRow(
                    _lit(
                        'A popup opens over this page without leaving'
                        ' it, and can act on it as it closes: refresh'
                        ' it (with new values), replace it, browse from'
                        ' it or close it.'
                    )
                ),
                dui2.ButtonRow(
                    buttons=[
                        _button(
                            'Open Popup',
                            rt.PopupsMain().popup(scroll_edge_style=es),
                        ),
                        _button(
                            'Open With Sets',
                            rt.PopupsMain().popup(
                                sets=[
                                    rt.PopupsState.assign(
                                        lambda s: s.opened_with,
                                        'Open With Sets',
                                    )
                                ],
                                scroll_edge_style=es,
                            ),
                        ),
                        _button(
                            'Open From Menu',
                            dui2.Menu(
                                items=[
                                    dui2.MenuItem(
                                        label=_lit('Open Popup'),
                                        action=rt.PopupsMain().popup(
                                            scroll_edge_style=es
                                        ),
                                    ),
                                    dui2.MenuItem(
                                        label=_lit('Open Other Popup'),
                                        action=rt.PopupsOther().popup(
                                            scroll_edge_style=es
                                        ),
                                    ),
                                ]
                            ),
                        ),
                    ],
                ),
                dui2.TitleRow(_lit('Popup Options')),
                dui2.SubtitleRow(
                    _lit(
                        'Smallest is the least a popup may ask for; the'
                        ' extra ones ask for far more than any screen'
                        ' and get shrunk to fit it. A press outside a'
                        ' popup always closes it.'
                    )
                ),
                dui2.ButtonRow(
                    buttons=[
                        _button(
                            'Smallest',
                            rt.PopupsOther().popup(
                                size=dui2.POPUP_MIN_SIZE, scroll_edge_style=es
                            ),
                        ),
                        # (Far bigger than any screen: each gets shrunk
                        # to fit, along its own axis.)
                        _button(
                            'Extra Wide',
                            rt.PopupsOther().popup(
                                size=(5000.0, 200.0), scroll_edge_style=es
                            ),
                        ),
                        _button(
                            'Extra Tall',
                            rt.PopupsOther().popup(
                                size=(200.0, 5000.0), scroll_edge_style=es
                            ),
                        ),
                        _button(
                            'With Title',
                            rt.PopupsOther().popup(
                                show_title=True, scroll_edge_style=es
                            ),
                        ),
                        _button(
                            'With Close Button',
                            rt.PopupsOther().popup(
                                show_close_button=True, scroll_edge_style=es
                            ),
                        ),
                        _button(
                            'Title And Close',
                            rt.PopupsOther().popup(
                                show_title=True,
                                show_close_button=True,
                                scroll_edge_style=es,
                            ),
                        ),
                        _button(
                            'Small',
                            rt.PopupsOther().popup(
                                size=(300.0, 200.0), scroll_edge_style=es
                            ),
                        ),
                        _button(
                            'No Dimming',
                            rt.PopupsOther().popup(
                                dim_background=False, scroll_edge_style=es
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )


def _page_main(
    route: bacommon.docui.routes.docuitest.PopupsMain,
) -> bacommon.docui.v2.Response:
    """The main popup: every way of acting on the parent."""
    parent = route.parent()
    parent_state = route.get_parent_state()
    count = 0 if parent_state is None else parent_state.count
    arrived = route.get_state(rt.PopupsMainState)
    state = rt.PopupsMainState() if arrived is None else arrived
    return dui2.Response(
        page=dui2.Page(
            title=_lit('Test Popup'),
            state=state.encode(),
            # (The popup look, with no vertical inset: trying it out.)
            h_inset=dui2.POPUP_H_INSET,
            v_inset=0.0,
            row_spacing=dui2.POPUP_ROW_SPACING,
            button_color=dui2.POPUP_BUTTON_COLOR,
            rows=[
                dui2.TitleRow(_lit(f'Parent: {_describe(parent_state)}')),
                dui2.SubtitleRow(
                    _lit(
                        f'This popup has its own state too (bumps:'
                        f' {state.bumps}). Bumping replaces the popup'
                        f'\'s page; the parent state still comes along.'
                    )
                ),
                dui2.ButtonRow(
                    buttons=[
                        _button(
                            'Bump Self',
                            rt.PopupsMain().replace(
                                sets=[
                                    rt.PopupsMainState.assign(
                                        lambda s: s.bumps, state.bumps + 1
                                    )
                                ]
                            ),
                        ),
                        _button(
                            'Swap Popup',
                            rt.PopupsOther().popup(
                                scroll_edge_style=_edge_style(parent_state)
                            ),
                        ),
                    ],
                ),
                dui2.TitleRow(_lit('Pick A Color (refreshes the parent)')),
                dui2.ButtonRow(
                    buttons=[
                        _button(
                            color,
                            parent.refresh(
                                rt.PopupsState.assign(lambda s: s.color, color)
                            ),
                            width=120,
                        )
                        for color in _COLORS
                    ],
                ),
                dui2.TitleRow(_lit('Act On The Parent')),
                dui2.ButtonRow(
                    buttons=[
                        _button(
                            'Count +1 (Replace)',
                            parent.replace(
                                rt.Popups(),
                                sets=[
                                    rt.PopupsState.assign(
                                        lambda s: s.count, count + 1
                                    )
                                ],
                            ),
                        ),
                        _button('Refresh Parent', parent.refresh()),
                        _button(
                            'Browse From Parent', parent.browse(rt.Test2())
                        ),
                        _button('Close Parent', parent.close()),
                        _button('Close To Root', parent.close_to(rt.Root)),
                        _button(
                            'Menu...',
                            dui2.Menu(
                                items=[
                                    dui2.MenuItem(
                                        label=_lit('Color: Purple'),
                                        action=parent.refresh(
                                            rt.PopupsState.assign(
                                                lambda s: s.color, 'Purple'
                                            )
                                        ),
                                    ),
                                    dui2.MenuItem(
                                        label=_lit('Dismiss'),
                                        action=parent.dismiss(),
                                    ),
                                ]
                            ),
                        ),
                    ],
                ),
                dui2.ButtonRow(
                    buttons=[_button('Close', parent.dismiss())],
                ),
            ],
        ),
    )


def _page_other(
    route: bacommon.docui.routes.docuitest.PopupsOther,
) -> bacommon.docui.v2.Response:
    """A second popup, for swapping one popup for another."""
    parent = route.parent()
    parent_state = route.get_parent_state()
    return dui2.Response(
        page=dui2.Page(
            title=_lit('Other Popup'),
            # (The popup look, with no vertical inset: trying it out.)
            h_inset=dui2.POPUP_H_INSET,
            v_inset=0.0,
            row_spacing=dui2.POPUP_ROW_SPACING,
            button_color=dui2.POPUP_BUTTON_COLOR,
            rows=[
                dui2.TitleRow(_lit(f'Parent: {_describe(parent_state)}')),
                dui2.SubtitleRow(
                    _lit(
                        'This replaced the first popup; the parent page'
                        ' under it is untouched.'
                    )
                ),
                dui2.ButtonRow(
                    buttons=[
                        _button(
                            'Swap Back',
                            rt.PopupsMain().popup(
                                scroll_edge_style=_edge_style(parent_state)
                            ),
                        ),
                        _button('Close', parent.dismiss()),
                    ],
                ),
            ],
        ),
    )
