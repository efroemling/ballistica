# Released under the MIT License. See LICENSE for details.
#
"""Closed-source bits of ballistica."""

from __future__ import annotations

# Note: there's not much here.
# All comms with this feature-set should go through app.plus.

import logging

from baplus._subsystem import PlusSubsystem

__all__ = [
    'PlusSubsystem',
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
