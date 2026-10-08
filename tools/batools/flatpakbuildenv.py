# Released under the MIT License. See LICENSE for details.
#
"""Generation of the offline Python build environment used by Flatpak.

Flatpak builds (and Flathub builds in particular) run with no network
access, and a virtual environment cannot be moved between machines: its
``bin/pythonX.Y`` symlink, its ``pyvenv.cfg`` ``home`` key and all of
its script shebangs name the absolute path of the interpreter that
created it. So the project venv has to be created *inside* the build
sandbox, from files flatpak-builder has already fetched as declared
sources.

``make flatpak-build-env`` first compiles
``pconfig/requirements_build_lock.txt``: the roots in
``pconfig/requirements_build.txt`` (what *building* the app needs, as
opposed to the full dev environment) constrained to the versions in
``pconfig/requirements_lock.txt``. This module then turns that lockfile
into ``pconfig/flatpak/python-build-env.yml``, a flatpak-builder module
supplying uv plus one wheel per package, staged where the main module's
``make env`` can install from them with uv in offline mode.

Both outputs are committed.
"""

import os
import re
import json
import urllib.request
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr
from efrotools.util import readfile, writefile

if TYPE_CHECKING:
    from typing import Any

# uv is not in the runtime or the SDK and `make env` requires it, so we
# supply it as a pinned source rather than piping an install script from
# the network (which no Flathub build could do anyway). Bump both the
# version and the checksums together; the checksums are published as
# <asset>.sha256 next to each release asset.
UV_VERSION = '0.12.23'
#
# Keyed by flatpak arch name, which is also the substring identifying a
# manylinux wheel built for it; these keys are the build arches.
UV_SHA256 = {
    'x86_64': (
        '9167d72b3319674b6303c4cbe071854bba13ebdf3d76b1a7cbdc175471fb66d6'
    ),
    'aarch64': (
        '6524bd338177ed50d035d39354e12545e993bbeba2ecbddf0480c5b3a81d313f'
    ),
}

# Where the generated module stages its payload, relative to
# FLATPAK_DEST (/app). The manifests name the absolute form in
# UV_FIND_LINKS. Both uv and the wheels are cleaned out of the finished
# app; they exist only for the duration of the build.
STAGE_SUBDIR = 'share/python-build-env'

# A lockfile entry is 'name==version[ ; marker]' followed by its
# hashes. The marker is easy to forget about (only a handful of
# packages carry one), so parse_lockfile cross-checks its tally
# against the raw pin count.
_LOCK_ENTRY = re.compile(
    r'^(?P<name>[A-Za-z0-9._-]+)==(?P<version>[^\s;\\]+)'
    r'(?:[ \t]*;[^\\\n]*)?'
    r'(?P<hashes>(?:[ \t]*\\\n[ \t]*--hash=sha256:[0-9a-f]+)+)',
    re.MULTILINE,
)
_LOCK_PIN = re.compile(r'^[A-Za-z0-9._-]+==', re.MULTILINE)


@dataclass
class LockedPackage:
    """A single pinned package as recorded in a uv lockfile."""

    name: str
    version: str
    hashes: list[str]


def parse_lockfile(path: str) -> list[LockedPackage]:
    """Parse a ``uv pip compile --generate-hashes`` lockfile."""
    text = readfile(path)
    out = [
        LockedPackage(
            name=match.group('name'),
            version=match.group('version'),
            hashes=re.findall(r'sha256:([0-9a-f]+)', match.group('hashes')),
        )
        for match in _LOCK_ENTRY.finditer(text)
    ]
    expected = len(_LOCK_PIN.findall(text))
    if len(out) != expected:
        raise CleanError(
            f"Parsed {len(out)} of {expected} pinned packages in '{path}';"
            f' the lockfile format has changed.'
        )
    if not out:
        raise CleanError(f"No pinned packages found in '{path}'.")
    return out


