# Released under the MIT License. See LICENSE for details.
#
"""A system to wrangle projects spun off from a parent Ballistica project.

Think of this as 'subclassing' the project.
Spinoff can arbitrarily filter/override/exclude files from
the source project such that only a minimal number of additions
and changes need to be included in the spinoff project itself.

Spinoff operates by copying or hard-linking source project files in
from a git submodule, while also telling git to ignore those same files.
At any point, the submodule/core system can be jettisoned to leave
a 100% self contained standalone project. To do this, just kill the
submodule and remove the 'spinoff' section in .gitignore.
"""

from batools.spinoff._context import SpinoffContext
from batools.spinoff._main import spinoff_main
from batools.spinoff._test import spinoff_test

__all__ = [
    'SpinoffContext',
    'spinoff_main',
    'spinoff_test',
]
