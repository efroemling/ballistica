# Released under the MIT License. See LICENSE for details.
#
"""Testing message functionality."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, overload
from dataclasses import dataclass

import pytest

from efrotools.statictest import static_type_equals
from efro.error import CleanError, RemoteError
from efro.dataclassio import ioprepped
from efro.message import (Message, Response, MessageProtocol, MessageSender,
                          MessageReceiver, EmptyResponse)

if TYPE_CHECKING:
    from typing import List, Type, Any, Callable, Union, Optional


@ioprepped
@dataclass
class _TMessage1(Message):
    """Just testing."""
    ival: int

    @classmethod
    def get_response_types(cls) -> List[Type[Response]]:
        return [_TResponse1]


@ioprepped
@dataclass
class _TMessage2(Message):
    """Just testing."""
    sval: str

    @classmethod
    def get_response_types(cls) -> List[Type[Response]]:
        return [_TResponse1, _TResponse2]


@ioprepped
@dataclass
class _TMessage3(Message):
    """Just testing."""
    sval: str


@ioprepped
@dataclass
class _TResponse1(Response):
    """Just testing."""
    bval: bool


@ioprepped
@dataclass
class _TResponse2(Response):
    """Just testing."""
    fval: float


@ioprepped
@dataclass
class _TResponse3(Message):
    """Just testing."""
    fval: float


# SEND_CODE_TEST_BEGIN


class _TestMessageSender(MessageSender):
    """Protocol-specific sender."""

    def __get__(self,
                obj: Any,
                type_in: Any = None) -> _BoundTestMessageSender:
        return _BoundTestMessageSender(obj, self)


class _BoundTestMessageSender:
    """Protocol-specific bound sender."""

    def __init__(self, obj: Any, sender: _TestMessageSender) -> None:
        assert obj is not None
        self._obj = obj
        self._sender = sender

    @overload
    def send(self, message: _TMessage1) -> _TResponse1:
        ...

    @overload
    def send(self, message: _TMessage2) -> Union[_TResponse1, _TResponse2]:
        ...

    @overload
    def send(self, message: _TMessage3) -> None:
        ...

    def send(self, message: Message) -> Optional[Response]:
        """Send a message."""
        return self._sender.send(self._obj, message)


# SEND_CODE_TEST_END
# RCV_CODE_TEST_BEGIN


class _TestMessageReceiver(MessageReceiver):
    """Protocol-specific receiver."""

    def __get__(
        self,
        obj: Any,
        type_in: Any = None,
    ) -> _BoundTestMessageReceiver:
        return _BoundTestMessageReceiver(obj, self)

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMessage1], _TResponse1],
    ) -> Callable[[Any, _TMessage1], _TResponse1]:
        ...

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMessage2], Union[_TResponse1, _TResponse2]],
    ) -> Callable[[Any, _TMessage2], Union[_TResponse1, _TResponse2]]:
        ...

    @overload
    def handler(
        self,
        call: Callable[[Any, _TMessage3], None],
    ) -> Callable[[Any, _TMessage3], None]:
        ...

    def handler(self, call: Callable) -> Callable:
        """Decorator to register message handlers."""
        self.register_handler(call)
        return call


class _BoundTestMessageReceiver:
    """Protocol-specific bound receiver."""

    def __init__(
        self,
        obj: Any,
        receiver: _TestMessageReceiver,
    ) -> None:
        assert obj is not None
        self._obj = obj
        self._receiver = receiver

    def handle_raw_message(self, message: bytes) -> bytes:
        """Handle a raw incoming message."""
        return self._receiver.handle_raw_message(self._obj, message)


# RCV_CODE_TEST_END

TEST_PROTOCOL = MessageProtocol(
    message_types={
        0: _TMessage1,
        1: _TMessage2,
        2: _TMessage3,
    },
    response_types={
        0: _TResponse1,
        1: _TResponse2,
        2: EmptyResponse,
    },
    trusted_client=True,
    log_remote_exceptions=False,
)


def test_protocol_creation() -> None:
    """Test protocol creation."""

    # This should fail because _TMessage1 can return _TResponse1 which
    # is not given an id here.
    with pytest.raises(ValueError):
        _protocol = MessageProtocol(
            message_types={0: _TMessage1},
            response_types={0: _TResponse2},
        )

    # Now it should work.
    _protocol = MessageProtocol(
        message_types={0: _TMessage1},
        response_types={0: _TResponse1},
    )


def test_sender_module_creation() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    smod = TEST_PROTOCOL.create_sender_module('Test', private=True)

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestMessageSender(MessageSender):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our test code.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = f'# SEND_CODE_TEST_BEGIN\n\n\n{clipped}\n\n\n# SEND_CODE_TEST_END\n'
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError('Generated sender module does not match embedded;'
                           ' test code needs to be updated.'
                           ' See test stdout for new code.')


def test_receiver_module_creation() -> None:
    """Test generation of protocol-specific sender modules for typing/etc."""
    smod = TEST_PROTOCOL.create_receiver_module('Test', private=True)

    # Clip everything up to our first class declaration.
    lines = smod.splitlines()
    classline = lines.index('class _TestMessageReceiver(MessageReceiver):')
    clipped = '\n'.join(lines[classline:])

    # This snippet should match what we've got embedded above;
    # If not then we need to update our test code.
    with open(__file__, encoding='utf-8') as infile:
        ourcode = infile.read()

    emb = f'# RCV_CODE_TEST_BEGIN\n\n\n{clipped}\n\n\n# RCV_CODE_TEST_END\n'
    if emb not in ourcode:
        print(f'EXPECTED EMBEDDED CODE:\n{emb}')
        raise RuntimeError('Generated sender module does not match embedded;'
                           ' test code needs to be updated.'
                           ' See test stdout for new code.')


def test_receiver_creation() -> None:
    """Test receiver creation."""

    # This should fail due to the registered handler only specifying
    # one response message type while the message type itself
    # specifies two.
    with pytest.raises(TypeError):

        class _TestClassR:
            """Test class incorporating receive functionality."""

            receiver = _TestMessageReceiver(TEST_PROTOCOL)

            @receiver.handler
            def handle_test_message_2(self, msg: _TMessage2) -> _TResponse2:
                """Test."""
                del msg  # Unused
                return _TResponse2(fval=1.2)

    # Should fail because not all message types in the protocol are handled.
    with pytest.raises(TypeError):

        class _TestClassR2:
            """Test class incorporating receive functionality."""

            receiver = _TestMessageReceiver(TEST_PROTOCOL)
            receiver.validate()


def test_message_sending() -> None:
    """Test simple message sending."""

    # Define a class that can send messages and one that can receive them.
    class TestClassS:
        """Test class incorporating send functionality."""

        msg = _TestMessageSender(TEST_PROTOCOL)

        def __init__(self, target: TestClassR) -> None:
            self._target = target

        @msg.send_raw_handler
        def _send_raw_message(self, data: bytes) -> bytes:
            """Test."""
            return self._target.receiver.handle_raw_message(data)

    class TestClassR:
        """Test class incorporating receive functionality."""

        receiver = _TestMessageReceiver(TEST_PROTOCOL)

        @receiver.handler
        def handle_test_message_1(self, msg: _TMessage1) -> _TResponse1:
            """Test."""
            if msg.ival == 1:
                raise CleanError('Testing Clean Error')
            if msg.ival == 2:
                raise RuntimeError('Testing Runtime Error')
            return _TResponse1(bval=True)

        @receiver.handler
        def handle_test_message_2(
                self, msg: _TMessage2) -> Union[_TResponse1, _TResponse2]:
            """Test."""
            del msg  # Unused
            return _TResponse2(fval=1.2)

        @receiver.handler
        def handle_test_message_3(self, msg: _TMessage3) -> None:
            """Test."""
            del msg  # Unused

        receiver.validate()

    obj_r = TestClassR()
    obj_s = TestClassS(target=obj_r)

    response = obj_s.msg.send(_TMessage1(ival=0))
    assert isinstance(response, _TResponse1)

    response2 = obj_s.msg.send(_TMessage2(sval='rah'))
    assert isinstance(response2, (_TResponse1, _TResponse2))

    response3 = obj_s.msg.send(_TMessage3(sval='rah'))
    assert response3 is None

    if os.environ.get('EFRO_TEST_MESSAGE_FAST') != '1':
        assert static_type_equals(response, _TResponse1)
        assert static_type_equals(response3, None)

    # Remote CleanErrors should come across locally as the same.
    try:
        _response3 = obj_s.msg.send(_TMessage1(ival=1))
    except Exception as exc:
        assert isinstance(exc, CleanError)
        assert str(exc) == 'Testing Clean Error'

    # Other remote errors should come across as RemoteError.
    with pytest.raises(RemoteError):
        _response4 = obj_s.msg.send(_TMessage1(ival=2))
