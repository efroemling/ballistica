# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for creating radio groups of buttons."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable, Sequence


def make_radio_group(
    check_boxes: Sequence[bui.Widget],
    value_names: Sequence[str],
    value: str,
    value_change_call: Callable[[str], Any],
) -> None:
    """Link the provided check_boxes together into a radio group."""

    def _radio_press(
        check_string: str, other_check_boxes: list[bui.Widget], val: int
    ) -> None:
        if val == 1:
            value_change_call(check_string)
            for cbx in other_check_boxes:
                bui.checkboxwidget(edit=cbx, value=False)

    for i, check_box in enumerate(check_boxes):
        bui.checkboxwidget(
            edit=check_box,
            value=(value == value_names[i]),
            is_radio_button=True,
            on_value_change_call=bui.Call(
                _radio_press,
                value_names[i],
                [c for c in check_boxes if c != check_box],
            ),
        )
