# Released under the MIT License. See LICENSE for details.
#
"""Finding games and other app instances on nearby networks."""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import _babase
from babase._appsubsystem import AppSubsystem

if TYPE_CHECKING:
    from typing import Callable

    from babase._nearbyimpl import NearbyDiscoveryThread

logger = logging.getLogger('ba.net')


class NearbyService(Enum):
    """Something a nearby host can offer."""

    #: A game that can be joined.
    GAME = 'game'

    #: A game that accepts remote-app controllers.
    REMOTE = 'remote'


class NearbyRouteType(Enum):
    """How a :class:`NearbyRoute` reaches its host.

    Only plain addresses exist today, but other kinds of connection
    (such as Apple peer-to-peer links) may join later, so code acting
    on a route should handle every type explicitly.
    """

    #: A plain IP address and port that the game's normal UDP
    #: networking can talk to.
    UDP = 'udp'


class NearbySource(Enum):
    """How a route to a nearby host was found."""

    #: Subnet broadcast queries (plus a query to this device itself).
    BROADCAST = 'broadcast'

    #: DNS-SD (Bonjour/mDNS) service browsing.
    DNS_SD = 'dns_sd'

    #: An address a scan was explicitly asked to check.
    TARGET = 'target'


@dataclass(frozen=True)
class NearbyRoute:
    """One way to reach a nearby host."""

    type: NearbyRouteType
    address: str
    port: int

    #: Smoothed round-trip time in seconds, or None if unmeasured
    #: (hosts too old to echo our query ids).
    rtt: float | None

    sources: frozenset[NearbySource]


@dataclass(frozen=True)
class NearbyGameInfo:
    """What a joinable nearby game says about itself."""

    #: The host's player-spec string (account name and type).
    player_spec: str

    #: Empty if the host isn't advertising a party name (or is too old
    #: to say).
    party_name: str

    #: Zero if unknown.
    party_size: int
    party_max_size: int
    auth_required: bool

    #: Zero if unknown.
    build_number: int
    protocol_version: int


@dataclass(frozen=True)
class NearbyRemoteInfo:
    """What a nearby game accepting remote controllers says about itself."""

    #: The host device's name.
    name: str

    #: Zero if unknown (hosts too old to say).
    build_number: int


@dataclass(frozen=True)
class NearbyHost:
    """A nearby host: one app instance, however many ways it was found.

    Hosts are deduplicated by app-instance-uuid; each keeps every route
    it answered on, ranked by measured round-trip time.
    """

    #: Unique per host -- its app-instance-uuid, or ``legacy:ADDR:PORT``
    #: for old hosts that don't send one.
    key: str

    #: The best route; also first in :attr:`routes`.
    route: NearbyRoute

    routes: tuple[NearbyRoute, ...]

    #: Set if the host answered as a joinable game.
    game: NearbyGameInfo | None

    #: Set if the host answered as accepting remote controllers.
    remote: NearbyRemoteInfo | None

    @property
    def services(self) -> frozenset[NearbyService]:
        """What this host offers."""
        out: set[NearbyService] = set()
        if self.game is not None:
            out.add(NearbyService.GAME)
        if self.remote is not None:
            out.add(NearbyService.REMOTE)
        return frozenset(out)


class NearbyScan:
    """An ongoing search for nearby hosts.

    Get one from :meth:`babase.NearbySubsystem.scan` and call :meth:`stop` when
    done; discovery runs while any scan is active.
    """

    def __init__(
        self,
        subsystem: NearbySubsystem,
        services: frozenset[NearbyService],
        targets: frozenset[tuple[str, int]] | None,
        on_change: Callable[[], None] | None,
    ) -> None:
        self._subsystem = subsystem
        self._services = services
        self._targets = targets
        self._on_change = on_change
        self._hosts: list[NearbyHost] = []
        self.active = True

    @property
    def services(self) -> frozenset[NearbyService]:
        """The services this scan looks for."""
        return self._services

    @property
    def targets(self) -> frozenset[tuple[str, int]] | None:
        """Addresses this scan is limited to, if any."""
        return self._targets

    @property
    def hosts(self) -> list[NearbyHost]:
        """Hosts found so far offering any of our services.

        Sorted by key, so the order is stable as round-trip times move
        around.
        """
        return self._hosts

    def stop(self) -> None:
        """Stop scanning (idempotent)."""
        if self.active:
            self.active = False
            self._on_change = None
            self._subsystem.remove_scan(self)

    def apply(self, hosts: list[NearbyHost], notify: bool = True) -> None:
        """Take a new host list from the subsystem.

        :meta private:
        """
        mine = [h for h in hosts if self._wants(h)]
        if mine == self._hosts:
            return
        self._hosts = mine
        if notify and self._on_change is not None:
            self._on_change()

    def _wants(self, host: NearbyHost) -> bool:
        if not host.services & self._services:
            return False
        if self._targets is None:
            return True
        return any((r.address, r.port) in self._targets for r in host.routes)


