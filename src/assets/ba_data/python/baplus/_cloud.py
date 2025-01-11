# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the cloud."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, overload

from efro.call import CallbackSet
import babase

if TYPE_CHECKING:
    from typing import Callable, Any

    from efro.message import Message, Response
    import bacommon.cloud
    import bacommon.bs


# TODO: Should make it possible to define a protocol in bacommon.cloud and
# autogenerate this. That would give us type safety between this and
# internal protocols.


class CloudSubsystem(babase.AppSubsystem):
    """Manages communication with cloud components."""

    def __init__(self) -> None:
        super().__init__()
        self.on_connectivity_changed_callbacks: CallbackSet[
            Callable[[bool], None]
        ] = CallbackSet()

    @property
    def connected(self) -> bool:
        """Property equivalent of CloudSubsystem.is_connected()."""
        return self.is_connected()

    def is_connected(self) -> bool:
        """Return whether a connection to the cloud is present.

        This is a good indicator (though not for certain) that sending
        messages will succeed.
        """
        return False  # Needs to be overridden

    def on_connectivity_changed(self, connected: bool) -> None:
        """Called when cloud connectivity state changes."""
        babase.balog.debug('Connectivity is now %s.', connected)

        plus = babase.app.plus
        assert plus is not None

        # Fire any registered callbacks for this.
        for call in self.on_connectivity_changed_callbacks.getcalls():
            try:
                call(connected)
            except Exception:
                logging.exception('Error in connectivity-changed callback.')

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

    def send_message_cb(
        self,
        msg: Message,
        on_response: Callable[[Any], None],
    ) -> None:
        """Asynchronously send a message to the cloud from the logic thread.

        The provided on_response call will be run in the logic thread
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
        """Synchronously send a message to the cloud.

        Must be called from the logic thread.
        """
        raise NotImplementedError(
            'Cloud functionality is not present in this build.'
        )

    def subscribe_test(
        self, updatecall: Callable[[int | None], None]
    ) -> babase.CloudSubscription:
        """Subscribe to some test data."""
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
