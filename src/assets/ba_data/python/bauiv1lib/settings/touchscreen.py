# Released under the MIT License. See LICENSE for details.
#
"""UI settings functionality related to touchscreens."""

from typing import override

import bauiv1 as bui
from bauiv1 import _commonassets, classicassets
from bauiv1lib.utils import (
    get_screen_margins,
    scroll_fade_bottom,
    scroll_fade_top,
)

import bascenev1 as bs

_tsstrs = classicassets.strings.settings.controllers.touchscreen


class TouchscreenSettingsWindow(bui.MainWindow):
    """Settings window for touchscreens."""

    def __del__(self) -> None:
        bs.set_touchscreen_editing(False)

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ) -> None:
        self._r = 'configTouchscreenWindow'

        bs.set_touchscreen_editing(True)

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1200.0 if uiscale is bui.UIScale.SMALL else 780.0
        self._height = 800.0 if uiscale is bui.UIScale.SMALL else 500.0

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.9
            if uiscale is bui.UIScale.SMALL
            else 1.25 if uiscale is bui.UIScale.MEDIUM else 1.1
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        self._scroll_width = target_width
        self._scroll_height = target_height - 47
        self._scroll_bottom = yoffs - 78 - self._scroll_height

        # In medium/large, sit the scroll area (and the drag-note
        # below it) a bit closer to the title and back button.
        if uiscale is not bui.UIScale.SMALL:
            self._scroll_bottom += 15.0

        # In small ui we extend our scrollable area out into the screen
        # margins (space between the virtual bounds and the actual
        # screen edges) while keeping content laid out within the
        # virtual bounds.
        margin_left, margin_right, margin_bottom, margin_top = (
            get_screen_margins(scale)
            if uiscale is bui.UIScale.SMALL
            else (0.0, 0.0, 0.0, 0.0)
        )

        # In small ui we also extend the scroll's top edge all the way
        # up to the top of the screen; soft blobs then keep our title
        # legible over any content scrolled up there. Content gets
        # padded to stay clear of the faded areas.
        top_extend = (
            (0.5 * self._height + 0.5 * (screensize[1] / scale))
            - (self._scroll_bottom + self._scroll_height)
            + margin_top
            if uiscale is bui.UIScale.SMALL
            else 0.0
        )

        # Extra padding above and below our content so the soft blobs
        # fading things out at the screen's top and bottom edges don't
        # eat into it.
        top_pad = 15.0 if uiscale is bui.UIScale.SMALL else 0.0
        bottom_pad = (
            50.0 + margin_bottom if uiscale is bui.UIScale.SMALL else 0.0
        )

        # Total dead space above our content within the subcontainer
        # (used by our layout code).
        self._content_top_offs = top_extend + top_pad

        self._sub_width = 660.0
        self._sub_height = 360.0 + self._content_top_offs + bottom_pad

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=scale,
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(55, yoffs - 59),
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                scale=0.8,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 - self._scroll_width * 0.5 - margin_left,
                self._scroll_bottom - margin_bottom,
            ),
            size=(
                self._scroll_width + margin_left + margin_right,
                self._scroll_height + margin_bottom + top_extend,
            ),
            highlight=False,
            border_opacity=0.4,
            center_small_content=True,
            center_small_content_horizontally=True,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )

        # Our scroll area extends to the screen edges; these soft blobs
        # (plus the title and drag-note being drawn after the scroll
        # area) keep those legible over content scrolled near them.
        # Note that we intentionally use the original
        # un-margin-extended scroll geometry here so the blobs coincide
        # with that text, which doesn't move when we extend out into
        # screen margins.
        if uiscale is bui.UIScale.SMALL:
            scroll_fade_top(
                self._root_widget,
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
                # Nudge the blobs up so their most-opaque core covers
                # our title area.
                yoffs_extra=30.0,
            )
            scroll_fade_bottom(
                self._root_widget,
                self._width * 0.5 - self._scroll_width * 0.5,
                self._scroll_bottom,
                self._scroll_width,
                self._scroll_height,
                center=True,
                # Nudge the blobs up a bit so their most-opaque core
                # covers our drag-note area.
                yoffs_extra=15.0,
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                yoffs - (53 if uiscale is bui.UIScale.SMALL else 35),
            ),
            size=(0, 0),
            text=_tsstrs.title,
            color=bui.app.ui_v1.title_color,
            maxwidth=280,
            h_align='center',
            v_align='center',
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                (
                    self._scroll_bottom + 30
                    if uiscale is bui.UIScale.SMALL
                    else self._scroll_bottom - 20
                ),
            ),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=_tsstrs.drag_controls,
            maxwidth=self._scroll_width * 0.8,
            scale=0.65,
            color=(1, 1, 1, 0.4),
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

    @override
    def main_window_should_preserve_selection(self) -> bool:
        # TODO: Wire this up.
        return False

    def _build_gui(self) -> None:
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
        # (start below any top-edge extension/padding so content sits
        # clear of the soft blobs fading things out up there).
        v = self._sub_height - self._content_top_offs - 85
        clr = (0.8, 0.8, 0.8, 1.0)
        clr2 = (0.8, 0.8, 0.8)
        bui.textwidget(
            parent=self._subcontainer,
            position=(self._sub_width * 0.5, v + 63),
            size=(0, 0),
            text=_tsstrs.swipe_info,
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
            text=_tsstrs.movement,
            maxwidth=190,
            color=clr,
            v_align='center',
        )
        cb1 = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(h + hoffs + 220, v),
            size=(170, 30),
            text=_tsstrs.joystick,
            maxwidth=100,
            textcolor=clr2,
            scale=0.9,
        )
        cb2 = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(h + hoffs + 357, v),
            size=(170, 30),
            text=_tsstrs.swipe,
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
            displayname=_tsstrs.movement_control_scale,
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
            text=_tsstrs.actions,
            maxwidth=190,
            color=clr,
            v_align='center',
        )
        cb1 = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(h + hoffs + 220, v),
            size=(170, 30),
            text=_tsstrs.buttons,
            maxwidth=100,
            textcolor=clr2,
            scale=0.9,
        )
        cb2 = bui.checkboxwidget(
            parent=self._subcontainer,
            position=(h + hoffs + 357, v),
            size=(170, 30),
            text=_tsstrs.swipe,
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
            displayname=_tsstrs.action_control_scale,
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
            text=_tsstrs.swipe_controls_hidden,
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
            label=_commonassets.strings.actions.reset,
            scale=0.75,
            on_activate_call=self._reset,
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
