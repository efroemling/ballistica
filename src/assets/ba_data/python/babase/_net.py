# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""
from __future__ import annotations

import ssl
import socket
import threading
import ipaddress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Timeout for standard functions talking to the master-server/etc.
DEFAULT_REQUEST_TIMEOUT_SECONDS = 60


class NetworkSubsystem:
    """Network related app subsystem."""

    def __init__(self) -> None:
        # Our shared SSL context. Creating these can be expensive so we
        # create it here once and recycle for our various connections.
        self.sslcontext = ssl.create_default_context()

        # Anyone accessing/modifying zone_pings should hold this lock,
        # as it is updated by a background thread.
        self.zone_pings_lock = threading.Lock()

        # Zone IDs mapped to average pings. This will remain empty
        # until enough pings have been run to be reasonably certain
        # that a nearby server has been pinged.
        self.zone_pings: dict[str, float] = {}

        # For debugging/progress.
        self.v1_test_log: str = ''
        self.v1_ctest_results: dict[int, str] = {}
        self.connectivity_state = 'uninited'
        self.transport_state = 'uninited'
        self.server_time_offset_hours: float | None = None


def get_ip_address_type(addr: str) -> socket.AddressFamily:
    """Return socket.AF_INET6 or socket.AF_INET4 for the provided address."""

    version = ipaddress.ip_address(addr).version
    if version == 4:
        return socket.AF_INET
    assert version == 6
    return socket.AF_INET6
