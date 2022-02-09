# Released under the MIT License. See LICENSE for details.
#
"""Util to get ballisticacore versions."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Sequence


def _handle_args(args: list[str]) -> str:
    """parse os args and return a mode"""
    mode = None
    if len(args) == 0:
        print('OPTIONS: info, build, version')
        sys.exit(0)
    elif len(args) == 1:
        if args[0] == 'info':
            mode = 'info'
        if args[0] == 'build':
            mode = 'build'
        if args[0] == 'version':
            mode = 'version'
    if mode is None:
        raise Exception('invalid args')
    return mode


def get_current_version() -> tuple[str, int]:
    """Pull current version and build_number from the project."""
    version = None
    build_number = None
    with open('src/ballistica/ballistica.cc', encoding='utf-8') as infile:
        lines = infile.readlines()
    for line in lines:
        if line.startswith('const char* kAppVersion = "'):
            if version is not None:
                raise Exception('found multiple version lines')
            version = line[27:-3]
        if line.startswith('const int kAppBuildNumber = '):
            if build_number is not None:
                raise Exception('found multiple build number lines')
            build_number = int(line[28:-2])
    if version is None:
        raise Exception('version not found')
    if build_number is None:
        raise Exception('build number not found')
    return version, build_number


def run(projroot: str, args: list[str]) -> None:
    """Main entry point for this script."""

    mode = _handle_args(args)

    # We want to run from the root dir.
    os.chdir(projroot)

    version, build_number = get_current_version()

    if mode == 'info':
        print('version = ' + version)
        print('build = ' + str(build_number))
    elif mode == 'version':
        print(version)
    elif mode == 'build':
        print(build_number)
    else:
        raise Exception('invalid mode: ' + str(mode))
