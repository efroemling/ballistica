# Released under the MIT License. See LICENSE for details.
#
"""UI functionality for entering promo codes."""

from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class SendInfoWindow(bui.MainWindow):
    """Window for sending info to the developer."""

    def __init__(
        self,
        modal: bool = False,
        legacy_code_mode: bool = False,
        transition: str | None = 'in_scale',
        origin_widget: bui.Widget | None = None,
    ):
        self._legacy_code_mode = legacy_code_mode

        # Need to wrangle our own transition-out in modal mode.
        if origin_widget is not None:
            self._transition_out = 'out_scale'
        else:
            self._transition_out = 'out_right'

        width = 450 if legacy_code_mode else 600
        height = 200 if legacy_code_mode else 300

        self._modal = modal
        self._r = 'promoCodeWindow'

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal_no_back'
                    if uiscale is bui.UIScale.SMALL or modal
                    else 'menu_full'
                ),
                scale=(
                    2.0
                    if uiscale is bui.UIScale.SMALL
                    else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        btn = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.5,
            position=(40, height - 40),
            size=(60, 60),
            label='',
            on_activate_call=self._do_back,
            autoselect=True,
            color=(0.55, 0.5, 0.6),
            icon=bui.gettexture('crossOut'),
            iconscale=1.2,
        )

        v = height - 74

        if legacy_code_mode:
            v -= 20
        else:
            v -= 20
            bui.textwidget(
                parent=self._root_widget,
                text=bui.Lstr(resource='sendInfoDescriptionText'),
                maxwidth=width * 0.9,
                position=(width * 0.5, v),
                color=(0.7, 0.7, 0.7, 1.0),
                size=(0, 0),
                scale=0.8,
                h_align='center',
                v_align='center',
            )
            v -= 20

            # bui.textwidget(
            #     parent=self._root_widget,
            #     text=bui.Lstr(
            #         resource='supportEmailText',
            #         subs=[('${EMAIL}', 'support@froemling.net')],
            #     ),
            #     maxwidth=width * 0.9,
            #     position=(width * 0.5, v),
            #     color=(0.7, 0.7, 0.7, 1.0),
            #     size=(0, 0),
            #     scale=0.65,
            #     h_align='center',
            #     v_align='center',
            # )
            v -= 80

        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(
                resource=(
                    f'{self._r}.codeText'
                    if legacy_code_mode
                    else 'descriptionText'
                )
            ),
            position=(22, v),
            color=(0.8, 0.8, 0.8, 1.0),
            size=(90, 30),
            h_align='right',
            maxwidth=100,
        )
        v -= 8

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(125, v),
            size=(280 if legacy_code_mode else 380, 46),
            text='',
            h_align='left',
            v_align='center',
            max_chars=64,
            color=(0.9, 0.9, 0.9, 1.0),
            description=bui.Lstr(
                resource=(
                    f'{self._r}.codeText'
                    if legacy_code_mode
                    else 'descriptionText'
                )
            ),
            editable=True,
            padding=4,
            on_return_press_call=self._activate_enter_button,
        )
        bui.widget(edit=btn, down_widget=self._text_field)

        v -= 79
        b_width = 200
        self._enter_button = btn2 = bui.buttonwidget(
            parent=self._root_widget,
            position=(width * 0.5 - b_width * 0.5, v),
            size=(b_width, 60),
            scale=1.0,
            label=bui.Lstr(
                resource='submitText', fallback_resource=f'{self._r}.enterText'
            ),
            on_activate_call=self._do_enter,
        )
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=btn,
            start_button=btn2,
            selected_child=self._text_field,
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        assert not self._modal

        # Pull stuff out of self here; if we do it in the lambda we'll
        # keep self alive which we don't want.
        legacy_code_mode = self._legacy_code_mode

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                legacy_code_mode=legacy_code_mode,
                transition=transition,
                origin_widget=origin_widget,
            )
        )

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import

        if not self._modal:
            self.main_window_back()
            return

        # Handle modal case:

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

    def _activate_enter_button(self) -> None:
        self._enter_button.activate()

    def _do_enter(self) -> None:
        # pylint: disable=cyclic-import
        # from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        plus = bui.app.plus
        assert plus is not None

        description: Any = bui.textwidget(query=self._text_field)
        assert isinstance(description, str)

        if self._modal:
            # no-op if our underlying widget is dead or on its way out.
            if not self._root_widget or self._root_widget.transitioning_out:
                return
            bui.containerwidget(
                edit=self._root_widget, transition=self._transition_out
            )
        else:
            # no-op if we're not in control.
            if not self.main_window_has_control():
                return
            self.main_window_back()

        # Used for things like unlocking shared playlists or linking
        # accounts: talk directly to V1 server via transactions.
        if self._legacy_code_mode:
            if plus.get_v1_account_state() != 'signed_in':
                bui.screenmessage(
                    bui.Lstr(resource='notSignedInErrorText'), color=(1, 0, 0)
                )
                bui.getsound('error').play()
            else:
                plus.add_v1_account_transaction(
                    {
                        'type': 'PROMO_CODE',
                        'expire_time': time.time() + 5,
                        'code': description,
                    }
                )
                plus.run_v1_account_transactions()
        else:
            bui.app.create_async_task(_send_info(description))


async def _send_info(description: str) -> None:
    from bacommon.cloud import SendInfoMessage

    plus = bui.app.plus
    assert plus is not None

    try:
        # Don't allow *anything* if our V2 transport connection isn't up.
        if not plus.cloud.connected:
            bui.screenmessage(
                bui.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # Ship to V2 server, with or without account info.
        if plus.accounts.primary is not None:
            with plus.accounts.primary:
                response = await plus.cloud.send_message_async(
                    SendInfoMessage(description)
                )
        else:
            response = await plus.cloud.send_message_async(
                SendInfoMessage(description)
            )

        # Support simple message printing from v2 server.
        if response.message is not None:
            bui.screenmessage(response.message, color=(0, 1, 0))

        # If V2 handled it, we're done.
        if response.handled:
            return

        # Ok; V2 didn't handle it. Try V1 if we're signed in there.
        if plus.get_v1_account_state() != 'signed_in':
            bui.screenmessage(
                bui.Lstr(resource='notSignedInErrorText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        # Push it along to v1 as an old style code. Allow v2 response to
        # sub in its own code.
        plus.add_v1_account_transaction(
            {
                'type': 'PROMO_CODE',
                'expire_time': time.time() + 5,
                'code': (
                    description
                    if response.legacy_code is None
                    else response.legacy_code
                ),
            }
        )
        plus.run_v1_account_transactions()
    except Exception:
        logging.exception('Error sending promo code.')
        bui.screenmessage('Error sending code (see log).', color=(1, 0, 0))
        bui.getsound('error').play()
