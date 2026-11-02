# Released under the MIT License. See LICENSE for details.
#
"""Nearby-discovery scenarios on a simulated network and clock.

Drives the real discovery protocol (``babase._nearbyimpl``) with no
sockets, threads or waiting: a fake event loop runs its timers on a
fake clock, and simulated hosts answer its queries the way real games
do (v2 hosts with their uuid, legacy hosts in the v1 forms only).
DNS-SD results and broadcast addresses come from a stand-in for the
native layer.

This needs the engine's Python environment (``babase`` won't import
without it), so ``test_nearby_discovery.py`` runs it inside the engine
binary; see there. Each scenario is a function raising
``AssertionError`` on failure.
"""

# (A test harness for internals; it pokes at them throughout.)
# pylint: disable=protected-access

import json
import time
import heapq
import struct
import traceback
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast, override

import _babase
from babase import NearbyService, NearbySource
from babase import _nearbyimpl as impl
from babase._dualstack import DualStackUDPEndpoint
from babase._nearbyroutes import RouteState, HostState, update_best_route

if TYPE_CHECKING:
    import asyncio
    from typing import Callable

    from babase import NearbyHost

SELF_UUID = 'self-uuid'
PORT = impl.GAME_PORT
BROADCAST_ADDR = '192.168.4.255'
GAME_TYPE = '_bagame._udp'
REMOTE_TYPE = '_baremote._udp'
START_TIME = 1000.0

# Timing expectations. These are generous on purpose: they say what a
# player would call broken, not what the current tuning happens to do.

# A host's best route dying with a working spare: switched within this.
FAILOVER_LIMIT = 12.0

# A much faster route appearing: made best within this (best routes are
# picked once a cycle).
FASTER_ROUTE_LIMIT = impl._CYCLE_INTERVAL_STABLE + 0.5

# A host leaving the network: gone from the list within this.
VANISH_LIMIT = 15.0

# A host appearing while the scan is stable (slow cycle): listed within
# this when heard about via broadcast, and via DNS-SD.
LATE_BROADCAST_LIMIT = impl._CYCLE_INTERVAL_STABLE + 0.5
LATE_DNS_SD_LIMIT = 0.5

# Packets per second sent once stable, for one host with two routes
# plus six advertised addresses that never answer.
STEADY_TRAFFIC_LIMIT = 4.0


class SimClock:
    """Stands in for the time module (only monotonic() is used)."""

    def __init__(self) -> None:
        self.now = START_TIME

    def monotonic(self) -> float:
        """The simulated time."""
        return self.now


class SimHandle:
    """A scheduled callback (the bits of TimerHandle used)."""

    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        """Don't run it after all."""
        self.cancelled = True


class SimLoop:
    """The bits of an asyncio loop the protocol uses, on a fake clock."""

    def __init__(self, clock: SimClock) -> None:
        self._clock = clock
        self._seq = 0
        self._events: list[tuple[float, int, SimHandle, Callable[[], None]]] = (
            []
        )

    def call_later[*Ts](
        self, delay: float, callback: Callable[[*Ts], None], *args: *Ts
    ) -> SimHandle:
        """Schedule a callback."""
        handle = SimHandle()
        self._seq += 1
        heapq.heappush(
            self._events,
            (
                self._clock.now + delay,
                self._seq,
                handle,
                lambda: callback(*args),
            ),
        )
        return handle

    def run_until(
        self, end: float, stop: Callable[[], bool] | None = None
    ) -> bool:
        """Run everything due by ``end`` (or until ``stop`` is true).

        Returns whether ``stop`` ended it (leaving the clock at the
        moment it became true).
        """
        while self._events and self._events[0][0] <= end:
            when, _seq, handle, callback = heapq.heappop(self._events)
            if handle.cancelled:
                continue
            self._clock.now = when
            callback()
            if stop is not None and stop():
                return True
        self._clock.now = end
        return False


