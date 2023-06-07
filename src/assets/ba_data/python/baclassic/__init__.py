# Released under the MIT License. See LICENSE for details.
#
"""Classic ballistica components.

This stuff is mostly used in the classic app-mode, old UIs, etc.
The app should be able to function cleanly without this package present
(just lacking classic mode functionality).

New code should try to avoid using code here if it wants to be usable
with newer more modern app-modes/etc.

Functionality in this package should be exposed through the ClassicSubsystem
class instance whenever possible. This will allow type-checked code to
go through babase.app.classic which will force it to properly handle the case
where babase.app.classic is None. When code instead imports classic submodules
directly, it will most likely not work without classic present.
"""

# ba_meta require api 8

# import traceback
# traceback.print_stack()
# sys.stderr.flush()
# sys.stdout.flush()


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
