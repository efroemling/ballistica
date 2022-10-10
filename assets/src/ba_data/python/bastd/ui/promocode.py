# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for entering promo codes."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import ba
import ba.internal

if TYPE_CHECKING:
    pass


class PromoCodeWindow(ba.Window):
    """Window for entering promo codes."""

    def __init__(
        self, modal: bool = False, origin_widget: ba.Widget | None = None
    ):

        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
            transition = 'in_right'

        width = 450
        height = 230

        self._modal = modal
        self._r = 'promoCodeWindow'

        uiscale = ba.app.ui.uiscale
        super().__init__(
            root_widget=ba.containerwidget(
                size=(width, height),
                transition=transition,
                toolbar_visibility='menu_minimal_no_back',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    2.0
                    if uiscale is ba.UIScale.SMALL
                    else 1.5
                    if uiscale is ba.UIScale.MEDIUM
                    else 1.0
                ),
            )
        )

        btn = ba.buttonwidget(
            parent=self._root_widget,
            scale=0.5,
            position=(40, height - 40),
            size=(60, 60),
            label='',
            on_activate_call=self._do_back,
            autoselect=True,
            color=(0.55, 0.5, 0.6),
            icon=ba.gettexture('crossOut'),
            iconscale=1.2,
        )

        ba.textwidget(
            parent=self._root_widget,
            text=ba.Lstr(resource=self._r + '.codeText'),
            position=(22, height - 113),
            color=(0.8, 0.8, 0.8, 1.0),
            size=(90, 30),
            h_align='right',
        )
        self._text_field = ba.textwidget(
            parent=self._root_widget,
            position=(125, height - 121),
            size=(280, 46),
            text='',
            h_align='left',
            v_align='center',
            max_chars=64,
            color=(0.9, 0.9, 0.9, 1.0),
            description=ba.Lstr(resource=self._r + '.codeText'),
            editable=True,
            padding=4,
            on_return_press_call=self._activate_enter_button,
        )
        ba.widget(edit=btn, down_widget=self._text_field)

        b_width = 200
        self._enter_button = btn2 = ba.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.5 - b_width * 0.5, height - 200),
            size=(b_width, 60),
            scale=1.0,
            label=ba.Lstr(
                resource='submitText', fallback_resource=self._r + '.enterText'
            ),
            on_activate_call=self._do_enter,
        )
        ba.containerwidget(
            edit=self._root_widget,
            cancel_button=btn,
            start_button=btn2,
            selected_child=self._text_field,
        )

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.advanced import AdvancedSettingsWindow

        ba.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        if not self._modal:
            ba.app.ui.set_main_menu_window(
                AdvancedSettingsWindow(transition='in_left').get_root_widget()
            )

    def _activate_enter_button(self) -> None:
        self._enter_button.activate()

    def _do_enter(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings.advanced import AdvancedSettingsWindow

        ba.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        if not self._modal:
            ba.app.ui.set_main_menu_window(
                AdvancedSettingsWindow(transition='in_left').get_root_widget()
            )
        ba.internal.add_transaction(
            {
                'type': 'PROMO_CODE',
                'expire_time': time.time() + 5,
                'code': ba.textwidget(query=self._text_field),
            }
        )
        ba.internal.run_transactions()
