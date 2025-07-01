# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from efro.message._protocol import MessageProtocol
from efro.message._sender import MessageSender, BoundMessageSender
from efro.message._receiver import MessageReceiver, BoundMessageReceiver
from efro.message._module import create_sender_module, create_receiver_module
from efro.message._message import (
    Message,
    Response,
    SysResponse,
    EmptySysResponse,
    ErrorSysResponse,
    StringResponse,
    BoolResponse,
    UnregisteredMessageIDError,
)

__all__ = [
    'Message',
    'Response',
    'SysResponse',
    'EmptySysResponse',
    'ErrorSysResponse',
    'StringResponse',
    'BoolResponse',
    'MessageProtocol',
    'MessageSender',
    'BoundMessageSender',
    'MessageReceiver',
    'BoundMessageReceiver',
    'create_sender_module',
    'create_receiver_module',
    'UnregisteredMessageIDError',
]
