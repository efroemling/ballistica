# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""

import socket
import threading
import ipaddress
from typing import TYPE_CHECKING

import _babase

if TYPE_CHECKING:
    pass


class NetworkSubsystem:
    """Network related app subsystem."""

    def __init__(self) -> None:
        import babase._env

        assert babase._env._g_net_warm_start_thread is not None
        babase._env._g_net_warm_start_thread.join()
        babase._env._g_net_warm_start_thread = None

        assert babase._env._g_net_warm_start_ssl_context is not None
        self.sslcontext = babase._env._g_net_warm_start_ssl_context
        babase._env._g_net_warm_start_ssl_context = None

        assert babase._env._g_net_warm_start_pool_manager is not None
        self.urllib3pool = babase._env._g_net_warm_start_pool_manager
        babase._env._g_net_warm_start_pool_manager = None

        # Anyone accessing/modifying zone_pings should hold this lock,
        # as it is updated by a background thread.
        self.zone_pings_lock = threading.Lock()

        # Zone IDs mapped to average pings. This will remain empty
        # until enough pings have been run to be reasonably certain
        # that a nearby server has been pinged.
        self.zone_pings: dict[str, float] = {}

        # For debugging/progress.
        self.connectivity_state = ''
        self.transport_state = ''
        self.server_time_offset_hours: float | None = None

        # OS-reported network path availability. Updated by a
        # callback that may fire on any thread; the GIL makes the
        # bare bool write/read safe. Defaults to False per the
        # platform API contract: "assume unavailable until informed
        # otherwise". The registration below installs the callback;
        # platforms with no native implementation flip us to True
        # promptly via the default monitoring-start path.
        self._available: bool = False
        _babase.add_network_availability_callback(self._on_availability_changed)

    def _on_availability_changed(self, available: bool) -> None:
        self._available = available

    @property
    def available(self) -> bool:
        """Whether the OS reports a usable network path is available.

        Useful as a 'don't even try' gate for things like connectivity
        pings and retry loops — when ``False`` (airplane mode, wifi
        off with no cellular, ethernet unplugged) network attempts
        will not succeed and should be skipped.

        Note that ``True`` does *not* mean internet actually works —
        captive portals, ISP outages, and DNS issues will still report
        ``True``. Callers that need confirmed reachability should
        continue running their existing probes; this property only
        confirms *non-functional* states.
        """
        return self._available

    def pre_interpreter_shutdown(self) -> None:
        """Called just before interpreter shuts down."""
        self.urllib3pool.clear()


def get_ip_address_type(addr: str) -> socket.AddressFamily:
    """Return an address-type given an address.

    Can be :attr:`socket.AF_INET` or :attr:`socket.AF_INET6`.
    """

    version = ipaddress.ip_address(addr).version
    if version == 4:
        return socket.AF_INET
    assert version == 6
    return socket.AF_INET6
