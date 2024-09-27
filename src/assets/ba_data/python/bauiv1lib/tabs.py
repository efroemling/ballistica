# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for creating tab style buttons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, Generic

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


@dataclass
class Tab:
    """Info for an individual tab in a TabRow"""

    button: bui.Widget
    position: tuple[float, float]
    size: tuple[float, float]


T = TypeVar('T')


class TabRow(Generic[T]):
    """Encapsulates a row of tab-styled buttons.

    Tabs are indexed by id which is an arbitrary user-provided type.
    """

    def __init__(
        self,
        parent: bui.Widget,
        tabdefs: list[tuple[T, bui.Lstr]],
        pos: tuple[float, float],
        size: tuple[float, float],
        *,
        on_select_call: Callable[[T], None] | None = None,
    ) -> None:
        if not tabdefs:
            raise ValueError('At least one tab def is required')
        self.tabs: dict[T, Tab] = {}
        tab_pos_v = pos[1]
        tab_button_width = float(size[0]) / len(tabdefs)
        tab_spacing = (250.0 - tab_button_width) * 0.06
        h = pos[0]
        for tab_id, tab_label in tabdefs:
            pos = (h + tab_spacing * 0.5, tab_pos_v)
            size = (tab_button_width - tab_spacing, 50.0)
            btn = bui.buttonwidget(
                parent=parent,
                position=pos,
                autoselect=True,
                button_type='tab',
                size=size,
                label=tab_label,
                enable_sound=False,
                on_activate_call=bui.Call(
                    self._tick_and_call, on_select_call, tab_id
                ),
            )
            h += tab_button_width
            self.tabs[tab_id] = Tab(button=btn, position=pos, size=size)

    def update_appearance(self, selected_tab_id: T) -> None:
        """Update appearances to make the provided tab appear selected."""
        for tab_id, tab in self.tabs.items():
            if tab_id == selected_tab_id:
                bui.buttonwidget(
                    edit=tab.button,
                    color=(0.5, 0.4, 0.93),
                    textcolor=(0.85, 0.75, 0.95),
                )  # lit
            else:
                bui.buttonwidget(
                    edit=tab.button,
                    color=(0.52, 0.48, 0.63),
                    textcolor=(0.65, 0.6, 0.7),
                )  # unlit

    def _tick_and_call(
        self, call: Callable[[Any], None] | None, arg: Any
    ) -> None:
        bui.getsound('click01').play()
        if call is not None:
            call(arg)
