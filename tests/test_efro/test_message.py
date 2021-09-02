# Released under the MIT License. See LICENSE for details.
#
"""Testing message functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

import pytest

from efro.dataclassio import ioprepped
from efro.message import (Message, MessageProtocol, MessageSender,
                          MessageReceiver)

if TYPE_CHECKING:
    from typing import List, Type


@ioprepped
@dataclass
class _TestMessage1(Message):
    """Just testing."""
    ival: int

    @classmethod
    def get_response_types(cls) -> List[Type[Message]]:
        return [_TestMessage2]


@ioprepped
@dataclass
class _TestMessage2(Message):
    """Just testing."""
    bval: bool


def test_protocol_creation() -> None:
    """Test protocol creation."""

    # This should fail because _TestMessage1 can return _TestMessage2 which
    # is not given an id here.
    with pytest.raises(ValueError):
        _protocol = MessageProtocol(message_types={1: _TestMessage1})

    _protocol = MessageProtocol(message_types={
        1: _TestMessage1,
        2: _TestMessage2
    })


def test_message_sending() -> None:
    """Test simple message sending."""

    protocol = MessageProtocol(message_types={
        1: _TestMessage1,
        2: _TestMessage2
    })

    class TestClassS:
        """For testing send functionality."""

        msg = MessageSender(protocol)

        def __init__(self, receiver: TestClassR) -> None:
            self._receiver = receiver

        @msg.send_raw_handler
        def _send_raw_message(self, data: bytes) -> bytes:
            """Test."""
            print(f'WOULD SEND RAW MSG OF SIZE: {len(data)}')
            return b''

    class TestClassR:
        """For testing receive functionality."""

        receiver = MessageReceiver(protocol)

        @receiver.handler
        def handle_test_message(self, msg: Message) -> Message:
            """Test."""
            del msg  # Unused
            print('Hello from test message 1 handler!')
            return _TestMessage2(bval=True)

    obj_r = TestClassR()
    obj_s = TestClassS(receiver=obj_r)
    print(f'MADE TEST OBJS {obj_s} and {obj_r}')
    obj_s.msg.send(_TestMessage1(ival=0))
