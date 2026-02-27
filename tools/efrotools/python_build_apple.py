# Released under the MIT License. See LICENSE for details.
#
"""Self-contained Apple Python build script.

Builds a static libpython3.13.a for each Apple platform slice
(macOS, iOS, tvOS, visionOS) and assembles them into a Python.xcframework.
Uses BeeWare's Python.patch and prebuilt cpython-apple-source-deps.
"""

# pylint: disable=too-many-lines
from __future__ import annotations

import glob
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Version constants (bump these to update)
# ---------------------------------------------------------------------------
#
# To sync with a new BeeWare Python-Apple-support release:
#
#   1. Update PY_VER_EXACT to the new Python micro version (e.g. 3.13.12).
#      This invalidates the Python source tarball and patch caches
#      automatically.
#
#   2. If BeeWare updated their patches independently of a Python bump, set
#      BEEWARE_COMMIT to the specific commit hash from the Python-Apple-support
#      repo.  This invalidates the patch cache while keeping the branch name
#      stable.  Clear BEEWARE_COMMIT (set back to None) once the branch tip is
#      trustworthy again.
#
#   3. Update any *_VER constants below whose versions changed in the new
#      cpython-apple-source-deps release.  The dep tarball filenames include
#      the version, so the download cache invalidates automatically.
#
#   4. Run `make python-apple-build` to rebuild all slices and verify.
#
# ---------------------------------------------------------------------------

PY_VER = '3.13'
PY_VER_EXACT = '3.13.11'
BEEWARE_BRANCH = '3.13'
# BEEWARE_COMMIT: str | None = None  # Pin to a commit hash to override branch.
BEEWARE_COMMIT: str | None = None

# Prebuilt dep versions from beeware/cpython-apple-source-deps.
OPENSSL_VER = '3.0.18-1'
LIBFFI_VER = '3.4.7-2'
XZ_VER = '5.6.4-2'
BZIP2_VER = '1.0.8-2'
MPDECIMAL_VER = '4.0.0-2'

# Deployment targets.
MACOS_MIN = '11.0'
IOS_MIN = '13.0'
TVOS_MIN = '12.0'
VISIONOS_MIN = '2.0'

# ---------------------------------------------------------------------------
# Slice table
# ---------------------------------------------------------------------------

# Maps slice name -> (sdk, host_triple, is_macos)
# is_macos=True: use native clang; False: use BeeWare toolchain wrappers.
_SLICE_INFO: dict[str, tuple[str, str, bool]] = {
    'macosx.arm64': (
        'macosx',
        f'arm64-apple-macosx{MACOS_MIN}',
        True,
    ),
    'macosx.x86_64': (
        'macosx',
        f'x86_64-apple-macosx{MACOS_MIN}',
        True,
    ),
    'iphoneos.arm64': (
        'iphoneos',
        f'aarch64-apple-ios{IOS_MIN}',
        False,
    ),
    'iphonesimulator.arm64': (
        'iphonesimulator',
        f'aarch64-apple-ios{IOS_MIN}-simulator',
        False,
    ),
    'iphonesimulator.x86_64': (
        'iphonesimulator',
        f'x86_64-apple-ios{IOS_MIN}-simulator',
        False,
    ),
    'appletvos.arm64': (
        'appletvos',
        f'aarch64-apple-tvos{TVOS_MIN}',
        False,
    ),
    'appletvsimulator.arm64': (
        'appletvsimulator',
        f'aarch64-apple-tvos{TVOS_MIN}-simulator',
        False,
    ),
    'appletvsimulator.x86_64': (
        'appletvsimulator',
        f'x86_64-apple-tvos{TVOS_MIN}-simulator',
        False,
    ),
    'xros.arm64': (
        'xros',
        f'aarch64-apple-xros{VISIONOS_MIN}',
        False,
    ),
    'xrsimulator.arm64': (
        'xrsimulator',
        f'aarch64-apple-xros{VISIONOS_MIN}-simulator',
        False,
    ),
}

# Public list of all valid slice names (used by pcommands.py).
SLICES = list(_SLICE_INFO.keys())

# Map SDK name -> BeeWare dep package SDK tag.
_SDK_DEP_TAG: dict[str, str] = {
    'macosx': 'macosx',
    'iphoneos': 'iphoneos',
    'iphonesimulator': 'iphonesimulator',
    'appletvos': 'appletvos',
    'appletvsimulator': 'appletvsimulator',
    'xros': 'xros',
    'xrsimulator': 'xrsimulator',
}

# Map SDK -> deployment-target env var name (for BeeWare wrappers).
_SDK_DEPLOY_ENV: dict[str, str] = {
    'iphoneos': 'IPHONEOS_DEPLOYMENT_TARGET',
    'iphonesimulator': 'IPHONEOS_DEPLOYMENT_TARGET',
    'appletvos': 'TVOS_DEPLOYMENT_TARGET',
    'appletvsimulator': 'TVOS_DEPLOYMENT_TARGET',
    'xros': 'XROS_DEPLOYMENT_TARGET',
    'xrsimulator': 'XROS_DEPLOYMENT_TARGET',
}