class NearbySubsystem(AppSubsystem):
    """Finds games and other app instances on nearby networks.

    Access the single shared instance of this class via
    :attr:`babase.App.nearby`.

    All discovery methods feed one deduplicated host list: subnet
    broadcast queries (understood by every game version) and, where the
    OS supports it, DNS-SD (Bonjour) browsing. Every address found is
    probed directly, and each host's routes are ranked by measured
    round-trip time, so whichever path is fastest ends up as its
    :attr:`NearbyHost.route`.

    Discovery runs on its own thread, only while a :class:`NearbyScan`
    is active and the app isn't suspended.
    """

    def __init__(self) -> None:
        self._scans: list[NearbyScan] = []
        self._hosts: list[NearbyHost] = []
        self._thread: NearbyDiscoveryThread | None = None
        self._suspended = False
        self._shutting_down = False

    @property
    def hosts(self) -> list[NearbyHost]:
        """Everything currently found (for any active scan)."""
        return self._hosts

    def scan(
        self,
        services: set[NearbyService] | frozenset[NearbyService],
        *,
        targets: list[tuple[str, int]] | None = None,
        on_change: Callable[[], None] | None = None,
    ) -> NearbyScan:
        """Start looking for nearby hosts offering any of ``services``.

        ``on_change`` is called (in the logic thread) whenever the
        scan's :attr:`~NearbyScan.hosts` changes, including round-trip
        time updates. It is not called for hosts already known when the
        scan starts; those are in :attr:`~NearbyScan.hosts` right away,
        so read it after starting. Pass ``targets`` to check only those
        addresses (no broadcasts or service browsing on their behalf);
        useful in testing so as not to latch onto other games on the
        network.
        """
        assert _babase.in_logic_thread()
        scan = NearbyScan(
            self,
            frozenset(services),
            None if targets is None else frozenset(targets),
            on_change,
        )
        self._scans.append(scan)
        scan.apply(self._hosts, notify=False)
        self._update_discovery()
        return scan

    def remove_scan(self, scan: NearbyScan) -> None:
        """Called by a scan when it stops.

        :meta private:
        """
        assert _babase.in_logic_thread()
        if scan in self._scans:
            self._scans.remove(scan)
        self._update_discovery()

    @override
    def on_app_suspend(self) -> None:
        self._suspended = True
        self._update_discovery()

    @override
    def on_app_unsuspend(self) -> None:
        self._suspended = False
        self._update_discovery()

    @override
    def on_app_shutdown(self) -> None:
        self._shutting_down = True
        self._update_discovery()

    def _update_discovery(self) -> None:
        """Start, stop, or reconfigure the discovery thread."""
        # pylint: disable=cyclic-import
        from babase._nearbyimpl import (
            NearbyDiscoveryThread,
            DiscoveryConfig,
        )

        want = bool(self._scans) and not (
            self._suspended or self._shutting_down
        )
        if not want:
            if self._thread is not None:
                self._thread.stop()
                self._thread = None
            if self._hosts:
                self._apply_hosts([])
            return

        services: set[NearbyService] = set()
        targets: set[tuple[str, int]] = set()
        open_scan = False
        for scan in self._scans:
            services |= scan.services
            if scan.targets is None:
                open_scan = True
            else:
                targets |= scan.targets
        config = DiscoveryConfig(
            services=frozenset(services),
            open_scan=open_scan,
            targets=frozenset(targets),
        )
        if self._thread is None:
            self._thread = NearbyDiscoveryThread(
                config=config, on_hosts=self._on_hosts_from_thread
            )
            self._thread.start()
        else:
            self._thread.set_config(config)

    def _on_hosts_from_thread(
        self, thread: NearbyDiscoveryThread, hosts: list[NearbyHost]
    ) -> None:
        """New host list from the discovery thread (logic thread)."""
        # Ignore stragglers from a thread we've since stopped.
        if thread is not self._thread:
            return
        self._apply_hosts(hosts)

    def _apply_hosts(self, hosts: list[NearbyHost]) -> None:
        self._hosts = hosts
        for scan in list(self._scans):
            scan.apply(hosts)
