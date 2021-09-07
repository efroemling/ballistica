# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar
from dataclasses import dataclass
from enum import Enum
import inspect
import logging
import json
import traceback

from typing_extensions import Annotated

from efro.error import CleanError, RemoteError
from efro.dataclassio import (ioprepped, is_ioprepped_dataclass, IOAttrs,
                              dataclass_to_dict, dataclass_from_dict)

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
                 log_remote_exceptions: bool = True,
                 trusted_client: bool = False) -> None:
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

        If 'trusted_client' is True, stringified remote stack traces will
        be included in the RemoteError. This should only be enabled in cases
        where the client is trusted.
        """
        self.message_types_by_id: Dict[int, Type[Message]] = {}
        self.message_ids_by_type: Dict[Type[Message], int] = {}
        for m_id, m_type in message_types.items():

            # Make sure only valid message types were passed and each
            # id was assigned only once.
            assert isinstance(m_id, int)
            assert m_id >= 0
            assert (is_ioprepped_dataclass(m_type)
                    and issubclass(m_type, Message))
            assert self.message_types_by_id.get(m_id) is None

            self.message_types_by_id[m_id] = m_type
            self.message_ids_by_type[m_type] = m_id

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
                if cls not in self.message_ids_by_type:
                    raise ValueError(f'Possible response type {cls}'
                                     f' was not included in message_types.')

        self._type_key = type_key
        self.preserve_clean_errors = preserve_clean_errors
        self.log_remote_exceptions = log_remote_exceptions
        self.trusted_client = trusted_client

    def message_encode(self,
                       message: Message,
                       is_error: bool = False) -> bytes:
        """Encode a message to bytes for transport."""

        m_id: Optional[int]
        if is_error:
            m_id = -1
        else:
            m_id = self.message_ids_by_type.get(type(message))
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
        """Decode a message from bytes.

        If the message represents a remote error, an Exception will
        be raised.
        """
        msgfull = json.loads(data.decode())
        assert isinstance(msgfull, dict)
        msgdict: Optional[dict]
        if self._type_key is not None:
            m_id = msgfull.pop(self._type_key)
            msgdict = msgfull
            assert isinstance(m_id, int)
        else:
            m_id = msgfull.get('t')
            msgdict = msgfull.get('m')
        assert isinstance(m_id, int)
        assert isinstance(msgdict, dict)

        # Special case: a remote error occurred. Raise a local Exception.
        if m_id == -1:
            err = dataclass_from_dict(RemoteErrorMessage, msgdict)
            if (self.preserve_clean_errors
                    and err.error_type is RemoteErrorType.CLEAN):
                raise CleanError(err.error_message)
            raise RemoteError(err.error_message)

        # Decode this particular type and make sure its valid.
        msgtype = self.message_types_by_id.get(m_id)
        if msgtype is None:
            raise TypeError(f'Got unregistered message type id of {m_id}.')

        return dataclass_from_dict(msgtype, msgdict)

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

    def send(self, bound_obj: Any, message: Message) -> Message:
        """Send a message and receive a response.

        Will encode the message for transport and call dispatch_raw_message()
        """
        if self._send_raw_message_call is None:
            raise RuntimeError('send() is unimplemented for this type.')

        # Only types with possible response types should ever be sent.
        assert type(message).get_response_types()

        msg_encoded = self._protocol.message_encode(message)
        response_encoded = self._send_raw_message_call(bound_obj, msg_encoded)
        response = self._protocol.message_decode(response_encoded)
        assert isinstance(response, Message)
        assert type(response) in type(message).get_response_types()
        return response

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
        self._handlers: Dict[Type[Message], Callable] = {}

    # noinspection PyProtectedMember
    def register_handler(self, call: Callable[[Any, Message],
                                              Message]) -> None:
        """Register a handler call.

        The message type handled by the call is determined by its
        type annotation.
        """
        # TODO: can use types.GenericAlias in 3.9.
        from typing import _GenericAlias  # type: ignore
        from typing import Union, get_type_hints, get_args

        sig = inspect.getfullargspec(call)

        # The provided callable should be a method taking one 'msg' arg.
        expectedsig = ['self', 'msg']
        if sig.args != expectedsig:
            raise ValueError(f'Expected callable signature of {expectedsig};'
                             f' got {sig.args}')

        # Check annotation types to determine what message types we handle.
        # Return-type annotation can be a Union, but we probably don't
        # have it available at runtime. Explicitly pull it in.
        anns = get_type_hints(call, localns={'Union': Union})
        msgtype = anns.get('msg')
        if not isinstance(msgtype, type):
            raise TypeError(
                f'expected a type for "msg" annotation; got {type(msgtype)}.')
        assert issubclass(msgtype, Message)

        ret = anns.get('return')
        responsetypes: Tuple[Type, ...]

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

        # Make sure our protocol has this message type registered and our
        # return types exactly match. (Technically we could return a subset
        # of the supported types; can allow this in the future if it makes
        # sense).
        registered_types = self._protocol.message_ids_by_type.keys()

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

    def validate_handler_completeness(self, warn_only: bool = False) -> None:
        """Return whether this receiver handles all protocol messages.

        Only messages having possible response types are considered, as
        those are the only ones that can be sent to a receiver.
        """
        for msgtype in self._protocol.message_ids_by_type.keys():
            if not msgtype.get_response_types():
                continue
            if msgtype not in self._handlers:
                msg = (f'Protocol message {msgtype} not handled'
                       f' by receiver.')
                if warn_only:
                    logging.warning(msg)
                raise TypeError(msg)

    def handle_raw_message(self, bound_obj: Any, msg: bytes) -> bytes:
        """Decode, handle, and return encoded response for a message."""
        try:
            # Decode the incoming message.
            msg_decoded = self._protocol.message_decode(msg)
            msgtype = type(msg_decoded)

            # Call the proper handler.
            handler = self._handlers.get(msgtype)
            if handler is None:
                raise RuntimeError(f'Got unhandled message type: {msgtype}.')
            response = handler(bound_obj, msg_decoded)

            # Re-encode the response.
            assert isinstance(response, Message)
            assert type(response) in msgtype.get_response_types()
            return self._protocol.message_encode(response)

        except Exception as exc:

            if self._protocol.log_remote_exceptions:
                logging.exception('Error handling message.')

            # If anything goes wrong, return a RemoteErrorMessage instead.
            if (isinstance(exc, CleanError)
                    and self._protocol.preserve_clean_errors):
                response = RemoteErrorMessage(error_message=str(exc),
                                              error_type=RemoteErrorType.CLEAN)
            else:

                response = RemoteErrorMessage(
                    error_message=(traceback.format_exc()
                                   if self._protocol.trusted_client else
                                   'An unknown error has occurred.'),
                    error_type=RemoteErrorType.OTHER)
            return self._protocol.message_encode(response, is_error=True)

    async def handle_raw_message_async(self, msg: bytes) -> bytes:
        """Should be called when the receiver gets a message.

        The return value is the raw response to the message.
        """
        raise RuntimeError('Unimplemented!')
