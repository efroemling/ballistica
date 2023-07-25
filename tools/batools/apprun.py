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
    from typing import Mapping


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


def acquire_binary_for_python_command(purpose: str) -> str:
    """Run acquire_binary as used for python_command call."""
    return acquire_binary(assets=True, purpose=purpose)


def python_command(
    cmd: str,
    purpose: str,
    include_project_tools: bool = False,
    env: Mapping[str, str] | None = None,
) -> None:
    """Run a cmd with a built bin and PYTHONPATH set to its scripts."""

    binpath = acquire_binary_for_python_command(purpose=purpose)
    bindir = os.path.dirname(binpath)

    # We'll set both the app python dir and its site-python-dir. This
    # should let us get at most engine stuff. We could also just use
    # baenv to set up app paths, but that might be overkill and could
    # unintentionally bring in stuff like local mods.
    pydir = f'{bindir}/ba_data/python'
    assert os.path.isdir(pydir)
    pysitedir = f'{bindir}/ba_data/python-site-packages'
    assert os.path.isdir(pysitedir)

    # Make our tools dir available if asked.
    tools_path_extra = ':tools' if include_project_tools else ''

    env_final = {} if env is None else dict(env)
    env_final['PYTHONPATH'] = f'{pydir}:{pysitedir}{tools_path_extra}'

    cmdargs = [binpath, '--command', cmd]
    print(f"apprun: Running with Python command: '{cmdargs}'...", flush=True)
    subprocess.run(cmdargs, env=env_final, check=True)


def acquire_binary(assets: bool, purpose: str) -> str:
    """Return path to a runnable binary, building/downloading as needed.

    If 'assets' is False, only the binary itself will be fetched or
    assembled; no scripts or assets. This generally saves some time, but
    must only be used for very simple '-c' command cases where no assets
    will be needed.

    Be aware that it is up to the particular environment whether a gui
    or headless binary will be provided. Commands should be designed to
    work with either.

    By default, downloaded prefab builds will be used here. This allows
    people without full compiler setups to still perform app runs for
    things like dummy-module generation. However, someone who *is* able
    to compile their own binaries might prefer to use their own binaries
    here so that changes to their local repo are properly reflected in
    app runs and whatnot. Set environment variable
    BA_APP_RUN_ENABLE_BUILDS=1 to enable that.

    When local builds are enabled, we use the same gui build targets as
    the 'make cmake-build' command. This works well if you are iterating
    using that build target anyway, minimizing redundant rebuilds. You
    may, however, prefer to instead assemble headless builds for various
    reasons including faster build times and fewer dependencies
    (equivalent to 'make cmake-server-build'). To do so, set environment
    variable BA_APP_RUN_BUILD_HEADLESS=1.
    """
    import textwrap

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
            binary_path = (
                'build/cmake/server-debug/staged/dist/ballisticakit_headless'
            )
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
            binary_path = 'build/cmake/debug/staged/ballisticakit'
    else:
        # Ok; going with prefab headless stuff.

        # Let the user know how to use their own binaries instead.
        note = '\n' + textwrap.fill(
            'NOTE: You can set env-var BA_APP_RUN_ENABLE_BUILDS=1'
            f' to use locally-built binaries for {purpose}'
            ' instead of prefab ones. This will properly reflect any changes'
            ' you\'ve made to the C/C++ layer.',
            80,
        )
        if assets:
            print(
                f'{Clr.SMAG}Fetching prefab binary & assets for'
                f' {purpose}...{note}{Clr.RST}',
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
                f'{Clr.SMAG}Fetching prefab binary for {purpose}...'
                f'{note}{Clr.RST}',
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
