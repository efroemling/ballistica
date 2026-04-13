# Released under the MIT License. See LICENSE for details.
#
"""Self-contained Android Python build script.

Replaces the GRRedWings/python3-android clone+patch approach with a
clean, in-tree build that owns all build logic directly.
No external repo dependency.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Version constants (easy to bump at the top of the file).

OPENAL_VER = '1.25.1'
BASE_PATH = 'build/static_dependencies'


# Versioned host triple used for configure --host=.
ARCH_TARGETS: dict[str, str] = {
    'arm': 'armv7a-linux-androideabi',
    'arm64': 'aarch64-linux-android',
    'x86': 'i686-linux-android',
    'x86_64': 'x86_64-linux-android',
}

# Non-versioned triple used for tool names (ranlib, ar, etc.).
ARCH_TARGETS_BARE: dict[str, str] = {
    'arm': 'arm-linux-androideabi',
    'arm64': 'aarch64-linux-android',
    'x86': 'i686-linux-android',
    'x86_64': 'x86_64-linux-android',
}


# # Arch names and related configuration (kept for reference but no longer used)
# ARCH_TARGETS, ARCH_TARGETS_BARE, etc. are commented out below


# ---------------------------------------------------------------------------
# Tarball fetch helpers
# ---------------------------------------------------------------------------


def _fetch(url: str, cache_dir: str) -> str:
    """Download url into cache_dir (keyed by filename); return local path."""
    os.makedirs(cache_dir, exist_ok=True)
    fname = url.split('/')[-1]
    local = os.path.join(cache_dir, fname)
    if not os.path.exists(local):
        print(f'  Downloading {url} ...')
        part = local + f'.part.{os.getpid()}'
        urllib.request.urlretrieve(url, part)
        os.rename(part, local)
    else:
        print(f'  Using cached {fname}')
    return local


def _extract(tarball: str, destdir: str) -> str:
    """Extract tarball into destdir; return path to top-level extracted dir."""
    os.makedirs(destdir, exist_ok=True)
    # Peek at the top-level directory name inside the archive.
    with tarfile.open(tarball) as tf:
        top = tf.getmembers()[0].name.split('/')[0]
        tf.extractall(destdir, filter='tar')
    return os.path.join(destdir, top)


def _extract_zip(zipfile_path: str, destdir: str) -> str:
    """Extract zip file into destdir; return path to top-level extracted dir."""
    import zipfile

    os.makedirs(destdir, exist_ok=True)
    with zipfile.ZipFile(zipfile_path, 'r') as zf:
        zf.extractall(destdir)
    # Find the top-level directory
    entries = os.listdir(destdir)
    if len(entries) == 1 and os.path.isdir(os.path.join(destdir, entries[0])):
        return os.path.join(destdir, entries[0])
    return destdir


def _cpus() -> int:
    return os.cpu_count() or 4


# ---------------------------------------------------------------------------
# Dependency builders
# ---------------------------------------------------------------------------


def _build_libopenal(
    cache_dir: str,
    build_dir: str,
    _arch: str,
    debug: bool,
) -> str:
    """Build and install OpenAL."""
    print('Building OpenAL...')
    url = (
        f'https://github.com/kcat/openal-soft/archive/refs/tags/'
        f'{OPENAL_VER}.zip'
    )
    print(f'  Fetching OpenAL from {url} ...')
    zipfile_path = _fetch(url, cache_dir)
    srcdir = _extract_zip(zipfile_path, build_dir)

    # Use cmake to build OpenAL
    builddir = os.path.join(srcdir, 'build')
    os.makedirs(builddir, exist_ok=True)

    subprocess.run(
        [
            'cmake',
            '..',
            f'-DCMAKE_BUILD_TYPE={'Debug' if debug else 'Release'}',
            '-DALSOFT_UTILS=OFF',
            '-DALSOFT_EXAMPLES=OFF',
            '-DALSOFT_TESTS=OFF',
            '-DLIBTYPE=STATIC',
        ],
        cwd=builddir,
        check=True,
    )
    subprocess.run(['make', f'-j{_cpus()}'], cwd=builddir, check=True)

    # Verify static library was created
    static_lib = os.path.join(builddir, 'libopenal.a')
    if not os.path.exists(static_lib):
        raise RuntimeError(f'OpenAL static library not found: {static_lib}')

    lib_size = os.path.getsize(static_lib)
    print(
        'OpenAL build complete!'
        f'Static library: {static_lib} ({lib_size} bytes)'
    )
    print('OpenAL build complete!')
    return srcdir


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def build(rootdir: str, arch: str, debug: bool) -> None:
    """Build OpenAL.

    arch parameter is ignored (kept for compatibility).
    Outputs are written to:

    - ``build/static_dependencies/openal_{arch}[_debug]/`` (OpenAL build)
    """

    suffix = '_debug' if debug else ''
    buildroot = os.path.join(rootdir, BASE_PATH, f'openal_{arch}{suffix}')

    # Shared tarball cache
    cache_dir = os.path.join(rootdir, BASE_PATH, 'openal_cache')

    print(f'=== Building OpenAL {OPENAL_VER} ===')
    print(f'    buildroot: {buildroot}')
    print(f'    debug: {debug}')

    # Start fresh
    subprocess.run(['rm', '-rf', buildroot], check=True)
    os.makedirs(buildroot, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    # Build OpenAL
    src_dir = _build_libopenal(cache_dir, buildroot, arch, debug)
    static_lib_path = os.path.join(src_dir, 'build', 'libopenal.a')
    shutil.copy(static_lib_path, BASE_PATH)
    include_dir = os.path.join(src_dir, 'include', 'AL')
    shutil.copytree(
        include_dir, os.path.join(BASE_PATH, 'include'), dirs_exist_ok=True
    )
    print(f'=== OpenAL {OPENAL_VER} build complete! ===')
    print(f'    Output: {buildroot}')
    print(f'cache: {cache_dir}')


# def gather(rootdir: str, debug: bool = False) -> None:
#     """Gather OpenAL build artifacts into the project.

