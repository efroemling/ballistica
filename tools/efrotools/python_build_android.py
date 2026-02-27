# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Self-contained Android Python build script.

Replaces the GRRedWings/python3-android clone+patch approach with a
clean, in-tree build that owns all build logic directly.
No external repo dependency.
"""

from __future__ import annotations

import glob
import os
import subprocess
import tarfile
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Version constants (easy to bump at the top of the file).
PY_VER = '3.13'
PY_VER_EXACT = '3.13.12'
ANDROID_API_VER = 24
OPENSSL_VER = '3.0.19'
ZLIB_VER = '1.3.2'
XZ_VER = '5.8.2'
BZIP2_VER = '1.0.8'
LIBFFI_VER = '3.5.2'
LIBUUID_VER: tuple[str, str] = ('2.41', '2.41')  # (minor, full)
SQLITE_VER: tuple[str, str] = ('2026', '3510200')  # (year, autoconf id)

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

# OpenSSL configure target names per arch.
_OPENSSL_TARGETS: dict[str, str] = {
    'arm': 'android-arm',
    'arm64': 'android-arm64',
    'x86': 'android-x86',
    'x86_64': 'android-x86_64',
}


def _get_ndk_path(rootdir: str) -> str:
    """Return the NDK path by calling android_sdk_utils."""
    result = subprocess.check_output(
        [f'{rootdir}/tools/pcommand', 'android_sdk_utils', 'get-ndk-path']
    )
    path = result.decode().strip()
    if not os.path.isdir(path):
        raise RuntimeError(f'NDK path does not exist: "{path}".')
    return path


def _get_toolchain_bin(ndk_path: str) -> str:
    """Return the path to the NDK LLVM toolchain bin dir."""
    return os.path.join(
        ndk_path, 'toolchains', 'llvm', 'prebuilt', 'linux-x86_64', 'bin'
    )


def _build_env(
    arch: str, api: int, ndk_path: str, tc_bin: str, dep_sysroot: str
) -> dict[str, str]:
    """Return an environment dict for cross-compiling to Android.

    dep_sysroot is the local sysroot where we install our built deps
    (openssl, zlib, etc.) so Python's configure can find them.
    """
    target = ARCH_TARGETS[arch]
    bare = ARCH_TARGETS_BARE[arch]
    versioned = f'{target}{api}'

    cc = f'{tc_bin}/{versioned}-clang'
    cxx = f'{tc_bin}/{versioned}-clang++'

    # Keep a minimal PATH that includes the toolchain bin.
    host_path = os.environ.get(
        'PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    )
    path = f'{tc_bin}:{host_path}'

    env: dict[str, str] = {
        'PATH': path,
        'CC': cc,
        'CXX': cxx,
        'CPP': f'{cc} -E',
        'AR': f'{tc_bin}/llvm-ar',
        'AS': f'{tc_bin}/{bare}-as',
        'NM': f'{tc_bin}/llvm-nm',
        'RANLIB': f'{tc_bin}/llvm-ranlib',
        'STRIP': f'{tc_bin}/llvm-strip',
        'CFLAGS': f'-fPIC -DANDROID -D__ANDROID_API__={api}',
        'CPPFLAGS': f'-I{dep_sysroot}/usr/include',
        'LDFLAGS': f'-L{dep_sysroot}/usr/lib',
        'PKG_CONFIG_SYSROOT_DIR': dep_sysroot,
        # OpenSSL uses ANDROID_NDK_ROOT to locate toolchain internals.
        'ANDROID_NDK_ROOT': ndk_path,
        # Some configure scripts check HOME.
        'HOME': os.environ.get('HOME', '/root'),
        # Locale settings.
        'LANG': 'en_US.UTF-8',
        'LC_ALL': 'en_US.UTF-8',
    }
    return env


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


def _cpus() -> int:
    return os.cpu_count() or 4


# ---------------------------------------------------------------------------
# Dependency builders
# ---------------------------------------------------------------------------


def _build_zlib(
    cache_dir: str,
    build_dir: str,
    dep_sysroot: str,
    arch: str,
    env: dict[str, str],
) -> None:
    """Build and install zlib into dep_sysroot."""
    print('Building zlib...')
    url = f'https://www.zlib.net/zlib-{ZLIB_VER}.tar.gz'
    tarball = _fetch(url, cache_dir)
    srcdir = _extract(tarball, build_dir)

    target = ARCH_TARGETS[arch]
    subprocess.run(
        [
            './configure',
            f'--prefix={dep_sysroot}/usr',
            f'CHOST={target}',
            '--static',
        ],
        cwd=srcdir,
        env=env,
        check=True,
    )
    subprocess.run(['make', f'-j{_cpus()}'], cwd=srcdir, env=env, check=True)
    subprocess.run(['make', 'install'], cwd=srcdir, env=env, check=True)


def _build_bzip2(
    cache_dir: str,
    build_dir: str,
    dep_sysroot: str,
    env: dict[str, str],
) -> None:
    """Build and install bzip2 into dep_sysroot."""
    print('Building bzip2...')
    url = f'https://sourceware.org/pub/bzip2/bzip2-{BZIP2_VER}.tar.gz'
    tarball = _fetch(url, cache_dir)
    srcdir = _extract(tarball, build_dir)

    cc = env['CC']
    ar = env['AR']
    ranlib = env['RANLIB']
    cflags = env.get('CFLAGS', '')

    # bzip2 uses a plain Makefile with no configure.
    subprocess.run(
        [
            'make',
            f'-j{_cpus()}',
            'libbz2.a',
            f'CC={cc}',
            f'AR={ar}',
            f'RANLIB={ranlib}',
            f'CFLAGS={cflags} -Wall -Winline -O2',
        ],
        cwd=srcdir,
        env=env,
        check=True,
    )
    # Manual install.
    prefix = f'{dep_sysroot}/usr'
    os.makedirs(f'{prefix}/include', exist_ok=True)
    os.makedirs(f'{prefix}/lib', exist_ok=True)
    for hdr in ['bzlib.h']:
        subprocess.run(
            ['cp', hdr, f'{prefix}/include/'],
            cwd=srcdir,
            check=True,
        )
    subprocess.run(
        ['cp', 'libbz2.a', f'{prefix}/lib/'],
        cwd=srcdir,
        check=True,
    )
    subprocess.run([env['RANLIB'], f'{prefix}/lib/libbz2.a'], check=True)


def _build_openssl(
    cache_dir: str,
    build_dir: str,
    dep_sysroot: str,
    arch: str,
    env: dict[str, str],
) -> None:
    """Build and install OpenSSL into dep_sysroot."""
    print('Building OpenSSL...')
    url = f'https://www.openssl.org/source/openssl-{OPENSSL_VER}.tar.gz'
    tarball = _fetch(url, cache_dir)
    srcdir = _extract(tarball, build_dir)

    # Apply the getenv.c patch so SSL_CERT_FILE env var works on Android.
    _openssl_patch_getenv(srcdir)

    openssl_target = _OPENSSL_TARGETS[arch]

    # OpenSSL's Android support uses ANDROID_NDK_ROOT from the env.
    subprocess.run(
        [
            './Configure',
            openssl_target,
            f'--prefix={dep_sysroot}/usr',
            'no-shared',
            'no-tests',
        ],
        cwd=srcdir,
        env=env,
        check=True,
    )
    subprocess.run(['make', f'-j{_cpus()}'], cwd=srcdir, env=env, check=True)
    subprocess.run(['make', 'install_sw'], cwd=srcdir, env=env, check=True)


def _openssl_patch_getenv(srcdir: str) -> None:
    """Patch crypto/getenv.c to always allow getenv() on Android.

    We bundle our own SSL root certificates and use the SSL_CERT_FILE env var
    to get them used by default. OpenSSL is picky about allowing env vars on
    Android, so we force-allow them here.
    """
    fname = os.path.join(srcdir, 'crypto', 'getenv.c')
    with open(fname, encoding='utf-8') as fh:
        txt = fh.read()
    old = 'char *ossl_safe_getenv(const char *name)\n{\n'
    new = (
        'char *ossl_safe_getenv(const char *name)\n'
        '{\n'
        '    // ERICF TWEAK: ALWAYS ALLOW GETENV.\n'
        '    return getenv(name);\n'
    )
    if old not in txt:
        raise RuntimeError(
            'openssl getenv.c patch: expected string not found;'
            ' OpenSSL version may have changed.'
        )
    txt = txt.replace(old, new, 1)
    with open(fname, 'w', encoding='utf-8') as fh:
        fh.write(txt)


def _build_libffi(
    cache_dir: str,
    build_dir: str,
    dep_sysroot: str,
    arch: str,
    env: dict[str, str],
) -> None:
    """Build and install libffi into dep_sysroot."""
    print('Building libffi...')
    url = (
        f'https://github.com/libffi/libffi/releases/'
        f'download/v{LIBFFI_VER}/libffi-{LIBFFI_VER}.tar.gz'
    )
    tarball = _fetch(url, cache_dir)
    srcdir = _extract(tarball, build_dir)

    # Apply the trampc forward-declaration patch if needed.
    _libffi_patch_trampc(srcdir)

    target = ARCH_TARGETS[arch]
    subprocess.run(
        [
            './configure',
            f'--host={target}',
            f'--prefix={dep_sysroot}/usr',
            '--disable-shared',
            '--disable-builddir-relocation',
        ],
        cwd=srcdir,
        env=env,
        check=True,
    )
    subprocess.run(['make', f'-j{_cpus()}'], cwd=srcdir, env=env, check=True)
    subprocess.run(['make', 'install'], cwd=srcdir, env=env, check=True)


def _libffi_patch_trampc(srcdir: str) -> None:
    """Apply forward-declaration fix to libffi's src/tramp.c if needed.

    The Android NDK may be missing stdint.h includes required by tramp.c.
    """
    fname = os.path.join(srcdir, 'src', 'tramp.c')
    if not os.path.exists(fname):
        return  # Older libffi versions don't have tramp.c.
    with open(fname, encoding='utf-8') as fh:
        txt = fh.read()
    # Only patch if not already patched.
    if '#include <stdint.h>' in txt:
        return
    # Add stdint.h include after the first #include line.
    old = '#include <fficonfig.h>\n'
    if old not in txt:
        # Try alternate first include.
        old = '#include "ffi.h"\n'
    if old not in txt:
        # Nothing to patch; skip silently.
        return
    new = old + '#include <stdint.h>\n'
    txt = txt.replace(old, new, 1)
    with open(fname, 'w', encoding='utf-8') as fh:
        fh.write(txt)


def _build_sqlite(
    cache_dir: str,
    build_dir: str,
    dep_sysroot: str,
    arch: str,
    env: dict[str, str],
) -> None:
    """Build and install SQLite into dep_sysroot."""
    print('Building SQLite...')
    url = (
        f'https://sqlite.org/{SQLITE_VER[0]}/'
        f'sqlite-autoconf-{SQLITE_VER[1]}.tar.gz'
    )
    tarball = _fetch(url, cache_dir)
    srcdir = _extract(tarball, build_dir)

    target = ARCH_TARGETS[arch]
    subprocess.run(
        [
            './configure',
            f'--host={target}',
            f'--prefix={dep_sysroot}/usr',
            '--disable-shared',
        ],
        cwd=srcdir,
        env=env,
        check=True,
    )
    subprocess.run(['make', f'-j{_cpus()}'], cwd=srcdir, env=env, check=True)
    subprocess.run(['make', 'install'], cwd=srcdir, env=env, check=True)


def _build_xz(
    cache_dir: str,
    build_dir: str,
    dep_sysroot: str,
    arch: str,
    env: dict[str, str],
) -> None:
    """Build and install XZ (liblzma) into dep_sysroot."""
    print('Building XZ...')
    url = f'https://tukaani.org/xz/xz-{XZ_VER}.tar.xz'
    tarball = _fetch(url, cache_dir)
    srcdir = _extract(tarball, build_dir)

    target = ARCH_TARGETS[arch]
    subprocess.run(
        [
            './configure',
            f'--host={target}',
            '--build=x86_64-linux-gnu',
            f'--prefix={dep_sysroot}/usr',
            '--disable-shared',
            '--enable-static',
            '--disable-xz',
            '--disable-xzdec',
            '--disable-lzmainfo',
            '--disable-lzma-links',
            '--disable-scripts',
            '--disable-doc',
            # XZ 5.8.x added a check that rejects CFLAGS which trigger
            # warnings under -Werror (our Android CFLAGS do this).
            'SKIP_WERROR_CHECK=yes',
        ],
        cwd=srcdir,
        env=env,
        check=True,
    )
    subprocess.run(['make', f'-j{_cpus()}'], cwd=srcdir, env=env, check=True)
    subprocess.run(['make', 'install'], cwd=srcdir, env=env, check=True)


def _build_libuuid(
    cache_dir: str,
    build_dir: str,
    dep_sysroot: str,
    arch: str,
    env: dict[str, str],
) -> None:
    """Build and install libuuid (from util-linux) into dep_sysroot."""
    print('Building libuuid...')
    url = (
        f'https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/'
        f'v{LIBUUID_VER[0]}/util-linux-{LIBUUID_VER[1]}.tar.xz'
    )
    tarball = _fetch(url, cache_dir)
    srcdir = _extract(tarball, build_dir)

    target = ARCH_TARGETS[arch]
    configure_args = [
        './configure',
        f'--host={target}',
        f'--prefix={dep_sysroot}/usr',
        '--disable-all-programs',
        '--enable-libuuid',
    ]
    # 32-bit targets need --disable-year2038 with current NDK.
    if arch in {'arm', 'x86'}:
        configure_args.append('--disable-year2038')

    subprocess.run(configure_args, cwd=srcdir, env=env, check=True)
    subprocess.run(['make', f'-j{_cpus()}'], cwd=srcdir, env=env, check=True)
    subprocess.run(['make', 'install'], cwd=srcdir, env=env, check=True)


# ---------------------------------------------------------------------------
# Python source patch helpers
# ---------------------------------------------------------------------------


def _patch_grp_h(tc_bin: str) -> None:
    """Lower getgrent/setgrent/endgrent API requirement in NDK grp.h 26→23.

    These functions are guarded by __ANDROID_API__ >= 26 in the NDK headers,
    but we target API 24. This patch lowers the guard so they're accessible.
    """
    # tc_bin = {ndk}/toolchains/llvm/prebuilt/linux-x86_64/bin
    # sysroot lives one level up from bin, at .../linux-x86_64/sysroot
    ndk_sysroot = os.path.join(os.path.dirname(tc_bin), 'sysroot')
    fname = os.path.join(ndk_sysroot, 'usr', 'include', 'grp.h')
    if not os.path.exists(fname):
        print(f'WARNING: grp.h not found at {fname}; skipping patch.')
        return
    with open(fname, encoding='utf-8') as fh:
        txt = fh.read()
    # Patch the API guard from 26 to 23.
    old = '__ANDROID_API__ >= 26'
    if old not in txt:
        # Already patched or not present; skip.
        print('grp.h: patch not needed (already applied or target not found).')
        return
    new = '__ANDROID_API__ >= 23'
    txt = txt.replace(old, new)
    with open(fname, 'w', encoding='utf-8') as fh:
        fh.write(txt)
    print('Patched grp.h: lowered getgrent/setgrent/endgrent to API 23.')


def _patch_modules_setup(pydir: str) -> None:
    """Patch Modules/Setup.stdlib.in to build our desired module set."""
    from efrotools.pybuild import patch_modules_setup

    patch_modules_setup(pydir, 'android')


def _patch_fileutils_h(pydir: str) -> None:
    """Add Py_BallisticaLowLevelDebugLog hook to Include/fileutils.h."""
    from efrotools.util import readfile, replace_exact, writefile

    fname = os.path.join(pydir, 'Include', 'fileutils.h')
    txt = readfile(fname)
    txt = replace_exact(
        txt,
        '\n#ifdef __cplusplus\n}\n',
        (
            '\n'
            '/* ericf hack for debugging */\n'
            '#define PY_HAVE_BALLISTICA_LOW_LEVEL_DEBUG_LOG\n'
            'extern void (*Py_BallisticaLowLevelDebugLog)(const char* msg);\n'
            '\n'
            '#ifdef __cplusplus\n}\n'
        ),
    )
    writefile(fname, txt)

    fname2 = os.path.join(pydir, 'Python', 'fileutils.c')
    txt2 = readfile(fname2)
    txt2 = replace_exact(
        txt2,
        '    _Py_END_SUPPRESS_IPH\n}',
        '    _Py_END_SUPPRESS_IPH\n}\n\n'
        'void (*Py_BallisticaLowLevelDebugLog)(const char* msg) = NULL;\n',
    )
    writefile(fname2, txt2)


def _patch_fileutils_c(pydir: str) -> None:
    """Fix readlink() cast in Python/fileutils.c for Android.

    Android's readlink() may return an incorrect ssize_t on some targets;
    casting to int fixes the error-value (-1) comparison.
    """
    from efrotools.util import readfile, replace_exact, writefile

    fname = os.path.join(pydir, 'Python', 'fileutils.c')
    txt = readfile(fname)
    txt = replace_exact(
        txt,
        '    res = readlink(cpath, cbuf, cbuf_len);\n',
        '    res = (int)readlink(cpath, cbuf, cbuf_len);\n',
    )
    writefile(fname, txt)


def _patch_ctypes(pydir: str) -> None:
    """Disable Android-specific .so loading path in ctypes.

    ctypes is hard-coded to load Python from a .so on Android, but we
    statically compile Python into our main.so. The default fallback
    handles our case correctly.
    """
    from efrotools.util import readfile, replace_exact, writefile

    fname = os.path.join(pydir, 'Lib', 'ctypes', '__init__.py')
    txt = readfile(fname)
    # In 3.13.12+ this condition covers both android and cygwin; strip
    # android from the list since we link Python statically.
    txt = replace_exact(
        txt,
        'elif _sys.platform in ["android", "cygwin"]:\n',
        'elif _sys.platform in ["cygwin"]:  # efro: android uses static lib\n',
    )
    writefile(fname, txt)


# ---------------------------------------------------------------------------
# Python configure + build
# ---------------------------------------------------------------------------


def _configure_python(
    pydir: str,
    arch: str,
    api: int,
    dep_sysroot: str,
    env: dict[str, str],
    debug: bool,
    build_python: str,
) -> None:
    """Run Python's configure for Android cross-compilation."""
    # pylint: disable=too-many-positional-arguments
    target = ARCH_TARGETS[arch]
    versioned_host = f'{target}{api}'

    configure_cmd = [
        './configure',
        f'--host={versioned_host}',
        '--build=x86_64-linux-gnu',
        '--prefix=/usr',
        '--without-ensurepip',
        '--enable-option-checking=fatal',
        f'--with-openssl={dep_sysroot}/usr',
        f'--with-build-python={build_python}',
    ]
    if debug:
        configure_cmd.append('--with-pydebug')

    # Python 3.13 detects sqlite3 via PKG_CHECK_MODULES([LIBSQLITE3]).
    # Our .pc files have absolute paths so PKG_CONFIG_SYSROOT_DIR doesn't
    # help here. Pass the flags directly so configure skips pkg-config.
    dep_inc = f'{dep_sysroot}/usr/include'
    dep_lib = f'{dep_sysroot}/usr/lib'
    env = dict(env)
    env['LIBSQLITE3_CFLAGS'] = f'-I{dep_inc}'
    # -lm needed because libsqlite3.a uses log/pow/exp/etc from libm.
    env['LIBSQLITE3_LIBS'] = f'-L{dep_lib} -lsqlite3 -lm'

    subprocess.run(configure_cmd, cwd=pydir, env=env, check=True)


