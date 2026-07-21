# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to net play."""

import os
import json
import socket
import asyncio
import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass, field

import babase

import _bascenev1

if TYPE_CHECKING:
    from typing import Any

netlog = logging.getLogger('ba.net')

# Wire packet-type bytes; must match BA_PACKET_HOST_REQUIREMENTS_QUERY
# / _RESPONSE in ballistica/base/networking/networking.h.
_REQS_QUERY_PACKET_TYPE = 40
_REQS_RESPONSE_PACKET_TYPE = 41

# The requirements exchange rides lossy UDP, so each page is retried a
# few times with short waits. A host that never answers is taken to be
# a legacy host predating the protocol (which by definition has no
# requirements).
_REQS_ATTEMPT_TIMEOUT = 0.75
_REQS_PAGE_ATTEMPTS = 3

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


def fetch_host_requirements(address: str, port: int) -> HostRequirements | None:
    """Fetch join requirements from a prospective host.

    Speaks the paged UDP requirements-query protocol (fragments merge
    across pages: lists concatenate, scalars are first-seen). Blocking
    (network waits up to a few seconds); call from a background thread.

    Returns None when the host never answers -- either a legacy host
    predating the protocol (nothing to require) or an unreachable/bogus
    address (in which case the subsequent connect attempt surfaces the
    error the user actually cares about).
    """
    try:
        infos = socket.getaddrinfo(address, port, type=socket.SOCK_DGRAM)
    except OSError:
        # Unresolvable address; let the real connect path report that.
        return None
    family, stype, proto, _canonname, sockaddr = infos[0]

    # Values here are parsed json, hence Any.
    merged: dict[str, Any] = {}
    page = 0
    page_count: int | None = None
    try:
        with socket.socket(family, stype, proto) as sock:
            # Connecting the socket pins the peer address, so the kernel
            # filters out datagrams from anyone but the host we asked.
            sock.connect(sockaddr)
            sock.settimeout(_REQS_ATTEMPT_TIMEOUT)
            while page_count is None or page < page_count:
                result = _fetch_requirements_page(sock, page)
                if result is None:
                    return None
                resp_page_count, fragment = result
                if page_count is None:
                    page_count = min(resp_page_count, _REQS_MAX_PAGES)
                for key, val in fragment.items():
                    if isinstance(val, list):
                        merged.setdefault(key, []).extend(val)
                    else:
                        merged.setdefault(key, val)
                page += 1
    except OSError:
        return None

    asset_packages = merged.get('ap')
    if not isinstance(asset_packages, list):
        asset_packages = []
    return HostRequirements(
        asset_packages=[pkg for pkg in asset_packages if isinstance(pkg, str)],
        password_required=bool(merged.get('pw')),
    )


def _fetch_requirements_page(
    sock: socket.socket, page: int
) -> tuple[int, dict[str, Any]] | None:
    """Fetch a single requirements page over a connected UDP socket.

    Returns ``(page_count, requirements_fragment)``, or None if the
    host never produced a valid response for this page.
    """
    query = json.dumps(
        {
            'v': 1,
            'b': babase.app.env.engine_build_number,
            'p': page,
        },
        separators=(',', ':'),
    ).encode()
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
        except TimeoutError, OSError:
            continue

        # Got a response to *this* query; validate it. A host serving
        # malformed data won't improve with retries, so treat that the
        # same as no response.
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
    return None


def connect_to_party(
    address: str, port: int = 43210, print_progress: bool = True
) -> None:
    """Attempt to connect to a party at a given address.

    Runs the pre-join requirements exchange first: the prospective host
    is asked what it requires of joiners (its asset-package listing,
    etc.) and anything not yet locally available is downloaded -- with
    a cancelable progress dialog -- before the actual connection
    attempt happens. Hosts predating the requirements protocol get a
    plain immediate connect.

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
            requirements = await babase.app.asyncio_loop.run_in_executor(
                babase.app.threadpool, fetch_host_requirements, address, port
            )
        except asyncio.CancelledError:
            netlog.debug('Pre-join requirements fetch cancelled.')
            return

        if requirements is None:
            netlog.debug(
                'No requirements response from %s:%d;'
                ' assuming legacy host with none.',
                address,
                port,
            )
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
            dialog: babase.SimpleDialog | None = None

            def on_cancel() -> None:
                if task is not None:
                    task.cancel()

            def ensure_dialog() -> None:
                # Lazily shown only if a real download begins (the
                # everything-already-local case stays instant with no
                # dialog flash).
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
                    requirements.asset_packages,
                    allow_downloads=True,
                    on_download_starting=ensure_dialog,
                    on_progress=babase.make_progress_reporter(on_update),
                )
            except asyncio.CancelledError:
                # User hit cancel (or clicked another party) -- bow out
                # of the whole join.
                if dialog is not None:
                    dialog.dismiss()
                netlog.info('Pre-join content download cancelled.')
                return
            except Exception:
                # Per the no-mid-game-downloads design, joining without
                # the host's content would just strand us at the
                # session entry check -- so fail the join cleanly here.
                netlog.exception(
                    'Pre-join content resolve failed for %s:%d.',
                    address,
                    port,
                )
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
                        babase.Lstr(
                            resource='internal.unavailableNoConnectionText'
                        ),
                        color=(1, 0, 0),
                    )
                return
            if dialog is not None:
                dialog.dismiss()

        # Requirements are met (or the host has none); on to the
        # actual connection attempt.
        _bascenev1.connect_to_party(
            address,
            port=port,
            print_progress=print_progress,
            password=password,
        )
    finally:
        if _g_prejoin_task is task:
            _g_prejoin_task = None
