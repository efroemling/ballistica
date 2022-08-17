# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, TypeVar

from efro.error import CleanError, RemoteError, CommunicationError
from efro.message._message import EmptyResponse, ErrorResponse

if TYPE_CHECKING:
    from typing import Any, Callable, Awaitable

    from efro.message._message import Message, Response
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

    # MyMessageSender class should provide overloads for send(), send_async(),
    # etc. to ensure all sending happens with valid types.
    obj = MyClass()
    obj.msg.send(SomeMessageType())
    """

    def __init__(self, protocol: MessageProtocol) -> None:
        self.protocol = protocol
        self._send_raw_message_call: Callable[[Any, str], str] | None = None
        self._send_async_raw_message_call: Callable[
            [Any, str], Awaitable[str]] | None = None
        self._encode_filter_call: Callable[[Any, Message, dict],
                                           None] | None = None
        self._decode_filter_call: Callable[[Any, Message, dict, Response],
                                           None] | None = None

    def send_method(
            self, call: Callable[[Any, str],
                                 str]) -> Callable[[Any, str], str]:
        """Function decorator for setting raw send method.

        Send methods take strings and should return strings.
        CommunicationErrors raised here will be returned to the sender
        as such; all other exceptions will result in a RuntimeError for
        the sender.
        """
        assert self._send_raw_message_call is None
        self._send_raw_message_call = call
        return call

    def send_async_method(
        self, call: Callable[[Any, str], Awaitable[str]]
    ) -> Callable[[Any, str], Awaitable[str]]:
        """Function decorator for setting raw send-async method.

        Send methods take strings and should return strings.
        CommunicationErrors raised here will be returned to the sender
        as such; all other exceptions will result in a RuntimeError for
        the sender.
        """
        assert self._send_async_raw_message_call is None
        self._send_async_raw_message_call = call
        return call

    def encode_filter_method(
        self, call: Callable[[Any, Message, dict], None]
    ) -> Callable[[Any, Message, dict], None]:
        """Function decorator for defining an encode filter.

        Encode filters can be used to add extra data to the message
        dict before is is encoded to a string and sent out.
        """
        assert self._encode_filter_call is None
        self._encode_filter_call = call
        return call

    def decode_filter_method(
        self, call: Callable[[Any, Message, dict, Response], None]
    ) -> Callable[[Any, Message, dict, Response], None]:
        """Function decorator for defining a decode filter.

        Decode filters can be used to extract extra data from incoming
        message dicts.
        """
        assert self._decode_filter_call is None
        self._decode_filter_call = call
        return call

    def send(self, bound_obj: Any, message: Message) -> Response | None:
        """Send a message synchronously."""
        return self.send_split_part_2(
            message=message,
            raw_response=self.send_split_part_1(
                bound_obj=bound_obj,
                message=message,
            ),
        )

    async def send_async(self, bound_obj: Any,
                         message: Message) -> Response | None:
        """Send a message asynchronously."""
        return self.send_split_part_2(
            message=message,
            raw_response=await self.send_split_part_1_async(
                bound_obj=bound_obj,
                message=message,
            ),
        )

    def send_split_part_1(self, bound_obj: Any, message: Message) -> Response:
        """Send a message synchronously.

        Generally you can just call send(); these split versions are
        for when message sending and response handling need to happen
        in different contexts/threads.
        """
        if self._send_raw_message_call is None:
            raise RuntimeError('send() is unimplemented for this type.')

        msg_encoded = self._encode_message(bound_obj, message)
        try:
            response_encoded = self._send_raw_message_call(
                bound_obj, msg_encoded)
        except Exception as exc:
            # Any error in the raw send call gets recorded as either
            # a local or communication error.
            return ErrorResponse(
                error_message=f'Error in send method ({type(exc)}): {exc}',
                error_type=(ErrorResponse.ErrorType.COMMUNICATION
                            if isinstance(exc, CommunicationError) else
                            ErrorResponse.ErrorType.LOCAL))
        return self._decode_raw_response(bound_obj, message, response_encoded)

    async def send_split_part_1_async(self, bound_obj: Any,
                                      message: Message) -> Response:
        """Send a message asynchronously.

        Generally you can just call send(); these split versions are
        for when message sending and response handling need to happen
        in different contexts/threads.
        """

        if self._send_async_raw_message_call is None:
            raise RuntimeError('send_async() is unimplemented for this type.')

        msg_encoded = self._encode_message(bound_obj, message)
        try:
            response_encoded = await self._send_async_raw_message_call(
                bound_obj, msg_encoded)
        except Exception as exc:
            # Any error in the raw send call gets recorded as either
            # a local or communication error.
            return ErrorResponse(
                error_message=f'Error in send async method ({type(exc)}):'
                f' {exc}',
                error_type=(ErrorResponse.ErrorType.COMMUNICATION
                            if isinstance(exc, CommunicationError) else
                            ErrorResponse.ErrorType.LOCAL))
        return self._decode_raw_response(bound_obj, message, response_encoded)

    def send_split_part_2(self, message: Message,
                          raw_response: Response) -> Response | None:
        """Complete message sending (both sync and async).

        Generally you can just call send(); these split versions are
        for when message sending and response handling need to happen
        in different contexts/threads.
        """
        response = self._unpack_raw_response(raw_response)
        assert (response is None
                or type(response) in type(message).get_response_types())
        return response

    def _encode_message(self, bound_obj: Any, message: Message) -> str:
        """Encode a message for sending."""
        msg_dict = self.protocol.message_to_dict(message)
        if self._encode_filter_call is not None:
            self._encode_filter_call(bound_obj, message, msg_dict)
        return self.protocol.encode_dict(msg_dict)

    def _decode_raw_response(self, bound_obj: Any, message: Message,
                             response_encoded: str) -> Response:
        """Create a Response from returned data.

        These Responses may encapsulate things like remote errors and
        should not be handed directly to users. _unpack_raw_response()
        should be used to translate to special values like None or raise
        Exceptions. This function itself should never raise Exceptions.
        """
        try:
            response_dict = self.protocol.decode_dict(response_encoded)
            response = self.protocol.response_from_dict(response_dict)
            if self._decode_filter_call is not None:
                self._decode_filter_call(bound_obj, message, response_dict,
                                         response)
        except Exception:
            # If we got to this point, we successfully communicated
            # with the other end so errors represent protocol mismatches
            # or other invalid data. For now let's just log it but perhaps
            # we'd want to somehow embed it in the ErrorResponse to be
            # available directly to the user later.
            logging.exception('Error decoding raw response')
            response = ErrorResponse(
                error_message=
                'Error decoding raw response; see log for details.',
                error_type=ErrorResponse.ErrorType.LOCAL)
        return response

    def _unpack_raw_response(self, raw_response: Response) -> Response | None:
        """Given a raw Response, unpacks to special values or Exceptions.

        The result of this call is what should be passed to users.
        For complex messaging situations such as response callbacks
        operating across different threads, this last stage should be
        run such that any raised Exception is active when the callback
        fires; not on the thread where the message was sent.
        """
        # EmptyResponse translates to None
        if isinstance(raw_response, EmptyResponse):
            return None

        # Some error occurred. Raise a local Exception for it.
        if isinstance(raw_response, ErrorResponse):

            if (raw_response.error_type is
                    ErrorResponse.ErrorType.COMMUNICATION):
                raise CommunicationError(raw_response.error_message)

            # If something went wrong on *our* end of the connection,
            # don't say it was a remote error.
            if raw_response.error_type is ErrorResponse.ErrorType.LOCAL:
                raise RuntimeError(raw_response.error_message)

            # If they want to support clean errors, do those.
            if (self.protocol.preserve_clean_errors and raw_response.error_type
                    is ErrorResponse.ErrorType.REMOTE_CLEAN):
                raise CleanError(raw_response.error_message)

            # Everything else gets lumped in as a remote error.
            raise RemoteError(raw_response.error_message)

        return raw_response


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

    def send_untyped(self, message: Message) -> Response | None:
        """Send a message synchronously.

        Whenever possible, use the send() call provided by generated
        subclasses instead of this; it will provide better type safety.
        """
        assert self._obj is not None
        return self._sender.send(bound_obj=self._obj, message=message)

    async def send_async_untyped(self, message: Message) -> Response | None:
        """Send a message asynchronously.

        Whenever possible, use the send_async() call provided by generated
        subclasses instead of this; it will provide better type safety.
        """
        assert self._obj is not None
        return await self._sender.send_async(bound_obj=self._obj,
                                             message=message)

    async def send_split_part_1_async_untyped(self,
                                              message: Message) -> Response:
        """Split send (part 1 of 2)."""
        assert self._obj is not None
        return await self._sender.send_split_part_1_async(bound_obj=self._obj,
                                                          message=message)

    def send_split_part_2_untyped(self, message: Message,
                                  raw_response: Response) -> Response | None:
        """Split send (part 2 of 2)."""
        return self._sender.send_split_part_2(message=message,
                                              raw_response=raw_response)