# Map SDK -> deployment target value.
_SDK_DEPLOY_VER: dict[str, str] = {
    'iphoneos': IOS_MIN,
    'iphonesimulator': IOS_MIN,
    'appletvos': TVOS_MIN,
    'appletvsimulator': TVOS_MIN,
    'xros': VISIONOS_MIN,
    'xrsimulator': VISIONOS_MIN,
}


# ---------------------------------------------------------------------------
# Fetch / extract helpers (mirrors python_build_android.py)
# ---------------------------------------------------------------------------


def _fetch(url: str, cache_dir: str, cache_name: str | None = None) -> str:
    """Download url into cache_dir; return local path.

    cache_name overrides the filename used as the cache key.
    """
    os.makedirs(cache_dir, exist_ok=True)
    fname = cache_name if cache_name is not None else url.split('/')[-1]
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
    with tarfile.open(tarball) as tf:
        top = tf.getmembers()[0].name.split('/')[0]
        tf.extractall(destdir, filter='tar')
    return os.path.join(destdir, top)


def _cpus() -> int:
    return os.cpu_count() or 4


# ---------------------------------------------------------------------------
# BeeWare patch fetchers
# ---------------------------------------------------------------------------


def _beeware_ref() -> str:
    """Return the BeeWare git ref to use (commit or branch)."""
    return BEEWARE_COMMIT if BEEWARE_COMMIT is not None else BEEWARE_BRANCH


def _fetch_beeware_patch(cache_dir: str, patch_filename: str) -> str:
    """Fetch a patch file from the BeeWare Python-Apple-support repo."""
    ref = _beeware_ref()
    url = (
        f'https://raw.githubusercontent.com/beeware/Python-Apple-support/'
        f'{ref}/patch/Python/{patch_filename}'
    )
    # Include the ref and Python version in the cache name so the cache
    # invalidates on branch/commit changes and on Python minor version bumps.
    safe_ref = ref.replace('/', '_')
    cache_name = f'beeware-{safe_ref}-{PY_VER_EXACT}-{patch_filename}'
    return _fetch(url, cache_dir, cache_name=cache_name)


def _check_beeware_versions(cache_dir: str) -> None:
    """Fetch BeeWare's Makefile and verify our version constants match.

    Raises ValueError listing all mismatches found.  If a variable cannot be
    located in the Makefile (e.g. BeeWare renamed it), a warning is printed
    but the build is not blocked — the download step will fail loudly anyway
    if a dep tarball URL doesn't exist.
    """
    ref = _beeware_ref()
    url = (
        f'https://raw.githubusercontent.com/beeware/Python-Apple-support/'
        f'{ref}/Makefile'
    )
    safe_ref = ref.replace('/', '_')
    cache_name = f'beeware-{safe_ref}-{PY_VER_EXACT}-Makefile'
    makefile_path = _fetch(url, cache_dir, cache_name=cache_name)
    with open(makefile_path, encoding='utf-8') as fh:
        content = fh.read()

    # Map: Makefile variable -> (our constant value, our constant name).
    checks = [
        ('PYTHON_VERSION', PY_VER_EXACT, 'PY_VER_EXACT'),
        ('OPENSSL_VERSION', OPENSSL_VER, 'OPENSSL_VER'),
        ('LIBFFI_VERSION', LIBFFI_VER, 'LIBFFI_VER'),
        ('XZ_VERSION', XZ_VER, 'XZ_VER'),
        ('BZIP2_VERSION', BZIP2_VER, 'BZIP2_VER'),
        ('MPDECIMAL_VERSION', MPDECIMAL_VER, 'MPDECIMAL_VER'),
    ]
    mismatches: list[str] = []
    for var, our_val, our_name in checks:
        m = re.search(rf'^{var}=(\S+)', content, re.MULTILINE)
        if m is None:
            print(
                f'  Warning: {var} not found in BeeWare Makefile'
                f' — cannot verify {our_name}'
            )
            continue
        beeware_val = m.group(1)
        if beeware_val != our_val:
            mismatches.append(
                f'  {our_name} = {our_val!r}'
                f'  but BeeWare {ref} has {var} = {beeware_val!r}'
            )
    if mismatches:
        raise ValueError(
            f'Version mismatch with BeeWare ref {ref!r}:\n'
            + '\n'.join(mismatches)
            + '\nUpdate the constants at the top of this file to match.'
        )
    print(f'  BeeWare version check passed (ref={ref!r})')


# ---------------------------------------------------------------------------
# Dep download helpers
# ---------------------------------------------------------------------------


def _dep_arch_tag(slice_name: str) -> str:
    """Return the arch portion of a BeeWare dep tarball name."""
    # Slice format: '<sdk>.<arch>' — but BeeWare uses 'x86_64' not 'x86-64'.
    arch = slice_name.split('.', 1)[1]
    return arch


def _fetch_dep(
    cache_dir: str,
    package: str,
    version: str,
    sdk: str,
    arch: str,
) -> str:
    """Fetch a prebuilt dep tarball from beeware/cpython-apple-source-deps."""
    tag = f'{package}-{version}'
    fname = f'{package}-{version}-{sdk}.{arch}.tar.gz'
    url = (
        f'https://github.com/beeware/cpython-apple-source-deps/'
        f'releases/download/{tag}/{fname}'
    )
    return _fetch(url, cache_dir)


# ---------------------------------------------------------------------------
# Toolchain env helpers
# ---------------------------------------------------------------------------


