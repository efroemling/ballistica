# Released under the MIT License. See LICENSE for details.
#
"""Testing message functionality."""

from __future__ import annotations

import os
import asyncio
from typing import TYPE_CHECKING, overload, Union
from dataclasses import dataclass

import pytest

from efrotools.statictest import static_type_equals
from efro.error import CleanError, RemoteError
from efro.dataclassio import ioprepped
from efro.message import (Message, Response, MessageProtocol, MessageSender,
                          BoundMessageSender, MessageReceiver,
                          BoundMessageReceiver)

if TYPE_CHECKING:
    from typing import Any, Callable, Optional, Awaitable


@ioprepped
@dataclass
class _TMsg1(Message):
    """Just testing."""
    ival: int

    @classmethod
    def get_response_types(cls) -> list[type[Response]]:
        return [_TResp1]


@ioprepped
@dataclass
class _TMsg2(Message):
    """Just testing."""
    sval: str

    @classmethod
    def get_response_types(cls) -> list[type[Response]]:
        return [_TResp1, _TResp2]


@ioprepped
@dataclass
class _TMsg3(Message):
    """Just testing."""
    sval: str


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

    def __get__(self,
                obj: Any,
                type_in: Any = None) -> _BoundTestMessageSenderSingle:
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

    def __get__(self,
                obj: Any,
                type_in: Any = None) -> _BoundTestMessageSenderSync:
        return _BoundTestMessageSenderSync(obj, self)


class _BoundTestMessageSenderSync(BoundMessageSender):
    """Protocol-specific bound sender."""

    @overload
    def send(self, message: _TMsg1) -> _TResp1:
        ...

    @overload
    def send(self, message: _TMsg2) -> Union[_TResp1, _TResp2]:
        ...

    @overload
    def send(self, message: _TMsg3) -> None:
        ...

    def send(self, message: Message) -> Optional[Response]:
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

    def __get__(self,
                obj: Any,
                type_in: Any = None) -> _BoundTestMessageSenderAsync:
        return _BoundTestMessageSenderAsync(obj, self)


class _BoundTestMessageSenderAsync(BoundMessageSender):
    """Protocol-specific bound sender."""

    @overload
    async def send_async(self, message: _TMsg1) -> _TResp1:
        ...

    @overload
    async def send_async(self, message: _TMsg2) -> Union[_TResp1, _TResp2]:
        ...

    @overload
    async def send_async(self, message: _TMsg3) -> None:
        ...

    async def send_async(self, message: Message) -> Optional[Response]:
        """Send a message asynchronously."""
        return await self._sender.send_async(self._obj, message)


# SEND_ASYNC_CODE_TEST_END

# Generated sender supporting both sync and async sending:
# SEND_BOTH_CODE_TEST_BEGIN


class _TestMessageSenderBoth(MessageSender):
    """Protocol-specific sender."""

    def __init__(self) -> None:
        protocol = TEST_PROTOCOL
        super().__init__(protocol)

    def __get__(self,
                obj: Any,
                type_in: Any = None) -> _BoundTestMessageSenderBoth:
        return _BoundTestMessageSenderBoth(obj, self)


class _BoundTestMessageSenderBoth(BoundMessageSender):
    """Protocol-specific bound sender."""

    @overload
    def send(self, message: _TMsg1) -> _TResp1:
        ...

    @overload
    def send(self, message: _TMsg2) -> Union[_TResp1, _TResp2]:
        ...

    @overload
    def send(self, message: _TMsg3) -> None:
        ...

    def send(self, message: Message) -> Optional[Response]:
        """Send a message synchronously."""
        return self._sender.send(self._obj, message)

    @overload
    async def send_async(self, message: _TMsg1) -> _TResp1:
        ...

    @overload
    async def send_async(self, message: _TMsg2) -> Union[_TResp1, _TResp2]:
        ...

    @overload
    async def send_async(self, message: _TMsg3) -> None:
        ...

    async def send_async(self, message: Message) -> Optional[Response]:
        """Send a message asynchronously."""
        return await self._sender.send_async(self._obj, message)


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

    def handle_raw_message(self, message: str) -> str:
        """Synchronously handle a raw incoming message."""
        return self._receiver.handle_raw_message(self._obj, message)


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
        call: Callable[[Any, _TMsg2], Union[_TResp1, _TResp2]],
    ) -> Callable[[Any, _TMsg2], Union[_TResp1, _TResp2]]:
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

    def handle_raw_message(self, message: str) -> str:
        """Synchronously handle a raw incoming message."""
        return self._receiver.handle_raw_message(self._obj, message)


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
        call: Callable[[Any, _TMsg2], Awaitable[Union[_TResp1, _TResp2]]],
    ) -> Callable[[Any, _TMsg2], Awaitable[Union[_TResp1, _TResp2]]]:
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

    async def handle_raw_message(self, message: str) -> str:
        """Asynchronously handle a raw incoming message."""
        return await self._receiver.handle_raw_message_async(
            self._obj, message)


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
    trusted_sender=True,
    log_remote_exceptions=False,
)

