# Released under the MIT License. See LICENSE for details.
#
"""Nearby discovery internals: the discovery thread and its protocol.

This is an internal module; the api is in babase._nearby.

Producers (subnet broadcast, DNS-SD browsing, explicit targets) only
ever yield *candidate* addresses. A host is listed once it answers a
query at one of them, and every query carries an id it echoes, so each
answer is also a round-trip-time sample for that route. Each host then
keeps its routes ranked by smoothed round-trip time (plus a per-type
bias), switching its best route only when another is clearly better.
"""

import json
import time
import random
import struct
import asyncio
import logging
import weakref
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from efro.util import strip_exception_tracebacks

import _babase
from babase._dualstack import DualStackUDPEndpoint
from babase._nearby import (
    NearbyService,
    NearbySource,
    NearbyGameInfo,
    NearbyRemoteInfo,
    NearbyHost,
)
from babase._nearbyroutes import (
    ROUTE_STALE_MISSES,
    answering_elsewhere,
    RouteState,
    HostState,
    route_score,
    update_best_route,
    public_route,
)

if TYPE_CHECKING:
    from typing import Any, Callable

logger = logging.getLogger('ba.net')

# The game's well-known UDP port (kDefaultPort in C++).
GAME_PORT = 43210

# Packet types (BA_PACKET_* in networking.h).
_HOST_QUERY = 22
_HOST_QUERY_RESPONSE = 23
_HOST_QUERY_V2 = 38
_HOST_QUERY_RESPONSE_V2 = 39
_REMOTE_GAME_QUERY = 8
_REMOTE_GAME_RESPONSE = 9
_REMOTE_GAME_QUERY_V2 = 42
_REMOTE_GAME_RESPONSE_V2 = 43

# How often we broadcast and probe each host's best route. Once nothing
# has changed for _STABLE_AFTER seconds this stretches to the longer
# value, snapping back on any change (a new host or route, a best-route
# switch, a lost host, new orders).
_CYCLE_INTERVAL = 1.0
_CYCLE_INTERVAL_STABLE = 3.0
_STABLE_AFTER = 10.0

# How often a host's other (spare) routes are probed. They're only there
# to notice a better path or take over if the best one dies.
_SPARE_PROBE_INTERVAL = 5.0

# A candidate address that never answers is probed less and less often:
# its interval doubles from _CYCLE_INTERVAL up to this. (Fresh DNS-SD
# news about it resets that.)
_CANDIDATE_MAX_BACKOFF = 5.0

# A route that has missed this many probes in a row is dropped (and a
# host with no routes left goes with it); see ROUTE_STALE_MISSES for
# when it stops being a best-route contender. Counting misses rather
# than time keeps a slowed-down cycle from slowing failover: a host
# whose best route misses even one probe gets all its routes probed at
# full rate again until it recovers.
_ROUTE_DROP_MISSES = 4
assert _ROUTE_DROP_MISSES > ROUTE_STALE_MISSES

# How often to log probe-traffic stats (at DEBUG).
_STATS_INTERVAL = 10.0

# Query ids older than this no longer count for round-trip times.
_QUERY_TIMEOUT = 3.0

# What nearby_browse_start() returns where there's no descriptor to
# wait on (kNearbyBrowseNoDescriptor), and how often we then collect.
_BROWSE_NO_DESCRIPTOR = -2
_BROWSE_POLL_INTERVAL = 0.25

# Smoothing for round-trip times (weight of each new sample).
_RTT_ALPHA = 0.25

# How long stop() waits for the thread. It never blocks on anything,
# so this only guards against a bug.
_STOP_TIMEOUT = 2.0


@dataclass(frozen=True)
class DiscoveryConfig:
    """What the discovery thread should be doing."""

    services: frozenset[NearbyService]

    #: Whether to broadcast and browse (vs. only probing targets).
    open_scan: bool

    targets: frozenset[tuple[str, int]]


