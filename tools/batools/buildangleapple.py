# Released under the MIT License. See LICENSE for details.
"""Build ANGLE (GL ES -> Metal) xcframeworks for Apple platforms via gn.

Uses ANGLE's native gn/depot_tools build (not vcpkg, which can only target
macOS) to build ANGLE for macOS, iOS, and tvOS. The iOS/tvOS slices are
assembled into ``.framework``-based xcframeworks (``libEGL.xcframework`` /
``libGLESv2.xcframework``); macOS ships as bare ``libEGL.dylib`` /
``libGLESv2.dylib`` (its consumers load ANGLE as bare dylibs, not frameworks).
Plus a shared header tree.

Self-containment is the whole point of this module: **everything** it creates
lives under ``build/angle-apple/`` and **all** PATH/environment mutations are
scoped to the subprocesses it spawns. It never modifies the user's shell, never
writes outside ``build/``, and redirects depot_tools' normally-global caches
(vpython virtualenvs, cipd packages) into the build dir too. Remove
``build/angle-apple/`` to fully clean up -- nothing else is left behind.

Layout under ``build/angle-apple/``:

- ``depot_tools/`` -- throwaway depot_tools clone (hermetic clang/gn/ninja);
- ``cache/`` -- depot_tools' redirected vpython/cipd caches;
- ``checkout/`` -- the ANGLE gclient checkout (source + toolchain), with
  per-slice gn builds under ``checkout/out/<variant>/<slice>``;
- ``artifacts/`` -- the assembled xcframeworks + headers that ``gather`` reads.

Two entry points build into the *same* ``artifacts/`` dir so ``gather`` is
agnostic to which produced them (and we never keep two multi-GB checkouts):

- :func:`test_build` -- lazy (reuses an existing checkout, incremental); builds
  every Apple platform at the cheap ``test`` variant + the macOS
  ``debug`` (validation) variant. For CI / exercising the pipeline; optimization
  doesn't matter.
- :func:`build` -- always from scratch; builds the shipping ``release`` variant
  (``is_official_build`` -> ThinLTO + auto-strip + dSYMs) + the macOS ``debug``
  variant.

The debug/validation variant produces only bare macOS dylibs (no xcframework --
its sole consumer is the macOS cmake build, which loads ANGLE as bare dylibs;
see :func:`!_macos_bare_dylibs`). :func:`gather` installs the xcframeworks +
release macOS dylibs to ``src/external/angle-apple`` and the debug macOS dylibs
to ``src/external/angle-apple-debug``.

depot_tools fetches a hermetic clang/gn/ninja, so the only host prerequisites
are a full Xcode install and a system git -- nothing is installed system-wide.
"""

import os
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass

DEPOT_TOOLS_REPO = (
    'https://chromium.googlesource.com/chromium/tools/depot_tools.git'
)

# The two shipped libraries (gn target names + dylib/framework stems).
LIBS = ['libEGL', 'libGLESv2']

# Public header dirs (identical across all slices; staged once).
HEADER_DIRS = ['EGL', 'GLES2', 'GLES3', 'KHR']

# Where, relative to the repo root, all of our state lives.
STATE_SUBDIR = Path('build') / 'angle-apple'


@dataclass(frozen=True)
class Slice:
    """One (os, cpu, environment, platform) combination we build via gn.

    ``group`` is the xcframework slice it contributes to: all slices in a group
    are lipo-merged into one fat framework for that slice (only ``macos`` has
    >1, merging arm64 + x86_64).
    """

    name: str  # out subdir + label, e.g. 'macos-arm64'.
    group: str  # 'macos' / 'ios' / 'ios-sim' / 'tvos' / 'tvos-sim'.
    target_os: str  # gn target_os: 'mac' / 'ios'.
    target_cpu: str  # gn target_cpu: 'arm64' / 'x64'.
    target_environment: str | None  # 'device' / 'simulator' / None (macos).
    # gn target_platform: 'tvos' for tvOS (rides the iOS toolchain), else None.
    target_platform: str | None = None


# macOS slices -- lipo-merged into the universal bare dylibs (libEGL.dylib +
# libGLESv2.dylib). macOS consumers (the macOS Xcode build + the desktop/SDL
# cmake build) load ANGLE as bare dylibs, so macOS is NOT in the xcframeworks.
# Built at the normal variant (release/test dylibs) and at 'debug' (validation
# dylibs).
MACOS_SLICES = [
    Slice('macos-arm64', 'macos', 'mac', 'arm64', None),
    Slice('macos-x64', 'macos', 'mac', 'x64', None),
]

