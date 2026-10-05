# Released under the MIT License. See LICENSE for details.
#
"""Communication from a sandboxed task to its owning basn process."""

from enum import Enum
from typing import Annotated
from dataclasses import dataclass

from efro.logging import LogEntry
from efro.dataclassio import ioprepped, IOAttrs
from efro.message import Message, MessageProtocol


def get_protocol() -> MessageProtocol:
    """Get the protocol used in this communication.

    Sandbox payloads send these messages to the owning basn process.
    basn is trusted to see sandbox-side error tracebacks (helpful for
    debugging mod failures). Remember to run 'make codegen' after
    changes here.
    """
    return MessageProtocol(
        message_types={
            0: ReadyMessage,
            1: ShuttingDownMessage,
            2: LogBatchMessage,
            3: StatBatchMessage,
            4: ProbeResultMessage,
        },
        response_types={},
        remote_errors_include_stack_traces=True,
    )


@ioprepped
@dataclass
class ReadyMessage(Message):
    """Sandbox has finished init and is ready for real traffic.

    Single bootstrap signal; basn advances its state machine from
    CONNECTED to READY on first receipt. Duplicates dropped.
    """


class ShutdownReason(Enum):
    """Why the sandboxed task is shutting itself down."""

    CLEAN_EXIT = 'c'
    ERROR = 'e'


@ioprepped
@dataclass
class ShuttingDownMessage(Message):
    """Sandbox is shutting itself down (not in response to a basn request).

    Lets basn distinguish clean self-shutdown from error/crash exits.
    """

    reason: Annotated[ShutdownReason, IOAttrs('r')]
    detail: Annotated[str, IOAttrs('d', store_default=False)] = ''


@ioprepped
@dataclass
class LogBatchMessage(Message):
    """Batched log entries from the sandboxed task.

    Reuses efro.logging.LogEntry so basn-side handler can hand
    entries straight to its existing log routing.
    """

    entries: Annotated[list[LogEntry], IOAttrs('e')]


@ioprepped
@dataclass
class StatUpdate:
    """A single counter or gauge update from the sandbox."""

    name: Annotated[str, IOAttrs('n')]
    value: Annotated[float, IOAttrs('v')]


@ioprepped
@dataclass
class StatBatchMessage(Message):
    """Batched stat updates."""

    updates: Annotated[list[StatUpdate], IOAttrs('u')]


class ProbeResultType(Enum):
    """Outcome of a single boundary probe."""

    ALLOWED = 'a'
    BLOCKED = 'b'
    INFO = 'i'


@ioprepped
@dataclass
class ProbeResultMessage(Message):
    """Structured result of one boundary probe run during sandbox startup.

    Sent before ReadyMessage as the test-app's startup phase runs.
    CI asserts directly against (name, result) pairs.
    """

    name: Annotated[str, IOAttrs('n')]
    result: Annotated[ProbeResultType, IOAttrs('r')]
    detail: Annotated[str, IOAttrs('d', store_default=False)] = ''