class NearbyDiscoveryThread:
    """Runs discovery on its own thread with its own asyncio loop.

    The logic thread creates, configures, and stops this; results come
    back to it via ``on_hosts`` (called in the logic thread).
    """

    def __init__(
        self,
        config: DiscoveryConfig,
        on_hosts: Callable[[NearbyDiscoveryThread, list[NearbyHost]], None],
    ) -> None:
        import babase

        self._loop = asyncio.new_event_loop()
        self._stop_event = asyncio.Event()

        # Results land in the logic thread through a weak call, so a
        # pending one doesn't keep anything alive. (The poster holds us
        # weakly too: our protocol keeps it, so a strong reference would
        # be a cycle.)
        on_hosts_weak = babase.WeakCallPartial(on_hosts)
        self_ref = weakref.ref(self)

        def _post(hosts: list[NearbyHost]) -> None:
            thread = self_ref()
            if thread is None:
                return
            babase.pushcall(
                babase.CallStrict(on_hosts_weak, thread, hosts),
                from_other_thread=True,
            )

        self._protocol = _DiscoveryProtocol(
            loop=self._loop,
            config=config,
            post=_post,
            self_uuid=_babase.app_instance_uuid(),
            build_number=babase.app.env.engine_build_number,
        )
        self._thread = threading.Thread(
            target=self._thread_main, name='nearby-discovery'
        )

    def start(self) -> None:
        """Start the thread."""
        self._thread.start()

    def set_config(self, config: DiscoveryConfig) -> None:
        """Change what we're looking for."""
        try:
            self._loop.call_soon_threadsafe(self._protocol.set_config, config)
        except RuntimeError:
            pass  # Loop already closed.

    def stop(self) -> None:
        """Stop and wait for the thread to exit."""
        try:
            self._loop.call_soon_threadsafe(self._stop_event.set)
        except RuntimeError:
            pass  # Loop already closed (thread exited on its own).
        self._thread.join(timeout=_STOP_TIMEOUT)
        if self._thread.is_alive():
            logger.error('Nearby discovery thread did not exit in time.')

    def _thread_main(self) -> None:
        loop = self._loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
        except Exception as exc:
            logger.exception('Nearby discovery thread failed.')
            strip_exception_tracebacks(exc)
        finally:
            loop.close()

    async def _run(self) -> None:
        protocol = self._protocol
        endpoint = DualStackUDPEndpoint(
            on_datagram=protocol.datagram_received,
            on_error=protocol.error_received,
        )
        if not await endpoint.open():
            logger.warning('Nearby discovery: could not open sockets.')
            return
        protocol.begin(endpoint)
        await self._stop_event.wait()
        protocol.end()

        # Let the transports' close callbacks run before the loop goes.
        await asyncio.sleep(0)


@dataclass(frozen=True)
class _Query:
    """A query we sent, kept until answered or forgotten."""

    sent: float

    # How its target was found (credited to whatever answers it).
    sources: frozenset[NearbySource]

    # Where it went (for debug logging).
    target: str


@dataclass
class _Candidate:
    """An address some producer thinks a host may be at."""

    sources: set[NearbySource] = field(default_factory=set)

    # DNS-SD instances vouching for this address.
    instances: set[str] = field(default_factory=set)

    # Probe schedule while it isn't (yet) a route: unanswered probes so
    # far, and when the next is due.
    misses: int = 0
    next_probe: float = 0.0