def _xcrun(sdk: str, tool: str) -> str:
    """Return the path to a tool in the given Xcode SDK toolchain."""
    return subprocess.check_output(
        ['xcrun', '--sdk', sdk, '--find', tool],
        text=True,
    ).strip()


def _sdk_path(sdk: str) -> str:
    """Return the sysroot path for the given Xcode SDK."""
    return subprocess.check_output(
        ['xcrun', '--sdk', sdk, '--show-sdk-path'],
        text=True,
    ).strip()


def _build_env_macos(arch: str, deps_dir: str | None = None) -> dict[str, str]:
    """Return env dict for a macOS slice (native clang, explicit arch).

    deps_dir, if given, restricts the library search path to the source-
    built dep prefix so we don't accidentally pick up Homebrew's arm64-only
    variants when cross-compiling for x86_64.
    """
    sdk = 'macosx'
    sysroot = _sdk_path(sdk)
    cc = subprocess.check_output(
        ['xcrun', '--sdk', sdk, '--find', 'clang'],
        text=True,
    ).strip()
    cxx = subprocess.check_output(
        ['xcrun', '--sdk', sdk, '--find', 'clang++'],
        text=True,
    ).strip()
    ar = subprocess.check_output(
        ['xcrun', '--sdk', sdk, '--find', 'ar'],
        text=True,
    ).strip()
    ranlib = subprocess.check_output(
        ['xcrun', '--sdk', sdk, '--find', 'ranlib'],
        text=True,
    ).strip()
    libtool_path = subprocess.check_output(
        ['xcrun', '--sdk', sdk, '--find', 'libtool'],
        text=True,
    ).strip()
    arch_flags = f'-arch {arch} -mmacosx-version-min={MACOS_MIN}'
    # -isysroot ensures both compiler and linker use the SDK's TBD stubs.
    # Without it, the macOS linker can't find unversioned library names like
    # libz.dylib (only versioned files, e.g. libz.1.dylib, exist on disk).
    sysroot_flag = f'-isysroot {sysroot}'
    env = dict(os.environ)
    env['CC'] = cc
    env['CXX'] = cxx
    env['AR'] = ar
    env['RANLIB'] = ranlib
    env['LIBTOOL'] = libtool_path
    env['CFLAGS'] = f'{arch_flags} {sysroot_flag}'
    env['CXXFLAGS'] = f'{arch_flags} {sysroot_flag}'
    env['SDKROOT'] = sysroot
    if deps_dir is not None:
        dep_lib = os.path.join(deps_dir, 'lib')
        dep_pc = os.path.join(deps_dir, 'lib', 'pkgconfig')
        # Restrict linker search to our source-built deps + SDK only.
        # This prevents configure from picking up Homebrew arm64 libs.
        env['LDFLAGS'] = f'{arch_flags} {sysroot_flag} -L{dep_lib}'
        # PKG_CONFIG_LIBDIR *replaces* (rather than prepends to) the built-in
        # default search paths, so Homebrew pkg-config no longer looks in
        # /opt/homebrew/lib/pkgconfig.  Set it to only our deps pc dir.
        env['PKG_CONFIG_LIBDIR'] = dep_pc
        env.pop('PKG_CONFIG_PATH', None)
    else:
        env['LDFLAGS'] = f'{arch_flags} {sysroot_flag}'
    return env


def _build_env_apple(sdk: str, _triple: str, pydir: str) -> dict[str, str]:
    """Return env dict for a non-macOS Apple slice (BeeWare wrappers).

    pydir must exist and already have the BeeWare patch applied so the
    Apple/{Platform}/Resources/bin/ wrapper scripts are present.
    """
    # BeeWare's Python.patch adds wrapper compiler scripts into the source
    # tree at Apple/{Platform}/Resources/bin/.  We need these on PATH so
    # configure can find e.g. 'arm64-apple-ios-clang'.
    sdk_to_platform: dict[str, str] = {
        'iphoneos': 'iOS',
        'iphonesimulator': 'iOS',
        'appletvos': 'tvOS',
        'appletvsimulator': 'tvOS',
        'xros': 'visionOS',
        'xrsimulator': 'visionOS',
    }
    platform_name = sdk_to_platform[sdk]
    wrapper_bin = os.path.join(
        pydir, 'Apple', platform_name, 'Resources', 'bin'
    )
    env = dict(os.environ)
    # Prepend the wrapper bin dir to PATH.
    cur_path = env.get('PATH', '/usr/local/bin:/usr/bin:/bin')
    env['PATH'] = wrapper_bin + ':' + cur_path
    # Set the platform deployment target env var expected by the wrappers.
    deploy_env = _SDK_DEPLOY_ENV[sdk]
    deploy_ver = _SDK_DEPLOY_VER[sdk]
    env[deploy_env] = deploy_ver
    return env


# ---------------------------------------------------------------------------
# macOS dep helpers (Homebrew)
# ---------------------------------------------------------------------------


def _macos_src_ver(beeware_ver: str) -> str:
    """Strip BeeWare build suffix from a dep version: '3.0.18-1' → '3.0.18'."""
    return beeware_ver.split('-')[0]


