# Released under the MIT License. See LICENSE for details.
#
"""Testing message functionality."""
# pylint: disable=too-many-lines

from __future__ import annotations

import os
import logging
import asyncio
from typing import TYPE_CHECKING, overload, assert_type
from dataclasses import dataclass

import pytest
from efro.error import CleanError, RemoteError, CommunicationError
from efro.dataclassio import ioprepped
from efro.message import (
    Message,
    Response,
    MessageProtocol,
    MessageSender,
    BoundMessageSender,
    MessageReceiver,
    BoundMessageReceiver,
    UnregisteredMessageIDError,
    EmptySysResponse,
)

if TYPE_CHECKING:
    from typing import Any, Callable, Awaitable

    from efro.message import SysResponse


@ioprepped
@dataclass
class _TMsg1(Message):
    """Just testing."""

    ival: int

    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [_TResp1]


@ioprepped
@dataclass
class _TMsg2(Message):
    """Just testing."""

    sval: str

    @classmethod
    def get_response_types(cls) -> list[type[Response] | None]:
        return [_TResp1, _TResp2]


@ioprepped
@dataclass
class _TMsg3(Message):
    """Just testing."""

    sval: str


@ioprepped
@dataclass
class _TMsg4(Message):
    """Just testing."""

    sval2: str


@ioprepped
@dataclass
class _TResp1(Response):
    """Just testing."""

    bval: bool


@ioprepped
@dataclass
class _TResp2(Response):
    """Just testing."""

    fval: float


@ioprepped
@dataclass
class _TResp3(Message):
    """Just testing."""

    fval: float


# Generated sender with a single message type:
# SEND_SINGLE_CODE_TEST_BEGIN


class _TestMessageSenderSingle(MessageSender):
    """Protocol-specific sender."""

    def __init__(self) -> None:
        protocol = TEST_PROTOCOL_SINGLE
        super().__init__(protocol)

    def __get__(
        self, obj: Any, type_in: Any = None
    ) -> _BoundTestMessageSenderSingle:
        return _BoundTestMessageSenderSingle(obj, self)


class _BoundTestMessageSenderSingle(BoundMessageSender):
    """Protocol-specific bound sender."""

    def send(self, message: _TMsg1) -> _TResp1:
        """Send a message synchronously."""
        out = self._sender.send(self._obj, message)
        assert isinstance(out, _TResp1)
        return out


# SEND_SINGLE_CODE_TEST_END

# Generated sender supporting both sync and async sending:
# SEND_SYNC_CODE_TEST_BEGIN


class _TestMessageSenderSync(MessageSender):
    """Protocol-specific sender."""

    def __init__(self) -> None:
        protocol = TEST_PROTOCOL
        super().__init__(protocol)

    def __get__(
        self, obj: Any, type_in: Any = None
    ) -> _BoundTestMessageSenderSync:
        return _BoundTestMessageSenderSync(obj, self)


class _BoundTestMessageSenderSync(BoundMessageSender):
    """Protocol-specific bound sender."""

    @overload
    def send(self, message: _TMsg1) -> _TResp1:
        ...

    @overload
    def send(self, message: _TMsg2) -> _TResp1 | _TResp2:
        ...

    @overload
    def send(self, message: _TMsg3) -> None:
        ...

    def send(self, message: Message) -> Response | None:
        """Send a message synchronously."""
        return self._sender.send(self._obj, message)


# SEND_SYNC_CODE_TEST_END

# Generated sender supporting only async sending:
# SEND_ASYNC_CODE_TEST_BEGIN


class _TestMessageSenderAsync(MessageSender):
    """Protocol-specific sender."""

    def __init__(self) -> None:
        protocol = TEST_PROTOCOL
        super().__init__(protocol)

    def __get__(
        self, obj: Any, type_in: Any = None
    ) -> _BoundTestMessageSenderAsync:
        return _BoundTestMessageSenderAsync(obj, self)


class _BoundTestMessageSenderAsync(BoundMessageSender):
    """Protocol-specific bound sender."""

    @overload
    async def send_async(self, message: _TMsg1) -> _TResp1:
        ...

    @overload
    async def send_async(self, message: _TMsg2) -> _TResp1 | _TResp2:
        ...

    @overload
    async def send_async(self, message: _TMsg3) -> None:
        ...

    def send_async(self, message: Message) -> Awaitable[Response | None]:
        """Send a message asynchronously."""
        return self._sender.send_async(self._obj, message)


