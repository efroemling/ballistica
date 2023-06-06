# Released under the MIT License. See LICENSE for details.
#
"""Tests for spinoff."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def spinoff_test(args: list[str]) -> None:
    """High level test run command; accepts args and raises CleanErrors."""

    import os
    import subprocess

    from batools.featureset import FeatureSet
    from efrotools import extract_flag
    from efro.terminal import Clr
    from efro.error import CleanError

    submodule_parent = extract_flag(args, '--submodule-parent')

    # A spinoff symlink means we're a spun-off project.
    if os.path.islink('tools/spinoff'):
        raise CleanError(
            'This must be run in a src project; this appears to be a dst.'
        )
    if len(args) != 1:
        raise CleanError('Expected 1 arg.')

    featuresets = {fs.name: fs for fs in FeatureSet.get_all_for_project('.')}

    testtype = args[0]
    if testtype == 'empty' or testtype in featuresets:
        path = f'build/spinofftest/{testtype}'
        print(
            f'{Clr.BLD}Running spinoff test{Clr.RST}'
            f" {Clr.SBLU}{Clr.BLD}'{testtype}'{Clr.RST}"
            f' {Clr.BLD}in{Clr.RST}'
            f" {Clr.BLU}'{path}'{Clr.RST}"
            f'{Clr.BLD}...{Clr.RST}',
            flush=True,
        )

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
            cmd = [
                './tools/spinoff',
                'create',
                'SpinoffTest',
                path,
                '--featuresets',
                'none' if testtype == 'empty' else testtype,
            ] + (['--submodule-parent'] if submodule_parent else [])

            # Show the spinoff command we'd use here.
            print(Clr.MAG + ' '.join(cmd) + Clr.RST, flush=True)

            # Avoid the 'what to do next' help.
            subprocess.run(
                cmd + ['--noninteractive'],
                check=True,
            )

        print(f'{Clr.MAG}tools/spinoff update{Clr.RST}', flush=True)
        subprocess.run(['tools/spinoff', 'update'], cwd=path, check=True)
        # subprocess.run(['make', 'cmake-server-binary'], cwd=path, check=True)

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
                BA_ENABLE_DUMMY_MODULE_BINARY_BUILDS='1',
                BA_DUMMY_MODULE_BINARY_BUILDS_USE_HEADLESS='1',
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
                    'build/cmake/server-debug/dist/spinofftest_headless',
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
