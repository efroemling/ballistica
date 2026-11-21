# Released under the MIT License. See LICENSE for details.
#
"""The pre-join requirements probe (see connect_to_party)."""

import os
import time
import json
import select
import socket
import logging
from enum import Enum
from typing import TYPE_CHECKING, assert_never
from dataclasses import dataclass, field

from efro.util import strip_exception_tracebacks
from bacommon.assetpackage import ApverNum

import babase

if TYPE_CHECKING:
    from typing import Any, Sequence

netlog = logging.getLogger('ba.net')

# Wire packet-type bytes; must match BA_PACKET_HOST_REQUIREMENTS_QUERY
# / _RESPONSE and BA_PACKET_HOST_QUERY / _RESPONSE in
# ballistica/base/networking/networking.h.
_REQS_QUERY_PACKET_TYPE = 40
_REQS_RESPONSE_PACKET_TYPE = 41
_HOST_QUERY_PACKET_TYPE = 22
_HOST_QUERY_RESPONSE_PACKET_TYPE = 23

# First protocol whose hosts REQUIRE the pre-join requirements exchange
# (must match kProtocolVersionLangStrWire in scene_v1.h). The legacy
# discovery query (which every host generation answers) reports the
# host's protocol, letting the probe distinguish 'legacy host with no
# requirements' from 'new host whose requirements responses got lost'
# by testimony rather than timeout.
_LANG_STR_WIRE_PROTOCOL = 39

# The exchange rides lossy UDP, so each page is retried a few times
# with short waits. The first page gets the long budget whether or not
# the host has answered anything yet: silence there fails the join, so
# a brief blip (wifi power-save, first-packet ARP, etc.) must not.
_REQS_ATTEMPT_TIMEOUT = 0.75
_REQS_PAGE_ATTEMPTS = 3
_REQS_PROBE_ATTEMPTS = 8

# Refuse to chase absurd page counts from a hostile/buggy host.
_REQS_MAX_PAGES = 64

# When a host has several addresses, each one's probe starts this long
# after the previous one's (a la Happy Eyeballs, RFC 8305), so a
# preferred address gets a head start but a dead one can't stall us.
_RACE_STAGGER = 0.15


@dataclass
class HostRequirements:
    """Everything a host requires of clients joining it.

    Fetched from prospective hosts by the pre-join requirements query
    (see :func:`~bascenev1.connect_to_party`).
    """

    asset_packages: list[ApverNum] = field(default_factory=list)
    password_required: bool = False


class HostProbeOutcome(Enum):
    """No-requirements outcomes of :func:`fetch_host_requirements`."""

    #: The host answered the legacy discovery query reporting a
    #: pre-lang-str protocol: a confirmed old host with no requirements
    #: to fetch. Connect immediately.
    LEGACY = 'legacy'

    #: Nothing answered anything -- the address is unreachable, bogus,
    #: or down (or every attempt was lost). The join fails; we never
    #: connect to a host whose requirements we couldn't learn.
    SILENT = 'silent'

    #: The host proved alive AND lang-str-era (or began the exchange)
    #: but never completed the requirements listing despite an extended
    #: retry budget. Joining it unprepped could only strand; fail the
    #: join like a standard connection failure.
    UNRESPONSIVE = 'unresponsive'


def fetch_host_requirements(
    address: str | Sequence[str], port: int
) -> HostRequirements | HostProbeOutcome:
    """Probe a prospective host for its join requirements.

    Fires the paged UDP requirements query and the legacy discovery
    query together (fragments merge across pages: lists concatenate,
    scalars are first-seen; the discovery response's protocol version
    disambiguates old hosts from packet loss without waiting out
    timeouts). Blocking (network waits up to a few seconds); call from
    a background thread.

    ``address`` may be several addresses (or hostnames) for the same
    host, such as its IPv6 and IPv4 addresses; they are raced, each
    starting shortly after the one before it, and whichever answers
    first is used (so a reachable-looking but broken IPv6 path can't
    stall things). Earlier entries are preferred.

    Returns the host's :class:`HostRequirements`, or a
    :class:`HostProbeOutcome` describing why there are none. Failures
    are logged here with what the probe saw (attempts, elapsed time,
    socket errors): failures that can't come from our own bugs (no
    answer at all, unresolvable address) go to ``ba.user``; the rest
    go to ``ba.net``.
    """
    addresses = [address] if isinstance(address, str) else list(address)
    return probe_host(addresses, port)[0]