# Framework-form slices for the xcframeworks: iOS + tvOS (device + sim). The
# xcframeworks' only consumers are the iOS/tvOS Xcode builds.
XCFRAMEWORK_SLICES = [
    Slice('ios-device', 'ios', 'ios', 'arm64', 'device'),
    Slice('ios-sim', 'ios-sim', 'ios', 'arm64', 'simulator'),
    Slice('tvos-device', 'tvos', 'ios', 'arm64', 'device', 'tvos'),
    Slice('tvos-sim', 'tvos-sim', 'ios', 'arm64', 'simulator', 'tvos'),
]


def _run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    """Run a command, echoing it, and raise on failure."""
    joined = ' '.join(cmd)
    print(f'\n+ {joined}  (cwd={cwd})', flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f'Command failed (code {proc.returncode}): {joined}')


def _base_env() -> dict[str, str]:
    """Environment copy with our hermetic-git tweak applied.

    Empties GIT_TEMPLATE_DIR so git never copies the host's hook templates into
    the checkouts we create (keeps trees host-hook-free and avoids the copy).
    """
    env = dict(os.environ)
    env['GIT_TEMPLATE_DIR'] = ''
    return env


def _scoped_env(root: Path, depot_tools: Path) -> dict[str, str]:
    """The environment for every depot_tools/gn/ninja subprocess.

    Prepends our throwaway depot_tools to PATH and redirects depot_tools'
    otherwise-global caches into the build dir, so nothing leaks outside
    ``build/angle-apple/`` or persists in the user's shell.
    """
    env = _base_env()
    env['PATH'] = os.pathsep.join([str(depot_tools), env.get('PATH', '')])
    # Pin depot_tools (no self-update mid-build) and opt out of metrics.
    env['DEPOT_TOOLS_UPDATE'] = '0'
    env['DEPOT_TOOLS_METRICS'] = '0'
    cache = root / 'cache'
    env['VPYTHON_VIRTUALENV_ROOT'] = str(cache / 'vpython')
    env['CIPD_CACHE_DIR'] = str(cache / 'cipd')
    return env


def _ensure_depot_tools(root: Path, base_env: dict[str, str]) -> Path:
    """Clone the throwaway depot_tools if not already present."""
    depot_tools = root / 'depot_tools'
    if (depot_tools / 'gclient').exists():
        print(f'Using existing depot_tools at {depot_tools}.', flush=True)
        return depot_tools
    _run(
        ['git', 'clone', '--depth', '1', DEPOT_TOOLS_REPO, str(depot_tools)],
        cwd=root,
        env=base_env,
    )
    return depot_tools


def _bootstrap_depot_tools(depot_tools: Path, env: dict[str, str]) -> None:
    """Ensure depot_tools' bundled python/cipd tools are downloaded.

    The gn/autoninja wrappers need depot_tools' own ``python-bin/python3``
    (recorded in ``python3_bin_reldir.txt``). A first gclient run normally
    bootstraps it, but our ``DEPOT_TOOLS_UPDATE=0`` (to keep depot_tools pinned)
    suppresses that, so we run ``ensure_bootstrap`` explicitly. It honors the
    current checkout (no git self-update) and is a no-op once bootstrapped.
    """
    if (depot_tools / 'python3_bin_reldir.txt').exists():
        return
    _run([str(depot_tools / 'ensure_bootstrap')], cwd=depot_tools, env=env)


def _ensure_target_os(gclient_file: Path) -> None:
    """Ensure the .gclient solution pulls deps for mac + ios (covers tvOS)."""
    text = gclient_file.read_text(encoding='utf-8')
    if 'target_os' in text:
        return  # Assume a prior run already set this up.
    gclient_file.write_text(
        text.rstrip() + "\ntarget_os = ['mac', 'ios']\n", encoding='utf-8'
    )
    print("Set target_os = ['mac', 'ios'] in .gclient.", flush=True)


