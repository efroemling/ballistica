# Released under the MIT License. See LICENSE for details.
#
"""Classic ballistica components.

This package is used as a 'dumping ground' for functionality that is
necessary to keep legacy parts of the app working, but which may no
longer be the best way to do things going forward.

New code should try to avoid using code from here when possible.

Functionality in this package should be exposed through the
ClassicSubsystem. This allows type-checked code to go through the
babase.app.classic singleton which forces it to explicitly handle the
possibility of babase.app.classic being None. When code instead imports
classic submodules directly, it is much harder to make it cleanly handle
classic not being present.
"""

# ba_meta require api 8

# Note: Code relying on classic should import things from here *only*
# for type-checking and use the versions in app.classic at runtime; that
# way type-checking will cleanly cover the classic-not-present case
# (app.classic being None).
import logging

from baclassic._subsystem import ClassicSubsystem
from baclassic._achievement import Achievement, AchievementSubsystem

__all__ = [
    'ClassicSubsystem',
    'Achievement',
    'AchievementSubsystem',
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