# ---------------------------------------------------------------------------
# Post-build checks
# ---------------------------------------------------------------------------


def _check_no_shared_modules(installdir: str, arch: str) -> None:
    """Fail if any .so extension modules appear in lib-dynload after install.

    All extension modules must be statically linked into libpython.  A file
    in lib-dynload means a module was not compiled statically and will be
    missing at runtime (since we don't ship lib-dynload in the APK).
    If this fires, update the cmodules/enables sets in
    pybuild.patch_modules_setup().
    """
    dynload_dir = os.path.join(
        installdir, 'usr', 'lib', f'python{PY_VER}', 'lib-dynload'
    )
    if not os.path.isdir(dynload_dir):
        return
    so_files = glob.glob(os.path.join(dynload_dir, '*.so'))
    if so_files:
        names = '\n'.join(f'  {os.path.basename(f)}' for f in sorted(so_files))
        raise RuntimeError(
            f'Android/{arch}: shared extension modules found in lib-dynload'
            f' (all must be static):\n{names}\n'
            f'Update cmodules/enables in pybuild.patch_modules_setup().'
        )
    print(f'  Static-module check passed for Android/{arch}.')


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def build(rootdir: str, arch: str, debug: bool) -> None:
    """Build Python for the given Android architecture.

    arch must be one of: arm, arm64, x86, x86_64.
    Outputs are written to::

      build/python_android_{arch}[_debug]/build/usr/   (installed Python)
      build/python_android_{arch}[_debug]/src/Python-{PY_VER_EXACT}/
        Include/          (Python headers)
        Lib/              (Python stdlib)
        Android/sysroot/  (dep .a files)
    """
    # pylint: disable=too-many-locals
    if arch not in ARCH_TARGETS:
        raise ValueError(
            f'Invalid arch {arch!r}; must be one of {list(ARCH_TARGETS)}'
        )

    suffix = '_debug' if debug else ''
    buildroot = os.path.join(rootdir, f'build/python_android_{arch}{suffix}')
    srcdir = os.path.join(buildroot, 'src')
    pydir = os.path.join(srcdir, f'Python-{PY_VER_EXACT}')
    dep_sysroot = os.path.join(pydir, 'Android', 'sysroot')
    installdir = os.path.join(buildroot, 'build')

    # Shared dep tarball cache (reused across all arch builds).
    cache_dir = os.path.join(rootdir, 'build', 'python_deps_cache')

    # Per-build dep extraction dir (fresh each build).
    deps_build_dir = os.path.join(buildroot, 'deps')

    print(f'=== Building Python {PY_VER_EXACT} for Android/{arch} ===')
    print(f'    buildroot: {buildroot}')
    print(f'    debug: {debug}')

    # Start fresh.
    subprocess.run(['rm', '-rf', buildroot], check=True)
    os.makedirs(srcdir, exist_ok=True)
    os.makedirs(dep_sysroot, exist_ok=True)
    os.makedirs(deps_build_dir, exist_ok=True)

    # Get NDK paths and build environment.
    ndk_path = _get_ndk_path(rootdir)
    tc_bin = _get_toolchain_bin(ndk_path)
    env = _build_env(arch, ANDROID_API_VER, ndk_path, tc_bin, dep_sysroot)

    # 1. Download + extract Python source.
    print('Fetching Python source...')
    py_url = (
        f'https://www.python.org/ftp/python/{PY_VER_EXACT}/'
        f'Python-{PY_VER_EXACT}.tar.xz'
    )
    py_tarball = _fetch(py_url, cache_dir)
    _extract(py_tarball, srcdir)
    assert os.path.isdir(pydir), f'Python source not found at {pydir}'

    # 2. Build dependencies into dep_sysroot.
    _build_zlib(cache_dir, deps_build_dir, dep_sysroot, arch, env)
    _build_bzip2(cache_dir, deps_build_dir, dep_sysroot, env)
    _build_openssl(cache_dir, deps_build_dir, dep_sysroot, arch, env)
    _build_libffi(cache_dir, deps_build_dir, dep_sysroot, arch, env)
    _build_sqlite(cache_dir, deps_build_dir, dep_sysroot, arch, env)
    _build_xz(cache_dir, deps_build_dir, dep_sysroot, arch, env)
    _build_libuuid(cache_dir, deps_build_dir, dep_sysroot, arch, env)

    # 3. Patch NDK headers and Python source.
    _patch_grp_h(tc_bin)
    _patch_modules_setup(pydir)
    _patch_fileutils_h(pydir)
    _patch_fileutils_c(pydir)
    _patch_ctypes(pydir)

    # 4. Configure Python.
    py_short = PY_VER.replace('.', '')
    build_python = f'/home/ubuntu/.py{py_short}/bin/python{PY_VER}'
    _configure_python(
        pydir, arch, ANDROID_API_VER, dep_sysroot, env, debug, build_python
    )

    # 5. Build Python.
    print('Building Python...')
    subprocess.run(['make', f'-j{_cpus()}'], cwd=pydir, env=env, check=True)

    # 6. Install Python.
    print('Installing Python...')
    subprocess.run(
        ['make', 'install', f'DESTDIR={installdir}'],
        cwd=pydir,
        env=env,
        check=True,
    )

    # 7. Verify no shared extension modules slipped through.
    print('Checking for shared extension modules...')
    _check_no_shared_modules(installdir, arch)

    print(f'=== Python {PY_VER_EXACT} for Android/{arch} build complete! ===')
    print(f'    Output: {installdir}')


