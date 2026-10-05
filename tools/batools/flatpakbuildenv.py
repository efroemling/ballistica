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

This module turns our committed hash-pinned lockfile into the two
things that make that possible:

- ``pconfig/requirements_build_lock.txt`` -- the subset of
  ``pconfig/requirements_lock.txt`` needed to *build* the app. The full
  dev lockfile also carries linters, type checkers, test and docs
  tooling that a packaging build never runs, and vendoring those would
  mean fetching hundreds of megabytes per build.
- ``pconfig/flatpak/python-build-env.yml`` -- a flatpak-builder module
  supplying uv plus one wheel per package in that subset, staged where
  the main module's ``make env`` can install from them with uv in
  offline mode.

Package versions and hashes come straight out of the main lockfile, so
there is only ever one place where a version is pinned. The roots of
the subset live in ``pconfig/requirements_build.txt``; everything they
pull in is derived from the ``# via`` annotations uv writes into the
lockfile.

Both outputs are committed. Regenerate them with ``make
flatpak-build-env`` after changing requirements.
"""

import os
import re
import json
import urllib.request
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import Any

# uv is not in the runtime or the SDK and `make env` requires it, so we
# supply it as a pinned source rather than piping an install script from
# the network (which no Flathub build could do anyway). Bump both the
# version and the checksums together; the checksums are published as
# <asset>.sha256 next to each release asset.
UV_VERSION = '0.12.23'
UV_SHA256 = {
    'x86_64': (
        '9167d72b3319674b6303c4cbe071854bba13ebdf3d76b1a7cbdc175471fb66d6'
    ),
    'aarch64': (
        '6524bd338177ed50d035d39354e12545e993bbeba2ecbddf0480c5b3a81d313f'
    ),
}
UV_TARGET = {
    'x86_64': 'x86_64-unknown-linux-gnu',
    'aarch64': 'aarch64-unknown-linux-gnu',
}

# Flatpak arch names mapped to the substring that identifies a wheel
# built for them. Linux-only; the flatpak build targets nothing else.
WHEEL_ARCHES = {'x86_64': 'x86_64', 'aarch64': 'aarch64'}

# Where the generated module stages its payload, relative to
# FLATPAK_DEST (/app). The manifests name the absolute form in
# UV_FIND_LINKS. Both uv and the wheels are cleaned out of the finished
# app; they exist only for the duration of the build.
STAGE_SUBDIR = 'share/python-build-env'

# A lockfile entry is 'name==version[ ; marker]' followed by its
# hashes and then uv's '# via ...' annotations. The marker is easy to
# forget about -- only a handful of packages carry one -- so
# parse_lockfile cross-checks its tally against the raw pin count.
_LOCK_ENTRY = re.compile(
    r'^(?P<name>[A-Za-z0-9._-]+)==(?P<version>[^\s;\\]+)'
    r'(?P<marker>[ \t]*;[^\\\n]*)?'
    r'(?P<hashes>(?:[ \t]*\\\n[ \t]*--hash=sha256:[0-9a-f]+)+)'
    r'(?P<via>(?:\n[ \t]*#.*)*)',
    re.MULTILINE,
)
_LOCK_PIN = re.compile(r'^[A-Za-z0-9._-]+==', re.MULTILINE)


def normalize(name: str) -> str:
    """Return a PEP 503 normalized project name."""
    return re.sub(r'[-_.]+', '-', name).lower()


@dataclass
class LockedPackage:
    """A single pinned package as recorded in a uv lockfile."""

    name: str
    version: str
    hashes: list[str]
    via: list[str] = field(default_factory=list)
    text: str = ''

    @property
    def key(self) -> str:
        """Normalized name; use this for any lookup."""
        return normalize(self.name)


def parse_lockfile(path: str) -> dict[str, LockedPackage]:
    """Parse a ``uv pip compile --generate-hashes`` lockfile."""
    with open(path, encoding='utf-8') as infile:
        text = infile.read()

    out: dict[str, LockedPackage] = {}
    for match in _LOCK_ENTRY.finditer(text):
        # 'via' blocks look like '# via\n#   foo\n#   bar' or
        # '# via foo'; either way the package names are the only
        # non-'via' words in there.
        via = [
            normalize(word)
            for word in re.findall(
                r'#\s*(?:via\s+)?([A-Za-z0-9._-]+)', match.group('via')
            )
            if word != 'via'
        ]
        pkg = LockedPackage(
            name=match.group('name'),
            version=match.group('version'),
            hashes=re.findall(r'sha256:([0-9a-f]+)', match.group('hashes')),
            via=via,
            text=match.group(0).rstrip(),
        )
        out[pkg.key] = pkg

    expected = len(_LOCK_PIN.findall(text))
    if len(out) != expected:
        raise CleanError(
            f"Parsed {len(out)} of {expected} pinned packages in '{path}';"
            f' the lockfile format has changed.'
        )
    if not out:
        raise CleanError(f"No pinned packages found in '{path}'.")
    return out


def read_roots(path: str) -> list[str]:
    """Read the list of root package names for the build subset."""
    roots: list[str] = []
    with open(path, encoding='utf-8') as infile:
        for line in infile:
            line = line.split('#', 1)[0].strip()
            if line:
                roots.append(line)
    if not roots:
        raise CleanError(f"No package names found in '{path}'.")
    return roots


def resolve_subset(
    packages: dict[str, LockedPackage], roots: list[str]
) -> list[LockedPackage]:
    """Return the roots plus everything they pull in, lockfile order.

    uv annotates each locked package with the packages that required it
    ('# via foo'), which is exactly the edge we need read backwards: a
    package belongs in the subset if anything already in the subset
    depends on it.
    """
    missing = sorted(r for r in roots if normalize(r) not in packages)
    if missing:
        names = ', '.join(missing)
        raise CleanError(
            f'Build requirements not present in the main lockfile: {names}.'
        )

    keep = {normalize(r) for r in roots}
    while True:
        added = {
            key
            for key, pkg in packages.items()
            if key not in keep and any(v in keep for v in pkg.via)
        }
        if not added:
            break
        keep |= added

    return [pkg for key, pkg in packages.items() if key in keep]


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
    wheel per arch so each builder only downloads what it can use. A
    package with no usable wheel falls back to its sdist, which uv
    builds locally.
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

    out: list[tuple[str | None, dict[str, Any]]] = []
    for arch, tag in WHEEL_ARCHES.items():
        matches = [
            f
            for f in wheels
            if 'manylinux' in f['filename'] and tag in f['filename']
        ]
        if matches:
            out.append((arch, min(matches, key=_wheel_rank)))
    if out:
        if len(out) != len(WHEEL_ARCHES):
            got = ', '.join(a for a, _ in out if a is not None)
            raise CleanError(
                f'{pkg.name}=={pkg.version} has manylinux wheels for'
                f' {got} but not for every build arch.'
            )
        return out

    sdists = [f for f in files if not f['filename'].endswith('.whl')]
    if not sdists:
        raise CleanError(
            f'No wheel or sdist usable for {pkg.name}=={pkg.version}.'
        )
    return [(None, sdists[0])]


def write_subset_lockfile(
    path: str, subset: list[LockedPackage], roots_path: str, lock_path: str
) -> None:
    """Write the reduced lockfile in uv's own format."""
    lines = [
        '# Generated by `make flatpak-build-env`; do not edit by hand.',
        '#',
        f'# The subset of {lock_path} needed to build the app, derived',
        f'# from the root package names in {roots_path}. Versions and',
        '# hashes are copied verbatim from the main lockfile, which',
        '# stays the single place any version is pinned.',
        '',
    ]
    lines.extend(pkg.text for pkg in subset)
    with open(path, 'w', encoding='utf-8') as outfile:
        outfile.write('\n'.join(lines) + '\n')


