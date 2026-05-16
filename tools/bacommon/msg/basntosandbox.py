# Released under the MIT License. See LICENSE for details.
#
"""Communication from basn to one of its sandboxed tasks."""

from __future__ import annotations

from dataclasses import dataclass

from efro.dataclassio import ioprepped
from efro.message import Message, MessageProtocol


def get_protocol() -> MessageProtocol:
    """Get the protocol used in this communication.

    basn sends these messages into a sandboxed task. The sandbox is
    NOT trusted with basn-side error tracebacks (could leak
    internals to untrusted code). Remember to run 'make codegen'
    after changes here.
    """
    return MessageProtocol(
        message_types={
            0: ShutdownMessage,
        },
        response_types={},
        remote_errors_include_stack_traces=False,
    )


@ioprepped
@dataclass
class ShutdownMessage(Message):
    """Request the sandboxed task to gracefully shut itself down.

    The (empty default) response acts as the ack — basn's send_async
    resolves only after the sandbox's handler returns, so the
    response IS the "shutdown complete" signal. basn awaits the
    response with a timeout; on timeout, falls through to the runsc
    kill SIGTERM ladder.
    """
