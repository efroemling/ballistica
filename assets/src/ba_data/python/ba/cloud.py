# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the cloud."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

import _ba

if TYPE_CHECKING:
    from typing import Union, Callable, Any

    from efro.message import Message
    import bacommon.cloud

# TODO: Should make it possible to define a protocol in bacommon.cloud and
# autogenerate this. That would give us type safety between this and
# internal protocols.


class CloudSubsystem:
    """Used for communicating with the cloud."""

    def is_connected(self) -> bool:
        """Return whether a connection to the cloud is present.

        This is a good indicator (though not for certain) that sending
        messages will succeed.
        """
        return False  # Needs to be overridden

    @overload
    def send_message(
        self,
        msg: bacommon.cloud.LoginProxyRequestMessage,
        on_response: Callable[
            [Union[bacommon.cloud.LoginProxyRequestResponse,
                   Exception]], None],
    ) -> None:
        ...

    @overload
    def send_message(
        self,
        msg: bacommon.cloud.LoginProxyStateQueryMessage,
        on_response: Callable[
            [Union[bacommon.cloud.LoginProxyStateQueryResponse,
                   Exception]], None],
    ) -> None:
        ...

    @overload
    def send_message(
        self,
        msg: bacommon.cloud.LoginProxyCompleteMessage,
        on_response: Callable[[Union[None, Exception]], None],
    ) -> None:
        ...

    @overload
    def send_message(
        self,
        msg: bacommon.cloud.CredentialsCheckMessage,
        on_response: Callable[
            [Union[bacommon.cloud.CredentialsCheckResponse, Exception]], None],
    ) -> None:
        ...

    @overload
    def send_message(
        self,
        msg: bacommon.cloud.AccountSessionReleaseMessage,
        on_response: Callable[[Union[None, Exception]], None],
    ) -> None:
        ...

    def send_message(
        self,
        msg: Message,
        on_response: Callable[[Any], None],
    ) -> None:
        """Asynchronously send a message to the cloud from the game thread.

        The provided on_response call will be run in the logic thread
        and passed either the response or the error that occurred.
        """
        from ba._general import Call
        del msg  # Unused.

        _ba.pushcall(
            Call(on_response,
                 RuntimeError('Cloud functionality is not available.')))