def _apply_local_patches(checkout: Path) -> None:
    """Apply our durable local patches to the freshly-synced checkout.

    These are wiped by ``gclient sync`` (they live in the checkout), so we
    re-apply after every sync. Idempotent.

    tvOS: Chromium asserts ``tvos`` builds require ``use_blink`` (its only tvOS
    consumer is Blink/content_shell); we build standalone libs, so comment out
    that one sanity assert. It gates nothing else.
    """
    mobile_config = (
        checkout / 'build' / 'config' / 'apple' / 'mobile_config.gni'
    )
    assert_line = '    assert(use_blink, "tvOS builds require use_blink=true")'
    patched_line = (
        '    # ballistica: patched out -- standalone libs, not Blink.\n'
        '    # assert(use_blink, "tvOS builds require use_blink=true")'
    )
    text = mobile_config.read_text(encoding='utf-8')
    if assert_line in text:
        mobile_config.write_text(
            text.replace(assert_line, patched_line), encoding='utf-8'
        )
        print('Applied tvOS use_blink patch to mobile_config.gni.', flush=True)


def _sync_angle(checkout: Path, env: dict[str, str]) -> None:
    """Fetch + sync the ANGLE checkout into ``checkout``, then patch it.

    ANGLE's fetch recipe uses gclient solution name '.', so it checks out
    directly into the cwd; we run it inside ``checkout`` so the ANGLE source
    root *is* ``checkout`` (kept separate from depot_tools + caches one level
    up, which a ``gclient sync -D`` would otherwise treat as stale deps -- we
    also drop ``-D`` for that reason).
    """
    checkout.mkdir(parents=True, exist_ok=True)
    gclient_file = checkout / '.gclient'
    if not gclient_file.exists():
        # 'fetch' creates .gclient + checks ANGLE out into the cwd. --nohooks
        # so we can inject target_os before the heavy hook/dep download.
        _run(['fetch', '--nohooks', 'angle'], cwd=checkout, env=env)
    _ensure_target_os(gclient_file)
    # --reset discards local modifications in the managed deps before syncing.
    # We deliberately patch one dep (build/config/apple/mobile_config.gni, the
    # tvOS use_blink assert -- see _apply_local_patches), which leaves that dep
    # 'dirty'; without --reset the *next* (incremental) sync refuses with "you
    # have uncommitted changes". --reset reverts it so sync proceeds, then we
    # re-apply the patch below. (Our depot_tools + caches live outside the
    # checkout, so they're untouched.)
    _run(['gclient', 'sync', '--reset'], cwd=checkout, env=env)
    if not (checkout / 'BUILD.gn').is_file():
        raise RuntimeError(
            f'ANGLE checkout looks wrong (no BUILD.gn): {checkout}'
        )
    _apply_local_patches(checkout)


def _variant_gn_args(variant: str) -> list[str]:
    """gn args selecting the build flavor (test / release / debug)."""
    # Common: Metal-only -- trim every other backend so we don't build or ship
    # Vulkan/GL/Null and, crucially, the WebGPU (Dawn) backend, which otherwise
    # data-depends SwiftShader (a CPU-Vulkan impl) and drags ~2400 extra build
    # steps + ~14MB of unused code into libGLESv2. Disabling wgpu cuts all of
    # that (build ~5x faster, lib ~70% smaller, still Metal-only). Plus
    # monolithic + system Xcode SDK (no Google RBE).
    args = [
        'angle_enable_metal=true',
        'angle_enable_vulkan=false',
        'angle_enable_gl=false',
        'angle_enable_null=false',
        'angle_enable_swiftshader=false',
        'angle_enable_wgpu=false',
        'is_component_build=false',
        'use_remoteexec=false',
        'ios_enable_code_signing=false',
    ]
    if variant == 'test':
        # Cheap: just needs to build + link. Optimization doesn't matter.
        args += ['is_debug=false']
    elif variant == 'release':
        # Shipping tier: is_official_build -> ThinLTO + auto-strip + dSYMs.
        # chrome_pgo_phase=0 since we have no ANGLE PGO profiles.
        args += [
            'is_debug=false',
            'is_official_build=true',
            'chrome_pgo_phase=0',
        ]
    elif variant == 'debug':
        # Diagnostic build: ANGLE asserts + debug layers (via assert_always_on)
        # + DCHECKs + GL API trace. See docs/initiatives/angle-on-apple.md.
        args += [
            'is_debug=false',
            'angle_assert_always_on=true',
            'dcheck_always_on=true',
            'angle_enable_trace=true',
        ]
    else:
        raise ValueError(f'Unknown variant: {variant}')
    return args