def probe_host(
    addresses: Sequence[str], port: int
) -> tuple[HostRequirements | HostProbeOutcome, str | None]:
    """Race the requirements probe across a host's addresses.

    Returns the outcome plus the resolved address that answered (what
    the actual connection should use), or None if nothing did.

    :meta private:
    """
    start = time.monotonic()
    label = ', '.join(f'{a}:{port}' for a in addresses)
    entries = _make_race_entries(addresses, port, start)
    try:
        raced = _race_page_zero(entries)
        if raced is None:
            outcome = (
                HostProbeOutcome.UNRESPONSIVE
                if any(
                    e.outcome is HostProbeOutcome.UNRESPONSIVE for e in entries
                )
                else HostProbeOutcome.SILENT
            )
            _log_probe_failure(outcome, _combined_diag(label, start, entries))
            return outcome, None
        winner, first = raced
        if len(entries) > 1:
            netlog.debug(
                'Join probe: %s answered first (of %d candidates).',
                winner.host,
                len(entries),
            )
        if first is HostProbeOutcome.LEGACY:
            return first, winner.host
        assert not isinstance(first, HostProbeOutcome)
        return _finish_requirements(winner, first), winner.host
    finally:
        for entry in entries:
            entry.sock.close()


def _make_race_entries(
    addresses: Sequence[str], port: int, start: float
) -> list[_RaceEntry]:
    """Resolve a host's addresses and set up a race candidate for each.

    Resolving is also what makes IPv6-only networks (NAT64) work: an
    IPv4 literal resolves to its synthesized IPv6 form there (and to
    itself everywhere else).
    """
    # (getaddrinfo's address tuples vary by family, hence Any.)
    targets: list[tuple[socket.AddressFamily, socket.SocketKind, int, Any]] = []
    seen: set[str] = set()
    for address in addresses:
        try:
            infos = socket.getaddrinfo(address, port, type=socket.SOCK_DGRAM)
        except OSError as exc:
            babase.userlog.warning(
                'Unable to resolve join address %r: %s', address, exc
            )
            strip_exception_tracebacks(exc)
            continue
        for family, kind, proto, _canonname, sockaddr in infos:
            host = _host_text(sockaddr)
            if host in seen:
                continue
            seen.add(host)
            targets.append((family, kind, proto, sockaddr))

    entries: list[_RaceEntry] = []
    for i, (tfamily, tkind, tproto, tsockaddr) in enumerate(targets):
        host = _host_text(tsockaddr)
        try:
            sock = socket.socket(tfamily, tkind, tproto)
        except OSError as exc:
            strip_exception_tracebacks(exc)
            continue
        entry = _RaceEntry(
            sock=sock,
            host=host,
            diag=_ProbeDiag(target=f'{host}:{port}', start=start),
            start_at=start + i * _RACE_STAGGER,
        )
        entries.append(entry)
        try:
            sock.setblocking(False)
            # Connecting the socket pins the peer address, so the
            # kernel filters out datagrams from anyone else.
            sock.connect(tsockaddr)
        except OSError as exc:
            # (No route to this one, etc.)
            entry.diag.record_error(exc)
            strip_exception_tracebacks(exc)
            entry.done = True
            entry.outcome = HostProbeOutcome.SILENT
    return entries


def _host_text(sockaddr: Any) -> str:
    """The text form of a resolved address, as the native join takes it.

    Link-local IPv6 addresses need their interface ('fe80::1%en0'), and
    getaddrinfo often leaves it only in the address tuple's scope slot.
    """
    host = str(sockaddr[0])
    if len(sockaddr) >= 4 and sockaddr[3] and '%' not in host:
        try:
            host = f'{host}%{socket.if_indextoname(sockaddr[3])}'
        except OSError:
            host = f'{host}%{sockaddr[3]}'
    return host


