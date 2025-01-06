# Released under the MIT License. See LICENSE for details.
#
"""Provides a picker for icons."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, override

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Sequence


class IconPickerDelegate:
    """Delegate for character-picker."""

    def on_icon_picker_pick(self, icon: str) -> None:
        """Called when a character is selected."""
        raise NotImplementedError()

    def on_icon_picker_get_more_press(self) -> None:
        """Called when the 'get more characters' button is pressed."""
        raise NotImplementedError()


class IconPicker(PopupWindow):
    """Picker for icons."""

    def __init__(
        self,
        parent: bui.Widget,
        position: tuple[float, float] = (0.0, 0.0),
        delegate: IconPickerDelegate | None = None,
        scale: float | None = None,
        *,
        offset: tuple[float, float] = (0.0, 0.0),
        tint_color: Sequence[float] = (1.0, 1.0, 1.0),
        tint2_color: Sequence[float] = (1.0, 1.0, 1.0),
        selected_icon: str | None = None,
    ):
        # pylint: disable=too-many-locals
        del parent  # unused here
        del tint_color  # unused_here
        del tint2_color  # unused here
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (
                1.85
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            )

        self._delegate = delegate
        self._transitioning_out = False

        assert bui.app.classic is not None
        self._icons = [
            bui.charstr(bui.SpecialChar.LOGO)
        ] + bui.app.classic.accounts.get_purchased_icons()
        count = len(self._icons)
        columns = 4
        rows = int(math.ceil(float(count) / columns))

        button_width = 50
        button_height = 50
        button_buffer_h = 10
        button_buffer_v = 5

        self._width = 10 + columns * (button_width + 2 * button_buffer_h) * (
            1.0 / 0.95
        ) * (1.0 / 0.8)
        self._height = self._width * (
            0.8 if uiscale is bui.UIScale.SMALL else 1.06
        )

        self._scroll_width = self._width * 0.8
        self._scroll_height = self._height * 0.8
        self._scroll_position = (
            (self._width - self._scroll_width) * 0.5,
            (self._height - self._scroll_height) * 0.5,
        )

        # creates our _root_widget
        super().__init__(
            position=position,
            size=(self._width, self._height),
            scale=scale,
            bg_color=(0.5, 0.5, 0.5),
            offset=offset,
            focus_position=self._scroll_position,
            focus_size=(self._scroll_width, self._scroll_height),
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self.root_widget,
            size=(self._scroll_width, self._scroll_height),
            color=(0.55, 0.55, 0.55),
            highlight=False,
            position=self._scroll_position,
        )
        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = (
            5 + rows * (button_height + 2 * button_buffer_v) + 100
        )
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
        )
        index = 0
        for y in range(rows):
            for x in range(columns):
                pos = (
                    x * (button_width + 2 * button_buffer_h) + button_buffer_h,
                    self._sub_height
                    - (y + 1) * (button_height + 2 * button_buffer_v)
                    + 0,
                )
                btn = bui.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    size=(button_width, button_height),
                    autoselect=True,
                    text_scale=1.2,
                    label='',
                    color=(0.65, 0.65, 0.65),
                    on_activate_call=bui.Call(
                        self._select_icon, self._icons[index]
                    ),
                    position=pos,
                )
                bui.textwidget(
                    parent=self._subcontainer,
                    h_align='center',
                    v_align='center',
                    size=(0, 0),
                    position=(pos[0] + 0.5 * button_width - 1, pos[1] + 15),
                    draw_controller=btn,
                    text=self._icons[index],
                    scale=1.8,
                )
                bui.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)
                if self._icons[index] == selected_icon:
                    bui.containerwidget(
                        edit=self._subcontainer,
                        selected_child=btn,
                        visible_child=btn,
                    )
                index += 1

                if index >= count:
                    break
            if index >= count:
                break
        self._get_more_icons_button = btn = bui.buttonwidget(
            parent=self._subcontainer,
            size=(self._sub_width * 0.8, 60),
            position=(self._sub_width * 0.1, 30),
            label=bui.Lstr(resource='editProfileWindow.getMoreIconsText'),
            on_activate_call=self._on_store_press,
            color=(0.6, 0.6, 0.6),
            textcolor=(0.8, 0.8, 0.8),
            autoselect=True,
        )
        bui.widget(edit=btn, show_buffer_top=30, show_buffer_bottom=30)

    def _on_store_press(self) -> None:
        from bauiv1lib.account.signin import show_sign_in_prompt

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return

        if self._delegate is not None:
            self._delegate.on_icon_picker_get_more_press()

        self._transition_out()

    def _select_icon(self, icon: str) -> None:
        if self._delegate is not None:
            self._delegate.on_icon_picker_pick(icon)
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()