# SEND_ASYNC_CODE_TEST_END

# Generated sender supporting both sync and async sending:
# SEND_BOTH_CODE_TEST_BEGIN


class _TestMessageSenderBBoth(MessageSender):
    """Protocol-specific sender."""

    def __init__(self) -> None:
        protocol = TEST_PROTOCOL_EVOLVED
        super().__init__(protocol)

    def __get__(
        self, obj: Any, type_in: Any = None
    ) -> _BoundTestMessageSenderBBoth:
        return _BoundTestMessageSenderBBoth(obj, self)


class _BoundTestMessageSenderBBoth(BoundMessageSender):
    """Protocol-specific bound sender."""

    @overload
    def send(self, message: _TMsg1) -> _TResp1:
        ...

    @overload
    def send(self, message: _TMsg2) -> _TResp1 | _TResp2:
        ...

    @overload
    def send(self, message: _TMsg3) -> None:
        ...

    @overload
    def send(self, message: _TMsg4) -> None:
        ...

    def send(self, message: Message) -> Response | None:
        """Send a message synchronously."""
        return self._sender.send(self._obj, message)

    @overload
    async def send_async(self, message: _TMsg1) -> _TResp1:
        ...

    @overload
    async def send_async(self, message: _TMsg2) -> _TResp1 | _TResp2:
        ...

    @overload
    async def send_async(self, message: _TMsg3) -> None:
        ...

    @overload
    async def send_async(self, message: _TMsg4) -> None:
        ...

    def send_async(self, message: Message) -> Awaitable[Response | None]:
        """Send a message asynchronously."""
        return self._sender.send_async(self._obj, message)


# SEND_BOTH_CODE_TEST_END

# Generated receiver with a single message type:
# RCV_SINGLE_CODE_TEST_BEGIN


class _TestSingleMessageReceiver(MessageReceiver):
    """Protocol-specific synchronous receiver."""

    is_async = False

    def __init__(self) -> None:
        protocol = TEST_PROTOCOL_SINGLE
        super().__init__(protocol)

    def __get__(
        self,
        obj: Any,
        type_in: Any = None,
    ) -> _BoundTestSingleMessageReceiver:
        return _BoundTestSingleMessageReceiver(obj, self)

    def handler(
        self,
        call: Callable[[Any, _TMsg1], _TResp1],
    ) -> Callable[[Any, _TMsg1], _TResp1]:
        """Decorator to register message handlers."""
        from typing import cast, Callable, Any

        self.register_handler(cast(Callable[[Any, Message], Response], call))
        return call


class _BoundTestSingleMessageReceiver(BoundMessageReceiver):
    """Protocol-specific bound receiver."""

    def handle_raw_message(
        self, message: str, raise_unregistered: bool = False
    ) -> str:
        """Synchronously handle a raw incoming message."""
        return self._receiver.handle_raw_message(
            self._obj, message, raise_unregistered
        )


# RCV_SINGLE_CODE_TEST_END

# Generated receiver supporting sync handling:
# RCV_SYNC_CODE_TEST_BEGIN


class _TestSyncMessageReceiver(MessageReceiver):
    """Protocol-specific synchronous receiver."""

    is_async = False

    def __init__(self) -> None:
        protocol = TEST_PROTOCOL
        super().__init__(protocol)

    def __get__(
        self,
        obj: Any,
        type_in: Any = None,
    ) -> _BoundTestSyncMessageReceiver:
        return _BoundTestSyncMessageReceiver(obj, self)

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMsg1], _TResp1],
    ) -> Callable[[Any, _TMsg1], _TResp1]:
        ...

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMsg2], _TResp1 | _TResp2],
    ) -> Callable[[Any, _TMsg2], _TResp1 | _TResp2]:
        ...

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMsg3], None],
    ) -> Callable[[Any, _TMsg3], None]:
        ...

    def handler(self, call: Callable) -> Callable:
        """Decorator to register message handlers."""
        self.register_handler(call)
        return call


class _BoundTestSyncMessageReceiver(BoundMessageReceiver):
    """Protocol-specific bound receiver."""

    def handle_raw_message(
        self, message: str, raise_unregistered: bool = False
    ) -> str:
        """Synchronously handle a raw incoming message."""
        return self._receiver.handle_raw_message(
            self._obj, message, raise_unregistered
        )


# RCV_SYNC_CODE_TEST_END