def _finish_requirements(
    winner: _RaceEntry, first: tuple[int, dict[str, Any]]
) -> HostRequirements | HostProbeOutcome:
    """Fetch the remaining requirements pages from the winning address."""
    diag = winner.diag
    sock = winner.sock
    if diag.attempts > 1:
        # Worked, but the link is lossy (or the host slow); handy
        # context if the join then misbehaves.
        netlog.info(
            'Join requirements probe to %s answered on attempt %d after'
            ' %.1fs.',
            diag.target,
            diag.attempts,
            time.monotonic() - diag.start,
        )
    sock.setblocking(True)

    # Values here are parsed json, hence Any.
    merged: dict[str, Any] = {}
    resp_page_count, fragment = first
    page_count = min(resp_page_count, _REQS_MAX_PAGES)
    _merge_requirements_fragment(merged, fragment)
    for page in range(1, page_count):
        result = _fetch_requirements_page(sock, page, diag)
        if result is None:
            # The host proved itself new by answering page 0 but went
            # dark mid-listing; joining on a partial listing could only
            # strand.
            stopped = f'stopped at page {page} of {page_count}'
            diag.note = (
                stopped if diag.note is None else f'{stopped}; {diag.note}'
            )
            _log_probe_failure(HostProbeOutcome.UNRESPONSIVE, diag)
            return HostProbeOutcome.UNRESPONSIVE
        _, fragment = result
        _merge_requirements_fragment(merged, fragment)

    asset_packages = merged.get('ap')
    if not isinstance(asset_packages, list):
        asset_packages = []
    return HostRequirements(
        # Hosts advertise numeric ids as text (engine package keys).
        asset_packages=[
            ApverNum(int(pkg))
            for pkg in asset_packages
            if isinstance(pkg, str) and pkg.isdigit()
        ],
        password_required=bool(merged.get('pw')),
    )


def _merge_requirements_fragment(
    merged: dict[str, Any], fragment: dict[str, Any]
) -> None:
    for key, val in fragment.items():
        if isinstance(val, list):
            merged.setdefault(key, []).extend(val)
        else:
            merged.setdefault(key, val)


@dataclass
class _ProbeDiag:
    """What a requirements probe saw, for logging its outcome."""

    target: str
    start: float
    attempts: int = 0
    host_protocol: int | None = None
    # Most recent socket error other than a plain timeout (no route,
    # refused, permission denied...); these say *why* nothing came back.
    last_error: str | None = None
    note: str | None = None

    def record_error(self, exc: OSError) -> None:
        """Note a socket error (plain timeouts are just silence)."""
        if not isinstance(exc, TimeoutError):
            self.last_error = str(exc)


def _log_probe_failure(outcome: HostProbeOutcome, diag: _ProbeDiag) -> None:
    details = (
        f'{diag.attempts} attempt(s) over'
        f' {time.monotonic() - diag.start:.1f}s'
    )
    if diag.last_error is not None:
        details += f'; last error: {diag.last_error}'
    if diag.note is not None:
        details += f'; {diag.note}'
    if outcome is HostProbeOutcome.SILENT:
        # Nothing ever answered: a network/address problem on the
        # user's end (or the host is gone), not an engine bug.
        babase.userlog.warning(
            'No response from %s to the join requirements probe (%s);'
            ' aborting join.',
            diag.target,
            details,
        )
    elif outcome is HostProbeOutcome.UNRESPONSIVE:
        # The host showed it's alive and new but the exchange didn't
        # complete; that can be our bug on either end, so keep it
        # reportable.
        netlog.warning(
            'Host %s (protocol %s) did not complete the join requirements'
            ' exchange (%s); aborting join.',
            diag.target,
            diag.host_protocol,
            details,
        )
    elif outcome is HostProbeOutcome.LEGACY:
        pass
    else:
        assert_never(outcome)


@dataclass
class _RaceEntry:
    """One candidate address in a requirements-probe race."""

    sock: socket.socket
    host: str
    diag: _ProbeDiag
    start_at: float
    started: bool = False
    done: bool = False

    # Why it lost, once done without winning.
    outcome: HostProbeOutcome | None = None
    reqs_query_id: bytes = b''
    disc_query_id: bytes = b''
    attempt_deadline: float = 0.0