class _DiscoveryProtocol:
    """The discovery logic; lives entirely on the discovery thread."""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        config: DiscoveryConfig,
        post: Callable[[list[NearbyHost]], None],
        self_uuid: str,
        build_number: int,
    ) -> None:
        self._loop = loop
        self._config = config
        self._post = post
        self._self_uuid = self_uuid

        # What v2 queries say about us.
        self._query_json = json.dumps(
            {'b': build_number, 'v': 1}, separators=(',', ':')
        ).encode()
        self._endpoint: DualStackUDPEndpoint | None = None
        self._running = False

        # Queries awaiting answers, by id.
        self._queries: dict[int, _Query] = {}
        self._next_query_id = random.randrange(1 << 32)

        self._candidates: dict[tuple[str, int], _Candidate] = {}
        self._hosts: dict[str, HostState] = {}

        # Addresses where we've heard ourself answer.
        self._self_addrs: set[tuple[str, int]] = set()
        self._last_posted: list[NearbyHost] | None = None
        self._publish_pending = False

        # Cycle pacing (see _CYCLE_INTERVAL).
        self._interval = _CYCLE_INTERVAL
        self._last_change = time.monotonic()

        # Probe-traffic stats (logged at DEBUG).
        self._stats_start = time.monotonic()
        self._stats_packets = 0

        # DNS-SD browsing.
        self._browse_fd = -1
        self._browse_poll: asyncio.TimerHandle | None = None
        self._browse_types: list[str] = []
        self._browse_failed = False

    # -- Entry points -----------------------------------------------------

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """A datagram arrived on one of our sockets."""
        if not data:
            return
        try:
            self._handle_packet(data, addr)
        except Exception as exc:
            # Anyone can send us anything; never let a bad packet take
            # down discovery.
            logger.debug('Nearby discovery: bad packet from %s: %s', addr, exc)
            strip_exception_tracebacks(exc)

    def error_received(
        self, exc: Exception, addr: tuple[str, int] | None
    ) -> None:
        """A socket reported an error (for a send to ``addr`` if known)."""
        # Expected on some networks (no route, local-network permission
        # denied, a peer whose Wi-Fi is dozing, etc.); we just keep
        # trying.
        if addr is None:
            logger.debug('Nearby discovery socket error: %s', exc)
        else:
            logger.debug(
                'Nearby discovery socket error sending to %s:%d: %s',
                addr[0],
                addr[1],
                exc,
            )
        strip_exception_tracebacks(exc)

    def begin(self, endpoint: DualStackUDPEndpoint) -> None:
        """Start working (once our sockets are up)."""
        self._endpoint = endpoint
        self._running = True
        self._apply_config()
        self._cycle()

    def end(self) -> None:
        """Shut down."""
        self._running = False
        self._stop_browse()
        if self._endpoint is not None:
            self._endpoint.close()
            self._endpoint = None

    def set_config(self, config: DiscoveryConfig) -> None:
        """New marching orders from the logic thread."""
        self._config = config
        if self._running:
            self._apply_config()

            # Ask right away rather than waiting for the next cycle.
            self._note_change()
            self._send_queries(time.monotonic())

    # -- Config -----------------------------------------------------------

    def _apply_config(self) -> None:
        config = self._config

        # Explicit targets are permanent candidates; drop ones no
        # longer asked for.
        for addr, cand in list(self._candidates.items()):
            if NearbySource.TARGET in cand.sources and (
                addr not in config.targets
            ):
                cand.sources.discard(NearbySource.TARGET)
                if not cand.sources:
                    del self._candidates[addr]
        for addr in config.targets:
            self._candidates.setdefault(addr, _Candidate()).sources.add(
                NearbySource.TARGET
            )

        # Browse for whatever services are wanted.
        game_type, remote_type = _babase.nearby_service_types()
        types: list[str] = []
        if config.open_scan:
            if NearbyService.GAME in config.services:
                types.append(game_type)
            if NearbyService.REMOTE in config.services:
                types.append(remote_type)
        if types != self._browse_types:
            self._stop_browse()
            if types:
                self._start_browse(types)

    # -- DNS-SD -----------------------------------------------------------

    def _start_browse(self, types: list[str]) -> None:
        if self._browse_failed or not _babase.nearby_browse_supported():
            return
        fd = _babase.nearby_browse_start(types)
        if fd == _BROWSE_NO_DESCRIPTOR:
            # Results queue natively (Windows); collect them often.
            self._browse_poll = self._loop.call_later(
                _BROWSE_POLL_INTERVAL, self._poll_browse
            )
        elif fd < 0:
            self._browse_failed = True
            return
        else:
            try:
                self._loop.add_reader(fd, self._on_browse_readable)
            except NotImplementedError:
                _babase.nearby_browse_stop()
                self._browse_failed = True
                return
            self._browse_fd = fd
        self._browse_types = types
        logger.debug('Nearby discovery: browsing for %s.', types)

    def _poll_browse(self) -> None:
        self._browse_poll = self._loop.call_later(
            _BROWSE_POLL_INTERVAL, self._poll_browse
        )
        self._on_browse_readable()

    def _stop_browse(self) -> None:
        if self._browse_fd >= 0:
            self._loop.remove_reader(self._browse_fd)
            self._browse_fd = -1
        if self._browse_poll is not None:
            self._browse_poll.cancel()
            self._browse_poll = None
        if self._browse_types:
            _babase.nearby_browse_stop()
        self._browse_types = []

        # Forget what browsing told us.
        for addr, cand in list(self._candidates.items()):
            cand.instances.clear()
            cand.sources.discard(NearbySource.DNS_SD)
            if not cand.sources:
                del self._candidates[addr]

    def _on_browse_readable(self) -> None:
        try:
            events = _babase.nearby_browse_process()
        except Exception as exc:
            logger.warning('Nearby discovery: DNS-SD browse failed: %s', exc)
            strip_exception_tracebacks(exc)
            self._stop_browse()
            self._browse_failed = True
            return
        now = time.monotonic()
        news: list[tuple[str, int]] = []
        for added, stype, instance, name, address, port, txt in events:
            if not added:
                self._forget_instance(instance)
                continue
            if txt.get('i') == self._self_uuid or port <= 0:
                continue
            logger.debug(
                'Nearby discovery: DNS-SD found %s %r at %s:%d.',
                stype,
                name,
                address,
                port,
            )
            addr = (address, port)
            cand = self._candidates.setdefault(addr, _Candidate())
            cand.sources.add(NearbySource.DNS_SD)
            cand.instances.add(instance)

            # Any news about an address is a reason to try it now, even
            # one that had gone quiet.
            cand.misses = 0
            cand.next_probe = 0.0
            if addr not in news:
                news.append(addr)

        # Check news right away (if not already a route; those keep
        # their own schedule).
        if news:
            self._note_change()
        route_addrs = self._route_addrs()
        for addr in news:
            if addr not in route_addrs:
                self._probe_candidate(addr, self._candidates[addr], now)

    def _forget_instance(self, instance: str) -> None:
        for addr, cand in list(self._candidates.items()):
            if instance in cand.instances:
                cand.instances.discard(instance)
                if not cand.instances:
                    cand.sources.discard(NearbySource.DNS_SD)
                    if not cand.sources:
                        del self._candidates[addr]

    # -- Sending ----------------------------------------------------------

    def _cycle(self) -> None:
        if not self._running:
            return
        now = time.monotonic()
        interval = (
            _CYCLE_INTERVAL_STABLE
            if now - self._last_change >= _STABLE_AFTER
            else _CYCLE_INTERVAL
        )
        if interval != self._interval:
            if interval > self._interval:
                logger.debug(
                    'Nearby discovery: stable; slowing to a %.1fs cycle.',
                    interval,
                )
            self._interval = interval
        self._send_queries(now)
        self._prune(now)
        self._publish()
        self._log_stats(now)
        self._loop.call_later(self._interval, self._cycle)

    def _note_change(self) -> None:
        """Something changed; go back to probing at full rate."""
        self._last_change = time.monotonic()
        if self._interval != _CYCLE_INTERVAL:
            logger.debug('Nearby discovery: change; back to full rate.')
            self._interval = _CYCLE_INTERVAL

    def _log_stats(self, now: float) -> None:
        elapsed = now - self._stats_start
        if elapsed < _STATS_INTERVAL:
            return
        logger.debug(
            'Nearby discovery: %.1f packets/s over %.0fs (cycle %.1fs; %d'
            ' host(s), %d route(s), %d candidate(s)).',
            self._stats_packets / elapsed,
            elapsed,
            self._interval,
            len(self._hosts),
            len(self._route_addrs()),
            len(self._candidates),
        )
        self._stats_start = now
        self._stats_packets = 0

    def _new_query_id(
        self, sources: frozenset[NearbySource], target: str
    ) -> int:
        """A fresh query id; ``sources`` say how its target was found.

        (Answers get credited to those sources even when they come back
        from a different address than the one asked, as hosts with
        several IPv6 addresses often do.) ``target`` describes where it
        went, for debug logging.
        """
        qid = self._next_query_id
        self._next_query_id = (qid + 1) & 0xFFFFFFFF
        self._queries[qid] = _Query(time.monotonic(), sources, target)
        return qid

    def _send(self, data: bytes, addr: tuple[str, int]) -> None:
        # Datagram sends never block; failures arrive in error_received.
        if self._endpoint is not None:
            self._endpoint.sendto(data, addr)
            self._stats_packets += 1

    def _v2_query(self, ptype: int, qid: int) -> bytes:
        return struct.pack('<BI', ptype, qid) + self._query_json

    def _send_queries(self, now: float) -> None:
        config = self._config
        want_game = NearbyService.GAME in config.services
        want_remote = NearbyService.REMOTE in config.services

        if config.open_scan:
            # Each interface's subnet broadcast address, looked up fresh
            # each time so network changes are picked up (the all-ones
            # 255.255.255.255 broadcast doesn't reliably leave iOS
            # devices). Plus localhost, for a game on this same device.
            targets = [
                (addr, GAME_PORT) for addr in _babase.nearby_broadcast_addrs()
            ] + [('127.0.0.1', GAME_PORT)]
            qid = self._new_query_id(
                frozenset({NearbySource.BROADCAST}), 'broadcast'
            )
            packets: list[bytes] = []
            if want_game:
                packets.append(struct.pack('<BI', _HOST_QUERY, qid))
                packets.append(self._v2_query(_HOST_QUERY_V2, qid))
            if want_remote:
                packets.append(bytes([_REMOTE_GAME_QUERY]))
                packets.append(self._v2_query(_REMOTE_GAME_QUERY_V2, qid))
            for target in targets:
                for packet in packets:
                    self._send(packet, target)

        # Probe routes on their schedules: each host's best one every
        # cycle (keeping its round trip and liveness fresh), the rest
        # much less often -- unless the best one has missed a probe
        # and no other route answered its latest, in which case all of
        # that host's routes go back to full rate so failover (or
        # noticing the host is gone) doesn't wait on a slow schedule.
        # (With another route answering, a missed probe is most likely
        # just lost, and that route is there to fail over to anyway.)
        route_addrs: set[tuple[str, int]] = set()
        for host in self._hosts.values():
            best = host.routes.get(host.best) if host.best else None
            degraded = best is None or (
                best.missed(now) > 0
                and not answering_elsewhere(host, best, now)
            )
            if degraded and self._interval != _CYCLE_INTERVAL:
                self._note_change()
            for addr, route in host.routes.items():
                if addr in route_addrs:
                    continue
                route_addrs.add(addr)
                full_rate = degraded or route is best
                if not full_rate and now < route.next_probe:
                    continue
                route.probe_interval = (
                    self._interval if full_rate else _SPARE_PROBE_INTERVAL
                )
                route.next_probe = now + route.probe_interval
                route.last_probe = now
                route.unanswered += 1
                self._send_unicast_queries(addr, route)

        # And candidates that aren't routes (yet), backing off ones
        # that never answer.
        for addr, cand in self._candidates.items():
            if addr not in route_addrs and now >= cand.next_probe:
                self._probe_candidate(addr, cand, now)

    def _route_addrs(self) -> set[tuple[str, int]]:
        return {addr for host in self._hosts.values() for addr in host.routes}

    def _probe_candidate(
        self, addr: tuple[str, int], cand: _Candidate, now: float
    ) -> None:
        """Probe a candidate, scheduling its next probe with backoff."""
        cand.misses += 1
        cand.next_probe = now + min(
            _CANDIDATE_MAX_BACKOFF, _CYCLE_INTERVAL * 2 ** (cand.misses - 1)
        )
        self._send_unicast_queries(addr, None)

    def _send_unicast_queries(
        self, addr: tuple[str, int], route: RouteState | None
    ) -> None:
        config = self._config
        cand = self._candidates.get(addr)
        sources = set(cand.sources) if cand is not None else set()
        if route is not None:
            sources |= route.sources
        qid = self._new_query_id(frozenset(sources), f'{addr[0]}:{addr[1]}')

        # Hosts too old for v2 only answer v1, so ask in both forms --
        # except where the host is known to be new: anything found via
        # DNS-SD (only new builds advertise) or a route that has
        # answered v2. (Pointless v1 answers there aren't harmless: the
        # v1 remote answer carries no uuid, so one beating its v2 twin
        # in would briefly list the host twice.)
        known_new = NearbySource.DNS_SD in sources
        if NearbyService.GAME in config.services:
            self._send(self._v2_query(_HOST_QUERY_V2, qid), addr)
            if not known_new and (route is None or not route.game_v2):
                self._send(struct.pack('<BI', _HOST_QUERY, qid), addr)
        if NearbyService.REMOTE in config.services:
            self._send(self._v2_query(_REMOTE_GAME_QUERY_V2, qid), addr)
            if not known_new and (route is None or not route.remote_v2):
                self._send(bytes([_REMOTE_GAME_QUERY]), addr)

    # -- Receiving --------------------------------------------------------

    def _handle_packet(self, data: bytes, addr: tuple[str, int]) -> None:
        ptype = data[0]
        if ptype == _HOST_QUERY_RESPONSE:
            self._handle_host_response_v1(data, addr)
        elif ptype == _HOST_QUERY_RESPONSE_V2:
            self._handle_host_response_v2(data, addr)
        elif ptype == _REMOTE_GAME_RESPONSE:
            self._handle_remote_response_v1(data, addr)
        elif ptype == _REMOTE_GAME_RESPONSE_V2:
            self._handle_remote_response_v2(data, addr)

    def _query_for(self, data: bytes) -> _Query | None:
        """The query an answer answers (None for unknown/forgotten ids)."""
        if len(data) < 5:
            return None
        (qid,) = struct.unpack_from('<I', data, 1)
        return self._queries.get(qid)

    def _handle_host_response_v1(
        self, data: bytes, addr: tuple[str, int]
    ) -> None:
        # Type, query-id, protocol, uuid-len, spec-len, uuid, spec.
        if len(data) < 13:
            return
        protocol, id_len, spec_len = struct.unpack_from('<IBB', data, 5)
        if id_len < 1 or spec_len < 1 or 11 + id_len + spec_len != len(data):
            return
        uuid = data[11 : 11 + id_len].decode(errors='replace')
        spec = data[11 + id_len :].decode(errors='replace')
        if uuid == self._self_uuid:
            return
        host, _route = self._note_route(uuid, addr, self._query_for(data))
        # v2 answers carry strictly more; never let v1 replace them.
        if not host.game_is_v2:
            host.game = NearbyGameInfo(
                player_spec=spec,
                party_name='',
                party_size=0,
                party_max_size=0,
                auth_required=False,
                build_number=0,
                protocol_version=protocol,
            )

    def _handle_host_response_v2(
        self, data: bytes, addr: tuple[str, int]
    ) -> None:
        info = _parse_json_payload(data)
        if info is None:
            return
        uuid = info.get('i')
        spec = info.get('s')
        if not isinstance(uuid, str) or not isinstance(spec, str):
            return
        if uuid == self._self_uuid:
            return
        host, route = self._note_route(uuid, addr, self._query_for(data))
        route.game_v2 = True
        host.game_is_v2 = True
        host.game = NearbyGameInfo(
            player_spec=spec,
            party_name=_json_str(info, 'n'),
            party_size=_json_int(info, 'sz'),
            party_max_size=_json_int(info, 'szx'),
            auth_required=bool(info.get('a', False)),
            build_number=_json_int(info, 'b'),
            protocol_version=_json_int(info, 'p'),
        )

    def _handle_remote_response_v1(
        self, data: bytes, addr: tuple[str, int]
    ) -> None:
        # Just a device name; no uuid and no query id. New hosts answer
        # v2 too, so only list this if nothing else is known there.
        if addr in self._self_addrs:
            return
        cand = self._candidates.get(addr)
        if cand is not None and NearbySource.DNS_SD in cand.sources:
            # A new host (it advertises); its v2 answer speaks for it.
            return
        for host in self._hosts.values():
            if host.remote_is_v2 and addr in host.routes:
                return
        name = data[1:].split(b'\0', 1)[0].decode(errors='replace')
        # These answers carry no query id to say which query they
        # answer: credit an address we asked directly with how we found
        # it, and anything else to our broadcasts.
        host, _route = self._note_route(
            f'legacy:{addr[0]}:{addr[1]}',
            addr,
            None,
            extra_sources=(
                frozenset(cand.sources)
                if cand is not None
                else frozenset({NearbySource.BROADCAST})
            ),
        )
        host.remote = NearbyRemoteInfo(name=name, build_number=0)

    def _handle_remote_response_v2(
        self, data: bytes, addr: tuple[str, int]
    ) -> None:
        info = _parse_json_payload(data)
        if info is None:
            return
        uuid = info.get('i')
        if not isinstance(uuid, str):
            return
        if uuid == self._self_uuid:
            # Our own remote-app server. Its v1 answers carry no uuid,
            # so remember where we are to recognize those too.
            self._self_addrs.add(addr)
            self._hosts.pop(f'legacy:{addr[0]}:{addr[1]}', None)
            return
        host, route = self._note_route(uuid, addr, self._query_for(data))
        route.remote_v2 = True
        host.remote_is_v2 = True
        host.remote = NearbyRemoteInfo(
            name=_json_str(info, 'n'), build_number=_json_int(info, 'b')
        )
        # Its legacy twin (from its v1 answer) is now redundant.
        legacy = self._hosts.get(f'legacy:{addr[0]}:{addr[1]}')
        if legacy is not None and legacy.game is None:
            del self._hosts[legacy.key]

    def _note_route(
        self,
        key: str,
        addr: tuple[str, int],
        query: _Query | None,
        extra_sources: frozenset[NearbySource] = frozenset(),
    ) -> tuple[HostState, RouteState]:
        """Record that a host answered at an address.

        ``query`` is the query answered, if known; the route is credited
        with the sources of that query's target (plus ``extra_sources``).
        A late answer to a forgotten query credits nothing.
        """
        now = time.monotonic()
        rtt = None if query is None else now - query.sent
        sources = extra_sources
        if query is not None:
            sources |= query.sources
        host = self._hosts.get(key)
        if host is None:
            host = self._hosts[key] = HostState(key=key)

            # Don't make anyone wait for the next cycle to hear of it.
            # (A moment's delay lets its other answers land first.)
            if not self._publish_pending:
                self._publish_pending = True
                self._loop.call_later(0.05, self._publish)
            logger.debug(
                'Nearby discovery: found host %s at %s:%d.', key, *addr
            )
        route = host.routes.get(addr)
        if route is None:
            route = host.routes[addr] = RouteState(
                address=addr[0], port=addr[1], last_heard=now
            )
            self._note_change()
        if route.quiet_logged:
            route.quiet_logged = False
            logger.debug(
                'Nearby discovery: %s:%d of %s answering again after'
                ' %.1fs (this answer took %s).',
                *addr,
                key,
                now - route.last_heard,
                'unknown' if rtt is None else f'{rtt * 1000.0:.0f}ms',
            )
        route.last_heard = now
        route.unanswered = 0
        cand = self._candidates.get(addr)
        if cand is not None:
            cand.misses = 0
        gained = sources - route.sources
        if gained:
            logger.debug(
                'Nearby discovery: route %s:%d of %s now credited to %s'
                ' (answer to a query sent to %s).',
                addr[0],
                addr[1],
                key,
                sorted(s.value for s in gained),
                'nowhere known' if query is None else query.target,
            )
            route.sources |= gained
        if rtt is not None and 0.0 <= rtt < _QUERY_TIMEOUT:
            route.srtt = (
                rtt
                if route.srtt is None
                else route.srtt * (1.0 - _RTT_ALPHA) + rtt * _RTT_ALPHA
            )
        return host, route

    # -- Upkeep -----------------------------------------------------------

    def _prune(self, now: float) -> None:
        for qid, query in list(self._queries.items()):
            if now - query.sent > _QUERY_TIMEOUT:
                del self._queries[qid]
        for key, host in list(self._hosts.items()):
            for addr, route in list(host.routes.items()):
                if route.missed(now) >= _ROUTE_DROP_MISSES:
                    del host.routes[addr]
                    self._note_change()
            if not host.routes:
                logger.debug('Nearby discovery: lost host %s.', key)
                del self._hosts[key]

    def _publish(self) -> None:
        self._publish_pending = False
        if not self._running:
            return
        now = time.monotonic()
        hosts: list[NearbyHost] = []
        for key in sorted(self._hosts):
            host = self._hosts[key]
            if update_best_route(host, now):
                self._note_change()
            assert host.best is not None
            best = host.routes[host.best]
            # (Address as tie-breaker so near-equal routes don't keep
            # swapping places.)
            ranked = [best] + sorted(
                (r for r in host.routes.values() if r is not best),
                key=lambda r: (route_score(r), r.address, r.port),
            )
            routes = tuple(public_route(r) for r in ranked)
            hosts.append(
                NearbyHost(
                    key=key,
                    route=routes[0],
                    routes=routes,
                    game=host.game,
                    remote=host.remote,
                )
            )
        if hosts != self._last_posted:
            self._last_posted = hosts
            self._post(hosts)


def _parse_json_payload(data: bytes) -> dict[str, Any] | None:
    if len(data) < 7:
        return None
    try:
        info = json.loads(data[5:])
    except ValueError:
        return None
    return info if isinstance(info, dict) else None


def _json_str(info: dict[str, Any], key: str) -> str:
    val = info.get(key)
    return val if isinstance(val, str) else ''


def _json_int(info: dict[str, Any], key: str) -> int:
    val = info.get(key)
    return val if isinstance(val, int) and not isinstance(val, bool) else 0
