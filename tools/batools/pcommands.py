# Released under the MIT License. See LICENSE for details.
#
"""A nice collection of ready-to-use pcommands for this package."""

# Note: import as little as possible here at the module level to
# keep launch times fast for small snippets.
import sys

from efrotools import pcommand


def prune_includes() -> None:
    """Check for unnecessary includes in C++ files.

    Pass --commit to actually modify files.
    """
    from batools.pruneincludes import Pruner

    args = sys.argv.copy()[2:]
    commit = False
    if '--commit' in args:
        args.remove('--commit')
        commit = True

    Pruner(commit=commit, paths=args).run()
    print('Prune run complete!')


def resize_image() -> None:
    """Resize an image and save it to a new location.

    args: xres, yres, src, dst
    """
    import os
    import subprocess

    if len(sys.argv) != 6:
        raise RuntimeError('Expected 5 args.')
    width = int(sys.argv[2])
    height = int(sys.argv[3])
    src = sys.argv[4]
    dst = sys.argv[5]
    if not dst.endswith('.png'):
        raise RuntimeError(f'dst must be a png; got "{dst}"')
    if not src.endswith('.png'):
        raise RuntimeError(f'src must be a png; got "{src}"')
    print('Creating: ' + os.path.basename(dst), file=sys.stderr)
    subprocess.run(
        f'convert "{src}" -resize {width}x{height} "{dst}"',
        shell=True,
        check=True,
    )


def check_clean_safety() -> None:
    """Ensure all files are are added to git or in gitignore.

    Use to avoid losing work if we accidentally do a clean without
    adding something.
    """
    import os
    import subprocess

    from efro.terminal import Clr
    from efro.error import CleanError

    import efrotools.pcommands

    ignorevar = 'BA_IGNORE_CLEAN_SAFETY_CHECK'
    if os.environ.get(ignorevar) == '1':
        return
    try:
        # First do standard checks.
        efrotools.pcommands.check_clean_safety()

        # Then also make sure there are no untracked changes to core files
        # (since we may be blowing core away here).
        spinoff_bin = os.path.join(str(pcommand.PROJROOT), 'tools', 'spinoff')
        if os.path.exists(spinoff_bin):
            result = subprocess.run(
                [spinoff_bin, 'cleancheck', '--soft'], check=False
            )
            if result.returncode != 0:
                raise CleanError()
    except Exception:
        print(
            f'{Clr.RED}Clean safety check failed.'
            f' Set {ignorevar}=1 to proceed anyway.{Clr.RST}'
        )
        raise


def archive_old_builds() -> None:
    """Stuff our old public builds into the 'old' dir.

    (called after we push newer ones)
    """
    import batools.build

    if len(sys.argv) < 3:
        raise RuntimeError('Invalid arguments.')
    ssh_server = sys.argv[2]
    builds_dir = sys.argv[3]
    ssh_args = sys.argv[4:]
    batools.build.archive_old_builds(ssh_server, builds_dir, ssh_args)


def lazy_increment_build() -> None:
    """Increment build number only if C++ sources have changed.

    This is convenient to place in automatic commit/push scripts.
    It could make sense to auto update build number when scripts/assets
    change too, but a build number change requires rebuilding all binaries
    so I'll leave that as an explicit choice to save work.
    """
    import os
    import subprocess
    from efro.terminal import Clr
    from efro.error import CleanError
    from efrotools.util import get_files_hash
    from efrotools.code import get_code_filenames

    if sys.argv[2:] not in [[], ['--update-hash-only']]:
        raise CleanError('Invalid arguments')
    update_hash_only = '--update-hash-only' in sys.argv
    codefiles = get_code_filenames(pcommand.PROJROOT, include_generated=False)
    codehash = get_files_hash(codefiles)
    hashfilename = '.cache/lazy_increment_build'
    try:
        with open(hashfilename, encoding='utf-8') as infile:
            lasthash = infile.read()
    except FileNotFoundError:
        lasthash = ''
    if codehash != lasthash:
        if not update_hash_only:
            print(
                f'{Clr.SMAG}Source(s) changed; incrementing build...{Clr.RST}'
            )
            # Just go ahead and bless; this will increment the build as needed.
            # subprocess.run(['make', 'bless'], check=True)
            subprocess.run(
                ['tools/pcommand', 'version', 'incrementbuild'], check=True
            )

        # We probably just changed code, so we need to re-calc the hash.
        codehash = get_files_hash(codefiles)
        os.makedirs(os.path.dirname(hashfilename), exist_ok=True)
        with open(hashfilename, 'w', encoding='utf-8') as outfile:
            outfile.write(codehash)