def _slice_gn_args(slc: Slice, variant: str) -> str:
    """Assemble the full --args string for one slice + variant."""
    args = [
        f'target_os="{slc.target_os}"',
        f'target_cpu="{slc.target_cpu}"',
    ]
    if slc.target_environment is not None:
        args.append(f'target_environment="{slc.target_environment}"')
    if slc.target_platform is not None:
        args.append(f'target_platform="{slc.target_platform}"')
    args += _variant_gn_args(variant)
    return ' '.join(args)


def _build_slice(
    angle: Path, slc: Slice, variant: str, env: dict[str, str]
) -> Path:
    """gn-gen + autoninja one slice; return its out dir."""
    out = angle / 'out' / variant / slc.name
    print(f'\n=== Building ANGLE {slc.name} ({variant}) ===', flush=True)
    _run(
        ['gn', 'gen', str(out), '--args=' + _slice_gn_args(slc, variant)],
        cwd=angle,
        env=env,
    )
    _run(['autoninja', '-C', str(out)] + LIBS, cwd=angle, env=env)
    return out


def _ad_hoc_sign(path: Path, env: dict[str, str]) -> None:
    """Ad-hoc codesign a framework binary (required to load after edits)."""
    _run(
        ['codesign', '--force', '--sign', '-', str(path)],
        cwd=path.parent,
        env=env,
    )


def _write_framework_plist(plist: Path, lib: str, platform: str) -> None:
    """Write a minimal framework Info.plist."""
    plist.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n<dict>\n'
        f'  <key>CFBundleExecutable</key><string>{lib}</string>\n'
        f'  <key>CFBundleIdentifier</key>'
        f'<string>net.froemling.ballistica.{lib}</string>\n'
        '  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>\n'
        f'  <key>CFBundleName</key><string>{lib}</string>\n'
        '  <key>CFBundlePackageType</key><string>FMWK</string>\n'
        '  <key>CFBundleShortVersionString</key><string>1.0</string>\n'
        '  <key>CFBundleVersion</key><string>1.0</string>\n'
        '  <key>CFBundleSupportedPlatforms</key>'
        f'<array><string>{platform}</string></array>\n'
        '</dict>\n</plist>\n',
        encoding='utf-8',
    )


def _macos_framework(
    dylibs: list[Path], lib: str, dest: Path, env: dict[str, str]
) -> Path:
    """lipo per-arch macOS dylibs into one universal versioned ``.framework``.

    macOS uses *deep* (versioned) framework bundles -- ``Versions/A/<lib>`` +
    ``Versions/A/Resources/Info.plist`` with ``Current`` and top-level symlinks
    -- NOT the flat/shallow layout iOS and tvOS use. Xcode's embed-frameworks
    validation rejects a shallow framework on macOS ("expected
    Versions/Current/Resources/Info.plist"), so emit the versioned layout. The
    binary lives at ``Versions/A/<lib>``; consumers that want a bare dylib (the
    cmake/SDL build) resolve the top-level ``<lib>`` symlink.
    """
    framework = dest / f'{lib}.framework'
    if framework.exists():
        shutil.rmtree(framework)
    versions_a = framework / 'Versions' / 'A'
    (versions_a / 'Resources').mkdir(parents=True)
    binary = versions_a / lib
    _run(
        ['lipo', '-create', '-output', str(binary)] + [str(d) for d in dylibs],
        cwd=dest,
        env=env,
    )
    _write_framework_plist(
        versions_a / 'Resources' / 'Info.plist', lib, 'MacOSX'
    )
    # Versioned-bundle symlinks (relative).
    (framework / 'Versions' / 'Current').symlink_to('A')
    (framework / lib).symlink_to(f'Versions/Current/{lib}')
    (framework / 'Resources').symlink_to('Versions/Current/Resources')
    # Use the top-level symlink path as the install_name (dyld follows it to
    # Versions/A). It's shorter than the full Versions/A path, which matters:
    # the gn build doesn't pad load commands (-headerpad_max_install_names), so
    # the longer path doesn't fit the x86_64 slice's LC_ID_DYLIB.
    _run(
        [
            'install_name_tool',
            '-id',
            f'@rpath/{lib}.framework/{lib}',
            str(binary),
        ],
        cwd=dest,
        env=env,
    )
    # Sign the bundle (puts _CodeSignature under Versions/A); Xcode re-signs on
    # embed anyway, but this keeps the vendored framework valid.
    _ad_hoc_sign(framework, env)
    return framework


