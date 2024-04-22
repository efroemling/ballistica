# Released under the MIT License. See LICENSE for details.
#
"""This module defines the major Python version we are using in the project.

Tools that need to do some work or regenerate files when this changes can
add this submodule file as a dependency.
"""
from pathlib import Path

# import subprocess

PYVER = '3.12'
PYVERNODOT = PYVER.replace('.', '')

_checked_valid_sys_executable = False  # pylint: disable=invalid-name
_valid_sys_executable: str | None = None


# def get_valid_sys_executable() -> str:
#     """Attempt to get a valid Python interpreter path.

#     Using sys.executable for this purpose may return the path to the
#     executable containing the embedded Python, which may not be a standard
#     iterpreter.
#     """

#     pyverstr = f'{sys.version_info.major}.{sys.version_info.minor}'

#     global _checked_valid_sys_executable
#     global _valid_sys_executable
#     if not _checked_valid_sys_executable:

#         # First look at sys.executable to see if it seems like a standard
#         # python interpreter.
#         try:
#             output = subprocess.run(
#                 [sys.executable, '--version'], check=True, capture_output=True
#             ).stdout.decode()
#             if output.startswith(f'Python {pyverstr}'):
#                 _valid_sys_executable = sys.executable
#         except Exception:
#             import logging

#             logging.exception(
#                 'Error checking sys.executable in get_valid_sys_executable'
#             )

#         if _valid_sys_executable is None:
#             # For now, as a fallback, just go with 'pythonX.Y'.
#             _valid_sys_executable = f'python{pyverstr}'

#             # As a fallback, look for bin/pythonX.Y under our sys.prefix.
#             # prefixpath = os.path.join(
# sys.prefix, 'bin', f'python{pyverstr}')
#             # if os.path.exists(prefixpath):
#             #     _valid_sys_executable = prefixpath

#         _checked_valid_sys_executable = True

#     if _valid_sys_executable is None:
#         raise RuntimeError('Have no valid sys executable.')

#     return _valid_sys_executable


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