# Generated receiver supporting async handling:
# RCV_ASYNC_CODE_TEST_BEGIN


class _TestAsyncMessageReceiver(MessageReceiver):
    """Protocol-specific asynchronous receiver."""

    is_async = True

    def __init__(self) -> None:
        protocol = TEST_PROTOCOL
        super().__init__(protocol)

    def __get__(
        self,
        obj: Any,
        type_in: Any = None,
    ) -> _BoundTestAsyncMessageReceiver:
        return _BoundTestAsyncMessageReceiver(obj, self)

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMsg1], Awaitable[_TResp1]],
    ) -> Callable[[Any, _TMsg1], Awaitable[_TResp1]]:
        ...

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMsg2], Awaitable[_TResp1 | _TResp2]],
    ) -> Callable[[Any, _TMsg2], Awaitable[_TResp1 | _TResp2]]:
        ...

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMsg3], Awaitable[None]],
    ) -> Callable[[Any, _TMsg3], Awaitable[None]]:
        ...

    def handler(self, call: Callable) -> Callable:
        """Decorator to register message handlers."""
        self.register_handler(call)
        return call


class _BoundTestAsyncMessageReceiver(BoundMessageReceiver):
    """Protocol-specific bound receiver."""

    def handle_raw_message(
        self, message: str, raise_unregistered: bool = False
    ) -> Awaitable[str]:
        """Asynchronously handle a raw incoming message."""
        return self._receiver.handle_raw_message_async(
            self._obj, message, raise_unregistered
        )


# RCV_ASYNC_CODE_TEST_END

TEST_PROTOCOL = MessageProtocol(
    message_types={
        0: _TMsg1,
        1: _TMsg2,
        2: _TMsg3,
    },
    response_types={
        0: _TResp1,
        1: _TResp2,
    },
    forward_clean_errors=True,
    forward_communication_errors=True,
    remote_errors_include_stack_traces=True,
)

# Represents an 'evolved' TEST_PROTOCOL (the same as TEST_PROTOCOL; just
# one extra message type added).
# This way we can test communication failures talking to older protocols.
TEST_PROTOCOL_EVOLVED = MessageProtocol(
    message_types={
        0: _TMsg1,
        1: _TMsg2,
        2: _TMsg3,
        3: _TMsg4,
    },
    response_types={
        0: _TResp1,
        1: _TResp2,
    },
    forward_clean_errors=True,
    forward_communication_errors=True,
    remote_errors_include_stack_traces=True,
)

TEST_PROTOCOL_SINGLE = MessageProtocol(
    message_types={
        0: _TMsg1,
    },
    response_types={
        0: _TResp1,
    },
    remote_errors_include_stack_traces=True,
)


def test_protocol_creation() -> None:
    """Test protocol creation."""

    # This should fail because _TMsg1 can return _TResp1 which
    # is not given an id here.
    with pytest.raises(ValueError):
        _protocol = MessageProtocol(
            message_types={0: _TMsg1},
            response_types={0: _TResp2},
        )

    # Now it should work.
    _protocol = MessageProtocol(
        message_types={0: _TMsg1},
        response_types={0: _TResp1},
    )


def test_sender_module_single_emb() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    # NOTE: Ideally we should be testing efro.message.create_sender_module()
    # here, but it requires us to pass code which imports this test module
    # to get at the protocol, and that currently fails in our static mypy
    # tests.
    smod = TEST_PROTOCOL_SINGLE.do_create_sender_module(
        'TestMessageSenderSingle',
        protocol_create_code='protocol = TEST_PROTOCOL_SINGLE',
        enable_sync_sends=True,
        enable_async_sends=False,
        private=True,
    )

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestMessageSenderSingle(MessageSender):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (
        f'# SEND_SINGLE_CODE_TEST_BEGIN'
        f'\n\n\n{clipped}\n\n\n# SEND_SINGLE_CODE_TEST_END\n'
    )
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated sender module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.'
        )


def test_sender_module_sync_emb() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    # NOTE: Ideally we should be testing efro.message.create_sender_module()
    # here, but it requires us to pass code which imports this test module
    # to get at the protocol, and that currently fails in our static mypy
    # tests.
    smod = TEST_PROTOCOL.do_create_sender_module(
        'TestMessageSenderSync',
        protocol_create_code='protocol = TEST_PROTOCOL',
        enable_sync_sends=True,
        enable_async_sends=False,
        private=True,
    )

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestMessageSenderSync(MessageSender):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (
        f'# SEND_SYNC_CODE_TEST_BEGIN'
        f'\n\n\n{clipped}\n\n\n# SEND_SYNC_CODE_TEST_END\n'
    )
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated sender module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.'
        )