def _macos_bare_dylibs(
    angle: Path, variant: str, dest: Path, env: dict[str, str]
) -> None:
    """Emit bare universal macOS dylibs (libEGL.dylib + libGLESv2.dylib).

    macOS ANGLE is *not* framework-based the way iOS/tvOS are: libEGL's loader
    dlopens ``libGLESv2.dylib`` from its own directory (SearchType::ModuleDir),
    so consumers that don't take the iOS framework path -- the cmake/SDL build
    and the macOS Xcode targets -- link these as sibling dylibs with
    ``@rpath/<lib>.dylib`` ids (loaded/embedded like any other dylib). Universal
    arm64 + x86_64; ad-hoc signed (re-signed on embed by Xcode).
    """
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for lib in LIBS:
        dylibs = [
            angle / 'out' / variant / 'macos-arm64' / f'{lib}.dylib',
            angle / 'out' / variant / 'macos-x64' / f'{lib}.dylib',
        ]
        binary = dest / f'{lib}.dylib'
        _run(
            ['lipo', '-create', '-output', str(binary)]
            + [str(d) for d in dylibs],
            cwd=dest,
            env=env,
        )
        _run(
            ['install_name_tool', '-id', f'@rpath/{lib}.dylib', str(binary)],
            cwd=dest,
            env=env,
        )
        _ad_hoc_sign(binary, env)
    print(f'  Created bare macOS dylibs in {dest.name}', flush=True)


def _copied_framework(
    src_framework: Path, lib: str, dest: Path, env: dict[str, str]
) -> Path:
    """Copy an iOS/tvOS framework as-is (id already correct) and re-sign it."""
    framework = dest / f'{lib}.framework'
    if framework.exists():
        shutil.rmtree(framework)
    shutil.copytree(src_framework, framework)
    _ad_hoc_sign(framework / lib, env)
    return framework


def _collect_dsym(out_dir: Path, lib: str) -> Path | None:
    """Return a slice's .dSYM if the build produced one (release only)."""
    candidates = sorted(out_dir.glob(f'{lib}*.dSYM'))
    return candidates[0] if candidates else None


def _macos_universal_dsym(
    out_dirs: list[Path], lib: str, dest: Path, env: dict[str, str]
) -> Path | None:
    """Build a universal macOS .dSYM by lipo-merging the per-arch dSYMs.

    The macOS xcframework slice is a universal (arm64 + x86_64) binary, so its
    dSYM must cover both arches; gn emits one dSYM per arch, so we lipo their
    inner DWARF binaries together (UUIDs are preserved by lipo +
    install_name_tool, so the merged dSYM matches the universal framework).
    Returns None if no dSYMs exist (e.g. the 'test' variant doesn't emit them).
    """
    src_dsyms = [d for d in (_collect_dsym(o, lib) for o in out_dirs) if d]
    if not src_dsyms:
        return None
    merged = dest / f'{lib}.dSYM'
    if merged.exists():
        shutil.rmtree(merged)
    shutil.copytree(src_dsyms[0], merged)
    dwarf_dir = merged / 'Contents' / 'Resources' / 'DWARF'
    # The inner DWARF binary (e.g. 'libEGL.dylib') -- same name across arches.
    inner = next(dwarf_dir.iterdir()).name
    if len(src_dsyms) > 1:
        _run(
            ['lipo', '-create', '-output', str(dwarf_dir / inner)]
            + [
                str(d / 'Contents' / 'Resources' / 'DWARF' / inner)
                for d in src_dsyms
            ],
            cwd=dest,
            env=env,
        )
    return merged


