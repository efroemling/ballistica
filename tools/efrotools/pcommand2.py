# Released under the MIT License. See LICENSE for details.
#
"""Standard snippets that can be pulled into project pcommand scripts.

A snippet is a mini-program that directly takes input from stdin and does
some focused task. This module is a repository of common snippets that can
be imported into projects' pcommand script for easy reuse.
"""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def with_build_lock() -> None:
    """Run a shell command wrapped in a build-lock."""
    from efro.error import CleanError
    from efrotools.buildlock import BuildLock

    import subprocess

    args = sys.argv[2:]
    if len(args) < 2:
        raise CleanError(
            'Expected one lock-name arg and at least one command arg'
        )
    with BuildLock(args[0]):
        subprocess.run(' '.join(args[1:]), check=True, shell=True)


def sortlines() -> None:
    """Sort provided lines. For tidying import lists, etc."""
    from efro.error import CleanError

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg.')
    val = sys.argv[2]
    lines = val.splitlines()
    print('\n'.join(sorted(lines, key=lambda l: l.lower())))
