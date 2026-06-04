# Released under the MIT License. See LICENSE for details.
"""Build ANGLE OpenGL ES libraries for Apple platforms via vcpkg.

The Apple analog of ``tools/batools/buildanglewindows.ps1``. Builds ANGLE (with
the Metal backend) via vcpkg for the Apple triplets, assembles the
per-platform/arch dylibs into xcframeworks (``libEGL.xcframework`` and
``libGLESv2.xcframework``) plus a shared header tree, and stages everything
to ``build/angle-artifacts/`` for pickup by ``gather()`` (which installs
them into ``src/external/angle-apple/``).

This is a self-contained local build: it clones and bootstraps a throwaway
vcpkg and shells out to xcodebuild/lipo/install_name_tool/codesign, so it
expects a full Xcode + command-line-tools host. Drive it via
``make angle-apple-build-local`` (build) and ``make angle-apple-gather``
(install).

iOS note: vcpkg's ``angle`` port only selects the Metal ("Mac") buildsystem
for ``VCPKG_TARGET_IS_OSX``; iOS triplets fall through to the desktop-GL
("Linux") config and do not build a usable Metal library. So only the macOS
triplets are built by default. The xcframework assembly here is written to
accept additional slice groups (``ios``/``ios-sim``) the moment a working
iOS build exists (a patched port or a native gn build) -- pass
``include_ios=True`` to attempt them once that lands.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass

VCPKG_REPO = 'https://github.com/microsoft/vcpkg.git'

# ANGLE's two shipped dynamic libraries (our final/standard names).
LIBS = ['libEGL', 'libGLESv2']

# vcpkg's ANGLE buildsystem emits dylibs with this 'liblib..._angle' naming;
# map our standard output name to the file it actually produces.
SOURCE_DYLIB = {
    'libEGL': 'liblibEGL_angle.dylib',
    'libGLESv2': 'liblibGLESv2_angle.dylib',
}

# Load-command rewrites applied to every assembled dylib. ANGLE's internal
# 'liblib..._angle' dylib names get normalized to the standard libEGL/libGLESv2
# names (so SDL's ES-driver and the engine resolve them), and ANGLE's
# vcpkg-built zlib dependency is repointed to the always-present system zlib --
# avoids bundling a third dylib, and zlib's basic ABI is stable across
# versions. (If a zlib version issue ever surfaces, bundle the vcpkg-built
# libz.1.3.2.dylib instead.)
RENAME_MAP = {
    '@rpath/liblibEGL_angle.dylib': '@rpath/libEGL.dylib',
    '@rpath/liblibGLESv2_angle.dylib': '@rpath/libGLESv2.dylib',
    '@rpath/libz.1.3.2.dylib': '/usr/lib/libz.1.dylib',
}

# Public header dirs (identical across all triplets).
HEADER_DIRS = ['EGL', 'GLES2', 'GLES3', 'KHR']


@dataclass(frozen=True)
class BuildTriplet:
    """A vcpkg triplet we build and how it slots into the xcframeworks.

    ``group`` is the xcframework slice it contributes to; all triplets in a
    group are lipo-merged into one fat dylib for that slice.
    """

    name: str  # Overlay triplet name, e.g. 'arm64-osx-dynamic'.
    group: str  # Xcframework slice group: 'macos' / 'ios' / 'ios-sim'.
    arch: str  # VCPKG_TARGET_ARCHITECTURE: 'arm64' / 'x64'.
    cmake_system: str  # VCPKG_CMAKE_SYSTEM_NAME: 'Darwin' / 'iOS'.
    osx_arch: str  # VCPKG_OSX_ARCHITECTURES: 'arm64' / 'x86_64'.
    sysroot: str | None  # VCPKG_OSX_SYSROOT: None / 'iphoneos' / etc.


# macOS slices: a universal (arm64 + x86_64) fat dylib.
MACOS_TRIPLETS = [
    BuildTriplet(
        name='arm64-osx-dynamic',
        group='macos',
        arch='arm64',
        cmake_system='Darwin',
        osx_arch='arm64',
        sysroot=None,
    ),
    BuildTriplet(
        name='x64-osx-dynamic',
        group='macos',
        arch='x64',
        cmake_system='Darwin',
        osx_arch='x86_64',
        sysroot=None,
    ),
]

# iOS slices: device (arm64) + simulator (arm64). Not built by default; see
# the iOS note in the module docstring.
IOS_TRIPLETS = [
    BuildTriplet(
        name='arm64-ios-dynamic',
        group='ios',
        arch='arm64',
        cmake_system='iOS',
        osx_arch='arm64',
        sysroot='iphoneos',
    ),
    BuildTriplet(
        name='arm64-ios-simulator-dynamic',
        group='ios-sim',
        arch='arm64',
        cmake_system='iOS',
        osx_arch='arm64',
        sysroot='iphonesimulator',
    ),
]


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a command, echoing it, and raise on failure."""
    joined = ' '.join(cmd)
    print(f'+ {joined}', flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def _triplet_cmake(triplet: BuildTriplet) -> str:
    """Generate the overlay-triplet .cmake contents for a triplet."""
    lines = [
        f'set(VCPKG_TARGET_ARCHITECTURE {triplet.arch})',
        'set(VCPKG_CRT_LINKAGE dynamic)',
        'set(VCPKG_LIBRARY_LINKAGE dynamic)',
        # Release-only; we never ship a debug ANGLE and it ~halves build time.
        'set(VCPKG_BUILD_TYPE release)',
        f'set(VCPKG_CMAKE_SYSTEM_NAME {triplet.cmake_system})',
        f'set(VCPKG_OSX_ARCHITECTURES {triplet.osx_arch})',
    ]
    if triplet.sysroot is not None:
        lines.append(f'set(VCPKG_OSX_SYSROOT {triplet.sysroot})')
    return '\n'.join(lines) + '\n'


def _bootstrap_vcpkg(vcpkg_dir: Path) -> Path:
    """Clone and bootstrap a throwaway vcpkg; return the vcpkg executable."""
    _run(['git', 'clone', '--depth', '1', VCPKG_REPO, str(vcpkg_dir)])
    _run([str(vcpkg_dir / 'bootstrap-vcpkg.sh'), '-disableMetrics'])
    return vcpkg_dir / 'vcpkg'


def _build_triplet(
    vcpkg: Path, triplet_dir: Path, triplet: BuildTriplet
) -> Path:
    """Build ANGLE for one triplet; return its vcpkg install dir."""
    (triplet_dir / f'{triplet.name}.cmake').write_text(
        _triplet_cmake(triplet), encoding='utf-8'
    )
    print(f'\n=== Building ANGLE for {triplet.name} ===\n', flush=True)
    _run(
        [
            str(vcpkg),
            'install',
            f'angle[metal]:{triplet.name}',
            f'--overlay-triplets={triplet_dir}',
            '--no-binarycaching',
            '--clean-buildtrees-after-build',
            '--clean-packages-after-build',
        ]
    )
    install_dir = vcpkg.parent / 'installed' / triplet.name
    if not install_dir.is_dir():
        raise RuntimeError(f'Expected install dir not found: {install_dir}')
    return install_dir


def _finalize_dylib(dylib: Path, lib: str) -> None:
    """Normalize a dylib's load commands and ad-hoc re-sign it.

    Sets the dylib id to the standard ``@rpath/{lib}.dylib`` and rewrites
    ANGLE's internal dylib references + its zlib dependency (see RENAME_MAP)
    so the dylibs are relocatable and resolve their siblings via @rpath. The
    install_name_tool edits invalidate the linker's signature, so we re-sign
    ad-hoc -- required for modified dylibs to load on Apple Silicon.
    """
    _run(['install_name_tool', '-id', f'@rpath/{lib}.dylib', str(dylib)])
    out = subprocess.run(
        ['otool', '-L', str(dylib)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for line in out.splitlines():
        dep = line.strip().split(' ')[0]
        new = RENAME_MAP.get(dep)
        if new is not None:
            _run(['install_name_tool', '-change', dep, new, str(dylib)])
    _run(['codesign', '--force', '--sign', '-', str(dylib)])


def _assemble_slice(install_dirs: list[Path], lib: str, out_dir: Path) -> Path:
    """lipo-merge a group's per-arch dylibs into one finalized fat dylib.

    Returns the path to the merged dylib (renamed to the standard
    ``{lib}.dylib`` and made relocatable).
    """
    sources = [d / 'lib' / SOURCE_DYLIB[lib] for d in install_dirs]
    for src in sources:
        if not src.is_file():
            raise RuntimeError(f'Expected dylib not found: {src}')
    out_dir.mkdir(parents=True, exist_ok=True)
    merged = out_dir / f'{lib}.dylib'
    if len(sources) == 1:
        shutil.copy2(sources[0], merged)
    else:
        _run(
            ['lipo', '-create', '-output', str(merged)]
            + [str(s) for s in sources]
        )
    # copy2 preserves the read-only-ish source mode; ensure writable for
    # install_name_tool.
    merged.chmod(0o755)
    _finalize_dylib(merged, lib)
    return merged


def _make_xcframework(
    lib: str, slice_dylibs: list[Path], staging: Path
) -> None:
    """Build one header-less xcframework from a lib's per-group dylibs."""
    out = staging / f'{lib}.xcframework'
    if out.exists():
        shutil.rmtree(out)
    cmd = ['xcodebuild', '-create-xcframework']
    for dylib in slice_dylibs:
        cmd += ['-library', str(dylib)]
    cmd += ['-output', str(out)]
    _run(cmd)
    print(f'  Created {out.name}', flush=True)


def _stage_headers(install_dir: Path, staging: Path) -> None:
    """Stage the shared GLES/EGL headers (identical across triplets)."""
    for hdir in HEADER_DIRS:
        src = install_dir / 'include' / hdir
        if not src.is_dir():
            raise RuntimeError(f'Expected header dir not found: {src}')
        dst = staging / 'include' / hdir
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f'  Staged headers: {hdir}', flush=True)


def _build_all(triplets: list[BuildTriplet], repo_root: Path) -> None:
    """Build all triplets and assemble the staged xcframeworks."""
    staging = repo_root / 'build' / 'angle-artifacts'
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    # Short temp root to keep vcpkg's deep paths sane.
    temp_base = Path(repo_root / 'build' / 'angle-apple-temp')
    if temp_base.exists():
        shutil.rmtree(temp_base)
    temp_base.mkdir(parents=True)
    triplet_dir = temp_base / 'overlay-triplets'
    triplet_dir.mkdir()

    vcpkg = _bootstrap_vcpkg(temp_base / 'vcpkg')

    # Build every requested triplet.
    install_dirs: dict[str, Path] = {}
    for triplet in triplets:
        install_dirs[triplet.name] = _build_triplet(vcpkg, triplet_dir, triplet)

    # Headers are identical across triplets; stage from any one.
    _stage_headers(next(iter(install_dirs.values())), staging)

    # Group triplets into xcframework slices (preserving order).
    groups: dict[str, list[Path]] = {}
    for triplet in triplets:
        groups.setdefault(triplet.group, []).append(install_dirs[triplet.name])

    # For each lib, build one fat dylib per group, then one xcframework.
    slices_dir = temp_base / 'slices'
    for lib in LIBS:
        slice_dylibs = [
            _assemble_slice(dirs, lib, slices_dir / group)
            for group, dirs in groups.items()
        ]
        _make_xcframework(lib, slice_dylibs, staging)

    print(f'\nANGLE artifacts staged to: {staging}\n', flush=True)


def build(
    projroot: str, *, include_ios: bool = False, triplets: str | None = None
) -> None:
    """Build the requested triplets and stage their xcframeworks.

    ``include_ios`` adds the (not-yet-usable) iOS triplets; ``triplets`` is
    an optional comma-separated subset of overlay-triplet names to limit the
    build to (for testing).
    """
    from efro.error import CleanError

    selected = list(MACOS_TRIPLETS)
    if include_ios:
        selected += IOS_TRIPLETS
    if triplets:
        wanted = set(triplets.split(','))
        selected = [t for t in selected if t.name in wanted]
        if not selected:
            raise CleanError(f'No triplets matched: {triplets}')

    _build_all(selected, Path(projroot))


def gather(projroot: str) -> None:
    """Install staged ANGLE artifacts into the source tree.

    Copies the headers and xcframeworks staged under ``build/angle-artifacts``
    into ``src/external/angle-apple/`` where the cmake build picks them up.
    """
    from efro.error import CleanError

    root = Path(projroot)
    staging = root / 'build' / 'angle-artifacts'
    dst_root = root / 'src' / 'external' / 'angle-apple'

    if not staging.is_dir():
        raise CleanError(
            f"Staging dir not found: '{staging}'."
            ' Run make angle-apple-build-local first.'
        )

    # Install shared headers.
    for hdir in HEADER_DIRS:
        src = staging / 'include' / hdir
        dst = dst_root / 'include' / hdir
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst)
            print(f'Installed headers: {dst}')

    # Install xcframeworks (whole-dir replace).
    for lib in LIBS:
        fwk = f'{lib}.xcframework'
        src = staging / fwk
        dst = dst_root / fwk
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            dst_root.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst)
            print(f'Installed: {dst}')