def gather(rootdir: str) -> None:
    """Gather Android Python build artifacts into the project.

    Reads from build/python_android_{arch}/ and writes to
    src/external/python-android[-debug]/ and
    src/assets/pylib-android/.

    Assumes all 4 arch builds (arm, arm64, x86, x86_64) have been run
    for both debug and release.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    from efrotools.pybuild import PRUNE_LIB_NAMES, tweak_empty_py_files

    # Arch name -> output lib dir name (matching Android ABI conventions).
    arch_libinst: dict[str, str] = {
        'arm': 'android_armeabi-v7a',
        'arm64': 'android_arm64-v8a',
        'x86': 'android_x86',
        'x86_64': 'android_x86_64',
    }

    # Arch name -> sysconfigdata suffix (platform tag in filename).
    arch_sysconfig_suffix: dict[str, str] = {
        'arm': 'android_arm-linux-androideabi',
        'arm64': 'android_aarch64-linux-android',
        'x86': 'android_i686-linux-android',
        'x86_64': 'android_x86_64-linux-android',
    }

    # Arch name -> pyconfig.h name suffix (matches CompileArch enum values
    # in pybuild.gather()).
    arch_compile_arch: dict[str, str] = {
        'arm': 'android_arm',
        'arm64': 'android_arm64',
        'x86': 'android_x86',
        'x86_64': 'android_x86_64',
    }

    archs = ('arm', 'arm64', 'x86', 'x86_64')

    os.chdir(rootdir)

    # Clear out any existing output.
    subprocess.run(
        [
            'rm',
            '-rf',
            'src/external/python-android',
            'src/external/python-android-debug',
            'src/assets/pylib-android',
        ],
        check=True,
    )

    apost2 = f'src/Python-{PY_VER_EXACT}/Android/sysroot'

    for buildtype in ['release', 'debug']:
        debug = buildtype == 'debug'
        debug_d = 'd' if debug else ''
        bsuffix = '_debug' if debug else ''
        bsuffix2 = '-debug' if debug else ''
        alibname = 'python' + PY_VER + debug_d

        src_dst = f'src/external/python-android{bsuffix2}'
        include_dst = os.path.join(src_dst, 'include')
        lib_dst = os.path.join(src_dst, 'lib')
        pylib_dst = 'src/assets/pylib-android'

        assert not os.path.exists(src_dst)
        subprocess.run(['mkdir', '-p', src_dst], check=True)
        subprocess.run(['mkdir', '-p', lib_dst], check=True)

        # Where each arch's build output lives.
        bases: dict[str, str] = {
            arch: f'build/python_android_{arch}{bsuffix}/build'
            for arch in archs
        }
        bases2: dict[str, str] = {
            arch: f'build/python_android_{arch}{bsuffix}/{apost2}'
            for arch in archs
        }

        # Base headers and pylib come from the release arm build (same for
        # all archs; we sanity-check that below).
        baseheaders = [
            f'build/python_android_{arch}/src/' f'Python-{PY_VER_EXACT}/Include'
            for arch in archs
        ]
        basepylib = [
            f'build/python_android_{arch}/src/' f'Python-{PY_VER_EXACT}/Lib'
            for arch in archs
        ]

        # Sanity check: all arch Include dirs should be identical.
        for i in range(len(baseheaders) - 1):
            returncode = subprocess.run(
                ['diff', baseheaders[i], baseheaders[i + 1]],
                check=False,
                capture_output=True,
            ).returncode
            if returncode != 0:
                raise RuntimeError(
                    f'Sanity check failed: Include dirs differ:\n'
                    f'{baseheaders[i]}\n'
                    f'{baseheaders[i + 1]}'
                )

        # Copy in the base Include dir.
        subprocess.run(
            ['cp', '-r', baseheaders[0], include_dst],
            check=True,
        )

        # Write the unified pyconfig.h that routes to per-arch headers.
        unified_pyconfig = (
            f'#if BA_XCODE_BUILD\n'
            f'// Necessary to get the TARGET_OS_SIMULATOR define.\n'
            f'#include <TargetConditionals.h>\n'
            f'#endif\n'
            f'\n'
            f'#if BA_PLATFORM_MACOS and defined(__aarch64__)\n'
            f'#include "pyconfig_mac_arm64.h"\n'
            f'\n'
            f'#elif BA_PLATFORM_MACOS and defined(__x86_64__)\n'
            f'#include "pyconfig_mac_x86_64.h"\n'
            f'\n'
            f'#elif BA_PLATFORM_IOS and defined(__aarch64__)\n'
            f'#if TARGET_OS_SIMULATOR\n'
            f'#include "pyconfig_ios_simulator_arm64.h"\n'
            f'#else\n'
            f'#include "pyconfig_ios_arm64.h"\n'
            f'#endif  // TARGET_OS_SIMULATOR\n'
            f'\n'
            f'#elif BA_PLATFORM_IOS and defined(__x86_64__)\n'
            f'#if TARGET_OS_SIMULATOR\n'
            f'#error x86 simulator no longer supported here.\n'
            f'#else\n'
            f'#error this platform combo should not be possible\n'
            f'#endif  // TARGET_OS_SIMULATOR\n'
            f'\n'
            f'#elif BA_PLATFORM_TVOS and defined(__aarch64__)\n'
            f'#if TARGET_OS_SIMULATOR\n'
            f'#include "pyconfig_tvos_simulator_arm64.h"\n'
            f'#else\n'
            f'#include "pyconfig_tvos_arm64.h"\n'
            f'#endif  // TARGET_OS_SIMULATOR\n'
            f'\n'
            f'#elif BA_PLATFORM_TVOS and defined(__x86_64__)\n'
            f'#if TARGET_OS_SIMULATOR\n'
            f'#error x86 simulator no longer supported here.\n'
            f'#else\n'
            f'#error this platform combo should not be possible\n'
            f'#endif  // TARGET_OS_SIMULATOR\n'
            f'\n'
            f'#elif BA_PLATFORM_ANDROID and defined(__arm__)\n'
            f'#include "pyconfig_{arch_compile_arch['arm']}.h"\n'
            f'\n'
            f'#elif BA_PLATFORM_ANDROID and defined(__aarch64__)\n'
            f'#include "pyconfig_{arch_compile_arch['arm64']}.h"\n'
            f'\n'
            f'#elif BA_PLATFORM_ANDROID and defined(__i386__)\n'
            f'#include "pyconfig_{arch_compile_arch['x86']}.h"\n'
            f'\n'
            f'#elif BA_PLATFORM_ANDROID and defined(__x86_64__)\n'
            f'#include "pyconfig_{arch_compile_arch['x86_64']}.h"\n'
            f'\n'
            f'#else\n'
            f'#error unknown platform\n'
            f'\n'
            f'#endif\n'
        )
        with open(f'{include_dst}/pyconfig.h', 'w', encoding='utf-8') as hfile:
            hfile.write(unified_pyconfig)

        # Assemble pylib only once (same content for debug and release).
        if not os.path.exists(pylib_dst):
            # Sanity check: all arch Lib dirs should be identical.
            for i in range(len(basepylib) - 1):
                returncode = subprocess.run(
                    ['diff', basepylib[i], basepylib[i + 1]],
                    check=False,
                    capture_output=True,
                ).returncode
                if returncode != 0:
                    raise RuntimeError(
                        f'Sanity check failed: Lib dirs differ:\n'
                        f'{basepylib[i]}\n'
                        f'{basepylib[i + 1]}'
                    )
            subprocess.run(['mkdir', '-p', pylib_dst], check=True)
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
                    f'{basepylib[0]}/',
                    pylib_dst,
                ],
                check=True,
            )
            tweak_empty_py_files(pylib_dst)
            # Prune modules we don't need (allows shell expansion).
            subprocess.run(
                'cd "' + pylib_dst + '" && rm -rf ' + ' '.join(PRUNE_LIB_NAMES),
                shell=True,
                check=True,
            )

        # For each arch, gather its pyconfig.h, sysconfigdata, and libs.
        for arch in archs:
            # Copy per-arch pyconfig.h with a unique name.
            src_cfg = f'{bases[arch]}/usr/include/{alibname}/pyconfig.h'
            dst_cfg = f'{include_dst}/pyconfig_{arch_compile_arch[arch]}.h'
            assert not os.path.exists(dst_cfg), f'exists: {dst_cfg}'
            subprocess.run(['cp', src_cfg, dst_cfg], check=True)
            assert os.path.exists(dst_cfg)

            # Copy _sysconfigdata script.
            sysconfig_src = (
                f'{bases[arch]}/usr/lib/python{PY_VER}/'
                f'_sysconfigdata_{debug_d}_{arch_sysconfig_suffix[arch]}.py'
            )
            sysconfig_dst = os.path.join(
                pylib_dst, os.path.basename(sysconfig_src)
            )
            assert not os.path.exists(sysconfig_dst)
            subprocess.run(['cp', sysconfig_src, pylib_dst], check=True)

            # Gather libs for this arch.
            libinst = arch_libinst[arch]
            targetdir = f'{lib_dst}/{libinst}'
            subprocess.run(['mkdir', '-p', targetdir], check=True)
            libs = [
                f'{bases[arch]}/usr/lib/lib{alibname}.a',
                f'{bases2[arch]}/usr/lib/libssl.a',
                f'{bases2[arch]}/usr/lib/libcrypto.a',
                f'{bases2[arch]}/usr/lib/liblzma.a',
                f'{bases2[arch]}/usr/lib/libsqlite3.a',
                f'{bases2[arch]}/usr/lib/libffi.a',
                f'{bases2[arch]}/usr/lib/libbz2.a',
                f'{bases2[arch]}/usr/lib/libuuid.a',
            ]
            for lib in libs:
                finalpath = os.path.join(targetdir, os.path.basename(lib))
                assert not os.path.exists(finalpath), f'exists: {finalpath}'
                subprocess.run(['cp', lib, targetdir], check=True)
                assert os.path.exists(finalpath)

    print('gather: done.')
