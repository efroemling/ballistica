# Released under the MIT License. See LICENSE for details.
#
"""Runs the shared SmartSocket conformance table against the endpoint.

The table (``smartsocket_conformance.json``, beside this file) is
also run by bamaster against the compiled browser client, which is
a hand-maintained mirror of :class:`efro.smartsocket.SmartSocketEndpoint`.
Anything the two must agree on -- close-code actions, when to
reconnect and for how long, what counts as an anomaly -- is a row in
that file rather than a test in either language, so drift between
them fails here or there instead of shipping.

The relay model here is deliberately small and *scripted*; the real
relay is exercised against this endpoint in basn's loopback tests.
"""

import asyncio
import json
from pathlib import Path
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, override
from enum import Enum

import pytest
from efrotools.virtualtime import run_virtual

import efro.smartsocket
from efro.dataclassio import (
    IOAttrs,
    IOMultiType,
    dataclass_from_json,
    dataclass_to_json,
    ioprepped,
)
from efro.smartsocket import (
    SS_CLOSE_RELAY_BUFFER_FULL,
    AckFrame,
    HelloFrame,
    MsgFrame,
    PingFrame,
    PongFrame,
    SmartSocketAction,
    SmartSocketClosed,
    SmartSocketEndpoint,
    SmartSocketEndpointPolicy,
    SmartSocketFrame,
    action_for_close_code,
)

if TYPE_CHECKING:
    from typing import Any

    from efro.smartsocket import SmartSocketAnomaly

_TABLE_PATH = Path(__file__).with_name('smartsocket_conformance.json')


def _table() -> dict[str, Any]:
    with _TABLE_PATH.open(encoding='utf-8') as infile:
        table: dict[str, Any] = json.load(infile)
    return table


class _PayloadTypeID(Enum):
    TEXT = 't'


class _Payload(IOMultiType[_PayloadTypeID]):
    @override
    @classmethod
    def get_type_id(cls) -> _PayloadTypeID:
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: _PayloadTypeID) -> type[_Payload]:
        assert type_id is _PayloadTypeID.TEXT
        return _Text


@ioprepped
@dataclass
class _Text(_Payload):
    text: Annotated[str, IOAttrs('t')]

    @override
    @classmethod
    def get_type_id(cls) -> _PayloadTypeID:
        return _PayloadTypeID.TEXT


def _unwrap(payload: str) -> str:
    message = dataclass_from_json(_Payload, payload)
    assert isinstance(message, _Text)
    return message.text


class _ScriptedRelay:
    """The relay model the table describes. Keep in step with the JS one."""

    def __init__(self, policy: SmartSocketEndpointPolicy) -> None:
        self.policy = policy
        self.recv = 0
        self.accepted: list[str] = []
        self.connects = 0
        self.refuse_count = 0
        self.reject_with: int | None = None
        self.silent = False
        self.full = False
        self.hello_delay = 0.0
        self.gap = False
        self.live: _Transport | None = None
        self._hello_tasks: set[asyncio.Task[None]] = set()

    async def connect(self) -> _Transport:
        """A dial."""
        if self.refuse_count > 0:
            self.refuse_count -= 1
            raise ConnectionError('refused')
        self.connects += 1
        if self.reject_with is not None:
            code = self.reject_with
            self.reject_with = None
            raise SmartSocketClosed(code, 'rejected')
        transport = _Transport(self)
        self.live = transport
        return transport

    def handle(self, transport: _Transport, raw: str) -> None:
        """React to one frame from the endpoint."""
        if self.silent or transport.closed_code is not None:
            return
        frame = dataclass_from_json(SmartSocketFrame, raw)
        if isinstance(frame, HelloFrame):
            reply = HelloFrame(last_recv=self.recv, policy=self.policy)
            if self.hello_delay > 0:
                task = asyncio.create_task(
                    self._deliver_later(transport, reply, self.hello_delay)
                )
                self._hello_tasks.add(task)
                task.add_done_callback(self._hello_tasks.discard)
            else:
                transport.deliver(reply)
        elif isinstance(frame, MsgFrame):
            if frame.seq <= self.recv:
                return
            if frame.seq != self.recv + 1:
                self.gap = True
                return
            if self.full:
                transport.drop(SS_CLOSE_RELAY_BUFFER_FULL, 'resend buffer full')
                return
            self.recv = frame.seq
            self.accepted.append(_unwrap(frame.payload))
            transport.deliver(AckFrame(recv=self.recv))
        elif isinstance(frame, PingFrame):
            transport.deliver(PongFrame())

    async def _deliver_later(
        self, transport: _Transport, frame: SmartSocketFrame, delay: float
    ) -> None:
        await asyncio.sleep(delay)
        if not self.silent:
            transport.deliver(frame)


