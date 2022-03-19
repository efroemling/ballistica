# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from efro.message._message import Response

if TYPE_CHECKING:
    from typing import Any, Callable, Optional, Awaitable

    from efro.message._message import Message
    from efro.message._protocol import MessageProtocol

TM = TypeVar('TM', bound='MessageSender')


class MessageSender:
    """Facilitates sending messages to a target and receiving responses.
    This is instantiated at the class level and used to register unbound
    class methods to handle raw message sending.

    Example:

    class MyClass:
        msg = MyMessageSender(some_protocol)

        @msg.send_method
        def send_raw_message(self, message: str) -> str:
            # Actually send the message here.

    # MyMessageSender class should provide overloads for send(), send_bg(),
    # etc. to ensure all sending happens with valid types.
    obj = MyClass()
    obj.msg.send(SomeMessageType())
    """

    def __init__(self, protocol: MessageProtocol) -> None:
        self.protocol = protocol
        self._send_raw_message_call: Optional[Callable[[Any, str], str]] = None
        self._send_async_raw_message_call: Optional[Callable[
            [Any, str], Awaitable[str]]] = None

    def send_method(
            self, call: Callable[[Any, str],
                                 str]) -> Callable[[Any, str], str]:
        """Function decorator for setting raw send method."""
        assert self._send_raw_message_call is None
        self._send_raw_message_call = call
        return call

    def send_async_method(
        self, call: Callable[[Any, str], Awaitable[str]]
    ) -> Callable[[Any, str], Awaitable[str]]:
        """Function decorator for setting raw send-async method."""
        assert self._send_async_raw_message_call is None
        self._send_async_raw_message_call = call
        return call

    def send(self, bound_obj: Any, message: Message) -> Optional[Response]:
        """Send a message and receive a response.

        Will encode the message for transport and call dispatch_raw_message()
        """
        if self._send_raw_message_call is None:
            raise RuntimeError('send() is unimplemented for this type.')

        msg_encoded = self.protocol.encode_message(message)
        response_encoded = self._send_raw_message_call(bound_obj, msg_encoded)
        response = self.protocol.decode_response(response_encoded)
        assert isinstance(response, (Response, type(None)))
        assert (response is None
                or type(response) in type(message).get_response_types())
        return response

    async def send_async(self, bound_obj: Any,
                         message: Message) -> Optional[Response]:
        """Send a message asynchronously using asyncio.

        The message will be encoded for transport and passed to
        dispatch_raw_message_async.
        """
        if self._send_async_raw_message_call is None:
            raise RuntimeError('send_async() is unimplemented for this type.')

        msg_encoded = self.protocol.encode_message(message)
        response_encoded = await self._send_async_raw_message_call(
            bound_obj, msg_encoded)
        response = self.protocol.decode_response(response_encoded)
        assert isinstance(response, (Response, type(None)))
        assert (response is None
                or type(response) in type(message).get_response_types())
        return response


class BoundMessageSender:
    """Base class for bound senders."""

    def __init__(self, obj: Any, sender: MessageSender) -> None:
        # Note: not checking obj here since we want to support
        # at least our protocol property when accessed via type.
        self._obj = obj
        self._sender = sender

    @property
    def protocol(self) -> MessageProtocol:
        """Protocol associated with this sender."""
        return self._sender.protocol

    def send_untyped(self, message: Message) -> Optional[Response]:
        """Send a message synchronously.

        Whenever possible, use the send() call provided by generated
        subclasses instead of this; it will provide better type safety.
        """
        assert self._obj is not None
        return self._sender.send(self._obj, message)

    async def send_async_untyped(self, message: Message) -> Optional[Response]:
        """Send a message asynchronously.

        Whenever possible, use the send_async() call provided by generated
        subclasses instead of this; it will provide better type safety.
        """
        assert self._obj is not None
        return await self._sender.send_async(self._obj, message)
