# Released under the MIT License. See LICENSE for details.
#
"""Bits of utility functionality related to co-op levels."""

from __future__ import annotations

import bauiv1 as bui


class CoopLevelLockedWindow(bui.Window):
    """Window showing that a level is locked."""

    def __init__(self, name: bui.Lstr, dep_name: bui.Lstr):
        width = 550.0
        height = 250.0
        lock_tex = bui.gettexture('lock')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                transition='in_right',
                scale=(
                    1.7
                    if uiscale is bui.UIScale.SMALL
                    else 1.3 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
            )
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(150 - 20, height * 0.63),
            size=(0, 0),
            h_align='left',
            v_align='center',
            text=bui.Lstr(
                resource='levelIsLockedText', subs=[('${LEVEL}', name)]
            ),
            maxwidth=400,
            color=(1, 0.8, 0.3, 1),
            scale=1.1,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(150 - 20, height * 0.48),
            size=(0, 0),
            h_align='left',
            v_align='center',
            text=bui.Lstr(
                resource='levelMustBeCompletedFirstText',
                subs=[('${LEVEL}', dep_name)],
            ),
            maxwidth=400,
            color=bui.app.ui_v1.infotextcolor,
            scale=0.8,
        )
        bui.imagewidget(
            parent=self._root_widget,
            position=(56 - 20, height * 0.39),
            size=(80, 80),
            texture=lock_tex,
            opacity=1.0,
        )
        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=((width - 140) / 2, 30),
            size=(140, 50),
            label=bui.Lstr(resource='okText'),
            on_activate_call=self._ok,
        )
        bui.containerwidget(
            edit=self._root_widget, selected_child=btn, start_button=btn
        )
        bui.getsound('error').play()

    def _ok(self) -> None:
        bui.containerwidget(edit=self._root_widget, transition='out_left')