def write_flatpak_module(
    path: str, subset: list[LockedPackage], lock_name: str
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

    for arch, target in UV_TARGET.items():
        lines += [
            '  - type: archive',
            f'    only-arches: [{arch}]',
            '    url: https://github.com/astral-sh/uv/releases/download/'
            f'{UV_VERSION}/uv-{target}.tar.gz',
            f'    sha256: {UV_SHA256[arch]}',
        ]

    for pkg in subset:
        print(f'  {Clr.BLU}{pkg.name}=={pkg.version}{Clr.RST}', flush=True)
        for wheel_arch, pypi_file in select_distributions(pkg):
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

    with open(path, 'w', encoding='utf-8') as outfile:
        outfile.write('\n'.join(lines) + '\n')


def generate(projroot: str) -> None:
    """Regenerate the build subset lockfile and the flatpak module."""
    lock_path = os.path.join('pconfig', 'requirements_lock.txt')
    roots_path = os.path.join('pconfig', 'requirements_build.txt')
    subset_path = os.path.join('pconfig', 'requirements_build_lock.txt')
    module_path = os.path.join('pconfig', 'flatpak', 'python-build-env.yml')

    os.chdir(projroot)

    packages = parse_lockfile(lock_path)
    subset = resolve_subset(packages, read_roots(roots_path))

    print(
        f'{Clr.BLD}Resolving {len(subset)} build packages'
        f' (of {len(packages)} locked)...{Clr.RST}',
        flush=True,
    )

    write_subset_lockfile(subset_path, subset, roots_path, lock_path)
    write_flatpak_module(module_path, subset, subset_path)

    print(
        f'{Clr.GRN}Wrote {subset_path} and {module_path}.{Clr.RST}',
        flush=True,
    )
