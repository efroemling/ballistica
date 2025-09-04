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
        transition: str | None = 'in_scale',
        origin_widget: bui.Widget | None = None,
    ):

        # Need to wrangle our own transition-out in modal mode.
        if origin_widget is not None:
            self._transition_out = 'out_scale'
        else:
            self._transition_out = 'out_right'

        uiscale = bui.app.ui_v1.uiscale

        width = 1200 if uiscale is bui.UIScale.SMALL else 600
        height = 600 if uiscale is bui.UIScale.SMALL else 300

        self._r = 'promoCodeWindow'

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(width - 80, screensize[0] / scale)
        target_height = min(height - 80, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 20.0

        assert bui.app.classic is not None
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_full' if bui.in_main_menu() else 'menu_minimal'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is not bui.UIScale.SMALL:
            close_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(25, yoffs - 35),
                size=(60, 60),
                scale=0.7,
                autoselect=True,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )

        else:
            close_button = None

        v = yoffs - 74

        v += -30 if uiscale is bui.UIScale.SMALL else 10
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
        v -= 100

        txoffs = -270
        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource='descriptionText'),
            position=(width * 0.5 + txoffs + 22, v),
            color=(0.8, 0.8, 0.8, 1.0),
            size=(90, 30),
            h_align='right',
            maxwidth=100,
        )
        v -= 8

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5 + txoffs + 125, v),
            size=(380, 46),
            text='',
            h_align='left',
            v_align='center',
            max_chars=64,
            color=(0.9, 0.9, 0.9, 1.0),
            description=bui.Lstr(resource='descriptionText'),
            editable=True,
            autoselect=True,
            padding=4,
            on_return_press_call=self._activate_enter_button,
        )
        if close_button is not None:
            bui.widget(edit=close_button, down_widget=self._text_field)

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
            autoselect=True,
        )
        bui.containerwidget(
            edit=self._root_widget,
            start_button=btn2,
            selected_child=self._text_field,
        )
        if close_button is not None:
            bui.containerwidget(
                edit=self._root_widget,
                cancel_button=close_button,
            )
        else:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
            )
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

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return
        self.main_window_back()

        # Used for things like unlocking shared playlists or linking
        # accounts: talk directly to V1 server via transactions.
        bui.app.create_async_task(_send_info(description))


class SendInfoWindowLegacyModal(bui.Window):
    """Window for sending info to the developer."""

    def __init__(
        self,
        transition: str | None = 'in_scale',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals

        # Need to wrangle our own transition-out in modal mode.
        if origin_widget is not None:
            self._transition_out = 'out_scale'
        else:
            self._transition_out = 'out_right'

        uiscale = bui.app.ui_v1.uiscale

        width = 450
        height = 200

        self._r = 'promoCodeWindow'

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(width - 80, screensize[0] / scale)
        target_height = min(height - 80, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 20.0

        scale_origin = (
            None
            if origin_widget is None
            else origin_widget.get_screen_space_center()
        )

        assert bui.app.classic is not None
        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=('menu_minimal_no_back'),
                transition=transition,
                scale_origin_stack_offset=scale_origin,
                scale=scale,
                darken_behind=True,
            ),
        )

        close_button = bui.buttonwidget(
            parent=self._root_widget,
            scale=0.5,
            position=(30, yoffs - 30),
            size=(60, 60),
            on_activate_call=self._do_back,
            autoselect=True,
            color=(0.55, 0.5, 0.6),
            label=bui.charstr(bui.SpecialChar.CLOSE),
            textcolor=(1, 1, 1),
        )

        v = yoffs - 74

        txoffs = -200
        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource=f'{self._r}.codeText'),
            position=(width * 0.5 + txoffs + 22, v),
            color=(0.8, 0.8, 0.8, 1.0),
            size=(90, 30),
            h_align='right',
            maxwidth=100,
        )
        v -= 8

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5 + txoffs + 125, v),
            size=(280, 46),
            text='',
            h_align='left',
            v_align='center',
            max_chars=64,
            color=(0.9, 0.9, 0.9, 1.0),
            description=bui.Lstr(resource=f'{self._r}.codeText'),
            editable=True,
            autoselect=True,
            padding=4,
            on_return_press_call=self._activate_enter_button,
        )
        if close_button is not None:
            bui.widget(edit=close_button, down_widget=self._text_field)

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
            autoselect=True,
        )
        bui.containerwidget(
            edit=self._root_widget,
            start_button=btn2,
            selected_child=self._text_field,
        )
        if close_button is not None:
            bui.containerwidget(
                edit=self._root_widget,
                cancel_button=close_button,
            )

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import

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

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )

        # Used for things like unlocking shared playlists or linking
        # accounts: talk directly to V1 server via transactions.
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


async def _send_info(description: str) -> None:
    from bacommon.bs import SendInfoMessage

    plus = bui.app.plus
    assert plus is not None

    classic = bui.app.classic
    assert classic is not None

    ui_pause: bui.RootUIUpdatePause | None = None  # pylint: disable=W0612

    try:
        # Don't allow *anything* if our V2 transport connection isn't up.
        if not plus.cloud.connected:
            bui.screenmessage(
                bui.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
            bui.getsound('error').play()
            return

        # Pause root ui updates so stuff like token counts don't change
        # automatically until we've run any client-effect animations
        # resulting from this message.
        ui_pause = bui.RootUIUpdatePause()

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
            bui.screenmessage(
                bui.Lstr(translate=('serverResponses', response.message)),
                color=(0, 1, 0),
            )
        # As of newer builds we support client-effects too.
        if response.effects:
            classic.run_bs_client_effects(response.effects)

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
    finally:
        # Make sure ui-pause is dead even if something is holding
        # on to this stack frame.
        ui_pause = None