def _clean_macos_dep_env(arch: str) -> dict[str, str]:
    """Return a minimal, Homebrew-free env for building macOS deps from source.

    Starts from a minimal base (PATH, HOME, TMPDIR only) and explicitly sets
    all compiler-related variables so that nothing leaks in from the user's
    shell profile (CPPFLAGS, LDFLAGS, PKG_CONFIG_*, LIBRARY_PATH, etc.).

    Matches BeeWare's cpython-macOS-source-deps approach:
    - Architecture and deployment target are specified via -target in CC,
      keeping CFLAGS/LDFLAGS free of arch flags.
    - Sysroot is provided via -isysroot in CFLAGS/LDFLAGS so the compiler
      and linker use the SDK's TBD stubs for system libraries.
    """
    sysroot = _sdk_path('macosx')
    cc = _xcrun('macosx', 'clang')
    cxx = _xcrun('macosx', 'clang++')
    ar = _xcrun('macosx', 'ar')
    ranlib = _xcrun('macosx', 'ranlib')
    # -target encodes both arch and deployment target in one flag, which is
    # the modern clang way and what BeeWare's dep builds use.
    target_flag = f'-target {arch}-apple-macosx{MACOS_MIN}'
    sysroot_flag = f'-isysroot {sysroot}'
    return {
        # Minimal base — just enough for subprocesses to function.
        'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
        'HOME': os.environ.get('HOME', ''),
        'TMPDIR': os.environ.get('TMPDIR', '/tmp'),
        # Compiler toolchain — all explicit, nothing inherited.
        # Arch + deployment target live in CC via -target; CFLAGS/LDFLAGS
        # only carry the sysroot so they stay arch-neutral.
        'CC': f'{cc} {target_flag}',
        'CXX': f'{cxx} {target_flag}',
        'AR': ar,
        'RANLIB': ranlib,
        'CFLAGS': sysroot_flag,
        'CXXFLAGS': sysroot_flag,
        'CPPFLAGS': '',
        'LDFLAGS': sysroot_flag,
        # Disable pkg-config lookups entirely for dep builds.
        'PKG_CONFIG_LIBDIR': '',
        'PKG_CONFIG_PATH': '',
        # SDK root so the compiler and linker use the right TBD stubs.
        'SDKROOT': sysroot,
    }


def _build_macos_openssl_source(
    deps_dir: str, arch: str, cache_dir: str
) -> None:
    """Build OpenSSL from source into deps_dir for macOS/arch."""
    ver = _macos_src_ver(OPENSSL_VER)
    url = f'https://www.openssl.org/source/openssl-{ver}.tar.gz'
    tarball = _fetch(url, cache_dir)
    src_parent = os.path.join(deps_dir, '_src_openssl')
    srcdir = _extract(tarball, src_parent)
    env = _clean_macos_dep_env(arch)
    # OpenSSL uses darwin64-arm64-cc or darwin64-x86_64-cc.
    openssl_target = (
        'darwin64-arm64-cc' if arch == 'arm64' else 'darwin64-x86_64-cc'
    )
    subprocess.run(
        [
            './Configure',
            openssl_target,
            f'--prefix={deps_dir}',
            'no-shared',
            'no-tests',
        ],
        cwd=srcdir,
        env=env,
        check=True,
    )
    subprocess.run(['make', f'-j{_cpus()}'], cwd=srcdir, env=env, check=True)
    subprocess.run(['make', 'install_sw'], cwd=srcdir, env=env, check=True)


def _build_macos_xz_source(deps_dir: str, arch: str, cache_dir: str) -> None:
    """Build XZ (liblzma) from source into deps_dir for macOS/arch."""
    ver = _macos_src_ver(XZ_VER)
    url = (
        f'https://github.com/tukaani-project/xz/releases/download/'
        f'v{ver}/xz-{ver}.tar.gz'
    )
    tarball = _fetch(url, cache_dir)
    src_parent = os.path.join(deps_dir, '_src_xz')
    srcdir = _extract(tarball, src_parent)
    env = _clean_macos_dep_env(arch)
    subprocess.run(
        [
            './configure',
            f'--host={arch}-apple-darwin',
            f'--build={platform.machine()}-apple-darwin',
            f'--prefix={deps_dir}',
            '--disable-shared',
            '--enable-static',
            '--disable-xz',
            '--disable-xzdec',
            '--disable-lzmainfo',
            '--disable-lzma-links',
            '--disable-scripts',
            '--disable-doc',
        ],
        cwd=srcdir,
        env=env,
        check=True,
    )
    subprocess.run(['make', f'-j{_cpus()}'], cwd=srcdir, env=env, check=True)
    subprocess.run(['make', 'install'], cwd=srcdir, env=env, check=True)


def _build_macos_bzip2_source(deps_dir: str, arch: str, cache_dir: str) -> None:
    """Build bzip2 from source into deps_dir for macOS/arch."""
    ver = _macos_src_ver(BZIP2_VER)
    url = f'https://sourceware.org/pub/bzip2/bzip2-{ver}.tar.gz'
    tarball = _fetch(url, cache_dir)
    src_parent = os.path.join(deps_dir, '_src_bzip2')
    srcdir = _extract(tarball, src_parent)
    env = _clean_macos_dep_env(arch)
    # bzip2 uses a plain Makefile with no autoconf; pass CC (with arch target
    # and sysroot already embedded) as a make variable, matching BeeWare's
    # cpython-macOS-source-deps approach.
    cc_val = env['CC'] + ' ' + env['CFLAGS'] + ' -Wall -Winline -O2'
    cc_var = f'CC={cc_val}'
    subprocess.run(
        ['make', f'-j{_cpus()}', 'libbz2.a', cc_var],
        cwd=srcdir,
        env=env,
        check=True,
    )
    subprocess.run(
        ['make', 'install', f'PREFIX={deps_dir}', cc_var],
        cwd=srcdir,
        env=env,
        check=True,
    )


