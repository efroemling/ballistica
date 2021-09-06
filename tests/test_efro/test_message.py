# Released under the MIT License. See LICENSE for details.
#
"""Testing message functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload
from dataclasses import dataclass

import pytest

from efro.dataclassio import ioprepped
from efro.message import (Message, MessageProtocol, MessageSender,
                          MessageReceiver)
# from efrotools.statictest import static_type_equals

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

    def send(self, message: Any) -> Any:
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


TEST_PROTOCOL = MessageProtocol(message_types={
    1: _TestMessage1,
    2: _TestMessage2,
    3: _TestMessageR1,
    4: _TestMessageR2,
})


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


def test_message_sending() -> None:
    """Test simple message sending."""

    # Define a class that can send messages and one that can receive them.
    class TestClassS:
        """Test class incorporating send functionality."""

        msg = _TestMessageSender(TEST_PROTOCOL)

        def __init__(self, receiver: TestClassR) -> None:
            self._receiver = receiver

        @msg.send_raw_handler
        def _send_raw_message(self, data: bytes) -> bytes:
            """Test."""
            print(f'WOULD SEND RAW MSG OF SIZE: {len(data)}')
            return b''

    class TestClassR:
        """Test class incorporating receive functionality."""

        receiver = _TestMessageReceiver(TEST_PROTOCOL)

        @receiver.handler
        def handle_test_message_1(self, msg: _TestMessage1) -> _TestMessageR1:
            """Test."""
            del msg  # Unused
            print('Hello from test message 1 handler!')
            return _TestMessageR1(bval=True)

        @receiver.handler
        def handle_test_message_2(
                self,
                msg: _TestMessage2) -> Union[_TestMessageR1, _TestMessageR2]:
            """Test."""
            del msg  # Unused
            print('Hello from test message 1 handler!')
            return _TestMessageR2(fval=1.2)

    obj_r = TestClassR()
    obj_s = TestClassS(receiver=obj_r)

    _result = obj_s.msg.send(_TestMessage1(ival=0))
    _result2 = obj_s.msg.send(_TestMessage2(sval='rah'))
    print('SKIPPING STATIC CHECK')
    # assert static_type_equals(result, _TestMessageR1)
    # assert isinstance(result, _TestMessageR1)