class SimNative:
    """Stands in for the native calls discovery makes."""

    def __init__(self) -> None:
        self.browse_supported = True
        self.browsing: list[str] | None = None
        self.broadcast_addrs = [BROADCAST_ADDR]
        self.events: list[
            tuple[bool, str, str, str, str, int, dict[str, str]]
        ] = []

    def nearby_service_types(self) -> tuple[str, str]:
        """DNS-SD service types (game, remote)."""
        return GAME_TYPE, REMOTE_TYPE

    def nearby_browse_supported(self) -> bool:
        """Whether DNS-SD browsing works here."""
        return self.browse_supported

    def nearby_browse_start(self, types: list[str]) -> int:
        """Start browsing; results are polled for (as on Windows)."""
        self.browsing = types
        return impl._BROWSE_NO_DESCRIPTOR

    def nearby_browse_stop(self) -> None:
        """Stop browsing."""
        self.browsing = None

    def nearby_browse_process(
        self,
    ) -> list[tuple[bool, str, str, str, str, int, dict[str, str]]]:
        """Collect browse results."""
        events, self.events = self.events, []
        return events

    def nearby_broadcast_addrs(self) -> list[str]:
        """Each interface's subnet broadcast address."""
        return list(self.broadcast_addrs)


@dataclass
class SimHost:
    """A game on the simulated network.

    ``addrs`` maps each address it answers at to its round trip there:
    a number, or a list cycled through answer by answer (for jitter).
    """

    uuid: str
    addrs: dict[str, float | list[float]]
    services: frozenset[NearbyService] = frozenset({NearbyService.GAME})

    #: Whether it speaks the v2 protocol (else it's a legacy build that
    #: only answers v1 queries, and never says its uuid).
    v2: bool = True
    name: str = 'Sim Host'

    #: Addresses it's currently not answering at.
    down: set[str] = field(default_factory=set)

    #: Addresses whose next answer gets lost.
    drop_next: set[str] = field(default_factory=set)
    answers: int = 0

    def rtt(self, addr: str) -> float:
        """The round trip for an answer from ``addr``."""
        val = self.addrs[addr]
        if isinstance(val, list):
            return val[self.answers % len(val)]
        return val

    def answer(self, data: bytes) -> bytes | None:
        """What it says back to a query (None for nothing)."""
        ptype = data[0]
        game = NearbyService.GAME in self.services
        remote = NearbyService.REMOTE in self.services
        qid = struct.unpack_from('<I', data, 1)[0] if len(data) >= 5 else 0
        if ptype == impl._HOST_QUERY_V2 and game and self.v2:
            return _v2_packet(
                impl._HOST_QUERY_RESPONSE_V2,
                qid,
                {'i': self.uuid, 's': '{}', 'n': self.name, 'b': 2, 'p': 1},
            )
        if ptype == impl._HOST_QUERY and game:
            uuid = self.uuid.encode()
            spec = b'{}'
            return (
                struct.pack(
                    '<BIIBB',
                    impl._HOST_QUERY_RESPONSE,
                    qid,
                    1,
                    len(uuid),
                    len(spec),
                )
                + uuid
                + spec
            )
        if ptype == impl._REMOTE_GAME_QUERY_V2 and remote and self.v2:
            return _v2_packet(
                impl._REMOTE_GAME_RESPONSE_V2,
                qid,
                {'i': self.uuid, 'n': self.name, 'b': 2},
            )
        if ptype == impl._REMOTE_GAME_QUERY and remote:
            return (
                bytes([impl._REMOTE_GAME_RESPONSE]) + self.name.encode() + b'\0'
            )
        return None


def _v2_packet(ptype: int, qid: int, info: dict[str, str | int]) -> bytes:
    return struct.pack('<BI', ptype, qid) + json.dumps(info).encode()


class SimEndpoint(DualStackUDPEndpoint):
    """Sends into the simulated network instead of real sockets."""

    def __init__(self, sim: Sim) -> None:
        super().__init__(sim.proto.datagram_received, sim.proto.error_received)
        self._sim = sim

    @override
    def sendto(self, data: bytes, addr: tuple[str, int]) -> None:
        self._sim.on_send(data, addr)

    @override
    def close(self) -> None:
        pass


