# Released under the MIT License. See LICENSE for details.
#
"""Components for the classic BombSquad experience.

This package/feature-set contains functionality related to the classic
BombSquad experience. Note that much legacy BombSquad code is still a
bit tangled and thus this feature-set is largely inseperable from
scenev1 and uiv1. Future feature-sets will be designed in a more modular
way.
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
from baclassic._chest import (
    ChestAppearanceDisplayInfo,
    CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,
    CHEST_APPEARANCE_DISPLAY_INFOS,
)
from baclassic._displayitem import show_display_item

__all__ = [
    'ChestAppearanceDisplayInfo',
    'CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT',
    'CHEST_APPEARANCE_DISPLAY_INFOS',
    'ClassicAppMode',
    'ClassicAppSubsystem',
    'Achievement',
    'AchievementSubsystem',
    'show_display_item',
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
