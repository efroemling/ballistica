# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to net play."""

import os
import time
import json
import socket
import asyncio
import logging
from enum import Enum
from typing import TYPE_CHECKING, assert_never
from dataclasses import dataclass, field

from efro.util import strip_exception_tracebacks
from bacommon.assetpackage import ApverNum, AssetPackageResolveError

import babase

import _bascenev1

if TYPE_CHECKING:
    from typing import Any

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

# The in-flight pre-join task, if any (see connect_to_party's
# latest-wins behavior).
_g_prejoin_task: asyncio.Task[None] | None = None

# The address/port of the in-flight pre-join, plus an id unique to that
# request. Set synchronously by connect_to_party (the task itself only
# starts on a later loop pass) so repeat requests are caught at once.
_g_prejoin_target: tuple[str, int, int] | None = None
_g_next_prejoin_id = 0

# The package universe of the host we most recently connected to (None
# if it advertised none).
_g_joined_host_asset_packages: frozenset[ApverNum] | None = None


def get_joined_host_asset_packages() -> frozenset[ApverNum] | None:
    """The package universe of the host we last joined.

    That is, the asset-package-versions it advertised before we
    connected (which we resolved before connecting). None if it
    advertised none (such as an older host).

    :meta private:
    """
    return _g_joined_host_asset_packages


def set_admins(admins: list[str]) -> None:
    """Set the v2 account ids (a-XXX) of this host's admins.

    Admins can't be kicked by vote, and kick anyone they choose to
    without one. (Sets ``app.classic.host_ui.admins``.)

    :meta private:
    """
    classic = babase.app.classic
    if classic is not None:
        classic.host_ui.admins = set(admins)


def set_enable_default_kick_voting(enable: bool) -> None:
    """Turn the standard kick-vote system on or off.

    (Calls ``app.classic.host_ui.kick_votes.set_enabled()``.)

    :meta private:
    """
    classic = babase.app.classic
    if classic is not None:
        classic.host_ui.kick_votes.set_enabled(enable)


@dataclass
class HostInfo:
    """Info about a host."""

    name: str
    build_number: int

    # Note this can be None for non-ip hosts such as bluetooth.
    address: str | None

    # Note this can be None for non-ip hosts such as bluetooth.
    port: int | None