def _assemble_xcframework(
    angle: Path,
    lib: str,
    slices: list[Slice],
    variant: str,
    *,
    out_path: Path,
    work: Path,
    env: dict[str, str],
) -> None:
    """Build one ``.framework``-based xcframework from a lib's slices.

    Groups slices (a ``macos`` group, if passed, has >1 and is lipo-merged;
    iOS/tvOS groups are single-slice); each group becomes one framework slice.
    dSYMs (release builds) ride inside via ``-debug-symbols``.
    """
    groups: dict[str, list[Slice]] = {}
    for slc in slices:
        groups.setdefault(slc.group, []).append(slc)

    # (framework, dsym|None) per group. dSYMs MUST be interleaved per-framework
    # below: xcodebuild's -debug-symbols attaches to the most recent -framework,
    # so emitting all -framework then all -debug-symbols piles every dSYM onto
    # the last slice and they collide ("item with the same name exists").
    pairs: list[tuple[Path, Path | None]] = []
    for group, gslices in groups.items():
        gdir = work / group
        gdir.mkdir(parents=True, exist_ok=True)
        out_dirs = [angle / 'out' / variant / s.name for s in gslices]
        if group == 'macos':
            dylibs = [d / f'{lib}.dylib' for d in out_dirs]
            framework = _macos_framework(dylibs, lib, gdir, env)
            dsym = _macos_universal_dsym(out_dirs, lib, gdir, env)
        else:
            src = out_dirs[0] / f'{lib}.framework'
            framework = _copied_framework(src, lib, gdir, env)
            dsym = _collect_dsym(out_dirs[0], lib)
        pairs.append((framework, dsym))

    if out_path.exists():
        shutil.rmtree(out_path)
    cmd = ['xcodebuild', '-create-xcframework']
    for framework, dsym in pairs:
        cmd += ['-framework', str(framework)]
        if dsym is not None:
            cmd += ['-debug-symbols', str(dsym)]
    cmd += ['-output', str(out_path)]
    _run(cmd, cwd=out_path.parent, env=env)
    print(f'  Created {out_path.name}', flush=True)


def _stage_headers(angle: Path, artifacts: Path) -> None:
    """Stage the shared GLES/EGL headers (identical across slices)."""
    # Headers live in the checkout's include/ tree.
    src_root = angle / 'include'
    dst_root = artifacts / 'include'
    for hdir in HEADER_DIRS:
        src = src_root / hdir
        if not src.is_dir():
            raise RuntimeError(f'Expected header dir not found: {src}')
        dst = dst_root / hdir
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
    print('  Staged headers: ' + ', '.join(HEADER_DIRS), flush=True)


def _do_build(
    projroot: str,
    *,
    variant: str,
    clean: bool,
    sync: bool = True,
    assemble_only: bool = False,
) -> None:
    """Shared core: set up, build all slices, assemble xcframeworks.

    ``variant`` is the flavor for the *normal* xcframeworks ('test' or
    'release'); the macOS *debug*-variant bare dylibs are always also built.

    ``sync`` controls whether the ANGLE checkout is (incrementally) re-synced
    via gclient before building; pass False to reuse an existing checkout as-is
    for fast local iteration (skips the network round-trips).

    ``assemble_only`` skips the depot_tools setup, ANGLE sync, and slice
    compiles and just (re)assembles + stages headers from the existing
    ``out/<variant>`` slices -- for iterating on assembly logic (e.g. the
    framework layout) without a rebuild.
    """
    root = Path(projroot) / STATE_SUBDIR
    angle = root / 'checkout'

    if assemble_only:
        env = _base_env()
        if not (angle / 'out').is_dir():
            raise RuntimeError(
                f'--assemble-only needs existing built slices under {angle}/out'
            )
    else:
        if clean and root.exists():
            print(f'Removing {root} ...', flush=True)
            shutil.rmtree(root)
        root.mkdir(parents=True, exist_ok=True)

        base_env = _base_env()
        depot_tools = _ensure_depot_tools(root, base_env)
        env = _scoped_env(root, depot_tools)
        _bootstrap_depot_tools(depot_tools, env)

        if sync:
            _sync_angle(angle, env)

        # Build the xcframework (iOS/tvOS) slices + the macOS slices for the
        # bare dylibs at the normal variant, plus the macOS slices at 'debug'
        # for the debug/validation dylibs.
        to_build: list[tuple[Slice, str]] = [
            (s, variant) for s in XCFRAMEWORK_SLICES + MACOS_SLICES
        ]
        to_build += [(s, 'debug') for s in MACOS_SLICES]
        for slc, var in to_build:
            _build_slice(angle, slc, var, env)

    # Assemble into the shared artifacts dir.
    artifacts = root / 'artifacts'
    if artifacts.exists():
        shutil.rmtree(artifacts)
    artifacts.mkdir(parents=True)
    work = root / 'assembly'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    for lib in LIBS:
        _assemble_xcframework(
            angle,
            lib,
            XCFRAMEWORK_SLICES,
            variant,
            out_path=artifacts / f'{lib}.xcframework',
            work=work / lib,
            env=env,
        )
    _stage_headers(angle, artifacts)

    # Bare macOS dylibs (libEGL.dylib + libGLESv2.dylib siblings) for the
    # macOS consumers that load ANGLE its native macOS way -- see
    # _macos_bare_dylibs. Normal variant + the debug/validation variant.
    _macos_bare_dylibs(angle, variant, artifacts / 'macos', env)
    _macos_bare_dylibs(angle, 'debug', artifacts / 'macos-debug', env)

    print(f'\nDone. xcframeworks staged to: {artifacts}', flush=True)


