# Released under the MIT License. See LICENSE for details.
#
"""Engine builds for 'linux-portable' builds.

Compiles the engine with ``-DPORTABLE=ON`` (bundled deps from
``src/external/linux-portable-deps*``) inside the Steam Runtime SDK
container, checks that the result only needs system libraries the Steam
Runtime and ordinary distros provide, and smoke-runs it inside Valve's
player-side runtime image. Runs on a docker-equipped build host of the
target arch; see ``docs/initiatives/linux-portable-builds.md``.
"""

import os
import re
from dataclasses import dataclass

from batools.build import cmake_prep_dir
from batools.linuxportable import (
    SDK_IMAGES,
    SDK_CC,
    SDK_CXX,
    UNAME_ARCHS,
    SdkContainer,
    cpus,
)

# server: headless; gui: the downloads-page client (test_build); steam:
# the client built as the steam variant (own build dirs, so switching
# between gui and steam never wipes one or the other).
KINDS = ('server', 'gui', 'steam')

# Player-side runtime image per arch (what Steam runs games in); must
# match SDK_IMAGES' runtime + version.
RUNTIME_IMAGES: dict[str, str] = {
    'x86_64': 'registry.gitlab.steamos.cloud/steamrt/sniper/platform:'
    '3.0.20261021.266025',
    'arm64': 'registry.gitlab.steamos.cloud/steamrt/steamrt4/platform/arm64:'
    '4.0.20261021.265997',
}

# Plain distro images the smoke run also boots in (the downloads-page
# case: no Steam runtime). Oldest supported plus distros with unusual
# system configs (Fedora's crypto-policies openssl.cnf broke our OpenSSL
# once; Arch tracks the newest of everything).
DISTRO_IMAGES: dict[str, list[str]] = {
    'x86_64': ['ubuntu:20.04', 'debian:11', 'fedora:41', 'archlinux:latest'],
    'arm64': ['ubuntu:24.04', 'debian:13', 'fedora:41'],
}

# Newest glibc symbol version a binary may require, per arch: the
# runtime's glibc (sniper is Debian 11; Steam Runtime 4 is Debian 13).
GLIBC_CEILINGS: dict[str, tuple[int, int]] = {
    'x86_64': (2, 31),
    'arm64': (2, 41),
}

# System libs a portable binary may link dynamically. Everything else
# must be bundled (static, or for GUI downloads-page packages, shipped
# beside the binary). libstdc++/libgcc_s are deliberately absent: we link
# the C++ runtime statically.
_ALLOWED_LIBS_COMMON = {
    'libc.so.6',
    'libm.so.6',
    'libdl.so.2',
    'libpthread.so.0',
    'libutil.so.1',
    'ld-linux-x86-64.so.2',
    'ld-linux-aarch64.so.1',
}
_ALLOWED_LIBS_GUI = {
    'libSDL3.so.0',
    # Not GLVND's libOpenGL.so.0: the sniper runtime lacks it.
    'libGL.so.1',
    'libGLX.so.0',
    'libEGL.so.1',
    'libogg.so.0',
    'libvorbisfile.so.3',
    'libpango-1.0.so.0',
    'libpangocairo-1.0.so.0',
    'libcairo.so.2',
    'libgobject-2.0.so.0',
    'libglib-2.0.so.0',
    'libharfbuzz.so.0',
    'libfontconfig.so.1',
    'libfreetype.so.6',
}
# Extra system libs that third-party libs we ship beside the binary
# (Discord's prebuilt .so) may link. Kept separate so our own binary can
# never start needing them (libgcc_s especially: we link it statically).
_ALLOWED_LIBS_BUNDLED_EXTRA = {
    'libgcc_s.so.1',
    'libatomic.so.1',
    'librt.so.1',
    'libasound.so.2',
    'libpulse.so.0',
    'libX11.so.6',
}
# Third-party shared libs that may sit beside the binary (found via its
# $ORIGIN rpath). Discord's SDK only exists for Linux x86_64.
_DISCORD_LIB = 'libdiscord_partner_sdk.so'
_SDL3_LIB = 'libSDL3.so.0'


