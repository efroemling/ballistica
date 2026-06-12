# Released under the MIT License. See LICENSE for details.
#
"""Common code checks shared by all efro projects.

Each project's ``update_project`` pcommand should call
:func:`run_common_code_checks` so cheap project-wide source sanity
checks stay consistent across repos. These checks never mutate
anything (so they are safe to run in both update and check modes);
they simply raise :class:`efro.error.CleanError` describing the first
problem found.
"""

import os
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    from pathlib import Path


def run_common_code_checks(projroot: Path) -> None:
    """Run the standard cross-project code checks.

    Operates on the same Python file set that lint/format targets use
    (see :func:`efrotools.code.get_script_filenames`). Projects with
    their own per-file scanning (such as ballistica's ProjectUpdater)
    can instead call the individual per-file checks from within their
    existing file loops to avoid reading files twice.
    """
    from efrotools.code import get_script_filenames

    for fname in get_script_filenames(projroot):
        try:
            with open(
                os.path.join(projroot, fname), encoding='utf-8'
            ) as infile:
                lines = infile.read().splitlines()
        except FileNotFoundError:
            # Generated files can blink out from under us when codegen
            # rebuilds run concurrently with update checks (CI commonly
            # runs both under one parallel make); a file that vanished
            # mid-scan simply isn't checked this round.
            continue
        check_no_future_imports(fname, lines)


def check_no_future_imports(fname: str, lines: list[str]) -> None:
    """Make sure ``__future__`` imports don't sneak back into a project.

    We target Python 3.14+, where PEP 649 deferred annotation
    evaluation is the default, so ``from __future__ import
    annotations`` (the last meaningful future-feature) should no
    longer appear anywhere; it would silently switch a module back to
    PEP 563 stringized annotations. Note that we simply error here and
    never auto-remove the line; whether surrounding code relies on the
    old behavior requires human judgement.

    A real ``__future__`` import must be a top-level statement, so
    only column-zero occurrences are flagged; mentions inside
    (indented) docstrings or comments don't trip this.
    """
    for i, line in enumerate(lines):
        if line.startswith('from __future__ import'):
            raise CleanError(
                f'{fname}:{i+1}: __future__ import found. The project'
                f' requires Python 3.14+ (PEP 649 deferred annotations),'
                f' so __future__ imports should no longer be used;'
                f' please remove this line.'
            )