class Sim:
    """A discovery protocol on a simulated network."""

    def __init__(
        self,
        services: frozenset[NearbyService] = frozenset({NearbyService.GAME}),
        *,
        open_scan: bool = True,
        targets: frozenset[tuple[str, int]] = frozenset(),
    ) -> None:
        self.clock = SimClock()
        self.loop = SimLoop(self.clock)
        self.native = SimNative()
        self.hosts: list[SimHost] = []
        self.posted: list[NearbyHost] = []
        self.ever_posted_keys: set[str] = set()

        # (time, address) of every send.
        self.sends: list[tuple[float, tuple[str, int]]] = []
        self.broadcasts = 0

        # The protocol reads the clock as it's built, so it must already
        # see ours. (Otherwise the first sim of a run gets the real
        # monotonic time, which is behind our clock on a freshly booted
        # machine such as a CI runner, so it thinks it's been stable for
        # ages and starts out on the slow cycle.)
        _patch(self)
        self.proto = impl._DiscoveryProtocol(
            # (Our stand-in has only the parts of a loop it uses.)
            loop=cast('asyncio.AbstractEventLoop', self.loop),
            config=impl.DiscoveryConfig(
                services=services, open_scan=open_scan, targets=targets
            ),
            post=self._on_post,
            self_uuid=SELF_UUID,
            build_number=1,
        )
        self._endpoint = SimEndpoint(self)

    # -- Driving it -------------------------------------------------------

    def start(self) -> None:
        """Start discovery (as the discovery thread does)."""
        _patch(self)
        self.proto.begin(self._endpoint)

    def run(self, seconds: float) -> None:
        """Let time pass."""
        _patch(self)
        self.loop.run_until(self.clock.now + seconds)

    def wait_for(self, cond: Callable[[], bool], limit: float) -> float | None:
        """Run until ``cond`` holds; return how long that took (or None)."""
        _patch(self)
        start = self.clock.now
        if cond():
            return 0.0
        if self.loop.run_until(start + limit, cond):
            return self.clock.now - start
        return None

    def advertise(self, host: SimHost, addr: str) -> None:
        """Have DNS-SD report ``host`` at ``addr``."""
        self.native.events.append(
            (True, GAME_TYPE, f'{host.uuid}-inst', host.name, addr, PORT, {})
        )

    # -- Looking at it ----------------------------------------------------

    @property
    def interval(self) -> float:
        """The protocol's current cycle interval."""
        return self.proto._interval

    def host(self, key: str) -> NearbyHost | None:
        """The listed host with ``key``, if any."""
        for host in self.posted:
            if host.key == key:
                return host
        return None

    def best(self, key: str) -> str | None:
        """The address of a listed host's best route."""
        host = self.host(key)
        return None if host is None else host.route.address

    def packets_since(self, start: float) -> int:
        """Packets sent since ``start``."""
        return sum(1 for when, _ in self.sends if when >= start)

    # -- Internals --------------------------------------------------------

    def _on_post(self, hosts: list[NearbyHost]) -> None:
        self.posted = hosts
        self.ever_posted_keys.update(h.key for h in hosts)

    def on_send(self, data: bytes, addr: tuple[str, int]) -> None:
        """The protocol sent a datagram."""
        self.sends.append((self.clock.now, addr))
        ip, port = addr
        if port != PORT:
            return
        if ip in self.native.broadcast_addrs:
            self.broadcasts += 1
            for host in self.hosts:
                for haddr in host.addrs:
                    if ':' not in haddr:
                        self._answer(host, haddr, data)
            return
        for host in self.hosts:
            if ip in host.addrs:
                self._answer(host, ip, data)

    def _answer(self, host: SimHost, addr: str, data: bytes) -> None:
        if addr in host.down:
            return
        reply = host.answer(data)
        if reply is None:
            return
        if addr in host.drop_next:
            host.drop_next.discard(addr)
            return
        rtt = host.rtt(addr)
        host.answers += 1
        self.loop.call_later(
            rtt, self.proto.datagram_received, reply, (addr, PORT)
        )


_g_active: Sim | None = None