@dataclass
class _KindInfo:
    binary: str
    cmake_args: list[str]
    # Where the binary goes in the staged tree (relative to staged/).
    dist_subdir: str
    # Extra env for smoke runs.
    smoke_env: dict[str, str]
    # Whether to also smoke-run in plain distro images.
    distro_smoke: bool


def _kind_info(kind: str) -> _KindInfo:
    match kind:
        case 'server':
            return _KindInfo(
                binary='ballisticakit_headless',
                cmake_args=['-DHEADLESS=true', '-DVARIANT=server'],
                dist_subdir='dist',
                smoke_env={},
                distro_smoke=True,
            )
        case 'gui' | 'steam':
            return _KindInfo(
                binary='ballisticakit',
                # Discord comes along where its SDK has a library
                # (x86_64); cmake warns and skips it elsewhere.
                cmake_args=[
                    '-DVARIANT='
                    + ('steam' if kind == 'steam' else 'test_build'),
                    '-DDISCORD=ON',
                ],
                dist_subdir='.',
                # No GPU or display: SDL's offscreen driver on Mesa's
                # llvmpipe (the runtime image ships Mesa), with
                # uncompressed textures (llvmpipe decodes BC7/ASTC
                # slowly), as test_game_run --platform linux does. (The
                # runtime image's Mesa is old -- 20.3 -- which is also a
                # useful check that we get a core-profile context: its
                # llvmpipe caps compat contexts at GL 3.1.)
                smoke_env={
                    'SDL_VIDEODRIVER': 'offscreen',
                    'LIBGL_ALWAYS_SOFTWARE': '1',
                    'BA_FORCE_TEXTURE_PROFILE': 'fallback_v1',
                },
                # Bare distro images lack Mesa/SDL3/pango; GUI distro
                # coverage comes with downloads-page packaging.
                distro_smoke=False,
            )
        case _:
            raise ValueError(f'Invalid kind {kind!r}; expected {KINDS}.')


def build_dir(rootdir: str, kind: str, arch: str, buildtype: str) -> str:
    """Return the dir for one portable engine build.

    Holds ``staged/`` (staged locally and synced up) and ``cmake/`` (the
    remote cmake build dir).
    """
    return os.path.join(
        rootdir, f'build/linux_portable/{kind}-{arch}-{buildtype}'
    )


