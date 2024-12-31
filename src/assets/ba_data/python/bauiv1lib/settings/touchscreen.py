# Released under the MIT License. See LICENSE for details.
#
"""UI settings functionality related to touchscreens."""
from __future__ import annotations

from typing import override

import bauiv1 as bui
import bascenev1 as bs


class TouchscreenSettingsWindow(bui.MainWindow):
    """Settings window for touchscreens."""

    def __del__(self) -> None:
        bs.set_touchscreen_editing(False)

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ) -> None:
        self._width = 780
        self._height = 380
        self._r = 'configTouchscreenWindow'

        bs.set_touchscreen_editing(True)

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    1.9
                    if uiscale is bui.UIScale.SMALL
                    else 1.55 if uiscale is bui.UIScale.MEDIUM else 1.2
                ),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                stack_offset=(
                    (0, -20) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(55, self._height - 60),
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                scale=0.8,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(25, self._height - 57),
            size=(self._width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            maxwidth=280,
            h_align='center',
            v_align='center',
        )

        self._scroll_width = self._width - 100
        self._scroll_height = self._height - 110
        self._sub_width = self._scroll_width - 20
        self._sub_height = 360

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(
                (self._width - self._scroll_width) * 0.5,
                self._height - 65 - self._scroll_height,
            ),
            size=(self._scroll_width, self._scroll_height),
            claims_left_right=True,
            selection_loops_to_parent=True,
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )
        self._build_gui()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    def _build_gui(self) -> None:
        # pylint: disable=too-many-locals
        from bauiv1lib.config import ConfigNumberEdit, ConfigCheckBox
        from bauiv1lib.radiogroup import make_radio_group

        # Clear anything already there.
        children = self._subcontainer.get_children()
        for child in children:
            child.delete()
        h = 30
        hoffs = 100
        hoffs2 = 70
        hoffs3 = 320
        v = self._sub_height - 85
        clr = (0.8, 0.8, 0.8, 1.0)
        clr2 = (0.8, 0.8, 0.8)
        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v + 63),
            size=(0, 0),
            text=bui.Lstr(resource=f'{self._r}.swipeInfoText'),
            flatness=1.0,
            color=(0, 0.9, 0.1, 0.7),
            maxwidth=self._sub_width * 0.9,
            scale=0.55,
            h_align='center',
            v_align='center',
        )
        cur_val = bui.app.config.get('Touch Movement Control Type', 'swipe')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v - 2),
            size=(0, 30),
            text=bui.Lstr(resource=f'{self._r}.movementText'),
            maxwidth=190,
            color=clr,
            v_align='center',
        )
        cb1 = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(h + hoffs + 220, v),
            size=(170, 30),
            text=bui.Lstr(resource=f'{self._r}.joystickText'),
            maxwidth=100,
            textcolor=clr2,
            scale=0.9,
        )
        cb2 = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(h + hoffs + 357, v),
            size=(170, 30),
            text=bui.Lstr(resource=f'{self._r}.swipeText'),
            maxwidth=100,
            textcolor=clr2,
            value=False,
            scale=0.9,
        )
        make_radio_group(
            (cb1, cb2), ('joystick', 'swipe'), cur_val, self._movement_changed
        )
        v -= 50
        ConfigNumberEdit(
            parent=self._subcontainer,
            position=(h, v),
            xoffset=hoffs2 + 65,
            configkey='Touch Controls Scale Movement',
            displayname=bui.Lstr(
                resource=f'{self._r}.movementControlScaleText'
            ),
            changesound=False,
            minval=0.1,
            maxval=4.0,
            increment=0.1,
        )
        v -= 50
        cur_val = bui.app.config.get('Touch Action Control Type', 'buttons')
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v - 2),
            size=(0, 30),
            text=bui.Lstr(resource=f'{self._r}.actionsText'),
            maxwidth=190,
            color=clr,
            v_align='center',
        )
        cb1 = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(h + hoffs + 220, v),
            size=(170, 30),
            text=bui.Lstr(resource=f'{self._r}.buttonsText'),
            maxwidth=100,
            textcolor=clr2,
            scale=0.9,
        )
        cb2 = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(h + hoffs + 357, v),
            size=(170, 30),
            text=bui.Lstr(resource=f'{self._r}.swipeText'),
            maxwidth=100,
            textcolor=clr2,
            scale=0.9,
        )
        make_radio_group(
            (cb1, cb2), ('buttons', 'swipe'), cur_val, self._actions_changed
        )
        v -= 50
        ConfigNumberEdit(
            parent=self._subcontainer,
            position=(h, v),
            xoffset=hoffs2 + 65,
            configkey='Touch Controls Scale Actions',
            displayname=bui.Lstr(resource=f'{self._r}.actionControlScaleText'),
            changesound=False,
            minval=0.1,
            maxval=4.0,
            increment=0.1,
        )

        v -= 50
        bui.textwidget(
            parent=self._subcontainer,
            position=(h, v - 2),
            size=(0, 30),
            text=bui.Lstr(resource=f'{self._r}.swipeControlsHiddenText'),
            maxwidth=190,
            color=clr,
            v_align='center',
        )

        ConfigCheckBox(
            parent=self._subcontainer,
            position=(h + hoffs3, v),
            size=(100, 30),
            maxwidth=400,
            configkey='Touch Controls Swipe Hidden',
            displayname='',
        )
        v -= 65

        bui.buttonwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5 - 70, v),
            size=(170, 60),
            label=bui.Lstr(resource=f'{self._r}.resetText'),
            scale=0.75,
            on_activate_call=self._reset,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, 38),
            size=(0, 0),
            h_align='center',
            text=bui.Lstr(resource=f'{self._r}.dragControlsText'),
            maxwidth=self._width * 0.8,
            scale=0.65,
            color=(1, 1, 1, 0.4),
        )

    def _actions_changed(self, v: str) -> None:
        cfg = bui.app.config
        cfg['Touch Action Control Type'] = v
        cfg.apply_and_commit()

    def _movement_changed(self, v: str) -> None:
        cfg = bui.app.config
        cfg['Touch Movement Control Type'] = v
        cfg.apply_and_commit()

    def _reset(self) -> None:
        cfg = bui.app.config
        cfgkeys = [
            'Touch Movement Control Type',
            'Touch Action Control Type',
            'Touch Controls Scale',
            'Touch Controls Scale Movement',
            'Touch Controls Scale Actions',
            'Touch Controls Swipe Hidden',
            'Touch DPad X',
            'Touch DPad Y',
            'Touch Buttons X',
            'Touch Buttons Y',
        ]
        for cfgkey in cfgkeys:
            if cfgkey in cfg:
                del cfg[cfgkey]
        cfg.apply_and_commit()
        bui.apptimer(0, self._build_gui)
