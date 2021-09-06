# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar
from dataclasses import dataclass
from enum import Enum
import json

from typing_extensions import Annotated

from efro.dataclassio import (ioprepped, is_ioprepped_dataclass, IOAttrs,
                              dataclass_to_dict)

if TYPE_CHECKING:
    from typing import (Dict, Type, Tuple, List, Any, Callable, Optional, Set,
                        Sequence)
    from efro.error import CommunicationError

TM = TypeVar('TM', bound='MessageSender')


class RemoteErrorType(Enum):
    """Type of error that occurred in remote message handling."""
    OTHER = 0
    CLEAN = 1


class Message:
    """Base class for messages and their responses."""

    @classmethod
    def get_response_types(cls) -> List[Type[Message]]:
        """Return all message types this Message can result in when sent.
        Messages intended only for response types can leave this empty.
        Note: RemoteErrorMessage is handled transparently and does not
        need to be specified here.
        """
        return []


@ioprepped
@dataclass
class RemoteErrorMessage(Message):
    """Message saying some error has occurred on the other end."""
    error_message: Annotated[str, IOAttrs('m')]
    error_type: Annotated[RemoteErrorType, IOAttrs('t')]


class MessageProtocol:
    """Wrangles a set of message types, formats, and response types.
    Both endpoints must be using a compatible Protocol for communication
    to succeed. To maintain Protocol compatibility between revisions,
    all message types must retain the same id, message attr storage names must
    not change, newly added attrs must have default values, etc.
    """

    def __init__(self,
                 message_types: Dict[int, Type[Message]],
                 type_key: Optional[str] = None,
                 preserve_clean_errors: bool = True,
                 remote_stack_traces: bool = False) -> None:
        """Create a protocol with a given configuration.
        Each entry for message_types should contain an ID, a message type,
        and all possible response types.

        If 'type_key' is provided, the message type ID is stored as the
        provided key in the message dict; otherwise it will be stored as
        part of a top level dict with the message payload appearing as a
        child dict. This is mainly for backwards compatibility.

        If 'preserve_clean_errors' is True, efro.error.CleanError errors
        on the remote end will result in the same error raised locally.
        All other Exception types come across as efro.error.RemoteError.

        If 'remote_stack_traces' is True, stringified remote stack traces will
        be included in the RemoteError. This should only be enabled in cases
        where the client is trusted.
        """
        self._message_types_by_id: Dict[int, Type[Message]] = {}
        self._message_ids_by_type: Dict[Type[Message], int] = {}
        for m_id, m_type in message_types.items():

            # Make sure only valid message types were passed and each
            # id was assigned only once.
            assert isinstance(m_id, int)
            assert (is_ioprepped_dataclass(m_type)
                    and issubclass(m_type, Message))
            assert self._message_types_by_id.get(m_id) is None

            self._message_types_by_id[m_id] = m_type
            self._message_ids_by_type[m_type] = m_id

        # Make sure all return types are valid and have been assigned
        # an ID as well.
        if __debug__:
            all_response_types: Set[Type[Message]] = set()
            for m_id, m_type in message_types.items():
                m_rtypes = m_type.get_response_types()
                assert isinstance(m_rtypes, list)
                assert len(set(m_rtypes)) == len(m_rtypes)  # check for dups
                all_response_types.update(m_rtypes)
            for cls in all_response_types:
                assert is_ioprepped_dataclass(cls) and issubclass(cls, Message)
                if cls not in self._message_ids_by_type:
                    raise ValueError(f'Possible response type {cls}'
                                     f' was not included in message_types.')

        self._type_key = type_key
        self._preserve_clean_errors = preserve_clean_errors
        self._remote_stack_traces = remote_stack_traces

    def message_encode(self, message: Message) -> bytes:
        """Encode a message to bytes for sending."""

        m_id = self._message_ids_by_type.get(type(message))
        if m_id is None:
            raise TypeError(f'Message type is not registered in Protocol:'
                            f' {type(message)}')
        msgdict = dataclass_to_dict(message)

        # Encode type as part of the message dict if desired
        # (for legacy compatibility).
        if self._type_key is not None:
            if self._type_key in msgdict:
                raise RuntimeError(f'Type-key {self._type_key}'
                                   f' found in msg of type {type(message)}')
            msgdict[self._type_key] = m_id
            out = msgdict
        else:
            out = {'m': msgdict, 't': m_id}
        return json.dumps(out, separators=(',', ':')).encode()

    def message_decode(self, data: bytes) -> Message:
        """Decode a message from bytes."""
        print(f'WOULD DECODE MSG FROM RAW: {str(data)}')
        return Message()

    def create_sender_module(self, classname: str) -> str:
        """"Create a Python module defining a MessageSender subclass.

        This class is primarily for type checking and will contain overrides
        for the varieties of send calls for message/response types defined
        in the protocol.
        """

    def create_receiver_module(self, classname: str) -> str:
        """"Create a Python module defining a MessageReceiver subclass.

        This class is primarily for type checking and will contain overrides
        for the register method for message/response types defined in
        the protocol.
        """

    def validate_message_type(self, msgtype: Type,
                              responsetypes: Sequence[Type]) -> None:
        """Ensure message type associated response types are valid.
        Raises an exception if not.
        """
        if msgtype not in self._message_ids_by_type:
            raise TypeError(f'Message type {msgtype} is not registered'
                            f' in this Protocol.')

        # Make sure the responses exactly matches what the message expects.
        assert len(set(responsetypes)) == len(responsetypes)

        for responsetype in responsetypes:
            if responsetype not in self._message_ids_by_type:
                raise TypeError(f'Response message type {responsetype} is'
                                f' not registered in this Protocol.')