def androidaddr() -> None:
    """Return the source file location for an android program-counter.

    command line args: archive_dir architecture addr
    """
    import batools.android
    from efro.error import CleanError

    if len(sys.argv) != 5:
        raise CleanError(
            f'ERROR: expected 3 args; got {len(sys.argv) - 2}\n'
            f'Usage: "tools/pcommand android_addr'
            f' <ARCHIVE-PATH> <ARCH> <ADDR>"'
        )
    archive_dir = sys.argv[2]
    arch = sys.argv[3]
    addr = sys.argv[4]
    batools.android.androidaddr(archive_dir=archive_dir, arch=arch, addr=addr)


def push_ipa() -> None:
    """Construct and push ios IPA for testing."""

    from efro.util import extract_arg
    import efrotools.ios

    args = sys.argv[2:]
    signing_config = extract_arg(args, '--signing-config')

    if len(args) != 1:
        raise RuntimeError('Expected 1 mode arg (debug or release).')
    modename = args[0].lower()
    efrotools.ios.push_ipa(
        pcommand.PROJROOT, modename, signing_config=signing_config
    )


def printcolors() -> None:
    """Print all colors available in efro.terminals.TerminalColor."""
    from efro.error import CleanError
    from efro.terminal import TerminalColor, Clr

    if Clr.RED == '':
        raise CleanError('Efro color terminal output is disabled.')

    clrnames = {getattr(Clr, s): s for s in dir(Clr) if s.isupper()}

    # Print everything in Clr (since that's what users should be using
    # but do it in the order of TerminalColor (since Clr is just a class
    # so is unordered)
    for value in TerminalColor:
        if value is TerminalColor.RESET:
            continue
        shortname = f'Clr.{clrnames[value.value]}'
        longname = f'({value.name})'
        print(
            f'{shortname:<12} {longname:<20} {value.value}'
            f'The quick brown fox jumps over the lazy dog.'
            f'{TerminalColor.RESET.value}'
        )


def python_version_android_base() -> None:
    """Print built Python base version."""
    # Source of truth is the new in-tree build script. Legacy
    # PY_VER_ANDROID in efrotools.pybuild is for the old pipeline
    # (build_android / patch flow) and is not what active builds
    # consume.
    from efrotools.python_build_android import PY_VER

    print(PY_VER, end='')


def python_version_android() -> None:
    """Print Android embedded Python version."""
    from efrotools.python_build_android import PY_VER_EXACT

    print(PY_VER_EXACT, end='')


def python_build_android_old() -> None:
    """Build an embeddable Python lib for Android (old pipeline)."""

    _python_build_android_old(debug=False)


def python_android_build() -> None:
    """Build Android Python lib using new in-tree build script."""

    _python_build_android(debug=False)


def python_android_build_debug() -> None:
    """Build Android Python lib using new in-tree script (debug)."""

    _python_build_android(debug=True)


def _python_build_android(debug: bool) -> None:
    import os
    from efro.error import CleanError
    from efrotools import python_build_android as _python_build_android_mod

    os.chdir(pcommand.PROJROOT)
    archs = ('arm', 'arm64', 'x86', 'x86_64')
    if len(sys.argv) != 3:
        raise CleanError('Error: Expected one <ARCH> arg: ' + ', '.join(archs))
    arch = sys.argv[2]
    if arch not in archs:
        raise CleanError(
            'Error: invalid arch. valid values are: ' + ', '.join(archs)
        )
    _python_build_android_mod.build(str(pcommand.PROJROOT), arch, debug=debug)


def static_dependencies_build_debug() -> None:
    """Build static dependencies for Android and Apple platforms."""

    _static_dependencies_build(debug=True)


