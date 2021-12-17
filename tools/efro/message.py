# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Annotated
from dataclasses import dataclass
from enum import Enum
import inspect
import logging
import json
import traceback

from efro.error import CleanError, RemoteError
from efro.dataclassio import (ioprepped, is_ioprepped_dataclass, IOAttrs,
                              dataclass_to_dict, dataclass_from_dict)

if TYPE_CHECKING:
    from typing import Any, Callable, Optional, Sequence, Union, Awaitable

TM = TypeVar('TM', bound='MessageSender')


class Message:
    """Base class for messages."""

    @classmethod
    def get_response_types(cls) -> list[type[Response]]:
        """Return all message types this Message can result in when sent.

        The default implementation specifies EmptyResponse, so messages with
        no particular response needs can leave this untouched.
        Note that ErrorMessage is handled as a special case and does not
        need to be specified here.
        """
        return [EmptyResponse]


class Response:
    """Base class for responses to messages."""


# Some standard response types:


class ErrorType(Enum):
    """Type of error that occurred in remote message handling."""
    OTHER = 0
    CLEAN = 1


@ioprepped
@dataclass
class ErrorResponse(Response):
    """Message saying some error has occurred on the other end.

    This type is unique in that it is not returned to the user; it
    instead results in a local exception being raised.
    """
    error_message: Annotated[str, IOAttrs('m')]
    error_type: Annotated[ErrorType, IOAttrs('e')] = ErrorType.OTHER


@ioprepped
@dataclass
class EmptyResponse(Response):
    """The response equivalent of None."""


# TODO: could allow handlers to deal in raw values for these
# types similar to how we allow None in place of EmptyResponse.
# Though not sure if they are widely used enough to warrant the
# extra code complexity.
@ioprepped
@dataclass
class BoolResponse(Response):
    """A simple bool value response."""

    value: Annotated[bool, IOAttrs('v')]


@ioprepped
@dataclass
class StringResponse(Response):
    """A simple string value response."""

    value: Annotated[str, IOAttrs('v')]


