# Released under the MIT License. See LICENSE for details.
#
"""Ballistica Template Feature Set - just an example."""

# ba_meta require api 9

# Package up various private bits (including stuff from our native
# module) into a nice clean public API.
from _batemplatefs import hello_again_world
from batemplatefs._appsubsystem import TemplateFsAppSubsystem

__all__ = [
    'TemplateFsAppSubsystem',
    'hello_again_world',
]