def _static_dependencies_build(debug: bool) -> None:
    """Build static dependencies for Android and Apple platforms."""
    import os
    from efro.error import CleanError
    from efrotools import (
        static_dependencies_build as static_dependencies_build__mod,
    )

    os.chdir(pcommand.PROJROOT)
    archs = ('arm', 'arm64', 'x86', 'x86_64')
    if len(sys.argv) != 3:
        raise CleanError('Error: Expected one <ARCH> arg: ' + ', '.join(archs))
    arch = sys.argv[2]
    if arch not in archs:
        raise CleanError(
            'Error: invalid arch. valid values are: ' + ', '.join(archs)
        )
    static_dependencies_build__mod.build(
        str(pcommand.PROJROOT), arch, debug=debug
    )


def python_android_gather() -> None:
    """Gather Android Python build into project."""
    from efrotools import python_build_android as _python_build_android_mod

    _python_build_android_mod.gather(str(pcommand.PROJROOT))


def python_build_apple() -> None:
    """Build one Apple Python slice using new in-tree script."""
    import os
    from efro.error import CleanError
    from efrotools import python_build_apple as _python_build_apple_mod

    slices = _python_build_apple_mod.SLICES
    if len(sys.argv) != 3 or sys.argv[2] not in slices:
        raise CleanError('Expected one slice arg: ' + ', '.join(slices))
    os.chdir(pcommand.PROJROOT)
    _python_build_apple_mod.build(str(pcommand.PROJROOT), sys.argv[2])


def python_apple_gather() -> None:
    """Gather Apple Python slices into XCFramework and copy to project."""
    import os
    from efrotools import python_build_apple as _python_build_apple_mod

    os.chdir(pcommand.PROJROOT)
    _python_build_apple_mod.gather(str(pcommand.PROJROOT))


def angle_apple_test_build() -> None:
    """Build all Apple ANGLE xcframeworks at the cheap 'test' variant.

    For CI / exercising the gn build pipeline -- optimization doesn't matter.
    Lazily reuses an existing checkout under build/angle-apple/ (incremental
    sync), builds mac/iOS/tvOS plus the macOS debug-validation variant, and
    assembles .xcframeworks into build/angle-apple/artifacts/. Self-contained
    (depot_tools fetches a hermetic clang/gn/ninja); needs Xcode + system git.
    Follow with 'make angle-apple-gather' to install into the source tree.
    """
    import os
    from batools import buildangleapple

    os.chdir(pcommand.PROJROOT)
    buildangleapple.test_build(str(pcommand.PROJROOT))


def angle_apple_build() -> None:
    """Build shipping-tier Apple ANGLE xcframeworks from scratch.

    Always starts clean and builds the optimized 'release' variant
    (is_official_build -> ThinLTO + stripped binaries + bundled dSYMs) plus the
    macOS debug-validation xcframeworks, assembling into
    build/angle-apple/artifacts/. Self-contained under build/angle-apple/; needs
    Xcode + system git. Follow with 'make angle-apple-gather' to install.

    Pass '--assemble-only' to skip the rebuild and just (re)assemble the
    xcframeworks from the existing build/angle-apple/checkout/out slices --
    for re-emitting after an assembly-logic change without a full build.
    """
    import os
    from batools import buildangleapple

    assemble_only = '--assemble-only' in sys.argv
    os.chdir(pcommand.PROJROOT)
    buildangleapple.build(str(pcommand.PROJROOT), assemble_only=assemble_only)


def angle_apple_gather() -> None:
    """Install assembled Apple ANGLE xcframeworks into the source tree.

    Copies build/angle-apple/artifacts/ into src/external/angle-apple (normal
    set + headers) and src/external/angle-apple-debug (macOS debug set).
    """
    import os
    from batools import buildangleapple

    os.chdir(pcommand.PROJROOT)
    buildangleapple.gather(str(pcommand.PROJROOT))


def python_build_android_old_debug() -> None:
    """Build embeddable Android Python lib (old pipeline, debug ver)."""

    _python_build_android_old(debug=True)


def _python_build_android_old(debug: bool) -> None:
    import os
    from efro.error import CleanError
    from efrotools import pybuild

    os.chdir(pcommand.PROJROOT)
    archs = ('arm', 'arm64', 'x86', 'x86_64')
    if len(sys.argv) != 3:
        raise CleanError('Error: Expected one <ARCH> arg: ' + ', '.join(archs))
    arch = sys.argv[2]
    if arch not in archs:
        raise CleanError(
            'Error: invalid arch. valid values are: ' + ', '.join(archs)
        )
    pybuild.build_android(str(pcommand.PROJROOT), arch, debug=debug)


