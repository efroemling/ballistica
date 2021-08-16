# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Type, Tuple, List, Any, Callable, Optional


class MessageProtocol:
    """Wrangles a set of message types, formats, and response types.
    Both endpoints must be using the same Protocol (even if one side
    is newer) for communication to succeed.
    """

    def __init__(
        self,
        message_types: Dict[int, Tuple[Type, List[Type]]],
        type_key: str = '_t',
    ) -> None:
        """Create a protocol with the given settings.
        Each entry for message_types should contain an ID, a message type,
        and all possible response types.
        """

    @classmethod
    def create_sender_module(cls, classname: str) -> str:
        """"Create a Python module defining a MessageSender subclass.

        This class is primarily for type checking and will contain overrides
        for the varieties of send calls for message/response types defined
        in the protocol.
        """

    @classmethod
    def create_receiver_module(cls, classname: str) -> str:
        """"Create a Python module defining a MessageReceiver subclass.

        This class is primarily for type checking and will contain overrides
        for the register method for message/response types defined in
        the protocol.
        """


class TransportError(Exception):
    """Error occurring for all transport related errors in messaging.

    This covers anything network-related going wrong in the sending
    of data or receiving of the response. This error does not imply
    that the message was not received on the other end; only that a
    complete response round trip was not completed.
    """


class MessageSender:
    """Facilitates sending messages to a target and receiving responses.
    This is instantiated at the class level and used to register unbound
    class methods to handle raw message sending.

    Example:

    class MyClass:

        def send_raw_message(self, message: bytes) -> bytes:
            # Actually send the message here.

        msg = MyMessageSender(some_protocol, send_raw_message)

    # MyMessageSender class should provide overloads for send(), send_bg(),
    # etc. to ensure all sending happens with valid types.
    obj = MyClass()
    obj.msg.send(SomeMessageType())
    """

    def __init__(
            self, protocol: MessageProtocol,
            send_raw_message: Optional[Callable[[Any, bytes], bytes]]) -> None:
        self._protocol = protocol
        self._send_raw_message = send_raw_message

    def __get__(self, obj: Any, type_in: Any = None) -> Any:
        if obj is None:
            raise RuntimeError('Must be called on an instance, not a type.')
        print(f'HELLO FROM GET {obj}')
        return self

    def send(self, message: Any) -> Any:
        """Send a message and receive a response.
        Will encode the message for transport and call dispatch_raw_message()
        """
        if self._send_raw_message is None:
            raise RuntimeError('Unimplemented!')
        print(f'WOULD CONVERT MSG TO RAW: {message}')
        return self._send_raw_message(None, b'')

    def send_bg(self, message: Any) -> Any:
        """Send a message asynchronously and receive a future.
        The message will be encoded for transport and passed to
        dispatch_raw_message from a background thread.
        """
        raise RuntimeError('Unimplemented!')

    def send_async(self, message: Any) -> Any:
        """Send a message asynchronously using asyncio.
        The message will be encoded for transport and passed to
        dispatch_raw_message_async.
        """
        raise RuntimeError('Unimplemented!')

    # def send_raw_message(self, msg: bytes) -> bytes:
    #     """Send a message and get a response synchronously.
    #     Should be overridden by child classes if supported.
    #     Gets called by send() or in a bg thread by send_bg().
    #     """
    #     raise TransportError('Unimplemented for this dispatch type.')

    # async def send_raw_message_async(self, msg: bytes) -> bytes:
    #     """Send a message and get a response via asyncio.
    #     Should be overridden by child classes if supported.
    #     """
    #     raise TransportError('Unimplemented for this dispatch type.')


class MessageReceiver:
    """Facilitates receiving & responding to messages from a remote source.
    This is instantiated at the class level with unbound methods registered
    as handlers for different message types in the protocol.

    Example:

    class MyClass:
        receiver = MyMessageReceiver()

        # MyMessageReceiver should provide overloads to register_handler()
        # to ensure all registered handlers have valid types/return-types.
        @receiver.register_handler
        def handle_some_message_type(self, message: SomeType) -> AnotherType:
            # Deal with this message type here.

    # This will be passed along to the registered handler.
    obj = MyClass()
    obj.receiver.handle_raw_message(some_raw_data)
    """

    def __init__(self, protocol: MessageProtocol) -> None:
        pass

    def register(self, call: Callable) -> None:
        """Register a call to handle a message type in the protocol."""

    def handle_raw_message(self, msg: bytes) -> bytes:
        """Should be called when the receiver gets a message.
        The return value is the raw response to the message.
        """

    async def handle_raw_message_async(self, msg: bytes) -> bytes:
        """Should be called when the receiver gets a message.
        The return value is the raw response to the message.
        """


# class SubTest(MessageSender):
#     """Test."""

#     if TYPE_CHECKING:

#         @overload
#         def send(self, message: str) -> str:
#             pass

#         @overload
#         def send(self, message: bool) -> bool:
#             pass

#         def send(self, message: Any) -> Any:
#             pass

# blah = SubTest(protocol=MessageProtocol(message_types={}))
# blah.send('foo')