class MessageProtocol:
    """Wrangles a set of message types, formats, and response types.
    Both endpoints must be using a compatible Protocol for communication
    to succeed. To maintain Protocol compatibility between revisions,
    all message types must retain the same id, message attr storage names must
    not change, newly added attrs must have default values, etc.
    """

    def __init__(self,
                 message_types: dict[int, type[Message]],
                 response_types: dict[int, type[Response]],
                 type_key: Optional[str] = None,
                 preserve_clean_errors: bool = True,
                 log_remote_exceptions: bool = True,
                 trusted_sender: bool = False) -> None:
        """Create a protocol with a given configuration.

        Note that common response types are automatically registered
        with (unchanging negative ids) so they don't need to be passed
        explicitly (but can be if a different id is desired).

        If 'type_key' is provided, the message type ID is stored as the
        provided key in the message dict; otherwise it will be stored as
        part of a top level dict with the message payload appearing as a
        child dict. This is mainly for backwards compatibility.

        If 'preserve_clean_errors' is True, efro.error.CleanError errors
        on the remote end will result in the same error raised locally.
        All other Exception types come across as efro.error.RemoteError.

        If 'trusted_sender' is True, stringified remote stack traces will
        be included in the responses if errors occur.
        """
        # pylint: disable=too-many-locals
        self.message_types_by_id: dict[int, type[Message]] = {}
        self.message_ids_by_type: dict[type[Message], int] = {}
        self.response_types_by_id: dict[int, type[Response]] = {}
        self.response_ids_by_type: dict[type[Response], int] = {}
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

        for r_id, r_type in response_types.items():
            assert isinstance(r_id, int)
            assert r_id >= 0
            assert (is_ioprepped_dataclass(r_type)
                    and issubclass(r_type, Response))
            assert self.response_types_by_id.get(r_id) is None
            self.response_types_by_id[r_id] = r_type
            self.response_ids_by_type[r_type] = r_id

        # Go ahead and auto-register a few common response types
        # if the user has not done so explicitly. Use unique IDs which
        # will never change or overlap with user ids.
        def _reg_if_not(reg_tp: type[Response], reg_id: int) -> None:
            if reg_tp in self.response_ids_by_type:
                return
            assert self.response_types_by_id.get(reg_id) is None
            self.response_types_by_id[reg_id] = reg_tp
            self.response_ids_by_type[reg_tp] = reg_id

        _reg_if_not(ErrorResponse, -1)
        _reg_if_not(EmptyResponse, -2)
        # _reg_if_not(BoolResponse, -3)

        # Some extra-thorough validation in debug mode.
        if __debug__:
            # Make sure all Message types' return types are valid
            # and have been assigned an ID as well.
            all_response_types: set[type[Response]] = set()
            for m_id, m_type in message_types.items():
                m_rtypes = m_type.get_response_types()
                assert isinstance(m_rtypes, list)
                assert m_rtypes, (
                    f'Message type {m_type} specifies no return types.')
                assert len(set(m_rtypes)) == len(m_rtypes)  # check dups
                all_response_types.update(m_rtypes)
            for cls in all_response_types:
                assert is_ioprepped_dataclass(cls)
                assert issubclass(cls, Response)
                if cls not in self.response_ids_by_type:
                    raise ValueError(f'Possible response type {cls}'
                                     f' needs to be included in response_types'
                                     f' for this protocol.')

            # Make sure all registered types have unique base names.
            # We can take advantage of this to generate cleaner looking
            # protocol modules. Can revisit if this is ever a problem.
            mtypenames = set(tp.__name__ for tp in self.message_ids_by_type)
            if len(mtypenames) != len(message_types):
                raise ValueError(
                    'message_types contains duplicate __name__s;'
                    ' all types are required to have unique names.')

        self._type_key = type_key
        self.preserve_clean_errors = preserve_clean_errors
        self.log_remote_exceptions = log_remote_exceptions
        self.trusted_sender = trusted_sender

    def encode_message(self, message: Message) -> str:
        """Encode a message to a json string for transport."""
        return self._encode(message, self.message_ids_by_type, 'message')

    def encode_response(self, response: Response) -> str:
        """Encode a response to a json string for transport."""
        return self._encode(response, self.response_ids_by_type, 'response')

    def _encode(self, message: Any, ids_by_type: dict[type, int],
                opname: str) -> str:
        """Encode a message to a json string for transport."""

        m_id: Optional[int] = ids_by_type.get(type(message))
        if m_id is None:
            raise TypeError(f'{opname} type is not registered in protocol:'
                            f' {type(message)}')
        msgdict = dataclass_to_dict(message)

        # Encode type as part of the message/response dict if desired
        # (for legacy compatibility).
        if self._type_key is not None:
            if self._type_key in msgdict:
                raise RuntimeError(f'Type-key {self._type_key}'
                                   f' found in msg of type {type(message)}')
            msgdict[self._type_key] = m_id
            out = msgdict
        else:
            out = {'m': msgdict, 't': m_id}
        return json.dumps(out, separators=(',', ':'))

    def decode_message(self, data: str) -> Message:
        """Decode a message from a json string."""
        out = self._decode(data, self.message_types_by_id, 'message')
        assert isinstance(out, Message)
        return out

    def decode_response(self, data: str) -> Optional[Response]:
        """Decode a response from a json string."""
        out = self._decode(data, self.response_types_by_id, 'response')
        assert isinstance(out, (Response, type(None)))
        return out

    # Weeeird; we get mypy errors returning dict[int, type] but
    # dict[int, typing.Type] or dict[int, type[Any]] works..
    def _decode(self, data: str, types_by_id: dict[int, type[Any]],
                opname: str) -> Any:
        """Decode a message from a json string."""
        msgfull = json.loads(data)
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

        # Decode this particular type.
        msgtype = types_by_id.get(m_id)
        if msgtype is None:
            raise TypeError(f'Got unregistered {opname} type id of {m_id}.')
        out = dataclass_from_dict(msgtype, msgdict)

        # Special case: if we get EmptyResponse, we simply return None.
        if isinstance(out, EmptyResponse):
            return None

        # Special case: a remote error occurred. Raise a local Exception
        # instead of returning the message.
        if isinstance(out, ErrorResponse):
            assert opname == 'response'
            if (self.preserve_clean_errors
                    and out.error_type is ErrorType.CLEAN):
                raise CleanError(out.error_message)
            raise RemoteError(out.error_message)

        return out

    def _get_module_header(self, part: str) -> str:
        """Return common parts of generated modules."""
        # pylint: disable=too-many-locals, too-many-branches
        import textwrap
        tpimports: dict[str, list[str]] = {}
        imports: dict[str, list[str]] = {}

        single_message_type = len(self.message_ids_by_type) == 1

        # Always import messages
        for msgtype in list(self.message_ids_by_type) + [Message]:
            tpimports.setdefault(msgtype.__module__,
                                 []).append(msgtype.__name__)
        for rsp_tp in list(self.response_ids_by_type) + [Response]:
            # Skip these as they don't actually show up in code.
            if rsp_tp is EmptyResponse or rsp_tp is ErrorResponse:
                continue
            if (single_message_type and part == 'sender'
                    and rsp_tp is not Response):
                # We need to cast to the single supported response type
                # in this case so need response types at runtime.
                imports.setdefault(rsp_tp.__module__,
                                   []).append(rsp_tp.__name__)
            else:
                tpimports.setdefault(rsp_tp.__module__,
                                     []).append(rsp_tp.__name__)

        import_lines = ''
        tpimport_lines = ''

        for module, names in sorted(imports.items()):
            jnames = ', '.join(names)
            line = f'from {module} import {jnames}'
            if len(line) > 79:
                # Recreate in a wrapping-friendly form.
                line = f'from {module} import ({jnames})'
            import_lines += f'{line}\n'
        for module, names in sorted(tpimports.items()):
            jnames = ', '.join(names)
            line = f'from {module} import {jnames}'
            if len(line) > 75:  # Account for indent
                # Recreate in a wrapping-friendly form.
                line = f'from {module} import ({jnames})'
            tpimport_lines += f'{line}\n'

        if part == 'sender':
            import_lines += ('from efro.message import MessageSender,'
                             ' BoundMessageSender')
            tpimport_typing_extras = ''
        else:
            if single_message_type:
                import_lines += ('from efro.message import (MessageReceiver,'
                                 ' BoundMessageReceiver, Message, Response)')
            else:
                import_lines += ('from efro.message import MessageReceiver,'
                                 ' BoundMessageReceiver')
            tpimport_typing_extras = ', Awaitable'

        ovld = ', overload' if not single_message_type else ''
        tpimport_lines = textwrap.indent(tpimport_lines, '    ')
        out = ('# Released under the MIT License. See LICENSE for details.\n'
               f'#\n'
               f'"""Auto-generated {part} module. Do not edit by hand."""\n'
               f'\n'
               f'from __future__ import annotations\n'
               f'\n'
               f'from typing import TYPE_CHECKING{ovld}\n'
               f'\n'
               f'{import_lines}\n'
               f'\n'
               f'if TYPE_CHECKING:\n'
               f'    from typing import Union, Any, Optional, Callable'
               f'{tpimport_typing_extras}\n'
               f'{tpimport_lines}'
               f'\n'
               f'\n')
        return out

    def do_create_sender_module(self,
                                basename: str,
                                protocol_create_code: str,
                                enable_sync_sends: bool,
                                enable_async_sends: bool,
                                private: bool = False) -> str:
        """Used by create_sender_module(); do not call directly."""
        # pylint: disable=too-many-locals
        import textwrap

        msgtypes = list(self.message_ids_by_type.keys())

        ppre = '_' if private else ''
        out = self._get_module_header('sender')
        ccind = textwrap.indent(protocol_create_code, '        ')
        out += (f'class {ppre}{basename}(MessageSender):\n'
                f'    """Protocol-specific sender."""\n'
                f'\n'
                f'    def __init__(self) -> None:\n'
                f'{ccind}\n'
                f'        super().__init__(protocol)\n'
                f'\n'
                f'    def __get__(self,\n'
                f'                obj: Any,\n'
                f'                type_in: Any = None)'
                f' -> {ppre}Bound{basename}:\n'
                f'        return {ppre}Bound{basename}'
                f'(obj, self)\n'
                f'\n'
                f'\n'
                f'class {ppre}Bound{basename}(BoundMessageSender):\n'
                f'    """Protocol-specific bound sender."""\n')

        def _filt_tp_name(rtype: type[Response]) -> str:
            # We accept None to equal EmptyResponse so reflect that
            # in the type annotation.
            return 'None' if rtype is EmptyResponse else rtype.__name__

        # Define handler() overloads for all registered message types.
        if msgtypes:
            for async_pass in False, True:
                if async_pass and not enable_async_sends:
                    continue
                if not async_pass and not enable_sync_sends:
                    continue
                pfx = 'async ' if async_pass else ''
                sfx = '_async' if async_pass else ''
                awt = 'await ' if async_pass else ''
                how = 'asynchronously' if async_pass else 'synchronously'

                if len(msgtypes) == 1:
                    # Special case: with a single message types we don't
                    # use overloads.
                    msgtype = msgtypes[0]
                    msgtypevar = msgtype.__name__
                    rtypes = msgtype.get_response_types()
                    if len(rtypes) > 1:
                        tps = ', '.join(_filt_tp_name(t) for t in rtypes)
                        rtypevar = f'Union[{tps}]'
                    else:
                        rtypevar = _filt_tp_name(rtypes[0])
                    out += (f'\n'
                            f'    {pfx}def send{sfx}(self,'
                            f' message: {msgtypevar})'
                            f' -> {rtypevar}:\n'
                            f'        """Send a message {how}."""\n'
                            f'        out = {awt}self._sender.'
                            f'send{sfx}(self._obj, message)\n'
                            f'        assert isinstance(out, {rtypevar})\n'
                            f'        return out\n')
                else:

                    for msgtype in msgtypes:
                        msgtypevar = msgtype.__name__
                        rtypes = msgtype.get_response_types()
                        if len(rtypes) > 1:
                            tps = ', '.join(_filt_tp_name(t) for t in rtypes)
                            rtypevar = f'Union[{tps}]'
                        else:
                            rtypevar = _filt_tp_name(rtypes[0])
                        out += (f'\n'
                                f'    @overload\n'
                                f'    {pfx}def send{sfx}(self,'
                                f' message: {msgtypevar})'
                                f' -> {rtypevar}:\n'
                                f'        ...\n')
                    out += (f'\n'
                            f'    {pfx}def send{sfx}(self, message: Message)'
                            f' -> Optional[Response]:\n'
                            f'        """Send a message {how}."""\n'
                            f'        return {awt}self._sender.'
                            f'send{sfx}(self._obj, message)\n')

        return out

    def do_create_receiver_module(self,
                                  basename: str,
                                  protocol_create_code: str,
                                  is_async: bool,
                                  private: bool = False) -> str:
        """Used by create_receiver_module(); do not call directly."""
        # pylint: disable=too-many-locals
        import textwrap

        desc = 'asynchronous' if is_async else 'synchronous'
        ppre = '_' if private else ''
        msgtypes = list(self.message_ids_by_type.keys())
        out = self._get_module_header('receiver')
        ccind = textwrap.indent(protocol_create_code, '        ')
        out += (f'class {ppre}{basename}(MessageReceiver):\n'
                f'    """Protocol-specific {desc} receiver."""\n'
                f'\n'
                f'    is_async = {is_async}\n'
                f'\n'
                f'    def __init__(self) -> None:\n'
                f'{ccind}\n'
                f'        super().__init__(protocol)\n'
                f'\n'
                f'    def __get__(\n'
                f'        self,\n'
                f'        obj: Any,\n'
                f'        type_in: Any = None,\n'
                f'    ) -> {ppre}Bound{basename}:\n'
                f'        return {ppre}Bound{basename}('
                f'obj, self)\n')

        # Define handler() overloads for all registered message types.

        def _filt_tp_name(rtype: type[Response]) -> str:
            # We accept None to equal EmptyResponse so reflect that
            # in the type annotation.
            return 'None' if rtype is EmptyResponse else rtype.__name__

        if msgtypes:
            cbgn = 'Awaitable[' if is_async else ''
            cend = ']' if is_async else ''
            if len(msgtypes) == 1:
                # Special case: when we have a single message type we don't
                # use overloads.
                msgtype = msgtypes[0]
                msgtypevar = msgtype.__name__
                rtypes = msgtype.get_response_types()
                if len(rtypes) > 1:
                    tps = ', '.join(_filt_tp_name(t) for t in rtypes)
                    rtypevar = f'Union[{tps}]'
                else:
                    rtypevar = _filt_tp_name(rtypes[0])
                rtypevar = f'{cbgn}{rtypevar}{cend}'
                out += (
                    f'\n'
                    f'    def handler(\n'
                    f'        self,\n'
                    f'        call: Callable[[Any, {msgtypevar}], '
                    f'{rtypevar}],\n'
                    f'    )'
                    f' -> Callable[[Any, {msgtypevar}], {rtypevar}]:\n'
                    f'        """Decorator to register message handlers."""\n'
                    f'        from typing import cast, Callable, Any\n'
                    f'        self.register_handler(cast(Callable'
                    f'[[Any, Message], Response], call))\n'
                    f'        return call\n')
            else:
                for msgtype in msgtypes:
                    msgtypevar = msgtype.__name__
                    rtypes = msgtype.get_response_types()
                    if len(rtypes) > 1:
                        tps = ', '.join(_filt_tp_name(t) for t in rtypes)
                        rtypevar = f'Union[{tps}]'
                    else:
                        rtypevar = _filt_tp_name(rtypes[0])
                    rtypevar = f'{cbgn}{rtypevar}{cend}'
                    out += (f'\n'
                            f'    @overload\n'
                            f'    def handler(\n'
                            f'        self,\n'
                            f'        call: Callable[[Any, {msgtypevar}], '
                            f'{rtypevar}],\n'
                            f'    )'
                            f' -> Callable[[Any, {msgtypevar}], {rtypevar}]:\n'
                            f'        ...\n')
                out += (
                    '\n'
                    '    def handler(self, call: Callable) -> Callable:\n'
                    '        """Decorator to register message handlers."""\n'
                    '        self.register_handler(call)\n'
                    '        return call\n')

        out += (f'\n'
                f'\n'
                f'class {ppre}Bound{basename}(BoundMessageReceiver):\n'
                f'    """Protocol-specific bound receiver."""\n')
        if is_async:
            out += (
                '\n'
                '    async def handle_raw_message(self, message: str)'
                ' -> str:\n'
                '        """Asynchronously handle a raw incoming message."""\n'
                '        return await'
                ' self._receiver.handle_raw_message_async(\n'
                '            self._obj, message)\n')
        else:
            out += (
                '\n'
                '    def handle_raw_message(self, message: str) -> str:\n'
                '        """Synchronously handle a raw incoming message."""\n'
                '        return self._receiver.handle_raw_message'
                '(self._obj, message)\n')

        return out


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
        assert obj is not None
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
        return self._sender.send(self._obj, message)

    async def send_async_untyped(self, message: Message) -> Optional[Response]:
        """Send a message asynchronously.

        Whenever possible, use the send_async() call provided by generated
        subclasses instead of this; it will provide better type safety.
        """
        return await self._sender.send_async(self._obj, message)


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

    def validate(self, warn_only: bool = False) -> None:
        """Check for handler completeness, valid types, etc."""
        for msgtype in self.protocol.message_ids_by_type.keys():
            if issubclass(msgtype, Response):
                continue
            if msgtype not in self._handlers:
                msg = (f'Protocol message type {msgtype} is not handled'
                       f' by receiver type {type(self)}.')
                if warn_only:
                    logging.warning(msg)
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

        # Re-encode the response.
        assert isinstance(response, Response)
        # (user should never explicitly return these)
        assert not isinstance(response, ErrorResponse)
        assert type(response) in msgtype.get_response_types()
        return self.protocol.encode_response(response)

    def raw_response_for_error(self, exc: Exception) -> str:
        """Return a raw response for an error that occurred during handling."""
        if self.protocol.log_remote_exceptions:
            logging.exception('Error handling message.')

        # If anything goes wrong, return a ErrorResponse instead.
        if (isinstance(exc, CleanError)
                and self.protocol.preserve_clean_errors):
            err_response = ErrorResponse(error_message=str(exc),
                                         error_type=ErrorType.CLEAN)
        else:
            err_response = ErrorResponse(
                error_message=(traceback.format_exc()
                               if self.protocol.trusted_sender else
                               'An unknown error has occurred.'),
                error_type=ErrorType.OTHER)
        return self.protocol.encode_response(err_response)

    def handle_raw_message(self, bound_obj: Any, msg: str) -> str:
        """Decode, handle, and return an response for a message."""
        assert not self.is_async, "can't call sync handler on async receiver"
        try:
            msg_decoded, msgtype = self._decode_incoming_message(msg)
            handler = self._handlers.get(msgtype)
            if handler is None:
                raise RuntimeError(f'Got unhandled message type: {msgtype}.')
            result = handler(bound_obj, msg_decoded)
            return self._encode_response(result, msgtype)

        except Exception as exc:
            return self.raw_response_for_error(exc)

    async def handle_raw_message_async(self, bound_obj: Any, msg: str) -> str:
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
            return self.raw_response_for_error(exc)


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

    def raw_response_for_error(self, exc: Exception) -> str:
        """Return a raw response for an error that occurred during handling.

        This is automatically called from standard handle_raw_message_x()
        calls but can be manually invoked if errors occur outside of there.
        This gives clients a better idea of what went wrong vs simply
        returning invalid data which they might dismiss as a connection
        related error.
        """
        return self._receiver.raw_response_for_error(exc)


