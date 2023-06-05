# Released under the MIT License. See LICENSE for details.
#
"""Testing asset manager functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    pass


def test_babase_imports() -> None:
    """Testing."""
    import subprocess
    import platform

    # Currently skipping this on Windows, as we can't assemble a
    # complete build there currently (can only compile binaries).
    if platform.system() == 'Windows':
        return

    # Put together the headless binary we use for testing.
    subprocess.run(['make', 'cmake-server-build'], check=True)
    builddir = 'build/cmake/server-debug/dist'

    # Make sure we can cleanly import both our Python package and binary
    # module by themselves.
    subprocess.run(
        f'PYTHONPATH={builddir}/ba_data/python'
        f' {builddir}/ballisticakit_headless -c "import babase"',
        check=True,
        shell=True,
    )

    subprocess.run(
        f'PYTHONPATH={builddir}/ba_data/python'
        f' {builddir}/ballisticakit_headless -c "import _babase"',
        check=True,
        shell=True,
    )