def python_android_patch_old() -> None:
    """Patches Python to prep for building for Android (old pipeline)."""
    import os
    from efrotools import pybuild

    os.chdir(sys.argv[2])
    pybuild.android_patch()


def python_android_patch_ssl_old() -> None:
    """Patches Python ssl to prep for building for Android (old pipeline)."""
    from efrotools import pybuild

    pybuild.android_patch_ssl()


def python_gather() -> None:
    """Gather build python components into the project.

    This assumes all embeddable py builds have been run successfully.
    """
    import os
    from efrotools import pybuild

    os.chdir(pcommand.PROJROOT)
    pybuild.gather(do_android=True)


def python_gather_android_old() -> None:
    """python_gather but only android bits (old pipeline)."""
    import os
    from efrotools import pybuild

    os.chdir(pcommand.PROJROOT)
    pybuild.gather(do_android=True)


def python_winprune() -> None:
    """Prune unneeded files from windows python."""
    import os
    from efrotools import pybuild

    os.chdir(pcommand.PROJROOT)
    pybuild.winprune()


def capitalize() -> None:
    """Print args capitalized."""

    print(' '.join(w.capitalize() for w in sys.argv[2:]), end='')


def upper() -> None:
    """Print args uppercased."""

    pcommand.clientprint(
        ' '.join(w.upper() for w in pcommand.get_args()), end=''
    )


def efrocache_update() -> None:
    """Build & push files to efrocache for public access."""
    from efrotools.efrocache import update_cache

    makefile_dirs = ['', 'src/assets', 'src/resources', 'src/codegen']
    update_cache(makefile_dirs)


def efrocache_get() -> None:
    """Get a file from efrocache."""
    from efrotools.efrocache import get_target

    args = pcommand.get_args()
    if len(args) != 1:
        raise RuntimeError('Expected exactly 1 arg')

    output = get_target(args[0], batch=pcommand.is_batch(), clr=pcommand.clr())
    if pcommand.is_batch():
        pcommand.clientprint(output)


def warm_start_asset_build() -> None:
    """Prep asset builds to run faster."""
    import os

    from efrotools.project import getprojectconfig
    from efro.error import CleanError

    args = pcommand.get_args()
    if len(args) != 1:
        raise CleanError('Expected a single "gui" or "server" arg.')
    cachetype = args[0]

    public: bool = getprojectconfig(pcommand.PROJROOT)['public']

    if public:
        from efrotools.efrocache import warm_start_cache

        os.chdir(pcommand.PROJROOT)
        warm_start_cache(cachetype)

    # In the internal repo there's currently nothing to warm up; the old
    # convert cache went away when converted asset kinds (textures, audio,
    # meshes) moved to asset-packages.


def gen_docs_sphinx() -> None:
    """Generate sphinx documentation."""
    import batools.docs

    batools.docs.generate_sphinx_docs()


def checkenv() -> None:
    """Check for tools necessary to build and run the app."""
    import batools.build

    batools.build.checkenv()


def prefab_platform() -> None:
    """Print the current prefab-platform value."""
    from efro.error import CleanError

    from batools.build import PrefabPlatform

    # Platform determination uses env vars; won't work in batch.

    args = pcommand.get_args()
    if len(args) != 0:
        raise CleanError('No arguments expected.')

    current = PrefabPlatform.get_current()

    print(current.value, end='')


def ensure_prefab_platform() -> None:
    """Ensure we are running on a particular prefab platform.

    Note that prefab platform may not exactly match hardware/os.
    For example, when running in Linux under a WSL environment,
    the prefab platform may be Windows; not Linux. Also, a 64-bit
    os may be targeting a 32-bit platform.
    """
    from efro.error import CleanError

    from batools.build import PrefabPlatform

    # Platform determination uses env vars; won't work in batch.

    args = pcommand.get_args()
    if len(args) != 1:
        options = ', '.join(t.value for t in PrefabPlatform)
        raise CleanError(
            f'Expected 1 PrefabPlatform arg. Options are {options}.'
        )
    needed = PrefabPlatform(args[0])
    current = PrefabPlatform.get_current()
    if current is not needed:
        raise CleanError(
            f'Incorrect platform: we are {current.value},'
            f' this requires {needed.value}.'
        )


