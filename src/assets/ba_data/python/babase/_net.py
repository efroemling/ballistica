# Released under the MIT License. See LICENSE for details.
#
"""Networking related functionality."""
from __future__ import annotations

import ssl
import socket
import threading
import ipaddress
from typing import TYPE_CHECKING

import urllib3

import _babase

if TYPE_CHECKING:
    pass

# Timeout for standard functions talking to the master-server/etc. We
# generally try to fail fast and retry instead of waiting a long time
# for things.
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10


class NetworkSubsystem:
    """Network related app subsystem."""

    def __init__(self) -> None:
        # Our shared SSL context. Creating these can be expensive so we
        # create it here once and recycle for our various connections.
        self.sslcontext = ssl.create_default_context()

        # I'm finding that urllib3 exceptions tend to give us reference
        # cycles, which we want to avoid as much as possible. We can
        # work around this by gutting the exceptions using
        # efro.util.strip_exception_tracebacks() after handling them.
        # Unfortunately this means we need to turn off retries here
        # since the retry mechanism effectively hides exceptions from
        # us.
        self.urllib3pool = urllib3.PoolManager(
            retries=False,
            ssl_context=self.sslcontext,
            timeout=urllib3.util.Timeout(total=DEFAULT_REQUEST_TIMEOUT_SECONDS),
            maxsize=5,
            headers={'User-Agent': _babase.user_agent_string()},
        )

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
        self.connectivity_state = ''
        self.transport_state = ''
        self.server_time_offset_hours: float | None = None

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
