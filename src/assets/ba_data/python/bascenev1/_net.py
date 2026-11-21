# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to net play."""

import asyncio
import logging
from typing import TYPE_CHECKING, assert_never
from dataclasses import dataclass

from efro.util import strip_exception_tracebacks
from bacommon.assetpackage import AssetPackageResolveError

import babase

import _bascenev1
from bascenev1._hostprobe import (
    HostProbeOutcome,
    HostRequirements,
    probe_host,
)

if TYPE_CHECKING:
    from typing import Sequence

    from bacommon.assetpackage import ApverNum

netlog = logging.getLogger('ba.net')

# The in-flight pre-join task, if any (see connect_to_party's
# latest-wins behavior).
_g_prejoin_task: asyncio.Task[None] | None = None

# The addresses/port of the in-flight pre-join, plus an id unique to
# that request. Set synchronously by connect_to_party (the task itself
# only starts on a later loop pass) so repeat requests are caught at
# once.
_g_prejoin_target: tuple[tuple[str, ...], int, int] | None = None
_g_next_prejoin_id = 0

# The addresses asked for in our most recent native connection attempt,
# and the one it actually used (the probe's winner).
_g_native_join: tuple[tuple[str, ...], str] | None = None

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


def get_party_member_names() -> dict[int, str]:
    """Each party member's name as party lists show it, by client id.

    That's their account's name (or, if not signed in, their device's);
    -1 is the host. Repeated names get numbered in roster order
    ("iPhone", "iPhone 2", ...), which every peer sees the same, so the
    host and its clients agree on who is who.

    :meta private:
    """
    names: dict[int, str] = {}
    counts: dict[str, int] = {}
    for entry in _bascenev1.get_game_roster():
        client_id = entry['client_id']
        name = entry['display_string']
        if not isinstance(client_id, int) or not isinstance(name, str):
            continue
        count = counts[name] = counts.get(name, 0) + 1
        names[client_id] = name if count == 1 else f'{name} {count}'
    return names


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

    # Whether the host lets clients save it to their favorites (see
    # :func:`set_host_allow_favorites`).
    allow_favorites: bool = True


def connect_to_party(
    address: str | Sequence[str],
    port: int = 43210,
    print_progress: bool = True,
) -> bool:
    """Attempt to connect to a party at a given address.

    ``address`` may be an IP address or hostname, or several of them
    for the same host (say its IPv6 and IPv4 addresses, or every route
    nearby discovery knows); they are raced, preferring earlier ones,
    and the join uses whichever answers first (see
    :func:`fetch_host_requirements`).

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

    addresses = (address,) if isinstance(address, str) else tuple(address)
    if not addresses:
        raise ValueError('No address given.')
    label = addresses[0] if len(addresses) == 1 else ', '.join(addresses)

    if _is_join_pending(addresses, port):
        netlog.debug(
            'Ignoring connect request for %s:%d; already joining it.',
            label,
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
    _g_prejoin_target = (addresses, port, prejoin_id)

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
        _prejoin_and_connect(
            addresses, label, port, print_progress, prejoin_id
        ),
        name=f'connect_to_party {label}:{port}',
    )
    return True


def _is_join_pending(addresses: tuple[str, ...], port: int) -> bool:
    """Is a join to this host already underway?

    Covers both the pre-join exchange and the native connection attempt
    that follows it (which gets cleared if it fails or times out). Any
    overlap with the addresses of the join underway counts.
    """
    if (
        _g_prejoin_target is not None
        and _g_prejoin_target[1] == port
        and set(_g_prejoin_target[0]) & set(addresses)
    ):
        return True
    info = _bascenev1.get_connection_to_host_info_2()
    if info is None or info.port != port:
        return False
    if info.address in addresses:
        return True
    # The native connection uses the address that won the probe, which
    # can differ from what was asked for (a hostname, a NAT64-translated
    # literal, the IPv6 one of several...).
    return (
        _g_native_join is not None
        and _g_native_join[1] == info.address
        and bool(set(_g_native_join[0]) & set(addresses))
    )


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
    addresses: tuple[str, ...],
    address: str,
    port: int,
    print_progress: bool,
    prejoin_id: int,
) -> None:
    """Requirements exchange + content downloads + the actual connect.

    (``address`` is a label for messages; ``addresses`` is what we
    actually try.)
    """
    # pylint: disable=global-statement
    global _g_prejoin_task, _g_prejoin_target, _g_native_join
    task = asyncio.current_task()
    _g_prejoin_task = task
    password = ''
    try:
        try:
            proberesult, connect_address = (
                await babase.app.asyncio_loop.run_in_executor(
                    babase.app.threadpool, probe_host, addresses, port
                )
            )
        except asyncio.CancelledError:
            netlog.debug('Pre-join requirements fetch cancelled.')
            return

        requirements, proceed = _interpret_probe_result(
            proberesult, address, port
        )
        if not proceed:
            return
        # (Anything but a failure means some address answered.)
        assert connect_address is not None

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
        # actual connection attempt, at the resolved address that
        # answered the probe -- never the raw text, which on an
        # IPv6-only network (NAT64; what App Review tests on) may only
        # work in its synthesized IPv6 form. The prepped flag tells the
        # native layer the exchange ran; unprepped handshakes with
        # lang-str-era hosts get refused there as a structural
        # backstop.
        if connect_address not in addresses:
            netlog.debug(
                'Joining %s:%d via %s.', address, port, connect_address
            )
        _g_native_join = (addresses, connect_address)
        _bascenev1.connect_to_party(
            connect_address,
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
        if _g_prejoin_target == (addresses, port, prejoin_id):
            _g_prejoin_target = None