def _patch(sim: Sim) -> None:
    """Point the discovery module at ``sim``'s clock and native layer."""
    global _g_active  # pylint: disable=global-statement
    if _g_active is not sim:
        setattr(impl, 'time', sim.clock)
        setattr(impl, '_babase', sim.native)
        _g_active = sim


def _stable_sim(*hosts: SimHost, advertise: bool = True) -> Sim:
    """A sim with these hosts, run until its cycle has slowed down."""
    sim = Sim()
    sim.hosts.extend(hosts)
    sim.start()
    if advertise:
        for host in hosts:
            for addr in host.addrs:
                sim.advertise(host, addr)
    sim.run(impl._STABLE_AFTER + 10.0)
    assert sim.interval == impl._CYCLE_INTERVAL_STABLE, sim.interval
    return sim


# -- Scenarios ---------------------------------------------------------------

SCENARIOS: dict[str, Callable[[], None]] = {}


def scenario[T: Callable[[], None]](func: T) -> T:
    """Register a scenario."""
    SCENARIOS[func.__name__] = func
    return func


def _two_route_host(uuid: str = 'host-a') -> SimHost:
    # A fast link-local IPv6 path and a slower IPv4 one.
    return SimHost(
        uuid=uuid, addrs={'fe80::a%en0': 0.005, '192.168.4.10': 0.020}
    )


@scenario
def dedupe_and_rank() -> None:
    """One host on two addresses is one entry; fastest route first."""
    sim = Sim()
    host = _two_route_host()
    sim.hosts.append(host)
    sim.start()
    for addr in host.addrs:
        sim.advertise(host, addr)
    sim.run(3.0)
    assert [h.key for h in sim.posted] == ['host-a'], sim.posted
    listed = sim.posted[0]
    assert listed.route.address == 'fe80::a%en0', listed.route
    assert len(listed.routes) == 2, listed.routes
    assert listed.route.rtt == 0.005, listed.route
    assert listed.game is not None and listed.game.party_name == 'Sim Host'
    by_addr = {r.address: r for r in listed.routes}
    assert by_addr['192.168.4.10'].sources == {
        NearbySource.BROADCAST,
        NearbySource.DNS_SD,
    }, by_addr
    assert by_addr['fe80::a%en0'].sources == {NearbySource.DNS_SD}, by_addr


@scenario
def ipv4_wins_ties() -> None:
    """Equally fast IPv4 and IPv6 routes: IPv4 is best."""
    sim = Sim()
    host = SimHost(
        uuid='host-a', addrs={'fd00::a': 0.010, '192.168.4.10': 0.010}
    )
    sim.hosts.append(host)
    sim.start()
    for addr in host.addrs:
        sim.advertise(host, addr)
    sim.run(5.0)
    assert sim.best('host-a') == '192.168.4.10', sim.posted


@scenario
def near_equal_routes_dont_flap() -> None:
    """Jittery routes of similar speed don't keep swapping best."""
    sim = Sim()
    host = SimHost(
        uuid='host-a',
        addrs={
            'fd00::a': [0.008, 0.014, 0.010, 0.016],
            'fd00::b': [0.015, 0.009, 0.013, 0.007],
        },
    )
    sim.hosts.append(host)
    sim.start()
    for addr in host.addrs:
        sim.advertise(host, addr)
    bests: list[str] = []
    end = sim.clock.now + 60.0
    while sim.clock.now < end:
        sim.run(0.5)
        best = sim.best('host-a')
        if best is not None and (not bests or bests[-1] != best):
            bests.append(best)
    assert len(bests) == 1, bests


@scenario
def faster_route_takes_over() -> None:
    """A much faster path showing up becomes the best one promptly."""
    sim = Sim()
    host = SimHost(uuid='host-a', addrs={'192.168.4.10': 0.030})
    sim.hosts.append(host)
    sim.start()
    sim.run(20.0)
    assert sim.best('host-a') == '192.168.4.10', sim.posted

    # A cable gets plugged in.
    host.addrs['fe80::a%en5'] = 0.002
    sim.advertise(host, 'fe80::a%en5')
    # (It gets measured at once, but best routes are only picked each
    # cycle.)
    took = sim.wait_for(
        lambda: sim.best('host-a') == 'fe80::a%en5', FASTER_ROUTE_LIMIT
    )
    assert took is not None, sim.posted
    measure('faster route took over (s)', took)


