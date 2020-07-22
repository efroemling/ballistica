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
"""UI settings functionality related to touchscreens."""
from __future__ import annotations

import _ba
import ba


class TouchscreenSettingsWindow(ba.Window):
    """Settings window for touchscreens."""

    def __del__(self) -> None:
        # Note - this happens in 'back' too;
        # we just do it here too in case the window is closed by other means.

        # FIXME: Could switch to a UI destroy callback now that those are a
        #  thing that exists.
        _ba.set_touchscreen_editing(False)

    def __init__(self) -> None:

        self._width = 650
        self._height = 380
        self._spacing = 40
        self._r = 'configTouchscreenWindow'

        _ba.set_touchscreen_editing(True)

        uiscale = ba.app.ui.uiscale
        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition='in_right',
            scale=(1.9 if uiscale is ba.UIScale.SMALL else
                   1.55 if uiscale is ba.UIScale.MEDIUM else 1.2)))

        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(55, self._height - 60),
                              size=(120, 60),
                              label=ba.Lstr(resource='backText'),
                              button_type='back',
                              scale=0.8,
                              on_activate_call=self._back)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)

        ba.textwidget(parent=self._root_widget,
                      position=(25, self._height - 50),
                      size=(self._width, 25),
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      color=ba.app.ui.title_color,
                      maxwidth=280,
                      h_align='center',
                      v_align='center')

        ba.buttonwidget(edit=btn,
                        button_type='backSmall',
                        size=(60, 60),
                        label=ba.charstr(ba.SpecialChar.BACK))

        self._scroll_width = self._width - 100
        self._scroll_height = self._height - 110
        self._sub_width = self._scroll_width - 20
        self._sub_height = 360

        self._scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            position=((self._width - self._scroll_width) * 0.5,
                      self._height - 65 - self._scroll_height),
            size=(self._scroll_width, self._scroll_height),
            claims_left_right=True,
            claims_tab=True,
            selection_loops_to_parent=True)
        self._subcontainer = ba.containerwidget(parent=self._scrollwidget,
                                                size=(self._sub_width,
                                                      self._sub_height),
                                                background=False,
                                                claims_left_right=True,
                                                claims_tab=True,
                                                selection_loops_to_parent=True)
        self._build_gui()

    def _build_gui(self) -> None:
        from bastd.ui.config import ConfigNumberEdit, ConfigCheckBox
        from bastd.ui.radiogroup import make_radio_group

        # Clear anything already there.
        children = self._subcontainer.get_children()
        for child in children:
            child.delete()
        h = 30
        v = self._sub_height - 85
        clr = (0.8, 0.8, 0.8, 1.0)
        clr2 = (0.8, 0.8, 0.8)
        ba.textwidget(parent=self._subcontainer,
                      position=(-10, v + 43),
                      size=(self._sub_width, 25),
                      text=ba.Lstr(resource=self._r + '.swipeInfoText'),
                      flatness=1.0,
                      color=(0, 0.9, 0.1, 0.7),
                      maxwidth=self._sub_width * 0.9,
                      scale=0.55,
                      h_align='center',
                      v_align='center')
        cur_val = ba.app.config.get('Touch Movement Control Type', 'swipe')
        ba.textwidget(parent=self._subcontainer,
                      position=(h, v - 2),
                      size=(0, 30),
                      text=ba.Lstr(resource=self._r + '.movementText'),
                      maxwidth=190,
                      color=clr,
                      v_align='center')
        cb1 = ba.checkboxwidget(parent=self._subcontainer,
                                position=(h + 220, v),
                                size=(170, 30),
                                text=ba.Lstr(resource=self._r +
                                             '.joystickText'),
                                maxwidth=100,
                                textcolor=clr2,
                                scale=0.9)
        cb2 = ba.checkboxwidget(parent=self._subcontainer,
                                position=(h + 357, v),
                                size=(170, 30),
                                text=ba.Lstr(resource=self._r + '.swipeText'),
                                maxwidth=100,
                                textcolor=clr2,
                                value=False,
                                scale=0.9)
        make_radio_group((cb1, cb2), ('joystick', 'swipe'), cur_val,
                         self._movement_changed)
        v -= 50
        ConfigNumberEdit(parent=self._subcontainer,
                         position=(h, v),
                         xoffset=65,
                         configkey='Touch Controls Scale Movement',
                         displayname=ba.Lstr(resource=self._r +
                                             '.movementControlScaleText'),
                         changesound=False,
                         minval=0.1,
                         maxval=4.0,
                         increment=0.1)
        v -= 50
        cur_val = ba.app.config.get('Touch Action Control Type', 'buttons')
        ba.textwidget(parent=self._subcontainer,
                      position=(h, v - 2),
                      size=(0, 30),
                      text=ba.Lstr(resource=self._r + '.actionsText'),
                      maxwidth=190,
                      color=clr,
                      v_align='center')
        cb1 = ba.checkboxwidget(parent=self._subcontainer,
                                position=(h + 220, v),
                                size=(170, 30),
                                text=ba.Lstr(resource=self._r +
                                             '.buttonsText'),
                                maxwidth=100,
                                textcolor=clr2,
                                scale=0.9)
        cb2 = ba.checkboxwidget(parent=self._subcontainer,
                                position=(h + 357, v),
                                size=(170, 30),
                                text=ba.Lstr(resource=self._r + '.swipeText'),
                                maxwidth=100,
                                textcolor=clr2,
                                scale=0.9)
        make_radio_group((cb1, cb2), ('buttons', 'swipe'), cur_val,
                         self._actions_changed)
        v -= 50
        ConfigNumberEdit(parent=self._subcontainer,
                         position=(h, v),
                         xoffset=65,
                         configkey='Touch Controls Scale Actions',
                         displayname=ba.Lstr(resource=self._r +
                                             '.actionControlScaleText'),
                         changesound=False,
                         minval=0.1,
                         maxval=4.0,
                         increment=0.1)

        v -= 50
        ConfigCheckBox(parent=self._subcontainer,
                       position=(h, v),
                       size=(400, 30),
                       maxwidth=400,
                       configkey='Touch Controls Swipe Hidden',
                       displayname=ba.Lstr(resource=self._r +
                                           '.swipeControlsHiddenText'))
        v -= 65

        ba.buttonwidget(parent=self._subcontainer,
                        position=(self._sub_width * 0.5 - 70, v),
                        size=(170, 60),
                        label=ba.Lstr(resource=self._r + '.resetText'),
                        scale=0.75,
                        on_activate_call=self._reset)

        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, 38),
                      size=(0, 0),
                      h_align='center',
                      text=ba.Lstr(resource=self._r + '.dragControlsText'),
                      maxwidth=self._width * 0.8,
                      scale=0.65,
                      color=(1, 1, 1, 0.4))

    def _actions_changed(self, v: str) -> None:
        cfg = ba.app.config
        cfg['Touch Action Control Type'] = v
        cfg.apply_and_commit()

    def _movement_changed(self, v: str) -> None:
        cfg = ba.app.config
        cfg['Touch Movement Control Type'] = v
        cfg.apply_and_commit()

    def _reset(self) -> None:
        cfg = ba.app.config
        cfgkeys = [
            'Touch Movement Control Type', 'Touch Action Control Type',
            'Touch Controls Scale', 'Touch Controls Scale Movement',
            'Touch Controls Scale Actions', 'Touch Controls Swipe Hidden',
            'Touch DPad X', 'Touch DPad Y', 'Touch Buttons X',
            'Touch Buttons Y'
        ]
        for cfgkey in cfgkeys:
            if cfgkey in cfg:
                del cfg[cfgkey]
        cfg.apply_and_commit()
        ba.timer(0, self._build_gui, timetype=ba.TimeType.REAL)

    def _back(self) -> None:
        from bastd.ui.settings import controls
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            controls.ControlsSettingsWindow(
                transition='in_left').get_root_widget())
        _ba.set_touchscreen_editing(False)