def test_sender_module_async_emb() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    # NOTE: Ideally we should be testing efro.message.create_sender_module()
    # here, but it requires us to pass code which imports this test module
    # to get at the protocol, and that currently fails in our static mypy
    # tests.
    smod = TEST_PROTOCOL.do_create_sender_module(
        'TestMessageSenderAsync',
        protocol_create_code='protocol = TEST_PROTOCOL',
        enable_sync_sends=False,
        enable_async_sends=True,
        private=True,
    )

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestMessageSenderAsync(MessageSender):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (
        f'# SEND_ASYNC_CODE_TEST_BEGIN'
        f'\n\n\n{clipped}\n\n\n# SEND_ASYNC_CODE_TEST_END\n'
    )
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated sender module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.'
        )


def test_sender_module_both_emb() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    # NOTE: Ideally we should be testing efro.message.create_sender_module()
    # here, but it requires us to pass code which imports this test module
    # to get at the protocol, and that currently fails in our static mypy
    # tests.
    smod = TEST_PROTOCOL_EVOLVED.do_create_sender_module(
        'TestMessageSenderBBoth',
        protocol_create_code='protocol = TEST_PROTOCOL_EVOLVED',
        enable_sync_sends=True,
        enable_async_sends=True,
        private=True,
    )

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestMessageSenderBBoth(MessageSender):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (
        f'# SEND_BOTH_CODE_TEST_BEGIN'
        f'\n\n\n{clipped}\n\n\n# SEND_BOTH_CODE_TEST_END\n'
    )
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated sender module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.'
        )


def test_receiver_module_single_emb() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    # NOTE: Ideally we should be testing efro.message.create_receiver_module()
    # here, but it requires us to pass code which imports this test module
    # to get at the protocol, and that currently fails in our static mypy
    # tests.
    smod = TEST_PROTOCOL_SINGLE.do_create_receiver_module(
        'TestSingleMessageReceiver',
        'protocol = TEST_PROTOCOL_SINGLE',
        is_async=False,
        private=True,
    )

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index(
        'class _TestSingleMessageReceiver(MessageReceiver):'
    )
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (
        f'# RCV_SINGLE_CODE_TEST_BEGIN'
        f'\n\n\n{clipped}\n\n\n# RCV_SINGLE_CODE_TEST_END\n'
    )
    if emb not in ourcode:
        print(f'EXPECTED SINGLE RECEIVER EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated single receiver module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.'
        )


def test_receiver_module_sync_emb() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    # NOTE: Ideally we should be testing efro.message.create_receiver_module()
    # here, but it requires us to pass code which imports this test module
    # to get at the protocol, and that currently fails in our static mypy
    # tests.
    smod = TEST_PROTOCOL.do_create_receiver_module(
        'TestSyncMessageReceiver',
        'protocol = TEST_PROTOCOL',
        is_async=False,
        private=True,
    )

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestSyncMessageReceiver(MessageReceiver):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (
        f'# RCV_SYNC_CODE_TEST_BEGIN'
        f'\n\n\n{clipped}\n\n\n# RCV_SYNC_CODE_TEST_END\n'
    )
    if emb not in ourcode:
        print(f'EXPECTED SYNC RECEIVER EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated sync receiver module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.'
        )


def test_receiver_module_async_emb() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    # NOTE: Ideally we should be testing efro.message.create_receiver_module()
    # here, but it requires us to pass code which imports this test module
    # to get at the protocol, and that currently fails in our static mypy
    # tests.
    smod = TEST_PROTOCOL.do_create_receiver_module(
        'TestAsyncMessageReceiver',
        'protocol = TEST_PROTOCOL',
        is_async=True,
        private=True,
    )

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestAsyncMessageReceiver(MessageReceiver):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (
        f'# RCV_ASYNC_CODE_TEST_BEGIN'
        f'\n\n\n{clipped}\n\n\n# RCV_ASYNC_CODE_TEST_END\n'
    )
    if emb not in ourcode:
        print(f'EXPECTED ASYNC RECEIVER EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated async receiver module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.'
        )


