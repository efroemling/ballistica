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


def openal_build_android() -> None:
    """Build openalsoft for android."""
    from efro.error import CleanError
    from efrotools.openalbuild import build

    args = sys.argv[2:]
    if len(args) != 2:
        raise CleanError(
            'Expected one <ARCH> arg: arm, arm64, x86, x86_64'
            ' and one <MODE> arg: debug, release'
        )

    build(args[0], args[1])


def openal_gather() -> None:
    """Gather built opealsoft libs into src."""
    from efro.error import CleanError
    from efrotools.openalbuild import gather

    args = sys.argv[2:]
    if args:
        raise CleanError('No args expected.')

    gather()
