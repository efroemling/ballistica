# Released under the MIT License. See LICENSE for details.
#
"""Build OpenAL Soft for Apple platforms (macOS / iOS / tvOS / visionOS).

Produces a single ``.framework``-based ``OpenALSoft.xcframework`` covering
macOS, iOS, tvOS and visionOS (device + simulator), plus a shared
``include/AL`` header tree (identical across every slice).

Unlike ANGLE (``batools/buildangleapple.py``), which keeps macOS on bare
dylibs because ``libEGL`` ``dlopen``s ``libGLESv2`` as a sibling file *and* the
non-Xcode cmake/SDL build consumes the same binaries, OpenAL Soft is a single
self-contained library with no such constraints (and the macOS cmake build
uses its own static ``libopenal.a``). So **every** Apple Xcode target -- macOS
included -- links + embeds the framework slice out of this one xcframework;
there is no standalone macOS dylib. OpenAL Soft is a plain CMake project, so
each slice is just a cross-compiled CMake build (no gn/depot_tools), wrapped
into a framework here.

Everything lives under ``build/openal-apple/``:

- ``checkout/`` -- the OpenAL Soft git checkout (one, shared by all slices;
  each slice gets its own ``checkout/build-<slice>`` CMake build dir);
- ``artifacts/`` -- the assembled ``OpenALSoft.xcframework`` + ``include``
  header tree that ``gather`` installs into the source tree.

Remove ``build/openal-apple/`` to fully clean up. Host prerequisites are a full
Xcode install and a system git + cmake -- nothing is installed system-wide.

The naming (``OpenALSoft`` rather than ``OpenAL``) deliberately avoids a clash
with Apple's deprecated system ``OpenAL.framework``; OpenAL Soft's own cmake
does the same (its framework is ``soft_oal``).
"""

import os
import shutil
import tarfile
import urllib.request
import subprocess
from pathlib import Path
from dataclasses import dataclass

from efro.error import CleanError

# OpenAL Soft version to build (a git tag in the upstream repo). We fetch the
# release source *tarball* rather than git-cloning: a pinned build needs no
# git history, and a nested .git checkout trips the build sandbox.
OPENAL_SOFT_TAG = '1.25.2'
OPENAL_SOFT_TARBALL = (
    f'https://github.com/kcat/openal-soft/archive/refs/tags/'
    f'{OPENAL_SOFT_TAG}.tar.gz'
)

# Framework + binary stem used inside the xcframework (NOT 'OpenAL' -- see the
# module docstring re: clashing with Apple's system OpenAL.framework).
FRAMEWORK_NAME = 'OpenALSoft'

# Where, relative to the repo root, all of our state lives.
STATE_SUBDIR = Path('build') / 'openal-apple'

# Deployment-target minimums -- kept in sync with the libpython Apple build
# (tools/efrotools/python_build_apple.py).
MACOS_MIN = '11.0'
IOS_MIN = '13.0'
TVOS_MIN = '12.0'
VISIONOS_MIN = '2.0'


@dataclass(frozen=True)
class Slice:
    """One Apple build target: an (os, arch(es), sdk) combination.

    Each slice is a single CMake cross-compile producing one shared
    ``libopenal`` dylib that becomes one framework slice of the xcframework.
    ``system_name`` is the CMake ``CMAKE_SYSTEM_NAME`` (``None`` => a native
    macOS build, where we go universal in a single pass).
    """

    name: str  # build-dir + label, e.g. 'iphoneos' / 'macos'.
    system_name: str | None  # CMAKE_SYSTEM_NAME: 'iOS'/'tvOS'/'visionOS'/None.
    archs: str  # CMAKE_OSX_ARCHITECTURES value, e.g. 'arm64' or 'arm64;x86_64'.
    sdk: str  # CMAKE_OSX_SYSROOT sdk name, e.g. 'iphoneos'.
    deployment_target: str  # CMAKE_OSX_DEPLOYMENT_TARGET.
    versioned: bool = False  # True => deep (Versions/A) framework (macOS only).


# All slices that make up the xcframework. macOS is a single universal slice;
# every other platform ships a device slice + a simulator slice (both arm64).
SLICES = [
    Slice('macos', None, 'arm64;x86_64', 'macosx', MACOS_MIN, versioned=True),
    Slice('iphoneos', 'iOS', 'arm64', 'iphoneos', IOS_MIN),
    Slice('iphonesimulator', 'iOS', 'arm64', 'iphonesimulator', IOS_MIN),
    Slice('appletvos', 'tvOS', 'arm64', 'appletvos', TVOS_MIN),
    Slice('appletvsimulator', 'tvOS', 'arm64', 'appletvsimulator', TVOS_MIN),
    Slice('xros', 'visionOS', 'arm64', 'xros', VISIONOS_MIN),
    Slice('xrsimulator', 'visionOS', 'arm64', 'xrsimulator', VISIONOS_MIN),
]