@dataclass
class HostRequirements:
    """Everything a host requires of clients joining it.

    Fetched from prospective hosts by the pre-join requirements query
    (see :func:`connect_to_party`).
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
    address: str, port: int
) -> HostRequirements | HostProbeOutcome:
    """Probe a prospective host for its join requirements.

    Fires the paged UDP requirements query and the legacy discovery
    query together (fragments merge across pages: lists concatenate,
    scalars are first-seen; the discovery response's protocol version
    disambiguates old hosts from packet loss without waiting out
    timeouts). Blocking (network waits up to a few seconds); call from
    a background thread.

    Returns the host's :class:`HostRequirements`, or a
    :class:`HostProbeOutcome` describing why there are none. Failures
    are logged here with what the probe saw (attempts, elapsed time,
    socket errors): failures that can't come from our own bugs (no
    answer at all, unresolvable address) go to ``ba.user``; the rest
    go to ``ba.net``.
    """
    diag = _ProbeDiag(target=f'{address}:{port}', start=time.monotonic())
    try:
        infos = socket.getaddrinfo(address, port, type=socket.SOCK_DGRAM)
    except OSError as exc:
        babase.userlog.warning(
            'Unable to resolve join address %r: %s', address, exc
        )
        strip_exception_tracebacks(exc)
        return HostProbeOutcome.SILENT
    family, stype, proto, _canonname, sockaddr = infos[0]
    if sockaddr[0] != address:
        diag.target = f'{address}:{port} ({sockaddr[0]})'

    # Values here are parsed json, hence Any.
    merged: dict[str, Any] = {}
    try:
        with socket.socket(family, stype, proto) as sock:
            # Connecting the socket pins the peer address, so the kernel
            # filters out datagrams from anyone but the host we asked.
            sock.connect(sockaddr)

            first = _probe_page_zero(sock, diag)
            if isinstance(first, HostProbeOutcome):
                _log_probe_failure(first, diag)
                return first
            if diag.attempts > 1:
                # Worked, but the link is lossy (or the host slow);
                # handy context if the join then misbehaves.
                netlog.info(
                    'Join requirements probe to %s answered on attempt'
                    ' %d after %.1fs.',
                    diag.target,
                    diag.attempts,
                    time.monotonic() - diag.start,
                )
            resp_page_count, fragment = first
            page_count = min(resp_page_count, _REQS_MAX_PAGES)
            _merge_requirements_fragment(merged, fragment)

            for page in range(1, page_count):
                result = _fetch_requirements_page(sock, page, diag)
                if result is None:
                    # The host proved itself new by answering page 0
                    # but went dark mid-listing; joining on a partial
                    # listing could only strand.
                    stopped = f'stopped at page {page} of {page_count}'
                    diag.note = (
                        stopped
                        if diag.note is None
                        else f'{stopped}; {diag.note}'
                    )
                    _log_probe_failure(HostProbeOutcome.UNRESPONSIVE, diag)
                    return HostProbeOutcome.UNRESPONSIVE
                _, fragment = result
                _merge_requirements_fragment(merged, fragment)
    except OSError as exc:
        # Socket creation/connect failed (no route, no network, etc.).
        babase.userlog.warning(
            'Join requirements probe to %s failed: %s', diag.target, exc
        )
        strip_exception_tracebacks(exc)
        return HostProbeOutcome.SILENT

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


def _probe_page_zero(
    sock: socket.socket, diag: _ProbeDiag
) -> tuple[int, dict[str, Any]] | HostProbeOutcome:
    """Run the combined discovery + requirements-page-0 probe.

    Each attempt sends the requirements query for page 0 plus (until
    one is answered) a legacy discovery query, then sorts incoming
    datagrams for the remainder of the attempt window. A discovery
    response reporting a pre-lang-str protocol short-circuits to
    LEGACY; one reporting a lang-str-era protocol proves the host
    alive-and-new, turning final failure into UNRESPONSIVE rather than
    SILENT.
    """
    host_protocol: int | None = None
    while diag.attempts < _REQS_PROBE_ATTEMPTS:
        diag.attempts += 1
        reqs_query_id = os.urandom(4)
        disc_query_id = os.urandom(4)
        try:
            sock.send(
                bytes([_REQS_QUERY_PACKET_TYPE])
                + reqs_query_id
                + _requirements_query_payload(0)
            )
            if host_protocol is None:
                sock.send(bytes([_HOST_QUERY_PACKET_TYPE]) + disc_query_id)
            deadline = time.monotonic() + _REQS_ATTEMPT_TIMEOUT
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    break
                sock.settimeout(remaining)
                data = sock.recv(1500)
                if (
                    len(data) >= 5
                    and data[0] == _REQS_RESPONSE_PACKET_TYPE
                    and data[1:5] == reqs_query_id
                ):
                    result = _parse_requirements_response(data, page=0)
                    if result is None:
                        # Malformed data won't improve with retries and
                        # only a new host emits this packet type at all.
                        diag.note = f'malformed page-0 response ({data!r:.80})'
                        return HostProbeOutcome.UNRESPONSIVE
                    return result
                if (
                    host_protocol is None
                    and len(data) >= 9
                    and data[0] == _HOST_QUERY_RESPONSE_PACKET_TYPE
                    and data[1:5] == disc_query_id
                ):
                    host_protocol = int.from_bytes(data[5:9], 'little')
                    diag.host_protocol = host_protocol
                    if host_protocol < _LANG_STR_WIRE_PROTOCOL:
                        netlog.debug(
                            'Discovery response reports legacy protocol'
                            ' %d; no requirements to fetch.',
                            host_protocol,
                        )
                        return HostProbeOutcome.LEGACY
                    netlog.debug(
                        'Discovery response reports protocol %d; host is'
                        ' alive and requires the requirements exchange.',
                        host_protocol,
                    )
        except OSError as exc:
            # Includes the attempt-window timeout; loop back around.
            diag.record_error(exc)
            strip_exception_tracebacks(exc)
            continue
    return (
        HostProbeOutcome.SILENT
        if host_protocol is None
        else HostProbeOutcome.UNRESPONSIVE
    )


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


def connect_to_party(
    address: str, port: int = 43210, print_progress: bool = True
) -> bool:
    """Attempt to connect to a party at a given address.

    Runs the pre-join requirements exchange first: the prospective host
    is asked what it requires of joiners (its asset-package listing,
    etc.) and anything not yet locally available is downloaded -- with
    a cancelable progress dialog -- before the actual connection
    attempt happens. Hosts confirmed (via the legacy discovery query)
    to predate the requirements protocol get a plain immediate
    connect; hosts new enough to require the exchange never get an
    unprepped connect (a failed exchange fails the join).

    A request for the host a join is already in progress to is ignored
    (players tend to tap a join button repeatedly, and restarting the
    join each time would keep it from ever completing). Returns whether
    a new join attempt was started.

    (internal)
    """
    # pylint: disable=global-statement
    global _g_prejoin_task, _g_prejoin_target, _g_next_prejoin_id
    assert babase.in_logic_thread()

    if _is_join_pending(address, port):
        netlog.debug(
            'Ignoring connect request for %s:%d; already joining it.',
            address,
            port,
        )
        return False

    # Latest-wins: a new connect request cancels any pre-join exchange
    # still in flight (the user clicked a different party).
    if _g_prejoin_task is not None and not _g_prejoin_task.done():
        _g_prejoin_task.cancel()
    _g_prejoin_task = None

    prejoin_id = _g_next_prejoin_id
    _g_next_prejoin_id += 1
    _g_prejoin_target = (address, port, prejoin_id)

    # Give immediate feedback; the requirements exchange can take a few
    # seconds before the actual connect starts.
    if print_progress:
        # The wrapper import stays deferred: bascenev1 is fully imported
        # by the time this runs; the cycle pylint sees is structural
        # only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _builtinassets

        babase.screenmessage(_builtinassets.strings.net.connecting)

    babase.app.create_async_task(
        _prejoin_and_connect(address, port, print_progress, prejoin_id),
        name=f'connect_to_party {address}:{port}',
    )
    return True


def _is_join_pending(address: str, port: int) -> bool:
    """Is a join to this host already underway?

    Covers both the pre-join exchange and the native connection attempt
    that follows it (which gets cleared if it fails or times out).
    """
    if _g_prejoin_target is not None and _g_prejoin_target[:2] == (
        address,
        port,
    ):
        return True
    info = _bascenev1.get_connection_to_host_info_2()
    return info is not None and (info.address, info.port) == (address, port)


async def resolve_asset_packages_with_dialog(
    asset_packages: list[ApverNum],
    *,
    task: asyncio.Task[None] | None,
    context: str,
) -> bool:
    """Resolve asset-packages, downloading with a cancelable dialog.

    Shared by the pre-join (``connect_to_party``), pre-playback
    (``new_replay_session``) and character-preview (classic's
    ``_characterpreview``) content-prep paths. Returns True when the
    packages are locally available (having downloaded any that were
    missing), False if the user cancelled or a download failed (an
    error dialog / screen-message is shown in the failure case). The
    dialog is created lazily -- only if a real download begins -- so
    the all-local common case stays instant with no dialog flash.
    ``task`` is the enclosing async task, cancelled if the user hits the
    dialog's cancel button; ``context`` is a short label for logs.

    :meta private:
    """
    # The wrapper import stays deferred: bascenev1 is fully imported by
    # the time this runs; the cycle pylint sees is structural only.
    # pylint: disable-next=cyclic-import
    from bascenev1 import _builtinassets

    dialog: babase.SimpleDialog | None = None

    def on_cancel() -> None:
        if task is not None:
            task.cancel()

    def ensure_dialog() -> None:
        nonlocal dialog
        if dialog is None and babase.app.env.gui:
            dialog = babase.SimpleDialog(
                title=_builtinassets.strings.ui.updating,
                progress=0.0,
                button_label=_builtinassets.strings.ui.cancel,
                on_button=on_cancel,
                # (Also covers the OK the error path swaps in.)
                cancel_activates_button=True,
            )

    def on_update(
        message: str | babase.LangStr, progress: float | None
    ) -> None:
        if dialog is not None:
            dialog.update(
                message=message,
                progress=0.0 if progress is None else progress,
            )

    try:
        await babase.app.assets.resolve(
            asset_packages,
            allow_downloads=True,
            on_download_starting=ensure_dialog,
            on_progress=babase.make_progress_reporter(on_update),
            label='join content',
        )
    except asyncio.CancelledError:
        if dialog is not None:
            dialog.dismiss()
        netlog.info('Content download cancelled (%s).', context)
        return False
    except Exception as exc:
        # Per the no-mid-game-downloads design, proceeding without the
        # required content would just strand us (net: at the session
        # entry check; replay: at the first missing asset) -- so fail
        # cleanly here.
        specific = _resolve_failure_message(exc)
        message: str | babase.LangStr
        if specific is None:
            netlog.exception('Content resolve failed (%s).', context)
            message = _builtinassets.strings.net.unavailable_no_connection
        else:
            # An expected refusal (no access, sign-in needed, ...): say
            # why rather than logging it as an error.
            netlog.warning('Content resolve refused (%s): %s', context, exc)
            message = specific
        if dialog is not None:
            dialog.update(
                title=_builtinassets.strings.ui.error,
                message=message,
                progress=None,
                button_label=_builtinassets.strings.ui.ok,
                on_button=dialog.dismiss,
            )
        else:
            babase.screenmessage(message, color=(1, 0, 0))
        strip_exception_tracebacks(exc)
        return False
    if dialog is not None:
        dialog.dismiss()
    return True


def _resolve_failure_message(
    exc: Exception,
) -> str | babase.LangStr | None:
    """A specific message for an expected content-resolve refusal.

    None for anything unexpected (a network failure, a server bug),
    which gets the generic no-connection error instead.
    """
    # Deferred like _resolve_with_dialog's (the cycle is structural
    # only; bascenev1 is fully imported by the time this runs).
    # pylint: disable-next=cyclic-import
    from bascenev1 import _builtinassets

    if not isinstance(exc, babase.AssetResolveError) or exc.code is None:
        return None

    code = exc.code
    pkg = exc.package
    if pkg is not None and code in (
        AssetPackageResolveError.ACCESS_DENIED,
        AssetPackageResolveError.AUTH_REQUIRED,
    ):
        netstrs = _builtinassets.strings.net
        if code is AssetPackageResolveError.ACCESS_DENIED:
            return netstrs.asset_package_access_denied(
                package=pkg.name, owner=pkg.owner
            )
        return netstrs.asset_package_auth_required(
            package=pkg.name, owner=pkg.owner
        )
    if code in (
        AssetPackageResolveError.ACCESS_DENIED,
        AssetPackageResolveError.AUTH_REQUIRED,
        AssetPackageResolveError.CLIENT_TOO_OLD,
        AssetPackageResolveError.CONTENT,
    ):
        # The server's own wording (older servers name no package; it
        # also says what to do for an outdated build or broken source
        # content).
        return exc.server_message
    return None


class _Cancelled:
    """Sentinel: the user aborted the password prompt."""


async def _password_gate(address: str, port: int) -> str | _Cancelled:
    """Run the pre-join password prompt.

    Returns the entered password (delivered to the host as an
    HMAC-over-salt proof in the native connect path), or a
    :class:`_Cancelled` sentinel if the user backed out / no UI was
    available to prompt.
    """
    try:
        password = await babase.app.ui_v1.get_password()
    except asyncio.CancelledError:
        netlog.debug('Pre-join password prompt cancelled.')
        return _Cancelled()
    if password is None:
        # None covers both an explicit user cancel and
        # no-interactive-UI-available; the latter deserves a log since
        # nothing was ever shown on screen.
        if babase.app.env.gui:
            netlog.info('Pre-join password entry cancelled; aborting join.')
        else:
            netlog.warning(
                'Host %s:%d requires a password; cannot prompt without a'
                ' UI. Aborting join.',
                address,
                port,
            )
        return _Cancelled()
    return password


def _interpret_probe_result(
    proberesult: HostRequirements | HostProbeOutcome, address: str, port: int
) -> tuple[HostRequirements | None, bool]:
    """Translate a probe result into ``(requirements, proceed)``.

    ``requirements`` is None for confirmed-legacy hosts (which have
    none); ``proceed`` False means the join should be aborted (we
    couldn't learn the host's requirements).
    """
    if isinstance(proberesult, HostRequirements):
        return proberesult, True
    if proberesult is HostProbeOutcome.LEGACY:
        netlog.debug(
            'Host %s:%d confirmed pre-lang-str; connecting without'
            ' requirements.',
            address,
            port,
        )
        return None, True
    if proberesult in (
        HostProbeOutcome.SILENT,
        HostProbeOutcome.UNRESPONSIVE,
    ):
        # We couldn't learn the host's requirements. Never connect
        # anyway: a lang-str-era host would refuse the unprepped
        # handshake (or we'd strand), and old hosts are identified by
        # their discovery-query answer (LEGACY above), so silence
        # proves nothing about age. Fail like a standard connection
        # failure. (fetch_host_requirements already logged the
        # details.)
        # The wrapper import stays deferred: bascenev1 is fully imported
        # by the time this runs; the cycle pylint sees is structural
        # only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _builtinassets

        babase.screenmessage(
            _builtinassets.strings.net.connection_failed,
            color=(1, 0, 0),
        )
        return None, False
    assert_never(proberesult)


async def _prejoin_and_connect(
    address: str, port: int, print_progress: bool, prejoin_id: int
) -> None:
    """Requirements exchange + content downloads + the actual connect."""
    global _g_prejoin_task, _g_prejoin_target  # pylint: disable=global-statement
    task = asyncio.current_task()
    _g_prejoin_task = task
    password = ''
    try:
        try:
            proberesult = await babase.app.asyncio_loop.run_in_executor(
                babase.app.threadpool, fetch_host_requirements, address, port
            )
        except asyncio.CancelledError:
            netlog.debug('Pre-join requirements fetch cancelled.')
            return

        requirements, proceed = _interpret_probe_result(
            proberesult, address, port
        )
        if not proceed:
            return

        if requirements is not None and requirements.password_required:
            # Password gate runs first: no point downloading content for
            # a join the user then declines to enter a password for.
            gate_result = await _password_gate(address, port)
            if isinstance(gate_result, _Cancelled):
                return
            password = gate_result
        if requirements is not None and requirements.asset_packages:
            netlog.debug(
                'Host %s:%d requires %d asset-package(s); resolving.',
                address,
                port,
                len(requirements.asset_packages),
            )
            if not await resolve_asset_packages_with_dialog(
                requirements.asset_packages,
                task=task,
                context=f'join {address}:{port}',
            ):
                return

        # Remember the host's package universe; it is fixed for the
        # host's whole run (asset-packages.md decision #36), so it
        # bounds what host-defined ui may reference for this whole
        # connection.
        global _g_joined_host_asset_packages  # pylint: disable=global-statement
        _g_joined_host_asset_packages = (
            None
            if requirements is None
            else frozenset(requirements.asset_packages)
        )

        # Requirements are met (or the host has none); on to the
        # actual connection attempt. The prepped flag tells the native
        # layer the exchange ran; unprepped handshakes with
        # lang-str-era hosts get refused there as a structural
        # backstop.
        _bascenev1.connect_to_party(
            address,
            port=port,
            print_progress=print_progress,
            password=password,
            prepped=requirements is not None,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # A bug somewhere in the join path; don't leave the user
        # staring at 'Connecting...' with nothing happening.
        netlog.exception('Unexpected error joining %s:%d.', address, port)
        strip_exception_tracebacks(exc)
        # The wrapper import stays deferred: bascenev1 is fully imported
        # by the time this runs; the cycle pylint sees is structural
        # only.
        # pylint: disable-next=cyclic-import
        from bascenev1 import _builtinassets

        babase.screenmessage(
            _builtinassets.strings.net.connection_failed, color=(1, 0, 0)
        )
    finally:
        if _g_prejoin_task is task:
            _g_prejoin_task = None
        if _g_prejoin_target == (address, port, prejoin_id):
            _g_prejoin_target = None