def _race_page_zero(
    entries: list[_RaceEntry],
) -> tuple[_RaceEntry, tuple[int, dict[str, Any]] | HostProbeOutcome] | None:
    """Run the combined discovery + requirements-page-0 probe as a race.

    Each candidate starts ``_RACE_STAGGER`` after the one before it
    (sooner if that one fails outright, e.g. no route) and then runs
    the same attempt loop a single probe always did: each attempt sends
    the requirements query for page 0 plus (until one is answered) a
    legacy discovery query, and incoming datagrams are sorted until the
    attempt window ends. The first candidate to get a page-0 answer, or
    a discovery answer reporting a pre-lang-str protocol (LEGACY), wins.
    Returns that entry and its result, or None if every candidate gave
    up (each entry's ``outcome`` then says how: SILENT, or UNRESPONSIVE
    if it proved the host alive and new).
    """
    while True:
        now = time.monotonic()
        for entry in entries:
            if entry.done:
                continue
            if not entry.started:
                if now >= entry.start_at:
                    entry.started = True
                    _race_send_attempt(entry, entries, now)
            elif now >= entry.attempt_deadline:
                if entry.diag.attempts >= _REQS_PROBE_ATTEMPTS:
                    entry.done = True
                    entry.outcome = (
                        HostProbeOutcome.SILENT
                        if entry.diag.host_protocol is None
                        else HostProbeOutcome.UNRESPONSIVE
                    )
                else:
                    _race_send_attempt(entry, entries, now)
        active = [e for e in entries if not e.done]
        if not active:
            return None
        wake = min(
            e.attempt_deadline if e.started else e.start_at for e in active
        )
        timeout = max(0.0, wake - time.monotonic())
        socks = [e.sock for e in active if e.started]
        if not socks:
            # (select() with nothing to watch fails on Windows.)
            time.sleep(timeout)
            continue
        readable, _, _ = select.select(socks, [], [], timeout)
        for sock in readable:
            entry = next(e for e in active if e.sock is sock)
            while not entry.done:
                try:
                    data = sock.recv(1500)
                except BlockingIOError:
                    break
                except OSError as exc:
                    # (ICMP errors such as 'connection refused' land
                    # here on connected UDP sockets.)
                    entry.diag.record_error(exc)
                    strip_exception_tracebacks(exc)
                    break
                result = _race_handle_packet(entry, data)
                if result is not None:
                    return entry, result


def _race_send_attempt(
    entry: _RaceEntry, entries: list[_RaceEntry], now: float
) -> None:
    """Start a new page-0 attempt for a race candidate."""
    entry.diag.attempts += 1
    entry.reqs_query_id = os.urandom(4)
    entry.disc_query_id = os.urandom(4)
    entry.attempt_deadline = now + _REQS_ATTEMPT_TIMEOUT
    try:
        entry.sock.send(
            bytes([_REQS_QUERY_PACKET_TYPE])
            + entry.reqs_query_id
            + _requirements_query_payload(0)
        )
        if entry.diag.host_protocol is None:
            entry.sock.send(
                bytes([_HOST_QUERY_PACKET_TYPE]) + entry.disc_query_id
            )
    except OSError as exc:
        # Failing outright (no route, etc.) is a strong hint this
        # address is dead, so don't make the next one wait its turn.
        entry.diag.record_error(exc)
        strip_exception_tracebacks(exc)
        for other in entries:
            if not other.started:
                other.start_at = min(other.start_at, now)
                break