def _env() -> dict[str, str]:
    """Environment for our subprocesses.

    Empties GIT_TEMPLATE_DIR so ``git clone`` never copies the host's hook
    templates into the checkout we create -- that copy both leaves host hooks
    behind and trips the build sandbox ("Operation not permitted").
    """
    env = dict(os.environ)
    env['GIT_TEMPLATE_DIR'] = ''
    return env


def _run(cmd: list[str], cwd: Path) -> None:
    """Run a command, echoing it, and raise on failure."""
    joined = ' '.join(cmd)
    print(f'\n+ {joined}  (cwd={cwd})', flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd), env=_env(), check=False)
    if proc.returncode != 0:
        raise RuntimeError(f'Command failed (code {proc.returncode}): {joined}')


def _cpus() -> int:
    return os.cpu_count() or 4


def _patch_checkout(checkout: Path) -> None:
    """Apply durable local patches to the extracted OpenAL Soft source.

    1.25.2 unconditionally promotes ``-Wfunction-effects`` to an error
    (``-Werror=function-effects`` -- independent of the ``ALSOFT_WERROR``
    option) whenever the compiler supports it, but its own CoreAudio backend
    trips that diagnostic under current Xcode clang (a noexcept lambda ->
    C-function-pointer conversion drops the ``nonblocking`` effect), so every
    Apple slice fails to build. Demote it back to a non-fatal warning; the
    plain ``-Wfunction-effects`` added earlier still fires. Idempotent.
    """
    cmakelists = checkout / 'CMakeLists.txt'
    text = cmakelists.read_text(encoding='utf-8')
    if '-Werror=function-effects' in text:
        cmakelists.write_text(
            text.replace('-Werror=function-effects', '-Wfunction-effects'),
            encoding='utf-8',
        )
        print('Patched -Werror=function-effects -> warning.', flush=True)


def _fetch_checkout(root: Path) -> Path:
    """Download + extract the pinned OpenAL Soft source tarball into ``root``.

    ``root`` is wiped fresh by the caller every run (see ``_do_build``), so
    there's no reuse path: we always download (the tarball is tiny and
    extraction is instant -- the slice compiles dominate, and they re-run every
    build regardless), which keeps the build trivially correct across version
    bumps.
    """
    tarball = root / f'openal-soft-{OPENAL_SOFT_TAG}.tar.gz'
    print(f'Downloading {OPENAL_SOFT_TARBALL} ...', flush=True)
    tmp = tarball.with_suffix('.tmp')
    with urllib.request.urlopen(OPENAL_SOFT_TARBALL) as resp:
        tmp.write_bytes(resp.read())
    tmp.rename(tarball)

    print(f'Extracting {tarball.name} ...', flush=True)
    extract_root = root / 'extract'
    extract_root.mkdir(parents=True)
    with tarfile.open(tarball, 'r:gz') as tar:
        tar.extractall(extract_root, filter='data')
    # The tarball extracts to a single top-level 'openal-soft-<tag>' dir.
    checkout = root / 'checkout'
    inner = next(extract_root.iterdir())
    inner.rename(checkout)
    shutil.rmtree(extract_root)
    if not (checkout / 'CMakeLists.txt').exists():
        raise RuntimeError(f'Extracted checkout looks wrong: {checkout}')
    _patch_checkout(checkout)
    return checkout


