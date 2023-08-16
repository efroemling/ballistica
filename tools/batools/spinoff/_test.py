# Released under the MIT License. See LICENSE for details.
#
"""Tests for spinoff."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def spinoff_test(args: list[str]) -> None:
    """High level test run command; accepts args and raises CleanErrors."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    import os
    import subprocess

    from batools.featureset import FeatureSet
    from efrotools import extract_flag, getprojectconfig
    from efro.terminal import Clr
    from efro.error import CleanError

    submodule_parent = extract_flag(args, '--submodule-parent')
    shared_test_parent = extract_flag(args, '--shared-test-parent')
    if submodule_parent and shared_test_parent:
        raise CleanError(
            "spinoff-test: can't pass both submodule parent"
            ' and shared test parent.'
        )
    public = getprojectconfig(Path('.'))['public']
    if shared_test_parent and public:
        raise CleanError('--shared-test-parent not available in public repo.')

    # A spinoff symlink means we're a spun-off project.
    if os.path.islink('tools/spinoff'):
        raise CleanError(
            'This must be run in a src project; this appears to be a dst.'
        )

    if len(args) != 1:
        raise CleanError('Expected 1 arg.')

    featuresets = {fs.name: fs for fs in FeatureSet.get_all_for_project('.')}

    testtype = args[0]
    if testtype in featuresets:
        path = f'build/spinofftest/{testtype}'
        print(
            f'{Clr.BLD}Running spinoff test{Clr.RST}'
            f" {Clr.SBLU}{Clr.BLD}'{testtype}'{Clr.RST}"
            f' {Clr.BLD}in{Clr.RST}'
            f" {Clr.BLU}'{path}'{Clr.RST}"
            f'{Clr.BLD}...{Clr.RST}',
            flush=True,
        )

        # Normally we spin the project off from where we currently
        # are, but for cloud builds we may want to use a dedicated
        # shared source instead. (since we need a git managed source
        # we need to pull *something* fresh from git instead of just
        # using the files that were synced up by cloudshell).
        # Here we make sure that shared source is up to date.
        spinoff_src = '.'
        spinoff_path = path
        if shared_test_parent:
            spinoff_src = 'build/spinoff_shared_test_parent'
            # Need an abs target path since we change cwd in this case.
            spinoff_path = os.path.abspath(path)
            if bool(False):
                print('TEMP BLOWING AWAY')
                subprocess.run(['rm', '-rf', spinoff_src], check=True)
            if os.path.exists(spinoff_src):
                print(
                    'Pulling latest spinoff_shared_test_parent...',
                    flush=True,
                )
                subprocess.run(
                    ['git', 'pull', '--ff-only'],
                    check=True,
                    cwd=spinoff_src,
                )
            else:
                os.makedirs(spinoff_src, exist_ok=True)
                cmd = [
                    'git',
                    'clone',
                    'git@github.com:efroemling/ballistica-internal.git',
                    spinoff_src,
                ]

                print(
                    f'{Clr.BLU}Creating spinoff shared test parent'
                    f" at '{spinoff_src}' with command {cmd}...{Clr.RST}"
                )
                subprocess.run(
                    cmd,
                    check=True,
                )

        # If the spinoff project already exists and is submodule-based,
        # bring the submodule up to date.
        if os.path.exists(path):
            if bool(False):
                subprocess.run(['rm', '-rf', path], check=True)
            submpath = os.path.join(path, 'submodules/ballistica')
            if os.path.exists(submpath):
                print(
                    f'{Clr.BLU}Pulling latest parent submodule'
                    f' for existing test setup...{Clr.RST}',
                    flush=True,
                )
                subprocess.run(
                    f'cd "{submpath}" && git checkout master && git pull',
                    shell=True,
                    check=True,
                )
        else:
            # No spinoff project there yet; create it.
            cmd = [
                './tools/spinoff',
                'create',
                'SpinoffTest',
                spinoff_path,
                '--featuresets',
                testtype,
            ] + (['--submodule-parent'] if submodule_parent else [])

            # Show the spinoff command we'd use here.
            print(Clr.MAG + ' '.join(cmd) + Clr.RST, flush=True)

            # Avoid the 'what to do next' help.
            subprocess.run(
                cmd + ['--noninteractive'],
                cwd=spinoff_src,
                check=True,
            )

        print(f'{Clr.MAG}tools/spinoff update{Clr.RST}', flush=True)
        subprocess.run(['tools/spinoff', 'update'], cwd=path, check=True)

        # Now let's simply run the mypy target. This will compile a
        # binary, use that binary to generate dummy Python modules, and
        # then check the assembled set of Python scripts. If all that
        # goes through it tells us that this spinoff project is at least
        # basically functional.
        subprocess.run(
            ['make', 'mypy'],
            cwd=path,
            env=dict(
                os.environ,
                BA_APP_RUN_ENABLE_BUILDS='1',
                BA_APP_RUN_BUILD_HEADLESS='1',
            ),
            check=True,
        )

        # Run the binary with a --help arg and make sure it spits
        # out what we expect it to.
        # DISABLING: the dummy-module generation part of the mypy target
        # covers this.
        if bool(False):
            help_output = subprocess.run(
                [
                    'build/cmake/server-debug/staged/dist/'
                    'spinofftest_headless',
                    '--help',
                ],
                cwd=path,
                check=True,
                capture_output=True,
            ).stdout.decode()
            if '-h, --help ' not in help_output:
                raise RuntimeError(
                    'Unexpected output when running test command.'
                )
    else:
        raise CleanError(f"Invalid test type '{testtype}'.")
