# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for linking accounts."""

from __future__ import annotations

import copy
import time
from typing import TYPE_CHECKING

import ba
import ba.internal

if TYPE_CHECKING:
    from typing import Any


class AccountLinkWindow(ba.Window):
    """Window for linking accounts."""

    def __init__(self, origin_widget: ba.Widget | None = None):
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
            transition = 'in_right'
        bg_color = (0.4, 0.4, 0.5)
        self._width = 560
        self._height = 420
        uiscale = ba.app.ui.uiscale
        base_scale = (
            1.65
            if uiscale is ba.UIScale.SMALL
            else 1.5
            if uiscale is ba.UIScale.MEDIUM
            else 1.1
        )
        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height),
                transition=transition,
                scale=base_scale,
                scale_origin_stack_offset=scale_origin,
                stack_offset=(0, -10)
                if uiscale is ba.UIScale.SMALL
                else (0, 0),
            )
        )
        self._cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(40, self._height - 45),
            size=(50, 50),
            scale=0.7,
            label='',
            color=bg_color,
            on_activate_call=self._cancel,
            autoselect=True,
            icon=ba.gettexture('crossOut'),
            iconscale=1.2,
        )
        maxlinks = ba.internal.get_v1_account_misc_read_val(
            'maxLinkAccounts', 5
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.56),
            size=(0, 0),
            text=ba.Lstr(
                resource=(
                    'accountSettingsWindow.linkAccountsInstructionsNewText'
                ),
                subs=[('${COUNT}', str(maxlinks))],
            ),
            maxwidth=self._width * 0.9,
            color=ba.app.ui.infotextcolor,
            max_height=self._height * 0.6,
            h_align='center',
            v_align='center',
        )
        ba.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )
        ba.buttonwidget(
            parent=self._root_widget,
            position=(40, 30),
            size=(200, 60),
            label=ba.Lstr(
                resource='accountSettingsWindow.linkAccountsGenerateCodeText'
            ),
            autoselect=True,
            on_activate_call=self._generate_press,
        )
        self._enter_code_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 240, 30),
            size=(200, 60),
            label=ba.Lstr(
                resource='accountSettingsWindow.linkAccountsEnterCodeText'
            ),
            autoselect=True,
            on_activate_call=self._enter_code_press,
        )

    def _generate_press(self) -> None:
        from bastd.ui import account

        if ba.internal.get_v1_account_state() != 'signed_in':
            account.show_sign_in_prompt()
            return
        ba.screenmessage(
            ba.Lstr(resource='gatherWindow.requestingAPromoCodeText'),
            color=(0, 1, 0),
        )
        ba.internal.add_transaction(
            {
                'type': 'ACCOUNT_LINK_CODE_REQUEST',
                'expire_time': time.time() + 5,
            }
        )
        ba.internal.run_transactions()

    def _enter_code_press(self) -> None:
        from bastd.ui import promocode

        promocode.PromoCodeWindow(
            modal=True, origin_widget=self._enter_code_button
        )
        ba.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

    def _cancel(self) -> None:
        ba.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )


class AccountLinkCodeWindow(ba.Window):
    """Window showing code for account-linking."""

    def __init__(self, data: dict[str, Any]):
        self._width = 350
        self._height = 200
        uiscale = ba.app.ui.uiscale
        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height),
                color=(0.45, 0.63, 0.15),
                transition='in_scale',
                scale=(
                    1.8
                    if uiscale is ba.UIScale.SMALL
                    else 1.35
                    if uiscale is ba.UIScale.MEDIUM
                    else 1.0
                ),
            )
        )
        self._data = copy.deepcopy(data)
        ba.playsound(ba.getsound('cashRegister'))
        ba.playsound(ba.getsound('swish'))
        self._cancel_button = ba.buttonwidget(
            parent=self._root_widget,
            scale=0.5,
            position=(40, self._height - 40),
            size=(50, 50),
            label='',
            on_activate_call=self.close,
            autoselect=True,
            color=(0.45, 0.63, 0.15),
            icon=ba.gettexture('crossOut'),
            iconscale=1.2,
        )
        ba.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=2.0,
            h_align='center',
            v_align='center',
            text=data['code'],
            maxwidth=self._width * 0.85,
        )

    def close(self) -> None:
        """close the window"""
        ba.containerwidget(edit=self._root_widget, transition='out_scale')
