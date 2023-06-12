# Released under the MIT License. See LICENSE for details.
#
"""Utils for wrangling runs of the app.

Manages constructing or downloading it as well as running it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import platform
import subprocess
import os

from efro.terminal import Clr

if TYPE_CHECKING:
    pass


def test_runs_disabled() -> bool:
    """Are test runs disabled on the current platform?"""

    # Currently skipping this on Windows, as we aren't able to assemble
    # complete build there without WSL.
    if platform.system() == 'Windows':
        return True

    return False


def test_runs_disabled_reason() -> str:
    """Why are test runs disabled here?"""
    # Can get more specific later.
    return 'App test runs disabled here.'


def python_command(cmd: str, purpose: str) -> None:
    """Run a cmd with a built bin and PYTHONPATH set to its scripts dir."""

    binpath = acquire_binary(assets=True, purpose=purpose)
    bindir = os.path.dirname(binpath)

    cmdargs = [binpath, '--command', cmd]
    print(f'Running command: {cmdargs}...')
    subprocess.run(
        cmdargs,
        env=dict(os.environ, PYTHONPATH=f'{bindir}/ba_data/python'),
        check=True,
    )


def acquire_binary(assets: bool, purpose: str) -> str:
    """Return a path to a runnable binary, building or downloading as needed.

    If 'assets' is False, only the binary itself will be fetched or
    assembled; no scripts or assets. This generally saves some time, but
    must only be used for very simple '-c' command cases where no assets
    will be needed.

    By default, binaries used here will be downloaded prefab builds.
    This allows people without full compiler setups to still perform app
    runs for things like dummy-module generation. However, someone who
    *is* able to compile their own binaries might prefer to use their
    own binaries here so that changes to their local repo are properly
    reflected in app runs and whatnot. Set environment variable
    BA_APP_RUN_ENABLE_BUILDS=1 to enable that.

    When local builds are enabled, we use the same gui build targets as
    the 'make cmake' command. This works well if you are iterating using
    that build target anyway, minimizing redundant rebuilds. You may,
    however, prefer to assemble headless builds for various reasons
    including faster build times and fewer dependencies. To do so, set
    environment variable BA_APP_RUN_BUILD_HEADLESS=1.
    """

    binary_build_command: list[str]
    if os.environ.get('BA_APP_RUN_ENABLE_BUILDS') == '1':
        # Going the build-it-ourselves route.

        if os.environ.get('BA_APP_RUN_BUILD_HEADLESS') == '1':
            # User has opted for headless builds.
            if assets:
                print(
                    f'{Clr.SMAG}Building headless binary & assets for'
                    f' {purpose}...{Clr.RST}',
                    flush=True,
                )
                binary_build_command = ['make', 'cmake-server-build']
            else:
                print(
                    f'{Clr.SMAG}Building headless binary for'
                    f' {purpose}...{Clr.RST}',
                    flush=True,
                )
                binary_build_command = ['make', 'cmake-server-binary']
            binary_path = 'build/cmake/server-debug/dist/ballisticakit_headless'
        else:
            # Using default gui builds.
            if assets:
                print(
                    f'{Clr.SMAG}Building gui binary & assets for'
                    f' {purpose}...{Clr.RST}',
                    flush=True,
                )
                binary_build_command = ['make', 'cmake-build']
            else:
                print(
                    f'{Clr.SMAG}Building gui binary for {purpose}...{Clr.RST}',
                    flush=True,
                )
                binary_build_command = ['make', 'cmake-binary']
            binary_path = 'build/cmake/debug/ballisticakit'
    else:
        # Ok; going with prefab headless stuff.
        if assets:
            print(
                f'{Clr.SMAG}Fetching prefab binary & assets for'
                f' {purpose}...{Clr.RST}',
                flush=True,
            )
            binary_path = (
                subprocess.run(
                    ['tools/pcommand', 'prefab_binary_path', 'server-release'],
                    check=True,
                    capture_output=True,
                )
                .stdout.decode()
                .strip()
            )
            binary_build_command = ['make', 'prefab-server-release-build']
        else:
            print(
                f'{Clr.SMAG}Fetching prefab binary for {purpose}...{Clr.RST}',
                flush=True,
            )
            binary_path = (
                subprocess.run(
                    ['tools/pcommand', 'prefab_binary_path', 'server-release'],
                    check=True,
                    capture_output=True,
                )
                .stdout.decode()
                .strip()
            )
            binary_build_command = ['make', binary_path]

    subprocess.run(binary_build_command, check=True)
    if not os.path.exists(binary_path):
        raise RuntimeError(
            f"Binary not found at expected path '{binary_path}'."
        )
    return binary_path
    # subprocess.run(['make', 'scripts-cmake'], cwd='src/assets', check=True)