class _Transport:
    def __init__(self, relay: _ScriptedRelay) -> None:
        self._relay = relay
        self._inbox: asyncio.Queue[str | tuple[int, str]] = asyncio.Queue()
        self.closed_code: int | None = None
        self.closed_reason = ''

    def deliver(self, frame: SmartSocketFrame) -> None:
        """Relay -> endpoint."""
        if self._relay.silent or self.closed_code is not None:
            return
        self._inbox.put_nowait(dataclass_to_json(frame))

    def drop(self, code: int, reason: str) -> None:
        """The relay closes this connection."""
        if self.closed_code is not None:
            return
        self.closed_code = code
        self.closed_reason = reason
        self._inbox.put_nowait((code, reason))

    async def send(self, data: str) -> None:
        """Endpoint -> relay."""
        if self.closed_code is not None:
            raise SmartSocketClosed(self.closed_code, self.closed_reason)
        self._relay.handle(self, data)

    async def recv(self) -> str:
        """Relay -> endpoint."""
        item = await self._inbox.get()
        if isinstance(item, tuple):
            self._inbox.put_nowait(item)
            raise SmartSocketClosed(*item)
        return item

    async def close(self, code: int = 1000, reason: str = '') -> None:
        """Endpoint closes; the relay learns of it unless black-holed."""
        if self.closed_code is None:
            self.closed_code = code
            self.closed_reason = reason
            self._inbox.put_nowait((code, reason))


@dataclass
class _Run:
    relay: _ScriptedRelay
    endpoint: SmartSocketEndpoint[_Payload, _Payload]
    received: list[str]
    refreshes: int
    anomalies: list[SmartSocketAnomaly]


async def _run_scenario(scenario: dict[str, Any]) -> None:
    pol = scenario['policy']
    policy = SmartSocketEndpointPolicy(
        linger_seconds=pol['lg'],
        ping_interval_seconds=pol['pi'],
        max_duration_seconds=pol['mx'],
    )
    relay = _ScriptedRelay(policy)
    received: list[str] = []
    anomalies: list[SmartSocketAnomaly] = []
    refreshes = [0]

    async def _on_message(message: _Payload) -> None:
        assert isinstance(message, _Text)
        received.append(message.text)

    async def _refresh() -> None:
        refreshes[0] += 1

    endpoint: SmartSocketEndpoint[_Payload, _Payload] = SmartSocketEndpoint(
        relay.connect,
        send_type=_Payload,
        recv_type=_Payload,
        on_message=_on_message,
        refresh=_refresh,
        label='conformance',
        on_anomaly=anomalies.append,
    )
    run_task: asyncio.Task[None] | None = None
    loop = asyncio.get_running_loop()
    name = scenario['name']
    try:
        for step in scenario['steps']:
            delay = step['t'] - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)
            # Let whatever the previous step set in motion land before
            # acting again (free and exact under virtual time).
            await asyncio.sleep(0.001)
            if step['op'] == 'start':
                run_task = asyncio.create_task(endpoint.run())
            elif step['op'] == 'expect':
                _check(
                    f'{name} @ t={step['t']}',
                    step,
                    _Run(relay, endpoint, received, refreshes[0], anomalies),
                )
            else:
                await _apply(name, step, relay, endpoint)
    finally:
        if run_task is not None:
            run_task.cancel()
            await asyncio.gather(run_task, return_exceptions=True)