def build(
    rootdir: str,
    *,
    kind: str,
    arch: str,
    buildtype: str,
    extra_cmake_args: list[str],
    smoke: bool,
    bundle: bool = False,
    dev: bool = False,
    fast: bool = False,
    deploy: str | None = None,
) -> None:
    """Build (and check, and optionally smoke-run) a portable engine.

    With ``bundle``, also gather the shared libs a downloads-page package
    ships beside the binary (SDL3 from the SDK, plus Discord where built)
    into ``bundle/`` in the build dir.

    ``dev`` makes a developer build (``--fleet`` etc.) in its own build
    dir. ``fast`` skips the binary checks (for iteration loops; packages
    and CI keep them). ``deploy`` names a dir (relative to rootdir) to
    receive a debug-stripped copy of the binary -- full DWARF makes a
    debug binary ~7x larger, which dominates transfer time to a device --
    plus any shared libs it needs beside it.
    """
    # pylint: disable=too-many-locals
    info = _kind_info(kind)
    if buildtype not in ('debug', 'release'):
        raise ValueError(f'Invalid buildtype {buildtype!r}.')
    host_arch = os.uname().machine
    if host_arch != UNAME_ARCHS[arch]:
        raise RuntimeError(
            f'Building {arch} requires a {UNAME_ARCHS[arch]} host'
            f' (this is {host_arch}).'
        )
    dirkind = f'{kind}-dev' if dev else kind
    bdir = build_dir(rootdir, dirkind, arch, buildtype)
    cmakedir = os.path.join(bdir, 'cmake')
    os.makedirs(cmakedir, exist_ok=True)
    binpath = os.path.join(cmakedir, info.binary)

    cmake_args = [
        '-DCMAKE_BUILD_TYPE='
        + ('Debug' if buildtype == 'debug' else 'Release'),
        f'-DCMAKE_C_COMPILER={SDK_CC}',
        f'-DCMAKE_CXX_COMPILER={SDK_CXX}',
        '-DPORTABLE=ON',
        *info.cmake_args,
        *extra_cmake_args,
    ]
    # Start a fresh dir whenever the SDK image or our configure options
    # change (as with cmake/python version changes), so we only need to
    # configure once per dir.
    cmake_prep_dir(
        cmakedir,
        extra_entries={
            'portable sdk image': SDK_IMAGES[arch],
            'portable cmake args': ' '.join(cmake_args),
        },
    )

    import time

    times: list[tuple[str, float]] = [('start', time.monotonic())]
    name = f'ba-linux-portable-{dirkind}-{arch}-{buildtype}'
    with SdkContainer(SDK_IMAGES[arch], rootdir, name) as sdk:
        times.append(('container', time.monotonic()))
        if not os.path.exists(os.path.join(cmakedir, 'Makefile')):
            sdk.run(
                [
                    'cmake',
                    *cmake_args,
                    os.path.join(rootdir, 'ballisticakit-cmake'),
                ],
                cwd=cmakedir,
            )
        sdk.run(['make', f'-j{cpus()}', 'ballisticakitbin'], cwd=cmakedir)
        times.append(('make', time.monotonic()))

        # Discord's lib sits beside the binary when built in.
        discordpath = os.path.join(cmakedir, _DISCORD_LIB)
        has_discord = os.path.exists(discordpath)
        if deploy is not None:
            _deploy(
                sdk,
                binpath,
                discordpath if has_discord else None,
                os.path.join(rootdir, deploy),
            )
            times.append(('deploy', time.monotonic()))
        spans = ', '.join(
            f'{label} {end - times[i][1]:.1f}s'
            for i, (label, end) in enumerate(times[1:])
        )
        print(f'Portable build timing: {spans}.', flush=True)
        if fast:
            return

        allowed = set(_ALLOWED_LIBS_COMMON)
        if kind != 'server':
            allowed |= _ALLOWED_LIBS_GUI
        _check_elf(
            sdk,
            binpath,
            arch,
            allowed | ({_DISCORD_LIB} if has_discord else set()),
        )
        bundled_allowed = allowed | _ALLOWED_LIBS_BUNDLED_EXTRA
        if has_discord:
            _check_elf(sdk, discordpath, arch, bundled_allowed)
        if bundle:
            _gather_bundle(
                rootdir, bdir, arch, discordpath if has_discord else None
            )
            _check_elf(
                sdk,
                os.path.join(bdir, 'bundle', _SDL3_LIB),
                arch,
                bundled_allowed,
            )

    if smoke:
        _smoke_run(rootdir, bdir, info, arch, buildtype)


def _deploy(
    sdk: SdkContainer, binpath: str, discordpath: str | None, deploydir: str
) -> None:
    """Write a debug-stripped binary (+ needed libs) into deploydir.

    Skips work when outputs are already up to date (mtimes), so an
    unchanged binary leaves the deploy copy untouched and syncs for free.
    """
    import shutil

    os.makedirs(deploydir, exist_ok=True)
    outpath = os.path.join(deploydir, os.path.basename(binpath))
    if not os.path.exists(outpath) or os.path.getmtime(
        outpath
    ) < os.path.getmtime(binpath):
        # Keep the symbol table (backtraces still get names); drop DWARF.
        tmppath = f'{outpath}.tmp'
        sdk.run(['objcopy', '--strip-debug', binpath, tmppath], cwd='/')
        os.replace(tmppath, outpath)
    if discordpath is not None:
        libout = os.path.join(deploydir, os.path.basename(discordpath))
        if not os.path.exists(libout) or os.path.getmtime(
            libout
        ) < os.path.getmtime(discordpath):
            shutil.copy2(discordpath, libout)


