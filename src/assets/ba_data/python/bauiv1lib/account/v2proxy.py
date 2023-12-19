# Released under the MIT License. See LICENSE for details.
#
"""V2 account ui bits."""

from __future__ import annotations

import logging

from efro.error import CommunicationError
import bacommon.cloud
import bauiv1 as bui

STATUS_CHECK_INTERVAL_SECONDS = 2.0


class V2ProxySignInWindow(bui.Window):
    """A window allowing signing in to a v2 account."""

    def __init__(self, origin_widget: bui.Widget):
        self._width = 600
        self._height = 550
        self._proxyid: str | None = None
        self._proxykey: str | None = None

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
                scale_origin_stack_offset=(
                    origin_widget.get_screen_space_center()
                ),
                scale=(
                    1.25
                    if uiscale is bui.UIScale.SMALL
                    else 1.05
                    if uiscale is bui.UIScale.MEDIUM
                    else 0.9
                ),
            )
        )

        self._loading_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            h_align='center',
            v_align='center',
            size=(0, 0),
            maxwidth=0.9 * self._width,
            text=bui.Lstr(
                value='${A}...',
                subs=[('${A}', bui.Lstr(resource='loadingText'))],
            ),
        )

        self._cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(30, self._height - 65),
            size=(130, 50),
            scale=0.8,
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=self._done,
            autoselect=True,
        )

        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._cancel_button
        )

        self._update_timer: bui.AppTimer | None = None

        # Ask the cloud for a proxy login id.
        assert bui.app.plus is not None
        bui.app.plus.cloud.send_message_cb(
            bacommon.cloud.LoginProxyRequestMessage(),
            on_response=bui.WeakCall(self._on_proxy_request_response),
        )

    def _on_proxy_request_response(
        self, response: bacommon.cloud.LoginProxyRequestResponse | Exception
    ) -> None:
        plus = bui.app.plus
        assert plus is not None

        # Something went wrong. Show an error message and that's it.
        if isinstance(response, Exception):
            bui.textwidget(
                edit=self._loading_text,
                text=bui.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
            return

        # Show link(s) the user can use to sign in.
        address = plus.get_master_server_address(version=2) + response.url
        address_pretty = address.removeprefix('https://')

        assert bui.app.classic is not None
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 95),
            size=(0, 0),
            text=bui.Lstr(
                resource='accountSettingsWindow.v2LinkInstructionsText'
            ),
            color=bui.app.ui_v1.title_color,
            maxwidth=self._width * 0.9,
            h_align='center',
            v_align='center',
        )
        button_width = 450
        if bui.is_browser_likely_available():
            bui.buttonwidget(
                parent=self._root_widget,
                position=(
                    (self._width * 0.5 - button_width * 0.5),
                    self._height - 185,
                ),
                autoselect=True,
                size=(button_width, 60),
                label=bui.Lstr(value=address_pretty),
                color=(0.55, 0.5, 0.6),
                textcolor=(0.75, 0.7, 0.8),
                on_activate_call=lambda: bui.open_url(address),
            )
            qroffs = 0.0
        else:
            bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5 - 200, self._height - 180),
                size=(button_width - 50, 50),
                text=bui.Lstr(value=address_pretty),
                flatness=1.0,
                maxwidth=self._width,
                scale=0.75,
                h_align='center',
                v_align='center',
                autoselect=True,
                on_activate_call=bui.Call(self._copy_link, address_pretty),
                selectable=True,
            )
            qroffs = 20.0

        qr_size = 270
        bui.imagewidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5 - qr_size * 0.5,
                self._height * 0.36 + qroffs - qr_size * 0.5,
            ),
            size=(qr_size, qr_size),
            texture=bui.get_qrcode_texture(address),
        )

        # Start querying for results.
        self._proxyid = response.proxyid
        self._proxykey = response.proxykey
        bui.apptimer(
            STATUS_CHECK_INTERVAL_SECONDS, bui.WeakCall(self._ask_for_status)
        )

    def _ask_for_status(self) -> None:
        assert self._proxyid is not None
        assert self._proxykey is not None
        assert bui.app.plus is not None
        bui.app.plus.cloud.send_message_cb(
            bacommon.cloud.LoginProxyStateQueryMessage(
                proxyid=self._proxyid, proxykey=self._proxykey
            ),
            on_response=bui.WeakCall(self._got_status),
        )

    def _got_status(
        self, response: bacommon.cloud.LoginProxyStateQueryResponse | Exception
    ) -> None:
        # For now, if anything goes wrong on the server-side, just abort
        # with a vague error message. Can be more verbose later if need be.
        if (
            isinstance(response, bacommon.cloud.LoginProxyStateQueryResponse)
            and response.state is response.State.FAIL
        ):
            bui.getsound('error').play()
            bui.screenmessage(bui.Lstr(resource='errorText'), color=(1, 0, 0))
            self._done()
            return

        # If we got a token, set ourself as signed in. Hooray!
        if (
            isinstance(response, bacommon.cloud.LoginProxyStateQueryResponse)
            and response.state is response.State.SUCCESS
        ):
            plus = bui.app.plus
            assert plus is not None
            assert response.credentials is not None
            plus.accounts.set_primary_credentials(response.credentials)

            # As a courtesy, tell the server we're done with this proxy
            # so it can clean up (not a huge deal if this fails)
            assert self._proxyid is not None
            try:
                plus.cloud.send_message_cb(
                    bacommon.cloud.LoginProxyCompleteMessage(
                        proxyid=self._proxyid
                    ),
                    on_response=bui.WeakCall(self._proxy_complete_response),
                )
            except CommunicationError:
                pass
            except Exception:
                logging.warning(
                    'Unexpected error sending login-proxy-complete message',
                    exc_info=True,
                )

            self._done()
            return

        # If we're still waiting, ask again soon.
        if (
            isinstance(response, Exception)
            or response.state is response.State.WAITING
        ):
            bui.apptimer(
                STATUS_CHECK_INTERVAL_SECONDS,
                bui.WeakCall(self._ask_for_status),
            )

    def _proxy_complete_response(self, response: None | Exception) -> None:
        del response  # Not used.
        # We could do something smart like retry on exceptions here, but
        # this isn't critical so we'll just let anything slide.

    def _copy_link(self, link: str) -> None:
        if bui.clipboard_is_supported():
            bui.clipboard_set_text(link)
            bui.screenmessage(
                bui.Lstr(resource='copyConfirmText'), color=(0, 1, 0)
            )

    def _done(self) -> None:
        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