def test_receiver_creation() -> None:
    """Test setting up receivers with handlers/etc."""

    # This should fail due to the registered handler only specifying
    # one response message type while the message type itself
    # specifies two.
    with pytest.raises(TypeError):

        class _TestClassR:
            """Test class incorporating receive functionality."""

            receiver = _TestSyncMessageReceiver()

            @receiver.handler
            def handle_test_message_2(self, msg: _TMsg2) -> _TResp2:
                """Test."""
                del msg  # Unused
                return _TResp2(fval=1.2)

    # Validation should  fail because not all message types in the
    # protocol are handled.
    with pytest.raises(TypeError):

        class _TestClassR2:
            """Test class incorporating receive functionality."""

            receiver = _TestSyncMessageReceiver()

            # Checks that we've added handlers for all message types, etc.
            receiver.validate()


def test_full_pipeline(caplog: pytest.LogCaptureFixture) -> None:
    """Test the full pipeline."""

    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    # Define a class that can send messages and one that can receive them.
    class TestClassS:
        """Test class incorporating send functionality."""

        msg = _TestMessageSenderBBoth()

        test_handling_unregistered = False
        test_send_method_exceptions = False
        test_send_method_exceptions_comm = False

        def __init__(self, target: TestClassRSync | TestClassRAsync) -> None:
            self.test_sidecar = False
            self._target = target

        @msg.send_method
        def _send_raw_message(self, data: str) -> str:
            """Handle synchronous sending of raw json message data."""

            # Test throwing exceptions in send methods.
            if self.test_send_method_exceptions:
                raise (
                    CommunicationError()
                    if self.test_send_method_exceptions_comm
                    else RuntimeError()
                )

            # Just talk directly to the receiver for this example.
            # (currently only support synchronous receivers)
            assert isinstance(self._target, TestClassRSync)
            try:
                return self._target.receiver.handle_raw_message(
                    data, raise_unregistered=self.test_handling_unregistered
                )
            except UnregisteredMessageIDError:
                if self.test_handling_unregistered:
                    # Emulate forwarding unregistered messages on to some
                    # other handler...
                    response_dict = self.msg.protocol.response_to_dict(
                        EmptySysResponse()
                    )
                    return self.msg.protocol.encode_dict(response_dict)
                raise

        @msg.send_async_method
        async def _send_raw_message_async(self, data: str) -> str:
            """Handle asynchronous sending of raw json message data."""

            # Test throwing exceptions in async send methods.
            if self.test_send_method_exceptions:
                raise (
                    CommunicationError()
                    if self.test_send_method_exceptions_comm
                    else RuntimeError()
                )

            # Just talk directly to the receiver for this example.
            # (we can do sync or async receivers)
            if isinstance(self._target, TestClassRSync):
                return self._target.receiver.handle_raw_message(data)
            return await self._target.receiver.handle_raw_message(data)

        @msg.encode_filter_method
        def _encode_filter(self, msg: Message, outdict: dict) -> None:
            """Filter our outgoing messages."""
            if self.test_sidecar:
                outdict['_sidecar_data'] = getattr(msg, '_sidecar_data')

        @msg.decode_filter_method
        def _decode_filter(
            self,
            message: Message,
            indata: dict,
            response: Response | SysResponse,
        ) -> None:
            """Filter our incoming responses."""
            del message  # Unused.
            if self.test_sidecar:
                setattr(response, '_sidecar_data', indata['_sidecar_data'])

    # Alternate sender for testing other protocol options.
    class TestClassSAlt:
        """Test class incorporating send functionality."""

        msg = _TestMessageSenderSingle()

        test_handling_unregistered = False
        test_send_method_exceptions = False
        test_send_method_exceptions_comm = False

        def __init__(self, target: TestClassRAlt) -> None:
            self.test_sidecar = False
            self._target = target

        @msg.send_method
        def _send_raw_message(self, data: str) -> str:
            """Handle synchronous sending of raw json message data."""

            # Test throwing exceptions in send methods.
            if self.test_send_method_exceptions:
                raise (
                    CommunicationError()
                    if self.test_send_method_exceptions_comm
                    else RuntimeError()
                )

            # Just talk directly to the receiver for this example.
            # (currently only support synchronous receivers)
            assert isinstance(self._target, TestClassRAlt)
            try:
                return self._target.receiver.handle_raw_message(
                    data, raise_unregistered=self.test_handling_unregistered
                )
            except UnregisteredMessageIDError:
                if self.test_handling_unregistered:
                    # Emulate forwarding unregistered messages on to some
                    # other handler...
                    response_dict = self.msg.protocol.response_to_dict(
                        EmptySysResponse()
                    )
                    return self.msg.protocol.encode_dict(response_dict)
                raise

    class TestClassRSync:
        """Test class incorporating synchronous receive functionality."""

        receiver = _TestSyncMessageReceiver()

        def __init__(self) -> None:
            self.test_sidecar = False

        @receiver.handler
        def handle_test_message_1(self, msg: _TMsg1) -> _TResp1:
            """Test."""
            if msg.ival == 1:
                raise CleanError('Testing Clean Error')
            if msg.ival == 2:
                raise RuntimeError('Testing Runtime Error')
            if msg.ival == 3:
                raise CommunicationError('Testing Communication Error')
            out = _TResp1(bval=True)
            if self.test_sidecar:
                setattr(out, '_sidecar_data', getattr(msg, '_sidecar_data'))
            return out

        @receiver.handler
        def handle_test_message_2(self, msg: _TMsg2) -> _TResp1 | _TResp2:
            """Test."""
            del msg  # Unused
            return _TResp2(fval=1.2)

        @receiver.handler
        def handle_test_message_3(self, msg: _TMsg3) -> None:
            """Test."""
            del msg  # Unused

        @receiver.decode_filter_method
        def _decode_filter(self, indata: dict, message: Message) -> None:
            """Filter our incoming messages."""
            if self.test_sidecar:
                setattr(message, '_sidecar_data', indata['_sidecar_data'])

        @receiver.encode_filter_method
        def _encode_filter(
            self,
            message: Message | None,
            response: Response | SysResponse,
            outdict: dict,
        ) -> None:
            """Filter our outgoing responses."""
            del message  # Unused.
            if self.test_sidecar:
                outdict['_sidecar_data'] = getattr(response, '_sidecar_data')

        receiver.validate()

    class TestClassRAlt:
        """Test class incorporating synchronous receive functionality."""

        receiver = _TestSingleMessageReceiver()

        def __init__(self) -> None:
            self.test_sidecar = False

        @receiver.handler
        def handle_test_message_1(self, msg: _TMsg1) -> _TResp1:
            """Test."""
            if msg.ival == 1:
                raise CleanError('Testing Clean Error')
            if msg.ival == 2:
                raise RuntimeError('Testing Runtime Error')
            if msg.ival == 3:
                raise CommunicationError('Testing Communication Error')
            out = _TResp1(bval=True)
            if self.test_sidecar:
                setattr(out, '_sidecar_data', getattr(msg, '_sidecar_data'))
            return out

        receiver.validate()

    class TestClassRAsync:
        """Test class incorporating asynchronous receive functionality."""

        receiver = _TestAsyncMessageReceiver()

        @receiver.handler
        async def handle_test_message_1(self, msg: _TMsg1) -> _TResp1:
            """Test."""
            if msg.ival == 1:
                raise CleanError('Testing Clean Error')
            if msg.ival == 2:
                raise RuntimeError('Testing Runtime Error')
            if msg.ival == 3:
                raise CommunicationError('Testing Communication Error')
            return _TResp1(bval=True)

        @receiver.handler
        async def handle_test_message_2(self, msg: _TMsg2) -> _TResp1 | _TResp2:
            """Test."""
            del msg  # Unused
            return _TResp2(fval=1.2)

        @receiver.handler
        async def handle_test_message_3(self, msg: _TMsg3) -> None:
            """Test."""
            del msg  # Unused

        receiver.validate()

    obj_r_sync = TestClassRSync()
    obj_r_async = TestClassRAsync()
    obj = TestClassS(target=obj_r_sync)
    obj2 = TestClassS(target=obj_r_async)

    obj_rb = TestClassRAlt()
    objb = TestClassSAlt(target=obj_rb)

    # Test sends (of sync and async varieties).
    response1 = obj.msg.send(_TMsg1(ival=0))
    assert_type(response1, _TResp1)
    assert isinstance(response1, _TResp1)

    response1b = objb.msg.send(_TMsg1(ival=0))
    assert_type(response1b, _TResp1)

    response2 = obj.msg.send(_TMsg2(sval='rah'))
    assert isinstance(response2, (_TResp1, _TResp2))

    response3 = obj.msg.send(_TMsg3(sval='rah'))
    assert_type(response3, None)
    assert response3 is None

    response4 = asyncio.run(obj.msg.send_async(_TMsg1(ival=0)))
    assert isinstance(response4, _TResp1)

    # Nothing up to this point should have logged any errors.
    # (note that warnings may happen since asyncio can complain about timing)
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)

    # Remote CleanErrors should come across locally as the same and
    # no errors should be logged.
    # (since our protocol has forward_clean_errors enabled).
    caplog.clear()
    try:
        _response5 = obj.msg.send(_TMsg1(ival=1))
    except Exception as exc:
        assert isinstance(exc, CleanError)
        assert str(exc) == 'Testing Clean Error'
    assert not caplog.records

    # Same using a protocol *without* forward_clean_errors should
    # give us a generic RemoteError and log the error.
    caplog.clear()
    with pytest.raises(RemoteError):
        _response5 = objb.msg.send(_TMsg1(ival=1))
    assert (
        len(caplog.records) == 1 and caplog.records[0].levelno == logging.ERROR
    )

    # Same with CommunicationErrors occurring on the peer; they should
    # come back to us intact if forward_communication_errors is enabled
    # and no errors should have been logged.
    caplog.clear()
    try:
        _response5 = obj.msg.send(_TMsg1(ival=3))
    except Exception as exc:
        assert isinstance(exc, CommunicationError)
        assert str(exc) == 'Testing Communication Error'
    assert not caplog.records

    # Same using a protocol *without* forward_clean_errors should
    # give us a generic RemoteError and log an error.
    caplog.clear()
    with pytest.raises(RemoteError):
        _response5 = objb.msg.send(_TMsg1(ival=3))
    assert (
        len(caplog.records) == 1 and caplog.records[0].levelno == logging.ERROR
    )

    # Misc other error types happening on peer should result in
    # RemoteError and log message.
    caplog.clear()
    with pytest.raises(RemoteError):
        _response5 = obj.msg.send(_TMsg1(ival=2))
    # This should have logged a single error message.
    assert (
        len(caplog.records) == 1 and caplog.records[0].levelno == logging.ERROR
    )

    # Now test sends to async handlers.
    response6 = asyncio.run(obj2.msg.send_async(_TMsg1(ival=0)))
    assert isinstance(response6, _TResp1)

    # Our sender here is using a 'newer' protocol which contains a message
    # type not in the older protocol used by our receivers. Make sure we
    # get the expected error when trying to send that message to them.
    with pytest.raises(RemoteError):
        _response7 = obj.msg.send(_TMsg4(sval2='blargh'))

    # Also make sure the receiver can explicitly handle unregistered
    # messages (by forwarding them along to something that can, etc).
    obj.test_handling_unregistered = True
    response7 = obj.msg.send(_TMsg4(sval2='blargh'))
    assert response7 is None

    # Make sure static typing lines up with what we expect.
    if os.environ.get('EFRO_TEST_MESSAGE_FAST') != '1':
        # assert static_type_equals(response6, _TResp1)
        assert_type(response6, _TResp1)

    # Now test adding extra data to messages. This should be transferred
    # into the encoded message, copied to the response, and again back
    # through the encoded response using the filter functions we defined.
    obj.test_sidecar = True
    obj_r_sync.test_sidecar = True
    outmsg = _TMsg1(ival=0)
    setattr(outmsg, '_sidecar_data', 198)  # Our test payload.
    response1 = obj.msg.send(outmsg)
    assert getattr(response1, '_sidecar_data') == 198
    obj.test_sidecar = False
    obj_r_sync.test_sidecar = False

    # Now test errors in the raw-send function. Errors there should
    # come across as either CommunicationErrors or RuntimeErrors
    obj.test_send_method_exceptions = True

    obj.test_send_method_exceptions_comm = False
    with pytest.raises(RuntimeError):
        response1 = obj.msg.send(_TMsg1(ival=0))
    with pytest.raises(RuntimeError):
        response4 = asyncio.run(obj.msg.send_async(_TMsg1(ival=0)))

    obj.test_send_method_exceptions_comm = True
    with pytest.raises(CommunicationError):
        response1 = obj.msg.send(_TMsg1(ival=0))
    with pytest.raises(CommunicationError):
        response4 = asyncio.run(obj.msg.send_async(_TMsg1(ival=0)))

    obj.test_send_method_exceptions = False
