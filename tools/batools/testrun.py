# Released under the MIT License. See LICENSE for details.
#
"""Utils for test runs of the app."""

from __future__ import annotations

from typing import TYPE_CHECKING
import platform
import subprocess
import os

if TYPE_CHECKING:
    pass


def test_runs_disabled() -> bool:
    """Are test runs disabled on the current platform?"""

    # Currently skipping this on Windows, as we aren't able to assemble
    # complete build there without WSL.
    if platform.system() == 'Windows':
        return True

    return False


def get_binary() -> str:
    """Return a path to a server build binary, building it if need be."""

    subprocess.run(['make', 'cmake-server-build'], check=True)
    builddir = 'build/cmake/server-debug/dist'
    binpath = os.path.join(builddir, 'ballisticakit_headless')
    assert os.path.isfile(binpath)
    return binpath


def run_command(cmd: str) -> None:
    """Run a cmd with a built bin and PYTHONPATH set to its scripts dir."""

    binpath = get_binary()
    bindir = os.path.dirname(binpath)

    cmdargs = [binpath, '--command', cmd]
    print(f'Running command: {cmdargs}...')
    subprocess.run(
        cmdargs,
        env=dict(os.environ, PYTHONPATH=f'{bindir}/ba_data/python'),
        check=True,
    )
