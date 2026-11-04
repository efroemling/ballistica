# Released under the MIT License. See LICENSE for details.
#
"""Bundled-dependency builds for 'linux-portable' builds.

Portable Linux builds (Steam, the downloads page) can't rely on the
host's libraries, so we build our own Python (with all extension
modules static, as on Android), OpenSSL, OpenAL Soft and friends inside
Valve's Steam Runtime SDK container and link them in. See
``docs/initiatives/linux-portable-builds.md``.

Runs on a docker-equipped Linux build host of the target arch. This
module itself runs on the host (in our regular venv); every compile
step runs via ``docker exec`` in one long-lived SDK container that has
the project root mounted at the same path, so paths mean the same thing
on both sides.

Each arch build ends by assembling a tidy ``out/`` dir; :func:`gather`
copies those into the project.
"""

import os
import re
import glob
import shutil
import hashlib
import subprocess
import urllib.request

# Dep + Python versions are shared with the Android build so the two
# get bumped in lockstep (same patch sets, same module list).
from efrotools.python_build_android import (
    PY_VER,
    PY_VER_EXACT,
    OPENSSL_VER,
    ZLIB_VER,
    XZ_VER,
    ZSTD_VER,
    BZIP2_VER,
    LIBFFI_VER,
    LIBUUID_VER,
    SQLITE_VER,
)
from efrotools.openalbuildapple import OPENAL_SOFT_TAG

ARCHS = ('x86_64', 'arm64')

# Steam Runtime SDK image per arch, pinned so builds don't drift; bump
# deliberately. x86_64 uses Steam Linux Runtime 3.0 'sniper' (glibc
# 2.31; what the Deck and most of Steam run). arm64 only exists in
# Steam Linux Runtime 4.0 (Debian 13 base).
SDK_IMAGES: dict[str, str] = {
    'x86_64': 'registry.gitlab.steamos.cloud/steamrt/sniper/sdk:'
    '3.0.20261021.266025',
    'arm64': 'registry.gitlab.steamos.cloud/steamrt/steamrt4/sdk/arm64:'
    '4.0.20261021.265997',
}

# Sniper's cmake (3.25) is too old for OpenAL Soft 1.25 (needs 3.26+),
# so we use Kitware's prebuilt (runs on glibc 2.17+) for every arch.
CMAKE_VER = '3.31.6'

# SDL3 we build to ship beside the binary in downloads-page packages
# (Steam builds use the runtime's). Built with upstream's defaults, which
# dlopen X11/Wayland/audio backends at runtime -- unlike the runtime's
# own SDL3, which links ~20 desktop libs directly, any one of which
# missing on a distro would keep the game from starting. Keep it >= the
# SDK's SDL3 (whose headers we compile against; 3.4.18 in the pinned
# sniper SDK).
SDL3_VER = '3.4.18'

# Host 'uname -m' value per arch (also Kitware's cmake tarball arch).
UNAME_ARCHS: dict[str, str] = {'x86_64': 'x86_64', 'arm64': 'aarch64'}

# OpenSSL ./Configure target per arch.
_OPENSSL_TARGETS: dict[str, str] = {
    'x86_64': 'linux-x86_64',
    'arm64': 'linux-aarch64',
}

# Both SDKs ship GCC 14 under these names (their default gcc is older in
# sniper's case). We link libstdc++/libgcc statically in the final app.
SDK_CC = 'gcc-14'
SDK_CXX = 'g++-14'

# Static libs every portable link needs, in out/lib.
_OUT_LIBS = (
    'libssl.a',
    'libcrypto.a',
    'libffi.a',
    'libsqlite3.a',
    'liblzma.a',
    'libbz2.a',
    'libz.a',
    'libuuid.a',
    'libzstd.a',
    'libopenal.a',
)


def build_root(rootdir: str, arch: str, debug: bool) -> str:
    """Return the build dir for one arch/flavor."""
    suffix = '_debug' if debug else ''
    return os.path.join(rootdir, f'build/linux_portable_deps/{arch}{suffix}')


