# Released under the MIT License. See LICENSE for details.
#
"""This module defines the major Python version we are using in the project.

Tools that need to do some work or regenerate files when this changes can
add this submodule file as a dependency.
"""
from __future__ import annotations

from pathlib import Path

PYVER = '3.13'
PYVERNODOT = PYVER.replace('.', '')

_checked_valid_sys_executable = False  # pylint: disable=invalid-name
_valid_sys_executable: str | None = None


def get_project_python_executable(projroot: Path | str) -> str:
    """Return the path to a standalone Python interpreter for this project.

    In some cases, using sys.executable will return an executable such as
    a game binary that contains an embedded Python but is not actually a
    standard interpreter. Tool functionality can use this instead when an
    interpreter is needed.
    """
    if isinstance(projroot, str):
        projroot = Path(projroot)
    path = Path(projroot, f'.venv/bin/python{PYVER}')
    if not path.exists():
        raise RuntimeError(
            f"Expected project Python executable not found at '{path}'."
        )
    return str(path)
