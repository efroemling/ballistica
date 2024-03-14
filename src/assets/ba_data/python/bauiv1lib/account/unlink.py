# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for unlinking accounts."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class AccountUnlinkWindow(bui.Window):
    """A window to kick off account unlinks."""

    def __init__(self, origin_widget: bui.Widget | None = None):
        plus = bui.app.plus
        assert plus is not None

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
        self._width = 540
        self._height = 350
        self._scroll_width = 400
        self._scroll_height = 200
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        base_scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.6 if uiscale is bui.UIScale.MEDIUM else 1.1
        )
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition=transition,
                scale=base_scale,
                scale_origin_stack_offset=scale_origin,
                stack_offset=(
                    (0, -10) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            )
        )
        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(30, self._height - 50),
            size=(50, 50),
            scale=0.7,
            label='',
            color=bg_color,
            on_activate_call=self._cancel,
            autoselect=True,
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.88),
            size=(0, 0),
            text=bui.Lstr(
                resource='accountSettingsWindow.unlinkAccountsInstructionsText'
            ),
            maxwidth=self._width * 0.7,
            color=bui.app.ui_v1.infotextcolor,
            h_align='center',
            v_align='center',
        )
        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            position=(
                (self._width - self._scroll_width) * 0.5,
                self._height - 85 - self._scroll_height,
            ),
            size=(self._scroll_width, self._scroll_height),
        )
        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget, border=2, margin=0, left_border=10
        )

        our_login_id = plus.get_v1_account_public_login_id()
        if our_login_id is None:
            entries = []
        else:
            account_infos = plus.get_v1_account_misc_read_val_2(
                'linkedAccounts2', []
            )
            entries = [
                {'name': ai['d'], 'id': ai['id']}
                for ai in account_infos
                if ai['id'] != our_login_id
            ]

        # (avoid getting our selection stuck on an empty column widget)
        if not entries:
            bui.containerwidget(edit=self._scrollwidget, selectable=False)
        for i, entry in enumerate(entries):
            txt = bui.textwidget(
                parent=self._columnwidget,
                selectable=True,
                text=entry['name'],
                size=(self._scroll_width - 30, 30),
                autoselect=True,
                click_activate=True,
                on_activate_call=bui.Call(self._on_entry_selected, entry),
            )
            bui.widget(edit=txt, left_widget=self._cancel_button)
            if i == 0:
                bui.widget(edit=txt, up_widget=self._cancel_button)

    def _on_entry_selected(self, entry: dict[str, Any]) -> None:
        plus = bui.app.plus
        assert plus is not None

        bui.screenmessage(
            bui.Lstr(
                resource='pleaseWaitText', fallback_resource='requestingText'
            ),
            color=(0, 1, 0),
        )
        plus.add_v1_account_transaction(
            {
                'type': 'ACCOUNT_UNLINK_REQUEST',
                'accountID': entry['id'],
                'expire_time': time.time() + 5,
            }
        )
        plus.run_v1_account_transactions()
        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

    def _cancel(self) -> None:
        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
