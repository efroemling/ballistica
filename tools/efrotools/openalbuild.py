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

# Arch names we take and their official android versions.
ARCHS = {
    'arm': 'armeabi-v7a',
    'arm64': 'arm64-v8a',
    'x86': 'x86',
    'x86_64': 'x86_64',
}

MODES = {'debug', 'release'}


def _build_dir(arch: str, mode: str) -> str:
    """Build dir given an arch and mode."""
    return f'build/openal_build_android_{arch}_{mode}'


def build(arch: str, mode: str) -> None:
    """Do the thing."""
    from efrotools import replace_exact

    if arch not in ARCHS:
        raise CleanError(f"Invalid arch '{arch}'.")

    if mode not in MODES:
        raise CleanError(f"Invalid mode '{mode}'.")

    # Get ndk path.
    ndk_path = (
        subprocess.run(
            ['tools/pcommand', 'android_sdk_utils', 'get-ndk-path'],
            check=True,
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )

    # Grab from git and build.
    builddir = _build_dir(arch, mode)
    subprocess.run(['rm', '-rf', builddir], check=True)
    subprocess.run(['mkdir', '-p', os.path.dirname(builddir)], check=True)
    subprocess.run(
        ['git', 'clone', 'https://github.com/kcat/openal-soft.git', builddir],
        check=True,
    )

    commit = 'd3875f3'  # Version 1.23.1
    subprocess.run(['git', 'checkout', commit], check=True, cwd=builddir)

    # One bit of filtering: by default, openalsoft sends all sorts of
    # log messages to the android log. This is reasonable since its
    # possible to filter by tag/level. However I'd prefer it to send
    # only the ones that it would send to stderr so I don't always have
    # to worry about filtering.
    loggingpath = f'{builddir}/core/logging.cpp'
    with open(loggingpath, encoding='utf-8') as infile:
        txt = infile.read()

    txt = replace_exact(
        txt,
        '    __android_log_print(android_severity(level),'
        ' "openal", "%s", str);',
        '    // ericf tweak; only send logs to'
        ' android that we\'d send to stderr.\n'
        '    if (gLogLevel >= level) {\n'
        '        __android_log_print(android_severity(level),'
        ' "openal", "%s", str);\n'
        '    }',
    )
    with open(loggingpath, 'w', encoding='utf-8') as outfile:
        outfile.write(txt)

    subprocess.run(
        [
            'cmake',
            '.',
            f'-DANDROID_ABI={ARCHS[arch]}',
            '-DANDROID_NATIVE_API_LEVEL=21',
            f'-DCMAKE_BUILD_TYPE={mode}',
            '-DLIBTYPE=STATIC',
            '-DCMAKE_TOOLCHAIN_FILE='
            f'{ndk_path}/build/cmake/android.toolchain.cmake',
        ],
        cwd=builddir,
        check=True,
    )
    subprocess.run(['make'], cwd=builddir, check=True)

    print('SUCCESS!')


def gather() -> None:
    """Gather the things. Assumes all have been built."""

    # Sanity-check; make sure everything appears to be built.
    for arch in ARCHS:
        for mode in MODES:
            builddir = _build_dir(arch, mode)
            libfile = os.path.join(builddir, 'libopenal.a')
            if not os.path.exists(libfile):
                raise CleanError(f"Built lib not found: '{libfile}'.")

    outdir = 'src/external/openal-android'
    subprocess.run(['rm', '-rf', outdir], check=True)

    subprocess.run(['mkdir', '-p', f'{outdir}/include'], check=True)

    builddir = _build_dir('arm', 'debug')  # Doesn't matter here.
    subprocess.run(
        ['cp', '-r', f'{builddir}/include/AL', f'{outdir}/include'],
        check=True,
    )

    for arch, andrarch in ARCHS.items():
        for mode in MODES:
            builddir = _build_dir(arch, mode)
            installdir = f'{outdir}/lib/{andrarch}_{mode}'
            subprocess.run(['mkdir', '-p', installdir], check=True)
            subprocess.run(
                ['cp', f'{builddir}/libopenal.a', installdir], check=True
            )
    print('OpenAL gather successful!')