@scenario
def failover_to_spare() -> None:
    """The best route dying hands over to the spare, host stays listed."""
    host = _two_route_host()
    sim = _stable_sim(host)
    assert sim.best('host-a') == 'fe80::a%en0'
    host.down.add('fe80::a%en0')
    vanished = False

    def switched() -> bool:
        nonlocal vanished
        if sim.host('host-a') is None:
            vanished = True
        return sim.best('host-a') == '192.168.4.10'

    took = sim.wait_for(switched, FAILOVER_LIMIT)
    assert took is not None, sim.posted
    assert not vanished
    measure('failover to spare (s)', took)


@scenario
def lost_answer_with_spare_stays_calm() -> None:
    """One lost answer, with the host answering elsewhere: no fuss.

    The best route stays put and the cycle doesn't go back to full rate
    (a lost probe on Wi-Fi is routine; full-rate bursts for it were
    measured as needless traffic).
    """
    host = _two_route_host()
    sim = _stable_sim(host)
    host.drop_next.add('fe80::a%en0')
    end = sim.clock.now + 15.0
    while sim.clock.now < end:
        sim.run(0.1)
        assert sim.best('host-a') == 'fe80::a%en0', sim.posted
        assert sim.interval == impl._CYCLE_INTERVAL_STABLE, sim.clock.now


@scenario
def lost_answer_alone_goes_full_rate() -> None:
    """A lone route missing an answer: back to full rate, host kept."""
    # (IPv6, so broadcast answers can't keep the route fresh.)
    host = SimHost(uuid='host-a', addrs={'fd00::a': 0.010})
    sim = _stable_sim(host)
    host.drop_next.add('fd00::a')

    # (Up to a cycle until the probe whose answer gets lost, and another
    # until it counts as missed.)
    took = sim.wait_for(
        lambda: sim.interval == impl._CYCLE_INTERVAL,
        2.0 * impl._CYCLE_INTERVAL_STABLE + 0.5,
    )
    assert took is not None
    assert sim.host('host-a') is not None

    # And once it's answering again things settle back down.
    took = sim.wait_for(
        lambda: sim.interval == impl._CYCLE_INTERVAL_STABLE,
        impl._STABLE_AFTER + 5.0,
    )
    assert took is not None
    assert sim.host('host-a') is not None


@scenario
def vanished_host_dropped() -> None:
    """A host that leaves is gone from the list promptly."""
    host = _two_route_host()
    sim = _stable_sim(host)
    host.down.update(host.addrs)
    took = sim.wait_for(lambda: sim.host('host-a') is None, VANISH_LIMIT)
    assert took is not None, sim.posted
    measure('vanished host dropped (s)', took)


@scenario
def late_host_found_via_broadcast() -> None:
    """A host arriving while things are stable shows up within a cycle."""
    sim = _stable_sim(_two_route_host())
    sim.hosts.append(SimHost(uuid='host-b', addrs={'192.168.4.20': 0.010}))
    took = sim.wait_for(
        lambda: sim.host('host-b') is not None, LATE_BROADCAST_LIMIT
    )
    assert took is not None, sim.posted
    measure('late host found via broadcast (s)', took)


@scenario
def late_host_found_via_dns_sd() -> None:
    """DNS-SD news of a host gets it probed (and listed) right away."""
    sim = _stable_sim(_two_route_host())
    host_b = SimHost(uuid='host-b', addrs={'fd00::b': 0.010})
    sim.hosts.append(host_b)
    sim.advertise(host_b, 'fd00::b')
    took = sim.wait_for(
        lambda: sim.host('host-b') is not None, LATE_DNS_SD_LIMIT
    )
    assert took is not None, sim.posted
    measure('late host found via DNS-SD (s)', took)


