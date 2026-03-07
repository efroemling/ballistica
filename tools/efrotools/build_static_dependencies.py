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

OPENAL_VER = "1.25.1"
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
    arch: str,
) -> str:
    """Build and install OpenAL."""
    print('Building OpenAL...')
    url = f'https://github.com/kcat/openal-soft/archive/refs/tags/{OPENAL_VER}.zip'
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
            '-DCMAKE_BUILD_TYPE=Release',
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
    print(f'OpenAL build complete! Static library: {static_lib} ({lib_size} bytes)')
    print('OpenAL build complete!')
    return static_lib


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def build(rootdir: str, arch: str, debug: bool) -> None:
    """Build OpenAL.

    arch parameter is ignored (kept for compatibility).
    Outputs are written to:
      build/static_dependencies/openal_{arch}[_debug]/   (OpenAL build)
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
    static_lib_path = _build_libopenal(cache_dir, buildroot, arch)
    shutil.copy(static_lib_path, BASE_PATH)
    print(f'=== OpenAL {OPENAL_VER} build complete! ===')
    print(f'    Output: {buildroot}')
    print(f'cache: {cache_dir}')


# def gather(rootdir: str) -> None:
#     """Gather Android Python build artifacts into the project.
#
#     Reads from build/python_android_{arch}/ and writes to
#     src/external/python-android[-debug]/ and
#     src/assets/pylib-android/.
#
#     Assumes all 4 arch builds (arm, arm64, x86, x86_64) have been run
#     for both debug and release.
#     """
#     # pylint: disable=too-many-locals
#     # pylint: disable=too-many-statements
#     from efrotools.pybuild import PRUNE_LIB_NAMES, tweak_empty_py_files
#
#     # Arch name -> output lib dir name (matching Android ABI conventions).
#     arch_libinst: dict[str, str] = {
#         'arm': 'android_armeabi-v7a',
#         'arm64': 'android_arm64-v8a',
#         'x86': 'android_x86',
#         'x86_64': 'android_x86_64',
#     }
#
#     # Arch name -> sysconfigdata suffix (platform tag in filename).
#     arch_sysconfig_suffix: dict[str, str] = {
#         'arm': 'android_arm-linux-androideabi',
#         'arm64': 'android_aarch64-linux-android',
#         'x86': 'android_i686-linux-android',
#         'x86_64': 'android_x86_64-linux-android',
#     }
#
#     # Arch name -> pyconfig.h name suffix (matches CompileArch enum values
#     # in pybuild.gather()).
#     arch_compile_arch: dict[str, str] = {
#         'arm': 'android_arm',
#         'arm64': 'android_arm64',
#         'x86': 'android_x86',
#         'x86_64': 'android_x86_64',
#     }
#
#     archs = ('arm', 'arm64', 'x86', 'x86_64')
#
#     os.chdir(rootdir)
#
#     # Clear out any existing output.
#     subprocess.run(
#         [
#             'rm',
#             '-rf',
#             'src/external/python-android',
#             'src/external/python-android-debug',
#             'src/assets/pylib-android',
#         ],
#         check=True,
#     )
#
#     apost2 = f'src/Python-{PY_VER_EXACT}/Android/sysroot'
#
#     for buildtype in ['release', 'debug']:
#         debug = buildtype == 'debug'
#         debug_d = 'd' if debug else ''
#         bsuffix = '_debug' if debug else ''
#         bsuffix2 = '-debug' if debug else ''
#         alibname = 'python' + PY_VER + debug_d
#
#         src_dst = f'src/external/python-android{bsuffix2}'
#         include_dst = os.path.join(src_dst, 'include')
#         lib_dst = os.path.join(src_dst, 'lib')
#         pylib_dst = 'src/assets/pylib-android'
#
#         assert not os.path.exists(src_dst)
#         subprocess.run(['mkdir', '-p', src_dst], check=True)
#         subprocess.run(['mkdir', '-p', lib_dst], check=True)
#
#         # Where each arch's build output lives.
#         bases: dict[str, str] = {
#             arch: f'build/python_android_{arch}{bsuffix}/build'
#             for arch in archs
#         }
#         bases2: dict[str, str] = {
#             arch: f'build/python_android_{arch}{bsuffix}/{apost2}'
#             for arch in archs
#         }
#
#         # Base headers and pylib come from the release arm build (same for
#         # all archs; we sanity-check that below).
#         baseheaders = [
#             f'build/python_android_{arch}/src/' f'Python-{PY_VER_EXACT}/Include'
#             for arch in archs
#         ]
#         basepylib = [
#             f'build/python_android_{arch}/src/' f'Python-{PY_VER_EXACT}/Lib'
#             for arch in archs
#         ]
#
#         # Sanity check: all arch Include dirs should be identical.
#         for i in range(len(baseheaders) - 1):
#             returncode = subprocess.run(
#                 ['diff', baseheaders[i], baseheaders[i + 1]],
#                 check=False,
#                 capture_output=True,
#             ).returncode
#             if returncode != 0:
#                 raise RuntimeError(
#                     f'Sanity check failed: Include dirs differ:\n'
#                     f'{baseheaders[i]}\n'
#                     f'{baseheaders[i + 1]}'
#                 )
#
#         # Copy in the base Include dir.
#         subprocess.run(
#             ['cp', '-r', baseheaders[0], include_dst],
#             check=True,
#         )
#
#         # Write the unified pyconfig.h that routes to per-arch headers.
#         unified_pyconfig = (
#             f'#if BA_XCODE_BUILD\n'
#             f'// Necessary to get the TARGET_OS_SIMULATOR define.\n'
#             f'#include <TargetConditionals.h>\n'
#             f'#endif\n'
#             f'\n'
#             f'#if BA_PLATFORM_MACOS and defined(__aarch64__)\n'
#             f'#include "pyconfig_mac_arm64.h"\n'
#             f'\n'
#             f'#elif BA_PLATFORM_MACOS and defined(__x86_64__)\n'
#             f'#include "pyconfig_mac_x86_64.h"\n'
#             f'\n'
#             f'#elif BA_PLATFORM_IOS and defined(__aarch64__)\n'
#             f'#if TARGET_OS_SIMULATOR\n'
#             f'#include "pyconfig_ios_simulator_arm64.h"\n'
#             f'#else\n'
#             f'#include "pyconfig_ios_arm64.h"\n'
#             f'#endif  // TARGET_OS_SIMULATOR\n'
#             f'\n'
#             f'#elif BA_PLATFORM_IOS and defined(__x86_64__)\n'
#             f'#if TARGET_OS_SIMULATOR\n'
#             f'#error x86 simulator no longer supported here.\n'
#             f'#else\n'
#             f'#error this platform combo should not be possible\n'
#             f'#endif  // TARGET_OS_SIMULATOR\n'
#             f'\n'
#             f'#elif BA_PLATFORM_TVOS and defined(__aarch64__)\n'
#             f'#if TARGET_OS_SIMULATOR\n'
#             f'#include "pyconfig_tvos_simulator_arm64.h"\n'
#             f'#else\n'
#             f'#include "pyconfig_tvos_arm64.h"\n'
#             f'#endif  // TARGET_OS_SIMULATOR\n'
#             f'\n'
#             f'#elif BA_PLATFORM_TVOS and defined(__x86_64__)\n'
#             f'#if TARGET_OS_SIMULATOR\n'
#             f'#error x86 simulator no longer supported here.\n'
#             f'#else\n'
#             f'#error this platform combo should not be possible\n'
#             f'#endif  // TARGET_OS_SIMULATOR\n'
#             f'\n'
#             f'#elif BA_PLATFORM_ANDROID and defined(__arm__)\n'
#             f'#include "pyconfig_{arch_compile_arch['arm']}.h"\n'
#             f'\n'
#             f'#elif BA_PLATFORM_ANDROID and defined(__aarch64__)\n'
#             f'#include "pyconfig_{arch_compile_arch['arm64']}.h"\n'
#             f'\n'
#             f'#elif BA_PLATFORM_ANDROID and defined(__i386__)\n'
#             f'#include "pyconfig_{arch_compile_arch['x86']}.h"\n'
#             f'\n'
#             f'#elif BA_PLATFORM_ANDROID and defined(__x86_64__)\n'
#             f'#include "pyconfig_{arch_compile_arch['x86_64']}.h"\n'
#             f'\n'
#             f'#else\n'
#             f'#error unknown platform\n'
#             f'\n'
#             f'#endif\n'
#         )
#         with open(f'{include_dst}/pyconfig.h', 'w', encoding='utf-8') as hfile:
#             hfile.write(unified_pyconfig)
#
#         # Assemble pylib only once (same content for debug and release).
#         if not os.path.exists(pylib_dst):
#             # Sanity check: all arch Lib dirs should be identical.
#             for i in range(len(basepylib) - 1):
#                 returncode = subprocess.run(
#                     ['diff', basepylib[i], basepylib[i + 1]],
#                     check=False,
#                     capture_output=True,
#                 ).returncode
#                 if returncode != 0:
#                     raise RuntimeError(
#                         f'Sanity check failed: Lib dirs differ:\n'
#                         f'{basepylib[i]}\n'
#                         f'{basepylib[i + 1]}'
#                     )
#             subprocess.run(['mkdir', '-p', pylib_dst], check=True)
#             subprocess.run(
#                 [
#                     'rsync',
#                     '--recursive',
#                     '--include',
#                     '*.py',
#                     '--exclude',
#                     '__pycache__',
#                     '--include',
#                     '*/',
#                     '--exclude',
#                     '*',
#                     f'{basepylib[0]}/',
#                     pylib_dst,
#                 ],
#                 check=True,
#             )
#             tweak_empty_py_files(pylib_dst)
#             # Prune modules we don't need (allows shell expansion).
#             subprocess.run(
#                 'cd "' + pylib_dst + '" && rm -rf ' + ' '.join(PRUNE_LIB_NAMES),
#                 shell=True,
#                 check=True,
#             )
#
#         # For each arch, gather its pyconfig.h, sysconfigdata, and libs.
#         for arch in archs:
#             # Copy per-arch pyconfig.h with a unique name.
#             src_cfg = f'{bases[arch]}/usr/include/{alibname}/pyconfig.h'
#             dst_cfg = f'{include_dst}/pyconfig_{arch_compile_arch[arch]}.h'
#             assert not os.path.exists(dst_cfg), f'exists: {dst_cfg}'
#             subprocess.run(['cp', src_cfg, dst_cfg], check=True)
#             assert os.path.exists(dst_cfg)
#
#             # Copy _sysconfigdata script.
#             sysconfig_src = (
#                 f'{bases[arch]}/usr/lib/python{PY_VER}/'
#                 f'_sysconfigdata_{debug_d}_{arch_sysconfig_suffix[arch]}.py'
#             )
#             sysconfig_dst = os.path.join(
#                 pylib_dst, os.path.basename(sysconfig_src)
#             )
#             assert not os.path.exists(sysconfig_dst)
#             subprocess.run(['cp', sysconfig_src, pylib_dst], check=True)
#
#             # Gather libs for this arch.
#             libinst = arch_libinst[arch]
#             targetdir = f'{lib_dst}/{libinst}'
#             subprocess.run(['mkdir', '-p', targetdir], check=True)
#             libs = [
#                 f'{bases[arch]}/usr/lib/lib{alibname}.a',
#                 f'{bases2[arch]}/usr/lib/libssl.a',
#                 f'{bases2[arch]}/usr/lib/libcrypto.a',
#                 f'{bases2[arch]}/usr/lib/liblzma.a',
#                 f'{bases2[arch]}/usr/lib/libsqlite3.a',
#                 f'{bases2[arch]}/usr/lib/libffi.a',
#                 f'{bases2[arch]}/usr/lib/libbz2.a',
#                 f'{bases2[arch]}/usr/lib/libuuid.a',
#             ]
#             for lib in libs:
#                 finalpath = os.path.join(targetdir, os.path.basename(lib))
#                 assert not os.path.exists(finalpath), f'exists: {finalpath}'
#                 subprocess.run(['cp', lib, targetdir], check=True)
#                 assert os.path.exists(finalpath)
#
#     print('gather: done.')