async def _apply(
    name: str,
    step: dict[str, Any],
    relay: _ScriptedRelay,
    endpoint: SmartSocketEndpoint[_Payload, _Payload],
) -> None:
    """Apply one non-lifecycle step to the relay model or endpoint."""
    op = step['op']
    if op == 'send':
        try:
            await endpoint.send(_Text(text=step['text']))
        except SmartSocketClosed:
            pass
    elif op == 'push':
        assert relay.live is not None
        relay.live.deliver(
            MsgFrame(
                seq=step['seq'],
                payload=dataclass_to_json(_Text(text=step['text'])),
            )
        )
    elif op == 'drop':
        assert relay.live is not None
        relay.live.drop(step['code'], 'scripted')
    elif op == 'refuse':
        relay.refuse_count = step['count']
    elif op == 'reject':
        relay.reject_with = step['code']
    elif op == 'silent':
        relay.silent = step['on']
    elif op == 'full':
        relay.full = step['on']
    elif op == 'hello_delay':
        relay.hello_delay = step['seconds']
    else:
        raise ValueError(f'unknown op {op!r} in {name} @ t={step['t']}')


def _check(where: str, exp: dict[str, Any], run: _Run) -> None:
    ep = run.endpoint
    if 'connects' in exp:
        assert (
            run.relay.connects == exp['connects']
        ), f'{where}: connects {run.relay.connects} != {exp['connects']}'
    if 'connects_min' in exp:
        assert (
            run.relay.connects >= exp['connects_min']
        ), f'{where}: connects {run.relay.connects} < {exp['connects_min']}'
    if 'connects_max' in exp:
        assert (
            run.relay.connects <= exp['connects_max']
        ), f'{where}: connects {run.relay.connects} > {exp['connects_max']}'
    if 'dead' in exp:
        if exp['dead'] is None:
            assert not ep.done, (
                f'{where}: dead ({ep.close_code} {ep.close_reason!r}),'
                f' expected alive'
            )
        else:
            assert ep.done, f'{where}: alive, expected dead {exp['dead']}'
            assert ep.close_code == exp['dead'], (
                f'{where}: dead with {ep.close_code} ({ep.close_reason!r}),'
                f' expected {exp['dead']}'
            )
            assert ep.close_reason, f'{where}: a death must carry a reason'
    if 'connected' in exp:
        assert (
            ep.connected == exp['connected']
        ), f'{where}: connected={ep.connected}'
    if 'received' in exp:
        assert run.received == exp['received'], f'{where}: {run.received}'
    if 'accepted' in exp:
        assert (
            run.relay.accepted == exp['accepted']
        ), f'{where}: {run.relay.accepted}'
    if 'refreshes' in exp:
        assert run.refreshes == exp['refreshes'], f'{where}: {run.refreshes}'
    if 'anomaly' in exp:
        kinds = [a.kind.value for a in run.anomalies]
        if exp['anomaly'] is None:
            assert not kinds, f'{where}: unexpected anomaly {kinds}'
        else:
            assert kinds == [exp['anomaly']], f'{where}: anomalies {kinds}'
    assert run.relay.gap == exp.get('gap', False), (
        f'{where}: relay saw a sequence gap'
        if run.relay.gap
        else f'{where}: expected a gap and saw none'
    )


def test_close_code_actions_match_the_table() -> None:
    """The table is the contract; the range logic must reproduce it."""
    for code, action in _table()['close_code_actions']:
        assert action_for_close_code(code) is SmartSocketAction(action), (
            f'code {code}: {action_for_close_code(code).value},'
            f' table says {action}'
        )


@pytest.mark.parametrize(
    'scenario', _table()['scenarios'], ids=lambda s: str(s['name'])
)
def test_scenario(
    scenario: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """One table row, under virtual time with jitter pinned to zero."""
    monkeypatch.setattr(efro.smartsocket, '_jitter', lambda: 0.0)
    # Fresh churn state per scenario; it is module-global by design.
    monkeypatch.setattr(efro.smartsocket, '_churn_deaths', {})
    monkeypatch.setattr(efro.smartsocket, '_churn_reported', {})
    run_virtual(_run_scenario(scenario), limit_seconds=4 * 3600.0)