def _gather_bundle(
    rootdir: str, bdir: str, arch: str, discordpath: str | None
) -> None:
    """Collect the shared libs a downloads-page package ships."""
    import shutil

    bundledir = os.path.join(bdir, 'bundle')
    if os.path.exists(bundledir):
        shutil.rmtree(bundledir)
    os.makedirs(bundledir)
    # Our own SDL3 from the bundled deps (not the SDK's: that one links
    # ~20 desktop libs directly; ours loads them at runtime).
    shutil.copy2(
        os.path.join(
            rootdir,
            f'src/external/linux-portable-deps/lib/linux_{arch}/{_SDL3_LIB}',
        ),
        bundledir,
    )
    if discordpath is not None:
        shutil.copy2(discordpath, bundledir)
    print(
        f'Gathered package libs: {sorted(os.listdir(bundledir))}.', flush=True
    )


def _check_elf(
    sdk: SdkContainer, binpath: str, arch: str, allowed: set[str]
) -> None:
    """Fail if a binary or lib needs anything a portable build can't."""
    dynamic = sdk.output(['readelf', '--dynamic', binpath], cwd='/')
    needed = set(re.findall(r'\(NEEDED\)\s+Shared library: \[(.+?)\]', dynamic))
    disallowed = sorted(needed - allowed)

    symbols = sdk.output(['objdump', '--dynamic-syms', binpath], cwd='/')
    glibc_versions = {
        (int(major), int(minor))
        for major, minor in re.findall(r'GLIBC_(\d+)\.(\d+)', symbols)
    }
    newest = max(glibc_versions, default=(0, 0))
    ceiling = GLIBC_CEILINGS[arch]

    print(
        f'Portable binary check ({os.path.basename(binpath)}):'
        f' needs {sorted(needed)};'
        f' newest glibc symbol {newest[0]}.{newest[1]}'
        f' (ceiling {ceiling[0]}.{ceiling[1]}).',
        flush=True,
    )
    problems: list[str] = []
    if disallowed:
        problems.append(f'links libraries outside the allowlist: {disallowed}')
    if newest > ceiling:
        problems.append(
            f'requires glibc {newest[0]}.{newest[1]}, newer than'
            f' {ceiling[0]}.{ceiling[1]}'
        )
    if problems:
        raise RuntimeError(
            f'Portable binary {binpath} ' + '; '.join(problems) + '.'
        )


def _smoke_run(
    rootdir: str, bdir: str, info: _KindInfo, arch: str, buildtype: str
) -> None:
    """Boot the staged build inside the player-side runtime and quit.

    Runs the binary from the cmake dir against the synced staged data
    (we don't copy it into staged/: the next sync would delete it).
    """
    distdir = os.path.normpath(os.path.join(bdir, 'staged', info.dist_subdir))
    if not os.path.isdir(os.path.join(distdir, 'ba_data')):
        raise RuntimeError(
            f'No staged data at {distdir}; stage the build before a smoke run.'
        )
    binpath = os.path.join(bdir, 'cmake', info.binary)

    images = [RUNTIME_IMAGES[arch]]
    if info.distro_smoke:
        images += DISTRO_IMAGES[arch]
    envargs = [
        f'{key}={val}'
        for key, val in {
            'BA_LOG_LEVELS': 'ba.lifecycle=INFO',
            **info.smoke_env,
        }.items()
    ]
    for image in images:
        print(f'Smoke-running in {image}...', flush=True)
        safename = re.sub(r'[^a-zA-Z0-9_.-]', '_', image.rsplit('/', 1)[-1])
        name = f'ba-linux-portable-smoke-{arch}-{buildtype}-{safename}'
        with SdkContainer(
            image,
            rootdir,
            name,
            # Steam's container runtime passes the host's machine-id
            # through (the engine derives its device id from it); a bare
            # container has none.
            extra_run_args=['--volume', '/etc/machine-id:/etc/machine-id:ro'],
        ) as container:
            output = container.output(
                [
                    'env',
                    *envargs,
                    'timeout',
                    '120',
                    binpath,
                    '--exec',
                    'import babase; babase.apptimer(5.0, babase.quit)',
                ],
                cwd=distdir,
                stderr_to_stdout=True,
            )
        # A clean exit isn't enough (network failures don't fail the
        # process); require the asset gate, which needs the cloud.
        if 'asset gate opened' not in output:
            raise RuntimeError(
                f'Smoke run in {image} never opened the asset gate:\n'
                + output[-4000:]
            )
        print(f'  OK in {image}.', flush=True)
    print('Smoke runs passed.', flush=True)
