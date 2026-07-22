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
# with short waits. Once a host has *proven* alive-and-new (it answered
# the discovery query reporting a lang-str-era protocol), the budget
# extends: at that point silence is definitely loss, not oldness.
_REQS_ATTEMPT_TIMEOUT = 0.75
_REQS_PAGE_ATTEMPTS = 3
_REQS_PAGE_ATTEMPTS_ALIVE = 8

# Refuse to chase absurd page counts from a hostile/buggy host.
_REQS_MAX_PAGES = 64

# The in-flight pre-join task, if any (see connect_to_party's
# latest-wins behavior).
_g_prejoin_task: asyncio.Task[None] | None = None


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

    asset_packages: list[str] = field(default_factory=list)
    password_required: bool = False


class HostProbeOutcome(Enum):
    """No-requirements outcomes of :func:`fetch_host_requirements`."""

    #: The host answered the legacy discovery query reporting a
    #: pre-lang-str protocol: a confirmed old host with no requirements
    #: to fetch. Connect immediately.
    LEGACY = 'legacy'

    #: Nothing answered anything -- the address is unreachable, bogus,
    #: or down. The plain connect attempt surfaces the error the user
    #: actually cares about.
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
    :class:`HostProbeOutcome` describing why there are none.
    """
    try:
        infos = socket.getaddrinfo(address, port, type=socket.SOCK_DGRAM)
    except OSError:
        # Unresolvable address; let the real connect path report that.
        return HostProbeOutcome.SILENT
    family, stype, proto, _canonname, sockaddr = infos[0]

    # Values here are parsed json, hence Any.
    merged: dict[str, Any] = {}
    try:
        with socket.socket(family, stype, proto) as sock:
            # Connecting the socket pins the peer address, so the kernel
            # filters out datagrams from anyone but the host we asked.
            sock.connect(sockaddr)

            first = _probe_page_zero(sock)
            if isinstance(first, HostProbeOutcome):
                return first
            resp_page_count, fragment = first
            page_count = min(resp_page_count, _REQS_MAX_PAGES)
            _merge_requirements_fragment(merged, fragment)

            sock.settimeout(_REQS_ATTEMPT_TIMEOUT)
            for page in range(1, page_count):
                result = _fetch_requirements_page(sock, page)
                if result is None:
                    # The host proved itself new by answering page 0
                    # but went dark mid-listing; joining on a partial
                    # listing could only strand.
                    return HostProbeOutcome.UNRESPONSIVE
                _, fragment = result
                _merge_requirements_fragment(merged, fragment)
    except OSError:
        return HostProbeOutcome.SILENT

    asset_packages = merged.get('ap')
    if not isinstance(asset_packages, list):
        asset_packages = []
    return HostRequirements(
        asset_packages=[pkg for pkg in asset_packages if isinstance(pkg, str)],
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


def _probe_page_zero(
    sock: socket.socket,
) -> tuple[int, dict[str, Any]] | HostProbeOutcome:
    """Run the combined discovery + requirements-page-0 probe.

    Each attempt sends the requirements query for page 0 plus (until
    one is answered) a legacy discovery query, then sorts incoming
    datagrams for the remainder of the attempt window. A discovery
    response reporting a pre-lang-str protocol short-circuits to
    LEGACY; one reporting a lang-str-era protocol proves the host
    alive-and-new, extending the retry budget and turning final
    failure into UNRESPONSIVE rather than SILENT.
    """
    host_protocol: int | None = None
    attempts = 0
    while attempts < (
        _REQS_PAGE_ATTEMPTS
        if host_protocol is None
        else _REQS_PAGE_ATTEMPTS_ALIVE
    ):
        attempts += 1
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
                        return HostProbeOutcome.UNRESPONSIVE
                    return result
                if (
                    host_protocol is None
                    and len(data) >= 9
                    and data[0] == _HOST_QUERY_RESPONSE_PACKET_TYPE
                    and data[1:5] == disc_query_id
                ):
                    host_protocol = int.from_bytes(data[5:9], 'little')
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
        except OSError:
            # Includes the attempt-window timeout; loop back around.
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
    sock: socket.socket, page: int
) -> tuple[int, dict[str, Any]] | None:
    """Fetch a single requirements page over a connected UDP socket.

    Returns ``(page_count, requirements_fragment)``, or None if the
    host never produced a valid response for this page.
    """
    query = _requirements_query_payload(page)
    for _attempt in range(_REQS_PAGE_ATTEMPTS):
        query_id = os.urandom(4)
        try:
            sock.send(bytes([_REQS_QUERY_PACKET_TYPE]) + query_id + query)
            while True:
                data = sock.recv(1500)
                if (
                    len(data) >= 5
                    and data[0] == _REQS_RESPONSE_PACKET_TYPE
                    and data[1:5] == query_id
                ):
                    break
        except OSError:
            continue

        # Got a response to *this* query; validate it. A host serving
        # malformed data won't improve with retries, so treat that the
        # same as no response.
        return _parse_requirements_response(data, page)
    return None


def connect_to_party(
    address: str, port: int = 43210, print_progress: bool = True
) -> None:
    """Attempt to connect to a party at a given address.

    Runs the pre-join requirements exchange first: the prospective host
    is asked what it requires of joiners (its asset-package listing,
    etc.) and anything not yet locally available is downloaded -- with
    a cancelable progress dialog -- before the actual connection
    attempt happens. Hosts confirmed (via the legacy discovery query)
    to predate the requirements protocol get a plain immediate
    connect; hosts new enough to require the exchange never get an
    unprepped connect (a failed exchange fails the join).

    (internal)
    """
    assert babase.in_logic_thread()

    # Latest-wins: a new connect request cancels any pre-join exchange
    # still in flight (the user clicked a different party).
    global _g_prejoin_task  # pylint: disable=global-statement
    if _g_prejoin_task is not None and not _g_prejoin_task.done():
        _g_prejoin_task.cancel()
    _g_prejoin_task = None

    babase.app.create_async_task(
        _prejoin_and_connect(address, port, print_progress),
        name=f'connect_to_party {address}:{port}',
    )


async def resolve_asset_packages_with_dialog(
    asset_packages: list[str],
    *,
    task: asyncio.Task[None] | None,
    context: str,
) -> bool:
    """Resolve asset-packages, downloading with a cancelable dialog.

    Shared by the pre-join (``connect_to_party``) and pre-playback
    (``new_replay_session``) content-prep paths. Returns True when the
    packages are locally available (having downloaded any that were
    missing), False if the user cancelled or a download failed (an
    error dialog / screen-message is shown in the failure case). The
    dialog is created lazily -- only if a real download begins -- so
    the all-local common case stays instant with no dialog flash.
    ``task`` is the enclosing async task, cancelled if the user hits the
    dialog's cancel button; ``context`` is a short label for logs.
    """
    dialog: babase.SimpleDialog | None = None

    def on_cancel() -> None:
        if task is not None:
            task.cancel()

    def ensure_dialog() -> None:
        nonlocal dialog
        if dialog is None and babase.app.env.gui:
            dialog = babase.SimpleDialog(
                title=babase.Lstr(resource='updatingText'),
                progress=0.0,
                button_label=babase.Lstr(resource='cancelText'),
                on_button=on_cancel,
            )

    def on_update(message: str, progress: float | None) -> None:
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
        )
    except asyncio.CancelledError:
        if dialog is not None:
            dialog.dismiss()
        netlog.info('Content download cancelled (%s).', context)
        return False
    except Exception:
        # Per the no-mid-game-downloads design, proceeding without the
        # required content would just strand us (net: at the session
        # entry check; replay: at the first missing asset) -- so fail
        # cleanly here.
        netlog.exception('Content resolve failed (%s).', context)
        if dialog is not None:
            dialog.update(
                title=babase.Lstr(resource='errorText'),
                message=babase.Lstr(
                    resource='internal.unavailableNoConnectionText'
                ),
                progress=None,
                button_label=babase.Lstr(resource='okText'),
                on_button=dialog.dismiss,
            )
        else:
            babase.screenmessage(
                babase.Lstr(resource='internal.unavailableNoConnectionText'),
                color=(1, 0, 0),
            )
        return False
    if dialog is not None:
        dialog.dismiss()
    return True


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

    ``requirements`` is None for hosts with none (confirmed-legacy or
    silent); ``proceed`` False means the join should be aborted (an
    alive new host that wouldn't complete the exchange).
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
    if proberesult is HostProbeOutcome.SILENT:
        netlog.debug(
            'No probe response from %s:%d; proceeding to the plain'
            ' connect (it surfaces unreachable-host errors).',
            address,
            port,
        )
        return None, True
    if proberesult is HostProbeOutcome.UNRESPONSIVE:
        # The host is alive and new but wouldn't complete the exchange;
        # joining unprepped could only strand us (and the native
        # handshake gate would refuse it anyway). Fail like a standard
        # connection failure.
        netlog.warning(
            'Host %s:%d is alive but did not complete the requirements'
            ' exchange; aborting join.',
            address,
            port,
        )
        babase.screenmessage(
            babase.Lstr(resource='internal.connectionFailedText'),
            color=(1, 0, 0),
        )
        return None, False
    assert_never(proberesult)


async def _prejoin_and_connect(
    address: str, port: int, print_progress: bool
) -> None:
    """Requirements exchange + content downloads + the actual connect."""
    global _g_prejoin_task  # pylint: disable=global-statement
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
    finally:
        if _g_prejoin_task is task:
            _g_prejoin_task = None