def _build_slice(checkout: Path, slc: Slice) -> Path:
    """CMake-configure + build one slice; return its built shared dylib path."""
    builddir = checkout / f'build-{slc.name}'
    if builddir.exists():
        shutil.rmtree(builddir)
    builddir.mkdir(parents=True)

    print(f'\n=== Building OpenAL Soft slice: {slc.name} ===', flush=True)
    args = [
        'cmake',
        '-S',
        str(checkout),
        '-B',
        str(builddir),
        '-DCMAKE_BUILD_TYPE=RelWithDebInfo',
        '-DLIBTYPE=SHARED',
        '-DALSOFT_EXAMPLES=OFF',
        '-DALSOFT_UTILS=OFF',
        '-DALSOFT_TESTS=OFF',
        '-DALSOFT_INSTALL=OFF',
        # Disable PortAudio so homebrew include paths can't leak in and shadow
        # the bundled fmt headers; CoreAudio is the native Apple backend and is
        # always preferred anyway (and the only one on iOS/tvOS/visionOS).
        '-DALSOFT_BACKEND_PORTAUDIO=OFF',
        f'-DCMAKE_OSX_ARCHITECTURES={slc.archs}',
        f'-DCMAKE_OSX_SYSROOT={slc.sdk}',
        f'-DCMAKE_OSX_DEPLOYMENT_TARGET={slc.deployment_target}',
    ]
    if slc.system_name is not None:
        # Cross-compiling to a non-host Apple OS. CMAKE_SYSTEM_NAME triggers
        # CMake's built-in iOS/tvOS/visionOS support (needs CMake >= 3.28 for
        # visionOS; the host has 4.x).
        args.append(f'-DCMAKE_SYSTEM_NAME={slc.system_name}')
    _run(args, cwd=checkout)
    _run(['cmake', '--build', str(builddir), '-j', str(_cpus())], cwd=checkout)

    # OpenAL Soft emits libopenal.<soversion>.dylib plus an unversioned
    # symlink; grab the real (non-symlink) versioned file.
    candidates = [
        p
        for p in builddir.glob('libopenal*.dylib')
        if p.is_file() and not p.is_symlink()
    ]
    if not candidates:
        raise RuntimeError(f'No built dylib found in {builddir}')
    # Prefer the longest name (the versioned one, e.g. libopenal.1.dylib).
    return sorted(candidates, key=lambda p: len(p.name))[-1]


def _ad_hoc_sign(path: Path) -> None:
    """Ad-hoc codesign a framework (Xcode re-signs on embed; keeps it valid)."""
    _run(['codesign', '--force', '--sign', '-', str(path)], cwd=path.parent)


def _write_framework_plist(plist: Path, platform: str) -> None:
    """Write a minimal framework Info.plist."""
    plist.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n<dict>\n'
        f'  <key>CFBundleExecutable</key><string>{FRAMEWORK_NAME}</string>\n'
        f'  <key>CFBundleIdentifier</key>'
        f'<string>net.froemling.ballistica.{FRAMEWORK_NAME}</string>\n'
        '  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>\n'
        f'  <key>CFBundleName</key><string>{FRAMEWORK_NAME}</string>\n'
        '  <key>CFBundlePackageType</key><string>FMWK</string>\n'
        '  <key>CFBundleShortVersionString</key><string>1.0</string>\n'
        '  <key>CFBundleVersion</key><string>1.0</string>\n'
        '  <key>CFBundleSupportedPlatforms</key>'
        f'<array><string>{platform}</string></array>\n'
        '</dict>\n</plist>\n',
        encoding='utf-8',
    )


def _make_framework(
    dylib: Path, slc: Slice, headers: Path, dest: Path
) -> tuple[Path, Path]:
    """Wrap a built dylib into a ``.framework``; return (framework, dSYM).

    macOS uses a *deep* (versioned) bundle (``Versions/A/...`` + symlinks),
    which Xcode's embed-frameworks validation requires on macOS; iOS / tvOS /
    visionOS use the flat/shallow layout.
    """
    install_id = f'@rpath/{FRAMEWORK_NAME}.framework/{FRAMEWORK_NAME}'
    framework = dest / f'{FRAMEWORK_NAME}.framework'
    if framework.exists():
        shutil.rmtree(framework)

    if slc.versioned:
        versions_a = framework / 'Versions' / 'A'
        (versions_a / 'Resources').mkdir(parents=True)
        binary = versions_a / FRAMEWORK_NAME
        shutil.copy(dylib, binary)
        shutil.copytree(headers, versions_a / 'Headers')
        _write_framework_plist(
            versions_a / 'Resources' / 'Info.plist', 'MacOSX'
        )
        (framework / 'Versions' / 'Current').symlink_to('A')
        (framework / FRAMEWORK_NAME).symlink_to(
            f'Versions/Current/{FRAMEWORK_NAME}'
        )
        (framework / 'Resources').symlink_to('Versions/Current/Resources')
        (framework / 'Headers').symlink_to('Versions/Current/Headers')
    else:
        framework.mkdir(parents=True)
        binary = framework / FRAMEWORK_NAME
        shutil.copy(dylib, binary)
        shutil.copytree(headers, framework / 'Headers')
        _write_framework_plist(framework / 'Info.plist', _sdk_platform(slc.sdk))

    _run(['install_name_tool', '-id', install_id, str(binary)], cwd=dest)
    # Extract a dSYM from the (post-rename) binary before signing.
    dsym = dest / f'{FRAMEWORK_NAME}.dSYM'
    if dsym.exists():
        shutil.rmtree(dsym)
    _run(['dsymutil', str(binary), '-o', str(dsym)], cwd=dest)
    _ad_hoc_sign(framework)
    return framework, dsym


