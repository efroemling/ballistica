# Released under the MIT License. See LICENSE for details.
#
"""Provides chest related ui."""

from __future__ import annotations

from typing import override, TYPE_CHECKING

import bacommon.cloud
import bauiv1 as bui

if TYPE_CHECKING:
    pass


class ChestWindow(bui.MainWindow):
    """Allows operations on a chest."""

    def __del__(self) -> None:
        print('~ChestWindow()')

    def __init__(
        self,
        index: int,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        print('ChestWindow()')

        self._index = index

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1050 if uiscale is bui.UIScale.SMALL else 850
        self._height = (
            500
            if uiscale is bui.UIScale.SMALL
            else 500 if uiscale is bui.UIScale.MEDIUM else 500
        )
        self._xoffs = 70 if uiscale is bui.UIScale.SMALL else 0
        self._yoffs = -42 if uiscale is bui.UIScale.SMALL else -25
        self._action_in_flight = False
        self._open_now_button: bui.Widget | None = None
        self._watch_ad_button: bui.Widget | None = None

        # The set of widgets we keep when doing a clear.
        self._core_widgets: list[bui.Widget] = []

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility='menu_full',
                scale=(
                    1.55
                    if uiscale is bui.UIScale.SMALL
                    else 1.1 if uiscale is bui.UIScale.MEDIUM else 0.9
                ),
                stack_offset=(
                    (0, 0)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 15) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        self._core_widgets.append(
            bui.textwidget(
                parent=self._root_widget,
                position=(0, self._height - 45 + self._yoffs),
                size=(self._width, 25),
                text=f'Chest #{self._index + 1}',
                color=bui.app.ui_v1.title_color,
                maxwidth=150.0,
                h_align='center',
                v_align='center',
            )
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(self._xoffs + 50, self._height - 55 + self._yoffs),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)
            self._core_widgets.append(btn)

        self._infotext = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 200 + self._yoffs),
            size=(0, 0),
            text=bui.Lstr(resource='loadingText'),
            maxwidth=700,
            scale=0.7,
            color=(0.6, 0.5, 0.6),
            h_align='center',
            v_align='center',
        )
        self._core_widgets.append(self._infotext)

        plus = bui.app.plus
        if plus is None:
            self._error('Plus feature-set is not present.')
            return

        if plus.accounts.primary is None:
            self._error(bui.Lstr(resource='notSignedInText'))
            return

        # Start by showing info/options for our target chest. Note that
        # we always ask the server for these values even though we may
        # have them through our appmode subscription which updates the
        # chest UI. This is because the wait_for_connectivity()
        # mechanism will often bring our window up a split second before
        # the chest subscription receives its first values which would
        # lead us to incorrectly think there is no chest there. If we
        # want to optimize this in the future we could perhaps use local
        # values only if there is a chest present in them.
        assert not self._action_in_flight
        self._action_in_flight = True
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.cloud.BSChestInfoMessage(chest_id=str(self._index)),
                on_response=bui.WeakCall(self._on_chest_info_response),
            )

    def _on_chest_info_response(
        self, response: bacommon.cloud.BSChestInfoResponse | Exception
    ) -> None:
        assert self._action_in_flight  # Should be us.
        self._action_in_flight = False

        if isinstance(response, Exception):
            self._error(
                bui.Lstr(resource='internal.unavailableNoConnectionText')
            )
            return

        if response.chest is None:
            self._error('Would show general info about chests.')
            return

        self.show_chest_actions(response.chest)

    def _on_chest_action_response(
        self, response: bacommon.cloud.BSChestActionResponse | Exception
    ) -> None:
        assert self._action_in_flight  # Should be us.
        self._action_in_flight = False

        # Communication/local error:
        if isinstance(response, Exception):
            self._error(
                bui.Lstr(resource='internal.unavailableNoConnectionText')
            )
            return

        # Server-side error:
        if response.error is not None:
            self._error(bui.Lstr(translate=('serverResponses', response.error)))
            return

        # If there's contents listed in the response, show them.
        if response.contents is not None:
            print('WOULD SHOW CONTENTS:', response.contents)
        else:
            # Otherwise we're done here; just close out our UI.
            self.main_window_back()

    def show_chest_actions(
        self, chest: bacommon.cloud.BSChestInfoResponse.Chest
    ) -> None:
        """Show state for our chest."""
        # pylint: disable=cyclic-import
        from baclassic import ClassicAppMode

        # We expect to be run under classic.
        mode = bui.app.mode
        if not isinstance(mode, ClassicAppMode):
            self._error('Classic app mode not active.')
            return

        now = bui.utc_now_cloud()
        secs_till_open = max(0.0, (chest.unlock_time - now).total_seconds())
        tstr = bui.timestring(secs_till_open, centi=False)

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 120 + self._yoffs),
            size=(0, 0),
            text=tstr,
            maxwidth=700,
            scale=0.7,
            color=(0.6, 0.5, 0.6),
            h_align='center',
            v_align='center',
        )
        self._open_now_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 - 200,
                self._height - 250 + self._yoffs,
            ),
            size=(150, 100),
            label=f'OPEN NOW FOR {chest.unlock_tokens} TOKENS',
            button_type='square',
            autoselect=True,
            on_activate_call=bui.WeakCall(
                self._open_now_press, chest.unlock_tokens
            ),
        )

        self._watch_ad_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 + 50,
                self._height - 250 + self._yoffs,
            ),
            size=(150, 100),
            label='WATCH AN AD TO REDUCE WAIT',
            button_type='square',
            autoselect=True,
            on_activate_call=bui.WeakCall(self._watch_ad_press),
        )
        bui.textwidget(edit=self._infotext, text='')

    def _open_now_press(self, token_payment: int) -> None:

        # Allow only one in-flight action at once.
        if self._action_in_flight:
            bui.screenmessage(
                bui.Lstr(resource='pleaseWaitText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        plus = bui.app.plus
        assert plus is not None

        if plus.accounts.primary is None:
            self._error(bui.Lstr(resource='notSignedInText'))
            return

        self._action_in_flight = True
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.cloud.BSChestActionMessage(
                    chest_id=str(self._index),
                    action=bacommon.cloud.BSChestActionMessage.Action.UNLOCK,
                    token_payment=token_payment,
                ),
                on_response=bui.WeakCall(self._on_chest_action_response),
            )

        # Convey that something is in progress.
        if self._open_now_button:
            bui.buttonwidget(edit=self._open_now_button, label='...')

    def _watch_ad_press(self) -> None:

        # Allow only one in-flight action at once.
        if self._action_in_flight:
            bui.screenmessage(
                bui.Lstr(resource='pleaseWaitText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        plus = bui.app.plus
        assert plus is not None

        if plus.accounts.primary is None:
            self._error(bui.Lstr(resource='notSignedInText'))
            return

        self._action_in_flight = True
        with plus.accounts.primary:
            plus.cloud.send_message_cb(
                bacommon.cloud.BSChestActionMessage(
                    chest_id=str(self._index),
                    action=bacommon.cloud.BSChestActionMessage.Action.AD,
                    token_payment=0,
                ),
                on_response=bui.WeakCall(self._on_chest_action_response),
            )

        # Convey that something is in progress.
        if self._watch_ad_button:
            bui.buttonwidget(edit=self._watch_ad_button, label='...')

    def _reset(self) -> None:
        """Clear all non-permanent widgets."""
        for widget in self._root_widget.get_children():
            if widget not in self._core_widgets:
                widget.delete()

    def _error(self, msg: str | bui.Lstr) -> None:
        """Put ourself in an error state with a visible error message."""
        self._reset()
        bui.textwidget(edit=self._infotext, text=msg, color=(1, 0, 0))

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull anything we need from self out here; if we do it in the
        # lambda we keep self alive which is bad.
        index = self._index

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                index=index, transition=transition, origin_widget=origin_widget
            )
        )


# Slight hack: we define different classes for our different chest slots
# so that the default UI behavior is to replace each other when
# different ones are pressed. If they are all the same class then the
# default behavior for such presses is to toggle the existing one back
# off.


class ChestWindow0(ChestWindow):
    """Child class of ChestWindow for slighty hackish reasons."""


class ChestWindow1(ChestWindow):
    """Child class of ChestWindow for slighty hackish reasons."""


class ChestWindow2(ChestWindow):
    """Child class of ChestWindow for slighty hackish reasons."""


class ChestWindow3(ChestWindow):
    """Child class of ChestWindow for slighty hackish reasons."""