def _build_macos_deps_from_source(
    deps_dir: str, arch: str, cache_dir: str
) -> tuple[str, str, str]:
    """Build all macOS deps from source; return (openssl_prefix, cflags, libs).

    Called when Homebrew cannot provide architecture-compatible libraries
    (e.g., building x86_64 on Apple Silicon, or for reproducibility).
    """
    os.makedirs(deps_dir, exist_ok=True)
    print(f'Building macOS deps from source for arch={arch}...')
    _build_macos_openssl_source(deps_dir, arch, cache_dir)
    _build_macos_xz_source(deps_dir, arch, cache_dir)
    _build_macos_bzip2_source(deps_dir, arch, cache_dir)
    # mpdecimal: Python 3.13 bundles a copy of mpdecimal (HACL*-accelerated)
    # and CPython's configure will use it automatically when
    # --with-system-libmpdec is absent.  No need to build it from source for
    # macOS, matching BeeWare's
    # cpython-macOS-source-deps which also omits mpdecimal.
    dep_inc = os.path.join(deps_dir, 'include')
    dep_lib = os.path.join(deps_dir, 'lib')
    cflags = f'-I{dep_inc}'
    libs = f'-L{dep_lib}'
    return deps_dir, cflags, libs


# ---------------------------------------------------------------------------
# Module setup patch
# ---------------------------------------------------------------------------


def _patch_modules_setup(pydir: str) -> None:
    """Apply the full module enable/disable list from pybuild.

    Uses the same cmodules/enables table as the Android build to ensure
    consistent coverage.  Modules not in the enables set are commented out
    and added to a *disabled* section so Python's build system cannot fall
    back to building them as shared extensions.
    """
    from efrotools.pybuild import patch_modules_setup

    patch_modules_setup(pydir, 'apple')


def _patch_macos_makefile(pydir: str) -> None:
    """Patch the generated Makefile for macOS cross-compilation correctness.

    Removes ``-ldl`` (dlopen is part of libSystem on macOS; no standalone
    libdl exists in the modern SDK) and clears MODULE__BLAKE2_LDFLAGS so
    the build uses the built-in HACL* blake2 instead of an arch-incompatible
    Homebrew libb2.
    """
    mk = os.path.join(pydir, 'Makefile')
    with open(mk, encoding='utf-8') as fh:
        txt = fh.read()
    # Remove all -ldl occurrences (may appear in LIBS, MODULE__CTYPES_LDFLAGS…).
    # Use a word-boundary regex so tabs/spaces before -ldl are handled.
    # Warning only: a future Python or macOS SDK may simply stop emitting -ldl,
    # which would be correct behaviour — not a sign anything broke.
    txt, n_ldl = re.subn(r'\s*-ldl\b', '', txt)
    if n_ldl == 0:
        print(
            '  Note: -ldl not found in Makefile — Python may have stopped'
            ' adding it, or the SDK now exposes libdl. Verify the build'
            ' still links correctly and remove this workaround if so.'
        )

    # Clear MODULE__BLAKE2_LDFLAGS — Python 3.13 has built-in HACL* blake2.
    # If left pointing at Homebrew, the arm64-only libb2 breaks x86_64 builds.
    # Warning only: if our PKG_CONFIG_LIBDIR isolation already prevented libb2
    # detection, the value may already be empty; if Python renames the variable,
    # the fix is a no-op but the build may still work via HACL*.
    txt, n_blake2 = re.subn(
        r'^(MODULE__BLAKE2_LDFLAGS=).*$',
        r'\1',
        txt,
        flags=re.MULTILINE,
    )
    if n_blake2 == 0:
        print(
            '  Note: MODULE__BLAKE2_LDFLAGS not found in Makefile — Python'
            ' may have renamed it. Verify no arm64-only libb2 is being linked'
            ' and update _patch_macos_makefile() if needed.'
        )
    with open(mk, 'w', encoding='utf-8') as fh:
        fh.write(txt)


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------