TEST_PROTOCOL_SINGLE = MessageProtocol(
    message_types={
        0: _TMsg1,
    },
    response_types={
        0: _TResp1,
    },
    trusted_sender=True,
    log_remote_exceptions=False,
)


def test_protocol_creation() -> None:
    """Test protocol creation."""

    # This should fail because _TMsg1 can return _TResp1 which
    # is not given an id here.
    with pytest.raises(ValueError):
        _protocol = MessageProtocol(message_types={0: _TMsg1},
                                    response_types={0: _TResp2})

    # Now it should work.
    _protocol = MessageProtocol(message_types={0: _TMsg1},
                                response_types={0: _TResp1})


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

    emb = (f'# SEND_SINGLE_CODE_TEST_BEGIN'
           f'\n\n\n{clipped}\n\n\n# SEND_SINGLE_CODE_TEST_END\n')
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError('Generated sender module does not match embedded;'
                           ' test code needs to be updated.'
                           ' See test stdout for new code.')


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

    emb = (f'# SEND_SYNC_CODE_TEST_BEGIN'
           f'\n\n\n{clipped}\n\n\n# SEND_SYNC_CODE_TEST_END\n')
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError('Generated sender module does not match embedded;'
                           ' test code needs to be updated.'
                           ' See test stdout for new code.')


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

    emb = (f'# SEND_ASYNC_CODE_TEST_BEGIN'
           f'\n\n\n{clipped}\n\n\n# SEND_ASYNC_CODE_TEST_END\n')
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError('Generated sender module does not match embedded;'
                           ' test code needs to be updated.'
                           ' See test stdout for new code.')


def test_sender_module_both_emb() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    # NOTE: Ideally we should be testing efro.message.create_sender_module()
    # here, but it requires us to pass code which imports this test module
    # to get at the protocol, and that currently fails in our static mypy
    # tests.
    smod = TEST_PROTOCOL.do_create_sender_module(
        'TestMessageSenderBoth',
        protocol_create_code='protocol = TEST_PROTOCOL',
        enable_sync_sends=True,
        enable_async_sends=True,
        private=True,
    )

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestMessageSenderBoth(MessageSender):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (f'# SEND_BOTH_CODE_TEST_BEGIN'
           f'\n\n\n{clipped}\n\n\n# SEND_BOTH_CODE_TEST_END\n')
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError('Generated sender module does not match embedded;'
                           ' test code needs to be updated.'
                           ' See test stdout for new code.')


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
        'class _TestSingleMessageReceiver(MessageReceiver):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (f'# RCV_SINGLE_CODE_TEST_BEGIN'
           f'\n\n\n{clipped}\n\n\n# RCV_SINGLE_CODE_TEST_END\n')
    if emb not in ourcode:
        print(f'EXPECTED SINGLE RECEIVER EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated single receiver module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.')


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

    emb = (f'# RCV_SYNC_CODE_TEST_BEGIN'
           f'\n\n\n{clipped}\n\n\n# RCV_SYNC_CODE_TEST_END\n')
    if emb not in ourcode:
        print(f'EXPECTED SYNC RECEIVER EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated sync receiver module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.')


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
    classline = lines.index(
        'class _TestAsyncMessageReceiver(MessageReceiver):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our embedded version.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = (f'# RCV_ASYNC_CODE_TEST_BEGIN'
           f'\n\n\n{clipped}\n\n\n# RCV_ASYNC_CODE_TEST_END\n')
    if emb not in ourcode:
        print(f'EXPECTED ASYNC RECEIVER EMBEDDED CODE:\n{emb}')
        raise RuntimeError(
            'Generated async receiver module does not match embedded;'
            ' test code needs to be updated.'
            ' See test stdout for new code.')


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


