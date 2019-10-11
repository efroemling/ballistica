# Copyright (c) 2011-2019 Eric Froemling
"""UI functionality for creating tab style buttons."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Tuple, List, Sequence


def create_tab_buttons(parent_widget: ba.Widget,
                       tabs: List[Tuple[str, ba.Lstr]],
                       pos: Sequence[float],
                       size: Sequence[float],
                       on_select_call: Callable[[Any], Any] = None,
                       return_extra_info: bool = False) -> Dict[str, Any]:
    """(internal)"""
    # pylint: disable=too-many-locals
    tab_pos_v = pos[1]
    tab_buttons = {}
    tab_buttons_indexed = []
    tab_button_width = float(size[0]) / len(tabs)

    # add a bit more visual spacing as our buttons get narrower
    tab_spacing = (250.0 - tab_button_width) * 0.06
    positions = []
    sizes = []
    h = pos[0]
    for _i, tab in enumerate(tabs):

        def _tick_and_call(call: Callable[[Any], Any], arg: Any) -> None:
            ba.playsound(ba.getsound('click01'))
            call(arg)

        pos = (h + tab_spacing * 0.5, tab_pos_v)
        size = (tab_button_width - tab_spacing, 50.0)
        positions.append(pos)
        sizes.append(size)
        btn = ba.buttonwidget(parent=parent_widget,
                              position=pos,
                              autoselect=True,
                              button_type='tab',
                              size=size,
                              label=tab[1],
                              enable_sound=False,
                              on_activate_call=ba.Call(_tick_and_call,
                                                       on_select_call, tab[0]))
        h += tab_button_width
        tab_buttons[tab[0]] = btn
        tab_buttons_indexed.append(btn)
    if return_extra_info:
        return {
            'buttons': tab_buttons,
            'buttons_indexed': tab_buttons_indexed,
            'positions': positions,
            'sizes': sizes
        }
    return tab_buttons


def update_tab_button_colors(tabs: Dict[str, ba.Widget],
                             selected_tab: str) -> None:
    """(internal)"""
    for t_id, tbutton in list(tabs.items()):
        if t_id == selected_tab:
            ba.buttonwidget(edit=tbutton,
                            color=(0.5, 0.4, 0.93),
                            textcolor=(0.85, 0.75, 0.95))  # lit
        else:
            ba.buttonwidget(edit=tbutton,
                            color=(0.52, 0.48, 0.63),
                            textcolor=(0.65, 0.6, 0.7))  # unlit