@scenario
def steady_state_traffic() -> None:
    """Once stable, probing stays light even with dead addresses."""
    host = _two_route_host()
    sim = _stable_sim(host)
    dead = SimHost(uuid='never', addrs={})
    for i in range(6):
        sim.advertise(dead, f'fe80::dead{i}%en{i}')
    sim.run(30.0)
    start = sim.clock.now
    sim.run(60.0)
    rate = sim.packets_since(start) / 60.0
    measure('steady-state packets/s', rate)
    assert rate <= STEADY_TRAFFIC_LIMIT, rate
    assert sim.host('host-a') is not None


@scenario
def dead_candidate_backs_off() -> None:
    """An advertised address that never answers is probed less and less."""
    sim = Sim()
    sim.start()
    dead = ('fe80::dead%en0', PORT)
    sim.advertise(SimHost(uuid='never', addrs={}), dead[0])
    sim.run(60.0)
    times: list[float] = []
    for when, addr in sim.sends:
        if addr == dead and (not times or when > times[-1]):
            times.append(when)
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert gaps, times
    for prev, gap in zip(gaps, gaps[1:]):
        assert gap >= prev - 0.01, gaps
    # (Probes only go out on cycle ticks, so the cap can round up by
    # one cycle.)
    cap = impl._CANDIDATE_MAX_BACKOFF + impl._CYCLE_INTERVAL_STABLE
    assert max(gaps) <= cap + 0.01, gaps
    assert gaps[-1] >= impl._CANDIDATE_MAX_BACKOFF - 0.01, gaps
    measure('dead address probe gaps (s)', gaps)


@scenario
def legacy_hosts_listed() -> None:
    """Old builds (v1 answers only) still show up, games and remotes."""
    sim = Sim(frozenset({NearbyService.GAME, NearbyService.REMOTE}))
    sim.hosts.append(
        SimHost(
            uuid='old-game',
            addrs={'192.168.4.30': 0.010},
            v2=False,
        )
    )
    sim.hosts.append(
        SimHost(
            uuid='old-remote',
            addrs={'192.168.4.31': 0.010},
            services=frozenset({NearbyService.REMOTE}),
            v2=False,
            name='Old Phone',
        )
    )
    sim.start()
    sim.run(3.0)
    game = sim.host('old-game')
    assert game is not None and game.game is not None, sim.posted
    assert game.game.protocol_version == 1, game.game
    # (v1 game answers do echo our query id, so round trips work.)
    assert game.route.rtt == 0.010, game.route
    remote = sim.host('legacy:192.168.4.31:43210')
    assert remote is not None and remote.remote is not None, sim.posted
    assert remote.remote.name == 'Old Phone', remote.remote


@scenario
def remote_v1_answer_first_no_duplicate() -> None:
    """A new host's v1 remote answer beating its v2 one: one entry.

    (Seen with a DNS-SD-found Android host; it briefly showed up twice,
    and its route got credited to broadcast.)
    """
    sim = Sim(frozenset({NearbyService.REMOTE}), open_scan=False)
    host = SimHost(
        uuid='pixel',
        addrs={'fdd4::7a64': 0.010},
        services=frozenset({NearbyService.REMOTE}),
    )
    sim.hosts.append(host)
    sim.start()

    # Treat it as advertised (as open scans do), then have its v1
    # answer land before anything else.
    cand = sim.proto._candidates.setdefault(
        ('fdd4::7a64', PORT), impl._Candidate()
    )
    cand.sources.add(NearbySource.DNS_SD)
    cand.instances.add('pixel-inst')
    sim.proto.datagram_received(
        bytes([impl._REMOTE_GAME_RESPONSE]) + b'Pixel\0', ('fdd4::7a64', PORT)
    )
    sim.run(3.0)
    assert [h.key for h in sim.posted] == ['pixel'], sim.posted
    assert sim.posted[0].route.sources == {NearbySource.DNS_SD}
    assert not any(k.startswith('legacy:') for k in sim.ever_posted_keys)


@scenario
def remote_v2_replaces_legacy_twin() -> None:
    """A host answering v1 and v2 remote queries ends up listed once."""
    sim = Sim(frozenset({NearbyService.REMOTE}))
    sim.hosts.append(
        SimHost(
            uuid='phone',
            addrs={'192.168.4.40': 0.010},
            services=frozenset({NearbyService.REMOTE}),
        )
    )
    sim.start()
    sim.run(3.0)
    assert [h.key for h in sim.posted] == ['phone'], sim.posted


