# Released under the MIT License. See LICENSE for details.
#
"""Testing message functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload
from dataclasses import dataclass

import pytest

from efro.error import CleanError, RemoteError
from efro.dataclassio import ioprepped
from efro.message import (Message, MessageProtocol, MessageSender,
                          MessageReceiver)
from efrotools.statictest import static_type_equals

if TYPE_CHECKING:
    from typing import List, Type, Any, Callable, Union


@ioprepped
@dataclass
class _TestMessage1(Message):
    """Just testing."""
    ival: int

    @classmethod
    def get_response_types(cls) -> List[Type[Message]]:
        return [_TestMessageR1]


@ioprepped
@dataclass
class _TestMessage2(Message):
    """Just testing."""
    sval: str

    @classmethod
    def get_response_types(cls) -> List[Type[Message]]:
        return [_TestMessageR1, _TestMessageR2]


@ioprepped
@dataclass
class _TestMessageR1(Message):
    """Just testing."""
    bval: bool


@ioprepped
@dataclass
class _TestMessageR2(Message):
    """Just testing."""
    fval: float


@ioprepped
@dataclass
class _TestMessageR3(Message):
    """Just testing."""
    fval: float


class _TestMessageSender(MessageSender):
    """Testing type overrides for message sending.

    Normally this would be auto-generated based on the protocol.
    """

    def __get__(self,
                obj: Any,
                type_in: Any = None) -> _BoundTestMessageSender:
        return _BoundTestMessageSender(obj, self)


class _BoundTestMessageSender:
    """Testing type overrides for message sending.

    Normally this would be auto-generated based on the protocol.
    """

    def __init__(self, obj: Any, sender: _TestMessageSender) -> None:
        assert obj is not None
        self._obj = obj
        self._sender = sender

    @overload
    def send(self, message: _TestMessage1) -> _TestMessageR1:
        ...

    @overload
    def send(self,
             message: _TestMessage2) -> Union[_TestMessageR1, _TestMessageR2]:
        ...

    def send(self, message: Message) -> Message:
        """Send a particular message type."""
        return self._sender.send(self._obj, message)


class _TestMessageReceiver(MessageReceiver):
    """Testing type overrides for message receiving.

    Normally this would be auto-generated based on the protocol.
    """

    def __get__(self,
                obj: Any,
                type_in: Any = None) -> _BoundTestMessageReceiver:
        return _BoundTestMessageReceiver(obj, self)

    @overload
    def handler(
        self, call: Callable[[Any, _TestMessage1], _TestMessageR1]
    ) -> Callable[[Any, _TestMessage1], _TestMessageR1]:
        ...

    @overload
    def handler(
        self, call: Callable[[Any, _TestMessage2], Union[_TestMessageR1,
                                                         _TestMessageR2]]
    ) -> Callable[[Any, _TestMessage2], Union[_TestMessageR1, _TestMessageR2]]:
        ...

    def handler(self, call: Callable) -> Callable:
        """Decorator to register a handler for a particular message type."""
        self.register_handler(call)
        return call


class _BoundTestMessageReceiver:
    """Testing type overrides for message receiving.

    Normally this would be auto-generated based on the protocol.
    """

    def __init__(self, obj: Any, receiver: _TestMessageReceiver) -> None:
        assert obj is not None
        self._obj = obj
        self._receiver = receiver

    def handle_raw_message(self, message: bytes) -> bytes:
        """Handle a raw incoming message."""
        return self._receiver.handle_raw_message(self._obj, message)


TEST_PROTOCOL = MessageProtocol(
    message_types={
        1: _TestMessage1,
        2: _TestMessage2,
        3: _TestMessageR1,
        4: _TestMessageR2,
    },
    trusted_client=True,
    log_remote_exceptions=False,
)


def test_protocol_creation() -> None:
    """Test protocol creation."""

    # This should fail because _TestMessage1 can return _TestMessageR1 which
    # is not given an id here.
    with pytest.raises(ValueError):
        _protocol = MessageProtocol(message_types={1: _TestMessage1})

    # Now it should work.
    _protocol = MessageProtocol(message_types={
        1: _TestMessage1,
        2: _TestMessageR1
    })


def test_receiver_creation() -> None:
    """Test receiver creation"""

    # This should fail due to the registered handler only specifying
    # one response message type while the message type itself
    # specifies two.
    with pytest.raises(TypeError):

        class _TestClassR:
            """Test class incorporating receive functionality."""

            receiver = _TestMessageReceiver(TEST_PROTOCOL)

            @receiver.handler
            def handle_test_message_2(self,
                                      msg: _TestMessage2) -> _TestMessageR2:
                """Test."""
                del msg  # Unused
                print('Hello from test message 1 handler!')
                return _TestMessageR2(fval=1.2)

    # Should fail because not all message types in the protocol are handled.
    with pytest.raises(TypeError):

        class _TestClassR2:
            """Test class incorporating receive functionality."""

            receiver = _TestMessageReceiver(TEST_PROTOCOL)
            receiver.validate_handler_completeness()


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
        def handle_test_message_1(self, msg: _TestMessage1) -> _TestMessageR1:
            """Test."""
            print('Hello from test message 1 handler!')
            if msg.ival == 1:
                raise CleanError('Testing Clean Error')
            if msg.ival == 2:
                raise RuntimeError('Testing Runtime Error')
            return _TestMessageR1(bval=True)

        @receiver.handler
        def handle_test_message_2(
                self,
                msg: _TestMessage2) -> Union[_TestMessageR1, _TestMessageR2]:
            """Test."""
            del msg  # Unused
            print('Hello from test message 2 handler!')
            return _TestMessageR2(fval=1.2)

        receiver.validate_handler_completeness()

    obj_r = TestClassR()
    obj_s = TestClassS(target=obj_r)

    response = obj_s.msg.send(_TestMessage1(ival=0))
    response2 = obj_s.msg.send(_TestMessage2(sval='rah'))
    assert static_type_equals(response, _TestMessageR1)
    assert isinstance(response, _TestMessageR1)
    assert isinstance(response2, (_TestMessageR1, _TestMessageR2))

    # Remote CleanErrors should come across locally as the same.
    try:
        _response3 = obj_s.msg.send(_TestMessage1(ival=1))
    except Exception as exc:
        assert isinstance(exc, CleanError)
        assert str(exc) == 'Testing Clean Error'

    # Other remote errors should come across as RemoteError.
    with pytest.raises(RemoteError):
        _response4 = obj_s.msg.send(_TestMessage1(ival=2))