def test_build(projroot: str) -> None:
    """Build all Apple ANGLE xcframeworks at the cheap 'test' variant.

    Lazy: reuses an existing checkout (incremental sync). For CI / exercising
    the pipeline; optimization doesn't matter.
    """
    _do_build(projroot, variant='test', clean=False)


def build(projroot: str, *, assemble_only: bool = False) -> None:
    """Build the shipping-tier Apple ANGLE xcframeworks from scratch.

    Builds the optimized 'release' variant (is_official_build -> ThinLTO +
    stripped binaries + bundled dSYMs), plus the macOS debug/validation bare
    dylibs.

    By default this blows the whole ``build/angle-apple/`` tree away and
    re-syncs ANGLE first, for a guaranteed-from-scratch clean build (this is
    what CI and the ``make angle-apple-build`` target do). Set
    ``BA_ANGLE_APPLE_KEEP_CHECKOUT=1`` to instead reuse the existing checkout
    as-is -- skipping the wipe + the gclient re-sync and just recompiling
    (ninja-incremental) + reassembling. A fast local-iteration escape hatch;
    leave it unset for any build whose output you intend to ship/commit.

    ``assemble_only`` skips the clean rebuild and just (re)assembles the
    xcframeworks from the existing ``out/release`` + ``out/debug`` slices --
    for re-emitting after an assembly-logic change without a recompile.
    """
    keep_checkout = bool(os.environ.get('BA_ANGLE_APPLE_KEEP_CHECKOUT'))
    _do_build(
        projroot,
        variant='release',
        clean=not (assemble_only or keep_checkout),
        sync=not keep_checkout,
        assemble_only=assemble_only,
    )


def gather(projroot: str) -> None:
    """Install assembled xcframeworks from build/angle-apple/artifacts into src.

    Normal xcframeworks + headers + release macOS dylibs ->
    ``src/external/angle-apple``; the debug macOS dylibs ->
    ``src/external/angle-apple-debug``.
    """
    from efro.error import CleanError

    root = Path(projroot)
    artifacts = root / STATE_SUBDIR / 'artifacts'
    if not artifacts.is_dir():
        raise CleanError(
            f"Artifacts dir not found: '{artifacts}'."
            ' Run make angle-apple-build or angle-apple-test-build first.'
        )

    normal_dst = root / 'src' / 'external' / 'angle-apple'
    debug_dst = root / 'src' / 'external' / 'angle-apple-debug'

    def _install(src: Path, dst: Path) -> None:
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # symlinks=True is essential: the macOS slices are versioned framework
        # bundles whose Versions/Current + top-level entries are symlinks.
        # Dereferencing them (the default) yields a malformed bundle that Xcode
        # can't re-sign on embed -- it stays ad-hoc and dyld's library
        # validation then rejects it ("different Team IDs").
        shutil.copytree(src, dst, symlinks=True)
        print(f'Installed: {dst}')

    for lib in LIBS:
        _install(
            artifacts / f'{lib}.xcframework', normal_dst / f'{lib}.xcframework'
        )
    # Headers go with the normal set.
    if (artifacts / 'include').is_dir():
        _install(artifacts / 'include', normal_dst / 'include')
    # Bare macOS dylibs (normal -> angle-apple/macos, debug -> -debug/macos).
    if (artifacts / 'macos').is_dir():
        _install(artifacts / 'macos', normal_dst / 'macos')
    if (artifacts / 'macos-debug').is_dir():
        _install(artifacts / 'macos-debug', debug_dst / 'macos')
