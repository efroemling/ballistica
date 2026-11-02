# Released under the MIT License. See LICENSE for details.
#
"""Squads functionality (in development for 1.9)."""

# ba_meta require api 9

# Package up various private bits (including stuff from our native
# module) into a nice clean public API.
from basquads._appmode import SquadsAppMode
from basquads._appsubsystem import SquadsAppSubsystem

__all__ = [
    'SquadsAppMode',
    'SquadsAppSubsystem',
]
