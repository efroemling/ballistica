# Released under the MIT License. See LICENSE for details.
#
"""Payload types for the cloud-console SmartSocket channel kind.

One root pair per channel kind (see the hierarchy-per-contract rule
in ``streamcall-smartsocket.md``): commands go up from the console as
:class:`ConsoleCommand`, everything it displays comes back down as
:class:`ConsoleEvent`. The relay never decodes either -- a new event
type must never require a basn rollout.

Payloads here are pure data. In particular they carry log entries and
levels, not pre-colored html; rendering belongs to whoever displays
them. That is both the payload-model rule and one less hand-rolled
escaping site than the polling console this replaced.

**Client-visible**, because the app itself can hold the far end of a
console session. That makes these definitions a public wire contract
once a build that speaks them ships: storage names and type-id values
may never be repurposed, and removed ones stay retired. Add rather
than change.
"""

from typing import Annotated, override
from enum import Enum
from dataclasses import dataclass

from efro.logging import LogEntry
from efro.dataclassio import ioprepped, IOMultiType, IOAttrs


class ConsoleCommandTypeID(Enum):
    """Type IDs for browser-to-adapter payloads."""

    EXEC = 'e'


class ConsoleCommand(IOMultiType[ConsoleCommandTypeID]):
    """Something the console's user asked us to do."""

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleCommandTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ConsoleCommandTypeID) -> type[ConsoleCommand]:
        out: type[ConsoleCommand]
        if type_id is ConsoleCommandTypeID.EXEC:
            out = ExecCommand
            return out
        raise ValueError(f'Unrecognized type-id {type_id}.')


@ioprepped
@dataclass
class ExecCommand(ConsoleCommand):
    """Run some code on the target."""

    code: Annotated[str, IOAttrs('c')]

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleCommandTypeID:
        return ConsoleCommandTypeID.EXEC


class ConsoleEventTypeID(Enum):
    """Type IDs for adapter-to-browser payloads."""

    LOG_ENTRIES = 'l'
    INSTANCE = 'i'
    GAP = 'g'
    STATUS = 's'
    EXEC_ACK = 'e'
    PERMISSION = 'p'


class ConsoleEvent(IOMultiType[ConsoleEventTypeID]):
    """Something for the console to display."""

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleEventTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: ConsoleEventTypeID) -> type[ConsoleEvent]:
        out: type[ConsoleEvent]
        if type_id is ConsoleEventTypeID.LOG_ENTRIES:
            out = LogEntriesEvent
        elif type_id is ConsoleEventTypeID.INSTANCE:
            out = InstanceEvent
        elif type_id is ConsoleEventTypeID.GAP:
            out = GapEvent
        elif type_id is ConsoleEventTypeID.STATUS:
            out = StatusEvent
        elif type_id is ConsoleEventTypeID.EXEC_ACK:
            out = ExecAckEvent
        elif type_id is ConsoleEventTypeID.PERMISSION:
            out = PermissionEvent
        else:
            raise ValueError(f'Unrecognized type-id {type_id}.')
        return out


@ioprepped
@dataclass
class LogEntriesEvent(ConsoleEvent):
    """A slice of the target's log."""

    entries: Annotated[list[LogEntry], IOAttrs('e')]

    #: Where the target's log stands after these entries. The console
    #: hands this back when it asks for a new handle, so a replacement
    #: session resumes instead of replaying everything the target
    #: still has cached.
    next_index: Annotated[int, IOAttrs('i')] = 0

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleEventTypeID:
        return ConsoleEventTypeID.LOG_ENTRIES


@ioprepped
@dataclass
class InstanceEvent(ConsoleEvent):
    """Which app instance we're now talking to.

    Sent on first contact and whenever the target's uuid changes,
    which is how a restarted app announces itself. A change means the
    log we were following is gone, so the console starts a fresh one.
    """

    target_uuid: Annotated[str, IOAttrs('u')]

    #: Display name of the device, when we know one.
    device_name: Annotated[str | None, IOAttrs('d')] = None

    #: True when this replaced an earlier instance rather than being
    #: the first one we saw -- the console words those differently.
    replaced_previous: Annotated[bool, IOAttrs('r')] = False

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleEventTypeID:
        return ConsoleEventTypeID.INSTANCE


@ioprepped
@dataclass
class GapEvent(ConsoleEvent):
    """Log lines we can never show.

    The target keeps a bounded archive, so entries can age out before
    we ask for them. Derived from the archive's start index running
    ahead of what we requested, not sent by the target.
    """

    dropped: Annotated[int, IOAttrs('d')]

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleEventTypeID:
        return ConsoleEventTypeID.GAP


@ioprepped
@dataclass
class ExecAckEvent(ConsoleEvent):
    """We handed some code to the target.

    Worth its own event because code with no output is otherwise
    indistinguishable from code that never arrived.
    """

    line_count: Annotated[int, IOAttrs('n')]

    #: The target's own clock when it ran, so the console can line
    #: the exec up against surrounding log timestamps.
    target_time: Annotated[float, IOAttrs('t')]

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleEventTypeID:
        return ConsoleEventTypeID.EXEC_ACK


class ConsolePermission(Enum):
    """Where our permission to control the target stands.

    A console session is offered to the target regardless; what this
    tracks is whether the person at the device has agreed to let it
    do anything. Until they have, no log flows and no code runs.
    """

    #: Asked, and waiting on someone at the device to answer.
    PENDING = 'p'

    #: Allowed. Log flows and commands run.
    GRANTED = 'g'

    #: Refused, or nobody answered. Retrying immediately just puts
    #: the same question in front of the same person, so a console
    #: that sees this should stop asking rather than loop.
    DENIED = 'd'


@ioprepped
@dataclass
class PermissionEvent(ConsoleEvent):
    """Whether the target has agreed to be controlled.

    Sent on every channel, including re-announcing the settled state
    after a reconnect, so a console that joins late still knows why
    it is (or isn't) seeing anything.
    """

    state: Annotated[ConsolePermission, IOAttrs('s')]

    #: Optional human-readable detail. English is fine; this surface
    #: is admin-only.
    message: Annotated[str | None, IOAttrs('m')] = None

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleEventTypeID:
        return ConsoleEventTypeID.PERMISSION


class ConsoleContact(Enum):
    """How we're getting along with the target."""

    #: Talking to it normally.
    OK = 'o'

    #: Transient trouble reaching it; we keep trying.
    UNREACHABLE = 'u'

    #: It is gone for good. The session ends after this, and the
    #: console must get a fresh handle to reach whatever replaced it.
    LOST = 'l'


@ioprepped
@dataclass
class StatusEvent(ConsoleEvent):
    """A change in our ability to reach the target."""

    contact: Annotated[ConsoleContact, IOAttrs('c')]

    #: Optional human-readable detail. English is fine; this
    #: surface is admin-only.
    message: Annotated[str | None, IOAttrs('m')] = None

    @override
    @classmethod
    def get_type_id(cls) -> ConsoleEventTypeID:
        return ConsoleEventTypeID.STATUS