def prefab_run_var() -> None:
    """Print the current platform prefab run target var."""
    from batools.build import PrefabPlatform

    # Platform determination uses env vars; won't work in batch.

    args = pcommand.get_args()
    if len(args) != 1:
        raise RuntimeError('Expected 1 arg.')
    base = args[0].replace('-', '_').upper()
    platform = PrefabPlatform.get_current().value.upper()
    pcommand.clientprint(f'RUN_PREFAB_{platform}_{base}', end='')


def prefab_binary_path() -> None:
    """Print the path to the current prefab binary."""
    from typing import assert_never

    from efro.error import CleanError

    from batools.build import PrefabPlatform, PrefabTarget

    # Platform determination uses env vars; won't work in batch.

    if len(sys.argv) != 3:
        options = ', '.join(t.value for t in PrefabTarget)
        raise CleanError(f'Expected 1 PrefabTarget arg. Options are {options}.')

    target = PrefabTarget(sys.argv[2])

    buildtype = target.buildtype
    buildmode = target.buildmode

    platform = PrefabPlatform.get_current()

    binpath = None

    if (
        platform is PrefabPlatform.WINDOWS_X86
        or platform is PrefabPlatform.WINDOWS_X86_64
    ):
        if buildtype == 'gui':
            binpath = 'BallisticaKit.exe'
        elif buildtype == 'server':
            binpath = 'dist/BallisticaKitHeadless.exe'
        else:
            raise ValueError(f"Invalid buildtype '{buildtype}'.")
    elif (
        platform is PrefabPlatform.MAC_ARM64
        or platform is PrefabPlatform.MAC_X86_64
        or platform is PrefabPlatform.LINUX_ARM64
        or platform is PrefabPlatform.LINUX_X86_64
    ):
        if buildtype == 'gui':
            binpath = 'ballisticakit'
        elif buildtype == 'server':
            binpath = 'dist/ballisticakit_headless'
        else:
            raise ValueError(f"Invalid buildtype '{buildtype}'.")
    else:
        # Make sure we're covering all options.
        assert_never(platform)

    assert binpath is not None
    print(
        f'build/prefab/full/{platform.value}_{buildtype}/{buildmode}/{binpath}',
        end='',
    )


def make_prefab() -> None:
    """Run prefab builds for the current platform."""
    import subprocess
    from batools.build import PrefabPlatform, PrefabTarget

    # Platform determination uses env vars; won't work in batch.

    if len(sys.argv) != 3:
        raise RuntimeError('Expected one argument')

    targetstr = PrefabTarget(sys.argv[2]).value
    platformstr = PrefabPlatform.get_current().value

    # We use dashes instead of underscores in target names.
    platformstr = platformstr.replace('_', '-')
    try:
        subprocess.run(
            ['make', f'prefab-{platformstr}-{targetstr}-build'], check=True
        )
    except (Exception, KeyboardInterrupt) as exc:
        if str(exc):
            print(f'make_prefab failed with error: {exc}')
        sys.exit(-1)


def lazybuild() -> None:
    """Run a build command only if an input has changed."""
    import subprocess
    import batools.build
    from efro.error import CleanError

    # This command is not a good candidate for batch since it can be
    # long running and prints various stuff throughout the process.

    args = pcommand.get_args()

    if len(args) < 3:
        raise CleanError('Expected at least 3 args')
    try:
        category = batools.build.LazyBuildCategory(args[0])
    except ValueError as exc:
        raise CleanError(exc) from exc
    target = args[1]
    command = ' '.join(args[2:])
    try:
        batools.build.lazybuild(target, category, command)
    except subprocess.CalledProcessError as exc:
        raise CleanError(exc) from exc


