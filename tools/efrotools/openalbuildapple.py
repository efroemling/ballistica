# Released under the MIT License. See LICENSE for details.
#
"""Functionality to build the openal library."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

from efro.error import CleanError

if TYPE_CHECKING:
    pass

BUILD_DIR_MAC = 'build/openal_build_mac'


def build_openal_mac() -> None:
    """Do the thing."""

    # Grab OpenALSoft
    builddir = BUILD_DIR_MAC

    subprocess.run(['rm', '-rf', builddir], check=True)
    subprocess.run(['mkdir', '-p', os.path.dirname(builddir)], check=True)
    subprocess.run(
        ['git', 'clone', 'https://github.com/kcat/openal-soft.git', builddir],
        check=True,
    )
    subprocess.run(
        [
            'git',
            'checkout',
            # '1.23.1',
            # '1381a951bea78c67281a2e844e6db1dedbd5ed7c',
            # 'bc83c874ff15b29fdab9b6c0bf40b268345b3026',
            # '59c466077fd6f16af64afcc6260bb61aa4e632dc',
            # '1.24.2',
            # 'dc7d7054a5b4f3bec1dc23a42fd616a0847af948',
            '1.24.3',
        ],
        check=True,
        cwd=builddir,
    )

    subprocess.run(
        [
            'cmake',
            '..',
            '-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64',
            '-DALSOFT_EXAMPLES=OFF',
            '-DALSOFT_UTILS=OFF',
            # (optional) pin min macOS:
            '-DCMAKE_OSX_DEPLOYMENT_TARGET=12.0',
            # (optional) app-friendly install_name:
            # '-DCMAKE_INSTALL_NAME_DIR=@rpath',
        ],
        cwd=f'{builddir}/build',
        check=True,
    )
    subprocess.run(['make'], cwd=f'{builddir}/build', check=True)

    print('SUCCESS!')


def gather_openal_mac() -> None:
    """Gather the things. Assumes all have been built."""

    # Sanity-check; make sure everything appears to be built.
    srcpath = os.path.join(BUILD_DIR_MAC, 'build', 'libopenal.1.dylib')
    if not os.path.exists(srcpath):
        raise CleanError(f'Built OpenAL not found: {srcpath}')

    outdir = 'src/external/openal-apple/macos'
    subprocess.run(['rm', '-rf', outdir], check=True)

    subprocess.run(['mkdir', '-p', outdir], check=True)

    # NOTE - should probably use these includes instead of Apple's.
    # subprocess.run(
    #     ['cp', '-r', f'{builddir}/include/AL', f'{outdir}/include'],
    #     check=True,
    # )

    subprocess.run(['cp', '-L', srcpath, outdir], check=True)

    print('OpenAL gather successful!')
