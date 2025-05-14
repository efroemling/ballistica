# Released under the MIT License. See LICENSE for details.
#
"""Provides a picker for characters."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, override

from bauiv1lib.popup import PopupWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Sequence


class CharacterPickerDelegate:
    """Delegate for character-picker."""

    def on_character_picker_pick(self, character: str) -> None:
        """Called when a character is selected."""
        raise NotImplementedError()

    def on_character_picker_get_more_press(self) -> None:
        """Called when the 'get more characters' button is pressed."""
        raise NotImplementedError()


class CharacterPicker(PopupWindow):
    """Popup window for selecting characters."""

    def __init__(
        self,
        parent: bui.Widget,
        position: tuple[float, float] = (0.0, 0.0),
        delegate: CharacterPickerDelegate | None = None,
        scale: float | None = None,
        offset: tuple[float, float] = (0.0, 0.0),
        tint_color: Sequence[float] = (1.0, 1.0, 1.0),
        tint2_color: Sequence[float] = (1.0, 1.0, 1.0),
        selected_character: str | None = None,
    ):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-positional-arguments
        from bascenev1lib.actor import spazappearance

        assert bui.app.classic is not None

        del parent  # unused here
        uiscale = bui.app.ui_v1.uiscale
        if scale is None:
            scale = (
                1.85
                if uiscale is bui.UIScale.SMALL
                else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
            )

        self._delegate = delegate
        self._transitioning_out = False

        # make a list of spaz icons
        self._spazzes = spazappearance.get_appearances()
        self._spazzes.sort()
        self._icon_textures = [
            bui.gettexture(bui.app.classic.spaz_appearances[s].icon_texture)
            for s in self._spazzes
        ]
        self._icon_tint_textures = [
            bui.gettexture(
                bui.app.classic.spaz_appearances[s].icon_mask_texture
            )
            for s in self._spazzes
        ]

        count = len(self._spazzes)

        columns = 3
        rows = int(math.ceil(float(count) / columns))

        button_width = 100
        button_height = 100
        button_buffer_h = 10
        button_buffer_v = 15

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

        # Creates our _root_widget.
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
        mask_texture = bui.gettexture('characterIconMask')
        for y in range(rows):
            for x in range(columns):
                pos = (
                    x * (button_width + 2 * button_buffer_h) + button_buffer_h,
                    self._sub_height
                    - (y + 1) * (button_height + 2 * button_buffer_v)
                    + 12,
                )
                btn = bui.buttonwidget(
                    parent=self._subcontainer,
                    button_type='square',
                    size=(button_width, button_height),
                    autoselect=True,
                    texture=self._icon_textures[index],
                    tint_texture=self._icon_tint_textures[index],
                    mask_texture=mask_texture,
                    label='',
                    color=(1, 1, 1),
                    tint_color=tint_color,
                    tint2_color=tint2_color,
                    on_activate_call=bui.Call(
                        self._select_character, self._spazzes[index]
                    ),
                    position=pos,
                )
                bui.widget(edit=btn, show_buffer_top=60, show_buffer_bottom=60)
                if self._spazzes[index] == selected_character:
                    bui.containerwidget(
                        edit=self._subcontainer,
                        selected_child=btn,
                        visible_child=btn,
                    )
                name = bui.Lstr(
                    translate=('characterNames', self._spazzes[index])
                )
                bui.textwidget(
                    parent=self._subcontainer,
                    text=name,
                    position=(pos[0] + button_width * 0.5, pos[1] - 12),
                    size=(0, 0),
                    scale=0.5,
                    maxwidth=button_width,
                    draw_controller=btn,
                    h_align='center',
                    v_align='center',
                    color=(0.8, 0.8, 0.8, 0.8),
                )
                index += 1

                if index >= count:
                    break
            if index >= count:
                break
        self._get_more_characters_button = btn = bui.buttonwidget(
            parent=self._subcontainer,
            size=(self._sub_width * 0.8, 60),
            position=(self._sub_width * 0.1, 30),
            label=bui.Lstr(resource='editProfileWindow.getMoreCharactersText'),
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
            self._delegate.on_character_picker_get_more_press()

        self._transition_out()

    def _select_character(self, character: str) -> None:
        if self._delegate is not None:
            self._delegate.on_character_picker_pick(character)
        self._transition_out()

    def _transition_out(self) -> None:
        if not self._transitioning_out:
            self._transitioning_out = True
            bui.containerwidget(edit=self.root_widget, transition='out_scale')

    @override
    def on_popup_cancel(self) -> None:
        bui.getsound('swish').play()
        self._transition_out()