class MessageSender:
    """Facilitates sending messages to a target and receiving responses.
    This is instantiated at the class level and used to register unbound
    class methods to handle raw message sending.

    Example:

    class MyClass:
        msg = MyMessageSender(some_protocol)

        @msg.send_raw_handler
        def send_raw_message(self, message: bytes) -> bytes:
            # Actually send the message here.

    # MyMessageSender class should provide overloads for send(), send_bg(),
    # etc. to ensure all sending happens with valid types.
    obj = MyClass()
    obj.msg.send(SomeMessageType())
    """

    def __init__(self, protocol: MessageProtocol) -> None:
        self._protocol = protocol
        self._send_raw_message_call: Optional[Callable[[Any, bytes],
                                                       bytes]] = None

    def send_raw_handler(
            self, call: Callable[[Any, bytes],
                                 bytes]) -> Callable[[Any, bytes], bytes]:
        """Function decorator for setting raw send method."""
        assert self._send_raw_message_call is None
        self._send_raw_message_call = call
        return call

    def send(self, bound_obj: Any, message: Message) -> Any:
        """Send a message and receive a response.
        Will encode the message for transport and call dispatch_raw_message()
        """
        if self._send_raw_message_call is None:
            raise RuntimeError('send() is unimplemented for this type.')
        encoded = self._protocol.message_encode(message)
        return self._send_raw_message_call(bound_obj, encoded)

    def send_bg(self, bound_obj: Any, message: Message) -> Message:
        """Send a message asynchronously and receive a future.
        The message will be encoded for transport and passed to
        dispatch_raw_message from a background thread.
        """
        raise RuntimeError('Unimplemented!')

    def send_async(self, bound_obj: Any, message: Message) -> Message:
        """Send a message asynchronously using asyncio.
        The message will be encoded for transport and passed to
        dispatch_raw_message_async.
        """
        raise RuntimeError('Unimplemented!')


class MessageReceiver:
    """Facilitates receiving & responding to messages from a remote source.
    This is instantiated at the class level with unbound methods registered
    as handlers for different message types in the protocol.

    Example:

    class MyClass:
        receiver = MyMessageReceiver()

        # MyMessageReceiver should provide overloads to register_handler()
        # to ensure all registered handlers have valid types/return-types.
        @receiver.handler
        def handle_some_message_type(self, message: SomeType) -> AnotherType:
            # Deal with this message type here.

    # This will trigger the registered handler being called.
    obj = MyClass()
    obj.receiver.handle_raw_message(some_raw_data)

    Any unhandled Exception occurring during message handling will result in
    an Exception being raised on the sending end.
    """

    def __init__(self, protocol: MessageProtocol) -> None:
        self._protocol = protocol

    # noinspection PyProtectedMember
    def register_handler(self, call: Callable) -> None:
        """Register a handler call.
        The message type handled by the call is determined by its
        type annotation.
        """
        # TODO: can use types.GenericAlias in 3.9.
        from typing import _GenericAlias  # type: ignore
        from typing import Union, get_type_hints, get_args

        # Return-type annotation can be a Union, but we probably don't
        # have it available at runtime. Explicitly pull it in.
        anns = get_type_hints(call, localns={'Union': Union})
        msg = anns.get('msg')
        if not isinstance(msg, type):
            raise TypeError(
                f'expected a type for "msg" annotation; got {type(msg)}.')
        ret = anns.get('return')
        rets: Tuple[Type, ...]

        # Return types can be a single type or a union of types.
        if isinstance(ret, _GenericAlias):
            targs = get_args(ret)
            if not all(isinstance(a, type) for a in targs):
                raise TypeError(f'expected only types for "return" annotation;'
                                f' got {targs}.')
            rets = targs

            print(f'LOOKED AT GENERIC ALIAS {targs}')
        else:
            if not isinstance(ret, type):
                raise TypeError(f'expected one or more types for'
                                f' "return" annotation; got a {type(ret)}.')
            rets = (ret, )

        print(f'WOULD REGISTER HANDLER! (got {msg} and {rets})')

    def handle_raw_message(self, msg: bytes) -> bytes:
        """Should be called when the receiver gets a message.
        The return value is the raw response to the message.
        """
        print('RECEIVER WOULD HANDLE RAW MESSAGE')
        del msg  # Unused
        return b''

    async def handle_raw_message_async(self, msg: bytes) -> bytes:
        """Should be called when the receiver gets a message.
        The return value is the raw response to the message.
        """
        raise RuntimeError('Unimplemented!')