#     Reads from build/static_dependencies/openal_{arch}[_debug]/ and writes to
#     src/external/openal[-debug]/.

#     Assumes all 4 arch builds (arm, arm64, x86, x86_64) have been run
#     for both debug and release.
#     """
#     suffix = '_debug' if debug else ''
#     archs = ('arm', 'arm64', 'x86', 'x86_64')

#     os.chdir(rootdir)

#     # Output directories
#     src_dst = f'src/external/openal{suffix}'
#     include_dst = os.path.join(src_dst, 'include')
#     lib_dst = os.path.join(src_dst, 'lib')

#     # Clear existing output
#     subprocess.run(['rm', '-rf', src_dst], check=True)
#     os.makedirs(include_dst, exist_ok=True)
#     os.makedirs(lib_dst, exist_ok=True)

#     # Copy headers from the first arch (should be identical for all)
#     arch = archs[0]
#     builddir_base = os.path.join(BASE_PATH, f'openal_{arch}{suffix}')

#     # Find the extracted openal-soft directory and its include path
#     src_include = None
#     if os.path.exists(builddir_base):
#         for entry in os.listdir(builddir_base):
#             entry_path = os.path.join(builddir_base, entry)
#             if os.path.isdir(entry_path) and 'openal' in entry.lower():
#                 potential_include = os.path.join(entry_path, 'include')
#                 if os.path.exists(potential_include):
#                     src_include = potential_include
#                     break

#     if src_include:
#         subprocess.run(['cp', '-r', src_include, include_dst], check=True)
#     else:
#         print(f'Warning: OpenAL headers not found for {arch}')

#     # Copy libraries for each architecture
#     for arch in archs:
#         builddir_base = os.path.join(BASE_PATH, f'openal_{arch}{suffix}')

#         if not os.path.exists(builddir_base):
#             print(f'Warning: Build directory not found for {arch}')
#             continue

#         # Find libopenal.a in the build tree
#         src_lib_path = None
#         for root, dirs, files in os.walk(builddir_base):
#             if 'libopenal.a' in files:
#                 src_lib_path = os.path.join(root, 'libopenal.a')
#                 break

#         if not src_lib_path:
#             print(f'Warning: OpenAL library not found for {arch}')
#             continue

#         lib_name = f'libopenal_{arch}{suffix}.a'
#         dst_lib = os.path.join(lib_dst, lib_name)
#         shutil.copy(src_lib_path, dst_lib)
#         print(f'  Gathered {arch}: {lib_name}')

#     print(f'OpenAL gather{suffix}: done.')