def build(rootdir: str, slice_name: str) -> None:
    """Build Python for a single Apple platform slice.

    slice_name must be one of SLICES.
    Output is written to build/python_apple_{slice_name_underscored}/.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    if slice_name not in _SLICE_INFO:
        raise ValueError(
            f'Invalid slice {slice_name!r}; must be one of: {SLICES}'
        )

    sdk, triple, is_macos = _SLICE_INFO[slice_name]
    arch = _dep_arch_tag(slice_name)
    safe_slice = slice_name.replace('.', '_')
    build_dir = os.path.join(rootdir, f'build/python_apple_{safe_slice}')
    src_dir = os.path.join(build_dir, 'src')
    pydir = os.path.join(src_dir, f'Python-{PY_VER_EXACT}')
    deps_dir = os.path.join(build_dir, 'deps')
    cache_dir = os.path.join(rootdir, 'build', 'python_deps_cache')

    print(f'=== Building Python {PY_VER_EXACT} for Apple/{slice_name} ===')
    print(f'    build_dir: {build_dir}')

    # ------------------------------------------------------------------
    # 0. Verify version constants match BeeWare's Makefile.
    # ------------------------------------------------------------------
    print('Checking BeeWare version constants...')
    _check_beeware_versions(cache_dir)

    # Start fresh.
    subprocess.run(['rm', '-rf', build_dir], check=True)
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(deps_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Fetch and extract Python source.
    # ------------------------------------------------------------------
    print('Fetching Python source...')
    py_url = (
        f'https://www.python.org/ftp/python/{PY_VER_EXACT}/'
        f'Python-{PY_VER_EXACT}.tgz'
    )
    py_tarball = _fetch(py_url, cache_dir)
    _extract(py_tarball, src_dir)
    assert os.path.isdir(pydir), f'Python source not found at {pydir}'

    # ------------------------------------------------------------------
    # 2. Fetch and apply BeeWare patches.
    # ------------------------------------------------------------------
    print('Fetching BeeWare patches...')
    python_patch = _fetch_beeware_patch(cache_dir, 'Python.patch')
    compliance_patch = _fetch_beeware_patch(
        cache_dir, 'app-store-compliance.patch'
    )

    print('Applying Python.patch...')
    subprocess.run(
        ['patch', '-p1', '--input', python_patch],
        cwd=pydir,
        check=True,
    )
    print('Applying app-store-compliance.patch...')
    subprocess.run(
        ['patch', '-p1', '--input', compliance_patch],
        cwd=pydir,
        check=True,
    )

    # patch(1) does not restore the executable bit on newly created files.
    # Make all wrapper scripts under Apple/*/Resources/bin/ executable.
    for wrapper_bin_glob in glob.glob(
        os.path.join(pydir, 'Apple', '*', 'Resources', 'bin', '*')
    ):
        if os.path.isfile(wrapper_bin_glob):
            os.chmod(wrapper_bin_glob, 0o755)

    # ------------------------------------------------------------------
    # 3. Fetch and extract prebuilt deps.
    # ------------------------------------------------------------------
    print('Fetching prebuilt deps...')

    if is_macos:
        # BeeWare does not ship macOS (desktop) dep tarballs —
        # only iOS/tvOS/visionOS/watchOS variants are available in
        # cpython-apple-source-deps.  Build the deps from source so the
        # result is self-contained and arch-correct (including x86_64 on
        # Apple Silicon where Homebrew only provides arm64 libraries).
        openssl_prefix, extra_cflags, extra_libs = (
            _build_macos_deps_from_source(deps_dir, arch, cache_dir)
        )
    else:
        # BeeWare dep tarballs have a flat layout: they contain 'include/'
        # and 'lib/' directly (no wrapping top-level directory).  We
        # extract all of them into the same deps_dir so that
        # deps_dir/include/ and deps_dir/lib/ merge together.
        dep_packages: list[tuple[str, str]] = [
            ('OpenSSL', OPENSSL_VER),
            ('XZ', XZ_VER),
            ('BZip2', BZIP2_VER),
            ('mpdecimal', MPDECIMAL_VER),
            ('libFFI', LIBFFI_VER),
        ]

        dep_sdk = _SDK_DEP_TAG[sdk]
        os.makedirs(deps_dir, exist_ok=True)
        for pkg, ver in dep_packages:
            tb = _fetch_dep(cache_dir, pkg, ver, dep_sdk, arch)
            # Use tar directly to extract flat into deps_dir.
            subprocess.run(['tar', '-xf', tb, '-C', deps_dir], check=True)

        dep_inc = os.path.join(deps_dir, 'include')
        dep_lib = os.path.join(deps_dir, 'lib')
        openssl_prefix = deps_dir
        extra_cflags = f'-I{dep_inc}'
        extra_libs = f'-L{dep_lib}'

    # ------------------------------------------------------------------
    # 4. Patch Modules/Setup.stdlib.in: *shared* -> *static*.
    # ------------------------------------------------------------------
    print('Patching Modules/Setup.stdlib.in...')
    _patch_modules_setup(pydir)

    # ------------------------------------------------------------------
    # 5. Build environment.
    # ------------------------------------------------------------------
    if is_macos:
        env = _build_env_macos(arch, deps_dir=deps_dir)
    else:
        env = _build_env_apple(sdk, triple, pydir)

    # ------------------------------------------------------------------
    # 6. Build host python path.
    # ------------------------------------------------------------------
    build_python = sys.executable

    # ------------------------------------------------------------------
    # 7. Configure Python.
    # ------------------------------------------------------------------
    print('Configuring Python...')
    uname_release = platform.release()

    if is_macos:
        # macOS: configure does not support --host for cross-arch builds;
        # the -arch flag in CFLAGS/LDFLAGS (set via _build_env_macos)
        # drives the target arch.  No --host or --build flags needed.
        # mpdecimal: omit --with-system-libmpdec so Python uses its bundled
        # copy (same as BeeWare's macOS dep builds — they don't build mpdecimal
        # from source either).
        configure_cmd = [
            './configure',
            f'--with-build-python={build_python}',
            '--enable-framework',
            '--without-ensurepip',
            f'--with-openssl={openssl_prefix}',
            '--disable-test-modules',
        ]
    else:
        configure_cmd = [
            './configure',
            f'--host={triple}',
            f'--build=arm64-apple-darwin{uname_release}',
            f'--with-build-python={build_python}',
            '--enable-framework',
            '--without-ensurepip',
            f'--with-openssl={openssl_prefix}',
            '--with-system-libmpdec',
        ]

    # Pass dep include/lib flags via env variables for each library.
    # XZ / liblzma
    env['LIBLZMA_CFLAGS'] = extra_cflags
    env['LIBLZMA_LIBS'] = extra_libs + ' -llzma'

    # bzip2
    env['BZIP2_CFLAGS'] = extra_cflags
    env['BZIP2_LIBS'] = extra_libs + ' -lbz2'

    # mpdecimal: non-macOS slices use BeeWare's prebuilt mpdecimal.
    # macOS uses Python's bundled copy (no --with-system-libmpdec in configure).
    if not is_macos:
        env['LIBMPDEC_CFLAGS'] = extra_cflags
        env['LIBMPDEC_LIBS'] = extra_libs + ' -lmpdec'

    # libffi (non-macOS only; macOS uses system libffi).
    if not is_macos:
        env['LIBFFI_CFLAGS'] = extra_cflags
        env['LIBFFI_LIBS'] = extra_libs + ' -lffi'

    subprocess.run(configure_cmd, cwd=pydir, env=env, check=True)

    # ------------------------------------------------------------------
    # 8b. Post-configure Makefile fixups (macOS only).
    # ------------------------------------------------------------------
    if is_macos:
        _patch_macos_makefile(pydir)

    # ------------------------------------------------------------------
    # 9. Build libpython<VER>.a (stop before framework creation).
    # ------------------------------------------------------------------
    lib_target = f'libpython{PY_VER}.a'
    print(f'Building {lib_target}...')
    subprocess.run(
        ['make', f'-j{_cpus()}', lib_target],
        cwd=pydir,
        env=env,
        check=True,
    )

    src_lib = os.path.join(pydir, lib_target)
    assert os.path.isfile(src_lib), f'Expected {src_lib} to exist after build'

    # ------------------------------------------------------------------
    # 9b. Collect all dep .a files and merge into one fat archive.
    # ------------------------------------------------------------------
    print('Merging dep .a files...')
    # deps_dir/lib contains all the static .a files for both macOS (source-
    # built) and non-macOS (BeeWare prebuilt) slices.
    dep_lib_dir = os.path.join(deps_dir, 'lib')
    dep_libs_a = sorted(glob.glob(os.path.join(dep_lib_dir, '*.a')))

    merged_lib = os.path.join(build_dir, 'libpython_merged.a')
    libtool_cmd = [
        'libtool',
        '-static',
        '-o',
        merged_lib,
        src_lib,
    ] + dep_libs_a
    subprocess.run(libtool_cmd, check=True)
    assert os.path.isfile(merged_lib)

    # ------------------------------------------------------------------
    # 11. Copy headers.
    # ------------------------------------------------------------------
    print('Copying headers...')
    include_dst = os.path.join(build_dir, 'include')
    shutil.copytree(os.path.join(pydir, 'Include'), include_dst)
    # Copy pyconfig.h (generated by configure, lives in pydir root).
    shutil.copy2(os.path.join(pydir, 'pyconfig.h'), include_dst)

    print(
        f'=== Python {PY_VER_EXACT} for Apple/{slice_name} build complete! ==='
    )
    print(f'    merged lib: {merged_lib}')


# ---------------------------------------------------------------------------
# Gather function
# ---------------------------------------------------------------------------


def gather(rootdir: str) -> None:
    """Assemble all slices into Python.xcframework and copy to project.

    Expects all 10 slice builds to exist under build/python_apple_*/
    Outputs:
      src/external/python-apple-new/Python.xcframework
      src/assets/pylib-apple-new/
    """
    # pylint: disable=too-many-locals
    from efrotools.pybuild import PRUNE_LIB_NAMES, tweak_empty_py_files

    print('=== Gathering Apple Python slices ===')

    def _slice_build_dir(slice_name: str) -> str:
        safe = slice_name.replace('.', '_')
        return os.path.join(rootdir, f'build/python_apple_{safe}')

    def _merged_lib(slice_name: str) -> str:
        return os.path.join(_slice_build_dir(slice_name), 'libpython_merged.a')

    def _include_dir(slice_name: str) -> str:
        return os.path.join(_slice_build_dir(slice_name), 'include')

    # Verify all slices are built.
    for sl in SLICES:
        lib = _merged_lib(sl)
        if not os.path.isfile(lib):
            raise RuntimeError(
                f'Missing merged lib for slice {sl!r}: {lib}\n'
                f'Run the individual slice build first.'
            )

    build_dir = os.path.join(rootdir, 'build')

    # ------------------------------------------------------------------
    # 1. lipo-merge simulator pairs (same SDK, different arch).
    # ------------------------------------------------------------------
    print('lipo-merging simulator pairs...')

    def _lipo_merge(a_slices: list[str], out_name: str) -> tuple[str, str]:
        """lipo-merge multiple slice .a files, return (merged_lib, include)."""
        out_dir = os.path.join(build_dir, out_name)
        os.makedirs(out_dir, exist_ok=True)
        out_lib = os.path.join(out_dir, 'libpython_merged.a')
        lipo_cmd = ['lipo', '-create', '-output', out_lib] + [
            _merged_lib(sl) for sl in a_slices
        ]
        subprocess.run(lipo_cmd, check=True)
        # Use the first slice's include dir (same headers for all arches).
        return out_lib, _include_dir(a_slices[0])

    # iOS simulators: arm64 + x86_64.
    sim_ios_lib, sim_ios_inc = _lipo_merge(
        ['iphonesimulator.arm64', 'iphonesimulator.x86_64'],
        'python_apple_sim_ios',
    )

    # tvOS simulators: arm64 + x86_64.
    sim_tvos_lib, sim_tvos_inc = _lipo_merge(
        ['appletvsimulator.arm64', 'appletvsimulator.x86_64'],
        'python_apple_sim_tvos',
    )

    # macOS: arm64 + x86_64.
    macos_lib, macos_inc = _lipo_merge(
        ['macosx.arm64', 'macosx.x86_64'],
        'python_apple_macos',
    )

    # xrOS simulator: arm64 only — no lipo needed, just reference directly.
    xrsim_lib = _merged_lib('xrsimulator.arm64')
    xrsim_inc = _include_dir('xrsimulator.arm64')

    # ------------------------------------------------------------------
    # 2. Build XCFramework.
    # ------------------------------------------------------------------
    print('Building XCFramework...')
    xcfw_out = os.path.join(
        build_dir, 'python_apple_xcframework', 'Python.xcframework'
    )
    # Remove old xcframework if present.
    if os.path.exists(xcfw_out):
        shutil.rmtree(xcfw_out)
    os.makedirs(os.path.dirname(xcfw_out), exist_ok=True)

    # Each device slice is a singleton (one arch per device SDK).
    def _xcfw_lib_args(lib_path: str, inc_path: str) -> list[str]:
        return ['-library', lib_path, '-headers', inc_path]

    xcodebuild_cmd = (
        ['xcodebuild', '-create-xcframework']
        + _xcfw_lib_args(macos_lib, macos_inc)
        + _xcfw_lib_args(
            _merged_lib('iphoneos.arm64'), _include_dir('iphoneos.arm64')
        )
        + _xcfw_lib_args(sim_ios_lib, sim_ios_inc)
        + _xcfw_lib_args(
            _merged_lib('appletvos.arm64'), _include_dir('appletvos.arm64')
        )
        + _xcfw_lib_args(sim_tvos_lib, sim_tvos_inc)
        + _xcfw_lib_args(_merged_lib('xros.arm64'), _include_dir('xros.arm64'))
        + _xcfw_lib_args(xrsim_lib, xrsim_inc)
        + ['-output', xcfw_out]
    )
    subprocess.run(xcodebuild_cmd, check=True)
    assert os.path.isdir(xcfw_out), f'xcframework not created: {xcfw_out}'

    # ------------------------------------------------------------------
    # 3. Gather stdlib from any one slice (all are identical).
    # ------------------------------------------------------------------
    print('Gathering stdlib...')
    ref_slice = 'iphoneos.arm64'
    ref_pydir = os.path.join(
        _slice_build_dir(ref_slice), 'src', f'Python-{PY_VER_EXACT}'
    )
    stdlib_src = os.path.join(ref_pydir, 'Lib')
    stdlib_dst = os.path.join(build_dir, 'python_apple_stdlib')

    if os.path.exists(stdlib_dst):
        shutil.rmtree(stdlib_dst)
    # rsync only .py files, skip __pycache__.
    subprocess.run(
        [
            'rsync',
            '--recursive',
            '--include',
            '*.py',
            '--exclude',
            '__pycache__',
            '--include',
            '*/',
            '--exclude',
            '*',
            f'{stdlib_src}/',
            stdlib_dst,
        ],
        check=True,
    )
    tweak_empty_py_files(stdlib_dst)
    # Prune unwanted modules (shell expansion needed for globs).
    subprocess.run(
        'cd "' + stdlib_dst + '" && rm -rf ' + ' '.join(PRUNE_LIB_NAMES),
        shell=True,
        check=True,
    )

    # ------------------------------------------------------------------
    # 4. Copy to project.
    # ------------------------------------------------------------------
    print('Copying to project...')
    xcfw_dst = os.path.join(
        rootdir, 'src', 'external', 'python-apple-new', 'Python.xcframework'
    )
    pylib_dst = os.path.join(rootdir, 'src', 'assets', 'pylib-apple-new')

    # XCFramework.
    if os.path.exists(xcfw_dst):
        shutil.rmtree(xcfw_dst)
    os.makedirs(os.path.dirname(xcfw_dst), exist_ok=True)
    shutil.copytree(xcfw_out, xcfw_dst)

    # Stdlib.
    if os.path.exists(pylib_dst):
        shutil.rmtree(pylib_dst)
    shutil.copytree(stdlib_dst, pylib_dst)

    print('=== Apple Python gather complete! ===')
    print(f'    XCFramework: {xcfw_dst}')
    print(f'    Stdlib:      {pylib_dst}')
