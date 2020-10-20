# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for creating tab style buttons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, Generic

import ba

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Tuple, List, Sequence, Optional


@dataclass
class Tab:
    """Info for an individual tab in a TabRow"""
    button: ba.Widget
    position: Tuple[float, float]
    size: Tuple[float, float]


T = TypeVar('T')


class TabRow(Generic[T]):
    """Encapsulates a row of tab-styled buttons.

    Tabs are indexed by id which is an arbitrary user-provided type.
    """

    def __init__(self,
                 parent: ba.Widget,
                 tabdefs: List[Tuple[T, ba.Lstr]],
                 pos: Tuple[float, float],
                 size: Tuple[float, float],
                 on_select_call: Callable[[T], None] = None) -> None:
        if not tabdefs:
            raise ValueError('At least one tab def is required')
        self.tabs: Dict[T, Tab] = {}
        tab_pos_v = pos[1]
        tab_button_width = float(size[0]) / len(tabdefs)
        tab_spacing = (250.0 - tab_button_width) * 0.06
        h = pos[0]
        for tab_id, tab_label in tabdefs:
            pos = (h + tab_spacing * 0.5, tab_pos_v)
            size = (tab_button_width - tab_spacing, 50.0)
            btn = ba.buttonwidget(parent=parent,
                                  position=pos,
                                  autoselect=True,
                                  button_type='tab',
                                  size=size,
                                  label=tab_label,
                                  enable_sound=False,
                                  on_activate_call=ba.Call(
                                      self._tick_and_call, on_select_call,
                                      tab_id))
            h += tab_button_width
            self.tabs[tab_id] = Tab(button=btn, position=pos, size=size)

    def update_appearance(self, selected_tab_id: T) -> None:
        """Update appearances to make the provided tab appear selected."""
        for tab_id, tab in self.tabs.items():
            if tab_id == selected_tab_id:
                ba.buttonwidget(edit=tab.button,
                                color=(0.5, 0.4, 0.93),
                                textcolor=(0.85, 0.75, 0.95))  # lit
            else:
                ba.buttonwidget(edit=tab.button,
                                color=(0.52, 0.48, 0.63),
                                textcolor=(0.65, 0.6, 0.7))  # unlit

    def _tick_and_call(self, call: Optional[Callable], arg: Any) -> None:
        ba.playsound(ba.getsound('click01'))
        if call is not None:
            call(arg)


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

    # Add a bit more visual spacing as our buttons get narrower.
    tab_spacing = (250.0 - tab_button_width) * 0.06
    positions = []
    sizes = []
    h = pos[0]
    for _i, tab in enumerate(tabs):

        def _tick_and_call(call: Optional[Callable[[Any], Any]],
                           arg: Any) -> None:
            ba.playsound(ba.getsound('click01'))
            if call is not None:
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
