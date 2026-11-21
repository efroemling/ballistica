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
import re
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    from pathlib import Path


def run_common_code_checks(projroot: Path) -> None:
    """Run the standard cross-project code checks.

    Operates on the Python file set that lint/format targets use, minus
    codegen output (see :func:`efrotools.code.get_script_filenames`).
    Projects with their own per-file scanning (such as ballistica's
    ProjectUpdater) can instead call the individual checks themselves
    to avoid reading files twice.
    """
    from efrotools.code import get_script_filenames

    check_makefile_trunk_order(projroot)

    # No generated files: these checks run as part of update, which
    # comes before codegen in the build order, so codegen output may
    # not exist yet or may be mid-regeneration under a parallel make.
    for fname in get_script_filenames(projroot, include_generated=False):
        with open(os.path.join(projroot, fname), encoding='utf-8') as infile:
            lines = infile.read().splitlines()
        check_no_future_imports(fname, lines)


def _makefile_prerequisites(makefile: str) -> dict[str, list[str]]:
    """Return the prerequisites of each simple target in a Makefile."""
    out: dict[str, list[str]] = {}
    # Join continued lines so a wrapped prerequisite list reads as one.
    for line in makefile.replace('\\\n', ' ').splitlines():
        match = re.match(r'^([A-Za-z0-9_.-]+):(?!=)(.*)$', line)
        if match is not None:
            # A later rule for the same target adds to its prereqs.
            out.setdefault(match.group(1), []).extend(match.group(2).split())
    return out


def check_makefile_trunk_order(projroot: Path) -> None:
    """Make sure the Makefile keeps the core build order.

    Every efro project builds in the order ``env-pre-update`` ->
    ``update`` -> ``env`` -> ``codegen`` -> everything else. A target
    in that chain depending on a later one inverts the order; it tends
    to work until two of them run under one parallel make, and then
    fails as a race. So:

    - ``update`` and ``update-check`` depend on ``env-pre-update`` and
      nothing else. Work that needs codegen output or the full env
      goes in its own target that runs after them.
    - ``env-pre-update`` depends on none of the later steps.
    - ``env`` depends on neither ``update`` nor ``codegen``.
    - ``codegen``, where present, depends on ``env`` and on neither
      update target.
    """
    path = os.path.join(projroot, 'Makefile')
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as infile:
        prereqs = _makefile_prerequisites(infile.read())

    problems: list[str] = []

    for target in ('update', 'update-check'):
        if prereqs.get(target) != ['env-pre-update']:
            found = ' '.join(prereqs.get(target, [])) or 'nothing'
            problems.append(
                f"'{target}' must depend on exactly 'env-pre-update'"
                f' (found: {found}).'
                f' Anything needing codegen output or the full env'
                f' belongs in its own target that runs afterward.'
            )

    forbidden: dict[str, set[str]] = {
        'env-pre-update': {'env', 'update', 'update-check', 'codegen'},
        'env': {'update', 'update-check', 'codegen'},
        'codegen': {'update', 'update-check'},
    }
    for target, later in forbidden.items():
        bad = sorted(later.intersection(prereqs.get(target, [])))
        if bad:
            problems.append(
                f"'{target}' must not depend on {', '.join(bad)}"
                f' (those come later in the build order).'
            )

    if 'codegen' in prereqs and 'env' not in prereqs['codegen']:
        problems.append("'codegen' must depend on 'env'.")

    if problems:
        raise CleanError(
            'Makefile breaks the core build order (env-pre-update ->'
            ' update -> env -> codegen):\n  ' + '\n  '.join(problems)
        )


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