def logcat() -> None:
    """Get logcat command for filtering."""
    import subprocess
    from efro.terminal import Clr
    from efro.error import CleanError

    if len(sys.argv) != 4:
        raise CleanError('Expected 2 args')
    adb = sys.argv[2]
    _plat = sys.argv[3]

    # My amazon tablet chokes on the color format.
    # if plat == 'amazon':
    #     format_args = ''
    # else:
    format_args = '-v color '
    cmd = (
        f'{adb} logcat {format_args}BallisticaKit:V CrashAnrDetector:V \'*:S\''
    )
    print(f'{Clr.BLU}Running logcat command: {Clr.BLD}{cmd}{Clr.RST}')
    subprocess.run(cmd, shell=True, check=True)


def _camel_case_split(string: str) -> list[str]:

    words = [[string[0]]]
    for char in string[1:]:
        if words[-1][-1].islower() and char.isupper():
            words.append(list(char))
        else:
            words[-1].append(char)
    return [''.join(word) for word in words]


def efro_gradle() -> None:
    """Calls ./gradlew with some extra magic."""
    import os
    import subprocess
    from efro.terminal import Clr
    from efrotools.android import filter_gradle_file

    args = ['./gradlew'] + sys.argv[2:]

    # Under Claude Code's sandbox, all network egress is forced through
    # an authenticating proxy that the JVM/Gradle won't use, so any
    # dependency or Gradle-distribution *download* fails. Force
    # --offline so the build relies solely on the already-warmed Gradle
    # caches (populated by normal, unsandboxed builds). No-op outside
    # the sandbox, where nothing sets these env vars.
    forced_offline = False
    in_sandbox = bool(os.environ.get('SANDBOX_RUNTIME')) or os.environ.get(
        'ALL_PROXY', ''
    ).startswith(('socks5://', 'socks5h://'))
    if in_sandbox and '--offline' not in args:
        args.append('--offline')
        forced_offline = True
        print(
            f'{Clr.YLW}efro_gradle: sandbox detected -- adding --offline'
            ' (Gradle cannot reach the network through the sandbox'
            ' proxy); dependencies must already be cached by a prior'
            f' unsandboxed build.{Clr.RST}',
            flush=True,
        )

    print(f'{Clr.BLU}Running gradle with args:{Clr.RST} {args}.', flush=True)
    enabled_tags: set[str] = {'true'}
    target_words = [w.lower() for w in _camel_case_split(args[-1])]
    if 'google' in target_words:
        # Augment rather than replace; otherwise we lose the 'true'
        # tag and the single-arch flavor declarations (arm/arm64/
        # x86/x86_64, gated by ``// EFRO_IF true``) stay commented
        # out — breaking ANDROID_MODE!=prod for google builds.
        enabled_tags |= {'google', 'crashlytics'}
    prev_suffix = 'efro_gradle_prev'

    buildfilename = 'BallisticaKit/build.gradle'

    # Move the original file out of the way and operate on a copy of it.
    subprocess.run(
        ['mv', buildfilename, f'{buildfilename}.{prev_suffix}'], check=True
    )
    subprocess.run(
        ['cp', f'{buildfilename}.{prev_suffix}', buildfilename], check=True
    )

    filter_gradle_file(buildfilename, enabled_tags)

    try:
        subprocess.run(args, check=True)
        errored = False
    except BaseException:
        errored = True

    # Restore the original.
    subprocess.run(
        ['mv', f'{buildfilename}.{prev_suffix}', buildfilename], check=True
    )

    if errored:
        if forced_offline:
            print(
                f'{Clr.RED}efro_gradle: build failed in sandbox-forced'
                ' offline mode. If the error above says "No cached'
                ' version ... available for offline mode" (or shows a'
                ' failed distribution download), a dependency or the'
                ' Gradle distribution is not cached -- run this build'
                " once OUTSIDE Claude's sandbox to warm the cache, then"
                f' retry.{Clr.RST}',
                flush=True,
            )
        sys.exit(1)


def stage_build() -> None:
    """Stage assets for a build."""
    import batools.staging
    from efro.error import CleanError

    try:
        batools.staging.stage_build(
            projroot=str(pcommand.PROJROOT), args=pcommand.get_args()
        )
    except CleanError as exc:
        exc.pretty_print()
        sys.exit(1)


