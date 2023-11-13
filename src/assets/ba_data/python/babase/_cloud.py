# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the cloud."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, overload

import _babase
from babase._appsubsystem import AppSubsystem

if TYPE_CHECKING:
    from typing import Callable, Any

    from efro.message import Message, Response
    import bacommon.cloud

DEBUG_LOG = False

# TODO: Should make it possible to define a protocol in bacommon.cloud and
# autogenerate this. That would give us type safety between this and
# internal protocols.


class CloudSubsystem(AppSubsystem):
    """Manages communication with cloud components."""

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
        if DEBUG_LOG:
            logging.debug('CloudSubsystem: Connectivity is now %s.', connected)

        plus = _babase.app.plus
        assert plus is not None

        # Inform things that use this.
        # (TODO: should generalize this into some sort of registration system)
        plus.accounts.on_cloud_connectivity_changed(connected)

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.LoginProxyRequestMessage,
        on_response: Callable[
            [bacommon.cloud.LoginProxyRequestResponse | Exception], None
        ],
    ) -> None:
        ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.LoginProxyStateQueryMessage,
        on_response: Callable[
            [bacommon.cloud.LoginProxyStateQueryResponse | Exception], None
        ],
    ) -> None:
        ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.LoginProxyCompleteMessage,
        on_response: Callable[[None | Exception], None],
    ) -> None:
        ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.PingMessage,
        on_response: Callable[[bacommon.cloud.PingResponse | Exception], None],
    ) -> None:
        ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.SignInMessage,
        on_response: Callable[
            [bacommon.cloud.SignInResponse | Exception], None
        ],
    ) -> None:
        ...

    @overload
    def send_message_cb(
        self,
        msg: bacommon.cloud.ManageAccountMessage,
        on_response: Callable[
            [bacommon.cloud.ManageAccountResponse | Exception], None
        ],
    ) -> None:
        ...

    def send_message_cb(
        self,
        msg: Message,
        on_response: Callable[[Any], None],
    ) -> None:
        """Asynchronously send a message to the cloud from the logic thread.

        The provided on_response call will be run in the logic thread
        and passed either the response or the error that occurred.
        """
        from babase._general import Call

        del msg  # Unused.

        _babase.pushcall(
            Call(
                on_response,
                RuntimeError('Cloud functionality is not available.'),
            )
        )

    @overload
    def send_message(
        self, msg: bacommon.cloud.WorkspaceFetchMessage
    ) -> bacommon.cloud.WorkspaceFetchResponse:
        ...

    @overload
    def send_message(
        self, msg: bacommon.cloud.MerchAvailabilityMessage
    ) -> bacommon.cloud.MerchAvailabilityResponse:
        ...

    @overload
    def send_message(
        self, msg: bacommon.cloud.TestMessage
    ) -> bacommon.cloud.TestResponse:
        ...

    def send_message(self, msg: Message) -> Response | None:
        """Synchronously send a message to the cloud.

        Must be called from a background thread.
        """
        raise RuntimeError('Cloud functionality is not available.')


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

        apptime = _babase.apptime()
        print(f'Exec error at time {apptime:.2f}.', file=sys.stderr)
        traceback.print_exc()

        # This helps the logging system ship stderr back to the
        # cloud promptly.
        sys.stderr.flush()
