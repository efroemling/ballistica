# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""UI functionality for creating radio groups of buttons."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import List, Any, Callable, Sequence


def make_radio_group(check_boxes: Sequence[ba.Widget],
                     value_names: Sequence[str], value: str,
                     value_change_call: Callable[[str], Any]) -> None:
    """Link the provided check_boxes together into a radio group."""

    def _radio_press(check_string: str, other_check_boxes: List[ba.Widget],
                     val: int) -> None:
        if val == 1:
            value_change_call(check_string)
            for cbx in other_check_boxes:
                ba.checkboxwidget(edit=cbx, value=False)

    for i, check_box in enumerate(check_boxes):
        ba.checkboxwidget(edit=check_box,
                          value=(value == value_names[i]),
                          is_radio_button=True,
                          on_value_change_call=ba.Call(
                              _radio_press, value_names[i],
                              [c for c in check_boxes if c != check_box]))
