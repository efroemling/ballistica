# Released under the MIT License. See LICENSE for details.
#
"""Bits of utility functionality related to co-op levels."""

from __future__ import annotations

import ba


class CoopLevelLockedWindow(ba.Window):
    """Window showing that a level is locked."""

    def __init__(self, name: ba.Lstr, dep_name: ba.Lstr):
        width = 550.0
        height = 250.0
        lock_tex = ba.gettexture('lock')
        uiscale = ba.app.ui.uiscale
        super().__init__(
            root_widget=ba.containerwidget(
                size=(width, height),
                transition='in_right',
                scale=(
                    1.7
                    if uiscale is ba.UIScale.SMALL
                    else 1.3
                    if uiscale is ba.UIScale.MEDIUM
                    else 1.0
                ),
            )
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(150 - 20, height * 0.63),
            size=(0, 0),
            h_align='left',
            v_align='center',
            text=ba.Lstr(
                resource='levelIsLockedText', subs=[('${LEVEL}', name)]
            ),
            maxwidth=400,
            color=(1, 0.8, 0.3, 1),
            scale=1.1,
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(150 - 20, height * 0.48),
            size=(0, 0),
            h_align='left',
            v_align='center',
            text=ba.Lstr(
                resource='levelMustBeCompletedFirstText',
                subs=[('${LEVEL}', dep_name)],
            ),
            maxwidth=400,
            color=ba.app.ui.infotextcolor,
            scale=0.8,
        )
        ba.imagewidget(
            parent=self._root_widget,
            position=(56 - 20, height * 0.39),
            size=(80, 80),
            texture=lock_tex,
            opacity=1.0,
        )
        btn = ba.buttonwidget(
            parent=self._root_widget,
            position=((width - 140) / 2, 30),
            size=(140, 50),
            label=ba.Lstr(resource='okText'),
            on_activate_call=self._ok,
        )
        ba.containerwidget(
            edit=self._root_widget, selected_child=btn, start_button=btn
        )
        ba.playsound(ba.getsound('error'))

    def _ok(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_left')
