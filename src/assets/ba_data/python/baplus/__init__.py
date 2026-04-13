# Released under the MIT License. See LICENSE for details.
#
"""Closed-source bits of ballistica.

This code concerns sensitive things like accounts and master-server
communication, so the native C++ parts of it remain closed. Native
precompiled static libraries of this portion are provided for those who
want to compile the rest of the engine, or a fully open-source app can
also be built by removing this feature-set.
"""

# ba_meta require api 9

# Note: Stuff in this module mostly exists for type-checking and docs
# generation and should generally not be imported or used at runtime.
# Generally all interaction with this feature-set should go through
# `ba*.app.plus`.

import logging

from baplus._cloud import CloudSubsystem
from baplus._appsubsystem import PlusAppSubsystem
from baplus._ads import AdsSubsystem

__all__ = [
    'AdsSubsystem',
    'CloudSubsystem',
    'PlusAppSubsystem',
]

# Sanity check: we want to keep ballistica's dependencies and
# bootstrapping order clearly defined; let's check a few particular
# modules to make sure they never directly or indirectly import us
# before their own execs complete.
if __debug__:
    for _mdl in 'babase', '_babase':
        if not hasattr(__import__(_mdl), '_REACHED_END_OF_MODULE'):
            logging.warning(
                '%s was imported before %s finished importing;'
                ' should not happen.',
                __name__,
                _mdl,
            )
