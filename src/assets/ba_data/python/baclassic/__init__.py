# Released under the MIT License. See LICENSE for details.
#
"""Components for the classic BombSquad experience.

This package is used as a dumping ground for functionality that is
necessary to keep classic BombSquad working, but which may no longer be
the best way to do things going forward.

New code should try to avoid using code from here when possible.

Functionality in this package should be exposed through the
ClassicAppSubsystem. This allows type-checked code to go through the
babase.app.classic singleton which forces it to explicitly handle the
possibility of babase.app.classic being None. When code instead imports
classic submodules directly, it is much harder to make it cleanly handle
classic not being present.
"""

# ba_meta require api 9

# Note: Code relying on classic should import things from here *only*
# for type-checking and use the versions in ba*.app.classic at runtime;
# that way type-checking will cleanly cover the classic-not-present case
# (ba*.app.classic being None).
import logging

from efro.util import set_canonical_module_names

from baclassic._appmode import ClassicAppMode
from baclassic._appsubsystem import ClassicAppSubsystem
from baclassic._achievement import Achievement, AchievementSubsystem

__all__ = [
    'ClassicAppMode',
    'ClassicAppSubsystem',
    'Achievement',
    'AchievementSubsystem',
]

# We want stuff here to show up as packagename.Foo instead of
# packagename._submodule.Foo.
set_canonical_module_names(globals())

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
