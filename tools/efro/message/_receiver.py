# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

import types
import inspect
import logging
from typing import TYPE_CHECKING

from efro.message._message import (
    Message,
    Response,
    EmptySysResponse,
    UnregisteredMessageIDError,
)

if TYPE_CHECKING:
    from typing import Any, Callable, Awaitable

    from efro.message._protocol import MessageProtocol
    from efro.message._message import SysResponse


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
        self._decode_filter_call: Callable[
            [Any, dict, Message], None
        ] | None = None
        self._encode_filter_call: Callable[
            [Any, Message | None, Response | SysResponse, dict], None
        ] | None = None

        # TODO: don't currently have async encode equivalent
        # or either for sender; can add as needed.
        self._decode_filter_async_call: Callable[
            [Any, dict, Message], Awaitable[None]
        ] | None = None

    # noinspection PyProtectedMember
    def register_handler(
        self, call: Callable[[Any, Message], Response | None]
    ) -> None:
        """Register a handler call.

        The message type handled by the call is determined by its
        type annotation.
        """
        # TODO: can use types.GenericAlias in 3.9.
        # (hmm though now that we're there,  it seems a drop-in
        # replace gives us errors. Should re-test in 3.10 as it seems
        # that typing_extensions handles it differently in that case)
        from typing import _GenericAlias  # type: ignore
        from typing import get_type_hints, get_args

        sig = inspect.getfullargspec(call)

        # The provided callable should be a method taking one 'msg' arg.
        expectedsig = ['self', 'msg']
        if sig.args != expectedsig:
            raise ValueError(
                f'Expected callable signature of {expectedsig};'
                f' got {sig.args}'
            )

        # Make sure we are only given async methods if we are an async handler
        # and sync ones otherwise.
        is_async = inspect.iscoroutinefunction(call)
        if self.is_async != is_async:
            msg = (
                'Expected a sync method; found an async one.'
                if is_async
                else 'Expected an async method; found a sync one.'
            )
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
                f'expected a type for "msg" annotation; got {type(msgtype)}.'
            )
        assert issubclass(msgtype, Message)

        ret = anns.get('return')
        responsetypes: tuple[type[Any] | None, ...]

        # Return types can be a single type or a union of types.
        if isinstance(ret, (_GenericAlias, types.UnionType)):
            targs = get_args(ret)
            if not all(isinstance(a, (type, type(None))) for a in targs):
                raise TypeError(
                    f'expected only types for "return" annotation;'
                    f' got {targs}.'
                )
            responsetypes = targs
        else:
            if not isinstance(ret, (type, type(None))):
                raise TypeError(
                    f'expected one or more types for'
                    f' "return" annotation; got a {type(ret)}.'
                )
            # This seems like maybe a mypy bug. Appeared after adding
            # types.UnionType above.
            responsetypes = (ret,)

        # This will contain NoneType for empty return cases, but
        # we expect it to be None.
        responsetypes = tuple(
            None if r is type(None) else r for r in responsetypes
        )

        # Make sure our protocol has this message type registered and our
        # return types exactly match. (Technically we could return a subset
        # of the supported types; can allow this in the future if it makes
        # sense).
        registered_types = self.protocol.message_ids_by_type.keys()

        if msgtype not in registered_types:
            raise TypeError(
                f'Message type {msgtype} is not registered'
                f' in this Protocol.'
            )

        if msgtype in self._handlers:
            raise TypeError(
                f'Message type {msgtype} already has a registered' f' handler.'
            )

        # Make sure the responses exactly matches what the message expects.
        if set(responsetypes) != set(msgtype.get_response_types()):
            raise TypeError(
                f'Provided response types {responsetypes} do not'
                f' match the set expected by message type {msgtype}: '
                f'({msgtype.get_response_types()})'
            )

        # Ok; we're good!
        self._handlers[msgtype] = call

    def decode_filter_method(
        self, call: Callable[[Any, dict, Message], None]
    ) -> Callable[[Any, dict, Message], None]:
        """Function decorator for defining a decode filter.

        Decode filters can be used to extract extra data from incoming
        message dicts. This version will work for both handle_raw_message()
        and handle_raw_message_async()
        """
        assert self._decode_filter_call is None
        self._decode_filter_call = call
        return call

    def decode_filter_async_method(
        self, call: Callable[[Any, dict, Message], Awaitable[None]]
    ) -> Callable[[Any, dict, Message], Awaitable[None]]:
        """Function decorator for defining a decode filter.

        Decode filters can be used to extract extra data from incoming
        message dicts. Note that this version will only work with
        handle_raw_message_async().
        """
        assert self._decode_filter_async_call is None
        self._decode_filter_async_call = call
        return call

    def encode_filter_method(
        self,
        call: Callable[
            [Any, Message | None, Response | SysResponse, dict], None
        ],
    ) -> Callable[[Any, Message | None, Response, dict], None]:
        """Function decorator for defining an encode filter.

        Encode filters can be used to add extra data to the message
        dict before is is encoded to a string and sent out.
        """
        assert self._encode_filter_call is None
        self._encode_filter_call = call
        return call

    def validate(self, log_only: bool = False) -> None:
        """Check for handler completeness, valid types, etc."""
        for msgtype in self.protocol.message_ids_by_type.keys():
            if issubclass(msgtype, Response):
                continue
            if msgtype not in self._handlers:
                msg = (
                    f'Protocol message type {msgtype} is not handled'
                    f' by receiver type {type(self)}.'
                )
                if log_only:
                    logging.error(msg)
                else:
                    raise TypeError(msg)

    def _decode_incoming_message_base(
        self, bound_obj: Any, msg: str
    ) -> tuple[Any, dict, Message]:
        # Decode the incoming message.
        msg_dict = self.protocol.decode_dict(msg)
        msg_decoded = self.protocol.message_from_dict(msg_dict)
        assert isinstance(msg_decoded, Message)
        if self._decode_filter_call is not None:
            self._decode_filter_call(bound_obj, msg_dict, msg_decoded)
        return bound_obj, msg_dict, msg_decoded

    def _decode_incoming_message(self, bound_obj: Any, msg: str) -> Message:
        bound_obj, _msg_dict, msg_decoded = self._decode_incoming_message_base(
            bound_obj=bound_obj, msg=msg
        )

        # If they've set an async filter but are calling sync
        # handle_raw_message() its likely a bug.
        assert self._decode_filter_async_call is None

        return msg_decoded

    async def _decode_incoming_message_async(
        self, bound_obj: Any, msg: str
    ) -> Message:
        bound_obj, msg_dict, msg_decoded = self._decode_incoming_message_base(
            bound_obj=bound_obj, msg=msg
        )

        if self._decode_filter_async_call is not None:
            await self._decode_filter_async_call(
                bound_obj, msg_dict, msg_decoded
            )
        return msg_decoded

    def encode_user_response(
        self, bound_obj: Any, message: Message, response: Response | None
    ) -> str:
        """Encode a response provided by the user for sending."""

        assert isinstance(response, Response | None)
        # (user should never explicitly return error-responses)
        assert (
            response is None or type(response) in message.get_response_types()
        )

        # A return value of None equals EmptySysResponse.
        out_response: Response | SysResponse
        if response is None:
            out_response = EmptySysResponse()
        else:
            out_response = response

        response_dict = self.protocol.response_to_dict(out_response)
        if self._encode_filter_call is not None:
            self._encode_filter_call(
                bound_obj, message, out_response, response_dict
            )
        return self.protocol.encode_dict(response_dict)

    def encode_error_response(
        self, bound_obj: Any, message: Message | None, exc: Exception
    ) -> tuple[str, bool]:
        """Given an error, return sysresponse str and whether to log."""
        response, dolog = self.protocol.error_to_response(exc)
        response_dict = self.protocol.response_to_dict(response)
        if self._encode_filter_call is not None:
            self._encode_filter_call(
                bound_obj, message, response, response_dict
            )
        return self.protocol.encode_dict(response_dict), dolog

    def handle_raw_message(
        self, bound_obj: Any, msg: str, raise_unregistered: bool = False
    ) -> str:
        """Decode, handle, and return an response for a message.

        if 'raise_unregistered' is True, will raise an
        efro.message.UnregisteredMessageIDError for messages not handled by
        the protocol. In all other cases local errors will translate to
        error responses returned to the sender.
        """
        assert not self.is_async, "can't call sync handler on async receiver"
        msg_decoded: Message | None = None
        try:
            msg_decoded = self._decode_incoming_message(bound_obj, msg)
            msgtype = type(msg_decoded)
            handler = self._handlers.get(msgtype)
            if handler is None:
                raise RuntimeError(f'Got unhandled message type: {msgtype}.')
            response = handler(bound_obj, msg_decoded)
            assert isinstance(response, Response | None)
            return self.encode_user_response(bound_obj, msg_decoded, response)

        except Exception as exc:
            if raise_unregistered and isinstance(
                exc, UnregisteredMessageIDError
            ):
                raise
            rstr, dolog = self.encode_error_response(
                bound_obj, msg_decoded, exc
            )
            if dolog:
                logging.exception('Error in efro.message handling.')
            return rstr

    async def handle_raw_message_async(
        self, bound_obj: Any, msg: str, raise_unregistered: bool = False
    ) -> str:
        """Should be called when the receiver gets a message.

        The return value is the raw response to the message.
        """
        assert self.is_async, "can't call async handler on sync receiver"
        msg_decoded: Message | None = None
        try:
            msg_decoded = await self._decode_incoming_message_async(
                bound_obj, msg
            )
            msgtype = type(msg_decoded)
            handler = self._handlers.get(msgtype)
            if handler is None:
                raise RuntimeError(f'Got unhandled message type: {msgtype}.')
            response = await handler(bound_obj, msg_decoded)
            assert isinstance(response, Response | None)
            return self.encode_user_response(bound_obj, msg_decoded, response)

        except Exception as exc:
            if raise_unregistered and isinstance(
                exc, UnregisteredMessageIDError
            ):
                raise
            rstr, dolog = self.encode_error_response(
                bound_obj, msg_decoded, exc
            )
            if dolog:
                logging.exception('Error in efro.message handling.')
            return rstr


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

    def encode_error_response(self, exc: Exception) -> str:
        """Given an error, return a response ready to send.

        This should be used for any errors that happen outside of
        standard handle_raw_message calls. Any errors within those
        calls will be automatically returned as encoded strings.
        """
        # Passing None for Message here; we would only have that available
        # for things going wrong in the handler (which this is not for).
        return self._receiver.encode_error_response(self._obj, None, exc)[0]
