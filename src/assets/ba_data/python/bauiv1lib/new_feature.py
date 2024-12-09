# Released under the MIT License. See LICENSE for details.
#
"""New feature implementation."""

from __future__ import annotations

import bauiv1 as bui

class NewFeatureWindow(bui.Window):
    """Window for the new feature."""

    def __init__(self, transition: str = 'in_right'):
        self._width = 400
        self._height = 300
        self._root_widget = bui.containerwidget(
            size=(self._width, self._height),
            transition=transition
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 50),
            size=(0, 0),
            text="New Feature",
            h_align="center",
            v_align="center",
            maxwidth=self._width * 0.9
        )
        bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width * 0.5 - 50, 50),
            size=(100, 50),
            label="OK",
            on_activate_call=self._ok
        )

    def _ok(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_left')
