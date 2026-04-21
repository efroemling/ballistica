# Released under the MIT License. See LICENSE for details.
#
"""Utils for wrangling running the app as part of a build.

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


def python_command(
    cmd: str,
    purpose: str,
    include_project_tools: bool = False,
    env: Mapping[str, str] | None = None,
) -> None:
    """Run a cmd with a built bin and PYTHONPATH set to its scripts."""

    binpath = acquire_binary(purpose=purpose)
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


def acquire_binary(purpose: str, *, gui: bool = False) -> str:
    """Return path to a runnable binary, building/downloading as needed.

    By default this provides a headless-server binary along with the
    full server asset bundle (Python scripts + fonts + data, but no
    audio/textures/meshes). That is enough for the binary to fully boot
    and is the right choice for the vast majority of tool/test
    workflows (dummy-module generation, import tests, transport tests,
    etc.).

    Pass ``gui=True`` when the caller genuinely needs a GUI binary and
    the full (including media) asset bundle — e.g. a test that
    exercises rendering. This only works in environments that have the
    full asset source tree available; environments like ba-check that
    strip audio/textures/meshes will fail the asset build in this mode.

    By default, downloaded prefab builds will be used here. This allows
    people without full compiler setups to still perform app runs for
    things like dummy-module generation. However, someone who *is* able
    to compile their own binaries might prefer to use their own binaries
    here so that changes to their local repo are properly reflected in
    app runs and whatnot. Set environment variable
    BA_APP_RUN_ENABLE_BUILDS=1 to enable that.
    """
    import textwrap

    binary_build_command: list[str]
    if os.environ.get('BA_APP_RUN_ENABLE_BUILDS') == '1':
        # Going the build-it-ourselves route.

        if gui:
            print(
                f'{Clr.SMAG}Building gui binary & assets for'
                f' {purpose}...{Clr.RST}',
                flush=True,
            )
            binary_build_command = ['make', 'cmake-build']
            binary_path = 'build/cmake/debug/staged/ballisticakit'
        else:
            print(
                f'{Clr.SMAG}Building headless binary & assets for'
                f' {purpose}...{Clr.RST}',
                flush=True,
            )
            binary_build_command = ['make', 'cmake-server-build']
            binary_path = (
                'build/cmake/server-debug/staged/dist/ballisticakit_headless'
            )
        env = None
    else:
        # Ok; going with a downloaded prefab build.

        # By default, prefab build targets on WSL (Linux running on
        # Windows) will give us Windows builds which won't work right
        # here. Ask it for Linux builds instead.
        env = dict(os.environ, BA_WSL_TARGETS_WINDOWS='0')

        # Let the user know how to use their own built binaries instead
        # if they prefer.
        note = '\n' + textwrap.fill(
            f'NOTE: You can set env-var BA_APP_RUN_ENABLE_BUILDS=1'
            f' to use locally-built binaries for {purpose} instead'
            f' of prefab ones. This will properly reflect any changes'
            f' you\'ve made to the C/C++ layer.',
            80,
        )

        if gui:
            print(
                f'{Clr.SMAG}Fetching prefab gui binary & assets for'
                f' {purpose}...{note}{Clr.RST}',
                flush=True,
            )
            binary_build_command = ['make', 'prefab-gui-release-build']
            binary_path = (
                subprocess.run(
                    ['tools/pcommand', 'prefab_binary_path', 'gui-release'],
                    env=env,
                    check=True,
                    capture_output=True,
                )
                .stdout.decode()
                .strip()
            )
        else:
            print(
                f'{Clr.SMAG}Fetching prefab headless binary & assets for'
                f' {purpose}...{note}{Clr.RST}',
                flush=True,
            )
            binary_build_command = ['make', 'prefab-server-release-build']
            binary_path = (
                subprocess.run(
                    ['tools/pcommand', 'prefab_binary_path', 'server-release'],
                    env=env,
                    check=True,
                    capture_output=True,
                )
                .stdout.decode()
                .strip()
            )

    subprocess.run(binary_build_command, env=env, check=True)
    if not os.path.exists(binary_path):
        raise RuntimeError(
            f"Binary not found at expected path '{binary_path}'."
        )
    return binary_path