def _pypi_release_files(pkg: LockedPackage) -> list[dict[str, Any]]:
    """Return the PyPI files for a package whose hash we have pinned."""
    url = f'https://pypi.org/pypi/{pkg.name}/{pkg.version}/json'
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = json.loads(response.read().decode())
    except Exception as exc:
        raise CleanError(
            f'Unable to fetch PyPI metadata for'
            f' {pkg.name}=={pkg.version}: {exc}'
        ) from exc

    pinned = set(pkg.hashes)
    files = [f for f in data['urls'] if f['digests']['sha256'] in pinned]
    if not files:
        raise CleanError(
            f'No PyPI file for {pkg.name}=={pkg.version} matches a hash'
            f' pinned in the lockfile.'
        )
    return files


# Legacy manylinux aliases, as the glibc version they stand for.
_MANYLINUX_ALIASES = {
    'manylinux1': (2, 5),
    'manylinux2010': (2, 12),
    'manylinux2014': (2, 17),
}
_MANYLINUX_VERSIONED = re.compile(r'manylinux_(\d+)_(\d+)_')


def _glibc_requirement(filename: str) -> tuple[int, int]:
    """Lowest glibc a wheel's platform tags will run against."""
    found = [
        (int(major), int(minor))
        for major, minor in _MANYLINUX_VERSIONED.findall(filename)
    ]
    found += [v for alias, v in _MANYLINUX_ALIASES.items() if alias in filename]
    return min(found) if found else (99, 99)


def _wheel_rank(pypi_file: dict[str, Any]) -> tuple[int, tuple[int, int], int]:
    """Sort key picking the most broadly compatible wheel first.

    abi3 wheels keep working across Python versions, so prefer them over
    a version-specific build; after that take the one that demands the
    oldest glibc, since the runtime we land on is not ours to choose.
    """
    name = pypi_file['filename']
    return (
        0 if 'abi3' in name else 1,
        _glibc_requirement(name),
        pypi_file['size'],
    )


def _cpython_tag_version(tag: str) -> int | None:
    """Return 314 for 'cp314', None for anything that isn't a cpython tag."""
    match = re.fullmatch(r'cp(\d)(\d+)', tag)
    return int(match.group(1) + match.group(2)) if match else None


def _is_usable_wheel(filename: str) -> bool:
    """Reject wheels this build could never install.

    uv would skip them at install time, but we only vendor one wheel per
    arch, so picking an unusable one leaves the build with nothing to
    install. Filtered out: musllinux wheels (the freedesktop runtimes
    are glibc), and anything whose interpreter/ABI tags don't accept the
    project's Python -- a free-threaded 'cp3NNt' ABI, or a build pinned
    to a different CPython minor.
    """
    from efrotools.pyver import PYVER

    if 'musllinux' in filename:
        return False

    target = int(PYVER.replace('.', ''))
    parts = filename.removesuffix('.whl').split('-')
    if len(parts) < 5:
        return False
    python_tags, abi_tag = parts[-3].split('.'), parts[-2]

    if abi_tag == 'abi3':
        # Stable-ABI wheels work on their own version and every later
        # one.
        return any(
            (ver := _cpython_tag_version(t)) is not None and ver <= target
            for t in python_tags
        )
    if abi_tag == 'none':
        return any(
            t in ('py3', f'py{PYVER[0]}', f'cp{target}') for t in python_tags
        )
    # A version-specific ABI (including free-threaded 'cp3NNt') has to
    # match exactly.
    return abi_tag == f'cp{target}'