def _race_handle_packet(
    entry: _RaceEntry, data: bytes
) -> tuple[int, dict[str, Any]] | HostProbeOutcome | None:
    """Handle a datagram for a race candidate; return a win, if any."""
    diag = entry.diag
    if (
        len(data) >= 5
        and data[0] == _REQS_RESPONSE_PACKET_TYPE
        and data[1:5] == entry.reqs_query_id
    ):
        result = _parse_requirements_response(data, page=0)
        if result is None:
            # Malformed data won't improve with retries, and only a new
            # host emits this packet type at all.
            diag.note = f'malformed page-0 response ({data!r:.80})'
            entry.done = True
            entry.outcome = HostProbeOutcome.UNRESPONSIVE
            return None
        return result
    if (
        diag.host_protocol is None
        and len(data) >= 9
        and data[0] == _HOST_QUERY_RESPONSE_PACKET_TYPE
        and data[1:5] == entry.disc_query_id
    ):
        diag.host_protocol = int.from_bytes(data[5:9], 'little')
        if diag.host_protocol < _LANG_STR_WIRE_PROTOCOL:
            netlog.debug(
                'Discovery response from %s reports legacy protocol %d;'
                ' no requirements to fetch.',
                entry.host,
                diag.host_protocol,
            )
            return HostProbeOutcome.LEGACY
        netlog.debug(
            'Discovery response from %s reports protocol %d; host is alive'
            ' and requires the requirements exchange.',
            entry.host,
            diag.host_protocol,
        )
    return None


def _combined_diag(
    label: str, start: float, entries: list[_RaceEntry]
) -> _ProbeDiag:
    """Fold a failed race's per-candidate findings into one for logging."""
    diag = _ProbeDiag(target=label, start=start)
    for entry in entries:
        diag.attempts += entry.diag.attempts
        if entry.diag.host_protocol is not None:
            diag.host_protocol = entry.diag.host_protocol
        if entry.diag.last_error is not None:
            diag.last_error = f'{entry.host}: {entry.diag.last_error}'
        if entry.diag.note is not None:
            diag.note = entry.diag.note
    if not entries:
        diag.note = 'no usable address'
    return diag


def _requirements_query_payload(page: int) -> bytes:
    return json.dumps(
        {
            'v': 1,
            'b': babase.app.env.engine_build_number,
            'p': page,
        },
        separators=(',', ':'),
    ).encode()


def _parse_requirements_response(
    data: bytes, page: int
) -> tuple[int, dict[str, Any]] | None:
    """Validate/parse a requirements response datagram body.

    Returns ``(page_count, requirements_fragment)``, or None for
    malformed data (which won't improve with retries).
    """
    try:
        response = json.loads(data[5:])
    except ValueError:
        return None
    if not isinstance(response, dict):
        return None
    version = response.get('v')
    if not isinstance(version, int) or version < 1:
        return None
    resp_page_count = response.get('n')
    fragment = response.get('r')
    if (
        response.get('p') != page
        or not isinstance(resp_page_count, int)
        or resp_page_count < 1
        or not isinstance(fragment, dict)
    ):
        return None
    return resp_page_count, fragment


def _fetch_requirements_page(
    sock: socket.socket, page: int, diag: _ProbeDiag
) -> tuple[int, dict[str, Any]] | None:
    """Fetch a single requirements page over a connected UDP socket.

    Returns ``(page_count, requirements_fragment)``, or None if the
    host never produced a valid response for this page.
    """
    query = _requirements_query_payload(page)
    for _attempt in range(_REQS_PAGE_ATTEMPTS):
        diag.attempts += 1
        query_id = os.urandom(4)
        data: bytes | None = None
        try:
            sock.send(bytes([_REQS_QUERY_PACKET_TYPE]) + query_id + query)
            # A hard deadline per attempt: stray datagrams (late
            # duplicates for earlier pages, etc.) must not keep
            # resetting the wait.
            deadline = time.monotonic() + _REQS_ATTEMPT_TIMEOUT
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    break
                sock.settimeout(remaining)
                packet = sock.recv(1500)
                if (
                    len(packet) >= 5
                    and packet[0] == _REQS_RESPONSE_PACKET_TYPE
                    and packet[1:5] == query_id
                ):
                    data = packet
                    break
        except OSError as exc:
            diag.record_error(exc)
            strip_exception_tracebacks(exc)
            continue
        if data is None:
            continue

        # Got a response to *this* query; validate it. A host serving
        # malformed data won't improve with retries, so treat that the
        # same as no response.
        result = _parse_requirements_response(data, page)
        if result is None:
            diag.note = f'malformed page-{page} response ({data!r:.80})'
        return result
    return None
