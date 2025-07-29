# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import traceback
import json

from efro.error import CleanError, CommunicationError
from efro.dataclassio import (
    is_ioprepped_dataclass,
    dataclass_to_dict,
    dataclass_from_dict,
)
from efro.message._message import (
    Message,
    Response,
    SysResponse,
    ErrorSysResponse,
    EmptySysResponse,
    UnregisteredMessageIDError,
)

if TYPE_CHECKING:
    from typing import Any, Literal


class MessageProtocol:
    """Wrangles a set of message types, formats, and response types.
    Both endpoints must be using a compatible Protocol for communication
    to succeed. To maintain Protocol compatibility between revisions,
    all message types must retain the same id, message attr storage
    names must not change, newly added attrs must have default values,
    etc.
    """

    def __init__(
        self,
        message_types: dict[int, type[Message]],
        response_types: dict[int, type[Response]],
        *,
        forward_communication_errors: bool = False,
        forward_clean_errors: bool = False,
        remote_errors_include_stack_traces: bool = False,
        log_errors_on_receiver: bool = True,
        log_response_decode_errors: bool = True,
    ) -> None:
        """Create a protocol with a given configuration.

        If 'forward_communication_errors' is True,
        efro.error.CommunicationErrors raised on the receiver end will
        result in a matching error raised back on the sender. This can
        be useful if the receiver will be in some way forwarding
        messages along and the sender doesn't need to know where
        communication breakdowns occurred; only that they did.

        If 'forward_clean_errors' is True, efro.error.CleanError
        exceptions raised on the receiver end will result in a matching
        CleanError raised back on the sender.

        When an exception is not covered by the optional forwarding
        mechanisms above, it will come across as efro.error.RemoteError
        and the exception will be logged on the receiver end - at least
        by default (see details below).

        If 'remote_errors_include_stack_traces' is True, stringified
        stack traces will be returned with efro.error.RemoteError
        exceptions. This is useful for debugging but should only be
        enabled in cases where the sender is trusted to see internal
        details of the receiver.

        By default, when a message-handling exception will result in an
        efro.error.RemoteError being returned to the sender, the
        exception will be logged on the receiver. This is because the
        goal is usually to avoid returning opaque RemoteErrors and to
        instead return something meaningful as part of the expected
        response type (even if that value itself represents a logical
        error state). If 'log_errors_on_receiver' is False, however,
        such exceptions will *not* be logged on the receiver. This can
        be useful in combination with
        'remote_errors_include_stack_traces' and 'forward_clean_errors'
        in situations where all error logging/management will be
        happening on the sender end. Be aware, however, that in that
        case it may be possible for communication errors to prevent some
        errors from ever being acknowledged.

        If an error occurs when decoding a message response, a
        RuntimeError is generated locally. However, in practice it is
        likely for such errors to be silently ignored by message
        handling code alongside more common communication type errors,
        meaning serious protocol breakage could go unnoticed. To avoid
        this, a log message is also printed in such cases. Pass
        'log_response_decode_errors' as False to disable this logging.
        """
        # pylint: disable=too-many-locals
        self.message_types_by_id: dict[int, type[Message]] = {}
        self.message_ids_by_type: dict[type[Message], int] = {}
        self.response_types_by_id: dict[
            int, type[Response] | type[SysResponse]
        ] = {}
        self.response_ids_by_type: dict[
            type[Response] | type[SysResponse], int
        ] = {}
        for m_id, m_type in message_types.items():
            # Make sure only valid message types were passed and each
            # id was assigned only once.
            assert isinstance(m_id, int)
            assert m_id >= 0
            assert is_ioprepped_dataclass(m_type) and issubclass(
                m_type, Message
            )
            assert self.message_types_by_id.get(m_id) is None
            self.message_types_by_id[m_id] = m_type
            self.message_ids_by_type[m_type] = m_id

        for r_id, r_type in response_types.items():
            assert isinstance(r_id, int)
            assert r_id >= 0
            assert is_ioprepped_dataclass(r_type) and issubclass(
                r_type, Response
            )
            assert self.response_types_by_id.get(r_id) is None
            self.response_types_by_id[r_id] = r_type
            self.response_ids_by_type[r_type] = r_id

        # Register our SysResponse types. These use negative
        # IDs so as to never overlap with user Response types.
        def _reg_sys(reg_tp: type[SysResponse], reg_id: int) -> None:
            assert self.response_types_by_id.get(reg_id) is None
            self.response_types_by_id[reg_id] = reg_tp
            self.response_ids_by_type[reg_tp] = reg_id

        _reg_sys(ErrorSysResponse, -1)
        _reg_sys(EmptySysResponse, -2)

        # Some extra-thorough validation in debug mode.
        if __debug__:
            # Make sure all Message types' return types are valid
            # and have been assigned an ID as well.
            all_response_types: set[type[Response] | None] = set()
            for m_id, m_type in message_types.items():
                m_rtypes = m_type.get_response_types()

                assert isinstance(m_rtypes, list)
                assert (
                    m_rtypes
                ), f'Message type {m_type} specifies no return types.'
                assert len(set(m_rtypes)) == len(m_rtypes)  # check dups
                for m_rtype in m_rtypes:
                    all_response_types.add(m_rtype)
            for cls in all_response_types:
                if cls is None:
                    continue
                assert is_ioprepped_dataclass(cls)
                assert issubclass(cls, Response)
                if cls not in self.response_ids_by_type:
                    raise ValueError(
                        f'Possible response type {cls} needs to be included'
                        f' in response_types for this protocol.'
                    )

            # Make sure all registered types have unique base names.
            # We can take advantage of this to generate cleaner looking
            # protocol modules. Can revisit if this is ever a problem.
            mtypenames = set(tp.__name__ for tp in self.message_ids_by_type)
            if len(mtypenames) != len(message_types):
                raise ValueError(
                    'message_types contains duplicate __name__s;'
                    ' all types are required to have unique names.'
                )

        self.forward_clean_errors = forward_clean_errors
        self.forward_communication_errors = forward_communication_errors
        self.remote_errors_include_stack_traces = (
            remote_errors_include_stack_traces
        )
        self.log_errors_on_receiver = log_errors_on_receiver
        self.log_response_decode_errors = log_response_decode_errors

    @staticmethod
    def encode_dict(obj: dict) -> str:
        """Json-encode a provided dict."""
        return json.dumps(obj, separators=(',', ':'))

    def message_to_dict(self, message: Message) -> dict:
        """Encode a message to a json ready dict."""
        return self._to_dict(message, self.message_ids_by_type, 'message')

    def response_to_dict(self, response: Response | SysResponse) -> dict:
        """Encode a response to a json ready dict."""
        return self._to_dict(response, self.response_ids_by_type, 'response')

    def error_to_response(self, exc: Exception) -> tuple[SysResponse, bool]:
        """Translate an Exception to a SysResponse.

        Also returns whether the error should be logged if this happened
        within handle_raw_message().
        """

        # If anything goes wrong, return a ErrorSysResponse instead
        # (either CLEAN or generic REMOTE).
        if self.forward_clean_errors and isinstance(exc, CleanError):
            return (
                ErrorSysResponse(
                    error_message=str(exc),
                    error_type=ErrorSysResponse.ErrorType.REMOTE_CLEAN,
                ),
                False,
            )
        if self.forward_communication_errors and isinstance(
            exc, CommunicationError
        ):
            return (
                ErrorSysResponse(
                    error_message=str(exc),
                    error_type=ErrorSysResponse.ErrorType.REMOTE_COMMUNICATION,
                ),
                False,
            )
        return (
            ErrorSysResponse(
                error_message=(
                    # Note: need to format exception ourself here; it
                    # might not be current so we can't use
                    # traceback.format_exc().
                    ''.join(
                        traceback.format_exception(
                            type(exc), exc, exc.__traceback__
                        )
                    )
                    if self.remote_errors_include_stack_traces
                    else 'An internal error has occurred.'
                ),
                error_type=ErrorSysResponse.ErrorType.REMOTE,
            ),
            self.log_errors_on_receiver,
        )

    def _to_dict(
        self, message: Any, ids_by_type: dict[type, int], opname: str
    ) -> dict:
        """Encode a message to a json string for transport."""

        m_id: int | None = ids_by_type.get(type(message))
        if m_id is None:
            raise TypeError(
                f'{opname} type is not registered in protocol:'
                f' {type(message)}'
            )
        out = {'t': m_id, 'm': dataclass_to_dict(message)}
        return out

    @staticmethod
    def decode_dict(data: str) -> dict:
        """Decode data to a dict."""
        out = json.loads(data)
        assert isinstance(out, dict)
        return out

    def message_from_dict(self, data: dict) -> Message:
        """Decode a message from a dict."""
        out = self._from_dict(data, self.message_types_by_id, 'message')
        assert isinstance(out, Message)
        return out

    def response_from_dict(self, data: dict) -> Response | SysResponse:
        """Decode a response from a json string."""
        out = self._from_dict(data, self.response_types_by_id, 'response')
        assert isinstance(out, Response | SysResponse)
        return out

    # Weeeird; we get mypy errors returning dict[int, type] but
    # dict[int, typing.Type] or dict[int, type[Any]] works..
    def _from_dict(
        self, data: dict, types_by_id: dict[int, type[Any]], opname: str
    ) -> Any:
        """Decode a message from a json string."""
        msgdict: dict | None

        m_id = data.get('t')
        # Allow omitting 'm' dict if its empty.
        msgdict = data.get('m', {})

        assert isinstance(m_id, int)
        assert isinstance(msgdict, dict)

        # Decode this particular type.
        msgtype = types_by_id.get(m_id)
        if msgtype is None:
            raise UnregisteredMessageIDError(
                f'Got unregistered {opname} id of {m_id}.'
            )

        # Explicitly allow any fallbacks we define for our enums and
        # multitypes. This allows us to build message types that remain
        # loadable even when containing unrecognized future
        # enums/multitype data. Be aware that this flags the object as
        # 'lossy' however which prevents it from being reserialized by
        # default.
        return dataclass_from_dict(msgtype, msgdict, lossy=True)

    def _get_module_header(
        self,
        part: Literal['sender', 'receiver'],
        extra_import_code: str | None,
        enable_async_sends: bool,
    ) -> str:
        """Return common parts of generated modules."""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        import textwrap

        tpimports: dict[str, list[str]] = {}
        imports: dict[str, list[str]] = {}

        single_message_type = len(self.message_ids_by_type) == 1

        msgtypes = list(self.message_ids_by_type)
        if part == 'sender':
            msgtypes.append(Message)
        for msgtype in msgtypes:
            tpimports.setdefault(msgtype.__module__, []).append(
                msgtype.__name__
            )
        rsptypes = list(self.response_ids_by_type)
        if part == 'sender':
            rsptypes.append(Response)
        for rsp_tp in rsptypes:
            # Skip these as they don't actually show up in code.
            if rsp_tp is EmptySysResponse or rsp_tp is ErrorSysResponse:
                continue
            if (
                single_message_type
                and part == 'sender'
                and rsp_tp is not Response
            ):
                # We need to cast to the single supported response type
                # in this case so need response types at runtime.
                imports.setdefault(rsp_tp.__module__, []).append(
                    rsp_tp.__name__
                )
            else:
                tpimports.setdefault(rsp_tp.__module__, []).append(
                    rsp_tp.__name__
                )

        import_lines = ''
        tpimport_lines = ''

        for module, names in sorted(imports.items()):
            jnames = ', '.join(names)
            line = f'from {module} import {jnames}'
            if len(line) > 80:
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
            import_lines += (
                'from efro.message import MessageSender, BoundMessageSender\n'
            )
            tpimport_typing_extras = ''
        else:
            if single_message_type:
                import_lines += (
                    'from efro.message import (MessageReceiver,'
                    ' BoundMessageReceiver, Message, Response)\n'
                )
            else:
                import_lines += (
                    'from efro.message import MessageReceiver,'
                    ' BoundMessageReceiver\n'
                )
            tpimport_typing_extras = ', Awaitable'

        if extra_import_code is not None:
            import_lines += extra_import_code

        ovld = ', overload' if not single_message_type else ''
        ovld2 = (
            ', cast, Awaitable'
            if (single_message_type and part == 'sender' and enable_async_sends)
            else ''
        )
        tpimport_lines = textwrap.indent(tpimport_lines, '    ')

        baseimps = ['Any']
        if part == 'receiver':
            baseimps.append('Callable')
        if part == 'sender' and enable_async_sends:
            baseimps.append('Awaitable')
        baseimps_s = ', '.join(baseimps)
        out = (
            '# Released under the MIT License. See LICENSE for details.\n'
            f'#\n'
            f'"""Auto-generated {part} module. Do not edit by hand."""\n'
            f'\n'
            f'from __future__ import annotations\n'
            f'\n'
            f'from typing import TYPE_CHECKING{ovld}{ovld2}\n'
            f'\n'
            f'{import_lines}'
            f'\n'
            f'if TYPE_CHECKING:\n'
            f'    from typing import {baseimps_s}'
            f'{tpimport_typing_extras}\n'
            f'{tpimport_lines}'
            f'\n'
            f'\n'
        )
        return out

    def do_create_sender_module(
        self,
        basename: str,
        protocol_create_code: str,
        enable_sync_sends: bool,
        enable_async_sends: bool,
        private: bool = False,
        protocol_module_level_import_code: str | None = None,
    ) -> str:
        """Used by create_sender_module(); do not call directly."""
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        import textwrap

        msgtypes = list(self.message_ids_by_type.keys())

        ppre = '_' if private else ''
        out = self._get_module_header(
            'sender',
            extra_import_code=protocol_module_level_import_code,
            enable_async_sends=enable_async_sends,
        )
        ccind = textwrap.indent(protocol_create_code, '        ')
        out += (
            f'class {ppre}{basename}(MessageSender):\n'
            f'    """Protocol-specific sender."""\n'
            f'\n'
            f'    def __init__(self) -> None:\n'
            f'{ccind}\n'
            f'        super().__init__(protocol)\n'
            f'\n'
            f'    def __get__(\n'
            f'        self, obj: Any, type_in: Any = None\n'
            f'    ) -> {ppre}Bound{basename}:\n'
            f'        return {ppre}Bound{basename}(obj, self)\n'
            f'\n'
            f'\n'
            f'class {ppre}Bound{basename}(BoundMessageSender):\n'
            f'    """Protocol-specific bound sender."""\n'
        )

        def _filt_tp_name(rtype: type[Response] | None) -> str:
            return 'None' if rtype is None else rtype.__name__

        # Define handler() overloads for all registered message types.
        if msgtypes:
            for async_pass in False, True:
                if async_pass and not enable_async_sends:
                    continue
                if not async_pass and not enable_sync_sends:
                    continue
                pfx = 'async ' if async_pass else ''
                sfx = '_async' if async_pass else ''
                # awt = 'await ' if async_pass else ''
                awt = ''
                how = 'asynchronously' if async_pass else 'synchronously'

                if len(msgtypes) == 1:
                    # Special case: with a single message types we don't
                    # use overloads.
                    msgtype = msgtypes[0]
                    msgtypevar = msgtype.__name__
                    rtypes = msgtype.get_response_types()
                    if len(rtypes) > 1:
                        rtypevar = ' | '.join(_filt_tp_name(t) for t in rtypes)
                    else:
                        rtypevar = _filt_tp_name(rtypes[0])
                    if async_pass:
                        rtypevar = f'Awaitable[{rtypevar}]'
                    out += (
                        f'\n'
                        f'    def send{sfx}(self,'
                        f' message: {msgtypevar})'
                        f' -> {rtypevar}:\n'
                        f'        """Send a message {how}."""\n'
                        f'        out = {awt}self._sender.'
                        f'send{sfx}(self._obj, message)\n'
                    )
                    if not async_pass:
                        out += (
                            f'        assert isinstance(out, {rtypevar})\n'
                            '        return out\n'
                        )
                    else:
                        out += f'        return cast({rtypevar}, out)\n'

                else:
                    for msgtype in msgtypes:
                        msgtypevar = msgtype.__name__
                        rtypes = msgtype.get_response_types()
                        if len(rtypes) > 1:
                            rtypevar = ' | '.join(
                                _filt_tp_name(t) for t in rtypes
                            )
                        else:
                            rtypevar = _filt_tp_name(rtypes[0])
                        out += (
                            f'\n'
                            f'    @overload\n'
                            f'    {pfx}def send{sfx}(self,'
                            f' message: {msgtypevar})'
                            f' -> {rtypevar}: ...\n'
                        )
                    rtypevar = 'Response | None'
                    if async_pass:
                        rtypevar = f'Awaitable[{rtypevar}]'
                    out += (
                        f'\n'
                        f'    def send{sfx}(self, message: Message)'
                        f' -> {rtypevar}:\n'
                        f'        """Send a message {how}."""\n'
                        f'        return {awt}self._sender.'
                        f'send{sfx}(self._obj, message)\n'
                    )

        return out

    def do_create_receiver_module(
        self,
        basename: str,
        protocol_create_code: str,
        is_async: bool,
        private: bool = False,
        protocol_module_level_import_code: str | None = None,
    ) -> str:
        """Used by create_receiver_module(); do not call directly."""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-positional-arguments
        import textwrap

        desc = 'asynchronous' if is_async else 'synchronous'
        ppre = '_' if private else ''
        msgtypes = list(self.message_ids_by_type.keys())
        out = self._get_module_header(
            'receiver',
            extra_import_code=protocol_module_level_import_code,
            enable_async_sends=False,
        )
        ccind = textwrap.indent(protocol_create_code, '        ')
        out += (
            f'class {ppre}{basename}(MessageReceiver):\n'
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
            f'obj, self)\n'
        )

        # Define handler() overloads for all registered message types.

        def _filt_tp_name(rtype: type[Response] | None) -> str:
            return 'None' if rtype is None else rtype.__name__

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
                    rtypevar = ' | '.join(_filt_tp_name(t) for t in rtypes)
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
                    f'\n'
                    f'        self.register_handler(cast(Callable'
                    f'[[Any, Message], Response], call))\n'
                    f'        return call\n'
                )
            else:
                for msgtype in msgtypes:
                    msgtypevar = msgtype.__name__
                    rtypes = msgtype.get_response_types()
                    if len(rtypes) > 1:
                        rtypevar = ' | '.join(_filt_tp_name(t) for t in rtypes)
                    else:
                        rtypevar = _filt_tp_name(rtypes[0])
                    rtypevar = f'{cbgn}{rtypevar}{cend}'
                    out += (
                        f'\n'
                        f'    @overload\n'
                        f'    def handler(\n'
                        f'        self,\n'
                        f'        call: Callable[[Any, {msgtypevar}], '
                        f'{rtypevar}],\n'
                        f'    )'
                        f' -> Callable[[Any, {msgtypevar}], {rtypevar}]: ...\n'
                    )
                out += (
                    '\n'
                    '    def handler(self, call: Callable) -> Callable:\n'
                    '        """Decorator to register message handlers."""\n'
                    '        self.register_handler(call)\n'
                    '        return call\n'
                )

        out += (
            f'\n'
            f'\n'
            f'class {ppre}Bound{basename}(BoundMessageReceiver):\n'
            f'    """Protocol-specific bound receiver."""\n'
        )
        if is_async:
            out += (
                '\n'
                '    def handle_raw_message(\n'
                '        self, message: str, raise_unregistered: bool = False\n'
                '    ) -> Awaitable[str]:\n'
                '        """Asynchronously handle a raw incoming message."""\n'
                '        return self._receiver.'
                'handle_raw_message_async(\n'
                '            self._obj, message, raise_unregistered\n'
                '        )\n'
            )

        else:
            out += (
                '\n'
                '    def handle_raw_message(\n'
                '        self, message: str, raise_unregistered: bool = False\n'
                '    ) -> str:\n'
                '        """Synchronously handle a raw incoming message."""\n'
                '        return self._receiver.handle_raw_message(\n'
                '            self._obj, message, raise_unregistered\n'
                '        )\n'
            )

        return out