def update_project() -> None:
    """Update project files.

    This command is in charge of generating Makefiles, IDE project files,
    etc. based on the current structure of the project.
    It can also perform sanity checks or cleanup tasks.

    Updating should be explicitly run by the user through commands such as
    'make update', 'make check' or 'make preflight'. Other make targets should
    avoid running this command as it can modify the project structure
    arbitrarily which is not a good idea in the middle of a build.

    If this command is invoked with a --check argument, it should not modify
    any files but instead fail if any modifications *would* have been made.
    (used in CI builds to make sure things are kosher).
    """
    import os
    from batools.project import ProjectUpdater

    check = '--check' in sys.argv
    fix = '--fix' in sys.argv

    # ProjectUpdater is supposed to work from any dir, so let's keep
    # ourself honest by forcing the issue.
    cwd = os.getcwd()
    os.chdir('/')

    ProjectUpdater(cwd, check=check, fix=fix).run()


def cmake_prep_dir() -> None:
    """Create dir & recreate when cmake/python/etc. version changes.

    Useful to prevent builds from breaking when cmake or other components
    are updated.
    """
    import os
    from efro.error import CleanError
    import batools.build

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg (dir name)')
    dirname = sys.argv[2]
    batools.build.cmake_prep_dir(
        dirname, verbose=os.environ.get('VERBOSE') == '1'
    )


def gen_binding_code() -> None:
    """Generate a binding_foo.inc file."""
    from efro.error import CleanError
    import batools.codegenbuild

    if len(sys.argv) != 4:
        raise CleanError('Expected 2 args (srcfile, dstfile)')
    inpath = sys.argv[2]
    outpath = sys.argv[3]
    batools.codegenbuild.gen_binding_code(
        str(pcommand.PROJROOT), inpath, outpath
    )


def genchangelog() -> None:
    """Gen a pretty html changelog."""
    from batools.changelog import generate

    generate(projroot=str(pcommand.PROJROOT))


def get_changelog() -> None:
    """Print the changelog for a specified version"""
    from efro.error import CleanError
    from efro.terminal import Clr

    from batools.changelog import get_version_changelog

    args = pcommand.get_args()
    if len(args) != 1:
        raise CleanError('Expected 1 arg: version')
    version_str = args[0]

    changelog_list = get_version_changelog(
        version=version_str, projroot=str(pcommand.PROJROOT)
    )
    print(f'{Clr.BLD}Changelog for version ' f'{version_str}:{Clr.RST}\n')
    for entry in changelog_list:
        print(f'{Clr.CYN}-{Clr.RST} {entry}')


def android_sdk_utils() -> None:
    """Wrangle android sdk stuff."""
    from batools.androidsdkutils import run

    run(projroot=str(pcommand.PROJROOT), args=sys.argv[2:])


def gen_python_enums_module() -> None:
    """Update our procedurally generated python enums."""
    from batools.enumspython import generate

    if len(sys.argv) != 4:
        raise RuntimeError('Expected infile and outfile args.')
    generate(
        projroot=str(pcommand.PROJROOT),
        infilename=sys.argv[2],
        outfilename=sys.argv[3],
    )


def gen_dummy_modules() -> None:
    """Generate all dummy modules."""
    from efro.error import CleanError
    from batools.dummymodule import generate_dummy_modules

    if len(sys.argv) != 2:
        raise CleanError(f'Expected no args; got {len(sys.argv)-2}.')

    generate_dummy_modules(projroot=str(pcommand.PROJROOT))


def gen_vanilla_completions() -> None:
    """Generate a JSON completion index for the vanilla API."""
    from efro.error import CleanError
    from batools.vanillacompletions import generate_vanilla_completions

    if len(sys.argv) != 2:
        raise CleanError(f'Expected no args; got {len(sys.argv) - 2}.')

    generate_vanilla_completions(projroot=str(pcommand.PROJROOT))


def gen_check_environment() -> None:
    """Generate a standalone mypy/pylint check environment."""
    from efro.error import CleanError
    from batools.checkenvironment import generate_check_environment

    if len(sys.argv) != 2:
        raise CleanError(f'Expected no args; got {len(sys.argv) - 2}.')

    generate_check_environment(projroot=str(pcommand.PROJROOT))


def version() -> None:
    """Check app versions."""
    from batools.version import run

    run(projroot=str(pcommand.PROJROOT), args=sys.argv[2:])