def select_distributions(
    pkg: LockedPackage,
) -> list[tuple[str | None, dict[str, Any]]]:
    """Pick the smallest set of files that covers every build arch.

    Returns (flatpak arch or None for 'any arch', pypi file) pairs. A
    pure-Python wheel covers everything; otherwise we take one manylinux
    wheel per arch so each builder only downloads what it can use.
    """
    files = _pypi_release_files(pkg)
    wheels = [
        f
        for f in files
        if f['filename'].endswith('.whl') and _is_usable_wheel(f['filename'])
    ]

    universal = [f for f in wheels if f['filename'].endswith('-none-any.whl')]
    if universal:
        return [(None, min(universal, key=_wheel_rank))]

    per_arch: dict[str, dict[str, Any]] = {}
    for arch in UV_SHA256:
        matches = [
            f
            for f in wheels
            if 'manylinux' in f['filename'] and arch in f['filename']
        ]
        if matches:
            per_arch[arch] = min(matches, key=_wheel_rank)
    if per_arch:
        if len(per_arch) != len(UV_SHA256):
            got = ', '.join(per_arch)
            raise CleanError(
                f'{pkg.name}=={pkg.version} has manylinux wheels for'
                f' {got} but not for every build arch.'
            )
        return list(per_arch.items())

    # An sdist is no use: the offline build vendors no build backend.
    raise CleanError(f'No usable wheel for {pkg.name}=={pkg.version}.')


def write_flatpak_module(
    path: str, packages: list[LockedPackage], lock_name: str
) -> None:
    """Write the flatpak-builder module supplying uv and the wheels."""
    lines = [
        '# Generated by `make flatpak-build-env`; do not edit by hand.',
        '#',
        '# Supplies everything the main module needs to create the',
        '# project venv with no network access: uv, plus a wheel for',
        f'# every package in {lock_name}. Both are staged under',
        f'# $FLATPAK_DEST/{STAGE_SUBDIR} and cleaned out of the app.',
        'name: python-build-env',
        'buildsystem: simple',
        'build-commands:',
        '  - install -Dm755 uv ${FLATPAK_DEST}/bin/uv',
        f'  - mkdir -p ${{FLATPAK_DEST}}/{STAGE_SUBDIR}/wheels',
        f'  - cp -a wheels/. ${{FLATPAK_DEST}}/{STAGE_SUBDIR}/wheels/',
        'cleanup:',
        '  - /bin/uv',
        f'  - /{STAGE_SUBDIR}',
        'sources:',
    ]

    for arch, sha256 in UV_SHA256.items():
        lines += [
            '  - type: archive',
            f'    only-arches: [{arch}]',
            '    url: https://github.com/astral-sh/uv/releases/download/'
            f'{UV_VERSION}/uv-{arch}-unknown-linux-gnu.tar.gz',
            f'    sha256: {sha256}',
        ]

    # One PyPI metadata request per package; they are independent, so
    # run them concurrently. map() keeps lockfile order for the output.
    with ThreadPoolExecutor(max_workers=8) as executor:
        selections = list(executor.map(select_distributions, packages))

    for pkg, selection in zip(packages, selections):
        print(f'  {Clr.BLU}{pkg.name}=={pkg.version}{Clr.RST}', flush=True)
        for wheel_arch, pypi_file in selection:
            lines.append('  - type: file')
            if wheel_arch is not None:
                lines.append(f'    only-arches: [{wheel_arch}]')
            url = pypi_file['url']
            sha256 = pypi_file['digests']['sha256']
            lines += [
                '    dest: wheels',
                f'    url: {url}',
                f'    sha256: {sha256}',
            ]

    writefile(path, '\n'.join(lines) + '\n')


def generate(projroot: str) -> None:
    """Regenerate the flatpak module from the build lockfile."""
    lock_path = os.path.join('pconfig', 'requirements_build_lock.txt')
    module_path = os.path.join('pconfig', 'flatpak', 'python-build-env.yml')

    packages = parse_lockfile(os.path.join(projroot, lock_path))
    print(
        f'{Clr.BLD}Selecting wheels for {len(packages)}'
        f' build packages...{Clr.RST}',
        flush=True,
    )
    write_flatpak_module(
        os.path.join(projroot, module_path), packages, lock_path
    )
    print(f'{Clr.GRN}Wrote {module_path}.{Clr.RST}', flush=True)
