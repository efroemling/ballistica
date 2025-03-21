# Released under the MIT License. See LICENSE for details.
#
"""Util to get ballisticakit versions."""

from __future__ import annotations

import os
from enum import Enum
from typing import TYPE_CHECKING, assert_never

from efro.error import CleanError

if TYPE_CHECKING:
    pass


class Mode(Enum):
    """Mode we can run this command in."""

    INFO = 'info'
    BUILD = 'build'
    VERSION = 'version'
    API = 'api'


def _handle_args(args: list[str]) -> Mode:
    """parse os args and return a mode"""
    mode: Mode | None = None
    if len(args) == 0:
        print('OPTIONS: info, build, version', 'api')
        raise CleanError()

    try:
        mode = Mode(args[0])
    except ValueError as exc:
        raise CleanError(f"Invalid mode '{args[0]}'") from exc

    if len(args) != 1:
        raise CleanError('Incorrect args.')
    return mode


def get_current_version(projroot: str = '') -> tuple[str, int]:
    """Pull current version and build_number from the project."""
    version = None
    build_number = None
    with open(
        os.path.join(projroot, 'src/ballistica/shared/ballistica.cc'),
        encoding='utf-8',
    ) as infile:
        lines = infile.readlines()
    for line in lines:
        prefix = 'const char* kEngineVersion = "'
        suffix = '";\n'
        if line.startswith(prefix) and line.endswith(suffix):
            if version is not None:
                raise RuntimeError('Found multiple version lines.')
            version = line.removeprefix(prefix).removesuffix(suffix)
        prefix = 'const int kEngineBuildNumber = '
        suffix = ';\n'
        if line.startswith(prefix) and line.endswith(suffix):
            if build_number is not None:
                raise RuntimeError('Found multiple build number lines.')
            build_number = int(line.removeprefix(prefix).removesuffix(suffix))
    if version is None:
        raise RuntimeError('Version not found.')
    if build_number is None:
        raise RuntimeError('Build number not found.')
    return version, build_number


def get_current_api_version() -> int:
    """Pull current api version from the project."""
    with open(
        'src/ballistica/shared/ballistica.cc', encoding='utf-8'
    ) as infile:
        lines = infile.readlines()
    linestart = 'const int kEngineApiVersion = '
    lineend = ';'
    for line in lines:
        if line.startswith(linestart):
            return int(
                line.strip()
                .removeprefix(linestart)
                .removesuffix(lineend)
                .strip()
            )
    raise RuntimeError('Api version line not found.')


def run(projroot: str, args: list[str]) -> None:
    """Main entry point for this script."""

    mode = _handle_args(args)

    # We want to run from the root dir.
    os.chdir(projroot)

    version, build_number = get_current_version()

    if mode is Mode.INFO:
        print('version = ' + version)
        print('build = ' + str(build_number))
        print('api = ' + str(get_current_api_version()))
    elif mode is Mode.VERSION:
        print(version)
    elif mode is Mode.BUILD:
        print(build_number)
    elif mode is Mode.API:
        print(get_current_api_version())
    else:
        assert_never(mode)
