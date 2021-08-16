# Released under the MIT License. See LICENSE for details.
#
"""Testing message functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

# import pytest

from efro.message import MessageProtocol, MessageSender

if TYPE_CHECKING:
    pass


def test_message_sending() -> None:
    """Test simple message sending."""

    protocol = MessageProtocol(message_types={})

    class TestClass:
        """Test."""

        def _send_raw_message(self, data: bytes) -> bytes:
            """Test."""
            print(f'WOULD SEND RAW MSG OF SIZE {len(data)}')
            return b''

        msg = MessageSender(protocol, _send_raw_message)

    obj = TestClass()
    print(f'MADE TEST OBJ {obj}')
    obj.msg.send('foo')