def test_full_pipeline() -> None:
    """Test the full pipeline."""

    # Define a class that can send messages and one that can receive them.
    class TestClassS:
        """Test class incorporating send functionality."""

        msg = _TestMessageSenderBoth()

        def __init__(self, target: Union[TestClassRSync,
                                         TestClassRAsync]) -> None:
            self._target = target

        @msg.send_method
        def _send_raw_message(self, data: str) -> str:
            """Handle synchronous sending of raw json message data."""
            # Just talk directly to the receiver for this example.
            # (currently only support synchronous receivers)
            assert isinstance(self._target, TestClassRSync)
            return self._target.receiver.handle_raw_message(data)

        @msg.send_async_method
        async def _send_raw_message_async(self, data: str) -> str:
            """Handle asynchronous sending of raw json message data."""
            # Just talk directly to the receiver for this example.
            # (we can do sync or async receivers)
            if isinstance(self._target, TestClassRSync):
                return self._target.receiver.handle_raw_message(data)
            return await self._target.receiver.handle_raw_message(data)

    class TestClassRSync:
        """Test class incorporating synchronous receive functionality."""

        receiver = _TestSyncMessageReceiver()

        @receiver.handler
        def handle_test_message_1(self, msg: _TMsg1) -> _TResp1:
            """Test."""
            if msg.ival == 1:
                raise CleanError('Testing Clean Error')
            if msg.ival == 2:
                raise RuntimeError('Testing Runtime Error')
            return _TResp1(bval=True)

        @receiver.handler
        def handle_test_message_2(self,
                                  msg: _TMsg2) -> Union[_TResp1, _TResp2]:
            """Test."""
            del msg  # Unused
            return _TResp2(fval=1.2)

        @receiver.handler
        def handle_test_message_3(self, msg: _TMsg3) -> None:
            """Test."""
            del msg  # Unused

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
            return _TResp1(bval=True)

        @receiver.handler
        async def handle_test_message_2(
                self, msg: _TMsg2) -> Union[_TResp1, _TResp2]:
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

    # Test sends (of sync and async varieties).
    response1 = obj.msg.send(_TMsg1(ival=0))
    response2 = obj.msg.send(_TMsg2(sval='rah'))
    response3 = obj.msg.send(_TMsg3(sval='rah'))
    response4 = asyncio.run(obj.msg.send_async(_TMsg1(ival=0)))

    # Make sure static typing lines up with what we expect.
    if os.environ.get('EFRO_TEST_MESSAGE_FAST') != '1':
        assert static_type_equals(response1, _TResp1)
        assert static_type_equals(response3, None)

    assert isinstance(response1, _TResp1)
    assert isinstance(response2, (_TResp1, _TResp2))
    assert response3 is None
    assert isinstance(response4, _TResp1)

    # Remote CleanErrors should come across locally as the same.
    try:
        _response5 = obj.msg.send(_TMsg1(ival=1))
    except Exception as exc:
        assert isinstance(exc, CleanError)
        assert str(exc) == 'Testing Clean Error'

    # Other remote errors should result in RemoteError.
    with pytest.raises(RemoteError):
        _response5 = obj.msg.send(_TMsg1(ival=2))

    # Now test sends to async handlers.
    response6 = asyncio.run(obj2.msg.send_async(_TMsg1(ival=0)))
    assert isinstance(response6, _TResp1)

    # Make sure static typing lines up with what we expect.
    if os.environ.get('EFRO_TEST_MESSAGE_FAST') != '1':
        assert static_type_equals(response6, _TResp1)