class SdkContainer:
    """A long-lived SDK container we run build steps in.

    The container name gets a hash of ``rootdir`` appended. Container
    names are host-wide, and we ``docker rm -f`` the name on entry, so
    without it two checkouts building on one host at once (CI jobs for
    different repos/branches) kill each other's builds.
    """

    def __init__(
        self,
        image: str,
        rootdir: str,
        name: str,
        extra_run_args: list[str] | None = None,
    ) -> None:
        self._image = image
        self._rootdir = rootdir
        roothash = hashlib.sha256(
            os.path.abspath(rootdir).encode()
        ).hexdigest()[:10]
        self._name = f'{name}-{roothash}'
        self._extra_run_args = extra_run_args or []

    def __enter__(self) -> 'SdkContainer':
        # Our images are pinned tags (immutable), so only pull when
        # missing; a registry round trip on every build adds up.
        if (
            subprocess.run(
                ['docker', 'image', 'inspect', self._image],
                check=False,
                capture_output=True,
            ).returncode
            != 0
        ):
            subprocess.run(
                ['docker', 'pull', '--quiet', self._image], check=True
            )
        # Clear out any leftover from an interrupted earlier run.
        subprocess.run(
            ['docker', 'rm', '-f', self._name],
            check=False,
            capture_output=True,
        )
        subprocess.run(
            [
                'docker',
                'run',
                '--detach',
                '--rm',
                '--name',
                self._name,
                '--user',
                f'{os.getuid()}:{os.getgid()}',
                '--env',
                'HOME=/tmp',
                '--volume',
                f'{self._rootdir}:{self._rootdir}',
                *self._extra_run_args,
                self._image,
                'sleep',
                'infinity',
            ],
            check=True,
        )
        return self

    def __exit__(self, *args: object) -> None:
        subprocess.run(
            ['docker', 'rm', '-f', self._name],
            check=False,
            capture_output=True,
        )

    def run(
        self, cmd: list[str], cwd: str, env: dict[str, str] | None = None
    ) -> None:
        """Run a command in the container (raises on failure)."""
        envargs: list[str] = []
        for key, val in (env or {}).items():
            envargs += ['--env', f'{key}={val}']
        subprocess.run(
            ['docker', 'exec', '--workdir', cwd, *envargs, self._name, *cmd],
            check=True,
        )

    def output(
        self, cmd: list[str], cwd: str, stderr_to_stdout: bool = False
    ) -> str:
        """Run a command in the container and return its stdout."""
        result = subprocess.run(
            ['docker', 'exec', '--workdir', cwd, self._name, *cmd],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT if stderr_to_stdout else subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f'Command failed in container ({result.returncode}):'
                f' {cmd}\n{result.stdout}{result.stderr or ''}'
            )
        return result.stdout


def cpus() -> int:
    """Return the number of parallel jobs to build with."""
    return os.cpu_count() or 8


