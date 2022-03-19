# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING

from efro.message._message import (Message, Response, EmptyResponse,
                                   ErrorResponse, UnregisteredMessageIDError)

if TYPE_CHECKING:
    from typing import Any, Callable, Optional, Awaitable, Union

    from efro.message._protocol import MessageProtocol


class MessageReceiver:
    """Facilitates receiving & responding to messages from a remote source.

    This is instantiated at the class level with unbound methods registered
    as handlers for different message types in the protocol.

    Example:

    class MyClass:
        receiver = MyMessageReceiver()

        # MyMessageReceiver fills out handler() overloads to ensure all
        # registered handlers have valid types/return-types.
        @receiver.handler
        def handle_some_message_type(self, message: SomeMsg) -> SomeResponse:
            # Deal with this message type here.

    # This will trigger the registered handler being called.
    obj = MyClass()
    obj.receiver.handle_raw_message(some_raw_data)

    Any unhandled Exception occurring during message handling will result in
    an Exception being raised on the sending end.
    """

    is_async = False

    def __init__(self, protocol: MessageProtocol) -> None:
        self.protocol = protocol
        self._handlers: dict[type[Message], Callable] = {}

    # noinspection PyProtectedMember
    def register_handler(
            self, call: Callable[[Any, Message], Optional[Response]]) -> None:
        """Register a handler call.

        The message type handled by the call is determined by its
        type annotation.
        """
        # TODO: can use types.GenericAlias in 3.9.
        from typing import _GenericAlias  # type: ignore
        from typing import get_type_hints, get_args

        sig = inspect.getfullargspec(call)

        # The provided callable should be a method taking one 'msg' arg.
        expectedsig = ['self', 'msg']
        if sig.args != expectedsig:
            raise ValueError(f'Expected callable signature of {expectedsig};'
                             f' got {sig.args}')

        # Make sure we are only given async methods if we are an async handler
        # and sync ones otherwise.
        is_async = inspect.iscoroutinefunction(call)
        if self.is_async != is_async:
            msg = ('Expected a sync method; found an async one.' if is_async
                   else 'Expected an async method; found a sync one.')
            raise ValueError(msg)

        # Check annotation types to determine what message types we handle.
        # Return-type annotation can be a Union, but we probably don't
        # have it available at runtime. Explicitly pull it in.
        # UPDATE: we've updated our pylint filter to where we should
        # have all annotations available.
        # anns = get_type_hints(call, localns={'Union': Union})
        anns = get_type_hints(call)

        msgtype = anns.get('msg')
        if not isinstance(msgtype, type):
            raise TypeError(
                f'expected a type for "msg" annotation; got {type(msgtype)}.')
        assert issubclass(msgtype, Message)

        ret = anns.get('return')
        responsetypes: tuple[Union[type[Any], type[None]], ...]

        # Return types can be a single type or a union of types.
        if isinstance(ret, _GenericAlias):
            targs = get_args(ret)
            if not all(isinstance(a, type) for a in targs):
                raise TypeError(f'expected only types for "return" annotation;'
                                f' got {targs}.')
            responsetypes = targs
        else:
            if not isinstance(ret, type):
                raise TypeError(f'expected one or more types for'
                                f' "return" annotation; got a {type(ret)}.')
            responsetypes = (ret, )

        # Return type of None translates to EmptyResponse.
        responsetypes = tuple(EmptyResponse if r is type(None) else r
                              for r in responsetypes)  # noqa

        # Make sure our protocol has this message type registered and our
        # return types exactly match. (Technically we could return a subset
        # of the supported types; can allow this in the future if it makes
        # sense).
        registered_types = self.protocol.message_ids_by_type.keys()

        if msgtype not in registered_types:
            raise TypeError(f'Message type {msgtype} is not registered'
                            f' in this Protocol.')

        if msgtype in self._handlers:
            raise TypeError(f'Message type {msgtype} already has a registered'
                            f' handler.')

        # Make sure the responses exactly matches what the message expects.
        if set(responsetypes) != set(msgtype.get_response_types()):
            raise TypeError(
                f'Provided response types {responsetypes} do not'
                f' match the set expected by message type {msgtype}: '
                f'({msgtype.get_response_types()})')

        # Ok; we're good!
        self._handlers[msgtype] = call

    def validate(self, log_only: bool = False) -> None:
        """Check for handler completeness, valid types, etc."""
        for msgtype in self.protocol.message_ids_by_type.keys():
            if issubclass(msgtype, Response):
                continue
            if msgtype not in self._handlers:
                msg = (f'Protocol message type {msgtype} is not handled'
                       f' by receiver type {type(self)}.')
                if log_only:
                    logging.error(msg)
                else:
                    raise TypeError(msg)

    def _decode_incoming_message(self,
                                 msg: str) -> tuple[Message, type[Message]]:
        # Decode the incoming message.
        msg_decoded = self.protocol.decode_message(msg)
        msgtype = type(msg_decoded)
        assert issubclass(msgtype, Message)
        return msg_decoded, msgtype

    def _encode_response(self, response: Optional[Response],
                         msgtype: type[Message]) -> str:

        # A return value of None equals EmptyResponse.
        if response is None:
            response = EmptyResponse()

        assert isinstance(response, Response)
        # (user should never explicitly return error-responses)
        assert not isinstance(response, ErrorResponse)
        assert type(response) in msgtype.get_response_types()
        return self.protocol.encode_response(response)

    def handle_raw_message(self,
                           bound_obj: Any,
                           msg: str,
                           raise_unregistered: bool = False) -> str:
        """Decode, handle, and return an response for a message.

        if 'raise_unregistered' is True, will raise an
        efro.message.UnregisteredMessageIDError for messages not handled by
        the protocol. In all other cases local errors will translate to
        error responses returned to the sender.
        """
        assert not self.is_async, "can't call sync handler on async receiver"
        try:
            msg_decoded, msgtype = self._decode_incoming_message(msg)
            handler = self._handlers.get(msgtype)
            if handler is None:
                raise RuntimeError(f'Got unhandled message type: {msgtype}.')
            result = handler(bound_obj, msg_decoded)
            return self._encode_response(result, msgtype)

        except Exception as exc:
            if (raise_unregistered
                    and isinstance(exc, UnregisteredMessageIDError)):
                raise
            return self.protocol.encode_error_response(exc)

    async def handle_raw_message_async(
            self,
            bound_obj: Any,
            msg: str,
            raise_unregistered: bool = False) -> str:
        """Should be called when the receiver gets a message.

        The return value is the raw response to the message.
        """
        assert self.is_async, "can't call async handler on sync receiver"
        try:
            msg_decoded, msgtype = self._decode_incoming_message(msg)
            handler = self._handlers.get(msgtype)
            if handler is None:
                raise RuntimeError(f'Got unhandled message type: {msgtype}.')
            result = await handler(bound_obj, msg_decoded)
            return self._encode_response(result, msgtype)

        except Exception as exc:
            if (raise_unregistered
                    and isinstance(exc, UnregisteredMessageIDError)):
                raise
            return self.protocol.encode_error_response(exc)


class BoundMessageReceiver:
    """Base bound receiver class."""

    def __init__(
        self,
        obj: Any,
        receiver: MessageReceiver,
    ) -> None:
        assert obj is not None
        self._obj = obj
        self._receiver = receiver

    @property
    def protocol(self) -> MessageProtocol:
        """Protocol associated with this receiver."""
        return self._receiver.protocol
