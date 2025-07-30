# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the cloud."""

from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING, overload

from efro.error import CommunicationError
from efro.call import CallbackSet
from efro.dataclassio import dataclass_from_dict, dataclass_to_dict
import bacommon.cloud
import babase

if TYPE_CHECKING:
    from typing import Callable, Any

    from efro.message import Message, Response, BoolResponse
    import bacommon.bs


# TODO: Should make it possible to define a protocol in bacommon.cloud and
# autogenerate this. That would give us type safety between this and
# internal protocols.


class CloudSubsystem(babase.AppSubsystem):
    """Manages communication with cloud components.

    Access the shared single instance of this class via the
    :attr:`~baplus.PlusAppSubsystem.cloud` attr on the
    :class:`~baplus.PlusAppSubsystem` class.
    """

    #: General engine config values provided by the cloud.
    vals: bacommon.cloud.CloudVals

    def __init__(self) -> None:
        super().__init__()
        self.on_connectivity_changed_callbacks: CallbackSet[
            Callable[[bool], None]
        ] = CallbackSet()

        # Restore saved cloud-vals (or init to default).
        try:
            cloudvals_data = babase.app.config.get('CloudVals')
            if isinstance(cloudvals_data, dict):
                self.vals = dataclass_from_dict(
                    bacommon.cloud.CloudVals, cloudvals_data
                )
            else:
                self.vals = bacommon.cloud.CloudVals()
        except Exception:
            babase.applog.warning(
                'Error loading CloudVals; resetting to default.', exc_info=True
            )
            self.vals = bacommon.cloud.CloudVals()

        # Set up to start updating cloud-vals once we've got
        # connectivity.
        self._vals_updated = False
        self._vals_update_timer: babase.AppTimer | None = None
        self._vals_last_request_time: float | None = None
        self._vals_update_conn_reg = (
            self.on_connectivity_changed_callbacks.register(
                self._update_vals_update_for_connectivity
            )
        )

    @property
    def connected(self) -> bool:
        """Whether a connection to the cloud is present.

        This is a good indicator (though not for certain) that sending
        messages will succeed.
        """
        return self.is_connected()

    def is_connected(self) -> bool:
        """Implementation for connected attr.

        :meta private:
        """
        raise NotImplementedError()

    def on_connectivity_changed(self, connected: bool) -> None:
        """Called when cloud connectivity state changes.

        :meta private:
        """
        babase.balog.debug('Connectivity is now %s.', connected)

        plus = babase.app.plus
        assert plus is not None

        # Fire any registered callbacks for this.
        for call in self.on_connectivity_changed_callbacks.getcalls():
            try:
                call(connected)
            except Exception:
                logging.exception('Error in connectivity-changed callback.')

    def _update_vals_update_for_connectivity(self, connected: bool) -> None:

        # If we don't have vals yet and are connected, start asking.
        if connected and not self._vals_updated:
            # Ask immediately and set up a timer to keep doing so until
            # successful.
            self._possibly_send_vals_request()
            self._vals_update_timer = babase.AppTimer(
                61.23, self._possibly_send_vals_request, repeat=True
            )
        else:
            # Ok; we're disconnected or have vals - stop asking.
            self._vals_update_timer = None

    def _possibly_send_vals_request(self) -> None:
        now = time.monotonic()

        # Only send if we havn't already recently.
        if (
            self._vals_last_request_time is None
            or now - self._vals_last_request_time > 30.0
        ):
            self._vals_last_request_time = now
            self.send_message_cb(
                bacommon.cloud.CloudValsRequest(), self._on_cloud_vals_response
            )

    def _on_cloud_vals_response(
        self, response: bacommon.cloud.CloudValsResponse | Exception
    ) -> None:
        if isinstance(response, Exception):
            # Make noise for any non-communication errors
            if not isinstance(response, CommunicationError):
                babase.applog.exception(
                    'Unexpected error in _on_cloud_vals_response().'
                )
            return

        # If what we got differs from what we already had, store it.
        if response.vals != self.vals:
            cfg = babase.app.config
            cfg['CloudVals'] = dataclass_to_dict(response.vals)
            cfg.commit()
            self.vals = response.vals

        # We can stop asking now.
        self._vals_updated = True
        self._vals_update_timer = None

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.LoginProxyRequestMessage,
        on_response: Callable[
            [bacommon.cloud.LoginProxyRequestResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.CloudValsRequest,
        on_response: Callable[
            [bacommon.cloud.CloudValsResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.LoginProxyStateQueryMessage,
        on_response: Callable[
            [bacommon.cloud.LoginProxyStateQueryResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.LoginProxyCompleteMessage,
        on_response: Callable[[None | Exception], None],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.PingMessage,
        on_response: Callable[[bacommon.cloud.PingResponse | Exception], None],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.SignInMessage,
        on_response: Callable[
            [bacommon.cloud.SignInResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.ManageAccountMessage,
        on_response: Callable[
            [bacommon.cloud.ManageAccountResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.bs.GetClassicPurchasesMessage,
        on_response: Callable[
            [bacommon.bs.GetClassicPurchasesResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.StoreQueryMessage,
        on_response: Callable[
            [bacommon.cloud.StoreQueryResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.bs.PrivatePartyMessage,
        on_response: Callable[
            [bacommon.bs.PrivatePartyResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.bs.InboxRequestMessage,
        on_response: Callable[
            [bacommon.bs.InboxRequestResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.bs.ClientUIActionMessage,
        on_response: Callable[
            [bacommon.bs.ClientUIActionResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.bs.ChestInfoMessage,
        on_response: Callable[
            [bacommon.bs.ChestInfoResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.bs.ChestActionMessage,
        on_response: Callable[
            [bacommon.bs.ChestActionResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.bs.GlobalProfileCheckMessage,
        on_response: Callable[[BoolResponse | Exception], None],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.bs.ScoreSubmitMessage,
        on_response: Callable[
            [bacommon.bs.ScoreSubmitResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.SecureDataCheckMessage,
        on_response: Callable[
            [bacommon.cloud.SecureDataCheckResponse | Exception], None
        ],
    ) -> None: ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.SecureDataCheckerRequest,
        on_response: Callable[
            [bacommon.cloud.SecureDataCheckerResponse | Exception], None
        ],
    ) -> None: ...

    def send_message_cb(
        self,
        msg: Message,
        on_response: Callable[[Any], None],
    ) -> None:
        """Asynchronously send a message to the cloud from the logic thread.

        The provided ``on_response`` call will be run in the logic thread
        and passed either the response or the error that occurred.
        """
        raise NotImplementedError(
            'Cloud functionality is not present in this build.'
        )

    @overload
    def send_message(
        self, msg: bacommon.cloud.WorkspaceFetchMessage
    ) -> bacommon.cloud.WorkspaceFetchResponse: ...

    @overload
    def send_message(
        self, msg: bacommon.cloud.MerchAvailabilityMessage
    ) -> bacommon.cloud.MerchAvailabilityResponse: ...

    @overload
    def send_message(
        self, msg: bacommon.cloud.TestMessage
    ) -> bacommon.cloud.TestResponse: ...

    def send_message(self, msg: Message) -> Response | None:
        """Synchronously send a message to the cloud.

        Must be called from a background thread.
        """
        raise NotImplementedError(
            'Cloud functionality is not present in this build.'
        )

    @overload
    async def send_message_async(
        self, msg: bacommon.cloud.SendInfoMessage
    ) -> bacommon.cloud.SendInfoResponse: ...

    @overload
    async def send_message_async(
        self, msg: bacommon.cloud.TestMessage
    ) -> bacommon.cloud.TestResponse: ...

    async def send_message_async(self, msg: Message) -> Response | None:
        """Asynchronously send a message to the cloud.

        Must be called from the logic thread.
        """
        raise NotImplementedError(
            'Cloud functionality is not present in this build.'
        )

    def subscribe_test(
        self, updatecall: Callable[[int | None], None]
    ) -> babase.CloudSubscription:
        """Subscribe to some test data.

        :meta private:
        """
        raise NotImplementedError(
            'Cloud functionality is not present in this build.'
        )

    def subscribe_classic_account_data(
        self,
        updatecall: Callable[[bacommon.bs.ClassicAccountLiveData], None],
    ) -> babase.CloudSubscription:
        """Subscribe to classic account data."""
        raise NotImplementedError(
            'Cloud functionality is not present in this build.'
        )

    def unsubscribe(self, subscription_id: int) -> None:
        """Unsubscribe from some subscription.

        Do not call this manually; it is called by CloudSubscription.

        :meta private:
        """
        raise NotImplementedError(
            'Cloud functionality is not present in this build.'
        )


def cloud_console_exec(code: str) -> None:
    """Called by the cloud console to run code in the logic thread."""
    import sys
    import __main__

    try:
        # First try it as eval.
        try:
            evalcode = compile(code, '<console>', 'eval')
        except SyntaxError:
            evalcode = None
        except Exception:
            # hmm; when we can't compile it as eval will we always get
            # syntax error?
            logging.exception(
                'unexpected error compiling code for cloud-console eval.'
            )
            evalcode = None
        if evalcode is not None:
            # pylint: disable=eval-used
            value = eval(evalcode, vars(__main__), vars(__main__))
            # For eval-able statements, print the resulting value if
            # it is not None (just like standard Python interpreter).
            if value is not None:
                print(repr(value), file=sys.stderr)

        # Fall back to exec if we couldn't compile it as eval.
        else:
            execcode = compile(code, '<console>', 'exec')
            # pylint: disable=exec-used
            exec(execcode, vars(__main__), vars(__main__))

    except Exception:
        import traceback

        # Note to self: Seems like we should just use
        # logging.exception() here. Except currently that winds up
        # triggering our cloud logging stuff so we'd probably want a
        # specific logger or whatnot to avoid that.
        apptime = babase.apptime()
        print(f'Exec error at time {apptime:.2f}.', file=sys.stderr)
        traceback.print_exc()

        # This helps the logging system ship stderr back to the
        # cloud promptly.
        sys.stderr.flush()