def _fetch(url: str, cache_dir: str) -> str:
    """Download url into cache_dir (if not already there); return path."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, os.path.basename(url))
    if not os.path.exists(path):
        print(f'Fetching {url}...', flush=True)
        tmppath = f'{path}.tmp'
        with urllib.request.urlopen(url, timeout=120) as response:
            with open(tmppath, 'wb') as outfile:
                shutil.copyfileobj(response, outfile)
        os.rename(tmppath, path)
    return path


def _extract(tarball: str, destdir: str) -> str:
    """Extract a tarball into destdir; return its single top-level dir."""
    before = set(os.listdir(destdir))
    subprocess.run(['tar', '-xf', tarball, '-C', destdir], check=True)
    new = set(os.listdir(destdir)) - before
    if len(new) != 1:
        raise RuntimeError(f'Expected one top-level dir from {tarball}.')
    return os.path.join(destdir, new.pop())


class _Builder:
    """Builds everything for one arch/flavor."""

    def __init__(self, rootdir: str, arch: str, debug: bool) -> None:
        if arch not in ARCHS:
            raise ValueError(f'Invalid arch {arch!r}; expected {ARCHS}.')
        host_arch = os.uname().machine
        if host_arch != UNAME_ARCHS[arch]:
            raise RuntimeError(
                f'Building {arch} requires a {UNAME_ARCHS[arch]} host'
                f' (this is {host_arch}).'
            )
        self.rootdir = rootdir
        self.arch = arch
        self.debug = debug
        self.buildroot = build_root(rootdir, arch, debug)
        self.srcdir = os.path.join(self.buildroot, 'src')
        self.pydir = os.path.join(self.srcdir, f'Python-{PY_VER_EXACT}')
        self.sysroot = os.path.join(self.buildroot, 'sysroot', 'usr')
        self.installdir = os.path.join(self.buildroot, 'install')
        self.outdir = os.path.join(self.buildroot, 'out')
        self.cmake = 'cmake'  # Replaced by _fetch_cmake().
        # Kept out of the sysroot so nothing else's configure finds it.
        self.sdl3_install = os.path.join(self.buildroot, 'sdl3')
        # Shared with the Android build; just a tarball cache.
        self.cache_dir = os.path.join(rootdir, 'build', 'python_deps_cache')
        cflags = '-fPIC -O2'
        self.env: dict[str, str] = {
            'CC': SDK_CC,
            'CXX': SDK_CXX,
            'CFLAGS': cflags,
            'CXXFLAGS': cflags,
            'CPPFLAGS': f'-I{self.sysroot}/include',
            'LDFLAGS': f'-L{self.sysroot}/lib',
            # Only ever see our own deps' .pc files; never the SDK's.
            'PKG_CONFIG_LIBDIR': f'{self.sysroot}/lib/pkgconfig',
            'LANG': 'C.UTF-8',
            'LC_ALL': 'C.UTF-8',
        }
        suffix = '-debug' if debug else ''
        self.container = SdkContainer(
            SDK_IMAGES[arch], rootdir, f'ba-linux-portable-deps-{arch}{suffix}'
        )

    def run(self) -> None:
        """Do the thing."""
        print(
            f'=== Building linux-portable deps for {self.arch}'
            f' (debug={self.debug}) in {SDK_IMAGES[self.arch]} ===',
            flush=True,
        )
        subprocess.run(['rm', '-rf', self.buildroot], check=True)
        for path in (self.srcdir, self.sysroot, self.installdir):
            os.makedirs(path)

        with self.container:
            self._fetch_cmake()
            self._fetch_python()
            self._build_zlib()
            self._build_bzip2()
            self._build_openssl()
            self._build_libffi()
            self._build_sqlite()
            self._build_xz()
            self._build_zstd()
            self._build_libuuid()
            self._build_openal()
            self._build_sdl3()
            self._patch_python()
            self._build_python()
            self._check_python()
            self._assemble_out()
        self._remove_intermediates()
        print(
            f'=== linux-portable deps for {self.arch} complete;'
            f' output in {self.outdir} ===',
            flush=True,
        )

    def _remove_intermediates(self) -> None:
        """Drop everything in the build root except ``out/``.

        Source and build trees run ~5 GB per arch+flavor, and build
        hosts carry one copy per workspace. A failed build never gets
        here, so its trees stay around for debugging.
        """
        for name in os.listdir(self.buildroot):
            if name != 'out':
                subprocess.run(
                    ['rm', '-rf', os.path.join(self.buildroot, name)],
                    check=True,
                )

    # -- Deps ---------------------------------------------------------------

    def _src(self, url: str) -> str:
        depsdir = os.path.join(self.buildroot, 'deps')
        os.makedirs(depsdir, exist_ok=True)
        return _extract(_fetch(url, self.cache_dir), depsdir)

    def _configure_make_install(
        self, srcdir: str, args: list[str], install: str = 'install'
    ) -> None:
        crun = self.container.run
        crun(args, cwd=srcdir, env=self.env)
        crun(['make', f'-j{cpus()}'], cwd=srcdir, env=self.env)
        crun(['make', install], cwd=srcdir, env=self.env)

    def _build_zlib(self) -> None:
        print('Building zlib...', flush=True)
        srcdir = self._src(f'https://www.zlib.net/zlib-{ZLIB_VER}.tar.gz')
        self._configure_make_install(
            srcdir, ['./configure', f'--prefix={self.sysroot}', '--static']
        )

    def _build_bzip2(self) -> None:
        print('Building bzip2...', flush=True)
        srcdir = self._src(
            f'https://sourceware.org/pub/bzip2/bzip2-{BZIP2_VER}.tar.gz'
        )
        # Plain Makefile, no configure; build just the static lib.
        self.container.run(
            [
                'make',
                f'-j{cpus()}',
                'libbz2.a',
                f'CC={SDK_CC}',
                f'CFLAGS={self.env['CFLAGS']} -Wall -Winline'
                ' -D_FILE_OFFSET_BITS=64',
            ],
            cwd=srcdir,
        )
        os.makedirs(f'{self.sysroot}/include', exist_ok=True)
        os.makedirs(f'{self.sysroot}/lib', exist_ok=True)
        shutil.copy(f'{srcdir}/bzlib.h', f'{self.sysroot}/include/')
        shutil.copy(f'{srcdir}/libbz2.a', f'{self.sysroot}/lib/')

    def _build_openssl(self) -> None:
        print('Building OpenSSL...', flush=True)
        srcdir = self._src(
            f'https://www.openssl.org/source/openssl-{OPENSSL_VER}.tar.gz'
        )
        # No getenv patch here (Android needs one); we pass our bundled
        # certifi store explicitly (see docs/design/client-ssl-trust.md).
        self._configure_make_install(
            srcdir,
            [
                './Configure',
                _OPENSSL_TARGETS[self.arch],
                f'--prefix={self.sysroot}',
                '--libdir=lib',
                # Never read the build container's config at runtime.
                '--openssldir=/etc/ssl',
                'no-shared',
                'no-tests',
                # No runtime loading of engines/providers (we never do),
                # so static consumers need no libdl.
                'no-dso',
                # Never read the system's openssl.cnf: distros' configs
                # target their own OpenSSL (Fedora's crypto-policies one
                # makes our 3.0 fail every SSL context with "unknown
                # error"), and we bring our own certs anyway.
                'no-autoload-config',
            ],
            install='install_sw',
        )

    def _build_libffi(self) -> None:
        print('Building libffi...', flush=True)
        srcdir = self._src(
            f'https://github.com/libffi/libffi/releases/'
            f'download/v{LIBFFI_VER}/libffi-{LIBFFI_VER}.tar.gz'
        )
        self._configure_make_install(
            srcdir,
            [
                './configure',
                f'--prefix={self.sysroot}',
                '--libdir',
                f'{self.sysroot}/lib',
                '--disable-shared',
                '--disable-docs',
            ],
        )

    def _build_sqlite(self) -> None:
        print('Building SQLite...', flush=True)
        srcdir = self._src(
            f'https://sqlite.org/{SQLITE_VER[0]}/'
            f'sqlite-autoconf-{SQLITE_VER[1]}.tar.gz'
        )
        self._configure_make_install(
            srcdir,
            ['./configure', f'--prefix={self.sysroot}', '--disable-shared'],
        )

    def _build_xz(self) -> None:
        print('Building XZ...', flush=True)
        srcdir = self._src(
            f'https://github.com/tukaani-project/xz/releases/download/'
            f'v{XZ_VER}/xz-{XZ_VER}.tar.xz'
        )
        self._configure_make_install(
            srcdir,
            [
                './configure',
                f'--prefix={self.sysroot}',
                '--disable-shared',
                '--enable-static',
                '--disable-xz',
                '--disable-xzdec',
                '--disable-lzmadec',
                '--disable-lzmainfo',
                '--disable-lzma-links',
                '--disable-scripts',
                '--disable-doc',
                '--disable-nls',
            ],
        )

    def _build_zstd(self) -> None:
        print('Building zstd...', flush=True)
        srcdir = self._src(
            f'https://github.com/facebook/zstd/releases/'
            f'download/v{ZSTD_VER}/zstd-{ZSTD_VER}.tar.gz'
        )
        # Plain Makefile; just the static lib and its public headers.
        # Backs both Python's _zstd module and the engine's packet codec.
        self.container.run(
            [
                'make',
                f'-j{cpus()}',
                '-C',
                'lib',
                'libzstd.a',
                f'CC={SDK_CC}',
                f'CFLAGS={self.env['CFLAGS']}',
            ],
            cwd=srcdir,
        )
        for hdr in ('zstd.h', 'zdict.h', 'zstd_errors.h'):
            shutil.copy(f'{srcdir}/lib/{hdr}', f'{self.sysroot}/include/')
        shutil.copy(f'{srcdir}/lib/libzstd.a', f'{self.sysroot}/lib/')

    def _build_libuuid(self) -> None:
        print('Building libuuid...', flush=True)
        srcdir = self._src(
            f'https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/'
            f'v{LIBUUID_VER[0]}/util-linux-{LIBUUID_VER[1]}.tar.xz'
        )
        self._configure_make_install(
            srcdir,
            [
                './configure',
                f'--prefix={self.sysroot}',
                '--disable-all-programs',
                '--enable-libuuid',
                '--disable-shared',
                '--disable-nls',
                '--without-systemd',
                '--without-python',
            ],
        )

    def _fetch_cmake(self) -> None:
        print(f'Fetching CMake {CMAKE_VER}...', flush=True)
        uarch = UNAME_ARCHS[self.arch]
        srcdir = self._src(
            f'https://github.com/Kitware/CMake/releases/download/'
            f'v{CMAKE_VER}/cmake-{CMAKE_VER}-linux-{uarch}.tar.gz'
        )
        self.cmake = os.path.join(srcdir, 'bin', 'cmake')
        assert os.path.isfile(self.cmake)

    def _build_openal(self) -> None:
        print('Building OpenAL Soft...', flush=True)
        srcdir = self._src(
            f'https://github.com/kcat/openal-soft/archive/refs/tags/'
            f'{OPENAL_SOFT_TAG}.tar.gz'
        )
        cmakebuild = os.path.join(srcdir, 'build-portable')
        os.makedirs(cmakebuild)
        mode = 'Debug' if self.debug else 'RelWithDebInfo'
        crun = self.container.run
        crun(
            [
                self.cmake,
                '..',
                f'-DCMAKE_BUILD_TYPE={mode}',
                f'-DCMAKE_C_COMPILER={SDK_CC}',
                f'-DCMAKE_CXX_COMPILER={SDK_CXX}',
                f'-DCMAKE_INSTALL_PREFIX={self.sysroot}',
                '-DCMAKE_INSTALL_LIBDIR=lib',
                '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
                '-DLIBTYPE=STATIC',
                '-DALSOFT_EXAMPLES=OFF',
                '-DALSOFT_UTILS=OFF',
                '-DALSOFT_TESTS=OFF',
                # Backends are dlopen'd at runtime (ALSOFT_DLOPEN default),
                # so building them needs only headers -- but a missing
                # header silently drops the backend and leaves a
                # soundless build, so require the ones players use.
                '-DALSOFT_REQUIRE_PIPEWIRE=ON',
                '-DALSOFT_REQUIRE_PULSEAUDIO=ON',
                '-DALSOFT_REQUIRE_ALSA=ON',
            ],
            cwd=cmakebuild,
        )
        crun([self.cmake, '--build', '.', f'-j{cpus()}'], cwd=cmakebuild)
        crun([self.cmake, '--install', '.'], cwd=cmakebuild)

    def _build_sdl3(self) -> None:
        print('Building SDL3...', flush=True)
        srcdir = self._src(
            f'https://github.com/libsdl-org/SDL/releases/download/'
            f'release-{SDL3_VER}/SDL3-{SDL3_VER}.tar.gz'
        )
        cmakebuild = os.path.join(srcdir, 'build-portable')
        os.makedirs(cmakebuild)
        crun = self.container.run
        crun(
            [
                self.cmake,
                '..',
                '-DCMAKE_BUILD_TYPE=Release',
                f'-DCMAKE_C_COMPILER={SDK_CC}',
                f'-DCMAKE_CXX_COMPILER={SDK_CXX}',
                f'-DCMAKE_INSTALL_PREFIX={self.sdl3_install}',
                '-DCMAKE_INSTALL_LIBDIR=lib',
                '-DSDL_SHARED=ON',
                '-DSDL_STATIC=OFF',
                '-DSDL_TEST_LIBRARY=OFF',
                '-DSDL_TESTS=OFF',
                '-DSDL_EXAMPLES=OFF',
                # Load optional system deps at runtime (upstream default;
                # explicit since it's the whole point of building our own).
                '-DSDL_DEPS_SHARED=ON',
            ],
            cwd=cmakebuild,
        )
        crun([self.cmake, '--build', '.', f'-j{cpus()}'], cwd=cmakebuild)
        crun([self.cmake, '--install', '.'], cwd=cmakebuild)

    # -- Python -------------------------------------------------------------

    def _fetch_python(self) -> None:
        print('Fetching Python source...', flush=True)
        tarball = _fetch(
            f'https://www.python.org/ftp/python/{PY_VER_EXACT}/'
            f'Python-{PY_VER_EXACT}.tar.xz',
            self.cache_dir,
        )
        _extract(tarball, self.srcdir)
        assert os.path.isdir(self.pydir)

    def _patch_python(self) -> None:
        from efrotools.util import readfile, replace_exact, writefile
        from efrotools.pybuild import (
            patch_modules_setup,
            patch_uuid_platform_check,
        )

        # Same module set as Android/Apple: everything static, nothing in
        # lib-dynload.
        patch_modules_setup(self.pydir, 'linux', python_version=PY_VER)

        # Keep 'import uuid' from pulling in ctypes.
        patch_uuid_platform_check(self.pydir)

        # Our low-level debug-log hook (as on Android; see
        # PY_HAVE_BALLISTICA_LOW_LEVEL_DEBUG_LOG in core_python.cc).
        fname = os.path.join(self.pydir, 'Include', 'fileutils.h')
        writefile(
            fname,
            replace_exact(
                readfile(fname),
                '\n#ifdef __cplusplus\n}\n',
                '\n'
                '/* ericf hack for debugging */\n'
                '#define PY_HAVE_BALLISTICA_LOW_LEVEL_DEBUG_LOG\n'
                'extern void (*Py_BallisticaLowLevelDebugLog)'
                '(const char* msg);\n'
                '\n'
                '#ifdef __cplusplus\n}\n',
            ),
        )
        fname = os.path.join(self.pydir, 'Python', 'fileutils.c')
        writefile(
            fname,
            replace_exact(
                readfile(fname),
                '    _Py_END_SUPPRESS_IPH\n}',
                '    _Py_END_SUPPRESS_IPH\n}\n\n'
                'void (*Py_BallisticaLowLevelDebugLog)(const char* msg)'
                ' = NULL;\n',
            ),
        )

    def _build_python(self) -> None:
        print('Configuring Python...', flush=True)
        inc = f'{self.sysroot}/include'
        lib = f'{self.sysroot}/lib'
        env = dict(self.env)
        # Hand configure our static deps directly (as on Android) so it
        # never falls back to anything in the SDK.
        env['LIBSQLITE3_CFLAGS'] = f'-I{inc}'
        env['LIBSQLITE3_LIBS'] = f'-L{lib} -lsqlite3 -lm'
        env['LIBZSTD_CFLAGS'] = f'-I{inc}'
        env['LIBZSTD_LIBS'] = f'-L{lib} -lzstd'
        env['LIBFFI_CFLAGS'] = f'-I{inc}'
        env['LIBFFI_LIBS'] = f'-L{lib} -lffi'
        env['LIBLZMA_CFLAGS'] = f'-I{inc}'
        env['LIBLZMA_LIBS'] = f'-L{lib} -llzma'
        env['BZIP2_CFLAGS'] = f'-I{inc}'
        env['BZIP2_LIBS'] = f'-L{lib} -lbz2'
        env['ZLIB_CFLAGS'] = f'-I{inc}'
        env['ZLIB_LIBS'] = f'-L{lib} -lz'
        env['LIBUUID_CFLAGS'] = f'-I{inc}/uuid'
        env['LIBUUID_LIBS'] = f'-L{lib} -luuid'
        # Static libcrypto needs libpthread on glibc < 2.34 (Android's
        # libc has it built in), and configure puts LIBS *before*
        # -lssl -lcrypto, which doesn't work for static archives. The
        # -pthread driver flag lands at the end of the link line instead.
        # (OpenSSL is built no-dso, so it needs no libdl.) Without this,
        # configure's "OpenSSL provides required ssl/hashlib APIs" link
        # tests fail and _ssl/_hashlib are silently dropped.
        env['LDFLAGS'] = f'{env['LDFLAGS']} -pthread'
        args = [
            './configure',
            '--prefix=/usr',
            '--without-ensurepip',
            '--enable-option-checking=fatal',
            f'--with-openssl={self.sysroot}',
            # Static OpenSSL; never bake a build-box path into anything.
            '--with-openssl-rpath=no',
        ]
        if self.debug:
            args.append('--with-pydebug')
        crun = self.container.run
        crun(args, cwd=self.pydir, env=env)
        self._check_configured_modules()
        self._patch_makefile()

        print('Building Python...', flush=True)
        crun(['make', f'-j{cpus()}'], cwd=self.pydir, env=env)
        crun(
            ['make', 'install', f'DESTDIR={self.installdir}'],
            cwd=self.pydir,
            env=env,
        )

        # 3.14 links the static _hmac module against the HACL* objects
        # via its LDFLAGS instead of archiving them into libpython.a,
        # leaving undefined _Py_LibHacl_* symbols for anyone linking the
        # archive. Append them (exactly as the Android build does).
        hacl_objs = sorted(glob.glob(f'{self.pydir}/Modules/_hacl/*.o'))
        if hacl_objs:
            print(f'Appending {len(hacl_objs)} HACL objects to libpython...')
            crun(['ar', '-q', self._libpython_path(), *hacl_objs], cwd='/')

    def _check_configured_modules(self) -> None:
        """Fail fast if configure couldn't use one of our deps.

        Configure quietly marks a module 'missing' when a dep check
        fails, which otherwise only shows up after the full build.
        """
        with open(f'{self.pydir}/Makefile', encoding='utf-8') as infile:
            txt = infile.read()
        bad = [
            mod
            for mod in (
                '_SSL',
                '_HASHLIB',
                '_SQLITE3',
                '_LZMA',
                '_ZSTD',
                '_CTYPES',
                'ZLIB',
                '_BZ2',
            )
            if f'MODULE_{mod}_STATE=yes' not in txt
        ]
        if bad:
            raise RuntimeError(
                f'Python configure did not enable: {bad}; see config.log in'
                f' {self.pydir}.'
            )

    def _patch_makefile(self) -> None:
        """Clear MODULE__BLAKE2_LDFLAGS in the generated Makefile.

        Same fix (and reasoning) as the Android build's
        ``_patch_android_makefile``: with both _blake2 and _hmac static,
        the python-executable link lists HACL Blake2 objects twice and
        fails on duplicate symbols. libpython.a itself is unaffected.
        """
        mkpath = os.path.join(self.pydir, 'Makefile')
        with open(mkpath, encoding='utf-8') as infile:
            txt = infile.read()
        txt, count = re.subn(
            r'^(MODULE__BLAKE2_LDFLAGS=).*$', r'\1', txt, flags=re.MULTILINE
        )
        if count == 0:
            raise RuntimeError(
                'MODULE__BLAKE2_LDFLAGS not found in Python Makefile;'
                ' update _patch_makefile() for this Python version.'
            )
        with open(mkpath, 'w', encoding='utf-8') as outfile:
            outfile.write(txt)

    def _libpython_path(self) -> str:
        dbgsfx = 'd' if self.debug else ''
        return f'{self.installdir}/usr/lib/libpython{PY_VER}{dbgsfx}.a'

    def _check_python(self) -> None:
        """Sanity-check the result (static modules, imports, versions)."""
        print('Checking Python build...', flush=True)
        libdir = f'{self.installdir}/usr/lib/python{PY_VER}'

        # All extension modules must be static; anything in lib-dynload
        # would be missing at runtime (we don't ship it).
        sofiles = glob.glob(f'{libdir}/lib-dynload/*.so')
        if sofiles:
            names = ', '.join(sorted(os.path.basename(f) for f in sofiles))
            raise RuntimeError(
                f'Shared extension modules found (all must be static): {names}.'
                ' Update cmodules/enables in pybuild.patch_modules_setup().'
            )

        # Unlike Android, we can run what we built. Exercise the modules
        # whose deps we built, from a clean environment.
        pyexe = f'{self.installdir}/usr/bin/python{PY_VER}'
        script = (
            'import ssl, sqlite3, lzma, bz2, zlib, ctypes, uuid, hashlib,'
            ' json, asyncio, compression.zstd, _hmac;'
            ' hashlib.blake2b(b"x"); hashlib.sha3_256(b"x");'
            ' print("OpenSSL:", ssl.OPENSSL_VERSION);'
            ' print("SQLite:", sqlite3.sqlite_version);'
            ' print("zstd:", compression.zstd.zstd_version);'
            ' print("ctypes:", ctypes.CDLL(None).getpid() > 0)'
        )
        print(
            self.container.output(
                [
                    'env',
                    '-i',
                    f'PYTHONHOME={self.installdir}/usr',
                    pyexe,
                    '-I',
                    '-c',
                    script,
                ],
                cwd='/',
            ),
            end='',
        )

    # -- Output -------------------------------------------------------------

    def _assemble_out(self) -> None:
        """Gather everything a portable link needs into out/."""
        from efrotools.pybuild import PRUNE_LIB_NAMES, tweak_empty_py_files

        dbgsfx = 'd' if self.debug else ''
        out = self.outdir
        os.makedirs(f'{out}/lib')
        os.makedirs(f'{out}/include')

        # Python headers (pyconfig.h renamed per-arch; gather adds a
        # router so one include dir serves both arches).
        shutil.copytree(
            f'{self.installdir}/usr/include/python{PY_VER}{dbgsfx}',
            f'{out}/include/python{PY_VER}',
        )
        os.rename(
            f'{out}/include/python{PY_VER}/pyconfig.h',
            f'{out}/include/python{PY_VER}/pyconfig_linux_{self.arch}.h',
        )
        shutil.copytree(f'{self.sysroot}/include/AL', f'{out}/include/AL')

        # Static libs. DWARF is most of their size (OpenAL alone is
        # ~200 MB with it) and these live in git LFS per arch+flavor, so
        # strip it, keeping symbols (crash backtraces still get names).
        # The debug flavor keeps libpython's debug info; that's what
        # it's for.
        shutil.copy(self._libpython_path(), f'{out}/lib/')
        for libname in _OUT_LIBS:
            shutil.copy(f'{self.sysroot}/lib/{libname}', f'{out}/lib/')
        # Our SDL3 (shared; packages ship it beside the binary) under the
        # soname the binary asks for.
        shutil.copy(
            os.path.realpath(f'{self.sdl3_install}/lib/libSDL3.so.0'),
            f'{out}/lib/libSDL3.so.0',
        )
        for libname in sorted(os.listdir(f'{out}/lib')):
            if self.debug and libname.startswith('libpython'):
                continue
            self.container.run(
                ['strip', '--strip-debug', f'{out}/lib/{libname}'], cwd='/'
            )

        # Stdlib: .py files only, pruned like Android's.
        pylib = f'{out}/pylib'
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
                f'{self.installdir}/usr/lib/python{PY_VER}/',
                f'{pylib}/',
            ],
            check=True,
        )
        tweak_empty_py_files(pylib)
        assert all(' ' not in name for name in PRUNE_LIB_NAMES)
        subprocess.run(
            f'cd "{pylib}" && rm -rf ' + ' '.join(PRUNE_LIB_NAMES),
            shell=True,
            check=True,
        )
        subprocess.run(
            ['find', pylib, '-type', 'd', '-empty', '-delete'], check=True
        )

        # Per-arch sysconfig data (pruned above; kept beside the stdlib
        # as on Android, under arch-unique names).
        sysconfig_dir = f'{out}/pylib_arch'
        os.makedirs(sysconfig_dir)
        for pattern in ('_sysconfigdata_*.py', '_sysconfig_vars_*.json'):
            for path in glob.glob(
                f'{self.installdir}/usr/lib/python{PY_VER}/{pattern}'
            ):
                shutil.copy(path, sysconfig_dir)


def build(rootdir: str, arch: str, debug: bool) -> None:
    """Build all linux-portable deps for one arch (on a matching host)."""
    _Builder(rootdir, arch, debug).run()


def gather(rootdir: str, arch: str, debug: bool) -> None:
    """Copy one arch's built deps (from :func:`build`) into the project.

    Writes ``src/external/linux-portable-deps[-debug]/`` (headers + per-arch
    static libs) and ``src/assets/pylib-linux-portable/`` (the stdlib,
    shared by all arches and flavors). Arch-independent parts must match
    what's already there from other arches; we fail if they don't.
    """
    outdir = os.path.join(build_root(rootdir, arch, debug), 'out')
    if not os.path.isdir(outdir):
        raise RuntimeError(f'No build output at {outdir}.')
    suffix = '-debug' if debug else ''
    extdir = os.path.join(rootdir, f'src/external/linux-portable-deps{suffix}')
    pylibdir = os.path.join(rootdir, 'src/assets/pylib-linux-portable')
    incdir = os.path.join(extdir, 'include')
    pyincname = f'python{PY_VER}'

    # Headers: identical across arches apart from the per-arch pyconfig.
    if os.path.isdir(incdir):
        _require_same(
            os.path.join(outdir, 'include'),
            incdir,
            excludes=['pyconfig.h', 'pyconfig_linux_*.h'],
        )
    else:
        shutil.copytree(os.path.join(outdir, 'include'), incdir)
    pyconfig = f'pyconfig_linux_{arch}.h'
    shutil.copy(
        os.path.join(outdir, 'include', pyincname, pyconfig),
        os.path.join(incdir, pyincname, pyconfig),
    )
    with open(
        os.path.join(incdir, pyincname, 'pyconfig.h'), 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(
            '// Generated by batools.linuxportable; routes to the per-arch'
            ' config.\n'
            '#if defined(__x86_64__)\n'
            '#include "pyconfig_linux_x86_64.h"\n'
            '#elif defined(__aarch64__)\n'
            '#include "pyconfig_linux_arm64.h"\n'
            '#else\n'
            '#error unsupported linux-portable arch\n'
            '#endif\n'
        )

    # Static libs for this arch.
    libdst = os.path.join(extdir, 'lib', f'linux_{arch}')
    subprocess.run(['rm', '-rf', libdst], check=True)
    shutil.copytree(os.path.join(outdir, 'lib'), libdst)

    # Stdlib: identical across arches and flavors apart from the
    # per-arch sysconfig files.
    sysconfig_names = sorted(os.listdir(os.path.join(outdir, 'pylib_arch')))
    if os.path.isdir(pylibdir):
        _require_same(
            os.path.join(outdir, 'pylib'),
            pylibdir,
            excludes=['_sysconfigdata_*', '_sysconfig_vars_*'],
        )
    else:
        shutil.copytree(os.path.join(outdir, 'pylib'), pylibdir)
    for name in sysconfig_names:
        shutil.copy(os.path.join(outdir, 'pylib_arch', name), pylibdir)

    print(f'Gathered linux-portable deps for {arch} (debug={debug}).')


def _require_same(src: str, dst: str, excludes: list[str]) -> None:
    """Fail if two dir trees differ (ignoring excludes)."""
    cmd = ['diff', '-r', '-q']
    for exclude in excludes:
        cmd.append(f'--exclude={exclude}')
    result = subprocess.run(
        [*cmd, src, dst], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f'{src} does not match existing {dst}:\n{result.stdout}'
            'If this is an intentional version bump, delete the existing'
            ' output and re-gather every arch.'
        )
