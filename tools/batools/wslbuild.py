# Released under the MIT License. See LICENSE for details.
#
"""Sanity checks for Visual Studio builds driven from WSL.

These run before we hand off to MSBuild. Everything here exists to turn
an environment problem into a clear explanation, since the raw failures
(a case-sensitivity compile error, a 'not found' from the shell) say
nothing about what to fix.
"""

import os
import glob
import textwrap
import subprocess

from efro.error import CleanError


def _wrap(txt: str) -> str:
    return textwrap.fill(txt, 76)


def check_win_drive() -> None:
    """Make sure we're building on a windows drive."""
    from efrotools.util import (
        is_wsl_windows_build_path,
        wsl_windows_build_path_description,
    )

    if (
        subprocess.run(
            ['which', 'wslpath'], check=False, capture_output=True
        ).returncode
        != 0
    ):
        raise CleanError(
            "'wslpath' not found. This does not seem to be a WSL environment."
        )

    if os.environ.get('WSL_BUILD_CHECK_WIN_DRIVE_IGNORE') == '1':
        return

    nativepath = os.getcwd()

    # Get a windows path to the current dir.
    winpath = (
        subprocess.run(
            ['wslpath', '-w', '-a', nativepath],
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .strip()
    )

    # If we're sitting under the linux filesystem, our path will start
    # with '\\wsl$' or '\\wsl.localhost' or '\\wsl\'; fail in that case
    # and explain why.
    if any(
        winpath.startswith(x) for x in ['\\\\wsl$', '\\\\wsl.', '\\\\wsl\\']
    ):
        raise CleanError(
            '\n\n'.join(
                [
                    _wrap(
                        'ERROR: This project appears to live'
                        ' on the Linux filesystem.'
                    ),
                    _wrap(
                        'Visual Studio compiles will error here'
                        ' for reasons related to Linux filesystem'
                        ' case-sensitivity, and thus are disallowed.'
                        ' Clone the repo to a location that maps to a native'
                        ' Windows drive such as \'/mnt/c/ballistica\''
                        ' and try again.'
                    ),
                    _wrap(
                        'Note that WSL2 filesystem performance'
                        ' is poor when accessing native Windows drives,'
                        ' so if Visual Studio builds are not needed it may'
                        ' be best to keep things here on the Linux filesystem.'
                        ' This behavior may differ under WSL1 (untested).'
                    ),
                    _wrap(
                        'Set env-var WSL_BUILD_CHECK_WIN_DRIVE_IGNORE=1 to skip'
                        ' this check.'
                    ),
                ]
            )
        )

    # We also now require this check to be true. We key off this same
    # check in other places to introduce various workarounds to deal
    # with funky permissions issues/etc.
    #
    # Note that we could rely on *only* this check, but it might be nice
    # to leave the above one in as well to better explain the Linux
    # filesystem situation.
    if not is_wsl_windows_build_path(nativepath):
        reqs = wsl_windows_build_path_description()
        raise CleanError(
            _wrap(
                f'ERROR: This project\'s path ({nativepath})'
                f' is not valid for WSL Windows builds.'
                f' Path must be: {reqs}.'
            )
        )


def check_msbuild(msbuild_path: str) -> None:
    """Make sure the msbuild we're about to invoke actually exists.

    Without this, a missing (or differently-placed) Visual Studio just
    gets us an inscrutable ``/bin/sh: MSBuild.exe: not found``, which
    tells the user nothing about what to install.
    """
    if os.path.exists(msbuild_path):
        return

    sections = [
        _wrap(
            'ERROR: Visual Studio MSBuild.exe was not found at the path'
            ' this project builds with:'
        ),
        f'  {msbuild_path}',
    ]

    # Landing here generally means either no Visual Studio at all or a
    # different version/edition of it, so say which of those it is.
    others = sorted(
        path
        for base in ['/mnt/c/Program Files', '/mnt/c/Program Files (x86)']
        for path in glob.glob(
            f'{base}/Microsoft Visual Studio/*/*/MSBuild/*/Bin/MSBuild.exe'
        )
    )
    if others:
        sections.append(
            _wrap(
                'MSBuild.exe WAS found at the following location(s), so it'
                ' looks like a different Visual Studio version or edition is'
                ' installed:'
            )
        )
        sections.append('\n'.join(f'  {path}' for path in others))
    else:
        sections.append(
            _wrap('No Visual Studio installation was found at all.')
        )

    sections.append(
        _wrap(
            'Windows builds require Visual Studio 2026 (major version 18),'
            ' Community edition, with the C++ desktop-development workload.'
            ' See https://github.com/efroemling/ballistica/wiki for build'
            ' setup info.'
        )
    )
    sections.append(
        _wrap(
            'If you have that version under a different edition or path, you'
            ' can point builds at it by passing'
            ' WIN_MSBUILD_EXE_B=\'<path-to-MSBuild.exe>\' to make.'
        )
    )
    raise CleanError('\n\n'.join(sections))