def create_sender_module(basename: str,
                         protocol_create_code: str,
                         enable_sync_sends: bool,
                         enable_async_sends: bool,
                         private: bool = False) -> str:
    """Create a Python module defining a MessageSender subclass.

    This class is primarily for type checking and will contain overrides
    for the varieties of send calls for message/response types defined
    in the protocol.

    Code passed for 'protocol_create_code' should import necessary
    modules and assign an instance of the Protocol to a 'protocol'
    variable.

    Class names are based on basename; a basename 'FooSender' will
    result in classes FooSender and BoundFooSender.

    If 'private' is True, class-names will be prefixed with an '_'.

    Note that line lengths are not clipped, so output may need to be
    run through a formatter to prevent lint warnings about excessive
    line lengths.
    """

    # Exec the passed code to get a protocol which we then use to
    # generate module code. The user could simply call
    # MessageProtocol.do_create_sender_module() directly, but this allows
    # us to verify that the create code works and yields the protocol used
    # to generate the code.
    protocol = _protocol_from_code(protocol_create_code)
    return protocol.do_create_sender_module(
        basename=basename,
        protocol_create_code=protocol_create_code,
        enable_sync_sends=enable_sync_sends,
        enable_async_sends=enable_async_sends,
        private=private)


def create_receiver_module(basename: str,
                           protocol_create_code: str,
                           is_async: bool,
                           private: bool = False) -> str:
    """"Create a Python module defining a MessageReceiver subclass.

    This class is primarily for type checking and will contain overrides
    for the register method for message/response types defined in
    the protocol.

    Class names are based on basename; a basename 'FooReceiver' will
    result in FooReceiver and BoundFooReceiver.

    If 'is_async' is True, handle_raw_message() will be an async method
    and the @handler decorator will expect async methods.

    If 'private' is True, class-names will be prefixed with an '_'.

    Note that line lengths are not clipped, so output may need to be
    run through a formatter to prevent lint warnings about excessive
    line lengths.
    """
    # Exec the passed code to get a protocol which we then use to
    # generate module code. The user could simply call
    # MessageProtocol.do_create_sender_module() directly, but this allows
    # us to verify that the create code works and yields the protocol used
    # to generate the code.
    protocol = _protocol_from_code(protocol_create_code)
    return protocol.do_create_receiver_module(
        basename=basename,
        protocol_create_code=protocol_create_code,
        is_async=is_async,
        private=private)


def _protocol_from_code(protocol_create_code: str) -> MessageProtocol:
    env: dict = {}
    exec(protocol_create_code, env)  # pylint: disable=exec-used
    protocol = env.get('protocol')
    if not isinstance(protocol, MessageProtocol):
        raise RuntimeError(
            f'protocol_create_code yielded'
            f' a {type(protocol)}; expected a MessageProtocol instance.')
    return protocol