def _sdk_platform(sdk: str) -> str:
    """Map an SDK name to a CFBundleSupportedPlatforms value."""
    return {
        'iphoneos': 'iPhoneOS',
        'iphonesimulator': 'iPhoneSimulator',
        'appletvos': 'AppleTVOS',
        'appletvsimulator': 'AppleTVSimulator',
        'xros': 'XROS',
        'xrsimulator': 'XRSimulator',
    }[sdk]


def _stage_headers(checkout: Path, dest: Path) -> Path:
    """Stage the shared OpenAL headers (identical across slices). Return dir."""
    src = checkout / 'include' / 'AL'
    if not src.is_dir():
        raise RuntimeError(f'OpenAL headers not found: {src}')
    include = dest / 'include'
    if include.exists():
        shutil.rmtree(include)
    (include / 'AL').mkdir(parents=True)
    shutil.copytree(src, include / 'AL', dirs_exist_ok=True)
    return include / 'AL'


def _do_build(projroot: str) -> None:
    """Build every slice from scratch and assemble the artifacts dir.

    Wipes the entire ``build/openal-apple/`` state dir up front so every run is
    a clean, self-contained build -- no stale source, tarball, or staged output
    can survive a version bump or interrupted run. (Unlike the ANGLE build,
    there's nothing worth caching here: the tarball is tiny and the per-slice
    CMake compiles -- the only real cost -- re-run every build regardless.)
    """
    root = Path(projroot) / STATE_SUBDIR
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    checkout = _fetch_checkout(root)

    artifacts = root / 'artifacts'
    artifacts.mkdir(parents=True)

    # Shared headers (used by both the framework Headers dirs and staged
    # standalone for consumers' header search paths).
    headers = _stage_headers(checkout, artifacts)

    work = root / 'assembly'
    work.mkdir(parents=True)

    # Build each slice and wrap it into a framework, accumulating the
    # create-xcframework args.
    create_args: list[str] = ['xcodebuild', '-create-xcframework']
    for slc in SLICES:
        dylib = _build_slice(checkout, slc)
        gdir = work / slc.name
        gdir.mkdir(parents=True, exist_ok=True)
        framework, dsym = _make_framework(dylib, slc, headers, gdir)
        create_args += ['-framework', str(framework)]
        create_args += ['-debug-symbols', str(dsym)]

    out_path = artifacts / f'{FRAMEWORK_NAME}.xcframework'
    create_args += ['-output', str(out_path)]
    _run(create_args, cwd=artifacts)

    print(f'\nDone. Artifacts staged to: {artifacts}', flush=True)


def build(projroot: str) -> None:
    """Build all Apple OpenAL Soft slices from scratch.

    Downloads OpenAL Soft at the pinned tag and builds every slice, assembling
    ``OpenALSoft.xcframework`` + headers into ``build/openal-apple/artifacts``.
    Follow with ``make openal-apple-gather`` to install into the source tree.
    """
    _do_build(projroot)


def test_build(projroot: str) -> None:
    """Alias for :func:`build` -- a CI-canary entry point.

    Identical to ``build`` (kept as a separate name mirroring the ANGLE
    ``*-test-*`` CI targets). OpenAL's build is cheap enough that there's no
    separate lazy/incremental variant.
    """
    _do_build(projroot)


def gather(projroot: str) -> None:
    """Install assembled artifacts into ``src/external/openal-apple``.

    Installs the ``OpenALSoft.xcframework`` (macOS/iOS/tvOS/visionOS framework
    slices) and the shared ``include/AL`` header tree.
    """
    root = Path(projroot)
    artifacts = root / STATE_SUBDIR / 'artifacts'
    if not artifacts.is_dir():
        raise CleanError(
            f"Artifacts dir not found: '{artifacts}'."
            ' Run make openal-apple-build or openal-apple-test-build first.'
        )

    dst = root / 'src' / 'external' / 'openal-apple'

    def _install(src: Path, dest: Path) -> None:
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        # symlinks=True preserves the macOS versioned-framework symlinks (and
        # the bare-dylib soname symlinks); dereferencing them yields a malformed
        # bundle Xcode can't re-sign on embed.
        shutil.copytree(src, dest, symlinks=True)
        print(f'Installed: {dest}')

    _install(
        artifacts / f'{FRAMEWORK_NAME}.xcframework',
        dst / f'{FRAMEWORK_NAME}.xcframework',
    )
    _install(artifacts / 'include', dst / 'include')