@scenario
def ignores_self_and_garbage() -> None:
    """Our own answers and malformed packets list nothing."""
    sim = Sim(frozenset({NearbyService.GAME, NearbyService.REMOTE}))
    sim.hosts.append(SimHost(uuid=SELF_UUID, addrs={'192.168.4.50': 0.001}))
    sim.start()
    addr = ('192.168.4.60', PORT)
    for junk in [
        b'',
        b'\x00',
        bytes([impl._HOST_QUERY_RESPONSE_V2]),
        bytes([impl._HOST_QUERY_RESPONSE_V2]) + b'\0\0\0\0{not json',
        bytes([impl._HOST_QUERY_RESPONSE_V2]) + b'\0\0\0\0[1, 2]',
        bytes([impl._HOST_QUERY_RESPONSE_V2]) + b'\0\0\0\0{"i": 5}',
        bytes([impl._HOST_QUERY_RESPONSE]) + b'\0' * 12,
        bytes([impl._REMOTE_GAME_RESPONSE_V2]) + b'\0\0\0\0{"n": "x"}',
        bytes(range(256)),
    ]:
        sim.proto.datagram_received(junk, addr)
    sim.run(3.0)
    assert not sim.posted, sim.posted


@scenario
def targets_only() -> None:
    """A targeted scan probes just its targets: no broadcast or DNS-SD."""
    target = ('192.168.4.70', PORT)
    sim = Sim(open_scan=False, targets=frozenset({target}))
    sim.hosts.append(SimHost(uuid='wanted', addrs={target[0]: 0.010}))
    sim.hosts.append(SimHost(uuid='other', addrs={'192.168.4.71': 0.010}))
    sim.start()
    sim.run(5.0)
    assert sim.broadcasts == 0
    assert sim.native.browsing is None
    assert [h.key for h in sim.posted] == ['wanted'], sim.posted
    assert sim.posted[0].route.sources == {NearbySource.TARGET}


def _route(addr: str, srtt: float, now: float) -> RouteState:
    return RouteState(
        address=addr, port=PORT, last_heard=now, srtt=srtt, last_probe=now
    )


@scenario
def quiet_best_route_news() -> None:
    """A quiet best route is only 'news' if the host is quiet elsewhere.

    (News sends everything back to full-rate probing.)
    """
    now = 100.0
    for spare_missed, expect_news in [(0, False), (1, True)]:
        best = _route('fd00::a', 0.005, now - 10.0)
        spare = _route('192.168.4.10', 0.020, now - 10.0)
        host = HostState(
            key='h',
            routes={('fd00::a', PORT): best, ('192.168.4.10', PORT): spare},
            best=('fd00::a', PORT),
        )
        # The best route has missed enough probes to be stale.
        best.unanswered = 3
        spare.unanswered = spare_missed
        news = update_best_route(host, now)
        assert host.best == ('192.168.4.10', PORT), host.best
        assert news is expect_news, (spare_missed, news)


_g_measurements: dict[str, float | list[float]] = {}


def measure(what: str, value: float | list[float]) -> None:
    """Note a timing or rate (reported alongside the results)."""
    _g_measurements[what] = (
        round(value, 3)
        if isinstance(value, float)
        else [round(v, 3) for v in value]
    )


def run_all(outpath: str) -> None:
    """Run every scenario, writing what happened to ``outpath``.

    That's json: ``results`` maps each scenario to its error (or None),
    and ``measurements`` holds the timings and rates noted along the
    way.
    """
    results: dict[str, str | None] = {}
    try:
        for name, func in SCENARIOS.items():
            try:
                func()
                results[name] = None
            except Exception:
                results[name] = traceback.format_exc()
    finally:
        setattr(impl, 'time', time)
        setattr(impl, '_babase', _babase)
    with open(outpath, 'w', encoding='utf-8') as outfile:
        json.dump(
            {'results': results, 'measurements': _g_measurements},
            outfile,
            indent=2,
        )
