# Released under the MIT License. See LICENSE for details.
#
"""Using a device as a game controller (in development for 1.9)."""

# ba_meta require api 9

# Package up various private bits (including stuff from our native
# module) into a nice clean public API.
from baremote._appmode import RemoteAppMode
from baremote._appsubsystem import RemoteAppSubsystem

__all__ = [
    'RemoteAppMode',
    'RemoteAppSubsystem',
]
